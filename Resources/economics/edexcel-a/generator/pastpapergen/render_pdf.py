# The project-root bootstrap must precede imports from the shared backend.

from __future__ import annotations

import hashlib
import io
import math
import os
import re
import sys
from contextlib import suppress
from itertools import pairwise
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

_PROJECT_ROOT = str(Path(__file__).resolve().parents[5])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Backend.Core.document_dsl import (
    CanvasBarcodeStyle,
    DocumentRole,
    GlyphRuleStyle,
    draw_barcode,
    draw_glyph_answer_rules,
    renderer_contract,
)
from Backend.Core.fonts import register_fonts as _rf
from Backend.Core.generation_date import formatted_generation_date
from Backend.Core.overlay.graphs import (
    ad_as_diagram,
    consumer_producer_surplus,
    demand_supply_diagram,
    externality_diagram,
    keynesian_ad_as_diagram,
    labour_market_diagram,
    laffer_curve,
    lorenz_curve,
    monopoly_diagram,
    mr_mc_ac_diagram,
    perfect_competition_diagram,
    phillips_curve,
    ppf_diagram,
    tax_subsidy_diagram,
    trade_cycle_diagram,
)
from Backend.Core.overlay.layouts import EDEXCEL_ECONOMICS as L
from Backend.Core.subjects.economics_contracts import EconomicsSource
from pastpapergen.exam_dates import economics_exam_schedule
from pastpapergen.models import GraphParams, PaperBlueprint, QuestionBlueprint, Syllabus
from pastpapergen.notes import note_points_for_topic
from pastpapergen.source_cases import GENERIC_SOURCE_ATTRIBUTION
from pastpapergen.stimulus_data import line_chart_data, table_rows

ANSWER_LINE_GAP_PT = L.answer_line_gap
ANSWER_LINE_COLOR_HEX = L.answer_line_color
ANSWER_LINE_DASH = L.answer_line_dash
ANSWER_LINE_WIDTH_PT = 0.5
RENDERER_CONTRACT = renderer_contract(
    "pearson-edexcel",
    roles=(
        DocumentRole.QUESTION_PAPER,
        DocumentRole.MARK_SCHEME,
        DocumentRole.SOURCE_BOOKLET,
    ),
    vector_components=("economic-curve", "statistical-chart"),
)
BODY_FONT_SIZE_PT = L.body_font_size
BODY_LEADING_PT = L.body_leading
FONT_REGULAR = L.font_regular
FONT_BOLD = L.font_bold
EDEXCEL_ANSWER_RULES = GlyphRuleStyle(
    left=42.5,
    gap=ANSWER_LINE_GAP_PT,
    glyph=".",
    glyph_count=276,
    font=FONT_REGULAR,
    font_size=6,
    character_spacing=0.174,
    color=colors.HexColor(ANSWER_LINE_COLOR_HEX),
)
FONT_ITALIC = "ExamSans-Italic"
MS_FONT = "ExamMarkScheme"
MS_FONT_BOLD = "ExamMarkScheme-Bold"
MS_FONT_ITALIC = "ExamMarkScheme-Italic"
SERIF_FONT = "ExamSerif"
SERIF_BOLD_ITALIC = "ExamSerif-BoldItalic"
MS_ANSWER_WRAP_CHARS = 54
MS_PAGE_SIZE = (595.44, 841.68)
MS_PAGE_SIZES = {
    "paper_1": (595.44, 841.56),
    "paper_2": (595.56, 842.04),
    "paper_3": MS_PAGE_SIZE,
}
MS_LEFT = 80
MS_RIGHT = 560
MS_NUMBER_W = 73
MS_MARK_W = 54
MS_HEADER_H = 38
MS_CONTENT_TOP = 85
MS_CONTENT_BOTTOM = 54
MS_MAX_ROW_HEIGHT = int(MS_PAGE_SIZE[1] - MS_CONTENT_TOP - MS_CONTENT_BOTTOM)
MS_BODY_LEADING = 14
EDEXCEL_MEDIA_BOX = L.media_box or (0.0, 0.0, 651.97, 898.58)
EDEXCEL_CROP_BOX = L.crop_box or (28.35, 28.35, 623.62, 870.24)
SECTION_A_FOOTER_SAFE_Y = 128
BLANK_AXIS_WIDTH_PT = 420
BLANK_AXIS_HEIGHT_PT = 300
ANSWER_FRAME_X = 34
ANSWER_FRAME_Y = 48
ANSWER_FRAME_W = 500
ANSWER_FRAME_H = 760
ANSWER_PAGE_START_Y = 803.3
RAIL_Y = 50
RAIL_H = 760
MARK_SCHEME_MIN_PAGES = {"paper_1": 29, "paper_2": 36, "paper_3": 31}
MARK_SCHEME_TITLE_COLOR = "#003A5D"
MARK_SCHEME_ACCENT_COLOR = "#007FA3"
MARK_SCHEME_COVER_LAYOUTS = {
    "paper_1": {
        "margin": 56.7,
        "title_offset": 325.3,
        "date_offset": 416.3,
        "information_offsets": (495.4, 535.7, 576.2),
    },
    "paper_2": {
        "margin": 37.0,
        "title_offset": 285.7,
        "date_offset": 388.4,
        "information_offsets": (485.2, 515.1, 545.1),
    },
    "paper_3": {
        "margin": 42.5,
        "title_offset": 319.1,
        "date_offset": 453.7,
        "information_offsets": (574.7, 615.0, 655.4),
    },
}
CROSS_BOX_TOKEN = "{box}"
SECTION_A_INSTRUCTION_LINES = [
    "Answer ALL questions. Write your answers in the spaces provided.",
    f"Some questions must be answered with a cross in a box {CROSS_BOX_TOKEN}. If you change your",
    f"mind about an answer, put a line through the box {CROSS_BOX_TOKEN} and then mark your new",
    f"answer with a cross {CROSS_BOX_TOKEN}.",
    "You are advised to spend 30 minutes on this section.",
    "Use the data to support your answers where relevant.",
    "You may annotate and include diagrams in your answers.",
]


_rf(FONT_REGULAR, FONT_BOLD, default_fallback="Times-Roman")
_rf(FONT_ITALIC, default_fallback="Times-Italic")
_rf(MS_FONT, MS_FONT_BOLD, default_fallback="Times-Roman")
_rf(MS_FONT_ITALIC, default_fallback="Times-Italic")
_rf(SERIF_FONT, SERIF_BOLD_ITALIC, default_fallback="Times-Roman")


_TOTAL_PAPER_PAGES: int = 0


def render_question_paper(blueprint: PaperBlueprint, output_path: Path) -> None:
    global _TOTAL_PAPER_PAGES
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _TOTAL_PAPER_PAGES = _count_pages(blueprint)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    _set_pdf_metadata(pdf, blueprint, "Question paper")
    try:
        _draw_cover(pdf, blueprint)
        pdf.showPage()
        _draw_question_pages(pdf, blueprint)
        pdf.save()
    finally:
        _cleanup_graph_cache()
    _apply_edexcel_page_boxes(output_path)


def _count_pages(blueprint: PaperBlueprint) -> int:
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    _set_pdf_metadata(pdf, blueprint, "Question paper")
    global _TOTAL_PAPER_PAGES
    _TOTAL_PAPER_PAGES = 0
    _draw_cover(pdf, blueprint)
    pdf.showPage()
    _draw_question_pages(pdf, blueprint)
    pdf.save()
    buf.seek(0)
    try:
        import pymupdf as fitz
        doc = fitz.open(stream=buf, filetype="pdf")
        count = doc.page_count
        doc.close()
        return count
    except ImportError:
        return 0
    finally:
        buf.close()


def _apply_edexcel_page_boxes(output_path: Path) -> None:
    """Match Pearson question-paper bleed and crop boxes without changing A4 content."""
    try:
        import pymupdf as fitz
    except ImportError:
        return

    source = fitz.open(output_path)
    rewritten = fitz.open()
    media_x0, media_y0, media_x1, media_y1 = EDEXCEL_MEDIA_BOX
    crop_rect = fitz.Rect(*EDEXCEL_CROP_BOX)
    try:
        for page_index in range(source.page_count):
            page = rewritten.new_page(width=media_x1 - media_x0, height=media_y1 - media_y0)
            page.show_pdf_page(crop_rect, source, page_index)
            page.set_bleedbox(page.mediabox)
            page.set_cropbox(crop_rect)
            page.set_trimbox(crop_rect)
            page.set_artbox(crop_rect)

        rewritten.set_metadata(source.metadata)
        tmp_path = output_path.with_name(f"{output_path.stem}.tmp{output_path.suffix}")
        rewritten.save(tmp_path, garbage=4, deflate=True)
    finally:
        rewritten.close()
        source.close()

    os.replace(tmp_path, output_path)


def _draw_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    width, _height = A4
    _draw_crop_marks(pdf)

    panel_x = 96
    panel_y = 457
    panel_w = 440
    panel_h = 348
    grey = colors.HexColor("#666666")
    dark = colors.HexColor("#4d494b")
    pdf.setStrokeColor(grey)
    pdf.setLineWidth(1.8)
    pdf.roundRect(panel_x, panel_y, panel_w, panel_h, 9, stroke=1, fill=0)

    pdf.setFont(FONT_BOLD, 9)
    pdf.drawCentredString(panel_x + panel_w / 2, panel_y + panel_h - 10, "Please check the examination details below before entering your candidate information")

    name_y = panel_y + panel_h - 45
    pdf.roundRect(panel_x + 14, name_y, panel_w - 28, 30, 8, stroke=1, fill=0)
    pdf.line(panel_x + panel_w / 2, name_y, panel_x + panel_w / 2, name_y + 30)
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawString(panel_x + 24, name_y + 18, "Candidate surname")
    pdf.drawString(panel_x + panel_w / 2 + 8, name_y + 18, "Other names")

    box_y = name_y - 42
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawString(panel_x + 16, box_y + 33, "Centre Number")
    _draw_boxes(pdf, panel_x + 17, box_y, 5, size=22)
    pdf.drawString(panel_x + 140, box_y + 33, "Candidate Number")
    _draw_boxes(pdf, panel_x + 140, box_y, 4, size=22)

    y = box_y - 22
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(panel_x + 14, y, "Level 3 GCE · Independent practice")
    y -= 50
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 28, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(panel_x + 22, y + 8, _exam_date_line(blueprint.paper_id))

    y -= 36
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 14, y + 11, f"{_exam_session(blueprint.paper_id)} (Time: {blueprint.duration_minutes // 60} hours)")
    pdf.rect(panel_x + 216, y, 58, 30, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 221, y + 18, "Paper")
    pdf.drawString(panel_x + 221, y + 7, "reference")
    pdf.setFillColor(dark)
    pdf.roundRect(panel_x + 274, y, 125, 30, 7, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 23)
    pdf.drawCentredString(panel_x + 337, y + 8, blueprint.paper_code)
    pdf.setFillColor(colors.black)

    y -= 90
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 96, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 24)
    pdf.drawString(panel_x + 22, y + 71.5, "Economics A")
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(panel_x + 22, y + 43, "Advanced")
    paper_number = blueprint.paper_id[-1]
    pdf.drawString(panel_x + 22, y + 26, f"PAPER {paper_number}: {blueprint.title}")
    square_y = y + 81
    for offset, shade in enumerate(("#b0b0b0", "#777777", "#4d494b")):
        pdf.setFillColor(colors.HexColor(shade))
        pdf.rect(panel_x + panel_w - 52 + offset * 14, square_y, 12, 12, stroke=0, fill=1)
    pdf.setFillColor(colors.black)

    y -= 45
    required_h = 40
    pdf.roundRect(panel_x + 14, y, panel_w - 88, required_h, 7, stroke=1, fill=0)
    pdf.roundRect(panel_x + panel_w - 70, y, 56, required_h, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 25, "You do not need any other materials.")
    pdf.setFont(FONT_BOLD, 8)
    pdf.drawCentredString(panel_x + panel_w - 42, y + 25, "Total Marks")

    text_x = 96
    y = 432
    _draw_front_section(
        pdf,
        text_x,
        y,
        "Instructions",
        [
            "Use black ink or ball-point pen.",
            "Fill in the boxes at the top of this page with your name, centre number and candidate number.",
            _instruction_line(blueprint),
            "Answer the questions in the spaces provided - there may be more space than you need.",
            "Calculators may be used.",
        ],
    )
    y -= 155.8
    _draw_front_section(
        pdf,
        text_x,
        y,
        "Information",
        [
            f"The total mark for this paper is {blueprint.total_marks}.",
            "The marks for each question are shown in brackets - use this as a guide as to how much time to spend on each question.",
        ],
    )
    y -= 80.7
    _draw_front_section(
        pdf,
        text_x,
        y,
        "Advice",
        [
            "Read each question carefully before you start to answer it.",
            "Try to answer every question.",
            "Check your answers if you have time at the end.",
        ],
    )
    _draw_turn_over(pdf, width - 25, 102.8)
    paper_code = blueprint.paper_code.partition("/")[0]
    barcode_text = f"{paper_code}01"
    pdf.setFont(FONT_REGULAR, 15)
    pdf.drawString(58, 43, barcode_text)
    pdf.setFont(FONT_REGULAR, 5.5)
    pdf.drawString(58, 31, f"Unofficial practice material, {economics_exam_schedule(blueprint.paper_id).date.year}.")
    _draw_fake_barcode(pdf, width / 2 - 105, 32, barcode_text)


def _draw_turn_over(pdf: canvas.Canvas, right_x: float, y: float) -> None:
    pdf.setFont(SERIF_BOLD_ITALIC, 12)
    pdf.drawRightString(right_x - 14, y, "Turn over")
    pdf.setFillColor(colors.HexColor("#b0b0b0"))
    pdf.setStrokeColor(colors.HexColor("#b0b0b0"))
    pdf.line(right_x - 6, y + 3, right_x + 1, y)
    pdf.line(right_x + 1, y, right_x - 6, y - 3)
    pdf.setFillColor(colors.black)
    pdf.setStrokeColor(colors.black)


def _exam_date_line(paper_id: str) -> str:
    return formatted_generation_date()


def _exam_session(paper_id: str) -> str:
    return economics_exam_schedule(paper_id).session


def _draw_boxes(pdf: canvas.Canvas, x: float, y: float, count: int, size: int = 13) -> None:
    for index in range(count):
        pdf.rect(x + index * (size + 1), y, size, size, stroke=1, fill=0)


def _draw_front_section(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    heading: str,
    lines: list[str],
) -> None:
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(x, y, heading)
    pdf.setFont(FONT_REGULAR, 11)
    y -= 18
    for line in lines:
        wrapped = _wrap(line, 74)
        for idx, part in enumerate(wrapped):
            if idx == 0:
                pdf.circle(x + 3, y + 4, 3, stroke=0, fill=1)
            pdf.drawString(x + 15, y, part)
            y -= 14


def _draw_crop_marks(pdf: canvas.Canvas) -> None:
    width, height = A4
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.6)
    marks = [
        (26, height - 26, 14, 0, 0, -14),
        (width - 40, height - 26, 14, 0, 0, -14),
        (26, 26, 14, 0, 0, 14),
        (width - 40, 26, 14, 0, 0, 14),
    ]
    for x, y, dx, dy, vx, vy in marks:
        pdf.line(x, y, x + dx, y + dy)
        pdf.line(x, y, x + vx, y + vy)
    pdf.setLineWidth(2.4)
    pdf.line(0, height - 56, 50, height - 56)
    pdf.line(0, 55, 50, 55)
    pdf.line(width - 50, height - 56, width, height - 56)
    pdf.line(width - 50, 55, width, 55)
    pdf.setLineWidth(1)


_BARCODE_CHAR_PATTERNS: dict[str, list[int]] = {
    c: [1, 2, 1, 3] if (ord(c) % 4 == 0) else [2, 1, 3, 1] if (ord(c) % 4 == 1) else [3, 1, 1, 2] if (ord(c) % 4 == 2) else [1, 3, 2, 1]
    for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}


def _encode_barcode(barcode_text: str) -> list[int]:
    encoded: list[int] = []
    for char in barcode_text.upper():
        pattern = _BARCODE_CHAR_PATTERNS.get(char, [2, 2, 2, 2])
        encoded.extend(pattern)
    encoded = [encoded[0]] + [max(w, 1) for w in encoded[1:]]
    return encoded


def _draw_fake_barcode(pdf: canvas.Canvas, x: float, y: float, caption: str) -> None:
    module = 2.7
    draw_barcode(
        pdf,
        x=x,
        y=y,
        caption=caption,
        style=CanvasBarcodeStyle(
            widths=tuple(width * module for width in _encode_barcode(caption)),
            repetitions=1,
            height=28,
            bar_y_offset=13,
            gap=module,
            font=FONT_REGULAR,
            font_size=6.5,
            caption_center_offset=0,
            spread_caption=True,
        ),
    )


def _instruction_line(blueprint: PaperBlueprint) -> str:
    if blueprint.paper_id == "paper_3":
        return (
            "There are two sections in this question paper. In each section, answer all "
            "short questions and one extended-response question."
        )
    return (
        "There are three sections in this question paper. Answer all questions from "
        "Section A and Section B. Answer one question from Section C."
    )


def _draw_question_pages(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    if blueprint.paper_id == "paper_3":
        _draw_paper_3_pages(pdf, blueprint)
        return

    _width, _height = A4
    margin = 76
    y = _prepare_answer_page(pdf, blueprint, 2)
    current_section = None
    page_number = 2
    questions = blueprint.questions
    for idx, question in enumerate(questions):
        next_question = questions[idx + 1] if idx + 1 < len(questions) else None
        if question.section != current_section:
            if current_section is not None:
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1
                y = _prepare_answer_page(pdf, blueprint, page_number)
            if blueprint.paper_id in {"paper_1", "paper_2"} and question.section == "B":
                section_b_start = 10 if blueprint.paper_id == "paper_1" else 12
                while page_number < section_b_start:
                    _draw_question_footer(pdf, blueprint, page_number)
                    pdf.showPage()
                    page_number += 1
                    y = _prepare_answer_page(pdf, blueprint, page_number)
            current_section = question.section
            y = _draw_section_intro(pdf, blueprint, current_section, y)
            if blueprint.paper_id in {"paper_1", "paper_2"} and question.section == "B":
                page_number, y = _draw_section_b_source_pages(pdf, blueprint, questions, page_number, y)
                y = _draw_section_b_prompt_page(pdf, questions, y)
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1
                y = _prepare_answer_page(pdf, blueprint, page_number)
            if blueprint.paper_id in {"paper_1", "paper_2"} and question.section == "C":
                section_c = [item for item in questions if item.section == "C"]
                y = _draw_section_c_choice_page(pdf, section_c, y)
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1
                y = _prepare_answer_page(pdf, blueprint, page_number)
                _draw_section_c_answer_pages(pdf, blueprint, section_c, page_number, margin, y)
                return
        if blueprint.paper_id in {"paper_1", "paper_2"} and question.section == "A":
            page_number, y = _draw_section_a_question(pdf, blueprint, question, page_number, margin, y)
            if next_question is None or next_question.section != question.section:
                current_section = None
            continue
        y = _draw_question(
            pdf,
            question,
            margin,
            y,
            fill_answer_page=blueprint.paper_id in {"paper_1", "paper_2"} and question.section == "B",
        )
        pages_needed = _extra_answer_pages(blueprint.paper_id, question)
        if pages_needed:
            for _ in range(pages_needed):
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1
                y = _prepare_answer_page(pdf, blueprint, page_number)
                y = _draw_continuation_lines(pdf, margin, y, question_number=question.number)
        pages_needed = _extra_answer_pages(blueprint.paper_id, question)
        if _force_new_page_after_question(blueprint.paper_id, question):
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = _prepare_answer_page(pdf, blueprint, page_number)
            if next_question is None or next_question.section != question.section:
                current_section = None
            continue
        if (
            y < 130
            and next_question is not None
            and next_question.section == current_section
        ):
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = _prepare_answer_page(pdf, blueprint, page_number)
    _draw_question_footer(pdf, blueprint, page_number, is_last=True)


def _draw_paper_3_pages(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    page_number = 2
    margin = 48
    sections = ("A", "B")

    for section_index, section in enumerate(sections):
        questions = [question for question in blueprint.questions if question.section == section]

        for source_page in range(3):
            y = _prepare_answer_page(pdf, blueprint, page_number)
            _draw_paper_3_source_page(pdf, questions, section, source_page, y)
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1

        y = _prepare_answer_page(pdf, blueprint, page_number)
        _draw_paper_3_question_summary(pdf, questions, y)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1

        for question, allocated_pages in zip(questions[:3], (1, 2, 3), strict=True):
            for answer_page in range(allocated_pages):
                y = _prepare_answer_page(pdf, blueprint, page_number)
                if answer_page == 0:
                    y = _draw_question(pdf, question, margin, y, fill_answer_page=True)
                else:
                    y = _draw_continuation_lines(pdf, margin, y, question.number)
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1

        for answer_page in range(6):
            y = _prepare_answer_page(pdf, blueprint, page_number)
            if answer_page == 0:
                y = _draw_paper_3_choice_header(pdf, questions[3:], y)
                _draw_answer_lines_until(pdf, margin, y, 520)
            else:
                _draw_continuation_lines(pdf, margin, y, questions[3].number)

            last_section_page = answer_page == 5
            if last_section_page:
                pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
                question_number = questions[0].number.split("(")[0]
                pdf.drawRightString(520, 122, f"(Total for Question {question_number} = 50 marks)")
                pdf.drawRightString(520, 98, f"TOTAL FOR SECTION {section} = 50 MARKS")
                if section_index == len(sections) - 1:
                    pdf.drawRightString(520, 74, f"TOTAL FOR PAPER = {blueprint.total_marks} MARKS")

            is_last_answer_page = section_index == len(sections) - 1 and last_section_page
            _draw_question_footer(pdf, blueprint, page_number, is_last=is_last_answer_page)
            if not is_last_answer_page:
                pdf.showPage()
                page_number += 1

    _draw_trailing_blank_pages(pdf, blueprint, page_number, count=3)


def _draw_paper_3_source_page(
    pdf: canvas.Canvas,
    questions: list,
    section: str,
    source_page: int,
    y: float,
) -> None:
    width, _ = A4
    margin = 76
    y = min(y, ANSWER_FRAME_Y + ANSWER_FRAME_H - 42)
    case_title = questions[0].source_title if questions else "Economic context"

    if source_page == 0:
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawCentredString(width / 2, y, f"SECTION {section}")
        y -= 22
        question_number = "1" if section == "A" else "2"
        figures = "Figures 1 and 2" if section == "A" else "Figure 3"
        extracts = "A to C" if section == "A" else "D to F"
        instructions = [
            f"Read {figures} and the extracts ({extracts}) before answering Question {question_number}.",
            (
                f"Answer ALL Questions {question_number}(a) to {question_number}(c), and EITHER "
                f"Question {question_number}(d) OR {question_number}(e)."
            ),
            "Write your answers in the spaces provided.",
            "You are advised to spend 1 hour on this section.",
        ]
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        for line in instructions:
            pdf.drawCentredString(width / 2, y, line)
            y -= 14
        y -= 10
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawString(margin, y, f"Question {question_number}")
        y -= 18
        for title_line in _wrap(case_title, 66):
            pdf.drawString(margin, y, title_line)
            y -= BODY_LEADING_PT
        y -= 11

        if questions[0].source_instance is not None:
            if section == "A":
                y = _draw_case_source_figure(pdf, margin, y, 1, questions[0].source_instance)
                _draw_case_source_figure(pdf, margin, y - 35, 2, questions[1].source_instance)
            else:
                y = _draw_case_source_figure(pdf, margin, y, 3, questions[0].source_instance)
                _draw_paper_3_extract(pdf, margin, y - 25, "Extract D", "Recent changes in the case-study market", questions[0].source_text)
            return

        if section == "A":
            _draw_paper_3_line_figure(
                pdf,
                margin,
                y - 210,
                430,
                190,
                1,
                f"Price index in {case_title.lower()}, 2021–2025",
                questions[0].source_text,
            )
            _draw_paper_3_bar_figure(
                pdf,
                margin,
                y - 455,
                430,
                205,
                2,
                f"Output and investment in {case_title.lower()}, 2021–2025",
                questions[1].source_text,
            )
            return

        _draw_paper_3_table_figure(
            pdf,
            margin,
            y - 150,
            430,
            126,
            3,
            f"Selected indicators for {case_title.lower()}",
            questions[0].source_text,
        )
        _draw_paper_3_extract(
            pdf,
            margin,
            y - 185,
            "Extract D",
            "Recent changes in the case-study market",
            questions[0].source_text,
        )
        return

    if section == "A" and source_page == 1:
        y = _draw_paper_3_extract(
            pdf,
            margin,
            y,
            "Extract A",
            "Prices, incentives and market adjustment",
            " ".join(dict.fromkeys([questions[0].source_text, questions[1].source_text])),
        )
        _draw_paper_3_extract(
            pdf,
            margin,
            y - 12,
            "Extract B",
            "Effects on firms, workers and consumers",
            questions[2].source_text,
        )
        return

    if section == "A":
        combined = f"{questions[3].source_text} {questions[4].source_text}"
        _draw_paper_3_extract(
            pdf,
            margin,
            y,
            "Extract C",
            "The wider economic debate",
            combined,
        )
        return

    if source_page == 1:
        combined = " ".join(dict.fromkeys(q.source_text for q in questions[1:4]))
        _draw_paper_3_extract(
            pdf,
            margin,
            y,
            "Extract E",
            "Growth, costs and policy constraints",
            combined,
        )
        return

    _draw_paper_3_extract(
        pdf,
        margin,
        y,
        "Extract F",
        "Long-run opportunities and risks",
        questions[4].source_text,
    )


def _draw_case_source_figure(pdf, x, y, number, source):
    """A figure is a view of source cells, never a random hash illustration."""
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(x, y, f"Figure {number}: illustrative case information")
    y -= 20
    if source.rows:
        for row in source.rows:
            labels = [cell.printed() for cell in row]
            pdf.setFont(FONT_REGULAR, 9)
            pdf.rect(x, y - 24, 430, 24, stroke=1, fill=0)
            pdf.line(x + 310, y, x + 310, y - 24)
            pdf.drawString(x + 6, y - 16, labels[0])
            pdf.drawString(x + 318, y - 16, labels[1])
            y -= 24
    else:
        pdf.setFont(FONT_REGULAR, 9)
        for line in _wrap(source.context, 84):
            pdf.drawString(x, y, line)
            y -= 12
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawString(x, y - 15, "Illustrative assumptions; not official statistics.")
    return y - 25


def _draw_paper_3_extract(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    label: str,
    heading: str,
    text: str,
) -> float:
    width, _ = A4
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, label)
    y -= 15
    pdf.drawString(x, y, heading)
    y -= 18
    pdf.setFont(FONT_REGULAR, 9)
    for line_number, line in enumerate(_wrap(text, 82), start=1):
        if y < 92:
            raise ValueError("Candidate source does not fit its printed page; refusing to truncate it")
        pdf.drawString(x, y, line)
        if line_number % 5 == 0:
            pdf.setFont(FONT_REGULAR, 7.5)
            pdf.drawRightString(width - 90, y + 1, str(line_number))
            pdf.setFont(FONT_REGULAR, 9)
        y -= 11
    pdf.setFont(FONT_REGULAR, 7.5)
    pdf.drawRightString(width - 82, y - 2, GENERIC_SOURCE_ATTRIBUTION)
    return y - 24


def _paper_3_values(text: str, count: int, low: int, high: int) -> list[int]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    span = high - low + 1
    return [low + digest[index] % span for index in range(count)]


def _draw_paper_3_line_figure(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    number: int,
    title: str,
    seed_text: str,
    *,
    two_series: bool = False,
) -> None:
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x, y + height + 16, f"Figure {number}: {title}")
    chart_x = x + 42
    chart_y = y + 22
    chart_w = width - 55
    chart_h = height - 42
    pdf.setStrokeColor(colors.HexColor("#777777"))
    pdf.setLineWidth(0.6)
    pdf.line(chart_x, chart_y, chart_x, chart_y + chart_h)
    pdf.line(chart_x, chart_y, chart_x + chart_w, chart_y)
    values = _paper_3_values(seed_text, 13, 24, 92)
    second = _paper_3_values(seed_text[::-1], 13, 18, 84)
    labels = ("Jan", "", "Mar", "", "May", "", "Jul", "", "Sep", "", "Nov", "", "Jan")
    for index, label in enumerate(labels):
        point_x = chart_x + index * chart_w / (len(labels) - 1)
        pdf.setFont(FONT_REGULAR, 7.5)
        if label:
            pdf.drawCentredString(point_x, chart_y - 13, label)
    for tick in range(0, 101, 20):
        tick_y = chart_y + tick / 100 * chart_h
        pdf.setStrokeColor(colors.HexColor("#dddddd"))
        pdf.line(chart_x, tick_y, chart_x + chart_w, tick_y)
        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.setFont(FONT_REGULAR, 7)
        pdf.drawRightString(chart_x - 6, tick_y - 2, str(tick))
    _draw_paper_3_series(pdf, chart_x, chart_y, chart_w, chart_h, values, colors.black)
    if two_series:
        _draw_paper_3_series(pdf, chart_x, chart_y, chart_w, chart_h, second, colors.HexColor("#777777"))
        pdf.setFont(FONT_REGULAR, 7.5)
        pdf.setFillColor(colors.black)
        pdf.drawString(chart_x + 8, y + 4, "Output index")
        pdf.setFillColor(colors.HexColor("#666666"))
        pdf.drawString(chart_x + 78, y + 4, "Investment index")
    pdf.setFillColor(colors.black)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)


def _draw_paper_3_bar_figure(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    number: int,
    title: str,
    seed_text: str,
) -> None:
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x, y + height + 16, f"Figure {number}: {title}")
    chart_x = x + 42
    chart_y = y + 28
    chart_w = width - 55
    chart_h = height - 52
    pdf.setStrokeColor(colors.HexColor("#777777"))
    pdf.setLineWidth(0.6)
    pdf.line(chart_x, chart_y, chart_x, chart_y + chart_h)
    pdf.line(chart_x, chart_y, chart_x + chart_w, chart_y)
    primary = _paper_3_values(seed_text, 18, 8, 72)
    secondary = _paper_3_values(seed_text[::-1], 18, 2, 18)
    bar_w = chart_w / 24
    for index, (first, second) in enumerate(zip(primary, secondary, strict=True)):
        bar_x = chart_x + index * chart_w / 18 + 2
        first_h = first / 100 * chart_h
        second_h = second / 100 * chart_h
        pdf.setFillColor(colors.HexColor("#b8b8b8"))
        pdf.rect(bar_x, chart_y, bar_w, first_h, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.rect(bar_x, chart_y, bar_w, min(second_h, first_h), stroke=0, fill=1)
        if index % 3 == 0 or index == 17:
            pdf.setFillColor(colors.black)
            pdf.setFont(FONT_REGULAR, 7)
            pdf.drawCentredString(bar_x + bar_w / 2, chart_y - 13, str(2008 + index)[-2:])
    pdf.setFillColor(colors.HexColor("#b8b8b8"))
    pdf.rect(chart_x + 80, y + 4, 10, 8, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    pdf.setFont(FONT_REGULAR, 7.5)
    pdf.drawString(chart_x + 94, y + 4, "Output index")
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.rect(chart_x + 170, y + 4, 10, 8, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    pdf.drawString(chart_x + 184, y + 4, "Investment index")
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)


def _draw_paper_3_series(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    values: list[int],
    colour,
) -> None:
    pdf.setStrokeColor(colour)
    pdf.setFillColor(colour)
    pdf.setLineWidth(1.3)
    points = [
        (x + index * width / (len(values) - 1), y + value / 100 * height)
        for index, value in enumerate(values)
    ]
    for first, second in pairwise(points):
        pdf.line(first[0], first[1], second[0], second[1])
    for point_x, point_y in points:
        pdf.circle(point_x, point_y, 2.2, stroke=1, fill=1)


def _draw_paper_3_table_figure(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    number: int,
    title: str,
    seed_text: str,
) -> None:
    values = _paper_3_values(seed_text, 8, 4, 96)
    rows = (
        ("Market share (%)", values[0], values[1]),
        ("Price index", values[2] + 60, values[3] + 60),
        ("Investment growth (%)", values[4] / 10, values[5] / 10),
        ("Employment (000s)", values[6] + 40, values[7] + 40),
    )
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x, y + height + 16, f"Figure {number}: {title}")
    row_h = height / 5
    columns = (x, x + width * 0.5, x + width * 0.75, x + width)
    pdf.setFillColor(colors.HexColor("#e5e5e5"))
    pdf.rect(x, y + height - row_h, width, row_h, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    for row in range(6):
        line_y = y + row * row_h
        pdf.line(x, line_y, x + width, line_y)
    for column in columns:
        pdf.line(column, y, column, y + height)
    pdf.setFont(FONT_BOLD, 8)
    pdf.drawCentredString((columns[1] + columns[2]) / 2, y + height - 16, "2023")
    pdf.drawCentredString((columns[2] + columns[3]) / 2, y + height - 16, "2025")
    pdf.setFont(FONT_REGULAR, 8)
    for index, (label, first, second) in enumerate(rows):
        baseline = y + height - (index + 2) * row_h + 8
        pdf.drawString(x + 6, baseline, label)
        pdf.drawCentredString((columns[1] + columns[2]) / 2, baseline, f"{first:g}")
        pdf.drawCentredString((columns[2] + columns[3]) / 2, baseline, f"{second:g}")


def _draw_paper_3_question_summary(pdf: canvas.Canvas, questions: list, y: float) -> None:
    width, _ = A4
    x = 76
    for index, question in enumerate(questions):
        if index == 3:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            pdf.drawString(x, y, "EITHER")
            y -= 20
        elif index == 4:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            pdf.drawString(x, y, "OR")
            y -= 20
        before = y
        y = _draw_question_prompt(pdf, question.number, question.prompt, x, y)
        pdf.setFillColor(colors.HexColor("#666666"))
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({question.marks})")
        pdf.setFillColor(colors.black)
        y -= 22 if question.marks < 25 else 30
        if before - y < 42:
            y -= 8


def _draw_paper_3_choice_header(pdf: canvas.Canvas, questions: list, y: float) -> float:
    width, _ = A4
    x = 76
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, "EITHER")
    y -= 20
    y = _draw_paper_3_choice_prompt(pdf, questions[0], x, y)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({questions[0].marks})")
    pdf.setFillColor(colors.black)
    y -= 20
    pdf.drawString(x, y, "OR")
    y -= 20
    y = _draw_paper_3_choice_prompt(pdf, questions[1], x, y)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({questions[1].marks})")
    pdf.setFillColor(colors.black)
    y -= 24
    instruction_lines = (
        f"Indicate which question you are answering by marking a cross in the box {CROSS_BOX_TOKEN}. If you change your",
        f"mind, put a line through the box {CROSS_BOX_TOKEN} and then indicate your new question with a cross {CROSS_BOX_TOKEN}.",
    )
    for line in instruction_lines:
        _draw_centred_instruction_line(pdf, width / 2, y, line)
        y -= BODY_LEADING_PT
    y -= 12
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, "Chosen question number:")
    cursor = x + 190
    for question in questions:
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawString(cursor, y, f"Question {question.number}")
        pdf.rect(cursor + 82, y - 1, 9, 9, stroke=1, fill=0)
        cursor += 142
    y -= 26
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, "Write your answer here:")
    return y - 24


def _draw_paper_3_choice_prompt(pdf: canvas.Canvas, question, x: float, y: float) -> float:
    parsed = _split_subquestion_number(question.number)
    part = parsed[1] if parsed else question.number
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    pdf.drawString(x + 24, y, f"({part})")
    lines = _wrap(question.prompt, 62)
    for index, line in enumerate(lines):
        pdf.drawString(x + 48, y - index * BODY_LEADING_PT, line)
    return y - max(1, len(lines)) * BODY_LEADING_PT


def _draw_trailing_blank_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    page_number: int,
    *,
    count: int,
) -> None:
    width, height = A4
    for offset in range(1, count + 1):
        pdf.showPage()
        blank_page_number = page_number + offset
        _prepare_answer_page(pdf, blueprint, blank_page_number)
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawCentredString(width / 2, height / 2 - 6.4, "BLANK PAGE")
        _draw_question_footer(
            pdf,
            blueprint,
            blank_page_number,
            is_last=True,
        )


def _force_new_page_after_question(paper_id: str, question) -> bool:
    if paper_id == "paper_3" and question.number.endswith("(e)"):
        return False
    if paper_id in {"paper_1", "paper_2"}:
        return question.section in {"A", "B"} or question.marks == 25
    return question.section in {"A", "B"}


def _extra_answer_pages(paper_id: str, question) -> int:
    if paper_id == "paper_3" and question.marks == 25:
        return 6 if question.number.endswith("(d)") else 5
    if question.marks == 25:
        return 4
    if paper_id in {"paper_1", "paper_2"} and question.section == "A":
        return 1
    if paper_id not in {"paper_1", "paper_2"} or question.section != "B":
        return 0
    return {5: 0, 8: 1, 10: 2, 12: 2, 15: 3}.get(question.marks, 0)


def _draw_section_b_prompt_page(pdf: canvas.Canvas, questions: list, y: float) -> float:
    width, _ = A4
    section_b = [question for question in questions if question.section == "B"]
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    first_row = True
    for question in section_b:
        parsed = _split_subquestion_number(question.number)
        base, part = parsed if parsed else (question.number, "")
        prompt_lines = _wrap(question.prompt, 58)
        if first_row:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            pdf.drawString(70, y, base)
            first_row = False
        pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
        if part:
            pdf.drawString(92, y, f"({part})")
            text_x = 112
        else:
            text_x = 92
        for index, line in enumerate(prompt_lines):
            pdf.drawString(text_x, y - index * BODY_LEADING_PT, line)
        pdf.setFillColor(colors.HexColor("#666666"))
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawRightString(width - 76, y - (len(prompt_lines) - 1) * BODY_LEADING_PT - 2, f"({question.marks})")
        pdf.setFillColor(colors.black)
        y -= max(1, len(prompt_lines)) * BODY_LEADING_PT + 22
    return y


def _draw_section_b_source_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    questions: list,
    page_number: int,
    y: float,
) -> tuple[int, float]:
    section_b = [question for question in questions if question.section == "B"]
    extracts = _section_b_extracts(section_b)
    groups = [[extract] for extract in extracts] if blueprint.paper_id == "paper_2" else [extracts[:2], extracts[2:]]
    for index, group in enumerate(groups):
        y = _draw_section_b_extract_block(
            pdf,
            section_b,
            group,
            y,
            include_question_title=index == 0,
        )
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)
    return page_number, y


def _section_b_extracts(section_b: list) -> list[tuple[str, str]]:
    if not section_b:
        return []
    texts = [question.source_text for question in section_b]
    indices = [0, 1, 2, 4 if len(texts) > 4 else 3]
    labels = ["Extract A", "Extract B", "Extract C", "Extract D"]
    return [(label, texts[min(index, len(texts) - 1)]) for label, index in zip(labels, indices, strict=True)]


def _draw_section_b_extract_block(
    pdf: canvas.Canvas,
    section_b: list,
    extracts: list[tuple[str, str]],
    y: float,
    include_question_title: bool = True,
) -> float:
    margin = 76
    width, _ = A4
    if include_question_title:
        first_question = section_b[0].number.split("(")[0] if section_b else "6"
        source_title = section_b[0].source_title.split(":", 1)[0] if section_b else "Economic context"
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(margin, y, f"Question {first_question}")
        y -= 18
        pdf.drawString(margin, y, source_title)
        y -= 24
    for extract_index, (label, text) in enumerate(extracts):
        if extract_index:
            y -= 8
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(margin, y, label)
        y -= 14
        pdf.setFont(FONT_REGULAR, 9)
        for line_index, line in enumerate(_wrap(text, 76), start=1):
            pdf.drawString(margin, y, line)
            if line_index % 5 == 0:
                pdf.setFont(FONT_REGULAR, 7.5)
                pdf.drawRightString(width - 88, y + 1, str(line_index))
                pdf.setFont(FONT_REGULAR, 9)
            y -= 11
        pdf.setFont(FONT_REGULAR, 7.5)
        pdf.setFont(FONT_REGULAR, 7.5)
        pdf.drawRightString(width - 94, y - 3, GENERIC_SOURCE_ATTRIBUTION)
        y -= 22
    return y


def _draw_section_c_choice_page(pdf: canvas.Canvas, section_c: list, y: float) -> float:
    width, _ = A4
    for index, question in enumerate(section_c):
        if index:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            pdf.drawString(72, y, "OR")
            y -= 24
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawString(72, y, question.number)
        pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
        source_lines = _wrap(question.source_text, 72)
        for line_index, line in enumerate(source_lines):
            pdf.drawString(92, y - line_index * BODY_LEADING_PT, line)
        y -= max(1, len(source_lines)) * BODY_LEADING_PT + 8
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawString(92, y, GENERIC_SOURCE_ATTRIBUTION)
        y -= 24
        pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
        prompt_lines = _wrap(question.prompt, 70)
        for line in prompt_lines:
            pdf.drawString(92, y, line)
            y -= BODY_LEADING_PT
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawRightString(width - 76, y + 2, f"(Total for Question {question.number} = {question.marks} marks)")
        y -= 28
    return y


def _draw_section_c_answer_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    section_c: list,
    page_number: int,
    x: float,
    y: float,
) -> None:
    width, _ = A4
    answer_pages = 6
    for index in range(answer_pages):
        if index == 0:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            instruction = (
                "Indicate which question you are answering by marking a cross in the box. "
                "If you change your mind, put a line through the box and then indicate your "
                "new question with a cross."
            )
            for line in _wrap(instruction, 78):
                pdf.drawCentredString(width / 2, y, line)
                y -= BODY_LEADING_PT
            y -= 14
            pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
            pdf.drawString(x, y, "Chosen question number:")
            cursor = x + 190
            for question in section_c:
                pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
                pdf.drawString(cursor, y, f"Question {question.number}")
                pdf.rect(cursor + 76, y - 1, 9, 9, stroke=1, fill=0)
                cursor += 132
            y -= 28
            pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
            pdf.drawString(x, y, "Write your answer here:")
            y -= 28
        bottom_y = 154 if index == answer_pages - 1 else 90
        _draw_answer_lines_until(pdf, x, y, width - x, bottom_y=bottom_y)
        if index == answer_pages - 1:
            pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
            pdf.drawRightString(width - x, 122, "TOTAL FOR SECTION C = 25 MARKS")
            pdf.drawRightString(width - x, 98, f"TOTAL FOR PAPER = {blueprint.total_marks} MARKS")
            _draw_question_footer(pdf, blueprint, page_number, is_last=True)
            return
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)


def _draw_continuation_lines(pdf: canvas.Canvas, x: float, y: float, question_number: str = "") -> float:
    if question_number:
        pdf.setFont(FONT_ITALIC, 8)
        pdf.setFillColor(colors.HexColor("#666666"))
        pdf.drawString(x, y + 6, f"Question {question_number} continued ...")
        pdf.setFillColor(colors.black)
        y -= 16
        pdf.setStrokeColor(colors.HexColor("#cccccc"))
        pdf.setLineWidth(0.35)
        pdf.line(x, y, 520, y)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(1)
        y -= 12
    return _draw_answer_lines_until(pdf, x, y, 520)


def _draw_answer_page_header(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int) -> None:
    return


def _draw_watermark(pdf: canvas.Canvas) -> None:
    return


def _prepare_answer_page(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int) -> float:
    _width, _height = A4
    _draw_crop_marks(pdf)
    _draw_watermark(pdf)
    _draw_answer_page_header(pdf, blueprint, page_number)
    _draw_do_not_write_rail(pdf, page_number)
    pdf.setStrokeColor(colors.HexColor("#9d9d9d"))
    pdf.setLineWidth(1.6)
    pdf.roundRect(ANSWER_FRAME_X, ANSWER_FRAME_Y, ANSWER_FRAME_W, ANSWER_FRAME_H, 8, stroke=1, fill=0)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    return ANSWER_PAGE_START_Y


def _draw_do_not_write_rail(pdf: canvas.Canvas, page_number: int) -> None:
    width, _height = A4
    is_left = page_number % 2 == 1
    rail_x = -2.7 if is_left else width - 36.8
    label_positions = (
        (182.5, 426.3, 673.0)
        if is_left
        else (178.9, 425.6, 669.4)
    )
    pdf.setFillColor(colors.HexColor("#f0f0f0"))
    pdf.rect(rail_x, RAIL_Y, 21, RAIL_H, stroke=0, fill=1)
    _draw_hatched_rail(pdf, rail_x, RAIL_Y, 21, RAIL_H)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.setFont(FONT_BOLD, 12)
    for y in label_positions:
        pdf.saveState()
        pdf.translate(rail_x + 14, y)
        pdf.rotate(270)
        pdf.drawCentredString(0, 0, "DO NOT WRITE IN THIS AREA")
        pdf.restoreState()
    _draw_staple_marks(pdf, page_number)
    pdf.setFillColor(colors.black)


def _draw_staple_marks(pdf: canvas.Canvas, page_number: int) -> None:
    width, height = A4
    x = 12 if page_number % 2 == 1 else width - 15
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.setStrokeColor(colors.HexColor("#999999"))
    pdf.setLineWidth(0.5)
    for y in (height - 28, 270, 570):
        pdf.circle(x, y, 2.5, stroke=1, fill=0)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)


def _draw_hatched_rail(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    pdf.setStrokeColor(colors.HexColor("#d2d2d2"))
    pdf.setLineWidth(0.35)
    step = 5
    top = y + h
    for yy in range(int(y), int(top), step):
        y2 = min(yy + w, top)
        dx = y2 - yy
        pdf.line(x, yy, x + dx, y2)
        pdf.line(x + w, yy, x + w - dx, y2)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)


def _draw_question_footer(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int, is_last: bool = False) -> None:
    width, _ = A4
    page_label = str(page_number)
    pdf.setFont(FONT_BOLD, 10)
    if page_number % 2 == 1:
        pdf.drawRightString(width - 49.3, 34.4, page_label)
        block_x = 72
    else:
        pdf.drawString(49.3, 34.4, page_label)
        block_x = width - 98
    if not is_last:
        pdf.setFont(FONT_REGULAR, 9)
        pdf.drawRightString(width - 58, 22, "Turn over  >")
    paper_code = blueprint.paper_code.partition("/")[0]
    _draw_fake_barcode(pdf, width / 2 - 105, 26, f"{paper_code}{page_number:02d}")
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawString(block_x, 42, "■□■□")


def _draw_section_intro(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    section: str,
    y: float,
) -> float:
    width, _ = A4
    # Section titles need a full heading inset, not the writing-line origin.
    # Keep continuation-page writing space and bottom-safe geometry unchanged.
    y = min(y, ANSWER_FRAME_Y + ANSWER_FRAME_H - 42)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawCentredString(width / 2, y, f"SECTION {section}")
    y -= 25
    if blueprint.paper_id in {"paper_1", "paper_2"} and section == "A":
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        for index, line in enumerate(SECTION_A_INSTRUCTION_LINES):
            _draw_centred_instruction_line(pdf, width / 2, y, line)
            y -= 24 if index in {0, 3, 4} else BODY_LEADING_PT
        return y - 4
    is_section_b_prompt = blueprint.paper_id in {"paper_1", "paper_2"} and section == "B"
    pdf.setFont(FONT_BOLD if is_section_b_prompt else FONT_REGULAR, BODY_FONT_SIZE_PT)
    for index, line in enumerate(_section_instruction_lines(blueprint.paper_id, section)):
        pdf.drawCentredString(width / 2, y, line)
        y -= 22 if is_section_b_prompt and index in {1, 2} else BODY_LEADING_PT
    return y - (18 if is_section_b_prompt else 12)


def _draw_centred_instruction_line(pdf: canvas.Canvas, center_x: float, y: float, line: str) -> None:
    if CROSS_BOX_TOKEN not in line:
        pdf.drawCentredString(center_x, y, line)
        return

    parts = line.split(CROSS_BOX_TOKEN)
    font_name = FONT_BOLD
    font_size = BODY_FONT_SIZE_PT
    box_size = 8
    box_gap = 4
    total_width = sum(pdf.stringWidth(part, font_name, font_size) for part in parts)
    total_width += (len(parts) - 1) * (box_size + box_gap)
    x = center_x - total_width / 2
    for index, part in enumerate(parts):
        pdf.drawString(x, y, part)
        x += pdf.stringWidth(part, font_name, font_size)
        if index < len(parts) - 1:
            box_x = x + 1
            box_y = y + 1
            pdf.setLineWidth(1)
            pdf.rect(box_x, box_y, box_size, box_size, stroke=1, fill=0)
            pdf.line(box_x + 1.3, box_y + 1.3, box_x + box_size - 1.3, box_y + box_size - 1.3)
            pdf.line(box_x + box_size - 1.3, box_y + 1.3, box_x + 1.3, box_y + box_size - 1.3)
            x += box_size + box_gap


def _section_instruction_lines(paper_id: str, section: str) -> list[str]:
    if paper_id in {"paper_1", "paper_2"} and section == "B":
        return [
            "Read the following extracts (A to D) before answering Question 6.",
            "Write your answers in the spaces provided.",
            "You are advised to spend 1 hour on this section.",
        ]
    return _wrap(_section_instruction(paper_id, section), 70)


def _section_instruction(paper_id: str, section: str) -> str:
    if paper_id in {"paper_1", "paper_2"}:
        if section == "A":
            return (
                "Answer ALL questions. You are advised to spend 30 minutes on this section. "
                "Use the data to support your answers where relevant."
            )
        if section == "B":
            return "Read the source material before answering Question 6."
        return "Answer EITHER Question 7 OR Question 8."
    if section == "A":
        return "Answer ALL Questions 1(a) to 1(c), and EITHER Question 1(d) OR 1(e)."
    return "Answer ALL Questions 2(a) to 2(c), and EITHER Question 2(d) OR 2(e)."


def _draw_question(
    pdf: canvas.Canvas,
    question,
    x: float,
    y: float,
    fill_answer_page: bool = False,
) -> float:
    width, _ = A4
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    y = _draw_question_prompt(pdf, question.number, question.prompt, x, y)
    if question.parts:
        if question.stimulus_kind:
            y = _draw_stimulus(pdf, question.stimulus_kind, x + 105, y, graph_params=question.graph_params, source_instance=question.source_instance)
            y -= 18
        y -= 4
        for part in question.parts:
            part_lines = _wrap(f"({part.label}) {part.prompt}", 64)
            for line in part_lines:
                pdf.drawString(x + 14, y, line)
                y -= BODY_LEADING_PT
            pdf.drawRightString(width - x, y + 12, f"({part.marks})")
            y -= 6
            y = _draw_answer_lines(pdf, x + 14, y, width - x, _answer_line_count(part.marks))
            y -= 8
        return y - 6

    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + 12, f"({question.marks})")
    pdf.setFillColor(colors.black)
    y -= 6
    if fill_answer_page:
        y = _draw_answer_lines_until(pdf, x, y, width - x)
    else:
        y = _draw_answer_lines(pdf, x, y, width - x, _answer_line_count(question.marks))
    return y - 10


def _draw_question_prompt(pdf: canvas.Canvas, number: str, prompt: str, x: float, y: float) -> float:
    parsed = _split_subquestion_number(number)
    if not parsed:
        for line in _wrap(f"{number} {prompt}", 68):
            pdf.drawString(x, y, line)
            y -= BODY_LEADING_PT
        return y

    base, part = parsed
    lines = _wrap(prompt, 62)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, base)
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    pdf.drawString(x + 24, y, f"({part})")
    for index, line in enumerate(lines):
        pdf.drawString(x + 50, y - index * BODY_LEADING_PT, line)
    return y - max(1, len(lines)) * BODY_LEADING_PT


def _split_subquestion_number(number: str) -> tuple[str, str] | None:
    match = re.match(r"^(\d+)\(([a-z])\)$", number)
    if not match:
        return None
    return match.group(1), match.group(2)


def _draw_section_a_question(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    question,
    page_number: int,
    x: float,
    y: float,
) -> tuple[int, float]:
    width, _ = A4
    # Source-page stems need clearance from the rounded frame. Do not change
    # the starting point of blank answer pages or their available writing space.
    y = min(y, 787.0)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawString(x, y, question.number)
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    stem_lines = _wrap(question.prompt, 68)
    for index, line in enumerate(stem_lines):
        pdf.drawString(x + 20, y - index * BODY_LEADING_PT, line)
    y -= max(1, len(stem_lines)) * BODY_LEADING_PT + 12

    first_part = question.parts[0] if question.parts else None
    second_part = question.parts[1] if len(question.parts) > 1 else None
    stimulus_kind = question.stimulus_kind
    if first_part and first_part.command_word == "draw":
        stimulus_kind = "context_extract"
    if _should_draw_inline_context(stimulus_kind) and question.source_instance is None:
        y = _draw_inline_context(pdf, question.source_text, x + 20, y)
        y -= 10
    if stimulus_kind:
        y = _draw_stimulus(pdf, stimulus_kind, x + 110, y, question.source_text, graph_params=question.graph_params, source_instance=question.source_instance)
        y -= 28

    if first_part and first_part.command_word == "draw" and second_part and second_part.marks == 1:
        compact = blueprint.paper_id == "paper_1" and question.number == "3"
        y = _draw_draw_part_with_axes(
            pdf,
            first_part,
            x,
            y,
            max_axis_height=220 if compact else None,
        )
        if compact:
            y = _draw_mcq_part(pdf, second_part, x, y - 4)
            _draw_total_for_question(pdf, question.number, question.marks, x, y)
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            return page_number, _prepare_answer_page(pdf, blueprint, page_number)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)
        y = _draw_mcq_part(pdf, second_part, x, y)
        _draw_total_for_question(pdf, question.number, question.marks, x, y)
        if question.number == "5":
            _draw_section_a_total(pdf, x, y - 34)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        return page_number, _prepare_answer_page(pdf, blueprint, page_number)

    if first_part and first_part.command_word == "calculate" and second_part and second_part.marks == 1:
        y = _draw_calculate_part_with_working_lines(pdf, first_part, x, y)
        if y - _estimate_mcq_height(second_part) < SECTION_A_FOOTER_SAFE_Y:
            _draw_answer_lines_until(pdf, x, y + 12, width - x, bottom_y=SECTION_A_FOOTER_SAFE_Y)
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = _prepare_answer_page(pdf, blueprint, page_number)
        y = _draw_mcq_part(pdf, second_part, x, y)
        _draw_total_for_question(pdf, question.number, question.marks, x, y)
        if question.number == "5":
            _draw_section_a_total(pdf, x, y - 34)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        return page_number, _prepare_answer_page(pdf, blueprint, page_number)

    if (
        blueprint.paper_id == "paper_1"
        and question.number == "4"
        and first_part
        and first_part.command_word == "explain"
        and second_part
        and second_part.command_word == "mcq"
    ):
        y = _draw_written_part_with_line_count(pdf, first_part, x, y, count=11)
        # The estimate includes an extra 18pt reserve. Here the total is drawn
        # above the returned baseline, so use the actual MCQ content height.
        if y - (_estimate_mcq_height(second_part) - 18) < SECTION_A_FOOTER_SAFE_Y:
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = min(_prepare_answer_page(pdf, blueprint, page_number), 787.0)
        y = _draw_mcq_part(pdf, second_part, x, y - 2)
        _draw_total_for_question(pdf, question.number, question.marks, x, y)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        return page_number, _prepare_answer_page(pdf, blueprint, page_number)

    if len(question.parts) > 2:
        y = _draw_compact_part(pdf, question.parts[0], x, y)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)
        # The official three-part response page starts below the frame header and
        # uses the full writable height: 11 rules for working, then 9 for the
        # explanation. Preserve that measured rhythm even when the generated
        # calculation stem is one line shorter than the reference example.
        y -= 63
        for index, part in enumerate(question.parts[1:]):
            part_y = y - 4 if index == 0 else y + 6
            y = _draw_compact_part(
                pdf,
                part,
                x,
                part_y,
                bottom_y=100,
            )
        _draw_total_for_question(pdf, question.number, question.marks, x, y)
        if question.number == "5":
            _draw_section_a_total(pdf, x, y - 34)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        return page_number, _prepare_answer_page(pdf, blueprint, page_number)

    if first_part and first_part.marks == 1:
        y = _draw_mcq_part(pdf, first_part, x, y)
    elif first_part:
        y = _draw_written_part_with_lines(pdf, first_part, x, y, bottom_y=90)

    _draw_question_footer(pdf, blueprint, page_number)
    pdf.showPage()
    page_number += 1
    y = _prepare_answer_page(pdf, blueprint, page_number)

    if second_part and first_part and first_part.marks == 1:
        y = _draw_written_part_with_lines(pdf, second_part, x, y - 4, bottom_y=125)
        total_y = max(y + 26, 88)
    elif second_part and second_part.command_word == "mcq":
        y = _draw_mcq_part(pdf, second_part, x, y - 4)
        total_y = y
    else:
        y = _draw_answer_lines(pdf, x, y - 4, width - x, 8)
        y -= 22
        if second_part:
            y = _draw_mcq_part(pdf, second_part, x, y)
        total_y = y

    _draw_total_for_question(pdf, question.number, question.marks, x, total_y)
    if question.number == "5":
        _draw_section_a_total(pdf, x, total_y - 34)
    _draw_question_footer(pdf, blueprint, page_number)
    pdf.showPage()
    page_number += 1
    if question.number == "5":
        return page_number, _prepare_answer_page(pdf, blueprint, page_number)
    return page_number, _prepare_answer_page(pdf, blueprint, page_number)


def _should_draw_inline_context(stimulus_kind: str) -> bool:
    return stimulus_kind in {"cost_revenue_graph"}


def _draw_written_part_with_lines(pdf: canvas.Canvas, part, x: float, y: float, bottom_y: float) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 28
    return _draw_answer_lines_until(pdf, x, y, width - x, bottom_y=bottom_y)


def _draw_written_part_with_line_count(pdf: canvas.Canvas, part, x: float, y: float, count: int) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 24
    return _draw_answer_lines(pdf, x, y, width - x, count, bottom_y=SECTION_A_FOOTER_SAFE_Y) - 10


def _draw_draw_part_with_axes(
    pdf: canvas.Canvas,
    part,
    x: float,
    y: float,
    *,
    max_axis_height: float | None = None,
) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 18
    y_label, x_label = _axis_labels_for_draw_prompt(part.prompt)
    axis_width = min(BLANK_AXIS_WIDTH_PT, width - x - 78)
    target_height = min(BLANK_AXIS_HEIGHT_PT, max_axis_height or BLANK_AXIS_HEIGHT_PT)
    axis_height = min(target_height, max(180, y - (SECTION_A_FOOTER_SAFE_Y + 35)))
    return _draw_blank_answer_axes(pdf, x + 34, y, axis_width, axis_height, x_label=x_label, y_label=y_label) - 10


def _draw_calculate_part_with_working_lines(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 20
    y = _draw_answer_lines(pdf, x, y, width - x, 6, bottom_y=SECTION_A_FOOTER_SAFE_Y)
    return y - 12


def _draw_compact_part(
    pdf: canvas.Canvas,
    part,
    x: float,
    y: float,
    *,
    bottom_y: float = SECTION_A_FOOTER_SAFE_Y,
) -> float:
    width, _ = A4
    if part.command_word == "mcq":
        return _draw_mcq_part(pdf, part, x, y)
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 18
    lines = (
        11 if part.command_word == "calculate" else 9
    ) if part.marks <= 2 else 7
    return _draw_answer_lines(
        pdf,
        x,
        y,
        width - x,
        lines,
        bottom_y=bottom_y,
    ) - 12


def _axis_labels_for_draw_prompt(prompt: str) -> tuple[str, str]:
    text = prompt.lower()
    if "cost" in text and "revenue" in text:
        return "Costs/revenues", "Output"
    if "aggregate demand" in text or "aggregate supply" in text:
        return "Price level", "Real output"
    if "labour" in text or "wage" in text:
        return "Wage rate", "Quantity of labour"
    if "ppc" in text or "production possibility" in text:
        return "Good Y", "Good X"
    return "Price", "Quantity"


def _draw_blank_answer_axes(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    x_label: str = "Quantity",
    y_label: str = "Price",
) -> float:
    bottom = y - h
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.7)
    _draw_axis_arrow(pdf, x, bottom, x, y)
    _draw_axis_arrow(pdf, x, bottom, x + w, bottom)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawString(x - 5, y + 8, y_label)
    pdf.drawRightString(x + w, bottom - 14, x_label)
    pdf.setLineWidth(1)
    return bottom


def _draw_part_prompt(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    lines = _wrap(f"({part.label}) {_part_prompt_text(part)}", 66)
    for line in lines:
        pdf.drawString(x + 18, y, line)
        y -= BODY_LEADING_PT
    return y


def _draw_inline_context(pdf: canvas.Canvas, text: str, x: float, y: float) -> float:
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    for line in _wrap(text, 66):
        pdf.drawString(x, y, line)
        y -= BODY_LEADING_PT
    return y


def _draw_mcq_part(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    width, _ = A4
    question_text, choices = _mcq_choices(part)
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    lines = _wrap(f"({part.label}) {question_text}", 66)
    for line in lines:
        pdf.drawString(x + 18, y, line)
        y -= BODY_LEADING_PT
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 24
    for letter, text in choices:
        pdf.rect(x + 38, y - 3, 8, 8, stroke=1, fill=0)
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        pdf.drawString(x + 66, y - 1, letter)
        pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
        option_lines = _wrap(text, 58)
        for index, line in enumerate(option_lines):
            pdf.drawString(x + 88, y - 1 - index * BODY_LEADING_PT, line)
        y -= max(1, len(option_lines)) * BODY_LEADING_PT + 10
    return y - 4


def _estimate_mcq_height(part) -> float:
    question_text, choices = _mcq_choices(part)
    height = len(_wrap(f"({part.label}) {question_text}", 66)) * BODY_LEADING_PT
    height += 24
    for _, text in choices:
        height += max(1, len(_wrap(text, 58))) * BODY_LEADING_PT + 10
    return height + 22


def _mcq_choices(part) -> tuple[str, list[tuple[str, str]]]:
    if part.options:
        return _part_prompt_text(part), [(option.label, option.text) for option in part.options]
    return _split_mcq_prompt(_part_prompt_text(part))


def _part_prompt_text(part) -> str:
    cleaned = part.prompt.strip()
    label = re.escape(part.label)
    for _ in range(3):
        updated = re.sub(rf"^(?:question\s+\d+\s*)?\(\s*{label}\s*\)\s*", "", cleaned, count=1, flags=re.IGNORECASE)
        updated = re.sub(rf"^{label}\)\s*", "", updated, count=1, flags=re.IGNORECASE)
        updated = re.sub(rf"^{label}\.\s*", "", updated, count=1, flags=re.IGNORECASE).strip()
        if updated == cleaned:
            break
        cleaned = updated
    return cleaned


def _split_mcq_prompt(prompt: str) -> tuple[str, list[tuple[str, str]]]:
    if "? " in prompt:
        question_text, option_text = prompt.split("? ", 1)
        question_text += "?"
    else:
        question_text, option_text = prompt, ""
    choices = re.findall(r"\b([A-D])\s+([^;]+)", option_text)
    if len(choices) != 4:
        choices = [("A", "Statement one"), ("B", "Statement two"), ("C", "Statement three"), ("D", "Statement four")]
    return question_text, [(letter, text.strip().rstrip(".")) for letter, text in choices]


def _draw_total_for_question(pdf: canvas.Canvas, number: str, marks: int, x: float, y: float) -> None:
    width, _ = A4
    pdf.setStrokeColor(colors.HexColor("#9d9d9d"))
    pdf.line(x, y + 6, width - x, y + 6)
    pdf.setStrokeColor(colors.black)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawRightString(width - x, y + 12, f"(Total for Question {number} = {marks} marks)")


def _draw_section_a_total(pdf: canvas.Canvas, x: float, y: float) -> None:
    width, _ = A4
    pdf.setStrokeColor(colors.HexColor("#9d9d9d"))
    pdf.setLineWidth(2)
    pdf.line(x, y, width - x, y)
    pdf.setLineWidth(1)
    pdf.setStrokeColor(colors.black)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawRightString(width - x, y - 18, "TOTAL FOR SECTION A = 25 MARKS")


def _draw_answer_lines(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    right_x: float,
    line_count: int,
    bottom_y: float = 90,
) -> float:
    available = max(0, int((y - bottom_y) // ANSWER_LINE_GAP_PT) + 1)
    return draw_glyph_answer_rules(
        pdf,
        first_y=y,
        count=min(line_count, available),
        style=EDEXCEL_ANSWER_RULES,
    )


def _draw_answer_lines_until(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    right_x: float,
    bottom_y: float = 70,
) -> float:
    line_count = max(0, int((y - bottom_y) // ANSWER_LINE_GAP_PT) + 1)
    return draw_glyph_answer_rules(
        pdf,
        first_y=y,
        count=line_count,
        style=EDEXCEL_ANSWER_RULES,
    )


def _answer_line_count(marks: int) -> int:
    if marks <= 5:
        return 10
    if marks <= 8:
        return 18
    if marks <= 12:
        return 25
    if marks <= 15:
        return 31
    return 38


_GRAPH_IMG_CACHE: list[str] = []


def _cleanup_graph_cache() -> None:
    for path in _GRAPH_IMG_CACHE:
        with suppress(OSError):
            os.unlink(path)
    _GRAPH_IMG_CACHE.clear()


_GRAPH_FUNCS: dict[str, object] = {
    "cost_revenue_graph": mr_mc_ac_diagram,
    "market_diagram": demand_supply_diagram,
    "demand_shift_graph": demand_supply_diagram,
    "supply_shift_graph": demand_supply_diagram,
    "ad_as_diagram": ad_as_diagram,
    "keynesian_as_diagram": keynesian_ad_as_diagram,
    "macro_chart": ad_as_diagram,
    "phillips_curve": phillips_curve,
    "lorenz_curve": lorenz_curve,
    "laffer_curve": laffer_curve,
    "labour_market_diagram": labour_market_diagram,
    "monopsony_diagram": labour_market_diagram,
    "externality_diagram": externality_diagram,
    "minimum_price_diagram": lambda params=None: tax_subsidy_diagram(kind="tax", tax_amount=10, params=params),
    "maximum_price_diagram": lambda params=None: tax_subsidy_diagram(kind="subsidy", tax_amount=10, params=params),
    "tax_subsidy_diagram": lambda params=None: tax_subsidy_diagram(kind="tax", tax_amount=15, params=params),
    "tariff_diagram": lambda params=None: tax_subsidy_diagram(kind="tax", tax_amount=12, params=params),
    "consumer_surplus_diagram": consumer_producer_surplus,
    "producer_surplus_diagram": consumer_producer_surplus,
    "production_possibility_frontier": ppf_diagram,
    "perfect_competition_diagram": perfect_competition_diagram,
    "monopoly_diagram": monopoly_diagram,
    "trade_cycle": trade_cycle_diagram,
    "multiplier_context": trade_cycle_diagram,
    "money_market_diagram": demand_supply_diagram,
    "poverty_trap_diagram": laffer_curve,
    "exchange_rate_diagram": demand_supply_diagram,
}


def candidate_stimulus_data(question: QuestionBlueprint) -> dict[str, object]:
    """Expose the same source values and dispatch rules used to draw a figure."""
    if question.source_instance:
        source = question.source_instance
        if question.parts and question.parts[0].command_word == "draw":
            return {"kind": "context_extract", "source_text": source.context,
                "source_id": source.source_id, "source_fingerprint": source.fingerprint(),
                "provenance": source.provenance, "rows": [], "values": [],
                "point_labels": [], "candidate_draws_diagram": True}
        return {"kind": source.kind, "source_text": source.context,
            "source_id": source.source_id, "source_fingerprint": source.fingerprint(),
            "provenance": source.provenance,
            "rows": [[cell.printed() for cell in row] for row in source.rows],
            "values": [float(v) for v in source.values], "point_labels": source.labels,
            "y_label": source.y_label, "x_label": source.x_label,
            "unit": source.unit, "givens": {name: cell.printed() for name, cell in source.givens.items()},
            "graph_params": question.graph_params.to_dict() if question.graph_params.kind else {}}
    kind = question.stimulus_kind
    data: dict[str, object] = {"kind": kind, "source_text": question.source_text}
    if kind in _TABLE_KINDS:
        data["rows"] = _table_rows(kind)
    elif kind in _BAR_CHART_KINDS or kind in _LINE_CHART_KINDS:
        y_label, x_label, values = (
            _bar_chart_data(kind) if kind in _BAR_CHART_KINDS else line_chart_data(kind)
        )
        data.update({"y_label": y_label, "x_label": x_label, "values": values})
        data["point_labels"] = (
            [_bar_label(kind, index) for index in range(len(values))]
            if kind in _BAR_CHART_KINDS else
            [f"{x_label} {index}" for index in range(1, len(values) + 1)]
        )
    elif kind == "payoff_matrix":
        data.update({"row_player": "Firm A", "column_player": "Firm B",
                     "strategies": ["High price", "Low price"],
                     "payoffs_A_B": [[[8, 8], [4, 10]], [[10, 4], [6, 6]]]})
    elif kind in _ECONOMICS_GRAPH_KINDS:
        data["graph_params"] = question.graph_params.to_dict() if question.graph_params.kind else {}
        data["diagram_kind"] = kind
    return data


def _draw_stimulus(pdf: canvas.Canvas, kind: str, x: float, y: float, context_text: str = "", graph_params: GraphParams | None = None, source_instance: EconomicsSource | None = None) -> float:
    if source_instance and kind == source_instance.kind:
        if source_instance.rows or source_instance.values:
            pdf.setFont(FONT_REGULAR, 8)
            pdf.drawString(104, y, "Illustrative data for this question; not official statistics.")
            y -= 15
            if source_instance.context:
                y = _draw_inline_context(pdf, source_instance.context, 104, y) - 10
            for name, cell in source_instance.givens.items():
                y = _draw_inline_context(pdf, f"{name.replace('_', ' ').capitalize()}: {cell.printed()}.", 104, y) - 6
            if source_instance.rows:
                return _draw_data_table(pdf, 104, y, kind, rows=[[cell.printed() for cell in row] for row in source_instance.rows])
            return _draw_instance_chart(pdf, 104, y, source_instance)
        if kind in _ECONOMICS_GRAPH_KINDS and source_instance.context:
            y = _draw_inline_context(pdf, source_instance.context, 104, y) - 10
    if kind in _ECONOMICS_GRAPH_KINDS:
        return _draw_economics_graph(pdf, 140, y + 18, kind, graph_params=graph_params)
    if kind in _TABLE_KINDS:
        return _draw_data_table(pdf, 104, y, kind)
    if kind in _BAR_CHART_KINDS:
        return _draw_bar_chart(pdf, 104, y + 24, kind)
    if kind in _LINE_CHART_KINDS:
        return _draw_line_graph(pdf, 104, y + 24, kind)
    if kind == "payoff_matrix":
        return _draw_payoff_matrix(pdf, 118, y)
    return _draw_context_box(pdf, 82, y, context_text)


_ECONOMICS_GRAPH_KINDS = {
    "cost_revenue_graph",
    "market_diagram",
    "macro_chart",
    "multiplier_context",
    "trade_cycle",
    "demand_shift_graph",
    "supply_shift_graph",
    "tax_subsidy_diagram",
    "externality_diagram",
    "consumer_surplus_diagram",
    "producer_surplus_diagram",
    "minimum_price_diagram",
    "maximum_price_diagram",
    "production_possibility_frontier",
    "perfect_competition_diagram",
    "monopoly_diagram",
    "monopsony_diagram",
    "labour_market_diagram",
    "ad_as_diagram",
    "keynesian_as_diagram",
    "phillips_curve",
    "lorenz_curve",
    "exchange_rate_diagram",
    "tariff_diagram",
    "money_market_diagram",
    "laffer_curve",
    "poverty_trap_diagram",
}

_TABLE_KINDS = {
    "data_table",
    "ped_data_table",
    "pes_data_table",
    "development_data_table",
    "elasticity_data_table",
    "concentration_ratio_table",
    "marginal_utility_table",
    "opportunity_cost_ppc_table",
    "shutdown_cost_table",
    "wage_rate_table",
    "contestability_barrier_table",
    "balance_payments_table",
    "inflation_index_table",
    "income_tax_schedule_table",
    "public_spending_pie_table",
}

_BAR_CHART_KINDS = {
    "bar_chart",
    "market_share_bar_chart",
    "gdp_growth_bar_chart",
    "unemployment_rate_bar_chart",
}

_LINE_CHART_KINDS = {
    "line_graph",
    "index_number_chart",
    "household_savings_line_chart",
    "investment_line_chart",
    "current_account_line_chart",
    "inequality_line_chart",
    "terms_of_trade_index_chart",
    "exchange_rate_index_chart",
}


def _draw_axis_arrow(pdf: canvas.Canvas, x1: float, y1: float, x2: float, y2: float) -> None:
    pdf.line(x1, y1, x2, y2)
    if abs(x1 - x2) < 0.1:
        pdf.line(x2, y2, x2 - 3, y2 - 7)
        pdf.line(x2, y2, x2 + 3, y2 - 7)
        return
    pdf.line(x2, y2, x2 - 7, y2 + 3)
    pdf.line(x2, y2, x2 - 7, y2 - 3)


def _draw_economics_graph(pdf: canvas.Canvas, x: float, y: float, kind: str, graph_params: GraphParams | None = None) -> float:
    fn = _GRAPH_FUNCS.get(kind)
    if fn is None:
        pdf.setFont("Times-Italic", 10)
        pdf.drawString(x, y - 14, f"[{kind.replace('_', ' ')}]")
        return y - 30
    params = graph_params.to_dict() if graph_params and graph_params.kind else None
    img_path = fn(params=params) if params else fn()
    _GRAPH_IMG_CACHE.append(img_path)
    graph_w = 360
    graph_h = 190
    pdf.drawImage(img_path, x, y - graph_h, width=graph_w, height=graph_h, preserveAspectRatio=True)
    return y - graph_h - 8


def _draw_data_table(pdf: canvas.Canvas, x: float, y: float, kind: str = "data_table", rows: list[list[str]] | None = None) -> float:
    rows = rows if rows is not None else _table_rows(kind)
    col_count = max(len(row) for row in rows)
    col_width = 124 if kind == "data_table" else 92 if col_count >= 4 else 100
    w = col_width * col_count
    row_h = 21
    h = row_h * len(rows) + 2
    pdf.setFillColor(colors.HexColor("#f2f2f2"))
    pdf.rect(x, y - row_h, w, row_h, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    pdf.setFont(FONT_REGULAR, 8.5 if kind == "data_table" else 9 if col_count >= 4 else 11)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            pdf.drawString(x + c * col_width + 6, y - 14 - r * row_h, text)
    pdf.rect(x, y - h, w, h, stroke=1, fill=0)
    for i in range(1, len(rows)):
        pdf.line(x, y - i * row_h, x + w, y - i * row_h)
    for i in range(1, col_count):
        pdf.line(x + i * col_width, y, x + i * col_width, y - h)
    return y - h - 8


def _table_rows(kind: str) -> list[list[str]]:
    return table_rows(kind)


def _draw_instance_chart(pdf: canvas.Canvas, x: float, y: float, source: EconomicsSource) -> float:
    """Actual numeric ordinate mapping, with exact data readings and time labels."""
    values = [float(value) for value in source.values]
    width, height = 408, 126
    bottom = y - height - 20
    low, high = min(values), max(values)
    if source.unit != "index" and source.kind != "inequality_line_chart":
        low, high = min(0.0, low), max(0.0, high)
    raw_step = (high - low or 1.0) / 5
    magnitude = 10 ** math.floor(math.log10(raw_step))
    tick_step = next(multiplier * magnitude for multiplier in (1, 2, 5, 10) if multiplier * magnitude >= raw_step)
    low, high = math.floor(low / tick_step) * tick_step, math.ceil(high / tick_step) * tick_step
    span = high - low or tick_step
    def ordinate(value):
        return bottom + (value - low) / span * height
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawString(x, y + 3, source.y_label)
    pdf.line(x, bottom, x, bottom + height)
    for index in range(round(span / tick_step) + 1):
        tick = low + tick_step * index
        ty = ordinate(tick)
        pdf.setStrokeColor(colors.HexColor("#d2d2d2"))
        pdf.line(x, ty, x + width, ty)
        pdf.setFillColor(colors.black)
        pdf.drawRightString(x - 5, ty - 3, f"{tick:.2f}".rstrip("0").rstrip("."))
    pdf.setStrokeColor(colors.black)
    pdf.line(x, ordinate(0) if low <= 0 <= high else bottom, x + width, ordinate(0) if low <= 0 <= high else bottom)
    step = (width - 32) / max(1, len(values) - 1)
    points = [(x + 16 + i * step, ordinate(value)) for i, value in enumerate(values)]
    if "bar_chart" in source.kind:
        for (px, py) in points:
            pdf.rect(px - 9, min(py, ordinate(0)), 18, abs(py - ordinate(0)), stroke=1, fill=0)
    else:
        for first, second in pairwise(points):
            pdf.line(*first, *second)
    pdf.setFont(FONT_REGULAR, 7)
    for i, (px, py) in enumerate(points):
        pdf.circle(px, py, 1.5, stroke=1, fill=1)
        pdf.drawCentredString(px, py + 5, format(source.values[i], "f"))
        label = source.labels[i]
        # Full identifiers remain visible, split across two lines if necessary.
        pieces = label.rsplit(" ", 1)
        pdf.drawCentredString(px, bottom - 12, pieces[0])
        if len(pieces) == 2:
            pdf.drawCentredString(px, bottom - 21, pieces[1])
    return bottom - 28


def _draw_bar_chart(pdf: canvas.Canvas, x: float, y: float, kind: str = "bar_chart") -> float:
    chart_width = 428
    chart_height = 155
    bottom = y - 190
    max_scale = 30 if kind == "market_share_bar_chart" else max(_bar_chart_data(kind)[2])
    if kind == "market_share_bar_chart":
        pdf.setStrokeColor(colors.HexColor("#d2d2d2"))
        pdf.setLineWidth(0.35)
        for tick in range(5, 31, 5):
            tick_y = bottom + chart_height * tick / max_scale
            pdf.line(x, tick_y, x + chart_width, tick_y)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(1)
    _draw_axis_arrow(pdf, x, bottom, x, y - 10)
    _draw_axis_arrow(pdf, x, bottom, x + chart_width, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label, x_label, values = _bar_chart_data(kind)
    pdf.drawString(x - 28, y - 18, y_label)
    pdf.drawRightString(x + chart_width + 5, bottom - 12, x_label)
    for i, value in enumerate(values):
        h = chart_height * value / max_scale
        spacing = chart_width / (len(values) + 1)
        pdf.setFillColor(colors.HexColor("#bdbdbd") if kind == "market_share_bar_chart" else colors.white)
        bar_x = x + spacing * (i + 1) - 14
        pdf.rect(bar_x, bottom, 28, h, stroke=1, fill=kind == "market_share_bar_chart")
        pdf.setFillColor(colors.black)
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawCentredString(bar_x + 14, bottom - 11, _bar_label(kind, i))
        if kind == "market_share_bar_chart":
            pdf.drawCentredString(bar_x + 14, bottom + h + 4, f"{value:.1f}%")
    return bottom - 10


def _bar_chart_data(kind: str) -> tuple[str, str, list[float]]:
    if kind == "market_share_bar_chart":
        return "%", "Firms", [26.6, 19.5, 12.7, 11.7, 10.9]
    if kind == "gdp_growth_bar_chart":
        return "%", "Quarter", [0.4, 0.1, -0.1, 0.1, 0.1]
    if kind == "unemployment_rate_bar_chart":
        return "%", "Economy", [3.9, 5.8, 7.1, 4.6]
    return "%", "Firms", [52, 80, 38, 96]


def _bar_label(kind: str, index: int) -> str:
    if kind == "market_share_bar_chart":
        return ["Lloyds", "NatWest", "Barclays", "HSBC", "Santander"][index]
    if kind == "unemployment_rate_bar_chart":
        return ["UK", "FR", "ES", "US"][index]
    return chr(65 + index)


def _draw_line_graph(pdf: canvas.Canvas, x: float, y: float, kind: str = "line_graph") -> float:
    chart_width = 428
    chart_height = 155
    bottom = y - 190
    _draw_axis_arrow(pdf, x, bottom, x, y - 10)
    _draw_axis_arrow(pdf, x, bottom, x + chart_width, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label, x_label, values = _line_chart_data(kind)
    pdf.drawString(x - 28, y - 18, y_label)
    pdf.drawRightString(x + chart_width + 5, bottom - 12, x_label)
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1
    step = (chart_width - 48) / max(1, len(values) - 1)
    points = [
        (x + 24 + i * step, bottom + 18 + (value - minimum) * (chart_height - 36) / span)
        for i, value in enumerate(values)
    ]
    for start, end in pairwise(points):
        pdf.line(*start, *end)
    for px, py in points:
        pdf.circle(px, py, 2.2, stroke=1, fill=1)
    return bottom - 10


def _line_chart_data(kind: str) -> tuple[str, str, list[float]]:
    return line_chart_data(kind)


def _draw_payoff_matrix(pdf: canvas.Canvas, x: float, y: float) -> float:
    w = 260
    h = 130
    pdf.rect(x, y - h, w, h, stroke=1, fill=0)
    pdf.line(x + 86, y, x + 86, y - h)
    pdf.line(x + 173, y, x + 173, y - h)
    pdf.line(x, y - 26, x + w, y - 26)
    pdf.line(x, y - 52, x + w, y - 52)
    pdf.line(x, y - 91, x + w, y - 91)
    pdf.setFont(FONT_REGULAR, 10)
    entries = [
        ("Firm B", x + 150, y - 18),
        ("Firm A", x + 24, y - 44),
        ("High price", x + 101, y - 44),
        ("Low price", x + 190, y - 44),
        ("High price", x + 10, y - 76),
        ("8, 8", x + 116, y - 76),
        ("4, 10", x + 202, y - 76),
        ("Low price", x + 10, y - 115),
        ("10, 4", x + 113, y - 115),
        ("6, 6", x + 202, y - 115),
    ]
    for text, tx, ty in entries:
        pdf.drawString(tx, ty, text)
    return y - h - 12


def _draw_context_box(pdf: canvas.Canvas, x: float, y: float, context_text: str = "") -> float:
    pdf.setFont(FONT_REGULAR, 11)
    text = context_text or "A short item of economic context is provided for use with this question."
    lines = _wrap(text, 74)
    for idx, line in enumerate(lines):
        pdf.drawCentredString(x + 170, y - idx * 12, line)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawCentredString(x + 170, y - len(lines) * 12 - 4, GENERIC_SOURCE_ATTRIBUTION)
    return y - len(lines) * 12 - 20


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def render_source_booklet(
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    _set_pdf_metadata(pdf, blueprint, "Source booklet")
    _draw_source_cover(pdf, blueprint)
    pdf.showPage()
    first_content_page = True
    for section in _source_sections(blueprint.paper_id):
        section_questions = [question for question in blueprint.questions if question.section == section]
        extracts = _extract_source_questions(section_questions)
        for start in range(0, len(extracts), 2):
            if not first_content_page:
                pdf.showPage()
            first_content_page = False
            _draw_source_content_page(
                pdf,
                blueprint,
                syllabus,
                section,
                section_questions,
                extracts[start : start + 2],
                start_label=start,
                include_title=start == 0,
            )

    _pad_pdf_pages(pdf, 4 if blueprint.paper_id in {"paper_1", "paper_2"} else 8)
    pdf.save()


def _pad_pdf_pages(pdf: canvas.Canvas, target_pages: int) -> None:
    while pdf.getPageNumber() < target_pages:
        pdf.showPage()
        _draw_crop_marks(pdf)


def _extract_source_questions(section_questions: list) -> list:
    if len(section_questions) >= 5:
        return [section_questions[0], section_questions[1], section_questions[3], section_questions[4]]
    return section_questions[:4]


def _draw_source_content_page(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    section: str,
    section_questions: list,
    questions: list,
    start_label: int = 0,
    include_title: bool = True,
) -> None:
    width, height = A4
    margin = 58
    _draw_crop_marks(pdf)
    y = height - 58
    if include_title:
        pdf.setFont(FONT_REGULAR, 9)
        pdf.drawCentredString(width / 2, y, "Do not return this Booklet with the question paper.")
        y -= 46
        pdf.setFont(FONT_BOLD, 11)
        pdf.drawCentredString(width / 2, y, f"Sources for use with SECTION {section}")
        y -= 18
        pdf.setFont(FONT_REGULAR, 9)
        prompt = _source_reading_prompt(blueprint.paper_id, section)
        for line in _wrap(prompt, 92):
            pdf.drawCentredString(width / 2, y, line)
            y -= 12
        y -= 16
        first_question = section_questions[0].number.split("(")[0]
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(margin, y, f"Question {first_question}")
        y -= 16
        pdf.drawString(margin, y, _source_title(section_questions, syllabus))
        y -= 24

    for extract_index, question in enumerate(questions, start=start_label):
        pdf.setFont(FONT_BOLD, 9)
        pdf.drawString(margin, y, f"Extract {chr(65 + extract_index)}")
        y -= 14
        pdf.setFont(FONT_REGULAR, 9)
        source_text = question.source_text or (
            "This source concerns the economic context in Question 6. It may include "
            "evidence for analysis and evaluation."
        )
        for line_index, line in enumerate(_wrap(source_text, 88), start=1):
            if y < 70:
                pdf.showPage()
                _draw_crop_marks(pdf)
                y = height - 58
            pdf.drawString(margin, y, line)
            if line_index % 5 == 0:
                pdf.setFont(FONT_REGULAR, 7.5)
                pdf.drawRightString(width - 88, y + 1, str(line_index))
                pdf.setFont(FONT_REGULAR, 9)
            y -= 12
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawString(margin, y, GENERIC_SOURCE_ATTRIBUTION)
        y -= 24


def _draw_source_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    width, _height = A4
    _draw_crop_marks(pdf)
    panel_x = 96
    panel_y = 523
    panel_w = 440
    panel_h = 260
    grey = colors.HexColor("#666666")
    dark = colors.HexColor("#4d494b")
    pdf.setStrokeColor(grey)
    pdf.setLineWidth(1.8)
    pdf.roundRect(panel_x, panel_y, panel_w, panel_h, 9, stroke=1, fill=0)
    y = panel_y + panel_h - 34
    pdf.setFont(FONT_BOLD, 17)
    pdf.drawString(panel_x + 14, y, "Unofficial Level 3 GCE Practice")
    y -= 51
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 28, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(panel_x + 22, y + 8, _exam_date_line(blueprint.paper_id))
    y -= 36
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 14, y + 11, f"{_exam_session(blueprint.paper_id)} (Time: {blueprint.duration_minutes // 60} hours)")
    pdf.rect(panel_x + 216, y, 58, 30, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 221, y + 18, "Paper")
    pdf.drawString(panel_x + 221, y + 7, "reference")
    pdf.setFillColor(dark)
    pdf.roundRect(panel_x + 274, y, 125, 30, 7, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 23)
    pdf.drawCentredString(panel_x + 337, y + 8, blueprint.paper_code)
    pdf.setFillColor(colors.black)
    y -= 90
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 88, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(panel_x + 22, y + 63, "Economics A")
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(panel_x + 22, y + 43, "Advanced")
    pdf.drawString(panel_x + 22, y + 26, f"PAPER {blueprint.paper_id[-1]}: {blueprint.title}")
    square_y = y + 73
    for offset, shade in enumerate(("#b0b0b0", "#777777", "#4d494b")):
        pdf.setFillColor(colors.HexColor(shade))
        pdf.rect(panel_x + panel_w - 52 + offset * 14, square_y, 12, 12, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    y -= 45
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 40, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(panel_x + 22, y + 24, "Source Booklet")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 9, "Do not return this Booklet with the question paper.")
    _draw_turn_over(pdf, width - 64, 75)
    paper_code = blueprint.paper_code.partition("/")[0]
    barcode_text = f"{paper_code}SB"
    pdf.setFont(FONT_REGULAR, 15)
    pdf.drawString(58, 43, barcode_text)
    pdf.setFont(FONT_REGULAR, 5.5)
    pdf.drawString(58, 31, f"Unofficial practice material, {economics_exam_schedule(blueprint.paper_id).date.year}.")
    _draw_fake_barcode(pdf, width / 2 - 80, 32, barcode_text)


def _source_sections(paper_id: str) -> list[str]:
    if paper_id in {"paper_1", "paper_2"}:
        return ["B"]
    return ["A", "B"]


def _source_reading_prompt(paper_id: str, section: str) -> str:
    if paper_id in {"paper_1", "paper_2"}:
        return "Read the following extracts (A to D) before answering Question 6."
    question_number = "1" if section == "A" else "2"
    return f"Read the following figures and extracts before answering Question {question_number}."


def _source_title(questions: list, syllabus: Syllabus) -> str:
    if not questions:
        return "Economic context"
    return syllabus.get_topic(questions[0].topic_id).title


def render_mark_scheme(
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_size = MS_PAGE_SIZES[blueprint.paper_id]
    pdf = canvas.Canvas(str(output_path), pagesize=page_size, pageCompression=0)
    _set_pdf_metadata(pdf, blueprint, "Mark scheme")
    width, height = page_size
    cover_layout = MARK_SCHEME_COVER_LAYOUTS[blueprint.paper_id]
    cover_margin = cover_layout["margin"]
    accent = colors.HexColor(MARK_SCHEME_ACCENT_COLOR)
    title_blue = colors.HexColor(MARK_SCHEME_TITLE_COLOR)
    pdf.setFillColor(colors.black)
    pdf.setFont(SERIF_FONT, 30)
    pdf.drawString(cover_margin, height - 200, "Unofficial Practice")
    pdf.setFillColor(title_blue)
    pdf.setFont(SERIF_FONT, 28)
    pdf.drawString(
        cover_margin,
        height - cover_layout["title_offset"],
        "Mark Scheme (Results)",
    )
    pdf.drawString(
        cover_margin,
        height - cover_layout["date_offset"],
        formatted_generation_date(),
    )
    pdf.setFont(MS_FONT, 22)
    pdf.setFillColor(accent)
    information_offsets = cover_layout["information_offsets"]
    pdf.drawString(
        cover_margin,
        height - information_offsets[0],
        "Unofficial GCE A Level Practice",
    )
    pdf.drawString(
        cover_margin,
        height - information_offsets[1],
        f"In Economics A ({blueprint.paper_code.split('/')[0]})",
    )
    paper_title = f"Paper {blueprint.paper_id[-1].zfill(2)} {blueprint.title}"
    title_size = 22.0
    title_width = pdf.stringWidth(paper_title, MS_FONT, title_size)
    available_width = width - cover_margin * 2
    if title_width > available_width:
        title_size *= available_width / title_width
        pdf.setFont(MS_FONT, title_size)
    pdf.drawString(cover_margin, height - information_offsets[2], paper_title)
    pdf.setFillColor(colors.black)
    pdf.showPage()

    _draw_mark_scheme_qualification_page(pdf, blueprint, 57, height)
    pdf.showPage()

    # This follows the left text column in the published reference material,
    # while keeping the content and identity unmistakably independent.
    guidance_margin = 84
    pdf.setFont(MS_FONT_BOLD, 14)
    pdf.drawString(guidance_margin, height - 155, "General Marking Guidance")
    pdf.setFont(MS_FONT, 11)
    y = height - 200
    guidance = [
        "All candidates must receive the same treatment: apply the same interpretation of each criterion to every response.",
        "Mark only against the published criteria, not an assumed grade boundary or a comparison with other candidates.",
        "Apply the question-specific criteria positively. Award full credit when the response meets the criterion; do not withhold a mark merely because the answer is concise.",
        "Use a best-fit judgement for levels-based responses, considering the quality of the response as a whole rather than adding isolated statements mechanically.",
        "Credit valid alternative wording where it communicates the required economic idea. Accept a clearly labelled diagram, calculation or chain of reasoning when it meets the criterion.",
        "Do not award the same analytical link more than once, even when it is repeated. Keep knowledge, application, analysis and evaluation distinct where the mark scheme requires them.",
        "Crossed out work should be marked unless the candidate has clearly replaced it with an alternative response.",
        "Give no credit for an assertion that is inaccurate, irrelevant or unsupported by the response. Credit a different but equally valid context consistently.",
        "Where the application of a criterion is genuinely unclear, retain the evidence in the response and seek a consistent interpretation before finalising the mark.",
    ]
    for item in guidance:
        for idx, line in enumerate(_wrap(item, 62)):
            pdf.drawString(
                guidance_margin + (0 if idx else 12),
                y,
                ("• " if idx == 0 else "  ") + line,
            )
            y -= 15
    pdf.showPage()

    y = height - MS_CONTENT_TOP
    for row in _mark_scheme_rows(blueprint, syllabus):
        if row.get("blank_page_before"):
            pdf.showPage()
            _draw_ms_blank_page(pdf, str(row["blank_page_before"]))
            pdf.showPage()
            y = height - MS_CONTENT_TOP
        elif row.get("force_page_break") and y < height - MS_CONTENT_TOP:
            pdf.showPage()
            y = height - MS_CONTENT_TOP
        row_height = _ms_row_height(row["answer_lines"])
        if y - row_height < MS_CONTENT_BOTTOM:
            pdf.showPage()
            y = height - MS_CONTENT_TOP
        y = _draw_ms_row(pdf, y, row["number"], row["answer_lines"], row["mark"])
        y -= 24
    if blueprint.paper_id == "paper_3":
        pdf.showPage()
        _draw_mark_scheme_end_page(pdf)
    if not any(question.source_instance is not None for question in blueprint.questions):
        _pad_mark_scheme_pages(pdf, MARK_SCHEME_MIN_PAGES.get(blueprint.paper_id, 29))
    pdf.save()
    _cleanup_graph_cache()


def _set_pdf_metadata(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    document_role: str,
) -> None:
    """Attach stable, searchable metadata to every released PDF role."""
    pdf.setTitle(f"{blueprint.title} — {document_role}")
    pdf.setAuthor("Paper Creator")
    pdf.setSubject(
        f"Unofficial Edexcel A Level Economics A practice {document_role.casefold()}"
    )
    pdf.setCreator("Paper Creator")


def _pad_mark_scheme_pages(pdf: canvas.Canvas, target_pages: int) -> None:
    while pdf.getPageNumber() <= target_pages:
        pdf.setFillColor(colors.white)
        pdf.circle(0, 0, 0.1, stroke=0, fill=1)
        pdf.showPage()


def _draw_mark_scheme_end_page(pdf: canvas.Canvas) -> None:
    pdf.setFont(MS_FONT, 8)
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.drawString(49, 44, "Paper Creator. Independent practice material.")
    pdf.drawString(49, 31, "Not produced, endorsed or approved by any examination board.")
    pdf.setFillColor(colors.black)


def _draw_ms_blank_page(pdf: canvas.Canvas, kind: str) -> None:
    _width, height = MS_PAGE_SIZE
    if kind == "header":
        _draw_ms_table_header(pdf, height - 67)
        return

    top = height - 39
    bottom = height - 762
    pdf.setStrokeColor(colors.HexColor("#8c8c8c"))
    pdf.setLineWidth(0.48)
    pdf.rect(MS_LEFT, bottom, MS_RIGHT - MS_LEFT, top - bottom, stroke=1, fill=0)
    pdf.line(MS_LEFT + MS_NUMBER_W, bottom, MS_LEFT + MS_NUMBER_W, top)
    pdf.line(MS_RIGHT - MS_MARK_W, bottom, MS_RIGHT - MS_MARK_W, top)
    pdf.setStrokeColor(colors.black)


def _draw_mark_scheme_qualification_page(pdf: canvas.Canvas, blueprint: PaperBlueprint, margin: float, height: float) -> None:
    y = height - 107
    pdf.setFont(MS_FONT_BOLD, 14)
    pdf.drawString(margin, y, "Unofficial practice qualification material")
    y -= 28
    pdf.setFont(MS_FONT, 11)
    paragraphs = [
        (
            "This unofficial practice mark scheme is generated for private revision and is "
            "not produced, endorsed or approved by Pearson or any exam board."
        ),
        (
            "For official qualification information, students should use Pearson's published "
            "specification, question papers and examiner materials."
        ),
        (
            "The guidance and indicative content in this generated version is designed to "
            "support consistent private practice marking across knowledge, application, "
            "analysis and evaluation."
        ),
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 82):
            pdf.drawString(margin, y, line)
            y -= 13
        y -= 12

    y -= 28
    pdf.setFont(MS_FONT_BOLD, 12)
    pdf.drawString(margin, y, "Independent practice material")
    y -= 24
    pdf.setFont(MS_FONT, 11)
    for line in _wrap(
        "This generated document follows the style of public mark schemes so that students can practise applying assessment objectives and levels-based descriptors.",
        82,
    ):
        pdf.drawString(margin, y, line)
        y -= 13

    paper_code = blueprint.paper_code.partition("/")[0]
    y = 132
    front_matter = [
        f"Summer {economics_exam_schedule(blueprint.paper_id).date.year}",
        f"Question Paper Log Number {paper_code}01",
        f"Publications Code {blueprint.paper_code.replace('/', '_')}_PRACTICE_MS",
        "All generated material in this practice publication is for revision use.",
        f"Unofficial independent practice material, {economics_exam_schedule(blueprint.paper_id).date.year}",
    ]
    for item in front_matter:
        pdf.drawString(margin, y, item)
        y -= 14


def _draw_ms_table_header(pdf: canvas.Canvas, y: float) -> None:
    _draw_ms_header_box(pdf, MS_LEFT, y - MS_HEADER_H, MS_RIGHT - MS_LEFT, MS_HEADER_H)


def _mark_scheme_rows(blueprint: PaperBlueprint, syllabus: Syllabus) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for question in blueprint.questions:
        if question.source_instance is not None:
            for item in question.parts or [question]:
                number = f"{question.number}({item.label})" if question.parts else question.number
                rows.extend(
                    _split_mark_scheme_row(
                        number,
                        f"({item.marks})",
                        _source_backed_mark_scheme_lines(item),
                    )
                )
            continue
        topic = syllabus.get_topic(question.topic_id)
        if question.parts:
            for part in question.parts:
                if (
                    blueprint.paper_id == "paper_1"
                    and question.section == "A"
                    and part.command_word not in {"calculate", "mcq"}
                ):
                    answer_lines = _paper_one_section_a_mark_scheme_lines(
                        question,
                        part,
                        topic,
                    )
                else:
                    answer_lines = _part_mark_scheme_lines(question, part, topic)
                if (
                    blueprint.paper_id == "paper_1"
                    and question.number == "1"
                    and part.label == "a"
                ):
                    answer_lines.extend(
                        [
                            "__PAGE_BREAK__",
                            "Further guidance",
                            "Credit a relevant diagram where it supports the stated chain of reasoning.",
                            "Award application only where the response uses the supplied data or context.",
                            "Do not award the same analytical link twice.",
                        ]
                    )
                if (
                    blueprint.paper_id == "paper_2"
                    and question.number == "1"
                    and part.label == "b"
                    and part.marks == 2
                ):
                    answer_lines = _paper_two_short_calculation_lines(
                        question,
                        part,
                        topic,
                    )
                part_rows = _split_mark_scheme_row(
                    f"{question.number}({part.label})",
                    f"({part.marks})",
                    answer_lines,
                )
                if (
                    blueprint.paper_id == "paper_1"
                    and (question.number, part.label) in {("3", "a"), ("5", "b")}
                ):
                    part_rows[0]["force_page_break"] = False
                rows.extend(part_rows)
        else:
            if (
                blueprint.paper_id == "paper_1"
                and question.number == "6(a)"
            ):
                rows.extend(
                    _split_mark_scheme_row(
                        question.number,
                        f"({question.marks})",
                        _paper_one_five_mark_diagram_lines(question, topic),
                    )
                )
                continue
            if (
                blueprint.paper_id == "paper_2"
                and question.number in {"6(c)", "6(d)", "6(e)"}
            ):
                rows.extend(
                    _split_mark_scheme_row(
                        question.number,
                        f"({question.marks})",
                        _paper_two_extended_mark_scheme_lines(question, topic),
                    )
                )
                continue
            if (
                blueprint.paper_id == "paper_1"
                and question.number == "6(e)"
            ):
                rows.extend(
                    _split_mark_scheme_row(
                        question.number,
                        f"({question.marks})",
                        _paper_one_fifteen_mark_scheme_lines(question, topic),
                    )
                )
                continue
            if question.marks == 12:
                knowledge_rows = _split_mark_scheme_row(
                    question.number,
                    "(8)",
                    _twelve_mark_knowledge_lines(question, topic),
                )
                knowledge_rows[0]["force_page_break"] = False
                rows.extend(knowledge_rows)
                rows.extend(
                    _split_mark_scheme_row(
                        f"{question.number} continued",
                        "(4)",
                        _twelve_mark_evaluation_lines(question, topic),
                    )
                )
                continue
            question_rows = _split_mark_scheme_row(
                question.number,
                f"({question.marks})",
                _question_mark_scheme_lines(question, topic),
            )
            if (
                blueprint.paper_id == "paper_3"
                and question.marks == 25
                and question.number in {"1(d)", "2(d)", "2(e)"}
            ):
                question_rows[1]["blank_page_before"] = "continuation"
            if question.section == "B" and question.marks == 5:
                question_rows[0]["force_page_break"] = False
            if blueprint.paper_id == "paper_3" and question.number == "2(b)":
                question_rows[0]["blank_page_before"] = "header"
            if blueprint.paper_id == "paper_3" and question.number == "1(b)":
                question_rows[1]["blank_page_before"] = "continuation"
            if blueprint.paper_id == "paper_1" and question.number == "8":
                question_rows[0]["blank_page_before"] = "header"
            rows.extend(question_rows)
    return rows


def _source_backed_mark_scheme_lines(item) -> list[str]:
    """Render each contract criterion as a discrete, visible examiner point."""
    criteria = []
    for point in item.mark_scheme:
        stripped = point.strip()
        if not stripped:
            continue
        if stripped.startswith(("The only correct answer", "Reject ")):
            criteria.append(stripped)
        else:
            criteria.append(f"● {stripped}")
    return [
        "Question focus: " + item.prompt,
        "Allocation: " + item.mark_breakdown,
        *criteria,
    ]


def _paper_two_short_calculation_lines(question, part, topic) -> list[str]:
    """Keep the two-mark calculation on its reference-matched single page."""

    return [
        *_specific_mark_scheme_context(
            question,
            part.prompt,
            topic,
            include_points=False,
        )[:3],
        "Knowledge 1, Application 1",
        "",
        *_calculation_answer_lines(part.prompt)[:5],
        "",
        "1 mark for selecting the correct values and method.",
        "1 mark for the correct answer with an appropriate unit.",
        "Award full marks for a valid alternative method.",
    ]


def _paper_one_fifteen_mark_scheme_lines(question, topic) -> list[str]:
    """Match the three-page knowledge, analysis and evaluation structure."""

    indicative = _scheme_bullets(
        question.indicative_content or topic.points,
        topic,
        limit=8,
    )
    source_points = _source_application_points(question.source_text, limit=6)
    return [
        question.mark_breakdown or "Knowledge 3, Application 3, Analysis 3, Evaluation 6",
        "Knowledge, application and analysis",
        *indicative[:5],
        "",
        "Credit accurate use of a relevant economic diagram where appropriate.",
        "__PAGE_BREAK__",
        "Application and developed analysis",
        "Relevant source evidence may include:",
        *(source_points or ["● Credit accurate use of the supplied context. (1)"]),
        "",
        "Level 0: A completely inaccurate response.",
        "Level 1: Identifies isolated economic ideas with limited application.",
        "Level 2: Applies evidence and develops a partial chain of reasoning.",
        "Level 3: Integrates relevant evidence within logical, sustained analysis.",
        "__PAGE_BREAK__",
        "Evaluation",
        "Level 0: No evaluative comments.",
        "Level 1: Identifies a generic limitation or alternative viewpoint.",
        "Level 2: Supports evaluation with relevant reasoning and context.",
        "Level 3: Weighs competing arguments and reaches a supported judgement.",
        "",
        "Credit any other valid, developed and context-supported evaluation.",
    ]


def _paper_one_five_mark_diagram_lines(question, topic) -> list[str]:
    title = topic.title.casefold()
    if "labour" in title or "wage" in title:
        diagram = "labour_market_diagram"
    elif topic.theme in {2, 4}:
        diagram = "ad_as_diagram"
    else:
        diagram = "market_diagram"
    source_points = _source_application_points(question.source_text, limit=3)
    return [
        question.mark_breakdown or "Knowledge 1, Application 1, Analysis 3",
        "Knowledge and analysis: up to 4 marks",
        *_one_mark_points(question, topic, limit=2),
        f"__ECONOMIC_DIAGRAM__:{diagram}",
        "Application: up to 1 mark",
        *(source_points[:2] or ["● Credit one accurate use of the supplied context. (1)"]),
    ]


def _paper_one_section_a_mark_scheme_lines(question, part, topic) -> list[str]:
    """Keep four-mark short answers concise enough for the measured page rhythm."""

    if part.command_word == "draw":
        return [
            part.mark_breakdown or "Knowledge 2, Application 2",
            "",
            "Diagram required",
            "1 mark for correctly labelled axes and relevant curves.",
            f"1 mark for the change linked to {topic.title.lower()}.",
            "1 mark for the resulting equilibrium, area or outcome.",
            "1 mark for accurate annotation or a context-linked explanation.",
            "",
            "Award full marks for an economically equivalent diagram.",
        ]

    source_points = _source_application_points(question.source_text, limit=2)
    return [
        part.mark_breakdown or "Knowledge 2, Application 1, Analysis 1",
        "Knowledge and analysis: up to 3 marks",
        "Valid points may include:",
        *_one_mark_points(question, topic, limit=4),
        "",
        "Application: 1 mark",
        *(source_points[:1] or ["● Credit one accurate use of the supplied context. (1)"]),
        "",
        "Credit a different valid chain of reasoning where it answers the question.",
    ]


def _paper_two_extended_mark_scheme_lines(question, topic) -> list[str]:
    """Use the four-page analysis/evaluation rhythm of the current Paper 2 scheme."""

    indicative = _scheme_bullets(
        question.indicative_content or topic.points,
        topic,
        limit=7,
    )
    source_points = _source_application_points(question.source_text, limit=5)
    return [
        question.mark_breakdown or "Knowledge, Application, Analysis and Evaluation",
        "Indicative content",
        *_specific_mark_scheme_context(
            question,
            question.prompt,
            topic,
            include_points=False,
        ),
        *indicative[:4],
        "",
        "Credit accurate use of a relevant economic diagram where appropriate.",
        "__PAGE_BREAK__",
        "Knowledge, application and analysis",
        "Level 0: A completely inaccurate response.",
        "Level 1: Displays isolated or imprecise knowledge and understanding.",
        "Uses generic information with no developed chain of reasoning.",
        "Level 2: Applies economic ideas to the context and develops partial analysis.",
        "Level 3: Selects relevant evidence and develops logical, coherent analysis.",
        "Level 4: Integrates evidence throughout a focused and sustained response.",
        *indicative[4:],
        "__PAGE_BREAK__",
        "Application and evaluation",
        "Relevant source evidence may include:",
        *(source_points or ["● Credit accurate use of the supplied context. (1)"]),
        "",
        "Indicative evaluation",
        "● The significance of the evidence depends on its scale and reliability.",
        "● Short-run adjustment may differ from the long-run outcome.",
        "● Effects can vary between consumers, firms, workers and regions.",
        "● Alternative policies or explanations may change the final judgement.",
        "__PAGE_BREAK__",
        "Evaluation",
        "Level 0: No evaluative comments.",
        "Level 1: Identifies generic evaluative comments without supporting evidence.",
        "There is little or no logical chain of reasoning.",
        "Level 2: Supports evaluative comments with relevant reasoning and context.",
        "Recognises at least one competing viewpoint or limitation.",
        "Level 3: Evaluates the relative significance of competing arguments.",
        "Reaches an informed judgement that answers the precise question.",
        "Credit any other valid, developed and context-supported evaluation.",
    ]


def _split_mark_scheme_row(number: str, mark: str, answer_lines: list[str]) -> list[dict[str, object]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in answer_lines:
        if line == "__PAGE_BREAK__":
            if current:
                chunks.append(current)
                current = []
            continue
        candidate = [*current, line]
        if current and _ms_row_height(candidate) > MS_MAX_ROW_HEIGHT:
            chunks.append(current)
            current = [line]
        else:
            current = candidate
    if current:
        chunks.append(current)

    return [
        {
            "number": number if index == 0 else f"{number} cont.",
            "mark": mark if index == len(chunks) - 1 else "",
            "answer_lines": chunk,
            "force_page_break": True,
        }
        for index, chunk in enumerate(chunks)
    ]


def _part_mark_scheme_lines(question, part, topic) -> list[str]:
    if part.command_word == "mcq":
        correct = part.correct_option or "A"
        lines = [f"The only correct answer is {correct}", ""]
        for option in part.options:
            if option.label != correct:
                lines.append(f"{option.label} is not correct as {option.text.lower().rstrip('.')}.")
                lines.append("")
        return lines
    if part.command_word == "calculate":
        return [
            *_specific_mark_scheme_context(question, part.prompt, topic),
            "Knowledge 2, Application 2",
            "",
            *_calculation_answer_lines(part.prompt),
            "Knowledge/Understanding: (up to 2 marks)",
            "1 mark for identifying the relevant values from the figure or data.",
            "1 mark for identifying the correct calculation or economic relationship.",
            "",
            "Application: (up to 2 marks)",
            "1 mark for accurate use of the data in the calculation.",
            "1 mark for the correct final answer with units or direction of change.",
            "",
            "Award full marks for a valid alternative method.",
        ]
    if part.command_word == "draw":
        return [
            *_specific_mark_scheme_context(question, part.prompt, topic),
            "Knowledge, Application and Analysis (4)",
            "",
            "1 mark for correctly labelled axes or curves.",
            f"1 mark for showing the relevant change linked to {topic.title.lower()}.",
            "1 mark for identifying the new equilibrium, area or outcome.",
            "1 mark for accurate annotation or explanation of the final effect.",
            "",
            "Award full marks for a correctly drawn and clearly labelled diagram.",
        ]
    if part.command_word == "explain":
        return [
            *_specific_mark_scheme_context(question, part.prompt, topic),
            "Knowledge 1, Application 1, Analysis 2",
            "",
            "Knowledge and Analysis (3)",
            f"1 mark for a relevant economic point about {topic.title.lower()}.",
            "1 mark for developing the point with a logical chain of reasoning.",
            "1 mark for explaining the likely effect on consumers, firms or the market.",
            "",
            "Application (1)",
            "1 mark for relevant use of the data, figure or context.",
        ]
    return [
        *_specific_mark_scheme_context(question, part.prompt, topic),
        part.mark_breakdown or "Knowledge 2, Application 2",
        "",
        "Knowledge/Understanding: (up to 2 marks)",
        f"1 mark for identifying a relevant point about {topic.title.lower()}.",
        "1 mark for developing the point using accurate economics.",
        "",
        "Application: (up to 2 marks)",
        "1 mark for relevant use of the figure, extract or data.",
        "1 mark for a supported conclusion or calculation.",
        "",
        "Award full marks for a complete and accurate response.",
    ]


def _question_mark_scheme_lines(question, topic) -> list[str]:
    if question.marks <= 5:
        knowledge = [
            "Knowledge 2, Application 2, Analysis 1",
            "",
            "Knowledge/implicit understanding and analysis: up to 3 marks e.g.",
            *_one_mark_points(question, topic, limit=5),
            "",
        ]
        application = [
            "Application: up to 2 marks e.g.",
            *_source_application_points(question.source_text, limit=5),
        ]
        return [*knowledge, *application]
    if question.marks == 8:
        return [
            "Knowledge 2, Application 2, Analysis 2, Evaluation 2",
            "",
            "Knowledge/analysis: up to 4 marks e.g.",
            *_one_mark_points(question, topic, limit=8),
            "",
            "__PAGE_BREAK__",
            "Application: 2 marks for two relevant points e.g.",
            *_source_application_points(question.source_text, limit=6),
            "",
            "Evaluation: 2 marks for one developed point or two points e.g.",
            "● The effect depends on the magnitude of the change and the evidence available. (1)",
            "● The short-run effect may differ from the long-run effect. (1)",
            "● Outcomes depend on elasticities, spare capacity and stakeholder responses. (1)",
            "● A supported alternative explanation or limitation should be credited. (1)",
        ]
    if question.marks == 25:
        return _twenty_five_mark_scheme_lines(question, topic)
    return [
        *_specific_mark_scheme_context(question, question.prompt, topic, include_points=False),
        "Indicative content",
        *_scheme_bullets(question.indicative_content or topic.points[:4], topic, limit=5),
        "",
        "Level 1: displays isolated knowledge and limited understanding of economic terms.",
        "Level 2: applies knowledge to the context with partial chains of reasoning.",
        "Level 3: demonstrates clear application and developed analysis of relevant issues.",
        "Level 4: provides balanced analysis with supported evaluation and judgement.",
        "Level 5: shows sustained judgement, coherent chains of reasoning and developed evaluation.",
        "",
        question.mark_breakdown or "Knowledge, Application, Analysis and Evaluation",
        *_scheme_bullets(question.mark_scheme, topic),
    ]


def _one_mark_points(question, topic, *, limit: int) -> list[str]:
    core_points = list(_CORE_MARK_SCHEME_POINTS.get(topic.title.lower(), ()))
    specific_points = _specific_answer_points(question, topic)
    context = " ".join(
        [
            getattr(question, "prompt", ""),
            getattr(question, "source_text", ""),
            *[
                getattr(part, "prompt", "")
                for part in getattr(question, "parts", ())
            ],
        ]
    )
    relevant_specific = sorted(
        enumerate(specific_points),
        key=lambda item: (-_mark_point_relevance(item[1], context), item[0]),
    )
    selected_specific = [
        point
        for _index, point in relevant_specific[: max(1, limit // 2)]
        if _mark_point_relevance(point, context) > 0
    ]
    points = [
        *core_points[:1],
        *selected_specific,
        *core_points[1:],
        *specific_points,
    ]
    points = list(dict.fromkeys(points))
    if not points:
        points = [f"Accurate explanation of {topic.title.lower()}."]
    return [f"● {point.rstrip('.')} (1)" for point in points[:limit]]


def _mark_point_relevance(point: str, context: str) -> int:
    ignored = {
        "about",
        "after",
        "above",
        "between",
        "change",
        "credit",
        "explain",
        "likely",
        "market",
        "point",
        "question",
        "reference",
        "their",
        "there",
        "these",
        "those",
        "where",
        "which",
    }

    def terms(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z]{4,}", text.casefold())
            if token not in ignored
        }

    return len(terms(point) & terms(context))


_CORE_MARK_SCHEME_POINTS = {
    "demand": (
        "Demand is the quantity consumers are willing and able to buy at a given price.",
        "A change in price causes a movement along the demand curve.",
        "Income, tastes, population and the prices of related goods can shift demand.",
        "The size of the response depends on price elasticity of demand.",
        "Substitutes and the proportion of income spent influence price elasticity.",
    ),
    "supply": (
        "Supply is the quantity producers are willing and able to sell at a given price.",
        "Price elasticity of supply measures responsiveness of quantity supplied to price.",
        "Limited capacity and stocks make supply less responsive in the short run.",
        "Production time, input availability and spare capacity affect supply responsiveness.",
        "Investment can make supply more elastic in the long run.",
    ),
    "market failure": (
        "Market failure occurs when the price mechanism causes a misallocation of resources.",
        "External costs or benefits affect third parties outside the market transaction.",
        "Imperfect information can prevent consumers from making welfare-maximising choices.",
        "The free-market equilibrium may differ from the socially efficient level of output.",
        "A welfare loss can be shown between marginal social and private curves.",
    ),
    "government intervention": (
        "An indirect tax raises firms' costs and shifts market supply to the left.",
        "A subsidy lowers production costs and can increase market supply.",
        "Regulation can change the incentives facing firms and consumers.",
        "The incidence of a policy depends on the elasticities of demand and supply.",
        "Intervention can create government failure if information or enforcement is weak.",
    ),
    "business growth": (
        "Organic growth occurs when a firm expands using its own resources.",
        "External growth occurs through a merger or takeover.",
        "Greater scale can reduce average cost through purchasing or technical economies.",
        "Rapid expansion can create communication and coordination diseconomies.",
        "Access to finance and market demand constrain the rate of growth.",
    ),
    "revenues, costs and profits": (
        "Profit is total revenue minus total cost.",
        "Fixed costs do not change with output in the short run.",
        "Higher variable costs increase total and average cost.",
        "Economies of scale reduce long-run average cost as output expands.",
        "The effect on profit depends on the response of revenue as well as cost.",
    ),
    "market structures": (
        "Barriers to entry protect incumbent firms from potential competition.",
        "A high concentration ratio may indicate substantial market power.",
        "Contestability depends on the height of entry and exit barriers.",
        "Economies of scale can create a cost disadvantage for new entrants.",
        "Stronger competition can increase allocative and dynamic efficiency.",
    ),
    "labour market": (
        "The demand for labour is derived from demand for the final product.",
        "Wages are influenced by labour demand, labour supply and productivity.",
        "Occupational immobility can create shortages of skilled workers.",
        "A monopsonist may have wage-setting power in a local labour market.",
        "Training and migration can increase the effective supply of labour over time.",
    ),
}


def _source_application_points(text: str, *, limit: int) -> list[str]:
    sentences = [
        _sentence(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
        if sentence.strip()
    ]
    return [f"● {sentence.rstrip('.')} (1)" for sentence in sentences[:limit]]


def _twelve_mark_knowledge_lines(question, topic) -> list[str]:
    return [
        "Knowledge 2, Application 2, Analysis 4",
        "Indicative content",
        *_scheme_bullets(question.indicative_content or topic.points, topic, limit=3),
    ]


def _twelve_mark_evaluation_lines(question, topic) -> list[str]:
    return [
        "Knowledge, application and analysis",
        "Level 0: A completely inaccurate response.",
        "Level 1 (1–2): Displays isolated or imprecise knowledge and understanding.",
        "Uses generic information and has no developed chains of reasoning.",
        "Level 2 (3–5): Applies some economic ideas to the context.",
        "Develops partial chains of reasoning but may lack balance or focus.",
        "Level 3 (6–8): Demonstrates accurate knowledge and understanding.",
        "Selects relevant evidence and develops logical, coherent chains of reasoning.",
        "",
        "Application evidence may include:",
        *_source_application_points(question.source_text, limit=3),
        "",
        "Evaluation 4",
        "Indicative evaluation",
        "● Prioritisation of the most significant factor or effect.",
        "● The significance of the evidence may change over time.",
        "● Short-run and long-run outcomes may differ.",
        "● Different firms, consumers or regions may experience different effects.",
        "● The conclusion depends on elasticities, spare capacity and policy effectiveness.",
        "",
        "__PAGE_BREAK__",
        "Further indicative content",
        *_scheme_bullets(question.indicative_content or topic.points, topic, limit=5),
        "",
        "Evaluation",
        "Level 0: No evaluative comments.",
        "Level 1 (1–2): Identifies generic evaluative comments without supporting evidence.",
        "There is little or no logical chain of reasoning.",
        "Level 2 (3–4): Supports evaluative comments with relevant reasoning and context.",
        "Recognises different viewpoints and reaches an informed judgement.",
    ]


def _twenty_five_mark_scheme_lines(question, topic) -> list[str]:
    context = question.source_title.lower() if question.source_title else "the case-study context"
    return [
        "Knowledge 4, Application 4, Analysis 8, Evaluation 9",
        "Indicative content",
        "Microeconomic analysis may include:",
        *_scheme_bullets(question.indicative_content or topic.points, topic, limit=8),
        f"● Effects on prices, output, costs, revenue and profit in {context}.",
        "● Effects on consumers, workers, competition and economic welfare.",
        "● A relevant and accurately labelled microeconomic diagram.",
        "● A developed chain from the initial change to stakeholder outcomes.",
        "",
        "__PAGE_BREAK__",
        "Macroeconomic analysis may include:",
        "● Effects on aggregate demand, aggregate supply and the price level.",
        "● Effects on real output, employment, investment and productivity.",
        "● Effects on tax revenue, government spending and the budget balance.",
        "● Effects on trade, exchange rates or the current account where relevant.",
        "● Multiplier, accelerator or supply-side effects where relevant.",
        *_source_application_points(question.source_text, limit=5),
        "",
        "Evaluation: up to 9 marks",
        "● Prioritise the most significant effect using the evidence.",
        "● Distinguish short-run adjustment from long-run outcomes.",
        "● Consider the magnitude, duration and distribution of the change.",
        "● Consider elasticities, spare capacity and the reliability of the data.",
        "● Compare impacts on different stakeholders and possible policy responses.",
        "● Reach a supported judgement that answers the precise question.",
        "",
        "__PAGE_BREAK__",
        "Knowledge, application and analysis",
        "Level 0: A completely inaccurate response.",
        "Level 1 (1–4): Identifies a small range of relevant information.",
        "Shows limited application and narrow or undeveloped analysis.",
        "Level 2 (5–8): Applies economic ideas to problems in context.",
        "Develops some analysis but does not cover the broad elements of the question.",
        "Level 3 (9–12): Analysis is clear and coherent with evidence integrated.",
        "Applies economic ideas directly to most broad elements of the question.",
        "Level 4 (13–16): Analysis is relevant, clear and coherent.",
        "Evidence is fully integrated and both microeconomic and macroeconomic effects are covered.",
        "",
        "Evaluation",
        "Level 0: No evaluative comments.",
        "Level 1 (1–3): Identifies evaluative comments without explanation.",
        "Level 2 (4–6): Gives evaluative comments with limited explanation.",
        "Considers alternatives but may make a generic or unbalanced judgement.",
        "Level 3 (7–9): Supports evaluation with relevant reasoning and context.",
        "Recognises different viewpoints, challenges assumptions and reaches an informed judgement.",
        "For Level 3 evaluation, the final judgement must be sustained and answer the question.",
    ]


def _scheme_bullets(items: list[str], topic=None, limit: int = 8) -> list[str]:
    points: list[str] = []
    for item in items:
        point = _normalise_mark_point(item, topic)
        if point:
            points.append(f"- {point}")
        if len(points) == limit:
            break
    return points


def _calculation_answer_lines(prompt: str) -> list[str]:
    lowered = prompt.lower()
    if "cinema tickets falls by 5%" in lowered and "ped value" in lowered:
        return [
            "Correct working:",
            "5% x 1.4 = 7%",
            "Correct answer: quantity demanded increases by 7%.",
            "",
        ]
    if "pes value for the rural market" in lowered and "quantity supplied increases by 3.6%" in lowered:
        return [
            "Correct working:",
            "3.6% / 1.8 = 2.0%",
            "Correct answer: price increases by 2.0%.",
            "",
        ]
    if "three-firm concentration ratio" in lowered:
        return [
            "Correct working:",
            "24.6% + 19.5% + 7.7% = 51.8%",
            "Correct answer: the three-firm concentration ratio is 51.8%.",
            "",
        ]
    if "percentage change in the quantity demanded index" in lowered:
        return [
            "Correct working:",
            "((88.0 - 74.2) / 74.2) x 100 = 18.6%",
            "Correct answer: the quantity demanded index increased by 18.6%.",
            "",
        ]
    if "difference between the quantity demanded index and the average price index" in lowered:
        return [
            "Correct working:",
            "88.0 - 75.2 = 12.8",
            "Correct answer: the difference is 12.8 index points.",
            "",
        ]
    if "trade deficit in 2023" in lowered:
        return [
            "Correct working:",
            "imports - exports = trade deficit",
            "Correct answer: the trade deficit is the gap between imports and exports.",
            "",
        ]
    if "index-point increase" in lowered:
        return [
            "Correct working:",
            "2023 CPI index - 2021 CPI index",
            "Correct answer: the increase is measured in index points.",
            "",
        ]
    if "hdi" in lowered:
        return [
            "Correct working:",
            "0.683 - 0.544 = 0.139",
            "Correct answer: the difference in HDI is 0.139.",
            "",
        ]
    return [
        "Correct working:",
        "Award marks for a valid calculation using the data shown.",
        "Correct answer: award marks for a final answer with units or direction of change.",
        "",
    ]


def _specific_mark_scheme_context(question, prompt: str, topic, *, include_points: bool = True) -> list[str]:
    lines = [
        f"Question focus: {_sentence(prompt)}",
    ]
    if question.source_text:
        lines.extend(
            [
                "",
                "Relevant source evidence:",
                f"- {_brief_source_evidence(question.source_text)}",
            ]
        )
    points = _specific_answer_points(question, topic) if include_points else []
    if points:
        lines.extend(["", "Valid points may include:", *[f"- {point}" for point in points]])
    lines.append("")
    return lines


def _specific_answer_points(question, topic) -> list[str]:
    seen: set[str] = set()
    points: list[str] = []
    note_points = note_points_for_topic(topic.id, title=topic.title, keywords=topic.points, limit=6)
    for item in [*question.indicative_content, *note_points, *question.mark_scheme, *topic.points]:
        cleaned = _normalise_mark_point(item, topic)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            points.append(cleaned)
        if len(points) == 5:
            break
    return points


def _sentence(text: str) -> str:
    cleaned = _strip_leading_bullet(text)
    cleaned = cleaned.rstrip(" .;:")
    return cleaned[:1].upper() + cleaned[1:] + "." if cleaned else ""


def _normalise_mark_point(text: str, topic=None) -> str:
    cleaned = _strip_leading_bullet(text)
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    weak_starts = (
        "advantage",
        "disadvantage",
        "advantages",
        "disadvantages",
        "as a result",
        "this diagram",
        "some example",
    )
    if lowered.startswith(weak_starts):
        return ""
    phrase = cleaned.rstrip(" .;:")
    if len(phrase.split()) <= 4:
        if not topic:
            return ""
        return f"Credit explanation of {phrase.lower()} where applied to {topic.title.lower()}."
    return _sentence(cleaned)


def _strip_leading_bullet(text: str) -> str:
    cleaned = " ".join(str(text).split())
    cleaned = re.sub(r"^(?:[•●]\s*|\-\s+|o\s+)+", "", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip()


def _brief_source_evidence(text: str, limit: int = 260) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return _sentence(cleaned)


def _draw_ms_row(
    pdf: canvas.Canvas,
    y: float,
    number: str,
    answer_lines: list[str],
    mark: str,
) -> float:
    left = MS_LEFT
    number_w = MS_NUMBER_W
    mark_w = MS_MARK_W
    right = MS_RIGHT
    answer_x = left + number_w + 6
    mark_x = right - mark_w
    row_height = _ms_row_height(answer_lines)
    bottom = y - row_height
    _draw_ms_header_box(pdf, left, y - MS_HEADER_H, right - left, MS_HEADER_H)
    pdf.rect(left, bottom, right - left, row_height - MS_HEADER_H, stroke=1, fill=0)
    pdf.line(left + number_w, bottom, left + number_w, y)
    pdf.line(mark_x, bottom, mark_x, y)
    pdf.setFont(MS_FONT_BOLD, 11)
    pdf.drawString(left + 6, y - MS_HEADER_H - 17, number)
    pdf.setFont(MS_FONT, 11)
    cursor = y - MS_HEADER_H - 13
    for line in answer_lines:
        if not line:
            cursor -= 10
            continue
        if line.startswith("__ECONOMIC_DIAGRAM__:"):
            diagram = line.partition(":")[2]
            cursor = _draw_economics_graph(
                pdf,
                answer_x + 28,
                cursor - 4,
                diagram,
            )
            continue
        if _ms_bold_line(line):
            font = MS_FONT_BOLD
        elif _ms_italic_line(line):
            font = MS_FONT_ITALIC
        else:
            font = MS_FONT
        pdf.setFont(font, 11)
        is_bullet = line.startswith("●")
        line_x = answer_x + (40 if is_bullet else 22)
        for wrapped in _wrap(line, _ms_wrap_width(line)):
            if _ms_centered_line(wrapped):
                pdf.drawCentredString((answer_x + mark_x) / 2, cursor, wrapped)
            else:
                pdf.drawString(line_x, cursor, wrapped)
            cursor -= MS_BODY_LEADING
        if _ms_bold_line(line) and not _ms_centered_line(line):
            cursor -= 8
    pdf.setFont(MS_FONT_BOLD, 11)
    pdf.drawString(mark_x + 10, bottom + 24, mark)
    return bottom


def _draw_ms_header_box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    pdf.setFillColor(colors.HexColor("#e6e6e6"))
    pdf.rect(x, y, w, h, stroke=1, fill=1)
    pdf.setFillColor(colors.black)
    pdf.line(x + MS_NUMBER_W, y, x + MS_NUMBER_W, y + h)
    pdf.line(x + w - MS_MARK_W, y, x + w - MS_MARK_W, y + h)
    pdf.setFont(MS_FONT, 11)
    pdf.drawString(x + 6, y + h - 14, "Question")
    pdf.drawString(x + 6, y + h - 27, "Number")
    pdf.drawString(x + MS_NUMBER_W + 6, y + h / 2 - 4, "Answer")
    pdf.drawString(x + w - MS_MARK_W + 10, y + h / 2 - 4, "Mark")


def _ms_row_height(answer_lines: list[str]) -> int:
    content_height = 0
    for line in answer_lines:
        if not line:
            content_height += 10
            continue
        if line.startswith("__ECONOMIC_DIAGRAM__:"):
            content_height += 202
            continue
        content_height += max(1, len(_wrap(line, _ms_wrap_width(line)))) * MS_BODY_LEADING
        if _ms_bold_line(line) and not _ms_centered_line(line):
            content_height += 8
    return max(112, int(MS_HEADER_H + 20 + content_height))


def _ms_wrap_width(line: str) -> int:
    return 48 if line.startswith("●") else MS_ANSWER_WRAP_CHARS


def _ms_centered_line(line: str) -> bool:
    return bool(re.match(r"^Knowledge \d, Application \d", line))


def _ms_italic_line(line: str) -> bool:
    content = line.removeprefix("● ")
    return content.startswith("Reject ") or " is not correct as " in content.casefold()


def _ms_bold_line(line: str) -> bool:
    prefixes = (
        "Knowledge",
        "Application",
        "Analysis",
        "Indicative content",
        "Level ",
        "Award full",
        "The only correct answer",
    )
    return line.startswith(prefixes)
