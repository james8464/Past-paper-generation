from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image
import pytest
from reportlab.pdfgen import canvas

from Backend.Core.pdf_validation import (
    _validate_typography_profile,
    validate_pdf_for_release,
)

def test_image_only_page_is_not_reported_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "image-only.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(200, 200))
    pdf.setTitle("Image-only release validation")
    image = Image.new("RGB", (200, 200), "white")
    pdf.drawInlineImage(image, 64, 64, width=72, height=72)
    pdf.save()

    result = validate_pdf_for_release(path, subject="business")

    assert result["pages"] == 1
    assert result["minimum_image_dpi"] == 200


def test_standard_pdf_font_is_recorded_as_controlled_ci_fallback() -> None:
    result = _validate_typography_profile(
        subject="economics_aqa",
        role="question_paper",
        font_characters=Counter({"Times-Roman": 120, "Times-Bold": 20}),
        font_sizes=Counter({11.0: 100, 7.0: 40}),
        filename="question-paper.pdf",
    )

    assert result is not None
    assert result["uses_standard_pdf_fallback"] is True
    assert result["font_family_overlap"] == 1.0


def _release_canvas(path: Path) -> canvas.Canvas:
    pdf = canvas.Canvas(str(path), pagesize=(200, 200))
    pdf.setTitle("Release artifact")
    pdf.setAuthor("Paper Creator")
    pdf.setSubject("Independent practice material")
    return pdf


def test_duplicate_text_at_the_same_position_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(40, 150, "Question 1")
    pdf.drawString(40, 150, "Question 1")
    pdf.save()

    with pytest.raises(ValueError, match="overlapping text.*page 1"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")


def test_page_with_only_a_folio_is_rejected_as_content_free(tmp_path: Path) -> None:
    path = tmp_path / "folio-only.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(100, 10, "1")
    pdf.save()

    with pytest.raises(ValueError, match="page 1 has too little content"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")


def test_ruled_answer_page_is_not_treated_as_content_free(tmp_path: Path) -> None:
    path = tmp_path / "answer-page.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(20, 180, "Answer")
    for y in range(30, 170, 12):
        pdf.line(20, y, 180, y)
    pdf.save()

    result = validate_pdf_for_release(path, subject="business", role="mark_scheme")

    page = result["layout_metrics"]["pages"][0]
    assert page["characters"] == len("Answer")
    assert page["vector_objects"] >= 10
    assert page["text_occupancy"] > 0
    assert page["overlapping_text_pairs"] == 0


def test_layout_metrics_record_each_page(tmp_path: Path) -> None:
    path = tmp_path / "metrics.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(20, 170, "A complete first page")
    pdf.showPage()
    pdf.drawString(20, 170, "A complete second page")
    pdf.save()

    result = validate_pdf_for_release(path, subject="business", role="mark_scheme")

    metrics = result["layout_metrics"]
    assert len(metrics["pages"]) == 2
    assert metrics["median_text_occupancy"] > 0
    assert metrics["overlapping_text_pairs"] == 0
