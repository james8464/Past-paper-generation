from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen import canvas

from cspapergen.models import PaperBlueprint, Question, QuestionPart, Stimulus

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
LEFT = 54
RIGHT = 500
TOP = 770
BOTTOM = 58
RAIL_X = 516
LINE_GAP = 20
AQA_A4 = (595.32, 841.92)


def render_question_paper(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _cover_page(pdf, blueprint)
    pdf.showPage()
    state = _QuestionRenderState(page=2, y=720)
    _draw_question_page_header(pdf, state.page)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(297, state.y, "Answer all questions.")
    state.y -= 44
    for question in blueprint.questions:
        state = _render_question(pdf, question, state)
    _draw_extra_answer_page(pdf, state.page + 1)
    pdf.save()


def render_mark_scheme(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _mark_scheme_cover(pdf)
    pdf.showPage()
    _mark_scheme_intro(pdf, 2)
    pdf.showPage()
    _mark_scheme_annotations(pdf, 3)
    pdf.showPage()
    page = 4
    y = _mark_scheme_table_header(pdf, page)
    for question in blueprint.questions:
        for part in question.parts:
            needed = 42 + 12 * (len(part.marking.points) + len(part.marking.accept) + len(part.marking.reject) + len(part.marking.levels))
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
    today = date.today()
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
    pdf.drawString(55, 458, f"{today:%A} {today.day} {today:%B %Y}")
    pdf.drawString(225, 458, "Morning")
    pdf.setFont(FONT, 9.5)
    pdf.drawString(302, 458, "Time allowed: 2 hours 30 minutes")

    y = 430
    y = _cover_section(pdf, y, "Materials", ["For this paper you must have:", "- a calculator."])
    y = _cover_section(
        pdf,
        y - 8,
        "Instructions",
        [
            "- Use black ink or black ball-point pen.",
            "- Fill in the boxes at the top of this page.",
            "- Answer all questions.",
            "- You must answer the questions in the spaces provided. Do not write outside the box around each page or on blank pages.",
            "- If you need extra space for your answer(s), use the lined page at the end of this book.",
            "- Do all rough work in this book. Cross through any work you do not want to be marked.",
        ],
    )
    y = _cover_section(pdf, y - 8, "Information", ["- The marks for questions are shown in brackets.", f"- The maximum mark for this paper is {blueprint.total_marks}."])
    _cover_section(
        pdf,
        y - 8,
        "Advice",
        [
            "- In some questions you are required to indicate your answer by completely shading a lozenge alongside the appropriate answer.",
            "- If you want to change your answer you must cross out your original answer.",
            "- If you wish to return to an answer previously crossed out, ring the answer you now wish to select.",
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
    pdf.setFont(FONT_BOLD, 8)
    pdf.drawCentredString(552, 780, "Do not write")
    pdf.drawCentredString(552, 769, "outside the")
    pdf.drawCentredString(552, 758, "box")
    pdf.setLineWidth(0.7)
    pdf.rect(44, 48, 470, 735, stroke=1, fill=0)
    pdf.setFont(FONT, 8)
    pdf.drawString(52, 28, f"*{page:02d}*")
    pdf.drawRightString(510, 28, "IB/G/Jun26/7517/2")


def _render_question(pdf: canvas.Canvas, question: Question, state: _QuestionRenderState) -> _QuestionRenderState:
    if state.y < 330:
        state = _new_question_page(pdf, state)
    state = _ensure_space(pdf, state, 80)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(64, state.y, _format_question_number(question.number))
    pdf.setFont(FONT, 10.5)
    for line in _wrap(question.stem, 78):
        pdf.drawString(118, state.y, line)
        state.y -= 14
    state.y -= 8
    if question.stimulus:
        state = _render_stimulus(pdf, question.stimulus, state)
        state.y -= 8
    for part in question.parts:
        state = _render_part(pdf, question, part, state)
    state = _ensure_space(pdf, state, 34)
    _mark_total_box(pdf, question.total_marks, state.y)
    state.y -= 42
    return state


def _render_part(pdf: canvas.Canvas, question: Question, part: QuestionPart, state: _QuestionRenderState) -> _QuestionRenderState:
    estimated = 52 + part.answer_lines * LINE_GAP
    state = _ensure_space(pdf, state, estimated)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(64, state.y, f"{_format_question_number(question.number)} . {part.label}")
    pdf.setFont(FONT, 10.5)
    prompt_y = state.y
    for line in _wrap(part.prompt.replace("{q}", f"{question.number:02d}"), 58):
        pdf.drawString(118, prompt_y, line)
        prompt_y -= 14
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawRightString(492, state.y, f"[{part.marks} mark{'s' if part.marks != 1 else ''}]")
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
        _answer_lines(pdf, state.y, part.answer_lines)
        state.y -= part.answer_lines * LINE_GAP
        pdf.setFont(FONT, 10)
        pdf.drawString(338, state.y + LINE_GAP, "Answer")
        pdf.line(382, state.y + LINE_GAP - 2, 455, state.y + LINE_GAP - 2)
        pdf.drawString(460, state.y + LINE_GAP, part.answer_unit)
    else:
        _answer_lines(pdf, state.y, part.answer_lines)
        state.y -= part.answer_lines * LINE_GAP
    state.y -= 14
    return state


def _render_stimulus(pdf: canvas.Canvas, stimulus: Stimulus, state: _QuestionRenderState) -> _QuestionRenderState:
    state = _ensure_space(pdf, state, 110)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y, stimulus.title)
    state.y -= 18
    if stimulus.kind in {"table", "bitgrid", "packet"}:
        state.y = _draw_table(pdf, stimulus, 118, state.y)
    elif stimulus.kind == "code":
        state.y = _draw_code_box(pdf, stimulus.code, 118, state.y)
    elif stimulus.kind == "logic":
        state.y = _draw_logic_box(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "erd":
        state.y = _draw_erd(pdf, stimulus.diagram, 118, state.y)
    else:
        for line in stimulus.lines:
            pdf.drawString(118, state.y, line)
            state.y -= 13
    return state


def _draw_table(pdf: canvas.Canvas, stimulus: Stimulus, x: float, y: float) -> float:
    width = 340
    cols = max(1, len(stimulus.headers))
    col_w = width / cols
    row_h = 20
    rows = [stimulus.headers, *stimulus.rows]
    pdf.setFont(FONT_BOLD, 9)
    for r_index, row in enumerate(rows):
        y0 = y - r_index * row_h
        for c_index in range(cols):
            pdf.rect(x + c_index * col_w, y0 - row_h, col_w, row_h, stroke=1, fill=0)
            value = row[c_index] if c_index < len(row) else ""
            pdf.drawString(x + c_index * col_w + 4, y0 - 14, value[:32])
        pdf.setFont(FONT, 9)
    return y - len(rows) * row_h - 8


def _draw_code_box(pdf: canvas.Canvas, code: str, x: float, y: float) -> float:
    lines = code.splitlines() or [code]
    h = 18 + 14 * len(lines)
    pdf.rect(x, y - h, 340, h, stroke=1, fill=0)
    pdf.setFont("Courier", 9)
    cursor = y - 18
    for line in lines:
        pdf.drawString(x + 8, cursor, line)
        cursor -= 14
    return y - h - 8


def _draw_logic_box(pdf: canvas.Canvas, expression: str, x: float, y: float) -> float:
    pdf.rect(x, y - 92, 340, 92, stroke=1, fill=0)
    pdf.setFont(FONT, 9)
    pdf.drawString(x + 18, y - 20, "Inputs")
    for idx, label in enumerate(["A", "B", "C"]):
        pdf.line(x + 24, y - 35 - idx * 16, x + 94, y - 35 - idx * 16)
        pdf.drawString(x + 8, y - 39 - idx * 16, label)
    pdf.rect(x + 100, y - 62, 64, 38, stroke=1, fill=0)
    pdf.drawCentredString(x + 132, y - 46, expression[:12])
    pdf.line(x + 164, y - 43, x + 250, y - 43)
    pdf.drawString(x + 258, y - 47, "Output")
    return y - 102


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


def _ensure_space(pdf: canvas.Canvas, state: _QuestionRenderState, height: float) -> _QuestionRenderState:
    if state.y - height >= BOTTOM:
        return state
    pdf.setFont(FONT, 9)
    pdf.drawRightString(500, 62, "Turn over >")
    pdf.showPage()
    state.page += 1
    state.y = 720
    _draw_question_page_header(pdf, state.page)
    return state


def _new_question_page(pdf: canvas.Canvas, state: _QuestionRenderState) -> _QuestionRenderState:
    pdf.setFont(FONT, 9)
    pdf.drawRightString(500, 62, "Turn over >")
    pdf.showPage()
    state.page += 1
    state.y = 720
    _draw_question_page_header(pdf, state.page)
    return state


def _format_question_number(number: int) -> str:
    if number < 10:
        return f"0 {number}"
    return f"{number // 10} {number % 10}"


def _answer_lines(pdf: canvas.Canvas, y: float, count: int) -> None:
    pdf.setStrokeColor(colors.HexColor("#404040"))
    pdf.setLineWidth(0.45)
    for index in range(count):
        line_y = y - index * LINE_GAP
        pdf.line(118, line_y, 492, line_y)
    pdf.setStrokeColor(colors.black)


def _lozenge(pdf: canvas.Canvas, x: float, y: float) -> None:
    pdf.roundRect(x, y - 5, 11, 8, 4, stroke=1, fill=0)


def _mark_total_box(pdf: canvas.Canvas, marks: int, y: float) -> None:
    pdf.rect(466, y - 20, 28, 20, stroke=1, fill=0)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(480, y - 14, str(marks))


def _draw_extra_answer_page(pdf: canvas.Canvas, page: int) -> None:
    pdf.showPage()
    _draw_question_page_header(pdf, page)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(282, 725, "Additional answer space")
    y = 680
    _answer_lines(pdf, y, 25)


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
    pdf.drawString(55, 555, f"June {date.today():%Y}")
    pdf.drawString(55, 530, "Version: 1.0 Practice")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(55, 40, "*26A7517/2/MS*")


def _mark_scheme_intro(pdf: canvas.Canvas, page: int) -> None:
    _ms_header(pdf, page)
    y = 705
    pdf.setFont(FONT, 10)
    paragraphs = [
        "This mark scheme is for an unofficial practice paper. It follows the structure and marking style of AQA Computer Science Paper 2.",
        "Award credit for valid alternative answers that show equivalent understanding. Do not award credit for vague statements unless the point is developed enough to answer the question.",
        "For extended responses, assign the level that best fits the response as a whole, then choose a mark within that level using the quality of technical detail and judgement.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 92):
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


def _mark_scheme_table_header(pdf: canvas.Canvas, page: int) -> float:
    _ms_header(pdf, page)
    y = 710
    pdf.setFont(FONT_BOLD, 9)
    pdf.rect(45, y - 24, 505, 24, stroke=1, fill=0)
    pdf.drawString(52, y - 16, "Qu")
    pdf.drawString(84, y - 16, "Pt")
    pdf.drawString(125, y - 16, "Marking guidance")
    pdf.drawString(494, y - 16, "Total marks")
    return y - 38


def _render_mark_scheme_part(pdf: canvas.Canvas, question: Question, part: QuestionPart, y: float) -> float:
    start_y = y
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(52, y, f"{question.number:02d}")
    pdf.drawString(86, y, part.label)
    pdf.drawRightString(528, y, str(part.marks))
    pdf.setFont(FONT, 8.5)
    pdf.drawString(125, y, f"All marks {part.marking.ao}")
    y -= 14
    for point in part.marking.points:
        for line in _wrap(point, 70):
            pdf.drawString(125, y, line)
            y -= 11
    for item in part.marking.accept:
        pdf.drawString(125, y, f"A. {item}")
        y -= 11
    for item in part.marking.reject:
        pdf.drawString(125, y, f"R. {item}")
        y -= 11
    for item in part.marking.levels:
        for line in _wrap(item, 70):
            pdf.drawString(125, y, line)
            y -= 11
    pdf.line(45, y - 5, 550, y - 5)
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
