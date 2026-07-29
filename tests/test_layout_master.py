from __future__ import annotations

import io
import hashlib
import json
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from Backend.Core.layout_master import (
    LayoutConformanceError,
    Rect,
    TextSlot,
    conform_pdf_to_box_template,
    draw_text_slot,
    load_layout_master,
)
from Backend.Core.layout_conformance import REGISTRY_PATH
from tools.build_layout_masters import write_layout_master


def _sample_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(595.32, 841.92))
    for page in range(2):
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, 790, f"Question {page + 1}")
        pdf.line(40, 40, 555, 40)
        pdf.drawCentredString(297.66, 20, str(page + 1))
        pdf.showPage()
    pdf.save()


def test_layout_master_preserves_coordinates_without_reference_text(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "master.json"
    _sample_pdf(source)

    write_layout_master(
        source,
        output,
        family="test-family",
        paper="1",
        document_role="question-paper",
    )

    raw = output.read_text(encoding="utf-8")
    master = load_layout_master(output)
    assert master.page_count == 2
    assert master.pages[0].media_box == Rect(0, 0, 595.32, 841.92)
    assert master.recurring_furniture
    assert '"text"' not in raw
    assert "Question 1" not in raw


def test_fixed_text_slot_rejects_overflow() -> None:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(200, 200))
    slot = TextSlot(
        rect=Rect(10, 10, 40, 20),
        font_name="Helvetica",
        font_size=11,
        leading=13,
    )

    with pytest.raises(LayoutConformanceError):
        draw_text_slot(pdf, 200, slot, "This text cannot fit")


def test_runtime_registry_covers_every_supported_paper() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    expected = {
        "accounting_aqa:1",
        "accounting_aqa:2",
        "business_aqa:1",
        "business_aqa:2",
        "business_aqa:3",
        "economics_aqa:1",
        "economics_aqa:2",
        "economics_aqa:3",
        "computer_science:1",
        "computer_science:2",
        "computer_science_ocr:1",
        "computer_science_ocr:2",
        "economics_ocr:1",
        "economics_ocr:2",
        "economics_ocr:3",
        "economics:1",
        "economics:2",
        "economics:3",
    }

    assert set(registry["papers"]) == expected
    assert registry["copyrighted_text_included"] is False
    assert all(
        record["question-paper"]["page_count"] > 0
        and len(record["question-paper"]["page_boxes"])
        == record["question-paper"]["page_count"]
        and all(
            set(boxes) == {"media", "crop", "trim", "bleed", "art"}
            for boxes in record["question-paper"]["page_boxes"]
        )
        for record in registry["papers"].values()
    )


def test_box_conformance_preserves_vector_drawings(tmp_path: Path) -> None:
    import fitz

    path = tmp_path / "drawing.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(595.28, 841.89))
    pdf.setTitle("Metadata survives conformance")
    pdf.line(50, 50, 500, 50)
    pdf.save()

    conform_pdf_to_box_template(
        path,
        {
            "media": [0, 0, 595.32, 841.92],
            "crop": [0, 0, 595.32, 841.92],
            "trim": [0, 0, 595.32, 841.92],
            "bleed": [0, 0, 595.32, 841.92],
            "art": [0, 0, 595.32, 841.92],
        },
    )

    document = fitz.open(path)
    try:
        assert document[0].get_drawings()
        assert document.metadata["title"] == "Metadata survives conformance"
    finally:
        document.close()


def test_box_conformance_is_no_op_when_boxes_already_match(
    tmp_path: Path,
) -> None:
    path = tmp_path / "already-conformant.pdf"
    _sample_pdf(path)
    boxes = {
        "media": [0, 0, 595.32, 841.92],
        "crop": [0, 0, 595.32, 841.92],
        "trim": [0, 0, 595.32, 841.92],
        "bleed": [0, 0, 595.32, 841.92],
        "art": [0, 0, 595.32, 841.92],
    }
    conform_pdf_to_box_template(path, boxes)
    first_digest = hashlib.sha256(path.read_bytes()).hexdigest()

    conform_pdf_to_box_template(path, boxes)

    assert hashlib.sha256(path.read_bytes()).hexdigest() == first_digest
