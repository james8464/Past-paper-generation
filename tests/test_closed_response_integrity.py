from __future__ import annotations

import json

import pytest

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution


class ResponseClient:
    def __init__(self, response):
        self.response = response
        self.prompt = ""

    def generate_json(self, prompt):
        self.prompt = prompt
        return self.response


def closed_item(slots=("1", "2")):
    return {
        "id": "closed",
        "marks": len(slots),
        "response_slots": list(slots),
        "prompt": "Complete the labelled blanks.",
        "marking": {"closed_answers": {"1": ["SECRET_KEY"]}},
    }


def scheme():
    return {
        "marks": 2,
        "mark_scheme": ["Application software", "Utility software"],
        "closed_answers": {
            "1": ["Application software", "applications"],
            "2": ["Utility software"],
        },
    }


def test_captured_duplicate_partial_points_cannot_pass_closed_classification():
    # Minimal captured live response: wrong answer plus duplicate partial credit.
    client = ResponseClient(
        {
            "answer": "System software, Application software",
            "mark_points": [
                {
                    "point": 1,
                    "description": "Award 1 mark if 'Application software' is named.",
                },
                {
                    "point": 2,
                    "description": "Award 1 mark if 'Application software' is named.",
                },
            ],
            "evidence_ids": [],
            "alternatives": [],
        }
    )
    with pytest.raises(ValueError, match="closed response"):
        IndependentSolver(client).solve(closed_item(), [])


@pytest.mark.parametrize(
    "answers",
    [
        {"1": "System software", "2": "Application software"},
        {"1": "Application software", "2": "Application software"},
        {"1": "Utility software", "2": "Application software"},
        {"1": "Application software or System software", "2": "Utility software"},
        {"1": "Application software", "2": "Operating system"},
    ],
)
def test_closed_reconciliation_rejects_wrong_duplicate_swapped_and_ambiguous_values(
    answers,
):
    solution = IndependentSolver(
        ResponseClient({"answer": answers, "mark_points": answers})
    ).solve(closed_item(), [])
    assert not reconcile_solution(solution, scheme()).passed


@pytest.mark.parametrize(
    "response",
    [
        {
            "answer": {"1": "Application software"},
            "mark_points": {"1": "Application software"},
        },
        {"answer": {"1": "Application software", "2": "Utility software"}},
        {"mark_points": {"1": "Application software", "2": "Utility software"}},
        {
            "answer": {"1": "Application software", "2": "Utility software"},
            "mark_points": {"1": "Application software", "2": "Application software"},
        },
        {
            "answer": {
                "1": "Application software",
                "2": "Utility software",
                "3": "Extra",
            },
            "mark_points": {"1": "Application software", "2": "Utility software"},
        },
    ],
)
def test_closed_solver_rejects_missing_extra_and_contradictory_fields(response):
    with pytest.raises(ValueError, match="closed response"):
        IndependentSolver(ResponseClient(response)).solve(closed_item(), [])


@pytest.mark.parametrize("first", ["Application software", "applications"])
def test_closed_slots_accept_only_declared_synonyms_and_hide_the_key(first):
    answers = {"2": "Utility software", "1": first}
    client = ResponseClient({"answer": answers, "mark_points": answers})
    solution = IndependentSolver(client).solve(closed_item(), [])
    assert reconcile_solution(solution, scheme()).passed
    payload = json.loads(client.prompt.split("\n", 1)[1])
    assert payload["item"]["response_slots"] == ["1", "2"]
    assert "SECRET_KEY" not in client.prompt


@pytest.mark.parametrize(
    "answers",
    [
        {"row-1": "0", "row-2": "1", "row-3": "0", "row-4": "1"},
        {"before": "8 bytes", "after": "6 bytes"},
    ],
)
def test_closed_numeric_and_truth_rows_compare_by_slot_not_number_bag(answers):
    solution = IndependentSolver(
        ResponseClient({"answer": answers, "mark_points": answers})
    ).solve(closed_item(tuple(answers)), [])
    accepted = {slot: [value] for slot, value in answers.items()}
    assert reconcile_solution(solution, {"closed_answers": accepted}).passed
    swapped = dict(zip(accepted, reversed(list(accepted.values())), strict=True))
    assert not reconcile_solution(solution, {"closed_answers": swapped}).passed


def test_closed_solution_cannot_fall_back_to_prose_when_slot_key_is_missing():
    answers = {"1": "Application software", "2": "Utility software"}
    solution = IndependentSolver(
        ResponseClient({"answer": answers, "mark_points": answers})
    ).solve(closed_item(), [])
    assert not reconcile_solution(
        solution, {"mark_scheme": list(answers.values())}
    ).passed


@pytest.mark.parametrize(
    "response",
    [
        {"answer": "Not Purchases journal", "mark_points": ["Purchases journal"]},
        {
            "answer": "Purchases journal or Sales journal",
            "mark_points": ["Purchases journal"],
        },
        {"answer": "Purchases journal", "mark_points": ["Sales journal"]},
        {
            "answer": "Purchases journal",
            "mark_points": ["Purchases journal", "Purchases journal"],
        },
        {"answer": "Purchases journal"},
    ],
)
def test_multiple_choice_never_discards_wrong_duplicate_or_missing_response_fields(
    response,
):
    item = {
        "id": "choice",
        "kind": "multiple_choice",
        "marks": 1,
        "choices": [
            "Purchases journal",
            "Sales journal",
            "Cash book",
            "General journal",
        ],
    }
    with pytest.raises(ValueError, match="closed response"):
        IndependentSolver(ResponseClient(response)).solve(item, [])


def test_specialist_mcq_uses_the_shared_closed_slot_contract():
    from Backend.Core.independent_solver import require_solution_matches_scheme

    item = {
        **closed_item(("choice",)),
        "kind": "multiple_choice",
        "marks": 1,
        "choices": ["Stack", "Queue"],
    }
    answer = {"choice": "Stack"}
    solution = IndependentSolver(
        ResponseClient({"answer": answer, "mark_points": answer})
    ).solve(item, [])
    require_solution_matches_scheme(solution, {}, expected_choice="Stack")
    with pytest.raises(ValueError, match="slot choice"):
        require_solution_matches_scheme(solution, {}, expected_choice="Queue")


def test_production_hosted_chat_preserves_closed_answer_objects(monkeypatch):
    from io import BytesIO

    from Backend.Core.providers import HostedLLMClient

    answer = {"1": "applications", "2": "Utility software"}
    calls = []

    def request(url, data, headers, *, attempts):
        calls.append((url, json.loads(data)))
        return BytesIO(
            json.dumps(
                {
                    "message": {
                        "content": json.dumps({"answer": answer, "mark_points": answer})
                    }
                }
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.providers.urllib_request", request)
    client = HostedLLMClient(provider="ollama", model="test-model", api_key="")
    solution = IndependentSolver(client).solve(closed_item(), [])
    assert reconcile_solution(solution, scheme()).passed
    assert calls[0][0].endswith("/api/chat")
    schema = calls[0][1]["format"]
    assert schema["required"] == ["steps", "answer", "mark_points"]
    assert next(iter(schema["properties"])) == "steps"
    for field in ("answer", "mark_points"):
        slots = schema["properties"][field]
        assert slots["required"] == ["1", "2"]
        assert slots["additionalProperties"] is False
        assert slots["properties"]["1"]["type"] == "string"
        assert slots["properties"]["2"]["type"] == "string"


def test_closed_scheme_rejects_legacy_solution_that_has_lost_its_slot_contract():
    from Backend.Core.independent_solver import CanonicalSolution

    solution = CanonicalSolution(
        item_id="legacy",
        answer="System software, Application software",
        mark_points=["Application software", "Application software"],
        mark_points_exhaustive=False,
    )
    assert not reconcile_solution(solution, scheme()).passed


@pytest.mark.parametrize(
    "raw",
    [
        '{"answer":{"1":"System software","1":"Application software","2":"Utility software"}}',
        '{"answer":"Wrong","answer":"Right"}',
    ],
)
def test_provider_rejects_duplicate_json_fields_instead_of_silently_overwriting(raw):
    from Backend.Core.providers import parse_json_object

    with pytest.raises(ValueError, match="duplicate"):
        parse_json_object(raw)


def test_shared_live_mcq_reconciliation_rejects_lexically_similar_wrong_option():
    item = {
        "id": "choice",
        "kind": "multiple_choice",
        "marks": 1,
        "choices": ["Higher costs increase supply", "Higher costs decrease supply"],
        "correct_choice": 1,
        "mark_scheme": ["Higher costs decrease supply"],
    }
    response = {
        "answer": "Higher costs increase supply",
        "mark_points": ["Higher costs increase supply"],
    }
    solution = IndependentSolver(ResponseClient(response)).solve(item, [])
    assert not reconcile_solution(solution, item).passed


def test_persisted_closed_solution_cannot_disagree_with_its_answer_fields():
    answer = {"1": "Application software", "2": "Utility software"}
    solution = IndependentSolver(
        ResponseClient({"answer": answer, "mark_points": answer})
    ).solve(closed_item(), [])
    contradictory = solution.model_copy(
        update={"answer": "System software, Application software"}
    )
    assert not reconcile_solution(contradictory, scheme()).passed


@pytest.mark.parametrize("wrong", ["2.75", "-275", "-2.75 or 2.75"])
def test_closed_numeric_slots_preserve_sign_and_decimal_point(wrong):
    response = {"result": wrong}
    solution = IndependentSolver(
        ResponseClient({"answer": response, "mark_points": response})
    ).solve(closed_item(("result",)), [])
    assert not reconcile_solution(
        solution, {"closed_answers": {"result": ["-2.75"]}}
    ).passed


def test_specialist_choice_key_comparison_preserves_numeric_sign():
    from Backend.Core.independent_solver import (
        CanonicalSolution,
        require_solution_matches_scheme,
    )

    solution = CanonicalSolution(item_id="mcq", answer="2.75", mark_points=["2.75"])
    with pytest.raises(ValueError, match="keyed option"):
        require_solution_matches_scheme(
            solution, {"mark_scheme": ["2.75"]}, expected_choice="-2.75"
        )


@pytest.mark.parametrize(
    "answer", ["36 kHz", "36kHz", "36000 Hz", "36000Hz", "36 000 Hz"]
)
def test_closed_numeric_contract_keeps_accepted_frequency_unit_formats(answer):
    values = {"result": answer}
    solution = IndependentSolver(
        ResponseClient({"answer": values, "mark_points": values})
    ).solve(closed_item(("result",)), [])
    assert reconcile_solution(
        solution, {"closed_answers": {"result": ["36 kHz", "36000 Hz", "36 000 Hz"]}}
    ).passed


@pytest.mark.parametrize("answer", ["36 Hz", "36000 kHz", "36MHz", "18 kHz"])
def test_closed_numeric_contract_rejects_wrong_frequency_value_or_scale(answer):
    values = {"result": answer}
    solution = IndependentSolver(
        ResponseClient({"answer": values, "mark_points": values})
    ).solve(closed_item(("result",)), [])
    assert not reconcile_solution(
        solution, {"closed_answers": {"result": ["36 kHz", "36000 Hz", "36 000 Hz"]}}
    ).passed


def test_closed_slot_schema_survives_provider_json_repair_instruction():
    from Backend.Core.providers import _ollama_json_schema

    client = ResponseClient(
        {"answer": {"1": "a", "2": "b"}, "mark_points": {"1": "a", "2": "b"}}
    )
    IndependentSolver(client).solve(closed_item(), [])
    schema = _ollama_json_schema(
        client.prompt + "\n\nREPAIR INSTRUCTION: Return valid JSON."
    )
    assert schema["properties"]["answer"]["required"] == ["1", "2"]


@pytest.mark.parametrize(
    "response",
    [
        {
            "answer": {"1": "Application software", "2": "System software"},
            "mark_points": {
                "1": {"aw": "Application software"},
                "2": {"aw": "System software"},
            },
        },
        {
            "answer": {"result": "20.75MiB"},
            "steps": ["25920000 / 1048576 = 24.71923828125"],
            "mark_points": {
                "result": "Award credit for a correct file size calculation"
            },
        },
        {
            "answer": {"row-1": "0", "row-2": "1", "row-3": "1", "row-4": "1"},
            "steps": ["Row 3 evaluates to 0"],
            "extraNote": "Complete",
        },
    ],
)
def test_live_app_probe_malformed_or_contradictory_answers_remain_rejected(response):
    with pytest.raises(ValueError, match="closed response"):
        IndependentSolver(ResponseClient(response)).solve(
            closed_item(tuple(response["answer"])), []
        )
