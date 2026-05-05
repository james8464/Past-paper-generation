from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from pastpapergen.models import PaperBlueprint, Syllabus
from pastpapergen.notes import note_points_for_topic

ANSWER_LINE_GAP_PT = 28
BODY_FONT_SIZE_PT = 12
BODY_LEADING_PT = 14
FONT_REGULAR = "Arial"
FONT_BOLD = "Arial-Bold"
MS_ANSWER_WRAP_CHARS = 58
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
    fonts = [
        (FONT_REGULAR, Path("/System/Library/Fonts/Supplemental/Arial.ttf"), 0),
        (FONT_BOLD, Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"), 0),
    ]
    if not fonts[0][1].exists():
        fonts = [
            (FONT_REGULAR, Path("/System/Library/Fonts/Helvetica.ttc"), 0),
            (FONT_BOLD, Path("/System/Library/Fonts/Helvetica.ttc"), 1),
        ]
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

    panel_x = 114
    panel_y = 452
    panel_w = 406
    panel_h = 330
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
    y -= 40
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 28, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(panel_x + 22, y + 8, "Mock Examination")

    y -= 36
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 14, y + 11, f"Morning (Time: {blueprint.duration_minutes // 60} hours)")
    pdf.rect(panel_x + 195, y, 58, 30, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 200, y + 18, "Paper")
    pdf.drawString(panel_x + 200, y + 7, "reference")
    pdf.setFillColor(dark)
    pdf.roundRect(panel_x + 253, y, 121, 30, 7, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 23)
    pdf.drawCentredString(panel_x + 313, y + 8, blueprint.paper_code)
    pdf.setFillColor(colors.black)

    y -= 90
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 88, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(panel_x + 22, y + 63, "Economics A")
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(panel_x + 22, y + 43, "Advanced")
    paper_number = blueprint.paper_id[-1]
    pdf.drawString(panel_x + 22, y + 26, f"PAPER {paper_number}: {blueprint.title}")

    y -= 54
    pdf.roundRect(panel_x + 14, y, panel_w - 88, 45, 7, stroke=1, fill=0)
    pdf.roundRect(panel_x + panel_w - 70, y, 56, 45, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 29, "You must have:")
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 22, y + 13, "Source Booklet (enclosed)")
    pdf.drawCentredString(panel_x + panel_w - 42, y + 24, "Total Marks")

    text_x = 114
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
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawString(58, 43, "P00000A")
    pdf.drawString(58, 31, "Practice paper generated for revision use.")
    _draw_fake_barcode(pdf, width / 2 - 105, 32, "P  0  0  0  0  0  A  0  1")


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
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(x, y, heading)
    pdf.setFont(FONT_REGULAR, 9)
    y -= 16
    for line in lines:
        wrapped = _wrap(line, 82)
        for idx, part in enumerate(wrapped):
            prefix = "• " if idx == 0 else "  "
            pdf.drawString(x, y, prefix + part)
            y -= 12


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
    margin = 72
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
                y = _draw_section_b_prompt_page(pdf, questions, y)
                _draw_question_footer(pdf, blueprint, page_number)
                pdf.showPage()
                page_number += 1
                y = _prepare_answer_page(pdf, blueprint, page_number)
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
    return {5: 1, 8: 2, 10: 2, 12: 3, 15: 4}.get(question.marks, 0)


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


def _draw_continuation_lines(pdf: canvas.Canvas, x: float, y: float) -> float:
    return _draw_answer_lines_until(pdf, x, y, 520)


def _prepare_answer_page(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int) -> float:
    width, height = A4
    _draw_crop_marks(pdf)
    _draw_do_not_write_rail(pdf)
    pdf.setStrokeColor(colors.HexColor("#9d9d9d"))
    pdf.setLineWidth(1.6)
    pdf.roundRect(58, 65, 480, 715, 8, stroke=1, fill=0)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    return height - 90


def _draw_do_not_write_rail(pdf: canvas.Canvas) -> None:
    width, height = A4
    rail_x = width - 52
    pdf.setFillColor(colors.HexColor("#f0f0f0"))
    pdf.rect(rail_x, 66, 21, 705, stroke=0, fill=1)
    pdf.rect(rail_x + 31, 66, 21, 705, stroke=0, fill=1)
    _draw_hatched_rail(pdf, rail_x, 66, 21, 705)
    _draw_hatched_rail(pdf, rail_x + 31, 66, 21, 705)
    pdf.setFillColor(colors.HexColor("#777777"))
    pdf.setFont(FONT_BOLD, 8)
    for x in (rail_x + 14, rail_x + 45):
        for y in (135, 330, 525):
            pdf.saveState()
            pdf.translate(x, y)
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
    pdf.drawString(72, 42, str(page_number))
    _draw_fake_barcode(pdf, width / 2 - 105, 26, f"P  0  0  0  0  0  A  0  {page_number:02d}")
    pdf.setFont(FONT_REGULAR, 7)
    pdf.drawRightString(width - 78, 42, "■□■□")


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
            "Read Figure 1 and the following extracts (A to C)",
            "in the Source Booklet before answering Question 6.",
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
    if first_part and first_part.command_word == "draw" and stimulus_kind == "bar_chart":
        stimulus_kind = "context_extract"
    if stimulus_kind:
        y = _draw_stimulus(pdf, stimulus_kind, x + 110, y, question.source_text)
        y -= 28

    if first_part and first_part.command_word == "draw" and second_part and second_part.marks == 1:
        y = _draw_draw_part_with_axes(pdf, first_part, x, y)
        y = _draw_mcq_part(pdf, second_part, x, y)
        _draw_total_for_question(pdf, question.number, question.marks, x, y)
        if question.number == "5":
            _draw_section_a_total(pdf, x, y - 34)
        _draw_question_footer(pdf, blueprint, page_number)
        pdf.showPage()
        page_number += 1
        if question.number == "5":
            _draw_section_transition_blank(pdf, blueprint, page_number, "QUESTION 6 BEGINS ON THE NEXT PAGE")
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
        _draw_section_transition_blank(pdf, blueprint, page_number, "QUESTION 6 BEGINS ON THE NEXT PAGE")
        pdf.showPage()
        page_number += 1
    return page_number, _prepare_answer_page(pdf, blueprint, page_number)


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
    return _draw_blank_answer_axes(pdf, x + 34, y, width - x - 130, 260) - 22


def _draw_blank_answer_axes(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> float:
    bottom = y - h
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.7)
    pdf.line(x, bottom, x, y)
    pdf.line(x, bottom, x + w, bottom)
    pdf.setLineWidth(1)
    return bottom


def _draw_part_prompt(pdf: canvas.Canvas, part, x: float, y: float) -> float:
    pdf.setFont(FONT_REGULAR, BODY_FONT_SIZE_PT)
    lines = _wrap(f"({part.label}) {part.prompt}", 66)
    for line in lines:
        pdf.drawString(x + 18, y, line)
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


def _mcq_choices(part) -> tuple[str, list[tuple[str, str]]]:
    if part.options:
        return part.prompt, [(option.label, option.text) for option in part.options]
    return _split_mcq_prompt(part.prompt)


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


def _draw_section_transition_blank(pdf: canvas.Canvas, blueprint: PaperBlueprint, page_number: int, message: str) -> None:
    width, height = A4
    _prepare_answer_page(pdf, blueprint, page_number)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawCentredString(width / 2, height / 2 + 22, message)
    pdf.setFont(FONT_BOLD, BODY_FONT_SIZE_PT)
    pdf.drawCentredString(width / 2, height / 2, "BLANK PAGE")
    _draw_question_footer(pdf, blueprint, page_number)


def _draw_answer_lines(pdf: canvas.Canvas, x: float, y: float, right_x: float, line_count: int) -> float:
    _set_answer_line_style(pdf)
    for _ in range(line_count):
        if y < 90:
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
    pdf.setStrokeColor(colors.HexColor("#333333"))
    pdf.setLineWidth(0.35)
    pdf.setDash(0.45, 1.65)


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
    if kind in {"cost_revenue_graph", "market_diagram", "macro_chart", "trade_cycle"}:
        return _draw_economics_graph(pdf, x, y, kind)
    if kind == "data_table":
        return _draw_data_table(pdf, x - 35, y)
    if kind == "bar_chart":
        return _draw_bar_chart(pdf, x - 10, y)
    return _draw_context_box(pdf, x - 70, y, context_text)


def _draw_economics_graph(pdf: canvas.Canvas, x: float, y: float, kind: str) -> float:
    bottom = y - 150
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.7)
    pdf.line(x, bottom, x, y - 8)
    pdf.line(x, bottom, x + 270, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    y_label = "Costs/revenues" if kind == "cost_revenue_graph" else "Price"
    pdf.drawString(x - 46, y - 20, y_label)
    pdf.drawRightString(x + 275, bottom - 12, "Quantity")
    if kind == "cost_revenue_graph":
        pdf.line(x, y - 24, x + 240, bottom + 10)
        pdf.drawString(x + 245, bottom + 6, "AR")
        pdf.line(x + 10, y - 24, x + 150, bottom - 18)
        pdf.drawString(x + 154, bottom - 24, "MR")
        pdf.bezier(x + 8, bottom + 30, x + 60, bottom + 10, x + 120, bottom + 55, x + 170, y - 55)
        pdf.drawString(x + 175, y - 56, "MC")
        pdf.bezier(x + 8, bottom + 52, x + 85, bottom + 30, x + 165, bottom + 65, x + 220, y - 76)
        pdf.drawString(x + 224, y - 78, "AC")
    elif kind == "trade_cycle":
        pdf.bezier(x + 10, bottom + 40, x + 65, y - 16, x + 140, bottom + 25, x + 250, y - 42)
        pdf.drawString(x + 180, y - 36, "Trend")
    else:
        pdf.line(x + 20, bottom + 112, x + 230, bottom + 20)
        pdf.drawString(x + 235, bottom + 18, "D")
        pdf.line(x + 25, bottom + 20, x + 230, bottom + 112)
        pdf.drawString(x + 235, bottom + 110, "S")
    return bottom - 8


def _draw_data_table(pdf: canvas.Canvas, x: float, y: float) -> float:
    w = 300
    h = 86
    pdf.rect(x, y - h, w, h, stroke=1, fill=0)
    for i in range(1, 4):
        pdf.line(x, y - i * 21, x + w, y - i * 21)
    for i in range(1, 3):
        pdf.line(x + i * 100, y, x + i * 100, y - h)
    pdf.setFont(FONT_REGULAR, 11)
    rows = [["Year", "Value A", "Value B"], ["2021", "74.2", "68.5"], ["2022", "81.6", "71.4"], ["2023", "88.0", "75.2"]]
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            pdf.drawString(x + c * 100 + 8, y - 14 - r * 21, text)
    return y - h - 8


def _draw_bar_chart(pdf: canvas.Canvas, x: float, y: float) -> float:
    bottom = y - 120
    pdf.line(x, bottom, x, y - 10)
    pdf.line(x, bottom, x + 250, bottom)
    pdf.setFont(FONT_REGULAR, 11)
    pdf.drawString(x - 28, y - 18, "%")
    pdf.drawRightString(x + 255, bottom - 12, "Firms")
    for i, h in enumerate([52, 80, 38, 96]):
        pdf.rect(x + 35 + i * 48, bottom, 22, h, stroke=1, fill=0)
    return bottom - 10


def _draw_context_box(pdf: canvas.Canvas, x: float, y: float, context_text: str = "") -> float:
    pdf.setFont(FONT_REGULAR, 11)
    text = context_text or "A short item of economic context is provided for use with this question."
    lines = _wrap(text, 74)[:4]
    for idx, line in enumerate(lines):
        pdf.drawCentredString(x + 170, y - idx * 12, line)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawCentredString(x + 170, y - len(lines) * 12 - 4, "Source: generated revision material based on the specification")
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
    width, height = A4
    margin = 58
    _draw_crop_marks(pdf)
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawCentredString(width / 2, height - 40, "Do not return this Booklet with the question paper.")
    y = height - 86

    for section in _source_sections(blueprint.paper_id):
        if y < 220:
            pdf.showPage()
            y = height - 58
        pdf.setFont(FONT_BOLD, 11)
        pdf.drawCentredString(width / 2, y, f"Sources for use with SECTION {section}")
        y -= 18
        pdf.setFont(FONT_REGULAR, 9)
        prompt = _source_reading_prompt(blueprint.paper_id, section)
        for line in _wrap(prompt, 92):
            pdf.drawCentredString(width / 2, y, line)
            y -= 12
        y -= 16

        section_questions = [question for question in blueprint.questions if question.section == section]
        first_question = section_questions[0].number.split("(")[0]
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(margin, y, f"Question {first_question}")
        y -= 16
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(margin, y, _source_title(section_questions, syllabus))
        y -= 24

        figure_question = section_questions[0]
        topic = syllabus.get_topic(figure_question.topic_id)
        pdf.setFont(FONT_BOLD, 9)
        pdf.drawString(margin, y, f"Figure 1: {topic.title}")
        y -= 14
        y = _draw_source_graph(pdf, margin, y, figure_question.stimulus_kind or "bar_chart")
        y -= 8

        for extract_index, question in enumerate(_extract_source_questions(section_questions)):
            topic = syllabus.get_topic(question.topic_id)
            label = chr(65 + extract_index)
            heading = f"Extract {label}"
            pdf.setFont(FONT_BOLD, 9)
            pdf.drawString(margin, y, heading)
            y -= 14
            pdf.setFont(FONT_REGULAR, 9)
            source_text = question.source_text or (
                f"This source concerns {topic.title.lower()}. It may include evidence on "
                f"{', '.join(topic.points[:3])}."
            )
            for line in _wrap(source_text, 92):
                pdf.drawString(margin, y, line)
                y -= 12
                if y < 70:
                    pdf.showPage()
                    y = height - 58
            pdf.setFont(FONT_REGULAR, 8)
            pdf.drawString(margin, y, "Source: generated revision material based on the specification")
            y -= 12
            y -= 12
        y -= 12

    _pad_pdf_pages(pdf, 4 if blueprint.paper_id in {"paper_1", "paper_2"} else 6)
    pdf.save()


def _pad_pdf_pages(pdf: canvas.Canvas, target_pages: int) -> None:
    while pdf.getPageNumber() < target_pages:
        pdf.showPage()
        _draw_crop_marks(pdf)


def _draw_source_graph(pdf: canvas.Canvas, x: float, y: float, kind: str) -> float:
    if kind == "data_table":
        return _draw_data_table(pdf, x + 55, y)
    if kind in {"cost_revenue_graph", "market_diagram", "macro_chart", "trade_cycle"}:
        return _draw_economics_graph(pdf, x + 82, y, kind)
    return _draw_bar_chart(pdf, x + 75, y)


def _extract_source_questions(section_questions: list) -> list:
    if len(section_questions) >= 4:
        return [section_questions[0], section_questions[2], section_questions[3]]
    return section_questions[:3]


def _draw_source_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    width, height = A4
    _draw_crop_marks(pdf)
    panel_x = 114
    panel_y = 528
    panel_w = 406
    panel_h = 255
    grey = colors.HexColor("#666666")
    dark = colors.HexColor("#4d494b")
    pdf.setStrokeColor(grey)
    pdf.setLineWidth(1.8)
    pdf.roundRect(panel_x, panel_y, panel_w, panel_h, 9, stroke=1, fill=0)
    y = panel_y + panel_h - 34
    pdf.setFont(FONT_BOLD, 17)
    pdf.drawString(panel_x + 14, y, "Pearson Edexcel Level 3 GCE")
    y -= 42
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 28, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(panel_x + 22, y + 8, "Mock Examination")
    y -= 36
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(panel_x + 14, y + 11, f"Morning (Time: {blueprint.duration_minutes // 60} hours)")
    pdf.rect(panel_x + 195, y, 58, 30, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 200, y + 18, "Paper")
    pdf.drawString(panel_x + 200, y + 7, "reference")
    pdf.setFillColor(dark)
    pdf.roundRect(panel_x + 253, y, 121, 30, 7, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 23)
    pdf.drawCentredString(panel_x + 313, y + 8, blueprint.paper_code)
    pdf.setFillColor(colors.black)
    y -= 90
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 88, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(panel_x + 22, y + 63, "Economics A")
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(panel_x + 22, y + 43, "Advanced")
    pdf.drawString(panel_x + 22, y + 26, f"PAPER {blueprint.paper_id[-1]}: {blueprint.title}")
    y -= 54
    pdf.roundRect(panel_x + 14, y, panel_w - 28, 45, 7, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(panel_x + 22, y + 27, "Source Booklet")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(panel_x + 22, y + 12, "Do not return this Booklet with the question paper.")
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawRightString(width - 64, 75, "Turn over  >")
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
        return "Read the following figure and extracts before answering Question 6."
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
    margin = 42
    blue = colors.HexColor("#006f95")
    pdf.setFillColor(blue)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(margin, height - 110, "Pearson Edexcel")
    pdf.setFont(FONT_REGULAR, 26)
    pdf.drawString(margin, height - 235, "Mark Scheme (Results)")
    pdf.drawString(margin, height - 300, "Practice Paper")
    pdf.setFont(FONT_REGULAR, 18)
    pdf.drawString(margin, height - 405, "Pearson Edexcel GCE A Level")
    pdf.drawString(margin, height - 430, f"In Economics A ({blueprint.paper_code.split('/')[0]})")
    pdf.drawString(margin, height - 455, f"Paper {blueprint.paper_id[-1].zfill(2)} {blueprint.title}")
    pdf.setFillColor(colors.black)
    pdf.showPage()

    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(margin, height - 70, "Qualification and publication information")
    pdf.setFont(FONT_REGULAR, 10)
    y = height - 105
    front_matter = [
        "This unofficial mark scheme is generated for revision practice.",
        f"Question Paper Log Number P00000A",
        f"Publications Code {blueprint.paper_code.replace('/', '_')}_PRACTICE_MS",
        "All material is generated for private revision and is not an official Pearson document.",
    ]
    for item in front_matter:
        pdf.drawString(margin, y, item)
        y -= 16
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
    width, height = A4
    while pdf.getPageNumber() < target_pages:
        pdf.showPage()
        pdf.setFont(FONT_BOLD, 9)
        pdf.drawCentredString(width / 2, height / 2, "BLANK PAGE")


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
            *_scheme_bullets(question.mark_scheme),
        ]
    return [
        *_specific_mark_scheme_context(question, question.prompt, topic),
        "Indicative content",
        *[f"- {item}" for item in (question.indicative_content or topic.points[:4])],
        "",
        "Level 1: displays isolated knowledge and limited understanding of economic terms.",
        "Level 2: applies knowledge to the context with partial chains of reasoning.",
        "Level 3: demonstrates clear application and developed analysis of relevant issues.",
        "Level 4: provides balanced analysis with supported evaluation and judgement.",
        "Level 5: shows sustained judgement, coherent chains of reasoning and developed evaluation.",
        "",
        question.mark_breakdown or "Knowledge, Application, Analysis and Evaluation",
        *_scheme_bullets(question.mark_scheme),
    ]


def _scheme_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items[:8]]


def _specific_mark_scheme_context(question, prompt: str, topic) -> list[str]:
    lines = [
        f"Question focus: {_sentence(prompt)}",
    ]
    if question.source_text:
        lines.extend(
            [
                "",
                "Relevant source evidence:",
                f"- {_sentence(question.source_text)}",
            ]
        )
    points = _specific_answer_points(question, topic)
    if points:
        lines.extend(["", "Valid points may include:", *[f"- {point}" for point in points]])
    lines.append("")
    return lines


def _specific_answer_points(question, topic) -> list[str]:
    seen: set[str] = set()
    points: list[str] = []
    note_points = note_points_for_topic(topic.id, title=topic.title, keywords=topic.points, limit=6)
    for item in [*question.indicative_content, *note_points, *question.mark_scheme, *topic.points]:
        cleaned = _sentence(item)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            points.append(cleaned)
        if len(points) == 5:
            break
    return points


def _sentence(text: str) -> str:
    cleaned = " ".join(str(text).split())
    return cleaned[:1].upper() + cleaned[1:].rstrip(".") + "." if cleaned else ""


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
