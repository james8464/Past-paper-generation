"""Owned long-prompt EAD controls, not question-quality qualification."""

from copy import deepcopy
from math import isclose

import pymupdf as fitz
import pytest
from cspapergen import paper1_assets as assets
from cspapergen.generator import build_paper1_blueprint
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint
from pypdf import PdfReader

from Backend.Core.render_transaction import render_pdf_atomically


def blueprint_with_prompt(minimum_lines):
    syllabus = load_syllabus()
    blueprint, _ = build_paper1_blueprint(syllabus, seed=27011105)
    part = blueprint.questions[0].parts[0]
    while len(assets._wrap(part.prompt, 88)) < minimum_lines:
        part.prompt += (
            " For this question, consider the representation of records and the "
            "behaviour of the program under valid inputs."
        )
    validate_blueprint(blueprint, syllabus)
    return blueprint


def assert_fields(reader, blueprint):
    expected = {
        f"question_{q.number}_{p.label}" for q in blueprint.questions for p in q.parts
    }
    fields = reader.get_fields()
    assert fields is not None and set(fields) == expected
    references = {
        field.get_object()["/T"]: field.idnum
        for field in reader.trailer["/Root"]["/AcroForm"]["/Fields"]
    }
    seen = []
    for page in reader.pages:
        for reference in page.get("/Annots", []):
            widget = reference.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = widget["/T"]
            assert references[name] == reference.idnum
            assert widget["/FT"] == "/Tx"
            assert int(widget["/Ff"]) & 4096
            assert str(widget["/V"]) == ""
            assert widget["/AP"]["/N"].get_object().get_data()
            seen.append(name)
    assert len(seen) == len(expected) and set(seen) == expected


@pytest.mark.parametrize("minimum_lines", [35, 85])
def test_full_prompt_continues_without_a_field_covering_text(tmp_path, minimum_lines):
    blueprint = blueprint_with_prompt(minimum_lines)
    before = deepcopy(blueprint.model_dump(mode="json"))
    path = tmp_path / "long-prompt-ead.pdf"
    assets.render_electronic_answer_document(blueprint, path)
    reader = PdfReader(path)
    assert_fields(reader, blueprint)
    first = blueprint.questions[0].parts[0]
    field_name = f"question_{blueprint.questions[0].number}_{first.label}"
    with fitz.open(path) as document:
        pages = []
        prompt = []
        first_complete = False
        for index, page in enumerate(document):
            widgets = list(page.widgets() or [])
            spans = [
                span
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
            ]
            for widget in widgets:
                assert widget.rect.height >= 280
                assert all(
                    not widget.rect.intersects(fitz.Rect(span["bbox"]))
                    for span in spans
                    if span["text"].strip()
                ), f"field covers printed text on page {index + 1}"
            if index and not first_complete:
                body = [span for span in spans if isclose(span["size"], 9.5)]
                prompt.extend(span["text"] for span in body)
                first_complete = any(w.field_name == field_name for w in widgets)
                pages.append((index, first_complete))
                assert all(
                    span["bbox"][0] >= 54.9 and span["bbox"][2] <= 535.1
                    for span in body
                )
        assert pages[-1][1]
        assert len(pages) >= (2 if minimum_lines == 35 else 3)
        assert " ".join(prompt).split() == first.prompt.split()
        text = "\n".join(document[index].get_text() for index, _ in pages)
        label = f"[{first.marks} mark{'s' if first.marks != 1 else ''}]"
        assert text.count(label) == 1
        for offset, (index, has_field) in enumerate(pages):
            text = document[index].get_text()
            assert f"Question {blueprint.questions[0].number}.{first.label}" in text
            if offset:
                assert "continued" in text
            if not has_field:
                assert len(document[index].get_text().split()) > 15
    assert blueprint.model_dump(mode="json") == before


def test_unrenderable_word_refuses_before_canvas_and_atomic_rewrite(
    tmp_path, monkeypatch
):
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=27011105)
    path = tmp_path / "existing.pdf"
    assets.render_electronic_answer_document(blueprint, path)
    before = path.read_bytes()
    blueprint.questions[0].parts[0].prompt = "W" * 150
    original = deepcopy(blueprint.model_dump(mode="json"))
    monkeypatch.setattr(
        assets.canvas,
        "Canvas",
        lambda *_a, **_k: pytest.fail("Canvas opened before admission"),
    )
    with pytest.raises(ValueError, match="word"):
        render_pdf_atomically(
            path,
            lambda target: assets.render_electronic_answer_document(blueprint, target),
            role="owned EAD",
        )
    assert path.read_bytes() == before
    assert blueprint.model_dump(mode="json") == original
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize(
    ("count", "page_lengths"),
    [
        (25, [25]),
        (26, [26, 0]),
        (49, [49, 0]),
        (50, [49, 1]),
        (74, [49, 25]),
        (75, [49, 26, 0]),
        (85, [49, 36, 0]),
    ],
)
def test_prompt_and_response_capacity_boundaries(count, page_lengths):
    text = " ".join(f"{index:03d}" + "x" * 80 for index in range(count))
    pages = assets._answer_prompt_pages(text)
    assert list(map(len, pages)) == page_lengths
    assert " ".join(line for page in pages for line in page).split() == text.split()


def test_actual_width_wraps_wide_words_but_accepts_a_long_narrow_word():
    text = "W" * 40 + " " + "W" * 40
    assert len(text) <= 88
    pages = assets._answer_prompt_pages(text)
    assert len(pages[0]) == 2
    assert " ".join(pages[0]) == text
    assert all(
        assets.pdfmetrics.stringWidth(line, assets.FONT, 9.5) <= 480
        for line in pages[0]
    )
    narrow = "i" * 120
    assert assets._answer_prompt_pages(narrow) == [(narrow,)]


def test_valid_continuation_replaces_existing_document_atomically(tmp_path):
    original, _ = build_paper1_blueprint(load_syllabus(), seed=27011105)
    destination = tmp_path / "rewritten.pdf"
    assets.render_electronic_answer_document(original, destination)
    old_bytes = destination.read_bytes()
    revised = blueprint_with_prompt(35)
    result = render_pdf_atomically(
        destination,
        lambda path: assets.render_electronic_answer_document(revised, path),
        role="owned EAD",
    )
    assert result.path == destination and result.pages > 40
    assert destination.read_bytes() != old_bytes
    assert_fields(PdfReader(destination), revised)
    assert not list(tmp_path.glob(".*.tmp"))
