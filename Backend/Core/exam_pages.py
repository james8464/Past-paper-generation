from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable

from Backend.Core.document_dsl import BlankPage, ContinuationPage, RuleSet

Board = Literal["aqa", "ocr"]
PageVariant = Literal["additional", "continuation", "blank"]


@dataclass(frozen=True)
class ExamPageProfile:
    board: Board
    code: str
    heading: str
    variant: PageVariant
    legal_notice: bool = False
    do_not_write: bool = False
    message: str = ""


class ExamPage(Flowable):
    """A full-page shell that can also live inside a Platypus story."""

    def __init__(
        self,
        profile: ExamPageProfile,
        *,
        font: str,
        bold_font: str,
        page_number: int = 0,
        page_size: tuple[float, float] = A4,
    ) -> None:
        super().__init__()
        self.profile = profile
        self.font = font
        self.bold_font = bold_font
        self.page_number = page_number
        self.page_width, self.page_height = page_size
        self.width = 167 * mm
        self.height = 226 * mm

    @property
    def component(self) -> BlankPage | ContinuationPage | RuleSet:
        """Expose identical page intent to the renderer-neutral DSL."""
        if self.profile.variant == "blank":
            return BlankPage(message=self.profile.message or self.profile.heading)
        if self.profile.variant == "continuation":
            return ContinuationPage(heading=self.profile.heading)
        return RuleSet(lines=25)

    def drawOn(
        self,
        canv: Canvas,
        x: float,
        y: float,
        _sW: float = 0,
    ) -> None:
        del x, y, _sW
        draw_exam_page(
            canv,
            self.profile,
            width=self.page_width,
            height=self.page_height,
            font=self.font,
            bold_font=self.bold_font,
            page_number=self.page_number,
            include_footer=True,
        )

    def draw(self) -> None:
        # ``drawOn`` deliberately works in page coordinates.
        return None


def draw_exam_page(
    pdf: Canvas,
    profile: ExamPageProfile,
    *,
    width: float,
    height: float,
    font: str,
    bold_font: str,
    page_number: int,
    include_footer: bool = True,
) -> None:
    pdf.saveState()
    pdf.setFillColor(colors.white)
    # Preserve the template's folio. Repainting it would leave a second hidden
    # text layer in extraction even when the visual background is opaque.
    pdf.rect(0, 0, width, height - 30, stroke=0, fill=1)
    pdf.restoreState()
    pdf.saveState()
    pdf.setFillColor(colors.black)
    pdf.setStrokeColor(colors.black)
    pdf.setLineCap(0)
    if profile.board == "aqa":
        _draw_aqa_page(
            pdf,
            profile,
            width=width,
            height=height,
            font=font,
            bold_font=bold_font,
            page_number=page_number,
            include_footer=include_footer,
        )
    else:
        _draw_ocr_page(
            pdf,
            profile,
            width=width,
            height=height,
            font=font,
            bold_font=bold_font,
            page_number=page_number,
            include_footer=include_footer,
        )
    pdf.restoreState()


def _draw_aqa_page(
    pdf: Canvas,
    profile: ExamPageProfile,
    *,
    width: float,
    height: float,
    font: str,
    bold_font: str,
    page_number: int,
    include_footer: bool,
) -> None:
    if page_number:
        pdf.setFont(font, 11.04)
        pdf.drawCentredString(290.73, height - 39.0, str(page_number))

    if profile.variant == "blank":
        if profile.do_not_write:
            pdf.setLineWidth(0.5)
            pdf.rect(
                39.7,
                height - 765.8,
                538.6 - 39.7,
                765.8 - 54.0,
                stroke=1,
                fill=0,
            )
            pdf.setLineWidth(0.75)
            pdf.line(114.0, height - 662.1, 538.6, height - 54.0)
        pdf.setFont(bold_font, 11.04)
        pdf.drawCentredString(width / 2, height - 78, profile.heading)
        if profile.do_not_write:
            pdf.setFont(bold_font, 11.04)
            pdf.drawCentredString(width / 2, height - 407, "DO NOT WRITE ON THIS PAGE")
            pdf.drawCentredString(
                width / 2,
                height - 420,
                "ANSWER IN THE SPACES PROVIDED",
            )
        if profile.legal_notice:
            _draw_independent_notice(pdf, font=font, bold_font=bold_font, height=height)
        if include_footer:
            _draw_aqa_footer(
                pdf, profile, width=width, font=font, page_number=page_number
            )
        return

    if profile.variant == "continuation":
        if profile.heading:
            pdf.setFont(bold_font, 9)
            pdf.drawCentredString(width / 2, height - 70, profile.heading)
        _draw_rules(
            pdf,
            left=91.2,
            right=533.0,
            top=79.5,
            bottom=749.2,
            spacing=25.75,
            page_height=height,
        )
        if include_footer:
            _draw_aqa_footer(
                pdf, profile, width=width, font=font, page_number=page_number
            )
        return

    left = 50.0
    right = 528.5
    top = 66.5
    header_bottom = 98.5
    bottom = 556.3 if profile.legal_notice else 748.6
    gutter = 102.5
    pdf.setLineWidth(2.0)
    pdf.rect(left, height - bottom, right - left, bottom - top, stroke=1, fill=0)
    pdf.setLineWidth(0.95)
    pdf.line(gutter, height - top, gutter, height - bottom)
    pdf.setLineWidth(1.4)
    pdf.line(left, height - header_bottom, right, height - header_bottom)

    pdf.setLineWidth(0.35)
    rule = 123.0
    while rule < bottom - 10:
        pdf.line(gutter, height - rule, right, height - rule)
        rule += 25.5

    pdf.setFont(font, 9)
    pdf.drawString(56.4, height - 81.12, "Question")
    pdf.drawString(56.4, height - 91.44, "number")
    pdf.setFont(bold_font, 10.56)
    pdf.drawCentredString((gutter + right) / 2, height - 80.76, profile.heading)
    pdf.drawCentredString(
        (gutter + right) / 2,
        height - 92.88,
        "Write the question numbers in the left-hand margin.",
    )

    if profile.legal_notice:
        pdf.setLineWidth(1.4)
        pdf.rect(50, height - 745.8, right - 50, 175.7, stroke=1, fill=0)
        _draw_independent_notice(pdf, font=font, bold_font=bold_font, height=height)
    if include_footer:
        _draw_aqa_footer(pdf, profile, width=width, font=font, page_number=page_number)


def _draw_aqa_footer(
    pdf: Canvas,
    profile: ExamPageProfile,
    *,
    width: float,
    font: str,
    page_number: int,
) -> None:
    _draw_barcode(pdf, 50, 17, profile.code)
    if profile.legal_notice:
        _draw_barcode(pdf, width - 145, 17, f"{profile.code}:legal")
    pdf.setFont(font, 6.5)
    pdf.drawCentredString(
        width / 2,
        18,
        f"{profile.code} • {page_number or 1} • UNOFFICIAL PRACTICE",
    )


def _draw_independent_notice(
    pdf: Canvas,
    *,
    font: str,
    bold_font: str,
    height: float,
) -> None:
    pdf.setFont(bold_font, 7.5)
    pdf.drawString(50, height - 674, "Independent practice material")
    pdf.setFont(font, 6.8)
    notice = (
        "Created independently by Paper Creator for private revision. "
        "Not produced, endorsed or approved by an examination board."
    )
    pdf.drawString(50, height - 690, notice)


def _draw_ocr_page(
    pdf: Canvas,
    profile: ExamPageProfile,
    *,
    width: float,
    height: float,
    font: str,
    bold_font: str,
    page_number: int,
    include_footer: bool,
) -> None:
    pdf.setFont(font, 10)
    if page_number:
        pdf.drawCentredString(width / 2, height - 40, str(page_number))
    pdf.setFont(bold_font, 11 if profile.variant == "blank" else 9)
    if profile.variant == "blank":
        pdf.drawCentredString(width / 2, height - 71.6, profile.heading)
        if profile.do_not_write:
            instruction = (
                "DO NOT WRITE ON THIS PAGE"
                if profile.message
                else "PLEASE DO NOT WRITE ON THIS PAGE"
            )
            instruction_baseline = 406.6 if profile.message else 425.6
            pdf.drawCentredString(
                width / 2,
                height - instruction_baseline,
                instruction,
            )
        if profile.message:
            pdf.drawCentredString(width / 2, height - 445.7, profile.message)
    elif profile.variant == "continuation":
        line_count = 22 if profile.legal_notice else 27
        _draw_ocr_rules(
            pdf,
            height=height,
            font=font,
            font_size=10.965,
            left=72.3,
            dots=" " + "." * 154,
            first_baseline=92.6,
            line_count=line_count,
            guide_bottom=632.1 if profile.legal_notice else 762.1,
            guide=False,
        )
    else:
        pdf.drawCentredString(width / 2, height - 72.5, profile.heading)
        pdf.setFont(font, 8.5)
        pdf.drawString(
            49.6,
            height - 99,
            "If you need extra space use this lined page. You must write the question numbers clearly in the",
        )
        pdf.drawString(49.6, height - 114, "margin.")

        _draw_ocr_rules(
            pdf,
            height=height,
            font=font,
            font_size=11,
            left=49.6,
            dots="." * 162,
            first_baseline=138.6,
            line_count=20 if profile.legal_notice else 25,
            guide_bottom=632.1 if profile.legal_notice else 762.5,
            guide=True,
        )

    if not include_footer or not profile.legal_notice:
        return
    pdf.setLineWidth(1.0)
    pdf.line(49.6, height - 657.85, 545.7, height - 657.85)
    _draw_ocr_notice(pdf, font=font, bold_font=bold_font, height=height)


def _draw_ocr_rules(
    pdf: Canvas,
    *,
    height: float,
    font: str,
    font_size: float,
    left: float,
    dots: str,
    first_baseline: float,
    line_count: int,
    guide_bottom: float,
    guide: bool,
) -> None:
    pdf.setFillColor(colors.black)
    pdf.setFont(font, font_size)
    for index in range(line_count):
        baseline = first_baseline + index * 26.0
        pdf.drawString(left, height - baseline, dots)
    if not guide:
        return
    pdf.setLineWidth(0.5)
    pdf.line(106.3, height - 137.1, 106.3, height - guide_bottom)


def _draw_ocr_notice(
    pdf: Canvas,
    *,
    font: str,
    bold_font: str,
    height: float,
) -> None:
    pdf.setFont(bold_font, 7.5)
    pdf.drawString(49.6, height - 700, "Independent practice material")
    pdf.setFont(font, 6.5)
    pdf.drawString(
        49.6,
        height - 714,
        "Created independently by Paper Creator for private revision; not produced or endorsed by OCR.",
    )


def _draw_rules(
    pdf: Canvas,
    *,
    left: float,
    right: float,
    top: float,
    bottom: float,
    spacing: float,
    page_height: float,
) -> None:
    pdf.setLineWidth(0.35)
    y = top
    while y <= bottom:
        pdf.line(left, page_height - y, right, page_height - y)
        y += spacing


def _draw_barcode(pdf: Canvas, x: float, y: float, value: str) -> None:
    bits = "".join(
        f"{byte:08b}" for byte in hashlib.sha256(value.encode("utf-8")).digest()[:7]
    )
    cursor = x
    for index, bit in enumerate(bits):
        bar_width = 0.8 if index % 4 else 1.2
        if bit == "1":
            pdf.rect(cursor, y, bar_width, 27, stroke=0, fill=1)
        cursor += bar_width + 0.7
