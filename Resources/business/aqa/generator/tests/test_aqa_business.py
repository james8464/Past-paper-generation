from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from aqabizgen.cli import generate_package
from aqabizgen.configs import RULES
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
        if paper == "3":
            assert len(PdfReader(paths["source_booklet"]).pages) == 8
