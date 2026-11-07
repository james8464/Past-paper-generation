"""Rendering must not invalidate an owned source's prior review identity."""

from pathlib import Path

import pymupdf as fitz
import pytest
from ocrcsgen.configs import load_rule
from ocrcsgen.generator import build_paper
from ocrcsgen.render_pdf import render_question_paper
from ocrcsgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import _demand_item, _difficulty_candidate, _tasks
from Backend.Core.assessment_package import _extract_items
from Backend.Core.candidate_identity import candidate_content_identity
from Backend.Core.model_review import (
    DifficultyReviewResult,
    require_difficulty_review,
    validate_saved_difficulty_evidence,
)
from Backend.Core.reference_demand import build_item_demand_target, profile_for

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    syllabus = load_syllabus(
        ROOT / "Resources/computer-science/ocr/generator/data/syllabus.json"
    )
    paper = build_paper(load_rule("2"), syllabus, seed=27011107)
    task = _tasks(paper, {topic.id: topic for topic in syllabus.topics})[0]
    profile = profile_for("ocr/computer-science", "2")
    target = build_item_demand_target(_demand_item(task), profile)
    projection = _difficulty_candidate(task, task.question)

    class OwnedReviewer:
        def generate_json(self, _prompt):
            return DifficultyReviewResult(
                approved=True,
                estimated_demand=target.demand_band,
                reasoning_steps=target.minimum_reasoning_steps,
                tariff_fit=True,
                command_word_fit=True,
                context_fit=True,
                profile_fit=True,
                observed_cognitive_operations=target.required_cognitive_operations,
                estimated_minutes=float(target.expected_minutes_min),
            ).model_dump(
                mode="json",
                exclude={
                    "candidate_content_identity",
                    "public_task_operation_evidence",
                },
            )

    evidence = require_difficulty_review(
        OwnedReviewer(),
        item_id=task.question.number,
        subject="Computer Science",
        target=target,
        candidate=projection,
        specification={},
    ).model_dump(mode="json")
    before = paper.model_dump(mode="json")
    path = tmp_path_factory.mktemp("owned-ocr-render") / "question-paper.pdf"
    render_question_paper(paper, path)
    return paper, before, projection, evidence, profile, path


def test_rendering_does_not_change_blueprint_or_reviewed_parent(rendered):
    paper, before, projection, _, _, _ = rendered
    assert paper.model_dump(mode="json") == before
    exported = _extract_items(
        paper.model_dump(mode="json"), subject="computer_science_ocr", paper_number="2"
    )
    assert candidate_content_identity(
        exported[0]["difficulty_candidate_projection"]
    ) == candidate_content_identity(projection)


def test_pre_render_difficulty_evidence_remains_valid_for_public_export(rendered):
    paper, _, _, evidence, profile, _ = rendered
    exported = _extract_items(
        paper.model_dump(mode="json"), subject="computer_science_ocr", paper_number="2"
    )[0]
    validate_saved_difficulty_evidence(
        evidence,
        build_item_demand_target(exported, profile),
        item_id=exported["id"],
        candidate=exported["difficulty_candidate_projection"],
    )


def test_display_heading_is_preserved_without_becoming_source_metadata(rendered):
    _, before, _, _, _, path = rendered
    assert before["sections"][0]["options"][0]["title"] == "Question 1"
    with fitz.open(path) as document:
        assert any("Section A · Question 1" in page.get_text() for page in document)
