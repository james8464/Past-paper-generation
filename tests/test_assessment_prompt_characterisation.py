from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from Backend.Core import ai_assessment, independent_solver
from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.generation_requests import OutputContract, make_request
from Backend.Core.independent_solver import IndependentSolver, _without_answer_key
from Backend.Core.model_review import ReviewResult
from tests.test_assessment_checkpoints import paper_fixture

GOLDEN = Path(__file__).parent / "fixtures" / "assessment_prompt_snapshots.json"
SUBJECT_HANDLERS = (
    "solve_accounting_calculation",
    "solve_computer_science_contract",
    "solve_economics_contract",
    "solve_selected_response",
)


def _snapshot(request):
    schema = request.schema
    return {
        "prompt": request.prompt,
        "prompt_sha256": hashlib.sha256(request.prompt.encode("utf-8")).hexdigest(),
        "metadata": {
            "version": request.version,
            "operation": request.operation,
            "generation_seed": request.generation_seed,
            "attempt": request.attempt,
            "seed": request.seed,
            "temperature": request.temperature,
            "output_budget": request.output_budget,
            "expected_ids": list(request.expected_ids),
            "schema": schema,
            "schema_sha256": hashlib.sha256(
                json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
    }


class CapturingClient:
    def __init__(self, answer="A supported explanation.", evidence_ids=()):
        self.requests = []
        self.answer = answer
        self.evidence_ids = evidence_ids

    def generate_json(self, _prompt):
        pytest.fail("current solver bypassed its trusted request")

    def generate_request(self, request):
        self.requests.append(request)
        result = {
            "steps": ["Use the supplied public information."],
            "answer": copy.deepcopy(self.answer),
            "mark_points": copy.deepcopy(self.answer)
            if isinstance(self.answer, dict)
            else [self.answer],
            "evidence_ids": list(self.evidence_ids),
            "alternatives": [],
            "partial_credit_boundaries": [],
            "follow_through_rules": [],
        }
        if "has_single_valid_choice" in request.schema.get("properties", {}):
            result["has_single_valid_choice"] = True
        return result


def capture_snapshots():
    paper, _rule, topics = paper_fixture()
    original = paper.model_dump(mode="json")
    task = ai_assessment._tasks(paper, {topic.id: topic for topic in topics})[0]
    candidate = task.question.model_copy(
        update={"prompt": "Explain why higher costs reduce profit."}
    )
    identifiers = (task.id,)
    prompts = {
        "author": make_request(
            ai_assessment._generation_prompt(
                [task],
                subject="Economics",
                seed=paper.seed,
                attempt=1,
                previous_failure="",
            ),
            OutputContract("authoring", identifiers=identifiers),
            generation_seed=paper.seed,
            attempt=1,
        ),
        "repair": make_request(
            ai_assessment._repair_prompt(
                task,
                candidate,
                ReviewResult(
                    approved=False, source_issues=["Address the declared task scope."]
                ),
                subject="Economics",
                seed=paper.seed,
                attempt=2,
            ),
            OutputContract("authoring", identifiers=identifiers),
            generation_seed=paper.seed,
            attempt=2,
        ),
        "review": make_request(
            ai_assessment._review_prompt([task], [candidate], subject="Economics"),
            OutputContract("batch_review", identifiers=identifiers),
        ),
    }
    assert paper.model_dump(mode="json") == original
    source = EvidenceRecord(
        id="source-1", text="Café records contain candidate-visible information."
    )
    base = {
        "id": "solver-fixture",
        "marks": 1,
        "prompt": "Explain a possible decision.",
        "mark_scheme": ["PRIVATE_KEY_CANARY"],
    }
    cases = {
        "solver_open": (base, "A supported explanation.", None),
        "solver_closed": (
            {
                **base,
                "marks": 2,
                "prompt": "Complete the labelled blanks.",
                "response_slots": ["type", "scope"],
            },
            {"type": "Applications", "scope": "Utilities"},
            None,
        ),
        "solver_mcq": (
            {
                **base,
                "kind": "multiple_choice",
                "prompt": "Choose the appropriate description.",
                "choices": ["Public option α", "Public option β"],
                "correct_choice": 1,
            },
            "Public option α",
            None,
        ),
        "solver_sql_correction": (
            {
                **base,
                "marks": 2,
                "prompt": "Write a SELECT statement for the declared relation.",
                "authoring_context": {"sql_answer_contract": {}},
            },
            "SELECT name FROM records;",
            [
                {
                    "kind": "unsupported_syntax",
                    "message": "Use only the declared SQL syntax.",
                }
            ],
        ),
    }
    for name, (item, answer, findings) in cases.items():
        before = copy.deepcopy(item)
        client = CapturingClient(answer, evidence_ids=(source.id,))
        IndependentSolver(client).solve(item, [source], correction_findings=findings)
        assert item == before
        assert len(client.requests) == 1
        assert "PRIVATE_KEY_CANARY" not in client.requests[0].prompt
        prompts[name] = client.requests[0]
    return {name: _snapshot(request) for name, request in prompts.items()}


def test_exact_prompt_bytes_and_trusted_metadata_match_current_policy_snapshot():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert capture_snapshots() == expected


@pytest.mark.parametrize("stop", [0, 1, 2, 3, None])
@pytest.mark.parametrize("empty", [False, True])
def test_subject_dispatch_order_and_none_vs_empty_result(monkeypatch, stop, empty):
    calls = []
    result = (
        {}
        if empty
        else {"answer": "Subject result.", "mark_points": ["Subject result."]}
    )
    for index, name in enumerate(SUBJECT_HANDLERS):

        def handler(_item, index=index, name=name):
            calls.append(name)
            return result if index == stop else None

        monkeypatch.setattr(independent_solver, name, handler)
    item = {"id": "dispatch", "marks": 1, "prompt": "Explain a possible decision."}
    before = copy.deepcopy(item)
    client = CapturingClient()
    if stop is not None and empty:
        with pytest.raises(ValueError, match="independent solver returned no answer"):
            IndependentSolver(client).solve(item, [])
        solution = None
    else:
        solution = IndependentSolver(client).solve(item, [])
    assert item == before
    assert calls == list(
        SUBJECT_HANDLERS[: stop + 1] if stop is not None else SUBJECT_HANDLERS
    )
    assert len(client.requests) == (1 if stop is None else 0)
    if solution is not None:
        assert solution.answer == (
            "A supported explanation." if stop is None else "Subject result."
        )


@pytest.mark.parametrize("failure_index", range(4))
def test_subject_dispatch_does_not_swallow_validation_errors(
    monkeypatch, failure_index
):
    calls = []
    failure = ValueError("Subject contract rejected")
    for index, name in enumerate(SUBJECT_HANDLERS):

        def handler(_item, index=index, name=name):
            calls.append(name)
            if index == failure_index:
                raise failure
            return None

        monkeypatch.setattr(independent_solver, name, handler)
    client = CapturingClient()
    with pytest.raises(ValueError) as raised:
        IndependentSolver(client).solve(
            {"id": "dispatch", "marks": 1, "prompt": "Explain a decision."}, []
        )
    assert raised.value is failure
    assert calls == list(SUBJECT_HANDLERS[: failure_index + 1])
    assert client.requests == []


def test_explicit_numeric_expression_keeps_precedence_over_subject_result(monkeypatch):
    calls = []
    monkeypatch.setattr(
        independent_solver,
        SUBJECT_HANDLERS[0],
        lambda _: calls.append("accounting") or {"answer": "Earlier subject result."},
    )
    item = {
        "id": "numeric",
        "marks": 1,
        "prompt": "Calculate the result.",
        "authoring_context": {
            "calculation_expression": "x+1",
            "calculation_variables": {"x": 2},
            "calculation_input_units": {"x": "1"},
            "calculation_output": {
                "role": "result",
                "unit": "1",
                "decimal_places": 0,
                "scheme_pattern": r"^Value: (?P<value>[0-9]+)$",
            },
        },
    }
    before = copy.deepcopy(item)
    client = CapturingClient()
    solution = IndependentSolver(client).solve(item, [])
    assert solution.answer_slots == {"result": "3"}
    assert solution.numeric_results == {"result": 3.0}
    assert calls == ["accounting"] and not client.requests
    assert item == before
    item["authoring_context"]["calculation_variables"] = None
    with pytest.raises(ValueError, match="incomplete numeric expression contract"):
        IndependentSolver(client).solve(item, [])


def test_known_key_filter_is_not_a_printed_candidate_whitelist():
    value = {
        "mark_scheme": ["PRIVATE_TOP"],
        "context": {
            "required_entries": ["UNPRINTED_METADATA_REMAINS"],
            "credit": "ordinary source column",
            "rows": [{"debit": 2, "credit": 3, "correct_choice": "PRIVATE_NESTED"}],
            "accounting_source_content": ["PRIVATE_CREDIT"],
            "grouped_level_policy": {"answer": "PRIVATE_GROUP"},
        },
    }
    before = copy.deepcopy(value)
    projected = _without_answer_key(value)
    assert "PRIVATE_" not in json.dumps(projected)
    assert projected["context"]["required_entries"] == ["UNPRINTED_METADATA_REMAINS"]
    assert projected["context"]["rows"] == [{"debit": 2, "credit": 3}]
    assert projected["context"]["credit"] == "ordinary source column"
    assert value == before
    preserved_tuple = ("non-JSON tuple",)
    assert _without_answer_key(preserved_tuple) is preserved_tuple


def test_legacy_helper_names_are_aliases_for_the_extracted_implementations():
    from Backend.Core import assessment_prompts
    from Backend.Core.answer_projection import without_private_answer_keys

    assert independent_solver._without_answer_key is without_private_answer_keys
    assert ai_assessment._Task is assessment_prompts.AssessmentPromptTask
    for old_name, new_name in {
        "_generation_prompt": "generation_prompt",
        "_repair_prompt": "repair_prompt",
        "_review_prompt": "review_prompt",
        "_required_awarded_entries": "required_awarded_entries",
        "_semantic_task_contract": "semantic_task_contract",
        "_review_question_payload": "review_question_payload",
        "_task_source": "task_source",
        "_demand_item": "demand_item",
        "_question_uses_option_source": "question_uses_option_source",
    }.items():
        assert getattr(ai_assessment, old_name) is getattr(assessment_prompts, new_name)


def test_sql_findings_still_require_a_declared_public_sql_contract():
    client = CapturingClient()
    with pytest.raises(
        ValueError, match="solver correction findings require a public SQL contract"
    ):
        IndependentSolver(client).solve(
            {"id": "sql", "marks": 1, "prompt": "Write a query."},
            [],
            correction_findings=[{"kind": "syntax"}],
        )
    assert client.requests == []
