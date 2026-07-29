from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from Backend.Core.pdf_validation import validate_pdf_for_release


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
