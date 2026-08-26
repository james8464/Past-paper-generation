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
            "observable_mark_points": [
                "subtract variable cost from revenue",
                "multiply unit contribution by units",
            ],
        },
    }


def test_independent_solver_recomputes_arithmetic_without_the_draft_scheme() -> None:
    solution = IndependentSolver().solve(_calculation_item(), [])

    assert solution.answer == "400"
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
