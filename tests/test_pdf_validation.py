from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image
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
