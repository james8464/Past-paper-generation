from __future__ import annotations

import pytest

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.independent_solver import (
    CanonicalSolution,
    IndependentSolver,
    reconcile_solution,
)


def _calculation_item() -> dict:
    return {
        "id": "q1",
        "marks": 4,
        "prompt": "Calculate total contribution.",
        "assessment_objectives": {"AO2": 4},
        "authoring_context": {
            "calculation_expression": "(revenue - variable_cost) * units",
            "calculation_variables": {
                "revenue": 100,
                "variable_cost": 60,
                "units": 10,
            },
            "calculation_input_units": {"revenue": "GBP/unit", "variable_cost": "GBP/unit", "units": "units"},
            "calculation_output": {"role": "result", "unit": "GBP", "decimal_places": 0, "scheme_pattern": r"Answer (?P<value>\d+)"},
            "observable_mark_points": [
                "subtract variable cost from revenue",
                "multiply unit contribution by units",
            ],
        },
    }


def test_independent_solver_recomputes_arithmetic_without_the_draft_scheme() -> None:
    solution = IndependentSolver().solve(_calculation_item(), [])

    assert solution.answer_slots == {"result": "£400"}
    assert solution.numeric_results["result"] == 400
    assert "mark_scheme" not in solution.solver_context_fields

    reconciliation = reconcile_solution(
        solution,
        {
            "marks": 4,
            "points": [
                {"text": "Subtract costs", "marks": 2, "assessment_objective": "AO2"},
                {"text": "Answer 500", "marks": 2, "assessment_objective": "AO2"},
            ],
        },
    )
    assert not reconciliation.passed
    assert any(issue.field == "answer" for issue in reconciliation.issues)


def test_model_solver_prompt_excludes_nested_answer_key_and_marking_guidance() -> None:
    prompts: list[str] = []

    class Client:
        def generate_json(self, prompt: str) -> dict[str, object]:
            prompts.append(prompt)
            return {"answer": "42", "steps": ["Compute from the supplied data."]}

    IndependentSolver(Client()).solve(
        {
            "id": "q1",
            "marks": 1,
            "prompt": "Calculate the result from the supplied values.",
            "authoring_context": {
                "source_data": {"x": 6, "y": 7},
                "verified_answers": {"answer": "SECRET_ANSWER_KEY"},
                "observable_mark_points": ["SECRET_MARKING_GUIDANCE"],
            },
        },
        [],
    )

    assert "SECRET_ANSWER_KEY" not in prompts[0]
    assert "SECRET_MARKING_GUIDANCE" not in prompts[0]
    assert '"x": 6' in prompts[0]


def test_reconciliation_rejects_missing_alternative_and_partial_credit_boundary() -> (
    None
):
    solution = CanonicalSolution(
        item_id="q2",
        answer="12",
        steps=["Use either valid method"],
        mark_points=["correct method", "correct answer"],
        assessment_objectives={"AO2": 2},
        alternatives=["accept equivalent graphical method"],
        partial_credit_boundaries=["method only: maximum 1 mark"],
    )

    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "points": [
                {"text": "Correct method", "marks": 1, "assessment_objective": "AO2"},
                {"text": "Answer 12", "marks": 1, "assessment_objective": "AO2"},
            ],
        },
    )

    assert {issue.field for issue in result.issues} >= {
        "alternatives",
        "partial_credit_boundaries",
    }


def test_reconciliation_rejects_ao_misallocation() -> None:
    solution = CanonicalSolution(
        item_id="q3",
        answer="valid judgement",
        mark_points=["knowledge", "analysis", "judgement"],
        assessment_objectives={"AO1": 1, "AO3": 2},
    )

    result = reconcile_solution(
        solution,
        {
            "marks": 3,
            "points": [
                {"text": "knowledge", "marks": 2, "assessment_objective": "AO1"},
                {
                    "text": "analysis and valid judgement",
                    "marks": 1,
                    "assessment_objective": "AO3",
                },
            ],
        },
    )

    assert any(issue.field == "assessment_objectives" for issue in result.issues)


def test_solver_and_reconciliation_accept_structured_rubric_metadata() -> None:
    class Client:
        def generate_json(self, _prompt: str) -> dict[str, object]:
            return {"answer": "19.6%", "steps": ["Calculate the percentage change"], "mark_points": ["Percentage change is 19.6%"]}

    item = {
        "id": "q-structured",
        "marks": 2,
        "prompt": "Calculate the percentage change from 78.0 to 93.3.",
        "assessment_objectives": {"AO2": 2},
        "authoring_context": {
            "observable_mark_points": [
                {"point": "Correct identification of values 78.0 and 93.3", "marks": 1},
                {"point": "Correct percentage change of 19.6%", "marks": 1},
            ],
            "partial_credit_boundaries": [
                {"condition": "Correct values but arithmetic error", "score": 1}
            ],
            "follow_through_rules": [
                {"rule": "Allow a correct calculation from the candidate's values"}
            ],
        },
    }
    solution = IndependentSolver(Client()).solve(item, [])

    assert solution.mark_points == ["Percentage change is 19.6%"]
    assert solution.examiner_expectations == [
        "Correct identification of values 78.0 and 93.3",
        "Correct percentage change of 19.6%",
    ]
    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "follow_through_rules": [
                "Allow a correct calculation from the candidate's values"
            ],
            "points": [
                {
                    "text": "Identifies 78.0 and 93.3; correct values but arithmetic error",
                    "marks": 1,
                    "assessment_objective": "AO2",
                },
                {
                    "text": "Correct percentage change: 19.6%",
                    "marks": 1,
                    "assessment_objective": "AO2",
                },
            ],
        },
    )
    assert result.passed, result.issues


def test_solver_rejects_citation_to_unavailable_evidence() -> None:
    class Client:
        def generate_json(self, _prompt: str) -> dict[str, object]:
            return {
                "answer": "Exports increased.",
                "steps": ["Use source-b"],
                "mark_points": ["identifies the increase"],
                "evidence_ids": ["source-b"],
            }

    with pytest.raises(ValueError, match="unavailable evidence"):
        IndependentSolver(Client()).solve(
            {"id": "q4", "marks": 1, "prompt": "State the change."},
            [EvidenceRecord(id="source-a", text="Exports rose by 4%.")],
        )


def test_one_mark_multiple_choice_rejects_contradictory_solver_mark_point() -> None:
    class Client:
        def generate_json(self, _prompt: str) -> dict[str, object]:
            return {
                "answer": "Purchases journal",
                "mark_points": [
                    "The purchase ledger is the book of prime entry for credit purchases"
                ],
            }

    item = {
        "id": "q-mcq",
        "marks": 1,
        "kind": "multiple_choice",
        "prompt": "Which book of prime entry records credit purchases?",
        "choices": [
            "Cash book",
            "General journal",
            "Purchases journal",
            "Sales journal",
        ],
        "correct_choice": 2,
        "assessment_objectives": {"AO1": 1},
    }

    with pytest.raises(ValueError, match="closed response"):
        IndependentSolver(Client()).solve(item, [])


def test_multiple_choice_solver_hides_key_and_normalises_option_number() -> None:
    class Client:
        prompt = ""

        def generate_json(self, prompt: str) -> dict[str, object]:
            self.prompt = prompt
            return {
                "answer": "1",
                "mark_points": ["1"],
                "evidence_ids": ["q-mcq"],
            }

    client = Client()
    item = {
        "id": "q-mcq",
        "marks": 1,
        "kind": "multiple_choice",
        "prompt": "Which journal records credit purchases?",
        "choices": [
            "Purchases journal",
            "Sales journal",
            "Cash book",
            "General journal",
        ],
        "correct_choice": 0,
        "assessment_objectives": {"AO1": 1},
    }

    solution = IndependentSolver(client).solve(item, [])

    assert '"correct_choice"' not in client.prompt
    assert solution.answer == "Purchases journal"
    assert solution.mark_points == ["Purchases journal"]
    assert solution.evidence_ids == []


def test_reconciliation_accepts_concise_scheme_for_elaborated_solver_points() -> None:
    solution = CanonicalSolution(
        item_id="q-discount",
        answer=(
            "A supplier may encourage large orders and defend its market share; "
            "larger orders can raise sales volume and generate economies of scale."
        ),
        mark_points=[
            "Reason 1: To encourage bulk purchasing or large orders.",
            "Explanation 1: This increases the quantity sold per order and may improve economies of scale.",
            "Reason 2: To compete with other suppliers in the market.",
            "Explanation 2: Lower trade prices can help retain customers and market share.",
        ],
        assessment_objectives={"AO1": 2, "AO2": 2},
    )
    scheme = {
        "marks": 4,
        "points": [
            {
                "text": "Encourages customers to purchase in bulk and place larger orders.",
                "marks": 1,
                "assessment_objective": "AO1",
            },
            {
                "text": "Higher sales volume may produce economies of scale.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
            {
                "text": "Allows the supplier to compete with rival suppliers.",
                "marks": 1,
                "assessment_objective": "AO1",
            },
            {
                "text": "May retain trade customers and protect market share.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
        ],
    }

    result = reconcile_solution(solution, scheme)

    assert result.passed, result.issues


def test_reconciliation_still_rejects_unrelated_scheme_for_elaborated_answer() -> None:
    solution = CanonicalSolution(
        item_id="q-discount",
        answer="Encourage large orders and defend market share.",
        mark_points=[
            "Encourage customers to purchase in bulk.",
            "Protect market share against competing suppliers.",
        ],
        assessment_objectives={"AO1": 2},
    )

    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "points": [
                {
                    "text": "Reduces the paperwork used to process invoices.",
                    "marks": 2,
                    "assessment_objective": "AO1",
                }
            ],
        },
    )

    assert not result.passed
    assert any(issue.field == "mark_points" for issue in result.issues)


def test_open_response_solver_examples_are_not_treated_as_exhaustive() -> None:
    class Client:
        def generate_json(self, _prompt: str) -> dict[str, object]:
            return {
                "answer": (
                    "Encourage bulk orders after sales fell by 7% and remain "
                    "competitive despite liabilities of £340,000."
                ),
                "mark_points": [
                    "Encourage bulk buying or larger orders.",
                    "Build customer loyalty or maintain competitiveness.",
                ],
            }

    item = {
        "id": "q-discount",
        "marks": 2,
        "prompt": "State two reasons why a supplier may offer a trade discount.",
        "assessment_objectives": {"AO1": 2},
        "authoring_context": {"expected_answer_form": "constructed_response"},
    }
    solution = IndependentSolver(Client()).solve(item, [])

    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "points": [
                {
                    "text": "Reward prompt payment from regular trade customers.",
                    "marks": 1,
                    "assessment_objective": "AO1",
                },
                {
                    "text": "Reduce selling and administration costs per unit.",
                    "marks": 1,
                    "assessment_objective": "AO1",
                },
            ],
        },
    )

    assert not solution.mark_points_exhaustive
    assert result.passed, result.issues
# Specialist schemes can encode keyed letters instead of full option text.
def test_specialist_reconciliation_rejects_a_different_keyed_option() -> None:
    from Backend.Core.independent_solver import require_solution_matches_scheme

    solution = CanonicalSolution(item_id="q1", answer="Current ratio", mark_points=["Current ratio"])
    with pytest.raises(ValueError, match="keyed option"):
        require_solution_matches_scheme(
            solution, {"marks": 1, "mark_scheme": ["Current ratio"]},
            expected_choice="Gearing",
        )
