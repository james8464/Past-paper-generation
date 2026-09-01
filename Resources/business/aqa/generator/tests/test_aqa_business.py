from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytest
from aqabizgen.cli import generate_package
from aqabizgen.configs import RULES
from aqabizgen.financials import FinancialPosition, format_number
from aqabizgen.generator import build_paper
from aqabizgen.syllabus import load_syllabus
from pypdf import PdfReader

from Backend.Core.exam_blueprints import (
    resolve_question_rules,
    validate_generated_paper,
    validate_rule,
)
from Backend.Core.independent_solver import IndependentSolver

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def _marks(paper_id: str) -> list[int]:
    return [
        question.marks
        for section in RULES[paper_id].sections
        for _ in range(section.option_count)
        for question in section.questions
    ]


def test_current_rules_and_printed_mark_sequences() -> None:
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)
    assert _marks("paper_1") == [1] * 15 + [4, 4, 9, 9, 9] + [25] * 4
    assert _marks("paper_2") == [3, 4, 9, 16, 3, 6, 9, 16, 9, 9, 16]
    assert _marks("paper_3") == [12, 12, 16, 16, 20, 24]


def test_rules_use_official_assessment_objective_allocations() -> None:
    paper_1 = RULES["paper_1"]
    section_b = paper_1.sections[1].questions
    assert [question.assessment_objectives for question in section_b] == [
        {"AO1": 1, "AO2": 3},
        {"AO1": 1, "AO2": 3},
        {"AO1": 2, "AO2": 3, "AO3": 4},
        {"AO1": 2, "AO2": 3, "AO3": 4},
        {"AO1": 2, "AO2": 3, "AO3": 4},
    ]
    assert paper_1.sections[2].questions[0].assessment_objectives == {
        "AO1": 5,
        "AO2": 4,
        "AO3": 6,
        "AO4": 10,
    }
    assert RULES["paper_3"].sections[0].questions[-1].assessment_objectives == {
        "AO1": 5,
        "AO2": 4,
        "AO3": 6,
        "AO4": 9,
    }


def test_paper_one_calculations_share_source_data_with_mark_scheme() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    option = paper.sections[1].options[0]
    current_ratio, roce = option.questions[:2]
    financials = FinancialPosition.from_chart_values(option.chart_values)

    assert current_ratio.rule_id == "current_ratio"
    assert roce.rule_id == "roce_calculation"
    assert current_ratio.command_word == roce.command_word == "Calculate"
    assert current_ratio.kind == roce.kind == "calculation"
    assert (
        f"{format_number(financials.current_ratio)}:1"
        in " ".join(current_ratio.mark_scheme)
    )
    assert (
        f"£{format_number(financials.operating_profit_at_twelve_percent)}m"
        in " ".join(roce.mark_scheme)
    )
    assert [point.assessment_objective for point in current_ratio.structured_mark_scheme] == [
        "AO1",
        "AO2",
        "AO2",
        "AO2",
    ]
    assert current_ratio.authoring_context["preserve_prompt"] is True
    assert roce.authoring_context["source_data"]["capital_employed"] == (
        financials.capital_employed
    )
    assert roce.authoring_context["verified_answers"]["operating_profit"] == (
        financials.operating_profit_at_twelve_percent
    )


def test_paper_two_calculations_name_the_displayed_sales_series() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 123)
    calculations = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.kind == "calculation"
    ]

    assert calculations
    assert all("business sales data" in question.prompt for question in calculations)
    assert all("2021 to 2025" in question.prompt for question in calculations)


def test_multi_seed_validity_and_uniqueness() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, 123)
        same = build_paper(rule, SYLLABUS, 123)
        different = build_paper(rule, SYLLABUS, 456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()


def test_mcq_choices_are_distinct() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    questions = [option.questions[0] for option in paper.sections[0].options]
    assert len(questions) == 15
    assert all(len(set(question.choices)) == 4 for question in questions)


def test_question_13_contract_matches_the_rendered_performance_table() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    option = paper.sections[0].options[12]
    question = option.questions[0]

    assert question.number == "13"
    contract = question.authoring_context["selected_response_contract"]
    assert contract["operation"] == "performance_statements"
    assert contract["rows"][0] == {
        "label": "Capacity utilisation",
        "target": "90",
        "actual": "88",
        "better_when": "higher",
    }
    assert question.authoring_context["preserve_prompt"] is True
    assert question.authoring_context["preserve_mark_scheme"] is True


def _candidate_objectives(paper_id: str) -> dict[str, int]:
    totals = {f"AO{index}": 0 for index in range(1, 5)}
    rule = RULES[paper_id]
    for section in rule.sections:
        for option_index in range(1, section.answer_options + 1):
            for question in resolve_question_rules(section, option_index):
                for objective, marks in question.assessment_objectives.items():
                    totals[objective] += marks
    return totals


def test_business_one_varies_mcq_work_and_preserves_other_paper_budgets() -> None:
    assert _candidate_objectives("paper_1") == {
        "AO1": 27,
        "AO2": 29,
        "AO3": 24,
        "AO4": 20,
    }
    assert _candidate_objectives("paper_2") == {
        "AO1": 24,
        "AO2": 27,
        "AO3": 28,
        "AO4": 21,
    }
    assert _candidate_objectives("paper_3") == {
        "AO1": 19,
        "AO2": 19,
        "AO3": 31,
        "AO4": 31,
    }


def test_fixed_business_mcqs_have_one_typed_source_for_task_key_and_renderer() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    questions = {
        int(option.questions[0].number): option.questions[0]
        for option in paper.sections[0].options
    }
    expected_topics = {
        6: "business-4",
        7: "business-5",
        10: "business-4",
        12: "business-10",
        13: "business-7",
    }
    for number, topic_id in expected_topics.items():
        question = questions[number]
        assert question.topic_id == topic_id
        assert "selected_response_contract" in question.authoring_context
        assert question.source_dependency in {"stem", "figure"}

    assert "strategic drift" not in questions[12].prompt.casefold()
    assert "widening mismatch" in questions[12].prompt.casefold()
    assert all(not option.chart_title and not option.chart_values for option in paper.sections[0].options)


def test_business_selected_responses_are_independently_derived_and_fail_closed() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    questions = {
        int(option.questions[0].number): option.questions[0]
        for option in paper.sections[0].options
    }
    for number in (5, 6, 7, 10, 12, 13):
        question = questions[number]
        raw = question.model_dump(mode="json")
        raw["correct_choice"] = (question.correct_choice + 1) % 4
        solution = IndependentSolver().solve(raw, [])
        assert solution.answer == next(
            choice for choice in question.choices
            if choice.casefold() in solution.answer.casefold()
        )
        assert solution.solution_source == "deterministic-candidate-inputs"

    malformed = questions[7].model_dump(mode="json")
    correct = questions[7].correct_choice
    malformed["choices"][correct] += " or £4m"
    with pytest.raises(ValueError, match="exactly one semantic option"):
        IndependentSolver().solve(malformed, [])

    tied = questions[10].model_dump(mode="json")
    tied["authoring_context"]["selected_response_contract"]["rows"][0].update(
        {"output": "840", "employees": "40"}
    )
    with pytest.raises(ValueError, match="one highest row"):
        IndependentSolver().solve(tied, [])
    assert "high external change and low strategic change" not in questions[12].prompt.casefold()


def test_packages_render_current_page_geometry(tmp_path: Path) -> None:
    mark_scheme_pages = {"1": 23, "2": 20, "3": 14}
    for paper, expected_pages in (("1", 32), ("2", 24), ("3", 28)):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        expected_roles = (
            {"question_paper", "source_booklet", "mark_scheme"}
            if paper == "3"
            else {"question_paper", "mark_scheme"}
        )
        expected_roles.add("assessment_package")
        assert paths.keys() == expected_roles
        assert len(PdfReader(paths["question_paper"]).pages) == expected_pages
        assert len(PdfReader(paths["mark_scheme"]).pages) == mark_scheme_pages[paper]
        if paper == "3":
            assert len(PdfReader(paths["source_booklet"]).pages) == 8


def test_paper_three_reserves_blank_leaf_and_three_additional_pages(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="3",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    assert "There are no questions printed on this page" in (
        pages[24].extract_text() or ""
    )
    assert all(
        "Additional page, if required" in (pages[index].extract_text() or "")
        for index in (25, 26, 27)
    )


def test_paper_two_matches_section_transitions_and_final_answer_leaves(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    for index in (8, 14, 21):
        assert "DO NOT WRITE ON THIS PAGE" in (pages[index].extract_text() or "")
    assert all(
        "Additional page, if required" in (pages[index].extract_text() or "")
        for index in (22, 23)
    )


def test_paper_one_uses_measured_question_and_answer_page_plan(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )
    pages = PdfReader(paths["question_paper"]).pages
    assert "change in the break-even point" in (pages[3].extract_text() or "")
    assert "Financial data" in (pages[4].extract_text() or "")
    assert "Extract from accounts of" in (
        pages[9].extract_text() or ""
    )
    assert "Average span of control" in (pages[11].extract_text() or "")
    assert "There are no questions printed on this page" in (
        pages[27].extract_text() or ""
    )
    assert "Additional page, if required" in (pages[28].extract_text() or "")
    assert "Independent practice material" in (pages[31].extract_text() or "")

    scheme_pages = PdfReader(paths["mark_scheme"]).pages
    assert "Objective Test Answers" in (scheme_pages[4].extract_text() or "")
    assert "Current assets" in (scheme_pages[6].extract_text() or "")
    assert "Section C" in (scheme_pages[13].extract_text() or "")
    assert "Section D" in (scheme_pages[18].extract_text() or "")
    assert "Evaluation" in (scheme_pages[22].extract_text() or "")
    scheme_text = "\n".join(page.extract_text() or "" for page in scheme_pages)
    option = build_paper(RULES["paper_1"], SYLLABUS, 123).sections[1].options[0]
    financials = FinancialPosition.from_chart_values(option.chart_values)
    assert f"{format_number(financials.current_ratio)}:1" in scheme_text
    assert (
        f"£{format_number(financials.operating_profit_at_twelve_percent)}m"
        in scheme_text
    )
    assert "AO1 = 5, AO2 = 4, AO3 = 6 and AO4 = 10" in scheme_text


def test_paper_one_mcq_labels_and_question_text_stay_inside_print_geometry(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=26090101,
    )

    with fitz.open(paths["question_paper"]) as document:
        financial_page = document[4]
        words = financial_page.get_text("words")
        diversification = next(word for word in words if word[4] == "Diversification")
        label = next(
            word
            for word in words
            if word[4] == "A" and abs(word[1] - diversification[1]) < 1
        )
        assert diversification[0] - label[2] >= 24

        strategy_page = document[6]
        strategy_text = strategy_page.get_text()
        assert "Which measure records employees leaving during a period?" in strategy_text
        first_prompt_word = next(
            word
            for word in strategy_page.get_text("words")
            if word[4] == "Which" and word[1] < 100
        )
        assert first_prompt_word[0] >= 100
        body_drawings = [
            drawing["rect"]
            for drawing in strategy_page.get_drawings()
            if 40 < drawing["rect"].y0 < 800
        ]
        assert body_drawings
        assert min(rect.x0 for rect in body_drawings) >= 39.58
