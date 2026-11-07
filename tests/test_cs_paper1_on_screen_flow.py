"""On-screen questions follow owned content, not a renderer-invented page plan."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pymupdf
import pytest
from cspapergen import generator, render_pdf
from cspapergen.generator import build_paper1_blueprint
from cspapergen.syllabus import load_syllabus

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "Resources/computer-science/aqa/generator/cspapergen"


def normalized(text):
    return " ".join(text.split())


@pytest.fixture(scope="module", params=[270100, 20, 123])
def rendered(request, tmp_path_factory):
    assert Path(render_pdf.__file__).resolve() == GENERATOR / "render_pdf.py"
    assert Path(generator.__file__).resolve() == GENERATOR / "generator.py"
    blueprint, context = build_paper1_blueprint(load_syllabus(), seed=request.param)
    before = (blueprint.model_dump_json(), context.model_dump_json())
    destination = tmp_path_factory.mktemp(f"cs1-{request.param}") / "question-paper.pdf"
    render_pdf.render_question_paper(blueprint, destination)
    return blueprint, context, before, destination


def test_on_screen_paper_has_no_invented_blank_or_post_end_pages(rendered):
    _blueprint, _context, _before, path = rendered
    with pymupdf.open(path) as document:
        pages = [page.get_text() for page in document]
        assert not [
            index + 1
            for index, text in enumerate(pages)
            if "There are no questions printed on this page" in text
        ]
        assert sum("END OF QUESTIONS" in text for text in pages) == 1
        assert "END OF QUESTIONS" in pages[-1]
        for page in document[1:]:
            body = normalized(page.get_text(clip=pymupdf.Rect(40, 70, 550, 770)))
            assert body and body != "END OF QUESTIONS"


def test_on_screen_renderer_adds_no_unowned_response_scaffolds(rendered):
    blueprint, _context, _before, path = rendered
    unowned = (
        "Recursive call / result",
        "Question 3 trace table",
        "Algorithm X time",
        "Algorithm Y time",
        "Selected algorithm",
        "Skeleton Program information",
        "This information is repeated so that it remains visible while you complete the task.",
    )
    authoritative = normalized(blueprint.model_dump_json())
    assert all(item not in authoritative for item in unowned)
    with pymupdf.open(path) as document:
        text = normalized(" ".join(page.get_text() for page in document))
    assert [item for item in unowned if item in text] == []


def test_question_start_owner_stays_with_its_first_declared_prompt(rendered):
    from Backend.Core.computer_science_question_content import _markers

    blueprint, _context, _before, path = rendered
    with pymupdf.open(path) as document:
        for question in blueprint.questions:
            pages = [
                page
                for page in document
                if any(
                    number == question.number and label is None
                    for _y, number, label in _markers(page.get_text("words"))
                )
            ]
            assert len(pages) == 1
            prompt = normalized(
                question.parts[0].prompt.replace("{q}", f"{question.number:02d}")
            )
            assert prompt in normalized(pages[0].get_text()), (
                question.number,
                pages[0].number + 1,
            )


def test_all_questions_prompts_marks_sections_and_timing_are_preserved(rendered):
    blueprint, context, before, path = rendered
    assert [question.number for question in blueprint.questions] == list(range(1, 13))
    assert blueprint.delivery_mode == "on-screen"
    assert (
        blueprint.total_marks == sum(q.total_marks for q in blueprint.questions) == 100
    )
    with pymupdf.open(path) as document:
        text = normalized(" ".join(page.get_text() for page in document))
        body = normalized(" ".join(page.get_text() for page in document[1:]))
    position = 0
    for question in blueprint.questions:
        position = text.index(normalized(question.stem), position)
        for part in question.parts:
            prompt = part.prompt.replace("{q}", f"{question.number:02d}")
            position = text.index(normalized(prompt), position) + len(
                normalized(prompt)
            )
    expected_marks = [part.marks for q in blueprint.questions for part in q.parts]
    assert [
        int(mark) for mark in re.findall(r"\[(\d+) marks?\]", body)
    ] == expected_marks
    for title, _timing in render_pdf.PAPER1_SECTIONS.values():
        assert body.count(title) == 1
    timings = Counter(timing for _title, timing in render_pdf.PAPER1_SECTIONS.values())
    assert {timing: body.count(timing) for timing in timings} == dict(timings)
    assert (blueprint.model_dump_json(), context.model_dump_json()) == before


def test_canonical_code_is_printed_once_without_source_loss(rendered):
    blueprint, _context, _before, path = rendered
    code = [
        q.stimulus.code
        for q in blueprint.questions
        if q.stimulus and q.stimulus.kind == "code"
    ]
    with pymupdf.open(path) as document:
        text = normalized(" ".join(page.get_text() for page in document))
        anchors = Counter(normalized(value.splitlines()[0]) for value in code)
        assert {anchor: text.count(anchor) for anchor in anchors} == dict(anchors)
        for value in code:
            for line in value.splitlines():
                if line.strip():
                    assert normalized(line) in text


def test_canonical_fsm_is_printed_once_without_source_loss(rendered):
    blueprint, _context, _before, path = rendered
    with pymupdf.open(path) as document:
        text = normalized(" ".join(page.get_text() for page in document))
        fsm = next(
            q.stimulus
            for q in blueprint.questions
            if q.stimulus and q.stimulus.kind == "fsm"
        )
        for value in [*fsm.headers, *(cell for row in fsm.rows for cell in row)]:
            if value.strip():
                assert normalized(value) in text
        circles = [
            drawing["rect"]
            for page in document
            for drawing in page.get_drawings()
            if len(drawing["items"]) == 4
            and all(item[0] == "c" for item in drawing["items"])
        ]
        assert (
            sum(abs(r.width - 44) < 0.1 and abs(r.height - 44) < 0.1 for r in circles)
            == 3
        )
        assert (
            sum(abs(r.width - 36) < 0.1 and abs(r.height - 36) < 0.1 for r in circles)
            == 1
        )


def test_question_body_text_does_not_escape_printable_page_area(rendered):
    _blueprint, _context, _before, path = rendered
    with pymupdf.open(path) as document:
        for page in document[1:]:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if (
                            not text
                            or text.startswith("Keldin /")
                            or text == "Turn over >"
                        ):
                            continue
                        x0, y0, x1, y1 = span["bbox"]
                        if y1 < 54:  # Folio above the body rule.
                            continue
                        assert 40 <= x0 <= x1 <= 550, (page.number + 1, span)
                        assert 54 <= y0 <= y1 <= page.rect.height - 70, (
                            page.number + 1,
                            span,
                        )
