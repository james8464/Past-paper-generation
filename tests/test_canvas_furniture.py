from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, call

import pymupdf
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from Backend.Core.document_dsl import (
    CanvasBarcodeStyle,
    GlyphRuleStyle,
    SolidRuleStyle,
    draw_barcode,
    draw_glyph_answer_rules,
    draw_solid_answer_rules,
)


def test_solid_answer_rules_preserve_coordinates_and_advance(tmp_path: Path) -> None:
    path = tmp_path / "solid.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(300, 300))

    next_y = draw_solid_answer_rules(
        pdf,
        first_y=220,
        count=3,
        style=SolidRuleStyle(
            left=40,
            right=260,
            gap=18,
            color=colors.HexColor("#404040"),
            width=0.45,
        ),
    )
    pdf.save()

    assert next_y == 166
    with pymupdf.open(path) as document:
        drawings = document[0].get_drawings()
        horizontal_rules = [
            item
            for drawing in drawings
            for item in drawing["items"]
            if item[0] == "l" and item[1].y == item[2].y
        ]
        assert len(horizontal_rules) == 3


def test_canvas_furniture_preserves_renderer_state_contract() -> None:
    pdf = Mock()
    solid_style = SolidRuleStyle(
        left=40,
        right=260,
        gap=18,
        color=colors.HexColor("#404040"),
        width=0.45,
    )
    barcode_style = CanvasBarcodeStyle(
        widths=(1, 2),
        repetitions=1,
        height=20,
        bar_y_offset=6,
        gap=1,
        font="Helvetica",
        font_size=8,
        caption_center_offset=12,
    )

    draw_solid_answer_rules(pdf, first_y=220, count=1, style=solid_style)
    draw_barcode(pdf, x=40, y=30, caption="01", style=barcode_style)

    assert pdf.setStrokeColor.call_args_list == [
        call(solid_style.color),
        call(colors.black),
    ]
    pdf.setFont.assert_called_once_with("Helvetica", 8)
    pdf.setFillColor.assert_called_once_with(colors.black)


def test_glyph_answer_rules_and_barcode_render_selectable_output(
    tmp_path: Path,
) -> None:
    path = tmp_path / "glyph-and-barcode.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(300, 300))

    next_y = draw_glyph_answer_rules(
        pdf,
        first_y=220,
        count=2,
        style=GlyphRuleStyle(
            left=32,
            gap=16,
            glyph=".",
            glyph_count=80,
            font="Helvetica",
            font_size=6,
            character_spacing=0.174,
            color=colors.HexColor("#4f5962"),
        ),
    )
    draw_barcode(
        pdf,
        x=40,
        y=30,
        caption="1234",
        style=CanvasBarcodeStyle(
            widths=(1, 2, 1, 3),
            repetitions=2,
            height=20,
            bar_y_offset=6,
            gap=1,
            font="Helvetica",
            font_size=8,
            caption_center_offset=12,
            spread_caption=True,
        ),
    )
    pdf.save()

    assert next_y == 188
    with pymupdf.open(path) as document:
        text = document[0].get_text()
        assert text.count(".") >= 150
        assert "1234" in text
        filled_rectangles = [
            drawing
            for drawing in document[0].get_drawings()
            if drawing.get("fill") is not None and drawing["rect"].height == 20
        ]
        assert len(filled_rectangles) == 4
