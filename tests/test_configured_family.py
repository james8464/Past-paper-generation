from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

from Backend.Core.assessment_package import validate_assessment_package
from Backend.Core.paths import REPO_ROOT

GENERATOR_ROOT = REPO_ROOT / "Resources" / "configured-generators" / "generator"
if str(GENERATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(GENERATOR_ROOT))

from configuredgen.cli import generate_package  # noqa: E402
from configuredgen.generator import build_paper  # noqa: E402
from configuredgen.models import load_syllabus  # noqa: E402


def _syllabus(subject: str) -> Path:
    return (
        REPO_ROOT
        / "Resources"
        / subject
        / "cambridge-international"
        / "generator"
        / "data"
        / "syllabus.json"
    )


def _family_syllabus(subject: str, board: str) -> Path:
    return (
        REPO_ROOT
        / "Resources"
        / subject
        / board
        / "generator"
        / "data"
        / "syllabus.json"
    )


def test_cambridge_economics_preview_covers_all_official_components(
    tmp_path: Path,
) -> None:
    syllabus = _syllabus("economics")
    payload = json.loads(syllabus.read_text(encoding="utf-8"))

    assert payload["specification_version"] == "9708-2026-2028"
    assert [
        (paper["id"], paper["marks"], paper["duration_minutes"])
        for paper in payload["papers"]
    ] == [
        ("1", 30, 60),
        ("2", 60, 120),
        ("3", 30, 75),
        ("4", 60, 120),
    ]
    assert payload["provenance"]

    for paper in ("1", "2", "3", "4"):
        output = tmp_path / f"economics-{paper}"
        paths = generate_package(
            paper=paper,
            syllabus_path=syllabus,
            output_dir=output,
            seed=8464,
            dry_run=True,
        )
        assert set(paths) == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
        }
        assessment = json.loads(paths["assessment_package"].read_text())
        assert assessment["paper"] == paper
        assert (
            sum(item["marks"] for item in assessment["items"])
            >= payload["papers"][int(paper) - 1]["marks"]
        )
        with pymupdf.open(paths["question_paper"]) as document:
            assert document.page_count >= 2
            text = "".join(page.get_text() for page in document)
            assert "UNOFFICIAL PRACTICE" in text
            assert "hours minutes" not in text
            assert "1 of the 1 option" not in text
            assert "1 of the 2 option in" not in text
            assert " could affect " not in text
        validation = validate_assessment_package(
            paths["assessment_package"],
            subject="economics_cambridge_international",
            paper_number=paper,
            preview=True,
            provider=None,
            model=None,
        )
        assert validation["item_count"] == len(assessment["items"])
        calculation_items = [
            item for item in assessment["items"] if item["kind"] == "calculation"
        ]
        for item in calculation_items:
            assert any(character.isdigit() for character in item["prompt"])
            assert "%" in item["prompt"]
            assert any("result:" in point.casefold() for point in item["mark_scheme"])
        if paper in {"2", "4"}:
            micro_topics = {
                item["topic_id"]
                for item in assessment["items"]
                if "@sections.1." in item["id"]
            }
            macro_topics = {
                item["topic_id"]
                for item in assessment["items"]
                if "@sections.2." in item["id"]
            }
            assert micro_topics
            assert macro_topics
            assert all("macro" not in topic for topic in micro_topics)
            assert all(
                "macro" in topic
                or topic
                in {
                    "a-level-growth-development",
                    "a-level-policy",
                }
                for topic in macro_topics
            )


def test_cambridge_computer_science_preview_covers_theory_and_practical_roles(
    tmp_path: Path,
) -> None:
    syllabus = _syllabus("computer-science")
    payload = json.loads(syllabus.read_text(encoding="utf-8"))

    assert payload["specification_version"] == "9618-2026"
    assert all(paper["marks"] == 75 for paper in payload["papers"])
    assert [paper["duration_minutes"] for paper in payload["papers"]] == [
        90,
        120,
        90,
        150,
    ]

    for paper in ("1", "2", "3", "4"):
        paths = generate_package(
            paper=paper,
            syllabus_path=syllabus,
            output_dir=tmp_path / f"computer-science-{paper}",
            seed=9618,
            dry_run=True,
        )
        expected = {
            "question_paper",
            "mark_scheme",
            "assessment_package",
        }
        if paper == "4":
            expected |= {"evidence_document", "source_file"}
        assert set(paths) == expected
        assessment = json.loads(paths["assessment_package"].read_text())
        assert sum(item["marks"] for item in assessment["items"]) == 75
        validation = validate_assessment_package(
            paths["assessment_package"],
            subject="computer_science_cambridge_international",
            paper_number=paper,
            preview=True,
            provider=None,
            model=None,
        )
        assert validation["item_count"] == 10
        if paper == "4":
            assert (
                "testing evidence"
                in paths["evidence_document"].read_text(encoding="utf-8").casefold()
            )
            assert paths["source_file"].suffix == ".py"
        trace_items = [item for item in assessment["items"] if item["kind"] == "trace"]
        for item in trace_items:
            assert "FOR index" in item["prompt"]
            assert "total ← total + index" in item["prompt"]
            assert any(
                "expected trace:" in point.casefold() for point in item["mark_scheme"]
            )


def test_aqa_mathematics_preview_covers_pure_mechanics_and_statistics(
    tmp_path: Path,
) -> None:
    syllabus = _family_syllabus("mathematics", "aqa")
    payload = json.loads(syllabus.read_text(encoding="utf-8"))

    assert payload["specification_version"] == "7357-2017"
    assert [
        (paper["id"], paper["marks"], paper["duration_minutes"])
        for paper in payload["papers"]
    ] == [("1", 100, 120), ("2", 100, 120), ("3", 100, 120)]
    paper_topics = {
        paper: {topic["id"] for topic in payload["topics"] if paper in topic["papers"]}
        for paper in ("1", "2", "3")
    }
    assert "mechanics-kinematics" not in paper_topics["1"]
    assert "mechanics-kinematics" in paper_topics["2"]
    assert "statistics-hypothesis-testing" in paper_topics["3"]

    for paper in ("1", "2", "3"):
        paths = generate_package(
            paper=paper,
            syllabus_path=syllabus,
            output_dir=tmp_path / f"mathematics-{paper}",
            seed=7357,
            dry_run=True,
        )
        assert set(paths) == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
        }
        assessment = json.loads(paths["assessment_package"].read_text())
        assert sum(item["marks"] for item in assessment["items"]) == 100
        assert all(
            item["assessment_contract"]["expected_answer_form"]
            in {
                "selected_response",
                "calculation_with_working",
                "mathematical_argument",
            }
            for item in assessment["items"]
        )
        assert all(
            any(character.isdigit() for character in item["prompt"])
            for item in assessment["items"]
        )
        assert all(
            "in relation to a system" not in item["prompt"].casefold()
            for item in assessment["items"]
        )
        assert all(
            not any("AO guidance:" in point for point in item["mark_scheme"])
            for item in assessment["items"]
        )
        validation = validate_assessment_package(
            paths["assessment_package"],
            subject="mathematics_aqa",
            paper_number=paper,
            preview=True,
            provider=None,
            model=None,
        )
        assert validation["item_count"] == len(assessment["items"])

        configured = load_syllabus(syllabus)
        generated = build_paper(configured.rule(paper), configured, seed=7357)
        questions = [
            question
            for section in generated.sections
            for option in section.options
            for question in option.questions
        ]
        assert all(
            question.authoring_context["preserve_mark_scheme"] is True
            for question in questions
        )
