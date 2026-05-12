from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from pastpapergen.exam_dates import economics_exam_schedule, formatted_economics_exam_date
from pastpapergen.models import PaperBlueprint, Syllabus
from pastpapergen.notes import note_points_for_topic
from pastpapergen.source_cases import GENERIC_SOURCE_ATTRIBUTION

ANSWER_LINE_GAP_PT = 28
ANSWER_LINE_COLOR_HEX = "#505050"
ANSWER_LINE_DASH = (0.6, 1.6)
BODY_FONT_SIZE_PT = 12
BODY_LEADING_PT = 14
FONT_REGULAR = "ExamSans"
FONT_BOLD = "ExamSans-Bold"
MS_ANSWER_WRAP_CHARS = 58
SECTION_A_FOOTER_SAFE_Y = 128
SECTION_A_INSTRUCTION_LINES = [
    "Answer ALL questions. Write your answers in the spaces provided.",
    "Some questions must be answered with a cross in a box. If you change your mind",
    "about an answer, put a line through the box and then mark your new answer",
    "with a cross.",
    "You are advised to spend 30 minutes on this section.",
    "Use the data to support your answers where relevant.",
    "You may annotate and include diagrams in your answers.",
]


def _register_fonts() -> None:
    font_sets = [
        [
            (FONT_REGULAR, Path("/System/Library/Fonts/HelveticaNeue.ttc"), 0),
            (FONT_BOLD, Path("/System/Library/Fonts/HelveticaNeue.ttc"), 1),
        ],
        [
            (FONT_REGULAR, Path("/System/Library/Fonts/Supplemental/Arial.ttf"), 0),
            (FONT_BOLD, Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"), 0),
        ],
    ]
    fonts = next((candidate for candidate in font_sets if all(path.exists() for _, path, _ in candidate)), font_sets[-1])
    for name, path, subfont_index in fonts:
        if name not in pdfmetrics.getRegisteredFontNames() and path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=subfont_index))


_register_fonts()


def render_question_paper(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    _draw_cover(pdf, blueprint)
    pdf.showPage()
    _draw_question_pages(pdf, blueprint)
    pdf.save()


def _draw_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    width, height = A4
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

    pdf.setFont(FONT_BOLD, 8)
    pdf.drawCentredString(panel_x + panel_w / 2, panel_y + panel_h - 14, "Please check the examination details below before entering your candidate information")

    name_y = panel_y + panel_h - 45
    pdf.roundRect(panel_x + 14, name_y, panel_w - 28, 30, 8, stroke=1, fill=0)
    pdf.line(panel_x + panel_w / 2, name_y, panel_x + panel_w / 2, name_y + 30)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawString(panel_x + 22, name_y + 18, "Candidate surname")
    pdf.drawString(panel_x + panel_w / 2 + 8, name_y + 18, "Other names")

    box_y = name_y - 42
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawString(panel_x + 16, box_y + 33, "Centre Number")
    _draw_boxes(pdf, panel_x + 17, box_y, 5, size=22)
    pdf.drawString(panel_x + 140, box_y + 33, "Candidate Number")
    _draw_boxes(pdf, panel_x + 140, box_y, 4, size=22)

    y = box_y - 22
    pdf.setFont(FONT_BOLD, 17)
    pdf.drawString(panel_x + 14, y, "Pearson Edexcel Level 3 GCE")
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
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 88, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(panel_x + 22, y + 63, "Economics A")
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(panel_x + 22, y + 43, "Advanced")
    paper_number = blueprint.paper_id[-1]
    pdf.drawString(panel_x + 22, y + 26, f"PAPER {paper_number}: {blueprint.title}")

    y -= 45
    required_h = 40
    pdf.roundRect(panel_x + 14, y, panel_w - 88, required_h, 7, stroke=1, fill=0)
    pdf.roundRect(panel_x + panel_w - 70, y, 56, required_h, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 25, "You must have:")
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 22, y + 9, "a calculator.")
    pdf.drawCentredString(panel_x + panel_w - 42, y + 21, "Total Marks")

    text_x = 96
    y = 430
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
        ],
    )
    y -= 126
    _draw_front_section(
        pdf,
        text_x,
        y,
        "Information",
        [
            f"The total mark for this paper is {blueprint.total_marks}.",
            "The marks for each question are shown in brackets - use this as a guide as to how much time to spend on each question.",
            "Calculators may be used.",
        ],
    )
    y -= 92
    _draw_front_section(
        pdf,
        text_x,
        y,
        "Advice",
        [
            "Read each question carefully before you start to answer it.",
            "Check your answers if you have time at the end.",
        ],
    )

    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawRightString(width - 64, 75, "Turn over  >")
    _draw_cover_pearson_mark(pdf, width - 88, 44)
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawString(58, 43, "P00000A")
    pdf.drawString(58, 31, "Practice paper generated for revision use.")
    _draw_fake_barcode(pdf, width / 2 - 105, 32, "P  0  0  0  0  0  A  0  1")


def _exam_date_line(paper_id: str) -> str:
    return formatted_economics_exam_date(paper_id)


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
    pdf.setFont(FONT_BOLD, 11.5)
    pdf.drawString(x, y, heading)
    pdf.setFont(FONT_REGULAR, 10.5)
    y -= 18
    for line in lines:
        wrapped = _wrap(line, 74)
        for idx, part in enumerate(wrapped):
            prefix = "• " if idx == 0 else "  "
            pdf.drawString(x, y, prefix + part)
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


def _draw_fake_barcode(pdf: canvas.Canvas, x: float, y: float, caption: str) -> None:
    widths = [1, 2, 1, 3, 1, 1, 2, 3, 1, 2, 1, 1, 3, 1, 2, 1, 1, 2, 3, 1, 2, 1, 1]
    cursor = x
    pdf.setFillColor(colors.black)
    for idx, width in enumerate(widths * 4):
        if idx % 2 == 0:
            pdf.rect(cursor, y + 13, width, 28, stroke=0, fill=1)
        cursor += width + 1
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawCentredString(x + 92, y, caption)
    pdf.setFillColor(colors.black)


def _draw_cover_pearson_mark(pdf: canvas.Canvas, x: float, y: float) -> None:
    pdf.setFillColor(colors.HexColor("#1f1f1f"))
    pdf.circle(x, y + 22, 12, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 15)
    pdf.drawCentredString(x, y + 17, "P")
    pdf.setFillColor(colors.HexColor("#1f1f1f"))
    pdf.setFont(FONT_BOLD, 16)
    pdf.drawCentredString(x, y - 4, "Pearson")
    pdf.setFillColor(colors.black)


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
    width, height = A4
    margin = 48
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
                y = _draw_continuation_lines(pdf, margin, y)
        pages_needed = _extra_answer_pages(blueprint.paper_id, question)
        if _force_new_page_after_question(blueprint.paper_id, question):
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = _prepare_answer_page(pdf, blueprint, page_number)
            if next_question is None or next_question.section != question.section:
                current_section = None
            continue
        if y < 130:
            _draw_question_footer(pdf, blueprint, page_number)
            pdf.showPage()
            page_number += 1
            y = _prepare_answer_page(pdf, blueprint, page_number)
    _draw_question_footer(pdf, blueprint, page_number)


def _force_new_page_after_question(paper_id: str, question) -> bool:
    if paper_id in {"paper_1", "paper_2"}:
        return question.section in {"A", "B"} or question.marks == 25
    return question.section in {"A", "B"}


def _extra_answer_pages(paper_id: str, question) -> int:
    if question.marks == 25:
        return 4
    if paper_id in {"paper_1", "paper_2"} and question.section == "A":
        return 1
    if paper_id not in {"paper_1", "paper_2"} or question.section != "B":
        return 0
    return {5: 0, 8: 1, 10: 1, 12: 2, 15: 4}.get(question.marks, 0)


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
        pdf.setFillColor(colors.HexColor("#999999"))
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
    y = _draw_section_b_extract_block(pdf, section_b, extracts[:2], y)
    _draw_question_footer(pdf, blueprint, page_number)
    pdf.showPage()
    page_number += 1
    y = _prepare_answer_page(pdf, blueprint, page_number)
    y = _draw_section_b_extract_block(pdf, section_b, extracts[2:], y, include_question_title=False)
    _draw_question_footer(pdf, blueprint, page_number)
    pdf.showPage()
    page_number += 1
    return page_number, _prepare_answer_page(pdf, blueprint, page_number)


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
        source_lines = _wrap(question.source_text, 72)[:5]
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
            _draw_question_footer(pdf, blueprint, page_number)
            return
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)


def _draw_continuation_lines(pdf: canvas.Canvas, x: float, y: float) -> float:
    return _draw_answer_lines_until(pdf, x, y, 520)


def _prepare_answer_page(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int) -> float:
    width, height = A4
    _draw_crop_marks(pdf)
    _draw_do_not_write_rail(pdf, page_number)
    pdf.setStrokeColor(colors.HexColor("#9d9d9d"))
    pdf.setLineWidth(1.6)
    pdf.roundRect(34, 76, 526, 704, 8, stroke=1, fill=0)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    return height - 90


def _draw_do_not_write_rail(pdf: canvas.Canvas, page_number: int) -> None:
    width, height = A4
    rail_x = 6 if page_number % 2 == 1 else width - 28
    pdf.setFillColor(colors.HexColor("#f0f0f0"))
    pdf.rect(rail_x, 66, 21, 705, stroke=0, fill=1)
    _draw_hatched_rail(pdf, rail_x, 66, 21, 705)
    pdf.setFillColor(colors.HexColor("#777777"))
    pdf.setFont(FONT_BOLD, 8)
    for y in (135, 330, 525):
        pdf.saveState()
        pdf.translate(rail_x + 14, y)
        pdf.rotate(270)
        pdf.drawCentredString(0, 0, "DO NOT WRITE IN THIS AREA")
        pdf.restoreState()
    pdf.setFillColor(colors.black)


def _draw_hatched_rail(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    pdf.setStrokeColor(colors.HexColor("#d2d2d2"))
    pdf.setLineWidth(0.25)
    step = 5
    top = y + h
    for yy in range(int(y), int(top), step):
        y2 = min(yy + w, top)
        dx = y2 - yy
        pdf.line(x, yy, x + dx, y2)
        pdf.line(x + w, yy, x + w - dx, y2)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)


def _draw_question_footer(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int) -> None:
    width, _ = A4
    pdf.setFont(FONT_BOLD, 8)
    if page_number % 2 == 1:
        pdf.drawRightString(width - 72, 42, str(page_number))
        pdf.setFont(FONT_REGULAR, 9)
        pdf.drawRightString(width - 58, 22, "Turn over  >")
        block_x = 72
    else:
        pdf.drawString(72, 42, str(page_number))
        block_x = width - 98
    _draw_fake_barcode(pdf, width / 2 - 105, 26, f"P  0  0  0  0  0  A  0  {page_number:02d}")
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawString(block_x, 42, "■□■□")


def _draw_section_intro(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    section: str,
    y: float,
) -> float:
    width, _ = A4
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawCentredString(width / 2, y, f"SECTION {section}")
    y -= 25
    if blueprint.paper_id in {"paper_1", "paper_2"} and section == "A":
        pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
        for index, line in enumerate(SECTION_A_INSTRUCTION_LINES):
            pdf.drawCentredString(width / 2, y, line)
            y -= 24 if index in {0, 3, 4} else BODY_LEADING_PT
        return y - 4
    is_section_b_prompt = blueprint.paper_id in {"paper_1", "paper_2"} and section == "B"
    pdf.setFont(FONT_BOLD if is_section_b_prompt else FONT_REGULAR, BODY_FONT_SIZE_PT)
    for index, line in enumerate(_section_instruction_lines(blueprint.paper_id, section)):
        pdf.drawCentredString(width / 2, y, line)
        y -= 22 if is_section_b_prompt and index in {1, 2} else BODY_LEADING_PT
    return y - (18 if is_section_b_prompt else 12)


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
            y = _draw_stimulus(pdf, question.stimulus_kind, x + 105, y)
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

    pdf.drawRightString(width - x, y + 12, f"({question.marks})")
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
    if _should_draw_inline_context(stimulus_kind):
        y = _draw_inline_context(pdf, question.source_text, x + 20, y)
        y -= 10
    if stimulus_kind:
        y = _draw_stimulus(pdf, stimulus_kind, x + 110, y, question.source_text)
        y -= 28

    if first_part and first_part.command_word == "draw" and second_part and second_part.marks == 1:
        y = _draw_draw_part_with_axes(pdf, first_part, x, y)
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

    if len(question.parts) > 2:
        y = _draw_compact_part(pdf, question.parts[0], x, y)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        y = _prepare_answer_page(pdf, blueprint, page_number)
        for part in question.parts[1:]:
            y = _draw_compact_part(pdf, part, x, y - 4)
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
    pdf.setFillColor(colors.HexColor("#999999"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 28
    return _draw_answer_lines_until(pdf, x, y, width - x, bottom_y=bottom_y)


def _draw_draw_part_with_axes(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#999999"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 18
    y_label, x_label = _axis_labels_for_draw_prompt(part.prompt)
    return _draw_blank_answer_axes(pdf, x + 34, y, width - x - 130, 130, x_label=x_label, y_label=y_label) - 10


def _draw_calculate_part_with_working_lines(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    width, _ = A4
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#999999"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 20
    y = _draw_answer_lines(pdf, x, y, width - x, 6, bottom_y=SECTION_A_FOOTER_SAFE_Y)
    return y - 12


def _draw_compact_part(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    width, _ = A4
    if part.command_word == "mcq":
        return _draw_mcq_part(pdf, part, x, y)
    y = _draw_part_prompt(pdf, part, x, y)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.setFillColor(colors.HexColor("#999999"))
    pdf.drawRightString(width - x, y + BODY_LEADING_PT, f"({part.marks})")
    pdf.setFillColor(colors.black)
    y -= 18
    lines = 4 if part.marks <= 2 else 7
    return _draw_answer_lines(pdf, x, y, width - x, lines, bottom_y=SECTION_A_FOOTER_SAFE_Y) - 12


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
    pdf.line(x, bottom, x, y)
    pdf.line(x, bottom, x + w, bottom)
    pdf.line(x, y, x - 3, y - 7)
    pdf.line(x, y, x + 3, y - 7)
    pdf.line(x + w, bottom, x + w - 7, bottom + 3)
    pdf.line(x + w, bottom, x + w - 7, bottom - 3)
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
    for line in _wrap(text, 66)[:3]:
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
    pdf.setFillColor(colors.HexColor("#999999"))
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
    _set_answer_line_style(pdf)
    for _ in range(line_count):
        if y < bottom_y:
            break
        pdf.line(x, y, right_x, y)
        y -= ANSWER_LINE_GAP_PT
    _reset_line_style(pdf)
    return y


def _draw_answer_lines_until(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    right_x: float,
    bottom_y: float = 90,
) -> float:
    _set_answer_line_style(pdf)
    while y >= bottom_y:
        pdf.line(x, y, right_x, y)
        y -= ANSWER_LINE_GAP_PT
    _reset_line_style(pdf)
    return y


def _set_answer_line_style(pdf: canvas.Canvas) -> None:
    pdf.setStrokeColor(colors.HexColor(ANSWER_LINE_COLOR_HEX))
    pdf.setLineWidth(0.35)
    if ANSWER_LINE_DASH:
        pdf.setDash(*ANSWER_LINE_DASH)
    else:
        pdf.setDash()


def _reset_line_style(pdf: canvas.Canvas) -> None:
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    pdf.setDash()


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


def _draw_stimulus(pdf: canvas.Canvas, kind: str, x: float, y: float, context_text: str = "") -> float:
    if kind in _ECONOMICS_GRAPH_KINDS:
        return _draw_economics_graph(pdf, x, y, kind)
    if kind in _TABLE_KINDS:
        return _draw_data_table(pdf, x - 35, y, kind)
    if kind in _BAR_CHART_KINDS:
        return _draw_bar_chart(pdf, x - 10, y, kind)
    if kind in _LINE_CHART_KINDS:
        return _draw_line_graph(pdf, x - 10, y, kind)
    if kind == "payoff_matrix":
        return _draw_payoff_matrix(pdf, x - 25, y)
    return _draw_context_box(pdf, x - 70, y, context_text)


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
    "balance_payments_table",
    "inflation_index_table",
}

_BAR_CHART_KINDS = {
    "bar_chart",
    "market_share_bar_chart",
    "gdp_growth_bar_chart",
}

_LINE_CHART_KINDS = {
    "line_graph",
    "index_number_chart",
    "household_savings_line_chart",
    "investment_line_chart",
    "current_account_line_chart",
    "terms_of_trade_index_chart",
}


def _draw_economics_graph(pdf: canvas.Canvas, x: float, y: float, kind: str) -> float:
    bottom = y - 150
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.7)
    pdf.line(x, bottom, x, y - 8)
    pdf.line(x, bottom, x + 270, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label = _axis_label(kind)
    pdf.drawString(x - 46, y - 20, y_label)
    pdf.drawRightString(x + 275, bottom - 12, _x_axis_label(kind))
    if kind == "cost_revenue_graph":
        geometry = _cost_revenue_geometry(x, y)
        pdf.line(*geometry["ar"][0], *geometry["ar"][1])
        pdf.drawString(geometry["ar"][1][0] + 5, geometry["ar"][1][1] - 3, "AR")
        pdf.line(*geometry["mr"][0], *geometry["mr"][1])
        pdf.drawString(geometry["mr"][1][0] + 5, geometry["mr"][1][1] - 3, "MR")
        pdf.bezier(x + 12, bottom + 32, x + 62, bottom + 12, x + 120, bottom + 55, x + 172, y - 55)
        pdf.drawString(x + 177, y - 56, "MC")
        pdf.bezier(x + 12, bottom + 54, x + 88, bottom + 32, x + 168, bottom + 66, x + 222, y - 76)
        pdf.drawString(x + 226, y - 78, "AC")
    elif kind in {"trade_cycle", "multiplier_context"}:
        pdf.bezier(x + 10, bottom + 40, x + 65, y - 16, x + 140, bottom + 25, x + 250, y - 42)
        pdf.drawString(x + 180, y - 36, "Trend")
    elif kind == "production_possibility_frontier":
        pdf.bezier(x + 18, y - 20, x + 132, y - 30, x + 225, bottom + 72, x + 248, bottom + 18)
        pdf.drawString(x + 210, bottom + 74, "PPF")
    elif kind in {"phillips_curve", "lorenz_curve", "laffer_curve", "poverty_trap_diagram"}:
        pdf.bezier(x + 15, bottom + 18, x + 72, bottom + 90, x + 166, y - 50, x + 245, y - 34)
        pdf.drawString(x + 210, y - 34, _curve_label(kind))
    elif kind in {"monopsony_diagram", "labour_market_diagram"}:
        pdf.line(x + 20, bottom + 112, x + 230, bottom + 20)
        pdf.drawString(x + 235, bottom + 18, "MRP")
        pdf.line(x + 25, bottom + 20, x + 230, bottom + 112)
        pdf.drawString(x + 235, bottom + 110, "S")
        if kind == "monopsony_diagram":
            pdf.line(x + 44, bottom + 20, x + 252, bottom + 122)
            pdf.drawString(x + 254, bottom + 120, "MC")
    elif kind in {"tax_subsidy_diagram", "minimum_price_diagram", "maximum_price_diagram", "tariff_diagram"}:
        _draw_demand_supply(pdf, x, bottom)
        pdf.setDash(2, 2)
        pdf.line(x + 38, bottom + 76, x + 235, bottom + 76)
        pdf.setDash()
        pdf.drawString(x + 238, bottom + 73, "P")
    elif kind == "externality_diagram":
        _draw_demand_supply(pdf, x, bottom)
        pdf.line(x + 30, bottom + 36, x + 230, bottom + 128)
        pdf.drawString(x + 235, bottom + 126, "MSC")
    elif kind in {"perfect_competition_diagram", "monopoly_diagram"}:
        pdf.line(x + 20, bottom + 92, x + 238, bottom + 92)
        pdf.drawString(x + 242, bottom + 89, "AR=MR")
        pdf.bezier(x + 16, bottom + 30, x + 78, bottom + 16, x + 132, bottom + 72, x + 190, y - 48)
        pdf.drawString(x + 195, y - 49, "MC")
    elif kind in {"macro_chart", "ad_as_diagram", "keynesian_as_diagram"}:
        pdf.line(x + 20, bottom + 112, x + 230, bottom + 20)
        pdf.drawString(x + 235, bottom + 18, "AD")
        pdf.line(x + 25, bottom + 20, x + 230, bottom + 112)
        pdf.drawString(x + 235, bottom + 110, "SRAS")
        if kind == "keynesian_as_diagram":
            pdf.line(x + 38, bottom + 32, x + 170, bottom + 32)
            pdf.line(x + 170, bottom + 32, x + 170, y - 16)
            pdf.drawString(x + 176, y - 20, "LRAS")
    else:
        _draw_demand_supply(pdf, x, bottom)
    return bottom - 8


def _cost_revenue_geometry(x: float, y: float) -> dict[str, object]:
    bottom = y - 150
    return {
        "axis": {"left": x, "right": x + 270, "bottom": bottom, "top": y - 8},
        "ar": ((x + 16, y - 26), (x + 238, bottom + 18)),
        "mr": ((x + 16, y - 26), (x + 146, bottom + 16)),
    }


def _axis_label(kind: str) -> str:
    if kind == "cost_revenue_graph":
        return "Costs/revenues"
    if kind in {"macro_chart", "ad_as_diagram", "keynesian_as_diagram"}:
        return "Price level"
    if kind in {"phillips_curve"}:
        return "Inflation"
    if kind in {"lorenz_curve"}:
        return "% income"
    if kind in {"production_possibility_frontier"}:
        return "Good A"
    if kind in {"labour_market_diagram", "monopsony_diagram"}:
        return "Wage rate"
    return "Price"


def _x_axis_label(kind: str) -> str:
    if kind in {"macro_chart", "ad_as_diagram", "keynesian_as_diagram"}:
        return "Real output"
    if kind == "phillips_curve":
        return "Unemployment"
    if kind == "lorenz_curve":
        return "% population"
    if kind == "production_possibility_frontier":
        return "Good B"
    if kind in {"labour_market_diagram", "monopsony_diagram"}:
        return "Labour"
    return "Quantity"


def _curve_label(kind: str) -> str:
    return {
        "phillips_curve": "PC",
        "lorenz_curve": "Lorenz curve",
        "laffer_curve": "Laffer curve",
        "poverty_trap_diagram": "Trap",
    }.get(kind, "Curve")


def _draw_demand_supply(pdf: canvas.Canvas, x: float, bottom: float) -> None:
    pdf.line(x + 20, bottom + 112, x + 230, bottom + 20)
    pdf.drawString(x + 235, bottom + 18, "D")
    pdf.line(x + 25, bottom + 20, x + 230, bottom + 112)
    pdf.drawString(x + 235, bottom + 110, "S")


def _draw_data_table(pdf: canvas.Canvas, x: float, y: float, kind: str = "data_table") -> float:
    rows = _table_rows(kind)
    col_count = max(len(row) for row in rows)
    col_width = 124 if kind == "data_table" else 92 if col_count >= 4 else 100
    w = col_width * col_count
    row_h = 21
    h = row_h * len(rows) + 2
    pdf.rect(x, y - h, w, h, stroke=1, fill=0)
    for i in range(1, len(rows)):
        pdf.line(x, y - i * row_h, x + w, y - i * row_h)
    for i in range(1, col_count):
        pdf.line(x + i * col_width, y, x + i * col_width, y - h)
    pdf.setFont(FONT_REGULAR, 8.5 if kind == "data_table" else 9 if col_count >= 4 else 11)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            pdf.drawString(x + c * col_width + 6, y - 14 - r * row_h, text)
    return y - h - 8


def _table_rows(kind: str) -> list[list[str]]:
    if kind == "ped_data_table":
        return [["Age group", "PED"], ["16-18", "-0.7"], ["Adult", "-0.4"]]
    if kind == "pes_data_table":
        return [["Region", "PES"], ["Urban", "+0.5"], ["Rural", "+1.8"]]
    if kind == "development_data_table":
        return [
            ["Country", "HDI", "GNI per head", "GDP per capita"],
            ["Morocco", "0.683", "7 303", "3 795"],
            ["Pakistan", "0.544", "4 624", "1 473"],
        ]
    if kind == "balance_payments_table":
        return [["Year", "Exports", "Imports"], ["2021", "612", "645"], ["2022", "701", "748"], ["2023", "742", "789"]]
    if kind == "inflation_index_table":
        return [["Year", "CPI index", "Inflation"], ["2021", "100.0", "2.5%"], ["2022", "109.1", "9.1%"], ["2023", "116.0", "6.3%"]]
    if kind == "concentration_ratio_table":
        return [["Firm", "Market share", "Rank"], ["A", "26.6%", "1"], ["B", "19.5%", "2"], ["C", "12.7%", "3"]]
    if kind == "elasticity_data_table":
        return [["Good", "PED", "YED"], ["Bus travel", "-0.6", "+0.2"], ["Cinema", "-1.4", "+1.8"], ["Fuel", "-0.2", "+0.1"]]
    return [
        ["Year", "Quantity demanded index", "Average price index"],
        ["2021", "74.2", "68.5"],
        ["2022", "81.6", "71.4"],
        ["2023", "88.0", "75.2"],
    ]


def _draw_bar_chart(pdf: canvas.Canvas, x: float, y: float, kind: str = "bar_chart") -> float:
    bottom = y - 120
    max_scale = 30 if kind == "market_share_bar_chart" else max(_bar_chart_data(kind)[2])
    if kind == "market_share_bar_chart":
        pdf.setStrokeColor(colors.HexColor("#d2d2d2"))
        pdf.setLineWidth(0.35)
        for tick in range(5, 31, 5):
            tick_y = bottom + 92 * tick / max_scale
            pdf.line(x, tick_y, x + 250, tick_y)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(1)
    pdf.line(x, bottom, x, y - 10)
    pdf.line(x, bottom, x + 250, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label, x_label, values = _bar_chart_data(kind)
    pdf.drawString(x - 28, y - 18, y_label)
    pdf.drawRightString(x + 255, bottom - 12, x_label)
    for i, value in enumerate(values):
        h = 92 * value / max_scale
        pdf.setFillColor(colors.HexColor("#bdbdbd") if kind == "market_share_bar_chart" else colors.white)
        pdf.rect(x + 30 + i * 42, bottom, 22, h, stroke=1, fill=kind == "market_share_bar_chart")
        pdf.setFillColor(colors.black)
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawCentredString(x + 41 + i * 42, bottom - 11, _bar_label(kind, i))
        if kind == "market_share_bar_chart":
            pdf.drawCentredString(x + 41 + i * 42, bottom + h + 4, f"{value:.1f}%")
    return bottom - 10


def _bar_chart_data(kind: str) -> tuple[str, str, list[float]]:
    if kind == "market_share_bar_chart":
        return "%", "Firms", [26.6, 19.5, 12.7, 11.7, 10.9]
    if kind == "gdp_growth_bar_chart":
        return "%", "Quarter", [0.4, 0.1, -0.1, 0.1, 0.1]
    return "%", "Firms", [52, 80, 38, 96]


def _bar_label(kind: str, index: int) -> str:
    if kind == "market_share_bar_chart":
        return ["Lloyds", "NatWest", "Barclays", "HSBC", "Santander"][index]
    return chr(65 + index)


def _draw_line_graph(pdf: canvas.Canvas, x: float, y: float, kind: str = "line_graph") -> float:
    bottom = y - 120
    pdf.line(x, bottom, x, y - 10)
    pdf.line(x, bottom, x + 250, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label, x_label, values = _line_chart_data(kind)
    pdf.drawString(x - 28, y - 18, y_label)
    pdf.drawRightString(x + 255, bottom - 12, x_label)
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1
    step = 210 / max(1, len(values) - 1)
    points = [(x + 24 + i * step, bottom + 18 + (value - minimum) * 84 / span) for i, value in enumerate(values)]
    for start, end in zip(points, points[1:]):
        pdf.line(*start, *end)
    for px, py in points:
        pdf.circle(px, py, 2.2, stroke=1, fill=1)
    return bottom - 10


def _line_chart_data(kind: str) -> tuple[str, str, list[float]]:
    if kind == "household_savings_line_chart":
        return "%", "Quarter", [8.8, 9.6, 7.3, 4.8, 5.1, 22.8, 13.4, 16.9, 10.1]
    if kind == "investment_line_chart":
        return "% GDP", "Quarter", [22.7, 23.3, 21.6, 24.2, 23.1, 21.6, 20.8, 22.4, 22.7, 22.8, 22.5]
    if kind == "current_account_line_chart":
        return "% GDP", "Year", [-3.8, -4.6, -4.9, -4.8, -5.2, -3.8, -4.2, -3.5, -3.7, -1.1, -4.3]
    if kind == "terms_of_trade_index_chart":
        return "Index", "Year", [82, 79, 80, 81, 83, 92, 92, 88, 85, 86, 91]
    return "Index", "Year", [74.2, 81.6, 78.5, 88.0]


def _draw_payoff_matrix(pdf: canvas.Canvas, x: float, y: float) -> float:
    w = 260
    h = 105
    pdf.rect(x, y - h, w, h, stroke=1, fill=0)
    pdf.line(x + 86, y, x + 86, y - h)
    pdf.line(x + 173, y, x + 173, y - h)
    pdf.line(x, y - 35, x + w, y - 35)
    pdf.line(x, y - 70, x + w, y - 70)
    pdf.setFont(FONT_REGULAR, 10)
    entries = [
        ("Firm B", x + 106, y - 15),
        ("High price", x + 95, y - 52),
        ("Low price", x + 184, y - 52),
        ("Firm A", x + 18, y - 52),
        ("High price", x + 10, y - 87),
        ("Low price", x + 96, y - 87),
        ("8, 8", x + 112, y - 87),
        ("4, 10", x + 196, y - 87),
    ]
    for text, tx, ty in entries:
        pdf.drawString(tx, ty, text)
    return y - h - 12


def _draw_context_box(pdf: canvas.Canvas, x: float, y: float, context_text: str = "") -> float:
    pdf.setFont(FONT_REGULAR, 11)
    text = context_text or "A short item of economic context is provided for use with this question."
    lines = _wrap(text, 74)[:4]
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

    _pad_pdf_pages(pdf, 4 if blueprint.paper_id in {"paper_1", "paper_2"} else 6)
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
    width, height = A4
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
    pdf.drawString(panel_x + 14, y, "Pearson Edexcel Level 3 GCE")
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
    y -= 45
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 40, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(panel_x + 22, y + 24, "Source Booklet")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 9, "Do not return this Booklet with the question paper.")
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawRightString(width - 64, 75, "Turn over  >")
    _draw_cover_pearson_mark(pdf, width - 88, 44)
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawString(58, 43, "P00000A")
    pdf.drawString(58, 31, "Practice paper generated for revision use.")
    _draw_fake_barcode(pdf, width / 2 - 80, 32, "P  0  0  0  0  0  A")


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
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    width, height = A4
    margin = 57
    blue = colors.HexColor("#006f95")
    pdf.setFillColor(blue)
    pdf.circle(margin + 100, height - 152, 22, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 28)
    pdf.drawCentredString(margin + 100, height - 162, "P")
    pdf.setFillColor(colors.black)
    pdf.setFont(FONT_REGULAR, 28)
    pdf.drawString(margin + 52, height - 200, "Pearson")
    pdf.setFillColor(blue)
    pdf.setFont(FONT_REGULAR, 31)
    pdf.drawString(margin, height - 324, "Mark Scheme (Results)")
    series_year = economics_exam_schedule(blueprint.paper_id).date.year
    pdf.drawString(margin, height - 415, f"Summer {series_year}")
    pdf.setFont(FONT_REGULAR, 23)
    pdf.drawString(margin, height - 500, "Pearson Edexcel GCE A Level")
    pdf.drawString(margin, height - 540, f"In Economics A ({blueprint.paper_code.split('/')[0]})")
    pdf.drawString(margin, height - 580, f"Paper {blueprint.paper_id[-1].zfill(2)} {blueprint.title}")
    pdf.setFillColor(colors.black)
    pdf.showPage()

    _draw_mark_scheme_qualification_page(pdf, blueprint, margin, height)
    pdf.showPage()

    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(margin, height - 70, "General Marking Guidance")
    pdf.setFont(FONT_REGULAR, 10)
    y = height - 105
    guidance = [
        "All candidates must receive the same treatment.",
        "Mark schemes should be applied positively.",
        "Examiners should mark according to the mark scheme.",
        "All the marks on the mark scheme are designed to be awarded.",
        "Where some judgement is required, levels-based descriptors should be used.",
        "Crossed out work should be marked unless replaced with an alternative response.",
    ]
    for item in guidance:
        for idx, line in enumerate(_wrap(item, 78)):
            pdf.drawString(margin + (0 if idx else 12), y, ("• " if idx == 0 else "  ") + line)
            y -= 15
    pdf.showPage()

    y = height - 58
    for row in _mark_scheme_rows(blueprint, syllabus):
        row_height = _ms_row_height(row["answer_lines"])
        if y - row_height < 54:
            pdf.showPage()
            y = height - 58
        y = _draw_ms_row(pdf, y, row["number"], row["answer_lines"], row["mark"])
        y -= 24
    _pad_mark_scheme_pages(pdf, 26)
    pdf.save()


def _pad_mark_scheme_pages(pdf: canvas.Canvas, target_pages: int) -> None:
    while pdf.getPageNumber() < target_pages:
        pdf.showPage()


def _draw_mark_scheme_qualification_page(pdf: canvas.Canvas, blueprint: PaperBlueprint, margin: float, height: float) -> None:
    y = height - 70
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(margin, y, "Edexcel and BTEC Qualifications")
    y -= 28
    pdf.setFont(FONT_REGULAR, 10)
    paragraphs = [
        (
            "Edexcel and BTEC qualifications are awarded by Pearson. This unofficial practice "
            "mark scheme is generated for private revision and is not an official Pearson document."
        ),
        (
            "For official qualification information, students should use Pearson's published "
            "specification, question papers and examiner materials."
        ),
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 82):
            pdf.drawString(margin, y, line)
            y -= 13
        y -= 12

    y -= 28
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(margin, y, "Pearson: helping people progress, everywhere")
    y -= 24
    pdf.setFont(FONT_REGULAR, 10)
    for line in _wrap(
        "This generated document follows the style of public mark schemes so that students can practise applying assessment objectives and levels-based descriptors.",
        82,
    ):
        pdf.drawString(margin, y, line)
        y -= 13

    y = 132
    front_matter = [
        f"Summer {economics_exam_schedule(blueprint.paper_id).date.year}",
        "Question Paper Log Number P00000A",
        f"Publications Code {blueprint.paper_code.replace('/', '_')}_PRACTICE_MS",
        f"All generated material in this practice publication is for revision use.",
        f"(c) Pearson Education Ltd style referenced for private study, {economics_exam_schedule(blueprint.paper_id).date.year}",
    ]
    for item in front_matter:
        pdf.drawString(margin, y, item)
        y -= 14


def _draw_ms_table_header(pdf: canvas.Canvas, y: float) -> None:
    _draw_ms_header_box(pdf, 54, y - 22, 488, 22)


def _mark_scheme_rows(blueprint: PaperBlueprint, syllabus: Syllabus) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for question in blueprint.questions:
        topic = syllabus.get_topic(question.topic_id)
        if question.parts:
            for part in question.parts:
                rows.append(
                    {
                        "number": f"{question.number}({part.label})",
                        "mark": f"({part.marks})",
                        "answer_lines": _part_mark_scheme_lines(question, part, topic),
                    }
                )
        else:
            rows.append(
                {
                    "number": question.number,
                    "mark": f"({question.marks})",
                    "answer_lines": _question_mark_scheme_lines(question, topic),
                }
            )
    return rows


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
        return [
            *_specific_mark_scheme_context(question, question.prompt, topic),
            question.mark_breakdown or "Knowledge 1, Application 2, Analysis 2",
            "",
            "Knowledge/Understanding:",
            f"Credit accurate definitions and concepts for {topic.title.lower()}.",
            "",
            "Application:",
            "Credit relevant use of the source material, data or context.",
            "",
            "Analysis:",
            "Credit clear logical chains of reasoning.",
            *_scheme_bullets(question.mark_scheme, topic),
        ]
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
    left = 72
    number_w = 70
    mark_w = 64
    right = 514
    answer_x = left + number_w + 6
    mark_x = right - mark_w
    row_height = _ms_row_height(answer_lines)
    bottom = y - row_height
    _draw_ms_header_box(pdf, left, y - 22, right - left, 22)
    pdf.rect(left, bottom, right - left, row_height - 22, stroke=1, fill=0)
    pdf.line(left + number_w, bottom, left + number_w, y)
    pdf.line(mark_x, bottom, mark_x, y)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(left + 6, y - 38, number)
    pdf.setFont(FONT_REGULAR, 10)
    cursor = y - 38
    for line in answer_lines:
        if not line:
            cursor -= 10
            continue
        font = FONT_BOLD if _ms_bold_line(line) else FONT_REGULAR
        pdf.setFont(font, 10)
        for wrapped in _wrap(line, MS_ANSWER_WRAP_CHARS):
            if _ms_centered_line(wrapped):
                pdf.drawCentredString((answer_x + mark_x) / 2, cursor, wrapped)
            else:
                pdf.drawString(answer_x, cursor, wrapped)
            cursor -= 12
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(mark_x + 10, bottom + 24, mark)
    return bottom


def _draw_ms_header_box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    pdf.setFillColor(colors.HexColor("#e6e6e6"))
    pdf.rect(x, y, w, h, stroke=1, fill=1)
    pdf.setFillColor(colors.black)
    pdf.line(x + 70, y, x + 70, y + h)
    pdf.line(x + w - 64, y, x + w - 64, y + h)
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(x + 6, y + 11, "Question")
    pdf.drawString(x + 6, y + 2, "Number")
    pdf.drawString(x + 76, y + 7, "Answer")
    pdf.drawString(x + w - 54, y + 7, "Mark")


def _ms_row_height(answer_lines: list[str]) -> int:
    wrapped_lines = 0
    for line in answer_lines:
        wrapped_lines += max(1, len(_wrap(line, MS_ANSWER_WRAP_CHARS))) if line else 1
    return max(112, 36 + wrapped_lines * 12)


def _ms_centered_line(line: str) -> bool:
    return bool(re.match(r"^Knowledge \d, Application \d", line))


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
