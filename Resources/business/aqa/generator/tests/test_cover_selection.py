from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pymupdf as fitz
import pytest
from aqabizgen import render_pdf as renderer
from aqabizgen.configs import RULES
from aqabizgen.generator import build_paper
from aqabizgen.syllabus import load_syllabus

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data/syllabus.json")
LEGACY_SELECTION = (
    "Answer all questions in Sections A and B.",
    "Answer one question from each optional section where instructed.",
)


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2", "paper_3"])
def test_cover_selection_matches_actual_topology(paper_id):
    assert Path(renderer.__file__).resolve() == ROOT / "aqabizgen/render_pdf.py"
    paper = build_paper(RULES[paper_id], SYLLABUS, 123)
    compulsory = all(
        section.answer_options == len(section.options) for section in paper.sections
    )
    assert compulsory == (paper_id != "paper_1")
    instructions = renderer._cover_profile(paper).instructions
    assert instructions[2:-2] == (
        ("Answer all questions.",) if compulsory else LEGACY_SELECTION
    )


def test_cover_selection_is_not_paper_id_switch():
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    for section in paper.sections:
        section.answer_options = len(section.options)
    assert renderer._cover_profile(paper).instructions[2:-2] == (
        "Answer all questions.",
    )


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2", "paper_3"])
def test_only_question_cover_changes_and_body_pages_are_identical(
    paper_id, tmp_path, monkeypatch
):
    paper = build_paper(RULES[paper_id], SYLLABUS, 123)
    snapshot = paper.model_dump(mode="json")
    current_profile = renderer._cover_profile

    def legacy_profile(value):
        profile = current_profile(value)
        return replace(
            profile,
            instructions=(
                *profile.instructions[:2],
                *LEGACY_SELECTION,
                *profile.instructions[-2:],
            ),
        )

    new = tmp_path / f"{paper_id}-new.pdf"
    old = tmp_path / f"{paper_id}-old.pdf"
    renderer.render_question_paper(paper, new)
    monkeypatch.setattr(renderer, "_cover_profile", legacy_profile)
    renderer.render_question_paper(paper, old)
    assert paper.model_dump(mode="json") == snapshot
    assert replace(current_profile(paper), instructions=()) == replace(
        legacy_profile(paper), instructions=()
    )
    with fitz.open(new) as after, fitz.open(old) as before:
        assert len(after) == len(before)
        for index in range(1, len(after)):
            assert after[index].get_text("words") == before[index].get_text("words")
            assert (
                after[index].get_pixmap().samples == before[index].get_pixmap().samples
            )
        if paper_id == "paper_1":
            assert after[0].get_pixmap().samples == before[0].get_pixmap().samples
        else:
            assert "Answer all questions." in after[0].get_text()
            assert "optional section" not in after[0].get_text()
            assert "Answer all questions in Sections A and B." in before[0].get_text()
