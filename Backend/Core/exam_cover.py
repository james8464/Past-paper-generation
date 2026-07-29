from __future__ import annotations

import hashlib
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable

from Backend.Core.generation_date import (
    formatted_generation_date,
    formatted_generation_series,
)


@dataclass(frozen=True)
class CoverProfile:
    board: str
    subject: str
    code: str
    paper_title: str
    duration: str
    total_marks: int
    candidate_fields: bool = True
    materials: tuple[str, ...] = ()
    instructions: tuple[str, ...] = ()
    information: tuple[str, ...] = ()
    mark_rows: tuple[tuple[str, int], ...] = ()


class QuestionPaperCover(Flowable):
    """Fixed-grid, board-shaped front page without copying protected artwork."""

    def __init__(
        self,
        profile: CoverProfile,
        *,
        font: str,
        bold_font: str,
    ) -> None:
        super().__init__()
        self.profile = profile
        self.font = font
        self.bold_font = bold_font
        self.width = 167 * mm
        self.height = 235 * mm

    def draw(self) -> None:
        if self.profile.board == "ocr":
            self._draw_ocr()
        else:
            self._draw_aqa()

    def _draw_aqa(self) -> None:
        pdf = self.canv
        top = self.height
        pdf.saveState()
        pdf.setFillColor(colors.HexColor("#141414"))
        self._wordmark(0, top - 1 * mm, "PAPER", "CREATOR")

        y = top - (21 * mm if self.profile.candidate_fields else 27 * mm)
        if self.profile.candidate_fields:
            y = self._candidate_box(y)
            y -= 8.2 * mm
        pdf.setFont(self.font, 27)
        pdf.drawString(0, y, "A-level")
        y -= 12 * mm
        pdf.setFont(self.bold_font, 27)
        pdf.drawString(0, y, self.profile.subject.upper())
        y -= 10 * mm
        pdf.setFont(self.font, 16)
        pdf.drawString(0, y, self.profile.paper_title)
        y -= 8 * mm
        pdf.setLineWidth(1.2)
        pdf.line(0, y, self.width, y)
        y -= 13 * mm

        pdf.setFont(self.font, 13)
        pdf.drawString(0, y, formatted_generation_date())
        pdf.drawCentredString(self.width * 0.58, y, "Practice session")
        pdf.drawRightString(self.width, y, f"Time allowed: {self.profile.duration}")
        y -= 10 * mm
        if self.profile.mark_rows:
            self._examiner_table(y)
        y = self._sections(y)
        self._barcode(4 * mm)
        pdf.setFont(self.font, 5.8)
        pdf.drawRightString(
            self.width,
            3 * mm,
            f"{self.profile.code}  •  UNOFFICIAL PRACTICE",
        )
        pdf.restoreState()

    def _draw_ocr(self) -> None:
        pdf = self.canv
        top = self.height
        pdf.saveState()
        pdf.setFillColor(colors.HexColor("#1f315f"))
        pdf.setFont(self.bold_font, 26)
        pdf.drawCentredString(self.width / 2, top - 13 * mm, "PAPER CREATOR")
        pdf.setFillColor(colors.HexColor("#141414"))
        pdf.setFont(self.bold_font, 11)
        pdf.drawString(0, top - 19 * mm, formatted_generation_date())
        pdf.drawRightString(self.width, top - 19 * mm, "Practice session")
        pdf.setFont(self.font, 10)
        pdf.drawString(0, top - 29 * mm, f"A Level {self.profile.subject.title()}")
        pdf.drawString(0, top - 39 * mm, self.profile.code)
        pdf.drawString(0, top - 47 * mm, f"Time allowed: {self.profile.duration}")

        warning_y = top - 67 * mm
        pdf.roundRect(0, warning_y, 72 * mm, 18 * mm, 2 * mm, stroke=1, fill=0)
        pdf.setFont(self.font, 7)
        pdf.drawString(4 * mm, warning_y + 11 * mm, "You may use an appropriate calculator.")
        pdf.drawString(4 * mm, warning_y + 6 * mm, "Unofficial practice material.")
        self._barcode(warning_y + 3 * mm, x=112 * mm)
        y = self._candidate_box(warning_y - 28 * mm)
        y += 6 * mm
        y = self._sections(y)
        pdf.setFont(self.font, 5.8)
        pdf.drawString(0, 3 * mm, "PAPER CREATOR • INDEPENDENT PRACTICE")
        pdf.drawRightString(self.width, 3 * mm, "Turn over")
        pdf.restoreState()

    def _wordmark(self, x: float, y: float, first: str, second: str) -> None:
        pdf = self.canv
        pdf.setFont(self.bold_font, 27)
        pdf.drawString(x, y, first)
        pdf.setFont(self.bold_font, 16)
        pdf.drawString(x, y - 5 * mm, second)

    def _candidate_box(self, y: float) -> float:
        pdf = self.canv
        box_height = 57 * mm
        pdf.setLineWidth(0.45)
        pdf.rect(0, y - box_height, self.width, box_height, stroke=1, fill=0)
        pdf.setFont(self.font, 11)
        pdf.drawString(3 * mm, y - 5 * mm, "Please write clearly in block capitals.")
        row_y = y - 15 * mm
        pdf.drawString(3 * mm, row_y, "Centre number")
        self._digit_boxes(42 * mm, row_y - 3 * mm, 5)
        pdf.drawString(90 * mm, row_y, "Candidate number")
        self._digit_boxes(130 * mm, row_y - 3 * mm, 4)
        pdf.drawString(3 * mm, row_y - 12 * mm, "Surname")
        pdf.line(29 * mm, row_y - 13 * mm, self.width - 3 * mm, row_y - 13 * mm)
        pdf.drawString(3 * mm, row_y - 22 * mm, "Forename(s)")
        pdf.line(34 * mm, row_y - 23 * mm, self.width - 3 * mm, row_y - 23 * mm)
        pdf.drawString(3 * mm, row_y - 32 * mm, "Candidate signature")
        pdf.line(40 * mm, row_y - 33 * mm, 91 * mm, row_y - 33 * mm)
        pdf.setFont(self.font, 10)
        pdf.drawString(96 * mm, row_y - 32 * mm, "I declare this is my own work.")
        return y - box_height

    def _digit_boxes(self, x: float, y: float, count: int) -> None:
        for index in range(count):
            self.canv.rect(x + index * 7 * mm, y, 6.5 * mm, 8 * mm, stroke=1, fill=0)

    def _examiner_table(self, y: float) -> None:
        pdf = self.canv
        rows = (*self.profile.mark_rows, ("TOTAL", self.profile.total_marks))
        width = 35 * mm
        row_height = 7 * mm
        x = self.width - width
        top = y + 1 * mm
        height = (len(rows) + 1) * row_height
        pdf.setLineWidth(0.45)
        pdf.rect(x, top - height, width, height, stroke=1, fill=0)
        pdf.line(x + 21 * mm, top, x + 21 * mm, top - height)
        for index in range(1, len(rows) + 1):
            row_y = top - index * row_height
            pdf.line(x, row_y, x + width, row_y)
        pdf.setFont(self.font, 8)
        pdf.drawCentredString(x + width / 2, top - 5 * mm, "For Examiner’s Use")
        pdf.setFont(self.font, 9)
        for index, (label, marks) in enumerate(rows, start=1):
            baseline = top - (index + 0.72) * row_height
            pdf.drawCentredString(x + 10.5 * mm, baseline, str(label))
            pdf.drawCentredString(x + 28 * mm, baseline, str(marks))

    def _sections(self, y: float) -> float:
        section_data = (
            ("Materials", self.profile.materials),
            ("Instructions", self.profile.instructions),
            (
                "Information",
                (
                    f"The maximum mark for this paper is {self.profile.total_marks}.",
                    *self.profile.information,
                ),
            ),
            (
                "Advice",
                (
                    "Read each question carefully before you start your answer.",
                    "Check your answers if you have time at the end.",
                ),
            ),
        )
        for heading, lines in section_data:
            if not lines:
                continue
            self.canv.setFont(self.bold_font, 12)
            self.canv.drawString(0, y, heading)
            y -= 5 * mm
            self.canv.setFont(self.font, 11)
            for line in lines:
                available_width = (
                    self.width - 44 * mm
                    if self.profile.mark_rows
                    else self.width - 5 * mm
                )
                for wrapped in _wrap(line, self.font, 11, available_width):
                    self.canv.drawString(3 * mm, y, f"• {wrapped}")
                    y -= 4.7 * mm
            y -= 3 * mm
        return y

    def _barcode(self, y: float, *, x: float = 0) -> None:
        bits = "".join(
            f"{byte:08b}"
            for byte in hashlib.sha256(self.profile.code.encode("utf-8")).digest()[:10]
        )
        cursor = x
        for index, bit in enumerate(bits):
            width = 0.55 if index % 3 else 0.9
            if bit == "1":
                self.canv.rect(cursor, y, width, 10 * mm, stroke=0, fill=1)
            cursor += width + 0.45


class MarkSchemeCover(Flowable):
    def __init__(
        self,
        profile: CoverProfile,
        *,
        font: str,
        bold_font: str,
    ) -> None:
        super().__init__()
        self.profile = profile
        self.font = font
        self.bold_font = bold_font
        self.width = 167 * mm
        self.height = 235 * mm

    def draw(self) -> None:
        pdf = self.canv
        top = self.height
        pdf.saveState()
        pdf.setFillColor(
            colors.HexColor("#1f315f")
            if self.profile.board == "ocr"
            else colors.HexColor("#141414")
        )
        pdf.setFont(self.bold_font, 24)
        pdf.drawString(0, top - 20 * mm, "PAPER CREATOR")
        pdf.setLineWidth(0.8)
        pdf.line(0, top - 25 * mm, self.width, top - 25 * mm)
        pdf.setFillColor(colors.HexColor("#141414"))
        if self.profile.board == "ocr":
            self._draw_ocr_details(pdf, top)
        else:
            self._draw_aqa_details(pdf, top)
        pdf.restoreState()

    def _draw_aqa_details(self, pdf: object, top: float) -> None:
        y = top - 44 * mm
        for text, size, step in (
            ("A-level", 28, 13),
            (self.profile.subject.upper(), 28, 13),
            (self.profile.code, 28, 14),
            (self.profile.paper_title, 16, 11),
            ("Mark scheme", 14, 9),
            (formatted_generation_series(), 14, 11),
            ("Version 1.0 • Unofficial independent practice", 11, 0),
        ):
            pdf.setFont(
                self.bold_font
                if text
                in {
                    "A-level",
                    self.profile.subject.upper(),
                    self.profile.code,
                }
                else self.font,
                size,
            )
            pdf.drawString(0, y, text)
            y -= step * mm
        barcode_cover = QuestionPaperCover(
            self.profile,
            font=self.font,
            bold_font=self.bold_font,
        )
        barcode_cover.canv = pdf
        barcode_cover._barcode(5 * mm)

    def _draw_ocr_details(self, pdf: object, top: float) -> None:
        y = top - 40 * mm
        for text, size, step in (
            ("GCE", 18, 19),
            (self.profile.subject.title(), 18, 15),
            (f"{self.profile.code}: {self.profile.paper_title}", 16, 18),
            ("A Level", 14, 19),
            (f"Mark Scheme for {formatted_generation_series()}", 18, 0),
        ):
            pdf.setFont(self.bold_font, size)
            pdf.drawString(0, y, text)
            y -= step * mm
        pdf.setFont(self.font, 7)
        pdf.drawString(0, 4 * mm, "Paper Creator • Unofficial independent practice")


def _wrap(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    result: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            result.append(line)
            line = word
    result.append(line)
    return result


def aqa_question_cover(profile: CoverProfile, font: str, bold_font: str) -> list[Flowable]:
    return [QuestionPaperCover(profile, font=font, bold_font=bold_font)]


def ocr_question_cover(profile: CoverProfile, font: str, bold_font: str) -> list[Flowable]:
    return [QuestionPaperCover(profile, font=font, bold_font=bold_font)]


def mark_scheme_cover(profile: CoverProfile, font: str, bold_font: str) -> list[Flowable]:
    return [MarkSchemeCover(profile, font=font, bold_font=bold_font)]
