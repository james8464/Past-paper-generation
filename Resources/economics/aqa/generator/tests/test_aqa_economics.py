from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule
from aqaecongen.cli import generate_package
from aqaecongen.configs import RULES
from aqaecongen.generator import build_paper
from aqaecongen.syllabus import load_syllabus


ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def test_all_paper_rules_have_exact_candidate_marks_and_syllabus_scope() -> None:
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_paper_one_and_two_have_exact_aqa_choice_structure() -> None:
    for paper_id in ("paper_1", "paper_2"):
        rule = RULES[paper_id]
        assert [(s.option_count, s.answer_options, s.option_marks) for s in rule.sections] == [
            (2, 1, 40),
            (3, 1, 40),
        ]
        assert [(q.kind, q.marks, q.command_word) for q in rule.sections[0].questions] == [
            ("calculation", 2, "Calculate"),
            ("data_response", 4, "Explain"),
            ("diagram_analysis", 9, "Explain"),
            ("extended_response", 25, "Discuss"),
        ]
        assert [q.marks for q in rule.sections[1].questions] == [15, 25]


def test_paper_three_has_thirty_mcqs_and_fifty_mark_case_study() -> None:
    rule = RULES["paper_3"]
    assert rule.sections[0].option_count == 30
    assert rule.sections[0].candidate_marks == 30
    assert [(q.kind, q.marks, q.command_word) for q in rule.sections[1].questions] == [
        ("data_interpretation", 10, "Assess"),
        ("essay", 15, "Explain"),
        ("extended_response", 25, "Recommend"),
    ]


def test_each_paper_is_valid_and_seed_changes_content() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, seed=123)
        same = build_paper(rule, SYLLABUS, seed=123)
        different = build_paper(rule, SYLLABUS, seed=456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()


def test_each_package_renders_readable_pdfs(tmp_path: Path) -> None:
    for paper in ("1", "2", "3"):
        output = tmp_path / paper
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=output,
            seed=123,
        )
        expected = (
            {"question_paper", "source_booklet", "mark_scheme"}
            if paper == "3"
            else {"question_paper", "mark_scheme"}
        )
        assert paths.keys() == expected
        for path in paths.values():
            reader = PdfReader(path)
            assert len(reader.pages) >= 2
            assert "A-level Economics" in (reader.pages[0].extract_text() or "")
        assert len(PdfReader(paths["question_paper"]).pages) == (44 if paper == "3" else 8)
        assert len(PdfReader(paths["mark_scheme"]).pages) == (
            11 if paper == "3" else 21
        )
        if paper == "3":
            assert len(PdfReader(paths["source_booklet"]).pages) == 8
            blueprint = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
            assert [q.number for q in blueprint.sections[1].options[0].questions] == [
                "31",
                "32",
                "33",
            ]
            mcqs = [
                option.questions[0]
                for option in blueprint.sections[0].options
            ]
            assert len({question.prompt for question in mcqs}) == 30
            assert all("Practice scenario" not in question.prompt for question in mcqs)
        else:
            question_pages = PdfReader(paths["question_paper"]).pages
            assert "Highest recorded index" in (question_pages[1].extract_text() or "")
            assert "Extract C" in (question_pages[2].extract_text() or "")
            assert "source insert" not in (question_pages[2].extract_text() or "")
            assert "DO NOT WRITE ON THIS PAGE" in (
                question_pages[7].extract_text() or ""
            )
