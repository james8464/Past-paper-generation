from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True)
class BoardLayout:
    page_width: float
    page_height: float
    margin_left: float
    margin_right: float
    margin_top: float
    margin_bottom: float
    content_x: float
    content_width: float
    answer_line_gap: float
    answer_line_color: str
    answer_line_dash: tuple[float, float] | None
    font_regular: str
    font_bold: str
    body_font_size: float
    body_leading: float
    crop_box: tuple[float, float, float, float] | None = None
    media_box: tuple[float, float, float, float] | None = None
    rail_x_left: float | None = None
    rail_x_right: float | None = None
    rail_y_bottom: float = 50
    rail_height: float = 760
    template_path: str | None = None


EDEXCEL_ECONOMICS = BoardLayout(
    page_width=595.28,
    page_height=841.89,
    margin_left=43,
    margin_right=555,
    margin_top=740,
    margin_bottom=50,
    content_x=43,
    content_width=510,
    answer_line_gap=28,
    answer_line_color="#505050",
    answer_line_dash=None,
    font_regular="ExamSans",
    font_bold="ExamSans-Bold",
    body_font_size=12,
    body_leading=14,
    media_box=(0.0, 0.0, 651.97, 898.58),
    crop_box=(28.35, 28.35, 623.62, 870.24),
    rail_x_left=10,
    rail_x_right=571,
    rail_y_bottom=92,
    rail_height=650,
)

AQA_CS = BoardLayout(
    page_width=595.32,
    page_height=841.92,
    margin_left=54,
    margin_right=534,
    margin_top=770,
    margin_bottom=76,
    content_x=54,
    content_width=480,
    answer_line_gap=20,
    answer_line_color="#000000",
    answer_line_dash=(1, 0),
    font_regular="AQAArial",
    font_bold="AQAArial-Bold",
    body_font_size=11,
    body_leading=14,
    rail_x_left=516,
    rail_y_bottom=76,
    rail_height=694,
)


MARK_SCHEME_LAYOUT = BoardLayout(
    page_width=595.28,
    page_height=841.89,
    margin_left=56,
    margin_right=539,
    margin_top=780,
    margin_bottom=60,
    content_x=56,
    content_width=483,
    answer_line_gap=0,
    answer_line_color="",
    answer_line_dash=(0, 0),
    font_regular="Helvetica",
    font_bold="Helvetica-Bold",
    body_font_size=10,
    body_leading=12,
)

BOARDS: dict[str, BoardLayout] = {
    "edexcel_economics": EDEXCEL_ECONOMICS,
    "aqa_computer_science": AQA_CS,
}
