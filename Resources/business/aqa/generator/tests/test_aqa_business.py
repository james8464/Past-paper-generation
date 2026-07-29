from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from aqabizgen.cli import generate_package
from aqabizgen.configs import RULES
from aqabizgen.financials import FinancialPosition, format_number
from aqabizgen.generator import build_paper
from aqabizgen.syllabus import load_syllabus
from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule


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
        assert paths.keys() == expected_roles
        assert len(PdfReader(paths["question_paper"]).pages) == expected_pages
        assert len(PdfReader(paths["mark_scheme"]).pages) == mark_scheme_pages[paper]
        if paper == "3":
            assert len(PdfReader(paths["source_booklet"]).pages) == 8


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
