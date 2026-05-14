from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from cspapergen.exam_dates import formatted_paper2_exam_date, paper2_exam_date
from cspapergen.models import PaperBlueprint, Question, QuestionPart, Stimulus

FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
FONT_MONO = "AQACourier"
LEFT = 54
RIGHT = 534
TOP = 770
BOTTOM = 76
RAIL_X = 516
LINE_GAP = 20
AQA_A4 = (595.32, 841.92)
EXTRA_ANSWER_PAGES = 7


def _register_fonts() -> None:
    font_paths = {
        "AQAArial": Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        "AQAArial-Bold": Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        "AQACourier": Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
    }
    for font_name, font_path in font_paths.items():
        if font_name in pdfmetrics.getRegisteredFontNames():
            continue
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))


_register_fonts()


def render_question_paper(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _cover_page(pdf, blueprint)
    pdf.showPage()
    state = _QuestionRenderState(page=2, y=724)
    _draw_question_page_header(pdf, state.page)
    for index, question in enumerate(blueprint.questions):
        if index:
            state = _new_question_page(pdf, state)
        state = _render_question(pdf, question, state)
    state = _ensure_space(pdf, state, 90)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y - 20, "END OF QUESTIONS")
    state.y -= 80
    for _index in range(EXTRA_ANSWER_PAGES):
        _draw_extra_answer_page(pdf, state.page + 1)
        state.page += 1
    pdf.save()


def render_mark_scheme(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _mark_scheme_cover(pdf)
    pdf.showPage()
    _mark_scheme_intro(pdf, 2)
    pdf.showPage()
    _mark_scheme_levels(pdf, 3)
    pdf.showPage()
    _mark_scheme_annotations(pdf, 4)
    pdf.showPage()
    _mark_scheme_examiner_notes(pdf, 5)
    pdf.showPage()
    page = 6
    y = _mark_scheme_table_header(pdf, page)
    for question_index, question in enumerate(blueprint.questions):
        if question_index:
            pdf.showPage()
            page += 1
            y = _mark_scheme_table_header(pdf, page)
        for part in question.parts:
            needed = 56 + 15 * (len(part.marking.points) + len(part.marking.accept) + len(part.marking.reject) + len(part.marking.levels))
            if y - needed < 70:
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page)
            y = _render_mark_scheme_part(pdf, question, part, y)
    pdf.save()


class _QuestionRenderState:
    def __init__(self, page: int, y: float) -> None:
        self.page = page
        self.y = y


def _cover_page(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT, 11)
    pdf.drawString(55, 790, "Please write clearly in block capitals.")
    _candidate_fields(pdf)

    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(55, 535, "A-level")
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(55, 508, "COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 16)
    pdf.drawString(55, 483, "Paper 2")
    pdf.setFont(FONT, 10.5)
    pdf.drawString(55, 458, formatted_paper2_exam_date())
    pdf.drawString(225, 458, "Morning")
    pdf.setFont(FONT, 9.5)
    pdf.drawString(302, 458, "Time allowed: 2 hours 30 minutes")

    y = 430
    y = _cover_section(pdf, y, "Materials", ["For this paper you must have:", "\u2022 a calculator."])
    y = _cover_section(
        pdf,
        y - 8,
        "Instructions",
        [
            "\u2022 Use black ink or black ball-point pen.",
            "\u2022 Fill in the boxes at the top of this page.",
            "\u2022 Answer all questions.",
            "\u2022 You must answer the questions in the spaces provided. Do not write outside the box around each page or on blank pages.",
            "\u2022 If you need extra space for your answer(s), use the lined pages at the end of this book. Write the question number against your answer(s).",
            "\u2022 Do all rough work in this book. Cross through any work you do not want to be marked.",
        ],
    )
    y = _cover_section(pdf, y - 8, "Information", ["\u2022 The marks for questions are shown in brackets.", f"\u2022 The maximum mark for this paper is {blueprint.total_marks}."])
    _cover_section(
        pdf,
        y - 8,
        "Advice",
        [
            "\u2022 In some questions you are required to indicate your answer by completely shading a lozenge alongside the appropriate answer.",
            "\u2022 If you want to change your answer you must cross out your original answer.",
            "\u2022 If you wish to return to an answer previously crossed out, ring the answer you now wish to select.",
        ],
    )

    _examiner_table(pdf, len(blueprint.questions), y_top=420)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(55, 35, "*JUN267517201*")
    pdf.setFont(FONT, 9)
    pdf.drawRightString(535, 35, "7517/2")


def _candidate_fields(pdf: canvas.Canvas) -> None:
    y = 744
    pdf.setFont(FONT, 10)
    pdf.drawString(55, y, "Centre number")
    pdf.drawString(255, y, "Candidate number")
    _small_boxes(pdf, 55, y - 28, 5)
    _small_boxes(pdf, 255, y - 28, 4)
    for label in ["Surname", "Forename(s)", "Candidate signature"]:
        y -= 48
        pdf.drawString(55, y, label)
        pdf.line(170, y - 2, 500, y - 2)
    pdf.setFont(FONT, 8.5)
    pdf.drawString(255, y - 21, "I declare this is my own work.")


def _small_boxes(pdf: canvas.Canvas, x: float, y: float, count: int) -> None:
    for index in range(count):
        pdf.rect(x + index * 18, y, 16, 18, stroke=1, fill=0)


def _cover_section(pdf: canvas.Canvas, y: float, heading: str, lines: list[str]) -> float:
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(55, y, heading)
    y -= 16
    pdf.setFont(FONT, 9)
    for line in lines:
        for wrapped in _wrap(line, 76):
            pdf.drawString(55, y, wrapped)
            y -= 12
    return y


def _examiner_table(pdf: canvas.Canvas, count: int, y_top: float = 470) -> None:
    x = 420
    y = y_top
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x, y + 24, "For Examiner's Use")
    pdf.rect(x, y - 14 * (count + 2), 108, 14 * (count + 2), stroke=1, fill=0)
    pdf.line(x + 62, y - 14 * (count + 2), x + 62, y)
    pdf.line(x, y - 14, x + 108, y - 14)
    pdf.drawString(x + 8, y - 10, "Question")
    pdf.drawString(x + 72, y - 10, "Mark")
    pdf.setFont(FONT, 9)
    for index in range(1, count + 1):
        row_y = y - 14 * (index + 1)
        pdf.line(x, row_y, x + 108, row_y)
        pdf.drawCentredString(x + 31, row_y + 4, str(index))
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x + 8, y - 14 * (count + 2) + 4, "TOTAL")


def _draw_question_page_header(pdf: canvas.Canvas, page: int) -> None:
    pdf.setFont(FONT, 10)
    pdf.drawCentredString(297, 805, str(page))
    pdf.setFont(FONT, 8)
    pdf.drawCentredString(564, 780, "Do not write")
    pdf.drawCentredString(564, 769, "outside the")
    pdf.drawCentredString(564, 758, "box")
    pdf.setLineWidth(0.7)
    pdf.rect(39, 76, 500, 713, stroke=1, fill=0)
    pdf.line(39, 751, 539, 751)
    if page == 2:
        pdf.setFont(FONT, 11)
        pdf.drawCentredString(289, 768, "Answer all questions.")
    pdf.setFont(FONT, 8)
    _draw_footer_barcode(pdf, 52, 2, page)
    pdf.drawRightString(539, 28, "IB/G/Jun26/7517/2")


def _render_question(pdf: canvas.Canvas, question: Question, state: _QuestionRenderState) -> _QuestionRenderState:
    if state.y < 520:
        state = _new_question_page(pdf, state)
    state = _ensure_space(pdf, state, 80)
    _draw_question_ref(pdf, 52, state.y + 1, question.number)
    pdf.setFont(FONT, 10.5)
    for line in _wrap(question.stem, 78):
        pdf.drawString(118, state.y, line)
        state.y -= 14
    state.y -= 8
    if question.stimulus:
        state = _render_stimulus(pdf, question.stimulus, state)
        state.y -= 8
    single_part = len(question.parts) == 1
    for part in question.parts:
        state = _render_part(pdf, question, part, state, draw_reference=not single_part)
    state = _ensure_space(pdf, state, 34)
    _mark_total_box(pdf, question.total_marks, state.y)
    state.y -= 42
    return state


def _render_part(
    pdf: canvas.Canvas,
    question: Question,
    part: QuestionPart,
    state: _QuestionRenderState,
    *,
    draw_reference: bool = True,
) -> _QuestionRenderState:
    line_count = _answer_line_count(part)
    state = _ensure_space(pdf, state, 92)
    if draw_reference:
        _draw_question_ref(pdf, 52, state.y + 1, question.number, part.label)
    pdf.setFont(FONT, 10.5)
    prompt_y = state.y
    wrap_width = 58 if draw_reference else 70
    for line in _wrap(part.prompt.replace("{q}", f"{question.number:02d}"), wrap_width):
        pdf.drawString(118, prompt_y, line)
        prompt_y -= 14
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawRightString(534, prompt_y + 14, f"[{part.marks} mark{'s' if part.marks != 1 else ''}]")
    state.y = prompt_y - 12
    if part.options:
        for option in part.options:
            _lozenge(pdf, 124, state.y + 1)
            pdf.setFont(FONT_BOLD, 10)
            pdf.drawString(140, state.y, option.label)
            pdf.setFont(FONT, 10)
            pdf.drawString(160, state.y, option.text)
            state.y -= 20
    elif part.answer_unit:
        state = _answer_lines_paginated(pdf, state, line_count)
        pdf.setFont(FONT, 10)
        pdf.drawString(338, state.y + LINE_GAP, "Answer")
        pdf.line(382, state.y + LINE_GAP - 2, 455, state.y + LINE_GAP - 2)
        pdf.drawString(460, state.y + LINE_GAP, part.answer_unit)
    else:
        state = _answer_lines_paginated(pdf, state, line_count)
    state.y -= 14
    return state


def _render_stimulus(pdf: canvas.Canvas, stimulus: Stimulus, state: _QuestionRenderState) -> _QuestionRenderState:
    state = _ensure_space(pdf, state, 110)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y, stimulus.title)
    state.y -= 18
    if stimulus.kind in {"table", "bitgrid", "packet", "truth_table"}:
        state.y = _draw_table(pdf, stimulus, 118, state.y)
    elif stimulus.kind == "code":
        state.y = _draw_code_box(pdf, stimulus.code, 118, state.y)
    elif stimulus.kind == "logic":
        state.y = _draw_logic_box(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "erd":
        state.y = _draw_erd(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "network":
        state.y = _draw_network_diagram(pdf, stimulus.diagram, 118, state.y)
    else:
        for line in stimulus.lines:
            pdf.drawString(118, state.y, line)
            state.y -= 13
    return state


def _draw_table(pdf: canvas.Canvas, stimulus: Stimulus, x: float, y: float) -> float:
    width = 390
    cols = max(1, len(stimulus.headers))
    col_w = width / cols
    row_h = 20
    rows = [stimulus.headers, *stimulus.rows]
    pdf.setFillColor(colors.HexColor("#f4f4f4"))
    pdf.rect(x, y - row_h, width, row_h, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    for r_index, row in enumerate(rows):
        y0 = y - r_index * row_h
        for c_index in range(cols):
            pdf.rect(x + c_index * col_w, y0 - row_h, col_w, row_h, stroke=1, fill=0)
            value = row[c_index] if c_index < len(row) else ""
            pdf.setFont(FONT_BOLD if r_index == 0 else FONT, 8)
            pdf.drawString(x + c_index * col_w + 4, y0 - 14, value[:34])
    return y - len(rows) * row_h - 8


def _draw_code_box(pdf: canvas.Canvas, code: str, x: float, y: float) -> float:
    lines = code.splitlines() or [code]
    width = 360
    gutter = 28
    h = 20 + 14 * len(lines)
    pdf.setFillColor(colors.HexColor("#f7f7f7"))
    pdf.rect(x, y - h, width, h, stroke=1, fill=1)
    pdf.setFillColor(colors.black)
    pdf.line(x + gutter, y, x + gutter, y - h)
    pdf.setFont(FONT_MONO, 8.5)
    cursor = y - 18
    for index, line in enumerate(lines, start=1):
        pdf.drawRightString(x + gutter - 7, cursor, str(index))
        pdf.drawString(x + gutter + 8, cursor, line[:58])
        cursor -= 14
    return y - h - 8


def _draw_logic_box(pdf: canvas.Canvas, expression: str, x: float, y: float) -> float:
    pdf.rect(x, y - 112, 360, 112, stroke=1, fill=0)
    pdf.setFont(FONT, 9)
    pdf.drawString(x + 18, y - 20, "Inputs")
    for idx, label in enumerate(["A", "B", "C"]):
        pdf.line(x + 24, y - 35 - idx * 16, x + 94, y - 35 - idx * 16)
        pdf.drawString(x + 8, y - 39 - idx * 16, label)
    first_gate = "XOR" if "XOR" in expression else "AND"
    second_gate = "OR" if " OR " in expression else "AND"
    _draw_logic_gate_symbol(pdf, first_gate, x + 102, y - 66)
    pdf.line(x + 158, y - 48, x + 202, y - 48)
    _draw_logic_gate_symbol(pdf, second_gate, x + 204, y - 66)
    pdf.line(x + 260, y - 48, x + 316, y - 48)
    pdf.drawString(x + 322, y - 52, "X")
    pdf.setFont(FONT, 8)
    pdf.drawString(x + 102, y - 92, expression[:44])
    return y - 122


def _draw_logic_gate_symbol(pdf: canvas.Canvas, label: str, x: float, y: float) -> None:
    top = y + 28
    bottom = y - 10
    if label == "OR":
        pdf.bezier(x + 2, bottom, x + 20, y + 2, x + 20, y + 16, x + 2, top)
        pdf.bezier(x + 2, top, x + 44, top, x + 54, y + 18, x + 54, y + 9)
        pdf.bezier(x + 54, y + 9, x + 44, bottom, x + 2, bottom, x + 2, bottom)
    elif label == "XOR":
        pdf.bezier(x - 4, bottom, x + 14, y + 2, x + 14, y + 16, x - 4, top)
        pdf.bezier(x + 2, bottom, x + 20, y + 2, x + 20, y + 16, x + 2, top)
        pdf.bezier(x + 2, top, x + 44, top, x + 54, y + 18, x + 54, y + 9)
        pdf.bezier(x + 54, y + 9, x + 44, bottom, x + 2, bottom, x + 2, bottom)
    else:
        pdf.line(x, bottom, x, top)
        pdf.bezier(x, top, x + 58, top, x + 58, bottom, x, bottom)
    pdf.setFont(FONT_BOLD, 7.5)
    pdf.drawCentredString(x + 30, y + 6, label)


def _draw_erd(pdf: canvas.Canvas, diagram: str, x: float, y: float) -> float:
    names = ["CUSTOMER", "ORDER", "ORDER_ITEM", "PRODUCT"]
    cursor = x
    for idx, name in enumerate(names):
        pdf.rect(cursor, y - 42, 72, 30, stroke=1, fill=0)
        pdf.setFont(FONT_BOLD, 8)
        pdf.drawCentredString(cursor + 36, y - 31, name)
        if idx < len(names) - 1:
            pdf.line(cursor + 72, y - 27, cursor + 98, y - 27)
        cursor += 98
    pdf.setFont(FONT, 8)
    pdf.drawString(x, y - 60, diagram)
    return y - 74


def _draw_network_diagram(pdf: canvas.Canvas, diagram: str, x: float, y: float) -> float:
    nodes = _network_nodes(diagram, x, y)
    for start, end in [("Client", "Switch"), ("Laptop", "Switch"), ("Switch", "Router"), ("Router", "Server")]:
        if start in nodes and end in nodes:
            sx, sy = nodes[start]
            ex, ey = nodes[end]
            pdf.line(sx, sy, ex, ey)
    for label, (cx, cy) in nodes.items():
        if label in {"Switch", "Router"}:
            pdf.rect(cx - 22, cy - 12, 44, 24, stroke=1, fill=0)
        else:
            pdf.roundRect(cx - 26, cy - 14, 52, 28, 4, stroke=1, fill=0)
        pdf.setFont(FONT, 7.5)
        pdf.drawCentredString(cx, cy - 3, label)
    pdf.setFont(FONT, 8)
    pdf.drawString(x, y - 118, "Network diagram")
    return y - 132


def _network_nodes(diagram: str, x: float, y: float) -> dict[str, tuple[float, float]]:
    if diagram == "mesh-wan":
        return {"Client": (x + 36, y - 42), "Laptop": (x + 36, y - 86), "Switch": (x + 140, y - 64), "Router": (x + 238, y - 64), "Server": (x + 330, y - 64)}
    if diagram == "star-lan":
        return {"Client": (x + 44, y - 40), "Laptop": (x + 44, y - 90), "Switch": (x + 178, y - 64), "Router": (x + 290, y - 64), "Server": (x + 342, y - 104)}
    return {"Client": (x + 40, y - 64), "Laptop": (x + 40, y - 104), "Switch": (x + 152, y - 84), "Router": (x + 252, y - 84), "Server": (x + 340, y - 84)}


def _ensure_space(pdf: canvas.Canvas, state: _QuestionRenderState, height: float) -> _QuestionRenderState:
    if state.y - height >= BOTTOM:
        return state
    pdf.setFont(FONT, 9)
    pdf.drawRightString(500, 62, "Turn over >")
    pdf.showPage()
    state.page += 1
    state.y = 724
    _draw_question_page_header(pdf, state.page)
    return state


def _new_question_page(pdf: canvas.Canvas, state: _QuestionRenderState) -> _QuestionRenderState:
    pdf.setFont(FONT, 9)
    pdf.drawRightString(500, 62, "Turn over >")
    pdf.showPage()
    state.page += 1
    state.y = 724
    _draw_question_page_header(pdf, state.page)
    return state


def _format_question_number(number: int) -> str:
    if number < 10:
        return f"0 {number}"
    return f"{number // 10} {number % 10}"


def _draw_question_ref(pdf: canvas.Canvas, x: float, y: float, number: int, part_label: str | None = None) -> None:
    digits = list(f"{number:02d}")
    cursor = x
    pdf.setFont(FONT_BOLD, 10)
    for digit in digits:
        pdf.rect(cursor, y - 16, 17, 16, stroke=1, fill=0)
        pdf.drawCentredString(cursor + 8.5, y - 12, digit)
        cursor += 17
    if part_label is not None:
        pdf.setFont(FONT_BOLD, 12)
        pdf.drawCentredString(cursor + 5, y - 13, ".")
        cursor += 10
        pdf.setFont(FONT_BOLD, 10)
        pdf.rect(cursor, y - 16, 17, 16, stroke=1, fill=0)
        pdf.drawCentredString(cursor + 8.5, y - 12, str(part_label))


def _answer_line_count(part: QuestionPart) -> int:
    if part.options:
        return 0
    if part.answer_unit:
        return max(part.answer_lines, 5 if part.marks == 1 else 7 if part.marks == 2 else part.marks * 3)
    if part.marks == 1:
        return max(part.answer_lines, 4)
    if part.marks == 2:
        return max(part.answer_lines, 7)
    if part.marks == 3:
        return max(part.answer_lines, 10)
    if part.marks == 4:
        return max(part.answer_lines, 15)
    if part.marks <= 6:
        return max(part.answer_lines, 20)
    if part.marks < 12:
        return max(part.answer_lines, 26)
    return max(part.answer_lines, 42)


def _answer_lines(pdf: canvas.Canvas, y: float, count: int) -> None:
    pdf.setStrokeColor(colors.HexColor("#404040"))
    pdf.setLineWidth(0.45)
    for index in range(count):
        line_y = y - index * LINE_GAP
        pdf.line(118, line_y, 534, line_y)
    pdf.setStrokeColor(colors.black)


def _answer_lines_paginated(pdf: canvas.Canvas, state: _QuestionRenderState, count: int) -> _QuestionRenderState:
    remaining = count
    while remaining:
        available = int((state.y - (BOTTOM + 60)) // LINE_GAP)
        if available <= 0:
            state = _new_question_page(pdf, state)
            continue
        lines = min(remaining, available)
        _answer_lines(pdf, state.y, lines)
        state.y -= lines * LINE_GAP
        remaining -= lines
        if remaining:
            state = _new_question_page(pdf, state)
    return state


def _lozenge(pdf: canvas.Canvas, x: float, y: float) -> None:
    pdf.roundRect(x, y - 5, 11, 8, 4, stroke=1, fill=0)


def _mark_total_box(pdf: canvas.Canvas, marks: int, y: float) -> None:
    pdf.rect(547, y - 42, 32, 42, stroke=1, fill=0)
    pdf.line(551, y - 18, 575, y - 18)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(563, y - 32, str(marks))


def _draw_extra_answer_page(pdf: canvas.Canvas, page: int) -> None:
    pdf.showPage()
    _draw_question_page_header(pdf, page)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(282, 725, "Additional answer space")
    y = 680
    _answer_lines(pdf, y, 25)


def _draw_footer_barcode(pdf: canvas.Canvas, x: float, y: float, page: int) -> None:
    widths = [1, 1, 2, 1, 3, 1, 1, 2, 1, 2, 3, 1, 1, 1, 2, 2, 1, 3]
    cursor = x
    pdf.setFillColor(colors.black)
    for index, width in enumerate(widths * 3):
        if index % 2 == 0:
            pdf.rect(cursor, y + 11, width, 27, stroke=0, fill=1)
        cursor += width + 1
    pdf.setFont(FONT, 8)
    pdf.drawCentredString(x + 31, y, f"{page:02d}")
    pdf.setFillColor(colors.black)


def _mark_scheme_cover(pdf: canvas.Canvas) -> None:
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(55, 720, "A-level")
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(55, 690, "COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 15)
    pdf.drawString(55, 665, "7517/2")
    pdf.drawString(55, 640, "Paper 2")
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(55, 585, "Mark scheme")
    pdf.setFont(FONT, 13)
    pdf.drawString(55, 555, f"June {paper2_exam_date().year}")
    pdf.drawString(55, 530, "Version: 1.0 Practice")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(55, 40, f"*{paper2_exam_date():%y}6A7517/2/MS*")


def _mark_scheme_intro(pdf: canvas.Canvas, page: int) -> None:
    _ms_header(pdf, page)
    y = 705
    pdf.setFont(FONT, 10)
    paragraphs = [
        "Mark schemes are prepared to support consistent marking. This unofficial practice mark scheme follows the structure of AQA A-level Computer Science Paper 2.",
        "The standardisation process ensures that responses are judged in the same way by different examiners. Alternative answers not listed in the mark scheme should be credited where they are technically correct and answer the question set.",
        "It must be stressed that a mark scheme is a working document. Details vary with the content of a particular question paper, while the assessment principles remain consistent.",
        "No student should be disadvantaged by the way they refer to themselves or others in written responses. Credit relevant technical content wherever it is communicated clearly.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 92):
            pdf.drawString(55, y, line)
            y -= 14
        y -= 10


def _mark_scheme_levels(pdf: canvas.Canvas, page: int) -> None:
    _ms_header(pdf, page)
    y = 705
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, y, "Level of response marking instructions")
    y -= 26
    pdf.setFont(FONT, 10)
    paragraphs = [
        "Level of response mark schemes are broken down into levels, each of which has a descriptor. The descriptor indicates the average performance expected at that level.",
        "Start at the lowest level and use it as a ladder. Decide whether the answer meets that descriptor, then move upwards until the best match is found.",
        "When assigning a level, consider the overall quality of the response. Do not focus on small weak parts if the response is otherwise stronger.",
        "Once a level has been selected, choose a mark within the level by considering accuracy, technical detail, application to the scenario and the quality of the final judgement.",
        "Indicative content is a guide for examiners. It is not exhaustive, and students do not need to include every listed point to reach the highest level.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 94):
            pdf.drawString(55, y, line)
            y -= 14
        y -= 10


def _mark_scheme_annotations(pdf: canvas.Canvas, page: int) -> None:
    _ms_header(pdf, page)
    y = 705
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, y, "Annotation used in the mark scheme")
    y -= 28
    pdf.setFont(FONT, 10)
    rows = [
        (";", "single mark point"),
        ("//", "alternative response"),
        ("A.", "acceptable creditworthy answer"),
        ("R.", "reject answer as not creditworthy"),
        ("NE.", "not enough for credit"),
        ("I.", "ignore"),
    ]
    for code, meaning in rows:
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(70, y, code)
        pdf.setFont(FONT, 10)
        pdf.drawString(120, y, meaning)
        y -= 22


def _mark_scheme_examiner_notes(pdf: canvas.Canvas, page: int) -> None:
    _ms_header(pdf, page)
    y = 705
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(55, y, "To Examiners:")
    y -= 28
    pdf.setFont(FONT, 10)
    paragraphs = [
        "A mark of 0 should be awarded where a candidate has attempted a question but failed to write anything creditworthy.",
        "Insert a hyphen when a candidate has not attempted a question, so that a distinction can be made between no response and nothing creditworthy.",
        "This mark scheme contains the correct responses candidates are most likely to give. Other valid responses are possible and should be credited.",
        "Where a candidate makes a valid point and then contradicts it, do not award the mark for that point.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 94):
            pdf.drawString(70, y, "\u2022 " + line if line == _wrap(paragraph, 94)[0] else "  " + line)
            y -= 14
        y -= 8


def _mark_scheme_table_header(pdf: canvas.Canvas, page: int) -> float:
    _ms_header(pdf, page)
    y = 710
    pdf.setFont(FONT_BOLD, 9)
    pdf.rect(45, y - 24, 505, 24, stroke=1, fill=0)
    pdf.line(73, y - 24, 73, y)
    pdf.line(106, y - 24, 106, y)
    pdf.line(500, y - 24, 500, y)
    pdf.drawString(52, y - 16, "Qu")
    pdf.drawString(84, y - 16, "Pt")
    pdf.drawString(125, y - 16, "Marking guidance")
    pdf.drawCentredString(525, y - 10, "Total")
    pdf.drawCentredString(525, y - 21, "marks")
    return y - 38


def _render_mark_scheme_part(pdf: canvas.Canvas, question: Question, part: QuestionPart, y: float) -> float:
    start_y = y
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(52, y, f"{question.number:02d}")
    pdf.drawString(86, y, part.label)
    pdf.drawRightString(528, y, str(part.marks))
    pdf.setFont(FONT_BOLD, 9.5)
    pdf.drawString(125, y, f"All marks {part.marking.ao}")
    y -= 14
    pdf.setFont(FONT, 9.5)
    for point in part.marking.points:
        for line in _wrap(point, 70):
            pdf.drawString(125, y, line)
            y -= 13
    for item in part.marking.accept:
        pdf.drawString(125, y, f"A. {item}")
        y -= 13
    for item in part.marking.reject:
        pdf.drawString(125, y, f"R. {item}")
        y -= 13
    for item in part.marking.levels:
        for line in _wrap(item, 70):
            pdf.drawString(125, y, line)
            y -= 13
    bottom = y - 5
    top = start_y + 10
    pdf.rect(45, bottom, 505, top - bottom, stroke=1, fill=0)
    pdf.line(73, bottom, 73, top)
    pdf.line(106, bottom, 106, top)
    pdf.line(500, bottom, 500, top)
    return min(start_y - 34, y - 18)


def _ms_header(pdf: canvas.Canvas, page: int) -> None:
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawCentredString(297, 800, "MARK SCHEME - A-LEVEL COMPUTER SCIENCE - 7517/2 - PRACTICE")
    pdf.setFont(FONT, 9)
    pdf.drawCentredString(297, 32, str(page))


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]
