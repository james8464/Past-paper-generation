from __future__ import annotations

import hashlib
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable

from Backend.Core.document_dsl import Cover
from Backend.Core.fonts import register_fonts
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
    subject_label: str | None = None
    title_font_size: float = 27.0


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
        register_fonts("ExamCover-Medium", "ExamCover-SemiBold")
        self.width = 167 * mm
        self.height = 235 * mm

    @property
    def component(self) -> Cover:
        """Return the renderer-neutral representation used for qualification."""
        return Cover(
            title=self.profile.subject,
            subtitle=self.profile.paper_title,
            code=self.profile.code,
        )

    def draw(self) -> None:
        if self.profile.board == "ocr":
            self._draw_ocr()
        else:
            self._draw_aqa()

    def drawOn(self, canv: object, x: float, y: float, _sW: float = 0) -> None:
        # Board covers have a page grid, not a position relative to the body
        # frame (whose padding differs between the specialist renderers).
        page_width, page_height = canv._pagesize
        canv.saveState()
        canv.setFillColor(colors.white)
        canv.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        if self.profile.board == "ocr":
            super().drawOn(canv, 0, 0)
        else:
            left = 41.04 if self.profile.candidate_fields else 48.0
            self.width = 545.64 - left
            super().drawOn(canv, left, page_height - self.height - 54.0)
        canv.restoreState()

    def _draw_aqa(self) -> None:
        pdf = self.canv
        top = self.height
        booklet = (
            self.profile.subject.lower() == "economics"
            and not self.profile.candidate_fields
        )
        pdf.saveState()
        pdf.setFillColor(colors.HexColor("#141414"))
        self._wordmark(0, top - 1 * mm, "PAPER", "CREATOR")
        if booklet:
            # The 2025 Economics booklet has no candidate form or barcode.
            # Keep its separator rails independent of the branding artwork.
            pdf.setLineWidth(0.96)
            pdf.line(-5.4, top - 65.52, 499.2, top - 65.52)

        y = top - 59.5
        if self.profile.candidate_fields:
            self._candidate_box(y)
        y = top - ((311.16 if self.profile.candidate_fields else 150.0) - 54.0)
        pdf.setFont("ExamCover-Medium", self.profile.title_font_size)
        pdf.drawString(0, y, "A-level")
        y -= 36.12 if self.profile.candidate_fields else 38.16
        pdf.setFont("ExamCover-SemiBold", self.profile.title_font_size)
        pdf.drawString(
            0,
            y,
            self.profile.subject_label or self.profile.subject.upper(),
        )
        y -= 28.68 if self.profile.candidate_fields else 25.32
        pdf.setFont("ExamCover-Medium", 16)
        pdf.drawString(0, y, self.profile.paper_title)
        y -= 26.82
        pdf.setLineWidth(3.0)
        pdf.line(0, y, self.width, y)
        y -= 27.18 if self.profile.candidate_fields else 22.74

        pdf.setFont(self.font, 13)
        pdf.drawString(0, y, formatted_generation_date())
        pdf.drawCentredString(self.width * 0.58, y, "Practice session")
        pdf.drawRightString(self.width, y, f"Time allowed: {self.profile.duration}")
        y -= 27.6
        if self.profile.mark_rows:
            self._examiner_table(y)
        y = self._sections(y)
        # The cover's content origin is not the page's footer origin.
        frame_bottom = pdf._pagesize[1] - self.height - 54.0
        if booklet:
            pdf.setStrokeColor(colors.HexColor("#b3b3b3"))
            pdf.setLineWidth(0.5)
            pdf.line(-2.85, top + 54 - 762.35, 498.85, top + 54 - 762.35)
            pdf.setFont(self.bold_font, 20.04)
            # Arial's descenders extend below the source Open Sans metrics;
            # keep the complete footer inside the 5mm printable region.
            pdf.drawRightString(499.2, top + 54 - 823.2, self.profile.code)
            pdf.setFont(self.font, 6.96)
            pdf.drawString(8.88, top + 54 - 825.36, "Independent unofficial practice")
        else:
            self._barcode(17 - frame_bottom)
            pdf.setFont(self.font, 5.8)
            pdf.drawRightString(
                self.width,
                18 - frame_bottom,
                f"{self.profile.code}  •  UNOFFICIAL PRACTICE",
            )
        pdf.restoreState()

    def _draw_ocr(self) -> None:
        pdf = self.canv
        top = pdf._pagesize[1]
        left, right = 94.96, 537.5
        pdf.saveState()
        pdf.setFillColor(colors.black)
        pdf.setFont(self.bold_font, 26)
        pdf.drawString(left, top - 80, "PAPER CREATOR")
        pdf.setFont(self.font, 8)
        pdf.drawString(left, top - 95, "Independent unofficial practice")
        pdf.setFont(self.bold_font, 20)
        pdf.drawString(left, top - 124.26, formatted_generation_date())
        pdf.setFont(self.bold_font, 16)
        pdf.drawString(left, top - 150.26, f"A Level {self.profile.subject.title()}")
        pdf.setFont(self.bold_font, 14)
        pdf.drawString(left, top - 176.26, self.profile.code)
        pdf.setFont(self.font, 14)
        pdf.drawString(151, top - 176.26, self.profile.paper_title)
        pdf.setFont(self.bold_font, 11)
        pdf.drawString(left, top - 197.26, f"Time allowed: {self.profile.duration}")

        pdf.setLineWidth(0.5)
        pdf.roundRect(left, top - 328.6, 223.4, 118.6, 5, stroke=1, fill=0)
        pdf.setFont(self.font, 9)
        y = top - 223.49
        for item in self.profile.materials:
            for line in _wrap(item, self.font, 9, 208):
                pdf.drawString(101.13, y, line)
                y -= 11
        self._barcode(top - 320, x=378)

        # OCR uses a two-name, no-signature identity panel. Sharing the AQA
        # signature form changed both its geometry and its required fields.
        pdf.roundRect(left, top - 467.8, right - left, 130.4, 12, stroke=1, fill=0)
        pdf.setFont(self.font, 11)
        pdf.drawString(103.13, top - 359.11, "Please write clearly in black ink.")
        pdf.setFont(self.bold_font, 11)
        pdf.drawString(270, top - 359.11, "Do not write in the barcodes.")
        pdf.setFont(self.font, 11)
        pdf.drawString(103.13, top - 385.45, "Centre number")
        pdf.drawString(326.37, top - 385.45, "Candidate number")
        for start, count in ((182.6, 5), (421.0, 4)):
            for index in range(count):
                pdf.rect(
                    start + index * 26.3, top - 396.3, 26.3, 25.9, stroke=1, fill=0
                )
        for label, baseline in (("First name(s)", 424.78), ("Last name", 451.12)):
            pdf.drawString(103.13, top - baseline, label)
            pdf.line(182.6, top - baseline - 3, 528.4, top - baseline - 3)

        y = top - 484.81
        for heading, items in (
            ("INSTRUCTIONS", self.profile.instructions),
            (
                "INFORMATION",
                (
                    f"The total mark for this paper is {self.profile.total_marks}.",
                    "The marks for each question are shown in brackets [ ].",
                    *self.profile.information,
                ),
            ),
            ("ADVICE", ("Read each question carefully before you start your answer.",)),
        ):
            pdf.setFont(self.bold_font, 11)
            pdf.drawString(left, y, heading)
            y -= 13
            pdf.setFont(self.font, 11)
            for item in items:
                for index, line in enumerate(
                    _wrap(item, self.font, 11, right - left - 14)
                ):
                    pdf.drawString(
                        left if index == 0 else left + 14,
                        y,
                        f"• {line}" if index == 0 else line,
                    )
                    y -= 13
            y -= 13
        pdf.setFont(self.font, 8)
        pdf.drawString(left, top - 779.5, "Paper Creator • Independent practice")
        pdf.setFont(self.bold_font, 10)
        pdf.drawRightString(right, top - 779.5, "Turn over")
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
                for line_index, wrapped in enumerate(
                    _wrap(line, self.font, 11, available_width)
                ):
                    self.canv.drawString(
                        3 * mm, y, f"{'• ' if line_index == 0 else '  '}{wrapped}"
                    )
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

    def drawOn(
        self,
        canv: object,
        x: float,
        y: float,
        _sW: float = 0,
    ) -> None:
        del x, y, _sW
        width, height = canv._pagesize
        draw_mark_scheme_cover(
            canv,
            self.profile,
            width=width,
            height=height,
            font=self.font,
            bold_font=self.bold_font,
        )

    def draw(self) -> None:
        # ``drawOn`` deliberately works in page coordinates.
        return None


def draw_mark_scheme_cover(
    pdf: object,
    profile: CoverProfile,
    *,
    width: float,
    height: float,
    font: str,
    bold_font: str,
) -> None:
    pdf.saveState()
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#141414"))
    if profile.board == "ocr":
        _draw_ocr_mark_scheme_cover(
            pdf,
            profile,
            height=height,
            font=font,
            bold_font=bold_font,
        )
    else:
        _draw_aqa_mark_scheme_cover(
            pdf,
            profile,
            height=height,
            font=font,
            bold_font=bold_font,
        )
    pdf.restoreState()


def _draw_aqa_mark_scheme_cover(
    pdf: object,
    profile: CoverProfile,
    *,
    height: float,
    font: str,
    bold_font: str,
) -> None:
    register_fonts("ExamCover-Medium", "ExamCover-SemiBold")
    left = 46.8
    pdf.setFont(bold_font, 28)
    pdf.drawString(left, height - 109.1, "PAPER")
    pdf.setFont(bold_font, 11)
    pdf.drawString(left, height - 131.5, "CREATOR")
    pdf.setLineWidth(0.5)
    pdf.line(41.9, height - 147.6, 552.9, height - 147.6)

    # June 2025 source baselines, not font-dependent extraction bounding boxes.
    baselines = (190.28, 227.84, 265.94, 294.56, 323.60, 349.82, 377.12)
    if profile.subject.lower() == "economics":
        baselines = (
            (189.86, 228.02, 266.90, 296.33, 329.33, 356.57, 383.69)
            if profile.code == "7136/3"
            else (190.28, 228.32, 259.58, 290.30, 323.30, 350.54, 377.84)
        )
    rows = (
        ("A-level", "ExamCover-SemiBold", 28),
        (profile.subject.upper(), "ExamCover-SemiBold", 28),
        (profile.code, "ExamCover-SemiBold", 28),
        (profile.paper_title, "ExamCover-Medium", 16),
        ("Mark scheme", "ExamCover-SemiBold", 14),
        (
            formatted_generation_series(),
            "ExamCover-SemiBold"
            if profile.subject.lower() == "computer science"
            else "ExamCover-Medium",
            14,
        ),
        ("Version: 1.0 • Unofficial independent practice", font, 11),
    )
    for (text, face, size), baseline in zip(rows, baselines, strict=True):
        pdf.setFont(face, size)
        pdf.drawString(left, height - baseline, text)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(3)
    pdf.line(44.4, height - baselines[3] - 11.1, 552.9, height - baselines[3] - 11.1)
    pdf.setLineWidth(0.48)
    pdf.line(41.88, height - baselines[5] - 10.62, 552.9, height - baselines[5] - 10.62)

    _draw_cover_barcode(
        pdf,
        profile.code,
        x=47.9,
        y=height - 782.3,
        target_width=176.7,
        bar_height=34.0,
    )


def _draw_ocr_mark_scheme_cover(
    pdf: object,
    profile: CoverProfile,
    *,
    height: float,
    font: str,
    bold_font: str,
) -> None:
    left = 59.5
    pdf.setFillColor(colors.HexColor("#1f315f"))
    pdf.setFont(bold_font, 28)
    pdf.drawString(left, height - 58.1, "PAPER")
    pdf.setFont(bold_font, 11)
    pdf.drawString(left, height - 79.2, "CREATOR")
    pdf.setFillColor(colors.HexColor("#141414"))

    rows = (
        ("GCE", 18, 160.7),
        (profile.subject.title(), 18, 214.1),
        (f"{profile.code}: {profile.paper_title}", 16, 255.5),
        ("A Level", 14, 304.6),
        (f"Mark Scheme for {formatted_generation_series()}", 18, 360.9),
    )
    for text, size, baseline in rows:
        pdf.setFont(bold_font, size)
        pdf.drawString(left, height - baseline, text)

    pdf.setFont(font, 8)
    pdf.drawString(
        left,
        height - 824.5,
        "Paper Creator • Independent unofficial practice",
    )


def _draw_cover_barcode(
    pdf: object,
    value: str,
    *,
    x: float,
    y: float,
    target_width: float,
    bar_height: float,
) -> None:
    bits = "".join(
        f"{byte:08b}" for byte in hashlib.sha256(value.encode("utf-8")).digest()[:10]
    )
    modules = [1.0 if index % 3 else 1.6 for index in range(len(bits))]
    gap = 0.8
    scale = target_width / (sum(modules) + gap * (len(bits) - 1))
    cursor = x
    guard_width = 1.2 * scale
    pdf.rect(x, y, guard_width, bar_height, stroke=0, fill=1)
    for bit, module in zip(bits, modules, strict=True):
        bar_width = module * scale
        if bit == "1":
            pdf.rect(cursor, y, bar_width, bar_height, stroke=0, fill=1)
        cursor += bar_width + gap * scale
    pdf.rect(
        x + target_width - guard_width,
        y,
        guard_width,
        bar_height,
        stroke=0,
        fill=1,
    )


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


def aqa_question_cover(
    profile: CoverProfile, font: str, bold_font: str
) -> list[Flowable]:
    return [QuestionPaperCover(profile, font=font, bold_font=bold_font)]


def ocr_question_cover(
    profile: CoverProfile, font: str, bold_font: str
) -> list[Flowable]:
    return [QuestionPaperCover(profile, font=font, bold_font=bold_font)]


def mark_scheme_cover(
    profile: CoverProfile, font: str, bold_font: str
) -> list[Flowable]:
    return [MarkSchemeCover(profile, font=font, bold_font=bold_font)]
