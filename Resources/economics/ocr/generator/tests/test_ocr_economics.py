from __future__ import annotations

from pathlib import Path

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
    for paper, expected_pages in (("1", 20), ("2", 20), ("3", 28)):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert paths.keys() == {"question_paper", "mark_scheme"}
        assert len(PdfReader(paths["question_paper"]).pages) == expected_pages
        assert "A-level Economics" in (PdfReader(paths["question_paper"]).pages[0].extract_text() or "")
