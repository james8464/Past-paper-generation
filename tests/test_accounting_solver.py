from __future__ import annotations

from pathlib import Path

import pytest
from aqaaccountgen.case_data import NonCurrentAssetCase, PartnershipCase
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution

SYLLABUS = load_syllabus(
    Path(__file__).resolve().parents[1]
    / "Resources/accounting/aqa/generator/data/syllabus.json"
)


class NoModelArithmetic:
    def generate_json(self, _prompt: str) -> dict[str, object]:
        raise AssertionError("closed accounting calculations must use source-data arithmetic")


@pytest.mark.parametrize("seed", [123, 26080100, 26083031])
def test_closed_accounting_solutions_ignore_the_draft_answer_key(seed: int) -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, seed)
    rules = {
        "statement_extract",
        "ledger_calculation",
        "accounting_concept",
        "company_statement",
        "partnership_1",
        "partnership_2",
    }
    for section in paper.sections:
        for option in section.options:
            for question in option.questions:
                if question.rule_id not in rules:
                    continue
                raw = question.model_dump(mode="json")
                raw["authoring_context"]["verified_answers"] = {"incorrect": -999}
                solution = IndependentSolver(NoModelArithmetic()).solve(raw, [])
                assert solution.numeric_results
                assert -999 not in solution.numeric_results.values()
                result = reconcile_solution(
                    solution,
                    {
                        "marks": question.marks,
                        "points": [
                            point.model_dump(mode="json")
                            for point in question.structured_mark_scheme
                        ],
                    },
                )
                assert result.passed, (question.number, result.issues)


def test_asset_depreciation_does_not_silently_round_to_hundreds() -> None:
    case = NonCurrentAssetCase(
        business="Example",
        plant_cost_opening=106_200,
        plant_accumulated_depreciation_opening=31_900,
        plant_purchase=19_000,
        motor_cost_opening=124_400,
        motor_accumulated_depreciation_opening=43_500,
        motor_disposal_cost=18_100,
        motor_disposal_accumulated_depreciation=10_900,
    )

    assert case.plant_depreciation_charge == 12_520
    assert case.motor_depreciation_charge == 14_740
    assert case.total_carrying_amount == 139_740


def test_seeded_partnership_allocations_balance_without_rounding_losses() -> None:
    for seed in range(30):
        paper = build_paper(RULES["paper_1"], SYLLABUS, seed)
        option = paper.sections[1].options[0]
        case = PartnershipCase.from_chart_values(option.chart_values)
        assert sum(case.goodwill_credit.values()) == case.goodwill
        assert sum(case.goodwill_write_off.values()) == case.goodwill
        for period in case.appropriation_by_period().values():
            assert sum(period["residual_profit_shares"].values()) == period["residual_profit"]
