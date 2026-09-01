from __future__ import annotations

from copy import deepcopy

import pytest

from Backend.Core.assessment_package import _extract_items
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    SectionRule,
    resolve_question_rules,
    validate_generated_paper,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.reference_demand import (
    ReferenceDemandProfile,
    build_item_demand_target,
)
from Backend.Core.subjects.selected_response import solve_selected_response


def _complete_solver_response(**updates: object) -> dict[str, object]:
    response: dict[str, object] = {
        "steps": ["Use the candidate-visible information."],
        "answer": "A complete answer",
        "mark_points": ["A complete answer"],
        "evidence_ids": [],
        "alternatives": [],
        "partial_credit_boundaries": [],
        "follow_through_rules": [],
    }
    response.update(updates)
    return response


class _SolverClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.prompt = ""

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.prompt = prompt
        return deepcopy(self.response)


def _profile() -> ReferenceDemandProfile:
    distribution = {"low": 1.0}
    return ReferenceDemandProfile(
        family_id="economics-aqa",
        paper_id="3",
        comparison_basis="task-source-demand-test",
        source_document_count=1,
        source_fingerprint="a" * 64,
        mark_band_distribution={"1": 1.0},
        command_word_distribution={"select": 1.0},
        demand_distribution=distribution,
        mark_weighted_demand_distribution=distribution,
        response_mode_distribution={"selected-response": 1.0},
        cognitive_operation_distribution={"transform": 1.0},
        extraction_coverage=1.0,
        metric_tolerances={
            "mark_band_distribution": 1.0,
            "command_family_distribution": 1.0,
            "mark_weighted_demand_distribution": 1.0,
            "response_mode_distribution": 1.0,
            "cognitive_operation_distribution": 1.0,
        },
    )


def test_per_option_rule_resolver_hydrates_task_source_and_objectives() -> None:
    default = QuestionRule(
        id="mcq",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        assessment_objectives={"AO1": 1},
        task_operation="retrieve",
        source_dependency="none",
    )
    applied = default.model_copy(
        update={
            "assessment_objectives": {"AO2": 1},
            "task_operation": "transform",
            "source_dependency": "stem",
        }
    )
    section = SectionRule(
        id="A",
        title="Selected response",
        option_count=2,
        answer_options=2,
        option_marks=1,
        questions=[default],
        question_overrides={2: [applied]},
    )
    rule = PaperRule(
        id="paper_3",
        code="TEST/3",
        title="Test",
        duration_minutes=2,
        total_marks=2,
        allowed_topic_ids={"topic"},
        sections=[section],
    )
    options = []
    for option_index in (1, 2):
        resolved = resolve_question_rules(section, option_index)[0]
        options.append(
            GeneratedOption(
                id=f"A{option_index}",
                title=f"Question {option_index}",
                questions=[
                    GeneratedQuestion(
                        rule_id="mcq",
                        number=str(option_index),
                        marks=1,
                        kind="multiple_choice",
                        command_word="Select",
                        topic_id="topic",
                        prompt=f"Select answer {option_index}.",
                        choices=["one", "two", "three", "four"],
                        correct_choice=0,
                        mark_scheme=["Option A: one."],
                        assessment_objectives=deepcopy(resolved.assessment_objectives),
                        task_operation=resolved.task_operation,
                        source_dependency=resolved.source_dependency,
                    )
                ],
            )
        )
    paper = GeneratedPaper(
        paper_id="paper_3",
        paper_code="TEST/3",
        title="Test",
        duration_minutes=2,
        total_marks=2,
        seed=1,
        sections=[GeneratedSection(id="A", title="Selected response", instructions="Answer all.", options=options)],
    )

    validate_generated_paper(paper, rule, {"topic"})
    assert paper.sections[0].options[0].questions[0].assessment_objectives == {"AO1": 1}
    assert paper.sections[0].options[1].questions[0].assessment_objectives == {"AO2": 1}
    assert paper.sections[0].options[1].questions[0].task_operation == "transform"
    assert paper.sections[0].options[1].questions[0].source_dependency == "stem"


def test_rule_override_cannot_change_slot_identity_or_tariff() -> None:
    base = QuestionRule(id="mcq", marks=1, kind="multiple_choice", command_word="Select")
    with pytest.raises(ValueError, match="identity and tariff"):
        SectionRule(
            id="A",
            title="Selected response",
            option_count=2,
            answer_options=2,
            option_marks=1,
            questions=[base],
            question_overrides={2: [base.model_copy(update={"marks": 2})]},
        )


def test_export_preserves_explicit_task_and_source_metadata() -> None:
    item = _extract_items(
        {
            "questions": [{
                "number": "1", "marks": 1, "kind": "multiple_choice",
                "prompt": "Use Figure 1 to select the change.",
                "task_operation": "analyse", "source_dependency": "figure",
            }]
        },
        subject="Economics", paper_number="3",
    )[0]
    assert item["task_operation"] == "analyse"
    assert item["source_dependency"] == "figure"


@pytest.mark.parametrize(
    ("item", "operation", "requires_context", "transformation"),
    [
        (
            {
                "id": "definition-under-shared-source",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "Select the definition of opportunity cost.",
                "context": ["A shared extract is printed above."],
                "assessment_objectives": {"AO1": 1},
                "task_operation": "retrieve",
                "source_dependency": "none",
            },
            "retrieve",
            False,
            False,
        ),
        (
            {
                "id": "index-transform",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "An index of 100 rises by 8%. Select the new value.",
                "assessment_objectives": {"AO2": 1},
                "task_operation": "transform",
                "source_dependency": "stem",
            },
            "transform",
            True,
            True,
        ),
        (
            {
                "id": "diagram-recognition",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "Use Figure 1 to select the shifted curve.",
                "assessment_objectives": {"AO1": 1},
                "task_operation": "analyse",
                "source_dependency": "figure",
                "source_references": ["Figure 1"],
            },
            "analyse",
            True,
            False,
        ),
    ],
)
def test_declared_task_work_not_tariff_or_source_presence_drives_target(
    item: dict[str, object],
    operation: str,
    requires_context: bool,
    transformation: bool,
) -> None:
    target = build_item_demand_target(item, _profile())

    assert target.response_mode == "selected-response"
    assert target.required_cognitive_operations[0] == operation
    assert target.requires_context is requires_context
    assert target.requires_data_transformation is transformation


def test_selected_response_index_is_derived_from_public_inputs_not_key() -> None:
    item = {
        "id": "index",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["92.0", "108.0", "113.0", "8.0"],
        "correct_choice": 1,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "index_percentage_increase",
                "inputs": {"base": "100", "rate_percent": "8"},
                "unit": "index",
                "decimal_places": 1,
            }
        },
    }

    result = solve_selected_response(item)
    assert result is not None
    assert result["answer"] == "108.0"
    assert result["mark_points"] == ["108.0"]
    mutated = deepcopy(item)
    mutated["correct_choice"] = 0
    assert solve_selected_response(mutated)["answer"] == "108.0"


def test_selected_response_rejects_semantically_duplicate_numeric_options() -> None:
    item = {
        "id": "index",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["92.0", "108.0", "108", "113.0"],
        "correct_choice": 1,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "index_percentage_increase",
                "inputs": {"base": "100", "rate_percent": "8"},
                "unit": "index",
                "decimal_places": 1,
            }
        },
    }

    with pytest.raises(ValueError, match="exactly one semantic option"):
        solve_selected_response(item)


def test_money_selected_response_rejects_a_malformed_distractor() -> None:
    item = {
        "id": "profit",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["£3m", "£10m", "£14m", "£7m or £8m"],
        "correct_choice": 0,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "after_tax_profit",
                "inputs": {
                    "revenue": "20",
                    "cost_of_sales": "6",
                    "operating_expenses": "4",
                    "taxation": "7",
                },
                "unit": "GBPm",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="exactly one semantic option"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    "mutation",
    [
        ("missing", "evidence_ids", None),
        ("extra", "confidence", 0.9),
        ("wrong_type", "mark_points", {"point": "A complete answer"}),
        ("wrong_type", "alternatives", "none"),
    ],
)
def test_open_solver_requires_the_literal_raw_response_envelope(mutation) -> None:
    action, field, value = mutation
    response = _complete_solver_response()
    if action == "missing":
        del response[field]
    else:
        response[field] = value
    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(_SolverClient(response)).solve(
            {"id": "open", "marks": 2, "prompt": "Explain the effect."}, []
        )


def test_solver_prompt_declares_all_raw_fields_and_blind_payload() -> None:
    client = _SolverClient(_complete_solver_response())
    IndependentSolver(client).solve(
        {
            "id": "open",
            "marks": 2,
            "prompt": "Explain the effect of the public input.",
            "correct_choice": 3,
            "mark_scheme": ["PRIVATE KEY"],
            "candidate_source": {
                "selected_response_contract": {
                    "version": "selected-response-v1",
                    "operation": "index_percentage_increase",
                    "inputs": {"base": "100", "rate_percent": "8"},
                    "unit": "index",
                    "decimal_places": 1,
                },
            },
            "authoring_context": {
                "verified_answers": {"answer": "PRIVATE ANSWER"},
            },
        },
        [],
    )
    for field in (
        "steps", "answer", "mark_points", "evidence_ids", "alternatives",
        "partial_credit_boundaries", "follow_through_rules",
    ):
        assert f'"{field}"' in client.prompt
    assert "selected_response_contract" in client.prompt
    assert '"base": "100"' in client.prompt
    assert "PRIVATE KEY" not in client.prompt
    assert "PRIVATE ANSWER" not in client.prompt
    assert '"correct_choice"' not in client.prompt
