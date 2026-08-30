from __future__ import annotations

from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.pdfgen.canvas import Canvas


@dataclass(frozen=True)
class SolidRuleStyle:
    left: float
    right: float
    gap: float
    color: Color
    width: float


@dataclass(frozen=True)
class GlyphRuleStyle:
    left: float
    gap: float
    glyph: str
    glyph_count: int
    font: str
    font_size: float
    character_spacing: float
    color: Color


@dataclass(frozen=True)
class CanvasBarcodeStyle:
    widths: tuple[float, ...]
    repetitions: int
    height: float
    bar_y_offset: float
    gap: float
    font: str
    font_size: float
    caption_center_offset: float
    spread_caption: bool = False
    color: Color = colors.black


def draw_solid_answer_rules(
    pdf: Canvas,
    *,
    first_y: float,
    count: int,
    style: SolidRuleStyle,
) -> float:
    """Draw a fixed number of solid response rules and return the next baseline."""

    pdf.setStrokeColor(style.color)
    pdf.setLineWidth(style.width)
    for index in range(count):
        y = first_y - index * style.gap
        pdf.line(style.left, y, style.right, y)
    pdf.setStrokeColor(colors.black)
    return first_y - count * style.gap


def draw_glyph_answer_rules(
    pdf: Canvas,
    *,
    first_y: float,
    count: int,
    style: GlyphRuleStyle,
) -> float:
    """Draw selectable glyph-based response rules and return the next baseline."""

    for index in range(count):
        text = pdf.beginText()
        text.setTextOrigin(style.left, first_y - index * style.gap)
        text.setFont(style.font, style.font_size)
        text.setCharSpace(style.character_spacing)
        text.setFillColor(style.color)
        text.textOut(style.glyph * style.glyph_count)
        pdf.drawText(text)
    return first_y - count * style.gap


def draw_barcode(
    pdf: Canvas,
    *,
    x: float,
    y: float,
    caption: str,
    style: CanvasBarcodeStyle,
) -> None:
    """Draw a deterministic neutral-practice barcode and its caption."""

    pdf.setFillColor(style.color)
    cursor = x
    for index, width in enumerate(style.widths * style.repetitions):
        if index % 2 == 0:
            pdf.rect(
                cursor,
                y + style.bar_y_offset,
                width,
                style.height,
                stroke=0,
                fill=1,
            )
        cursor += width + style.gap
    pdf.setFont(style.font, style.font_size)
    if style.spread_caption:
        total_width = cursor - x
        character_step = total_width / max(1, len(caption))
        for index, character in enumerate(caption):
            pdf.drawCentredString(x + character_step * (index + 0.5), y, character)
    else:
        pdf.drawCentredString(x + style.caption_center_offset, y, caption)
