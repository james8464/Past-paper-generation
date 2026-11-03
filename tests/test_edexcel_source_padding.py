"""Label deliberately padded booklet leaves without relaxing PDF checks."""

from pathlib import Path

import pymupdf as fitz
import pytest
from pastpapergen import render_pdf
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus
from reportlab.pdfgen import canvas

from Backend.Core.pdf_validation import validate_pdf_for_release

ROOT = Path(__file__).resolve().parents[1]
assert Path(render_pdf.__file__).resolve() == (
    ROOT / "Resources/economics/edexcel-a/generator/pastpapergen/render_pdf.py"
)


@pytest.mark.parametrize("paper,target", [("1", 4), ("2", 4), ("3", 8)])
def test_real_booklet_labels_only_padding_and_preserves_content(
    tmp_path, monkeypatch, paper, target
):
    syllabus = load_syllabus(
        ROOT / "Resources/economics/edexcel-a/generator/data/syllabus_seed.json"
    )
    blueprint = build_paper_blueprint(
        load_builtin_paper_config(f"paper_{paper}"), syllabus, seed=270100
    )
    original = blueprint.model_dump(mode="json")
    content = tmp_path / "content.pdf"
    with monkeypatch.context() as patch:
        patch.setattr(render_pdf, "_pad_pdf_pages", lambda *_args: None)
        render_pdf.render_source_booklet(blueprint, syllabus, content)
    output = tmp_path / "source.pdf"
    render_pdf.render_source_booklet(blueprint, syllabus, output)
    with fitz.open(content) as before, fitz.open(output) as after:
        content_pages = len(before)
        assert len(after) == target
        assert len(before) < target
        for index, page in enumerate(before):
            assert after[index].get_text("words") == page.get_text("words")
            assert after[index].get_pixmap().samples == page.get_pixmap().samples
        for page in list(after)[len(before) :]:
            assert page.get_text().strip() == "BLANK PAGE"
    assert blueprint.model_dump(mode="json") == original
    report = validate_pdf_for_release(
        output, subject="economics", paper_number=paper, role="source_booklet"
    )
    assert [
        page["intentional_blank"] for page in report["layout_metrics"]["pages"]
    ] == ([False] * content_pages + [True] * (target - content_pages))


@pytest.mark.parametrize("existing,target", [(4, 4), (5, 4), (8, 8), (9, 8)])
def test_padding_does_not_add_or_label_full_or_overflowing_booklets(
    tmp_path, existing, target
):
    path = tmp_path / "pages.pdf"
    pdf = canvas.Canvas(str(path))
    for index in range(existing):
        if index:
            pdf.showPage()
        pdf.drawString(60, 700, f"Actual source content {index}")
    render_pdf._pad_pdf_pages(pdf, target)
    pdf.save()
    with fitz.open(path) as document:
        assert len(document) == existing
        assert all("BLANK PAGE" not in page.get_text() for page in document)


def test_labelled_interior_blank_is_not_a_padding_exception(tmp_path):
    path = tmp_path / "interior.pdf"
    with fitz.open() as document:
        for text in ["Source cover", "BLANK PAGE", "Actual assessed source"]:
            document.new_page().insert_text((60, 70), text)
        document.set_metadata(
            {"title": "Source booklet", "author": "Keldin", "subject": "Practice"}
        )
        document.save(path)
    with pytest.raises(ValueError, match=r"padding.*trailing"):
        validate_pdf_for_release(
            path, subject="economics", paper_number="1", role="source_booklet"
        )


def test_source_mentioning_blank_page_is_not_classified_as_padding(tmp_path):
    path = tmp_path / "source.pdf"
    with fitz.open() as document:
        document.new_page().insert_text(
            (60, 70), "This source discusses BLANK PAGE as an example."
        )
        document.set_metadata(
            {"title": "Source booklet", "author": "Keldin", "subject": "Practice"}
        )
        document.save(path)
    report = validate_pdf_for_release(
        path, subject="economics", paper_number="1", role="source_booklet"
    )
    assert report["layout_metrics"]["pages"][0]["intentional_blank"] is False


@pytest.mark.parametrize("line_only", [False, True])
def test_assessed_vector_content_with_blank_label_is_not_padding(tmp_path, line_only):
    path = tmp_path / "diagram.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((60, 70), "BLANK PAGE")
        if line_only:
            page.draw_line((100, 150), (300, 150))
        else:
            page.draw_rect(fitz.Rect(100, 150, 300, 350))
        document.set_metadata(
            {"title": "Source booklet", "author": "Keldin", "subject": "Practice"}
        )
        document.save(path)
    report = validate_pdf_for_release(
        path, subject="economics", paper_number="1", role="source_booklet"
    )
    assert report["layout_metrics"]["pages"][0]["intentional_blank"] is False
