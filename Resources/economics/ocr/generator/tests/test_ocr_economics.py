from __future__ import annotations

from pathlib import Path

import fitz
from pypdf import PdfReader

from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule
from ocregen.cli import generate_package
from ocregen.configs import RULES
from ocregen.generator import build_paper
from ocregen.syllabus import load_syllabus

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def test_all_rules_have_exact_candidate_marks() -> None:
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_paper_one_and_two_current_mark_sequences() -> None:
    expected = {
        "paper_1": [2, 4, 2, 2, 8, 12],
        "paper_2": [2, 1, 3, 4, 8, 12],
    }
    for paper_id, sequence in expected.items():
        rule = RULES[paper_id]
        assert [question.marks for question in rule.sections[0].questions] == sequence
        assert [(section.option_count, section.answer_options, section.option_marks) for section in rule.sections] == [
            (1, 1, 30), (2, 1, 25), (2, 1, 25)
        ]
    paper_one = build_paper(RULES["paper_1"], SYLLABUS, 123)
    assert [
        question.number
        for question in paper_one.sections[0].options[0].questions
    ] == ["1(a)", "1(b)", "1(c)(i)", "1(c)(ii)", "1(d)", "1(e)"]


def test_paper_three_exact_structure() -> None:
    rule = RULES["paper_3"]
    assert rule.sections[0].option_count == 30
    assert [question.marks for question in rule.sections[1].questions] == [2, 3, 15, 3, 2, 15, 2, 8]


def test_multi_seed_validity_and_uniqueness() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, 123)
        same = build_paper(rule, SYLLABUS, 123)
        different = build_paper(rule, SYLLABUS, 456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()


def test_mcq_choices_are_distinct_and_contextual() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, 123)
    questions = [option.questions[0] for option in paper.sections[0].options]
    assert all(len(set(question.choices)) == 4 for question in questions)
    assert all(len(question.prompt.split()) >= 20 for question in questions)


def test_written_references_match_rendered_figure() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 123)
    prompts = [question.prompt for question in paper.sections[0].options[0].questions]
    assert all("Table 1" not in prompt for prompt in prompts)
    assert any("Figure 1" in prompt for prompt in prompts)


def test_all_packages_render_reference_page_geometry(tmp_path: Path) -> None:
    expected_scheme_pages = {"1": 30, "2": 33, "3": 32}
    for paper, expected_pages in (("1", 20), ("2", 20), ("3", 28)):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert paths.keys() == {"question_paper", "mark_scheme"}
        assert len(PdfReader(paths["question_paper"]).pages) == expected_pages
        cover = PdfReader(paths["question_paper"]).pages[0].extract_text() or ""
        assert "A Level Economics" in cover
        if paper in {"1", "2"}:
            question_pages = PdfReader(paths["question_paper"]).pages
            assert "Figure 2" in (question_pages[2].extract_text() or "")
            assert "Section B" in (question_pages[8].extract_text() or "")
            assert "Section C" in (question_pages[12].extract_text() or "")
            assert "EXTRA ANSWER SPACE" in (
                question_pages[16].extract_text() or ""
            )
            assert "continued" in (question_pages[18].extract_text() or "")
        scheme = PdfReader(paths["mark_scheme"])
        assert len(scheme.pages) == expected_scheme_pages[paper]
        assert scheme.pages[0].mediabox.height > scheme.pages[0].mediabox.width
        assert scheme.pages[2].mediabox.width > scheme.pages[2].mediabox.height
        assert scheme.pages[-1].mediabox.height > scheme.pages[-1].mediabox.width


def test_mark_scheme_uses_dense_ocr_tables_and_guidance_pages(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["mark_scheme"]).pages
    assert "PREPARATION FOR MARKING" in (pages[2].extract_text() or "")
    assert "LEVELS OF RESPONSE" in (pages[9].extract_text() or "")
    question_page = pages[10].extract_text() or ""
    assert all(heading in question_page for heading in ("Question", "Answer", "Mark", "Guidance"))
    assert "Diagram guidance for 1(b)" in question_page
    data_page = pages[11].extract_text() or ""
    assert "x 100 =" in data_page
    assert "index points" in data_page
    assert "Worked calculation" not in data_page
    objectives_page = pages[-2].extract_text() or ""
    assert all(heading in objectives_page for heading in ("AO1", "AO2", "AO3", "AO4", "TOTAL"))

    rendered = fitz.open(paths["mark_scheme"])
    assert len(rendered[10].get_drawings()) >= 30
    diagram_text = rendered[20].get_text().casefold()
    assert "diagram guidance" in diagram_text
    assert "contestability" in diagram_text
    assert "labour" not in diagram_text
    assert len(rendered[20].get_drawings()) >= 20


def test_business_objectives_use_cost_and_revenue_diagrams(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=1,
    )

    diagram_page = PdfReader(paths["mark_scheme"]).pages[20].extract_text() or ""
    assert "Profit maximisation: MC = MR" in diagram_page
    assert "Revenue maximisation: MR = 0" in diagram_page
    assert "Entry increases competitive supply" not in diagram_page
