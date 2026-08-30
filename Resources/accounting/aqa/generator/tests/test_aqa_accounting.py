from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pymupdf as fitz
import pytest
from aqaaccountgen import case_data
from aqaaccountgen.case_data import (
    CostingCase,
    IncomeStatementCase,
    NonCurrentAssetCase,
    PartnershipCase,
    SalesLedgerCase,
    ShareholderCase,
)
from aqaaccountgen.cli import generate_package
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus
from pypdf import PdfReader

from Backend.Core.independent_solver import CanonicalSolution, reconcile_solution

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")
EXPECTED = {
    "paper_1": [1] * 10 + [6, 7, 5, 2, 14, 6, 6, 8, 6, 25, 25],
    "paper_2": [1] * 10 + [3, 6, 3, 8, 4, 8, 2, 6, 8, 1, 5, 6, 25, 25],
}


def test_shareholder_case_exposes_candidate_visible_source_contract() -> None:
    assert getattr(case_data, "ShareholderCase", None) is not None


def test_shareholder_case_keeps_equity_and_investor_figures_in_consistent_units() -> None:
    case = ShareholderCase(
        business="Cedar Components plc",
        nominal_share_value_pence=50,
        opening_ordinary_shares=5_000_000,
        bonus_shares_issued=1_000_000,
        opening_share_premium_thousands=1_600,
        opening_retained_earnings_thousands=4_000,
        revaluation_reserve_increase_thousands=600,
        profit_for_year_thousands=1_200,
        dividends_paid_thousands=240,
        share_price_start_pence=150,
        share_price_end_pence=180,
        long_term_borrowings_thousands=4_000,
        comparator_name="Northbridge plc",
        comparator_share_price_pence=156,
        comparator_earnings_per_share_pence=24.0,
        comparator_dividend_per_share_pence=5.0,
        comparator_long_term_borrowings_thousands=2_400,
        comparator_total_equity_thousands=9_600,
    )

    assert case.ordinary_share_capital_opening_thousands == 2_500
    assert case.bonus_issue_capital_thousands == 500
    assert case.ordinary_share_capital_closing_thousands == 3_000
    assert case.share_premium_closing_thousands == 1_100
    assert case.retained_earnings_closing_thousands == 4_960
    assert case.total_equity_closing_thousands == 9_660
    assert case.earnings_per_share_pence == 20.0
    assert case.dividend_per_share_pence == 4.0
    assert case.price_earnings_ratio == 9.0
    assert case.dividend_yield_percent == 2.2
    assert case.gearing_percent == 29.3


def test_shareholder_question_uses_the_same_visible_case_for_generator_context() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26083107)
    option = paper.sections[-1].options[0]
    question = next(item for item in option.questions if item.rule_id == "decision_2")
    case = ShareholderCase.from_chart_values(option.title, option.chart_values)

    assert question.authoring_context["candidate_source"] == case.candidate_source()
    assert question.authoring_context["source_data"] == case.candidate_source()
    assert "verified_answers" not in question.authoring_context
    assert "price_earnings_ratio" not in question.authoring_context["candidate_source"]
    assert "dividend_yield_percent" not in question.authoring_context["candidate_source"]


def test_shareholder_visible_source_reaches_reviewer_and_solver_without_answer_keys() -> None:
    from Backend.Core.ai_assessment import _Task, _task_source
    from Backend.Core.independent_solver import IndependentSolver

    class CapturingSolver:
        payload: dict[str, object]

        def generate_json(self, prompt: str) -> dict[str, object]:
            self.payload = json.loads(prompt.rsplit("\n", 1)[-1])
            return {"answer": "A conditional retain-or-sell judgement.", "evidence_ids": []}

    paper = build_paper(RULES["paper_1"], SYLLABUS, 26083108)
    option = paper.sections[-1].options[0]
    question = next(item for item in option.questions if item.rule_id == "decision_2")
    visible_source = question.authoring_context["candidate_source"]
    task = _Task(key=(2, 0, 1), question=question, option=option, topic=None)
    reviewer_source = _task_source(task)
    client = CapturingSolver()

    IndependentSolver(client).solve(question, [])

    assert reviewer_source["question_context"]["candidate_source"] == visible_source
    solver_item = client.payload["item"]
    assert solver_item["authoring_context"]["candidate_source"] == visible_source
    assert "mark_scheme" not in solver_item
    assert "verified_answers" not in solver_item["authoring_context"]
    assert (
        "closing_total_equity"
        not in solver_item["authoring_context"]["candidate_source"]
        ["statement_of_changes_in_equity"]
    )


def test_shareholder_pdf_source_and_scheme_preserve_the_complete_visible_contract(
    tmp_path: Path,
) -> None:
    seed = 26083112
    paper = build_paper(RULES["paper_1"], SYLLABUS, seed)
    option = paper.sections[-1].options[0]
    case = ShareholderCase.from_chart_values(option.title, option.chart_values)
    source = case.candidate_source()
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=seed,
    )

    source_page = next(
        page
        for page in PdfReader(paths["question_paper"]).pages
        if "Statement of changes in equity" in (page.extract_text() or "")
    )
    source_text = re.sub(r"\s+", " ", source_page.extract_text() or "")
    scheme_text = re.sub(
        r"\s+",
        " ",
        " ".join(page.extract_text() or "" for page in PdfReader(paths["mark_scheme"]).pages),
    )

    assert "closing_total_equity" not in source["statement_of_changes_in_equity"]
    for visible_value in (
        case.business,
        f"{case.nominal_share_value_pence}p",
        f"{case.opening_ordinary_shares:,}",
        f"{case.bonus_shares_issued:,}",
        f"{case.share_price_start_pence}p",
        f"{case.share_price_end_pence}p",
        f"{case.earnings_per_share_pence:.1f}p",
        f"{case.dividend_per_share_pence:.1f}p",
        f"{case.long_term_borrowings_thousands:,} (£000)",
        case.comparator_name,
        f"{case.comparator_share_price_pence}p",
        f"{case.comparator_earnings_per_share_pence:.1f}p",
        f"{case.comparator_dividend_per_share_pence:.1f}p",
        f"{case.comparator_long_term_borrowings_thousands:,} (£000)",
        f"{case.comparator_total_equity_thousands:,} (£000)",
    ):
        assert visible_value in source_text
    for evidence in source["qualitative_evidence"]:
        assert evidence in source_text
    for point in case.mark_scheme_points():
        assert point in scheme_text

    rendered = fitz.open(paths["question_paper"])
    page = next(page for page in rendered if "Statement of changes in equity" in page.get_text())
    header_words = page.get_text("words")
    ordinary = next(word for word in header_words if word[4] == "Ordinary")
    premium = next(word for word in header_words if word[4] == "premium")
    assert ordinary[2] < premium[0]
    rectangles = [drawing["rect"] for drawing in page.get_drawings()]
    source_panel_right = max(
        rect.x1
        for rect in rectangles
        if 520 < rect.x0 < 540 and rect.height > 500
    )
    equity_table_right = max(
        rect.x1
        for rect in rectangles
        if 200 < rect.y0 < 300 and rect.width > 400
    )
    assert equity_table_right <= source_panel_right


def test_shareholder_cases_vary_deterministically_and_keep_bonus_premium_non_negative() -> None:
    cases = []
    for seed in (26083109, 26083110, 26083111):
        paper = build_paper(RULES["paper_1"], SYLLABUS, seed)
        option = paper.sections[-1].options[0]
        cases.append(ShareholderCase.from_chart_values(option.title, option.chart_values))

    assert len({repr(case.candidate_source()) for case in cases}) == 3
    for case in cases:
        source = case.candidate_source()
        equity = source["statement_of_changes_in_equity"]
        opening_shares = source["opening_ordinary_shares"]
        bonus_shares = source["bonus_shares_issued"]
        nominal_value = source["nominal_share_value_pence"]
        closing_shares = opening_shares + bonus_shares

        assert equity["bonus_issue_capital_transfer"] == bonus_shares * nominal_value // 100_000
        assert equity["closing_share_premium"] >= 0
        published_total_equity = sum(
            equity[column]
            for column in (
                "closing_ordinary_share_capital",
                "closing_share_premium",
                "revaluation_increase",
                "closing_retained_earnings",
            )
        )
        assert published_total_equity == case.total_equity_closing_thousands
        assert source["market_data"]["earnings_per_share"] == round(
            equity["profit_for_year"] * 100_000 / closing_shares,
            1,
        )
        assert source["market_data"]["dividend_per_share"] == round(
            equity["dividends_paid"] * 100_000 / closing_shares,
            1,
        )


@pytest.mark.parametrize(
    "page_builder",
    [
        "_levels_with_indicative_scheme_page",
        "_indicative_content_page",
        "_extended_indicative_content_page",
    ],
)
def test_indicative_rows_preserve_explicit_objectives_without_inventing_labels(
    page_builder: str,
) -> None:
    from aqaaccountgen import render_pdf
    from reportlab.platypus import Table

    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    question = paper.sections[-1].options[0].questions[-1].model_copy(
        update={
            "mark_scheme": [
                "AO1: Explain the meaning of dividend yield.",
                "AO4: Justify the recommendation against the investor's needs.",
                "AO2/AO3: Apply and interpret the supplied figures.",
                "AO2: Use the company's financial evidence.",
                "Consider another valid approach.",
            ]
        }
    )
    flowables = getattr(render_pdf, page_builder)(question, "Question 17")
    expected = {
        "AO1: Explain the meaning of dividend yield.": "AO1",
        "AO4: Justify the recommendation against the investor's needs.": "AO4",
        "AO2/AO3: Apply and interpret the supplied figures.": "AO2/AO3",
        "AO2: Use the company's financial evidence.": "AO2",
        "Consider another valid approach.": "—",
    }
    checked = set()
    for table in (item for item in flowables if isinstance(item, Table)):
        for row in table._cellvalues[1:]:
            text = (
                row[0].getPlainText()
                if hasattr(row[0], "getPlainText")
                else str(row[0])
            )
            if text not in expected:
                continue
            label = (
                row[1].getPlainText()
                if hasattr(row[1], "getPlainText")
                else str(row[1])
            )
            assert label == expected[text]
            checked.add(text)
    assert checked == set(expected)


def page_count(path: Path) -> int:
    text = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True
    ).stdout
    return int(next(line.split(":", 1)[1] for line in text.splitlines() if line.startswith("Pages:")))


def test_exact_current_mark_sequences_and_totals() -> None:
    for key, rule in RULES.items():
        generated = build_paper(rule, SYLLABUS, 123)
        sequence = [
            question.marks
            for section in generated.sections
            for option in section.options
            for question in option.questions
        ]
        assert sequence == EXPECTED[key]
        assert sum(section.option_marks for section in rule.sections) == 120


def test_multi_seed_determinism_uniqueness_and_scope() -> None:
    for rule in RULES.values():
        papers = [build_paper(rule, SYLLABUS, seed) for seed in range(20)]
        assert build_paper(rule, SYLLABUS, 7) == build_paper(rule, SYLLABUS, 7)
        fingerprints = {
            hashlib.sha256(
                json.dumps(paper.model_dump(), sort_keys=True).encode()
            ).hexdigest()
            for paper in papers
        }
        assert len(fingerprints) == 20
        assert {
            question.topic_id
            for paper in papers
            for section in paper.sections
            for option in section.options
            for question in option.questions
        } == rule.allowed_topic_ids


def test_non_current_asset_question_and_scheme_share_verified_case_data() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    option = generated.sections[0].options[0]
    question = next(
        item
        for section in generated.sections
        for item in section.options[0].questions
        if item.rule_id == "statement_extract"
    )
    case = NonCurrentAssetCase.from_chart_values(option.title, option.chart_values)

    assert question.topic_id == "accounting-6"
    assert question.authoring_context["verified_answers"] == {
        "plant_cost": case.plant_cost_closing,
        "plant_accumulated_depreciation": (
            case.plant_accumulated_depreciation_closing
        ),
        "plant_carrying_amount": case.plant_carrying_amount,
        "motor_cost": case.motor_cost_closing,
        "motor_accumulated_depreciation": (
            case.motor_accumulated_depreciation_closing
        ),
        "motor_carrying_amount": case.motor_carrying_amount,
        "total_carrying_amount": case.total_carrying_amount,
    }
    assert case.total_carrying_amount == (
        case.plant_carrying_amount + case.motor_carrying_amount
    )


def test_locked_calculation_schemes_are_exactly_derived_from_the_case_data() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    questions = {
        question.rule_id: (question, option)
        for section in generated.sections
        for option in section.options
        for question in option.questions
    }
    assets_option = questions["statement_extract"][1]
    ledger_option = questions["ledger_calculation"][1]
    statement_option = questions["company_statement"][1]
    partnership_option = questions["partnership_1"][1]
    assets = NonCurrentAssetCase.from_chart_values(
        assets_option.title, assets_option.chart_values
    )
    ledger = SalesLedgerCase.from_chart_values(
        ledger_option.title, ledger_option.chart_values
    )
    statement = IncomeStatementCase.from_chart_values(
        statement_option.title, statement_option.chart_values
    )
    partnership = PartnershipCase.from_chart_values(partnership_option.chart_values)

    expected = {
        "statement_extract": assets.mark_scheme_points(),
        "ledger_calculation": ledger.ledger_mark_scheme_points(),
        "accounting_concept": ledger.sales_account_mark_scheme_points(),
        "company_statement": statement.mark_scheme_points(),
        "partnership_1": partnership.retirement_mark_scheme_points(),
        "partnership_2": partnership.appropriation_mark_scheme_points(),
    }
    for rule_id, mark_points in expected.items():
        question = questions[rule_id][0]
        assert question.mark_scheme[: len(mark_points)] == mark_points
        assert question.authoring_context["observable_mark_points"] == mark_points
        assert len(mark_points) == question.marks


def test_locked_calculation_schemes_include_final_answers_and_all_case_numbers() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    questions = {
        question.rule_id: (question, option)
        for section in generated.sections
        for option in section.options
        for question in option.questions
    }
    assets_option = questions["statement_extract"][1]
    ledger_option = questions["ledger_calculation"][1]
    statement_option = questions["company_statement"][1]
    partnership_option = questions["partnership_1"][1]
    assets = NonCurrentAssetCase.from_chart_values(
        assets_option.title, assets_option.chart_values
    )
    ledger = SalesLedgerCase.from_chart_values(
        ledger_option.title, ledger_option.chart_values
    )
    statement = IncomeStatementCase.from_chart_values(
        statement_option.title, statement_option.chart_values
    )
    partnership = PartnershipCase.from_chart_values(partnership_option.chart_values)

    assert f"£{assets.total_carrying_amount:,}" in " ".join(
        questions["statement_extract"][0].mark_scheme
    )
    assert f"£{ledger.closing_receivables:,}" in " ".join(
        questions["ledger_calculation"][0].mark_scheme
    )
    assert f"£{ledger.net_sales:,}" in " ".join(
        questions["accounting_concept"][0].mark_scheme
    )
    assert f"£{statement.profit_for_year:,}" in " ".join(
        questions["company_statement"][0].mark_scheme
    )
    for amount in partnership.target_capital.values():
        assert f"£{amount:,}" in " ".join(questions["partnership_1"][0].mark_scheme)
    for period in partnership.appropriation_by_period().values():
        assert f"£{period['residual_profit']:,}" in " ".join(
            questions["partnership_2"][0].mark_scheme
        )


def test_asset_scheme_reconciles_with_an_independent_exact_solution() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    option = generated.sections[0].options[0]
    question = next(
        item for item in option.questions if item.rule_id == "statement_extract"
    )
    case = NonCurrentAssetCase.from_chart_values(option.title, option.chart_values)
    solution = CanonicalSolution(
        item_id=question.number,
        answer=(
            f"Plant and machinery: £{case.plant_carrying_amount:,}\n"
            f"Motor vehicles: £{case.motor_carrying_amount:,}\n"
            f"Total non-current assets: £{case.total_carrying_amount:,}\n"
            f"Plant accumulated depreciation: £{case.plant_accumulated_depreciation_opening:,} "
            f"+ £{case.plant_depreciation_charge:,} = "
            f"£{case.plant_accumulated_depreciation_closing:,}\n"
            f"Motor accumulated depreciation before charge: "
            f"£{case.motor_accumulated_depreciation_opening:,} − "
            f"£{case.motor_disposal_accumulated_depreciation:,} = "
            f"£{case.motor_accumulated_depreciation_before_charge:,}"
        ),
        steps=[],
        mark_points=[
            f"plant cost after purchase £{case.plant_cost_closing:,}",
            f"plant depreciation £{case.plant_depreciation_charge:,}",
            (
                "plant opening accumulated depreciation "
                f"£{case.plant_accumulated_depreciation_opening:,}"
            ),
            f"plant carrying amount £{case.plant_carrying_amount:,}",
            f"motor cost after disposal £{case.motor_cost_closing:,}",
            f"motor depreciation £{case.motor_depreciation_charge:,}",
            (
                "motor opening accumulated depreciation "
                f"£{case.motor_accumulated_depreciation_opening:,}"
            ),
            f"motor carrying amount £{case.motor_carrying_amount:,}",
            f"total non-current assets £{case.total_carrying_amount:,}",
        ],
        assessment_objectives={"AO2": question.marks},
        mark_points_exhaustive=True,
    )

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

    assert result.passed, result.issues


def test_company_and_partnership_schemes_expose_complete_working_data() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26083031)
    questions = {
        question.rule_id: (question, option)
        for section in generated.sections
        for option in section.options
        for question in option.questions
    }
    company_question, company_option = questions["company_statement"]
    retirement_question, partnership_option = questions["partnership_1"]
    appropriation_question = questions["partnership_2"][0]
    company = IncomeStatementCase.from_chart_values(
        company_option.title, company_option.chart_values
    )
    partnership = PartnershipCase.from_chart_values(partnership_option.chart_values)

    adjustment_data = company_question.authoring_context["adjustment_source_data"]
    assert adjustment_data["new_debenture"] == company.new_debenture
    assert adjustment_data["earlier_debenture"] == company.earlier_debenture
    company_scheme = " ".join(company_question.mark_scheme)
    for amount in (
        company.roof_repair,
        company.insurance_claim,
        company.new_debenture,
        company.earlier_debenture,
    ):
        assert f"£{amount:,}" in company_scheme

    retirement_scheme = " ".join(retirement_question.mark_scheme)
    assert f"£{partnership.goodwill:,}" in retirement_scheme
    appropriation_scheme = " ".join(appropriation_question.mark_scheme)
    assert f"£{partnership.profit_for_year:,}" in appropriation_scheme
    for drawings in (
        partnership.first_period_drawings_interest,
        partnership.second_period_drawings_interest,
    ):
        for amount in drawings.values():
            assert f"£{amount:,}" in appropriation_scheme


def test_income_statement_question_has_a_complete_task_specific_source_contract() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    question = next(
        item
        for section in generated.sections
        for item in section.options[0].questions
        if item.rule_id == "company_statement"
    )

    context = question.authoring_context
    assert context["required_prompt_terms"] == ["income statement"]
    assert "statement of financial position" not in context["task_scope"].casefold()
    assert {
        "administration_expenses",
        "cost_of_sales",
        "marketing_expenses",
        "revenue",
        "warehouse_expenses",
    } <= context["source_data"].keys()
    assert context["adjustments"]["current_tax_charge"] > 0
    assert context["verified_answers"]["profit_for_year"] > 0


def test_contribution_question_uses_a_complete_costing_identity() -> None:
    generated = build_paper(RULES["paper_2"], SYLLABUS, 26080100)
    option = generated.sections[0].options[0]
    question = next(
        item
        for section in generated.sections
        for item in section.options[0].questions
        if item.rule_id == "contribution"
    )
    case = CostingCase.from_chart_values(option.chart_values)

    assert question.authoring_context["source_data"] == {
        "units_sold": case.units_sold,
        "selling_price_per_unit": case.selling_price_per_unit,
        "variable_cost_per_unit": case.variable_cost_per_unit,
        "fixed_cost": case.fixed_cost,
    }
    assert question.authoring_context["verified_answers"] == {
        "contribution_per_unit": case.contribution_per_unit,
        "contribution": case.contribution,
        "profit": case.profit,
    }
    assert question.authoring_context["preserve_prompt"] is True
    assert question.authoring_context["preserve_mark_scheme"] is True
    assert case.contribution_per_unit == (
        case.selling_price_per_unit - case.variable_cost_per_unit
    )
    assert case.contribution == case.units_sold * case.contribution_per_unit
    assert case.profit == case.contribution - case.fixed_cost
    awarded = [
        point for point in question.structured_mark_scheme if point.marks > 0
    ]
    assert len(awarded) == question.marks
    assert any("Contribution per unit" in point.text for point in awarded)
    assert any("Total contribution" in point.text for point in awarded)
    assert any("Profit" in point.text for point in awarded)


def test_trade_discount_explanation_has_two_contextual_reasoning_chains() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26083001)
    question = next(
        item
        for section in generated.sections
        for item in section.options[0].questions
        if item.rule_id == "explain_trade"
    )
    awarded = [
        point.text
        for point in question.structured_mark_scheme
        if point.marks > 0
    ]

    assert len(awarded) == question.marks
    assert not any(
        text.casefold().startswith(("award", "credit", "indicative content"))
        for text in awarded
    )
    developed = [
        text
        for text in awarded
        if question.prompt.split()[4] in text and " therefore " in text.casefold()
    ]
    assert len(developed) >= 2


def test_paper_two_written_items_use_specific_a_level_accounting_tasks() -> None:
    generated = build_paper(RULES["paper_2"], SYLLABUS, 26083002)
    questions = {
        item.rule_id: item
        for section in generated.sections
        for item in section.options[0].questions
    }
    required_focus = {
        "frc": "accounting standards",
        "limitation": "special order",
        "variance_3": "adverse direct materials price variance",
        "variance_4": "investigate",
        "costing_2": "cost driver",
        "costing_4": "activity-based costing",
    }

    for rule_id, focus in required_focus.items():
        question = questions[rule_id]
        assert focus in question.prompt.casefold()
        assert "treated or interpreted" not in question.prompt.casefold()
        assert len(
            [point for point in question.structured_mark_scheme if point.marks > 0]
        ) == question.marks

    for rule_id in ("variance_4", "costing_4"):
        developed = [
            point.text.casefold()
            for point in questions[rule_id].structured_mark_scheme
            if point.marks > 0 and " therefore " in point.text.casefold()
        ]
        assert len(developed) >= 2


def test_every_management_calculation_has_complete_immutable_source_data() -> None:
    generated = build_paper(RULES["paper_2"], SYLLABUS, 26080107)
    calculations = {
        item.rule_id: item
        for section in generated.sections
        for option in section.options
        for item in option.questions
        if item.kind == "calculation"
    }

    for rule_id in ("budget", "variance_1", "variance_2", "costing_1", "costing_3"):
        question = calculations[rule_id]
        context = question.authoring_context
        assert context["preserve_prompt"] is True
        assert context["preserve_mark_scheme"] is True
        assert context["source_data"]
        assert context["verified_answers"]
        compact_prompt = question.prompt.replace(",", "")
        assert all(str(value) in compact_prompt for value in context["prompt_values"])
        awarded = [
            point
            for point in question.structured_mark_scheme
            if point.marks > 0
        ]
        assert len(awarded) == question.marks
        assert all(point.marks == 1 for point in awarded)


def test_budget_uses_exam_standard_currency_formatting() -> None:
    generated = build_paper(RULES["paper_2"], SYLLABUS, 26080107)
    budget = next(
        item
        for section in generated.sections
        for option in section.options
        for item in option.questions
        if item.rule_id == "budget"
    )
    rendered_scheme = " ".join(budget.mark_scheme)
    sales = budget.authoring_context["source_data"]["sales_receipts"]
    formatted_sales = f"£{sales:,}"

    assert "£-" not in rendered_scheme
    assert "−£" in rendered_scheme
    assert formatted_sales in budget.prompt
    assert formatted_sales in rendered_scheme


def test_management_calculations_group_large_currency_values() -> None:
    generated = build_paper(RULES["paper_2"], SYLLABUS, 26080107)
    calculations = [
        item
        for section in generated.sections
        for option in section.options
        for item in option.questions
        if item.kind == "calculation"
    ]

    for question in calculations:
        rendered = " ".join([question.prompt, *question.mark_scheme])
        assert re.search(r"£\d{4,}", rendered) is None, question.rule_id
        assert "£-" not in rendered, question.rule_id


def test_partnership_calculations_have_complete_shared_source_contracts() -> None:
    generated = build_paper(RULES["paper_1"], SYLLABUS, 26080100)
    questions = {
        item.rule_id: item
        for section in generated.sections
        for item in section.options[0].questions
    }

    retirement = questions["partnership_1"].authoring_context
    assert retirement["source_data"] == {
        "opening_capital": {"Alex": 16_000, "Morgan": 14_500, "Riley": 16_000},
        "goodwill": 24_000,
        "old_profit_sharing_ratio": {"Alex": 3, "Morgan": 2, "Riley": 1},
        "new_profit_sharing_ratio": {"Alex": 3, "Morgan": 2},
        "target_capital": {"Alex": 10_900, "Morgan": 10_300},
    }
    assert retirement["verified_answers"] == {
        "goodwill_credit": {"Alex": 12_000, "Morgan": 8_000, "Riley": 4_000},
        "goodwill_write_off": {"Alex": 14_400, "Morgan": 9_600},
        "cash_withdrawn": {"Alex": 2_700, "Morgan": 2_600},
        "closing_capital": {"Alex": 10_900, "Morgan": 10_300},
    }

    appropriation = questions["partnership_2"].authoring_context
    assert appropriation["source_data"]["period_months"] == [8, 4]
    assert appropriation["source_data"]["profit_for_year"] == 80_400
    assert appropriation["source_data"]["partner_salary_per_year"] == {
        "Morgan": 12_000
    }
    assert appropriation["verified_answers"]["period_profit"] == [53_600, 26_800]
    assert set(appropriation["verified_answers"]["appropriation_by_period"]) == {
        "first_period",
        "second_period",
    }


def test_both_packages_render_36_page_question_papers(tmp_path: Path) -> None:
    mark_scheme_pages = {"1": 26, "2": 28}
    for paper in ("1", "2"):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert set(paths) == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
        }
        assert page_count(paths["question_paper"]) == 36
        assert page_count(paths["mark_scheme"]) == mark_scheme_pages[paper]
        assert all(path.stat().st_size > 2000 for path in paths.values())


def test_paper_two_calculations_do_not_print_unrelated_index_tables(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=26083002,
    )
    pages = PdfReader(paths["question_paper"]).pages
    contribution_page = next(
        page
        for page in pages
        if "Calculate total contribution and profit" in (page.extract_text() or "")
    )
    text = contribution_page.extract_text() or ""

    assert "Revenue / activity index" not in text
    assert "Variable-cost index" not in text


def test_paper_two_mark_scheme_rows_contain_only_item_specific_guidance(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=26083002,
    )
    text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(paths["mark_scheme"]).pages
    )

    assert "Contribution per unit: £10 − £6 = £4." in text
    assert "Accounting standards require consistent recognition" in text
    assert "Marker check: reward a valid alternative route" not in text
    assert "confusing Marginal costing with a superficially related concept" not in text


def test_paper_one_section_a_matches_measured_case_and_account_pages(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    assert "DO NOT WRITE ON THIS PAGE" in (pages[6].extract_text() or "")
    assert "Additional information" in (pages[7].extract_text() or "")
    assert "13.1" not in (pages[8].extract_text() or "")
    assert "Sales journal" in (pages[9].extract_text() or "")
    assert "Sales Ledger Control Account" in (pages[10].extract_text() or "")
    assert "not yet been accounted for" in (pages[11].extract_text() or "")
    assert "Income statement" in (pages[12].extract_text() or "")
    assert "Capital Accounts" in (pages[15].extract_text() or "")
    assert "Interest on drawings has been calculated" in (
        pages[17].extract_text() or ""
    )
    assert "Profit and loss appropriation account" in (pages[18].extract_text() or "")
    assert "employ a bookkeeper" in (pages[21].extract_text() or "")
    assert "Advise the owner" in (pages[22].extract_text() or "")
    assert "DO NOT WRITE ON THIS PAGE" in (pages[26].extract_text() or "")
    assert "Statement of changes in equity" in (pages[27].extract_text() or "")
    assert "Advise the investor" in (pages[28].extract_text() or "")
    assert "There are no questions printed on this page" in (
        pages[32].extract_text() or ""
    )
    assert "Additional page, if required" in (pages[33].extract_text() or "")
    assert "Independent practice material" in (pages[35].extract_text() or "")


def test_partnership_appropriation_grid_matches_reference_page_depth(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=26080100,
    )
    page = fitz.open(paths["question_paper"])[18]
    horizontal_rules = [
        drawing["rect"]
        for drawing in page.get_drawings()
        if 60 <= drawing["rect"].x0 <= 65
        and 530 <= drawing["rect"].x1 <= 540
        and abs(drawing["rect"].y1 - drawing["rect"].y0) < 1
    ]

    assert 145 <= min(rule.y0 for rule in horizontal_rules) <= 175
    assert 730 <= max(rule.y1 for rule in horizontal_rules) <= 770


def test_paper_two_section_c_matches_reference_page_roles(tmp_path: Path) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    assert "Section C" in (pages[19].extract_text() or "")
    assert "Advise" in (pages[20].extract_text() or "")
    assert "DO NOT WRITE ON THIS PAGE" in (pages[24].extract_text() or "")
    assert "Extract 2" in (pages[25].extract_text() or "")
    assert "Advise" in (pages[26].extract_text() or "")
    assert "END OF QUESTIONS" in (pages[29].extract_text() or "")
    assert "There are no questions printed on this page" in (
        pages[30].extract_text() or ""
    )
    assert all(
        "Additional page, if required" in (pages[index].extract_text() or "")
        for index in range(31, 35)
    )
    assert "Independent practice material" in (pages[35].extract_text() or "")


def test_non_current_asset_question_and_mark_scheme_use_the_same_figures(
    tmp_path: Path,
) -> None:
    seed = 26080100
    generated = build_paper(RULES["paper_1"], SYLLABUS, seed)
    option = generated.sections[0].options[0]
    case = NonCurrentAssetCase.from_chart_values(option.title, option.chart_values)
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=seed,
    )

    question_pages = [page.extract_text() or "" for page in PdfReader(paths["question_paper"]).pages]
    scheme_pages = [page.extract_text() or "" for page in PdfReader(paths["mark_scheme"]).pages]
    question_text = next(
        text
        for text in question_pages
        if "Plant and machinery" in text and "Additional information" in text
    )
    scheme_text = next(
        text
        for text in scheme_pages
        if "Plant and machinery" in text and "Total non-current assets" in text
    )

    assert f"{case.plant_cost_opening:,}" in question_text
    assert f"{case.motor_disposal_cost:,}" in question_text
    assert f"{case.plant_cost_closing:,}" in scheme_text
    assert f"{case.motor_carrying_amount:,}" in scheme_text
    assert f"{case.total_carrying_amount:,}" in scheme_text


def test_sales_ledger_question_ai_contract_and_scheme_share_verified_data(
    tmp_path: Path,
) -> None:
    seed = 26080100
    generated = build_paper(RULES["paper_1"], SYLLABUS, seed)
    option = generated.sections[0].options[0]
    case = SalesLedgerCase.from_chart_values(option.title, option.chart_values)
    ledger_question, sales_question = option.questions[12:14]

    assert ledger_question.authoring_context["source_data"] == {
        "opening_trade_receivables": case.opening_receivables,
        "credit_sales": case.credit_sales,
        "sales_returns": case.sales_returns,
        "cash_received_from_credit_customers": case.cash_received,
        "discount_allowed": case.discount_allowed,
    }
    assert ledger_question.authoring_context["verified_answers"][
        "closing_trade_receivables"
    ] == case.closing_receivables
    assert sales_question.authoring_context["verified_answers"][
        "net_sales_transferred_to_income_statement"
    ] == case.net_sales

    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=seed,
    )
    question_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(paths["question_paper"]).pages[9:11]
    )
    scheme_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(paths["mark_scheme"]).pages[10:12]
    )
    for amount in (
        case.opening_receivables,
        case.credit_sales,
        case.sales_returns,
        case.cash_received,
        case.discount_allowed,
    ):
        assert f"{amount:,}" in question_text
    assert f"{case.closing_receivables:,}" in scheme_text
    assert f"{case.net_sales:,}" in scheme_text


def test_paper_one_mark_scheme_matches_reference_question_sequence(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["mark_scheme"]).pages
    expected = {
        7: "Objective test answers",
        8: "trade discount",
        9: "non-current assets section",
        10: "sales ledger control account",
        11: "sales account",
        12: "Prepare the income statement",
        15: "usefulness of the income statement",
        17: "Partners' Capital Accounts",
        18: "Profit and loss appropriation account",
        19: "formal partnership agreement",
        20: "Advise the owner",
        22: "Question 16 continued",
        23: "Advise the investor",
        25: "Question 17 continued",
    }
    assert len(pages) == 26
    for page_index, label in expected.items():
        assert label in (pages[page_index].extract_text() or "")


def test_invalid_paper_is_rejected(tmp_path: Path) -> None:
    try:
        generate_package(
            paper="3",
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path,
        )
    except ValueError as error:
        assert "1 or 2" in str(error)
    else:
        raise AssertionError("invalid paper was accepted")
