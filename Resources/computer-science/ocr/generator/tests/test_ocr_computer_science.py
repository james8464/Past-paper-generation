from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule
from ocrcsgen.cli import generate_package
from ocrcsgen.configs import PAPER_1_MARKS, PAPER_2_MARKS, RULES
from ocrcsgen.generator import build_paper
from ocrcsgen.render_pdf import MARK_SCHEME_PAGE_PLANS
from ocrcsgen.syllabus import load_syllabus


ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def _flatten(values: list[list[int]]) -> list[int]:
    return [mark for group in values for mark in group]


def test_current_mark_sequences_and_rules() -> None:
    assert sum(_flatten(PAPER_1_MARKS)) == 140
    assert sum(_flatten(PAPER_2_MARKS)) == 140
    assert len(_flatten(PAPER_1_MARKS)) == 41
    assert len(_flatten(PAPER_2_MARKS)) == 40
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_multi_seed_validity_scope_and_uniqueness() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, 123)
        same = build_paper(rule, SYLLABUS, 123)
        different = build_paper(rule, SYLLABUS, 456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()
        topic_ids = {
            question.topic_id
            for section in first.sections
            for option in section.options
            for question in option.questions
        }
        assert topic_ids == rule.allowed_topic_ids


def test_packages_render_current_page_geometry(tmp_path: Path) -> None:
    for paper, expected_pages, expected_scheme_pages in (
        ("1", 28, 36),
        ("2", 32, 27),
    ):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert paths.keys() == {"question_paper", "mark_scheme"}
        reader = PdfReader(paths["question_paper"])
        assert len(reader.pages) == expected_pages
        assert "A Level Computer Science" in (reader.pages[0].extract_text() or "")
        assert "EXTRA ANSWER SPACE" in (reader.pages[-1].extract_text() or "")
        if paper == "1":
            assert "Iteration" in (reader.pages[3].extract_text() or "")
            assert "First technology" in (reader.pages[9].extract_text() or "")
        scheme = PdfReader(paths["mark_scheme"])
        assert len(scheme.pages) == expected_scheme_pages
        assert float(scheme.pages[0].mediabox.height) > float(scheme.pages[0].mediabox.width)
        assert float(scheme.pages[1].mediabox.height) > float(scheme.pages[1].mediabox.width)
        assert all(
            float(page.mediabox.width) > float(page.mediabox.height)
            for page in scheme.pages[2:-1]
        )
        assert float(scheme.pages[-1].mediabox.height) > float(scheme.pages[-1].mediabox.width)


def test_mark_scheme_page_plans_cover_every_part() -> None:
    for paper_id, rule in RULES.items():
        planned = {
            (section_index, question_index)
            for page in MARK_SCHEME_PAGE_PLANS[paper_id]
            for section_index, question_index, _segment, _segment_count in page
        }
        expected = {
            (section_index, question_index)
            for section_index, section in enumerate(rule.sections)
            for question_index, _question in enumerate(section.questions)
        }
        assert planned == expected


def test_every_question_has_board_specific_context_and_marking() -> None:
    for rule in RULES.values():
        paper = build_paper(rule, SYLLABUS, 123)
        questions = [
            question
            for section in paper.sections
            for option in section.options
            for question in option.questions
        ]
        assert all("For part" not in question.prompt for question in questions)
        assert all("Independent case" not in question.prompt for question in questions)
        assert all(question.mark_scheme for question in questions)
        assert all(
            any("Level " in point for point in question.mark_scheme)
            for question in questions
            if question.marks >= 9
        )
