from __future__ import annotations

import math
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from Backend.Core.computer_science_reference_solutions import (
    paper1_reference_code as _paper1_reference_code,
)
from Backend.Core.document_dsl import (
    CanvasBarcodeStyle,
    DocumentRole,
    SolidRuleStyle,
    draw_barcode,
    draw_solid_answer_rules,
    renderer_contract,
)
from Backend.Core.exam_cover import CoverProfile, draw_mark_scheme_cover
from Backend.Core.exam_pages import ExamPageProfile, draw_exam_page
from Backend.Core.fonts import register_fonts as _rf
from Backend.Core.generation_date import (
    formatted_generation_date,
    generation_date,
)
from Backend.Core.open_credit import printed_credit_points
from Backend.Core.subjects.sql_contracts import render_sql_schema
from cspapergen.models import PaperBlueprint, Question, QuestionPart, Stimulus

FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
FONT_MONO = "AQACourier"
RENDERER_CONTRACT = renderer_contract(
    "aqa",
    roles=(DocumentRole.QUESTION_PAPER, DocumentRole.MARK_SCHEME),
    vector_components=("program-trace", "logic-circuit", "statistical-chart"),
)
LEFT = 54
RIGHT = 534
TOP = 770
BOTTOM = 76
RAIL_X = 516
LINE_GAP = 20
AQA_CS_ANSWER_RULES = SolidRuleStyle(
    left=118,
    right=534,
    gap=LINE_GAP,
    color=colors.HexColor("#404040"),
    width=0.45,
)
AQA_CS_FOOTER_BARCODE = CanvasBarcodeStyle(
    widths=(1, 1, 2, 1, 3, 1, 1, 2, 1, 2, 3, 1, 1, 1, 2, 2, 1, 3),
    repetitions=3,
    height=27,
    bar_y_offset=11,
    gap=1,
    font=FONT,
    font_size=8,
    caption_center_offset=31,
)
AQA_A4 = (595.32, 841.92)
EXTRA_ANSWER_PAGES = 3
PAPER2_QUESTION_PAGE_ALLOCATION = (3, 2, 2, 1, 2, 5, 3, 2, 4, 2, 2, 3, 1, 3)
PAPER2_PART_PAGE_OFFSETS = {
    1: (0, 1, 2),
    2: (0, 0, 1, 1),
    3: (0, 1),
    4: (0,),
    5: (0,),
    6: (0, 1, 2, 3, 4),
    7: (0, 0, 1, 2),
    8: (0,),
    9: (0, 1, 2),
    10: (0, 1),
    11: (0, 0, 1, 1),
    12: (0, 0, 1, 1, 2, 2),
    13: (0,),
    14: (0,),
}
PAPER1_SECTIONS = {
    1: ("Section A", "You are advised to spend about 40 minutes on this section."),
    4: ("Section B", "You are advised to spend about 20 minutes on this section."),
    5: ("Section C", "You are advised to spend about 20 minutes on this section."),
    7: ("Section D", "You are advised to spend about 70 minutes on this section."),
}
PAPER1_INTERSTITIAL_AFTER = {3: "support", 4: "blank", 6: "blank"}
PAPER1_SHARE_PAGE_WITH_PREVIOUS = {8, 10}
PAPER1_TRAILING_BLANK_PAGES = 5

_rf(FONT, FONT_BOLD, FONT_MONO, default_fallback="Times-Roman")


def render_question_paper(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _set_document_metadata(pdf, blueprint, "Question paper")
    _cover_page(pdf, blueprint)
    pdf.showPage()
    state = _QuestionRenderState(page=2, y=724, blueprint=blueprint)
    _draw_question_page_header(pdf, state.page, blueprint)
    if blueprint.paper_number == "1" and blueprint.delivery_mode == "on-screen":
        state = _render_paper1_question_pages(pdf, blueprint, state)
        pdf.save()
        return
    if blueprint.paper_number == "2":
        state = _render_paper2_question_pages(pdf, blueprint, state)
        pdf.save()
        return
    for index, question in enumerate(blueprint.questions):
        if index:
            state = _new_question_page(pdf, state)
        state = _render_question(
            pdf,
            question,
            state,
            show_answer_space=blueprint.delivery_mode == "written",
        )
    state = _ensure_space(pdf, state, 90)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y - 20, "END OF QUESTIONS")
    state.y -= 80
    extra_pages = EXTRA_ANSWER_PAGES if blueprint.delivery_mode == "written" else 0
    for index in range(extra_pages):
        _draw_extra_answer_page(
            pdf,
            state.page + 1,
            blueprint,
            legal_notice=index == extra_pages - 1,
        )
        state.page += 1
    pdf.save()


def _render_paper2_question_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    state: _QuestionRenderState,
) -> _QuestionRenderState:
    if len(blueprint.questions) != len(PAPER2_QUESTION_PAGE_ALLOCATION):
        raise ValueError("Paper 2 question count does not match its measured page plan")
    for index, (question, allocation) in enumerate(
        zip(blueprint.questions, PAPER2_QUESTION_PAGE_ALLOCATION, strict=True)
    ):
        if index:
            state = _new_question_page(pdf, state)
        first_page = state.page
        last_page = first_page + allocation - 1
        state = _render_paper2_question(
            pdf,
            question,
            state,
            first_page,
            last_page,
        )
        if state.page > last_page:
            raise ValueError(
                f"Question {question.number} overflowed its {allocation}-page fixed slot"
            )
        while state.page < last_page:
            state = _new_question_page(pdf, state)
            if question.number == 5:
                _draw_intentionally_blank_page(pdf, state)
            elif question.number == 14:
                _draw_assembly_support_page(
                    pdf,
                    state,
                    page_offset=state.page - first_page,
                )
            else:
                _draw_question_continuation(pdf, state, question.number)

    state = _ensure_space(pdf, state, 54)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y - 18, "END OF QUESTIONS")
    state = _new_question_page(pdf, state)
    _draw_intentionally_blank_page(pdf, state, do_not_write=True)
    for index in range(EXTRA_ANSWER_PAGES):
        _draw_extra_answer_page(
            pdf,
            state.page + 1,
            blueprint,
            legal_notice=index == EXTRA_ANSWER_PAGES - 1,
        )
        state.page += 1
    return state


def _render_paper2_question(
    pdf: canvas.Canvas,
    question: Question,
    state: _QuestionRenderState,
    first_page: int,
    last_page: int,
) -> _QuestionRenderState:
    offsets = PAPER2_PART_PAGE_OFFSETS[question.number]
    if len(offsets) != len(question.parts):
        raise ValueError(
            f"Question {question.number} part count does not match its measured page plan"
        )
    _draw_question_ref(pdf, 52, state.y + 1, question.number)
    pdf.setFont(FONT, 11)
    for line in _wrap(question.stem, 78):
        pdf.drawString(118, state.y, line)
        state.y -= 14
    state.y -= 8
    if question.stimulus:
        state = _render_stimulus(pdf, question.stimulus, state)
        state.y -= 8

    for part, page_offset in zip(question.parts, offsets, strict=True):
        desired_page = first_page + page_offset
        while state.page < desired_page:
            state = _new_question_page(pdf, state)
            _draw_question_continuation_heading(pdf, state, question.number)
        state = _render_part(
            pdf,
            question,
            part,
            state,
            draw_reference=True,
            show_answer_space=True,
        )
        if state.page > last_page:
            raise ValueError(
                f"Question {question.number} overflowed its fixed page range"
            )

    state = _ensure_space(pdf, state, 34)
    _mark_total_box(pdf, question.total_marks, state.y)
    state.y -= 42
    return state


def _draw_question_continuation_heading(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question_number: int,
) -> None:
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, 718, f"Question {question_number} continued")
    state.y = 682


def _draw_assembly_support_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    *,
    page_offset: int,
) -> None:
    pdf.setFont(FONT_BOLD, 10.5)
    title = (
        "Program 1 continued"
        if page_offset == 1
        else "Standard assembly language instruction set"
    )
    pdf.drawCentredString(282, 718, title)
    if page_offset == 1:
        rows = [
            ["Section", "Purpose"],
            ["Initialisation", "Set register values and the loop counter"],
            ["Loop", "Compare, branch, shift and update the counter"],
            ["Termination", "Store the final result in memory"],
        ]
    else:
        rows = [
            ["Instruction", "Meaning"],
            ["MOV Rd, operand", "Copy operand into register Rd"],
            ["CMP Rn, operand", "Compare Rn with operand"],
            ["BEQ label", "Branch when the comparison is equal"],
            ["ADD Rd, Rn, operand", "Add Rn and operand; store in Rd"],
            ["LSR Rd, Rn, operand", "Logical shift right"],
            ["STR Rd, address", "Store register value in memory"],
        ]
    stimulus = Stimulus(kind="table", title="", headers=rows[0], rows=rows[1:])
    state.y = _draw_table(pdf, stimulus, 92, 680)
    pdf.setFont(FONT, 9)
    pdf.drawString(
        92,
        state.y - 10,
        "Use this independently written instruction summary when answering Question 14.",
    )


def _draw_question_continuation(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question_number: int,
) -> None:
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, 718, f"Question {question_number} continued")
    draw_solid_answer_rules(
        pdf,
        first_y=680,
        count=25,
        style=AQA_CS_ANSWER_RULES,
    )
    state.y = 160


def _render_paper1_question_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    state: _QuestionRenderState,
) -> _QuestionRenderState:
    if [question.number for question in blueprint.questions] != list(range(1, 13)):
        raise ValueError("Paper 1 question paper requires Questions 1 to 12")
    questions = {question.number: question for question in blueprint.questions}

    _draw_paper1_compact_section_heading(pdf, state, *PAPER1_SECTIONS[1])
    state = _render_question(
        pdf,
        questions[1],
        state,
        show_answer_space=False,
        allow_current_page=True,
    )

    state = _new_question_page(pdf, state)
    state = _render_question(
        pdf,
        questions[2],
        state,
        show_answer_space=False,
        allow_current_page=True,
    )
    state = _render_paper1_partial_question(
        pdf,
        questions[3],
        questions[3].parts[:2],
        state,
        allow_current_page=True,
    )

    state = _new_question_page(pdf, state)
    state = _render_paper1_partial_question(
        pdf,
        questions[3],
        questions[3].parts[2:4],
        state,
    )

    state = _new_question_page(pdf, state)
    state = _render_paper1_partial_question(
        pdf,
        questions[3],
        questions[3].parts[4:],
        state,
    )
    _draw_trace_response_grid(pdf, state, rows=8)

    state = _new_question_page(pdf, state)
    _draw_paper1_support_page(pdf, state, questions[3])

    state = _new_question_page(pdf, state)
    _draw_paper1_trace_support_page(pdf, state, questions[3])

    state = _new_question_page(pdf, state)
    _draw_paper1_compact_section_heading(pdf, state, *PAPER1_SECTIONS[4])
    state = _render_question(
        pdf,
        questions[4],
        state,
        show_answer_space=False,
        allow_current_page=True,
    )

    state = _new_question_page(pdf, state)
    _draw_complexity_support_page(pdf, state, questions[4])

    state = _new_question_page(pdf, state)
    _draw_intentionally_blank_page(pdf, state)

    state = _new_question_page(pdf, state)
    _draw_paper1_compact_section_heading(pdf, state, *PAPER1_SECTIONS[5])
    state = _render_question(
        pdf,
        questions[5],
        state,
        show_answer_space=False,
        allow_current_page=True,
    )

    state = _new_question_page(pdf, state)
    state = _render_paper1_partial_question(
        pdf,
        questions[6],
        questions[6].parts[:4],
        state,
    )

    state = _new_question_page(pdf, state)
    state = _render_paper1_partial_question(
        pdf,
        questions[6],
        questions[6].parts[4:],
        state,
    )

    state = _new_question_page(pdf, state)
    _draw_paper1_support_page(pdf, state, questions[6])

    state = _new_question_page(pdf, state)
    _draw_intentionally_blank_page(pdf, state)

    state = _new_question_page(pdf, state)
    _draw_paper1_compact_section_heading(pdf, state, *PAPER1_SECTIONS[7])
    for number in (7, 8, 9):
        state = _render_question(
            pdf,
            questions[number],
            state,
            show_answer_space=False,
            allow_current_page=True,
        )

    state = _new_question_page(pdf, state)
    _draw_skeleton_program_support_page(pdf, state, questions[9])

    for number in (10, 11, 12):
        state = _new_question_page(pdf, state)
        state = _render_question(
            pdf,
            questions[number],
            state,
            show_answer_space=False,
            allow_current_page=True,
        )

    state = _ensure_space(pdf, state, 72)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y - 18, "END OF QUESTIONS")
    for _index in range(4):
        state = _new_question_page(pdf, state)
        _draw_intentionally_blank_page(pdf, state)
    return state


def _draw_paper1_compact_section_heading(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    title: str,
    timing: str,
) -> None:
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawCentredString(289, 720, title)
    pdf.setFont(FONT, 10)
    pdf.drawCentredString(289, 698, timing)
    pdf.drawCentredString(
        289,
        680,
        "Enter your answers in the supplied Electronic Answer Document.",
    )
    state.y = 650


def _render_paper1_partial_question(
    pdf: canvas.Canvas,
    question: Question,
    parts: list[QuestionPart],
    state: _QuestionRenderState,
    *,
    allow_current_page: bool = False,
) -> _QuestionRenderState:
    partial = question.model_copy(update={"parts": parts})
    return _render_question(
        pdf,
        partial,
        state,
        show_answer_space=False,
        allow_current_page=allow_current_page,
    )


def _draw_trace_response_grid(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    *,
    rows: int,
) -> None:
    state.y -= 10
    values = [
        ["Step", "Current vertex", "Visited", "Recursive call / result"],
        *[[str(index), "", "", ""] for index in range(1, rows + 1)],
    ]
    stimulus = Stimulus(
        kind="table",
        title="Trace table",
        headers=values[0],
        rows=values[1:],
    )
    state.y = _draw_table(pdf, stimulus, 92, state.y)


def _draw_paper1_trace_support_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question: Question,
) -> None:
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(289, 710, f"Question {question.number} trace table")
    state.y = 680
    if question.stimulus:
        state = _render_stimulus(pdf, question.stimulus, state)
    state.y -= 12
    _draw_trace_response_grid(pdf, state, rows=14)


def _draw_complexity_support_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question: Question,
) -> None:
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(289, 710, f"Information for Question {question.number}")
    pdf.setFont(FONT, 10)
    pdf.drawString(82, 676, "Record timing results for both algorithms before reaching a conclusion.")
    rows = [
        ["Input size", "Algorithm X time", "Algorithm Y time", "Selected algorithm"],
        ["100", "", "", ""],
        ["1 000", "", "", ""],
        ["10 000", "", "", ""],
        ["100 000", "", "", ""],
    ]
    stimulus = Stimulus(kind="table", title="", headers=rows[0], rows=rows[1:])
    state.y = _draw_table(pdf, stimulus, 82, 650)
    pdf.setFont(FONT, 9)
    pdf.drawString(
        82,
        state.y - 12,
        "Use repeated trials and explain any anomalous result in the Electronic Answer Document.",
    )


def _draw_skeleton_program_support_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question: Question,
) -> None:
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(289, 710, "Skeleton Program information")
    pdf.setFont(FONT, 10)
    y = 678
    for line in _wrap(question.stem, 82):
        pdf.drawString(82, y, line)
        y -= 14
    rows = [
        ["Command", "Required validation", "Expected action"],
        ["ADD", "Unused identifier; valid category; value 0–100", "Append one record"],
        ["REPORT", "At least one valid record", "Print category totals"],
        ["QUIT", "No parameters", "End without changing data"],
    ]
    stimulus = Stimulus(kind="table", title="", headers=rows[0], rows=rows[1:])
    state.y = _draw_table(pdf, stimulus, 82, y - 14)
    pdf.setFont(FONT_MONO, 9)
    pdf.drawString(82, state.y - 16, "Input format: COMMAND,param1,param2,param3")


def _draw_paper1_support_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    question: Question,
) -> None:
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(289, 708, f"Information for Question {question.number}")
    state.y = 676
    pdf.setFont(FONT, 9.5)
    for line in _wrap(question.stem, 82):
        pdf.drawString(82, state.y, line)
        state.y -= 14
    if question.stimulus:
        state.y -= 8
        state = _render_stimulus(pdf, question.stimulus, state)
    pdf.setFont(FONT, 9)
    state.y -= 12
    pdf.drawString(82, state.y, "This information is repeated so that it remains visible while you complete the task.")


def _draw_intentionally_blank_page(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    *,
    do_not_write: bool = False,
) -> None:
    draw_exam_page(
        pdf,
        ExamPageProfile(
            board="aqa",
            code=state.blueprint.paper_code,
            heading="There are no questions printed on this page",
            variant="blank",
            do_not_write=do_not_write,
        ),
        width=AQA_A4[0],
        height=AQA_A4[1],
        font=FONT,
        bold_font=FONT_BOLD,
        page_number=0,
    )
    state.y = 380


def render_mark_scheme(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _set_document_metadata(pdf, blueprint, "Mark scheme")
    _mark_scheme_cover(pdf, blueprint)
    pdf.showPage()
    _mark_scheme_intro(pdf, 2, blueprint)
    pdf.showPage()
    _mark_scheme_levels(pdf, 3, blueprint)
    pdf.showPage()
    if blueprint.assessment_kind == "question-bank":
        _render_generic_mark_scheme_pages(pdf, blueprint, first_page=4)
        pdf.save()
        return
    _mark_scheme_annotations(pdf, 4, blueprint)
    pdf.showPage()
    _mark_scheme_examiner_notes(pdf, 5, blueprint)
    pdf.showPage()
    if blueprint.paper_number == "1":
        _render_paper1_mark_scheme_pages(pdf, blueprint)
        pdf.save()
        return
    if blueprint.paper_number == "2":
        _render_paper2_mark_scheme_pages(pdf, blueprint)
        pdf.save()
        return
    _render_generic_mark_scheme_pages(pdf, blueprint, first_page=6)
    pdf.save()


def _render_generic_mark_scheme_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    *,
    first_page: int,
) -> None:
    page = first_page
    y = _mark_scheme_table_header(pdf, page, blueprint)
    for question_index, question in enumerate(blueprint.questions):
        if question_index:
            pdf.showPage()
            page += 1
            y = _mark_scheme_table_header(pdf, page, blueprint)
        for part in question.parts:
            needed = 56 + 15 * (len(part.marking.points) + len(part.marking.accept) + len(part.marking.reject) + len(part.marking.levels))
            if y - needed < 70:
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
            y = _render_mark_scheme_part(pdf, question, part, y)


def _set_document_metadata(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    role: str,
) -> None:
    pdf.setTitle(f"{blueprint.paper_code} {blueprint.title} — {role}")
    pdf.setAuthor("Paper creator")
    pdf.setCreator("Paper creator")
    pdf.setSubject(
        "Independent A-level Computer Science practice material"
    )


def _render_paper1_mark_scheme_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
) -> None:
    if [question.number for question in blueprint.questions] != list(range(1, 13)):
        raise ValueError("Paper 1 mark scheme requires Questions 1 to 12")

    page = 6
    y = _mark_scheme_table_header(pdf, page, blueprint)
    for question in blueprint.questions:
        for part in question.parts:
            needed = _mark_scheme_part_height(part) + _mark_scheme_artifact_height(question, part)
            if y - needed < 70:
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
            if y - needed < 70:
                raise ValueError(
                    f"Question {question.number}.{part.label} marking guidance exceeds a page"
                )
            y = _render_mark_scheme_part(pdf, question, part, y)

    question_by_number = {question.number: question for question in blueprint.questions}
    for question_number in (4, 9, 10, 11, 12):
        pdf.showPage()
        page += 1
        _draw_paper1_reference_solution_page(
            pdf, blueprint, question_by_number[question_number], page,
        )


def _mark_scheme_artifact_height(question: Question, part: QuestionPart) -> float:
    if question.style_id == "recursive_graph_traversal" and part.label == "3":
        return 425
    if question.style_id == "recursive_graph_traversal" and part.label == "5":
        return 192
    if question.style_id == "finite_state_machine" and part.label == "1":
        return 124
    if part.marking.ao == "AO3" and part.marks >= 7:
        return 23 + (4 * 49 if part.marks >= 12 else 3 * 55) + 22
    return 0


def _draw_paper1_reference_solution_page(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    question: Question,
    page: int,
) -> None:
    _ms_header(pdf, page, blueprint)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(43, 745, f"Question {question.number:02d}: Example Python 3 solution")
    y = 715
    pdf.setFont(FONT, 10)
    for line in _wrap(question.parts[0].prompt, 88):
        pdf.drawString(55, y, line)
        y -= 14
    y -= 10
    code = _paper1_reference_code(question.number, record_name=blueprint.program_record_name)
    pdf.setFont(FONT_MONO, 10)
    for line in code.splitlines():
        pdf.drawString(62, y, line[:86])
        y -= 13


def _render_paper2_mark_scheme_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
) -> None:
    if [question.number for question in blueprint.questions] != list(range(1, 15)):
        raise ValueError("Paper 2 mark scheme requires Questions 1 to 14")

    page = 6
    y = _mark_scheme_table_header(pdf, page, blueprint)
    for question in blueprint.questions:
        # Match the board's typography and table geometry, not an unrelated
        # paper's page count. Padding that count repeats already awarded points.
        for part in question.parts:
            needed = _mark_scheme_part_height(part)
            if y - needed < 70:
                if part.marking.levels:
                    points_only = part.model_copy(
                        update={
                            "marking": part.marking.model_copy(
                                update={"levels": []}
                            )
                        }
                    )
                    levels_only = part.model_copy(
                        update={
                            "label": "",
                            "marking": part.marking.model_copy(
                                update={
                                    "points": [],
                                    "accept": [],
                                    "reject": [],
                                }
                            ),
                        }
                    )
                    if (
                        y - _mark_scheme_part_height(points_only) >= 70
                        and 672 - _mark_scheme_part_height(levels_only) >= 70
                    ):
                        y = _render_mark_scheme_part(pdf, question, points_only, y)
                        pdf.showPage()
                        page += 1
                        y = _mark_scheme_table_header(pdf, page, blueprint)
                        y = _render_mark_scheme_part(
                            pdf,
                            question,
                            levels_only,
                            y,
                            show_total=False,
                            heading="Extended response levels",
                        )
                        continue
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
            if y - needed < 70:
                raise ValueError(
                    f"Question {question.number}.{part.label} marking guidance "
                    "exceeds a page; shorten it or separate its levels guidance"
                )
            y = _render_mark_scheme_part(pdf, question, part, y)


def _mark_scheme_part_height(part: QuestionPart) -> float:
    wrapped_lines = 1
    wrapped_lines += sum(len(_wrap_scheme_text(point)) for point in printed_credit_points(part.marking.model_dump(mode="json")))
    wrapped_lines += sum(len(_wrap_scheme_text(f"A. {item}")) for item in part.marking.accept)
    wrapped_lines += sum(len(_wrap_scheme_text(f"R. {item}")) for item in part.marking.reject)
    wrapped_lines += sum(len(_wrap_scheme_text(item)) for item in part.marking.levels)
    return 38 + 15 * wrapped_lines


class _QuestionRenderState:
    def __init__(self, page: int, y: float, blueprint: PaperBlueprint) -> None:
        self.page = page
        self.y = y
        self.blueprint = blueprint


def _cover_page(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT_BOLD, 27)
    pdf.drawString(40, 768, "PAPER")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(40, 752, "CREATOR")
    pdf.setFont(FONT, 11)
    candidate_instruction = (
        "Complete the candidate details and save all electronic work clearly."
        if blueprint.delivery_mode == "on-screen"
        else "Please write clearly in block capitals."
    )
    pdf.rect(40, 564, 504, 166, stroke=1, fill=0)
    pdf.drawString(55, 708, candidate_instruction)
    _candidate_fields(pdf)

    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(40, 535, "A-level")
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(40, 501, "COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 16)
    document_title = (
        "Topic Question Bank"
        if blueprint.assessment_kind == "question-bank"
        else f"Paper {blueprint.paper_number}"
    )
    pdf.drawString(40, 476, document_title)
    pdf.setLineWidth(2)
    pdf.line(40, 455, 545, 455)
    pdf.setFont(FONT, 11)
    pdf.drawString(40, 438, _formatted_exam_date(blueprint))
    pdf.drawString(231, 438, blueprint.session)
    hours, minutes = divmod(blueprint.duration_minutes, 60)
    if hours and minutes:
        duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minutes"
    elif hours:
        duration = f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        duration = f"{minutes} minutes"
    pdf.drawString(306, 438, f"Time allowed: {duration}")

    y = 410
    material_lines = ["For this paper you must have:"] + [f"\u2022 {item}." for item in blueprint.materials]
    y = _cover_section(pdf, y, "Materials", material_lines)
    response_instruction = (
        "\u2022 Enter written answers in the supplied Electronic Answer Document and complete programming tasks in your development environment."
        if blueprint.delivery_mode == "on-screen"
        else "\u2022 You must answer the questions in the spaces provided. Do not write outside the box around each page or on blank pages."
    )
    extra_space_instruction = (
        "\u2022 Save your work frequently and use the question number in every response."
        if blueprint.delivery_mode == "on-screen"
        else "\u2022 If you need extra space for your answer(s), use the lined pages at the end of this book. Write the question number against your answer(s)."
    )
    y = _cover_section(
        pdf,
        y - 8,
        "Instructions",
        [
            "\u2022 Use black ink or black ball-point pen.",
            "\u2022 Fill in the boxes at the top of this page.",
            "\u2022 Answer all questions.",
            response_instruction,
            extra_space_instruction,
            "\u2022 Do all rough work in this book. Cross through any work you do not want to be marked.",
        ],
    )
    y = _cover_section(pdf, y - 8, "Information", ["\u2022 The marks for questions are shown in brackets.", f"\u2022 The maximum mark for this paper is {blueprint.total_marks}."])
    advice = (
        [
            "\u2022 Run and test programming answers in Python 3.",
            "\u2022 Keep an unchanged copy of the supplied Skeleton Program.",
            "\u2022 Include concise test evidence where a programming question asks for it.",
        ]
        if blueprint.delivery_mode == "on-screen"
        else [
            "\u2022 In some questions you are required to indicate your answer by completely shading a lozenge alongside the appropriate answer.",
            "\u2022 If you want to change your answer you must cross out your original answer.",
            "\u2022 If you wish to return to an answer previously crossed out, ring the answer you now wish to select.",
        ]
    )
    _cover_section(pdf, y - 8, "Advice", advice)

    _examiner_table(pdf, len(blueprint.questions), y_top=390)
    draw_barcode(
        pdf,
        x=52,
        y=17,
        caption="01",
        style=AQA_CS_FOOTER_BARCODE,
    )
    pdf.setFont(FONT_BOLD, 8)
    pdf.drawString(130, 35, f"*PRACTICE{blueprint.paper_code.replace('/', '')}01*")
    pdf.setFont(FONT, 9)
    pdf.drawRightString(535, 35, blueprint.paper_code)


def _candidate_fields(pdf: canvas.Canvas) -> None:
    pdf.setFont(FONT, 10)
    pdf.drawString(55, 680, "Centre number")
    pdf.drawString(312, 680, "Candidate number")
    _small_boxes(pdf, 139, 650, 5)
    _small_boxes(pdf, 414, 650, 4)
    for label, y in (
        ("Surname", 638),
        ("Forename(s)", 612),
        ("Candidate signature", 586),
    ):
        pdf.drawString(55, y, label)
        pdf.line(166, y - 2, 528, y - 2)
    pdf.setFont(FONT, 8.5)
    pdf.drawString(166, 568, "I declare this is my own work.")


def _small_boxes(pdf: canvas.Canvas, x: float, y: float, count: int) -> None:
    for index in range(count):
        pdf.rect(x + index * 28.5, y, 28.5, 28, stroke=1, fill=0)


def _cover_section(pdf: canvas.Canvas, y: float, heading: str, lines: list[str]) -> float:
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(40, y, heading)
    y -= 16
    pdf.setFont(FONT, 10)
    for line in lines:
        for wrapped in _wrap(line, 82):
            pdf.drawString(40, y, wrapped)
            y -= 14
    return y


def _examiner_table(pdf: canvas.Canvas, count: int, y_top: float = 470) -> None:
    x = 450
    y = y_top
    row_height = 18
    header_height = 22
    bottom = y - row_height * (count + 2)
    pdf.setFillColor(colors.HexColor("#dddddd"))
    pdf.rect(x, y, 100, header_height, stroke=1, fill=1)
    pdf.rect(x + 50, bottom, 50, y - bottom, stroke=0, fill=1)
    pdf.setFillColor(colors.black)
    pdf.rect(x, bottom, 100, y - bottom, stroke=1, fill=0)
    pdf.line(x + 50, bottom, x + 50, y)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawCentredString(x + 50, y + 7, "For Examiner's Use")
    pdf.line(x, y - row_height, x + 100, y - row_height)
    pdf.drawString(x + 7, y - 13, "Question")
    pdf.drawString(x + 59, y - 13, "Mark")
    pdf.setFont(FONT, 9)
    for index in range(1, count + 1):
        row_y = y - row_height * (index + 1)
        pdf.line(x, row_y, x + 100, row_y)
        pdf.drawCentredString(x + 25, row_y + 5, str(index))
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(x + 8, bottom + 5, "TOTAL")


def _draw_question_page_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT, 10)
    pdf.drawCentredString(297, 805, str(page))
    pdf.setFont(FONT, 7)
    pdf.drawCentredString(564, 780, "Do not write")
    pdf.drawCentredString(564, 769, "outside the")
    pdf.drawCentredString(564, 758, "box")
    pdf.setLineWidth(0.7)
    pdf.rect(39, 76, 500, 713, stroke=1, fill=0)
    pdf.line(39, 751, 539, 751)
    if page == 2:
        pdf.setFont(FONT, 11)
        instruction = (
            "Use the Electronic Answer Document and development environment."
            if blueprint.delivery_mode == "on-screen"
            else "Answer all questions."
        )
        pdf.drawCentredString(289, 768, instruction)
    pdf.setFont(FONT, 7)
    draw_barcode(
        pdf,
        x=52,
        y=17,
        caption=f"{page:02d}",
        style=AQA_CS_FOOTER_BARCODE,
    )
    pdf.drawRightString(539, 28, f"Paper Creator / {blueprint.paper_code}")


def _render_question(
    pdf: canvas.Canvas,
    question: Question,
    state: _QuestionRenderState,
    *,
    show_answer_space: bool,
    allow_current_page: bool = False,
) -> _QuestionRenderState:
    if state.y < 520 and not allow_current_page:
        state = _new_question_page(pdf, state)
    state = _ensure_space(pdf, state, 80)
    _draw_question_ref(pdf, 52, state.y + 1, question.number)
    pdf.setFont(FONT, 11)
    for line in _wrap(question.stem, 78):
        pdf.drawString(118, state.y, line)
        state.y -= 14
    state.y -= 8
    if question.stimulus:
        state = _render_stimulus(pdf, question.stimulus, state)
        state.y -= 8
    single_part = len(question.parts) == 1
    for part in question.parts:
        state = _render_part(
            pdf,
            question,
            part,
            state,
            draw_reference=not single_part,
            show_answer_space=show_answer_space,
        )
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
    show_answer_space: bool = True,
) -> _QuestionRenderState:
    line_count = _answer_line_count(part)
    state = _ensure_space(pdf, state, 92)
    if draw_reference:
        _draw_question_ref(pdf, 52, state.y + 1, question.number, part.label)
    pdf.setFont(FONT, 11)
    prompt_y = state.y
    wrap_width = 58 if draw_reference else 70
    for line in _wrap(part.prompt.replace("{q}", f"{question.number:02d}"), wrap_width):
        pdf.drawString(118, prompt_y, line)
        prompt_y -= 14
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawRightString(534, prompt_y + 14, f"[{part.marks} mark{'s' if part.marks != 1 else ''}]")
    state.y = prompt_y - 12
    response_is_in_stimulus = (
        question.style_id == "software_classification" and part.label == "1"
    )
    if part.options:
        for option in part.options:
            _lozenge(pdf, 124, state.y + 1)
            pdf.setFont(FONT_BOLD, 10)
            pdf.drawString(140, state.y, option.label)
            pdf.setFont(FONT, 10)
            pdf.drawString(160, state.y, option.text)
            state.y -= 20
    elif response_is_in_stimulus:
        state.y -= 8
    elif not show_answer_space:
        pdf.setFont(FONT, 7.4)
        pdf.drawString(
            118,
            state.y,
            "Respond in the Electronic Answer Document or development environment.",
        )
        state.y -= 12
    elif part.answer_unit:
        state = _answer_lines_paginated(pdf, state, line_count)
        pdf.setFont(FONT, 10)
        pdf.drawString(338, state.y + LINE_GAP, "Answer")
        pdf.line(382, state.y + LINE_GAP - 2, 455, state.y + LINE_GAP - 2)
        pdf.drawString(460, state.y + LINE_GAP, part.answer_unit)
    else:
        state = _answer_lines_paginated(pdf, state, line_count)
    state.y -= 6 if not show_answer_space else 14
    return state


def candidate_stimulus_data(stimulus: Stimulus | None) -> dict[str, object]:
    """Describe visible figure content for text-only independent solvers."""
    if stimulus is None:
        return {}
    data = stimulus.model_dump(mode="json")
    if stimulus.sql_contract is not None:
        data["source_id"] = stimulus.sql_contract.source_id
        data["code"] = render_sql_schema(stimulus.sql_contract)
    if stimulus.kind == "classification":
        if not stimulus.lines:
            raise ValueError("classification figure lacks candidate-visible maintenance examples")
        first, second, *_ = stimulus.diagram.split("|")
        data.pop("diagram", None)
        data["links"] = [
            {"parent": parent, "child": child} for parent, child in [
                ("Software", "1"), ("Software", "System software"),
                ("1", first), ("1", second),
                ("System software", "2"), ("System software", "Translators"),
            ]
        ]
    elif stimulus.kind == "network":
        data.pop("diagram", None)
        data["links"] = [
            ["Client", "Switch"], ["Laptop", "Switch"],
            ["Switch", "Router"], ["Router", "Server"],
        ]
    elif stimulus.kind == "fsm":
        data.pop("diagram", None)
        data.update({
            "start_state": "S0", "accepting_states": ["S1"],
            "transitions": [["S0", "1", "S1"], ["S1", "0", "S2"],
                            ["S2", "0", "S1"], ["S1", "1", "S1"], ["S2", "1", "S2"]],
        })
    elif stimulus.kind == "optical":
        data["visible_labels"] = ["laser", "spiral track", "pits and lands"]
    if stimulus.kind in {"table", "bitgrid", "packet", "truth_table", "fsm"}:
        data["headers"] = [cell[:34] for cell in stimulus.headers]
        data["rows"] = [[cell[:34] for cell in row] for row in stimulus.rows]
    return data


def _render_stimulus(pdf: canvas.Canvas, stimulus: Stimulus, state: _QuestionRenderState) -> _QuestionRenderState:
    state = _ensure_space(pdf, state, 110)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y, stimulus.title)
    state.y -= 18
    if stimulus.kind in {"table", "bitgrid", "packet", "truth_table"}:
        state.y = _draw_table(pdf, stimulus, 118, state.y)
    elif stimulus.kind == "code":
        code = (
            render_sql_schema(stimulus.sql_contract)
            if stimulus.sql_contract is not None
            else stimulus.code
        )
        state.y = _draw_code_box(pdf, code, 118, state.y)
    elif stimulus.kind == "logic":
        state.y = _draw_logic_box(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "erd":
        state.y = _draw_erd(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "network":
        state.y = _draw_network_diagram(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "classification":
        state.y = _draw_classification_diagram(pdf, stimulus, 118, state.y)
    elif stimulus.kind == "optical":
        state.y = _draw_optical_diagram(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "fsm":
        state.y = _draw_fsm_stimulus(pdf, stimulus, 118, state.y)
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


def _draw_fsm_stimulus(
    pdf: canvas.Canvas,
    stimulus: Stimulus,
    x: float,
    y: float,
) -> float:
    state_y = y - 54
    states = {
        "S0": (x + 56, state_y),
        "S1": (x + 195, state_y),
        "S2": (x + 334, state_y),
    }
    _draw_arrow(pdf, x + 2, state_y, x + 34, state_y)
    _draw_arrow(pdf, x + 80, state_y + 8, x + 171, state_y + 8, "1")
    _draw_arrow(pdf, x + 219, state_y + 8, x + 310, state_y + 8, "0")
    _draw_arrow(pdf, x + 310, state_y - 8, x + 219, state_y - 8, "0")

    for label, (cx, cy) in states.items():
        pdf.circle(cx, cy, 22, stroke=1, fill=0)
        if label == "S1":
            pdf.circle(cx, cy, 18, stroke=1, fill=0)
        pdf.setFont(FONT_BOLD, 9)
        pdf.drawCentredString(cx, cy - 3, label)

    for label, cx in (("1", states["S1"][0]), ("1", states["S2"][0])):
        pdf.arc(cx - 23, state_y + 8, cx + 23, state_y + 48, 10, 160)
        pdf.setFont(FONT, 8)
        pdf.drawCentredString(cx, state_y + 51, label)
    pdf.setFont(FONT, 8)
    pdf.drawCentredString(x + 195, state_y - 34, "Figure 6")

    return _draw_table(pdf, stimulus, x, state_y - 50)


def _draw_arrow(
    pdf: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: str = "",
) -> None:
    pdf.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    for offset in (-0.5, 0.5):
        pdf.line(
            x2,
            y2,
            x2 - 8 * math.cos(angle + offset),
            y2 - 8 * math.sin(angle + offset),
        )
    if label:
        pdf.setFont(FONT, 8)
        pdf.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 8, label)


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
    gates = _logic_gate_names(expression)
    first_gate = gates[0] if gates else "AND"
    second_gate = gates[1] if len(gates) > 1 else first_gate
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
    base_gate = {"NOR": "OR", "NAND": "AND"}.get(label, label)
    if base_gate == "NOT":
        pdf.line(x, bottom, x, top)
        pdf.line(x, top, x + 48, y + 9)
        pdf.line(x + 48, y + 9, x, bottom)
        pdf.circle(x + 53, y + 9, 5, stroke=1, fill=0)
    elif base_gate == "OR":
        pdf.bezier(x + 2, bottom, x + 20, y + 2, x + 20, y + 16, x + 2, top)
        pdf.bezier(x + 2, top, x + 44, top, x + 54, y + 18, x + 54, y + 9)
        pdf.bezier(x + 54, y + 9, x + 44, bottom, x + 2, bottom, x + 2, bottom)
    elif base_gate == "XOR":
        pdf.bezier(x - 4, bottom, x + 14, y + 2, x + 14, y + 16, x - 4, top)
        pdf.bezier(x + 2, bottom, x + 20, y + 2, x + 20, y + 16, x + 2, top)
        pdf.bezier(x + 2, top, x + 44, top, x + 54, y + 18, x + 54, y + 9)
        pdf.bezier(x + 54, y + 9, x + 44, bottom, x + 2, bottom, x + 2, bottom)
    else:
        pdf.line(x, bottom, x, top)
        pdf.bezier(x, top, x + 58, top, x + 58, bottom, x, bottom)
    if label in {"NAND", "NOR"}:
        pdf.circle(x + 59, y + 9, 5, stroke=1, fill=0)


def _logic_gate_names(expression: str) -> list[str]:
    symbols = {
        "⊼": "NAND",
        "⊽": "NOR",
        "⊕": "XOR",
        "̅": "NOT",
        "¬": "NOT",
        "·": "AND",
        ".": "AND",
        "+": "OR",
    }
    return [symbols[character] for character in expression if character in symbols]


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


def _draw_classification_diagram(
    pdf: canvas.Canvas,
    stimulus: Stimulus,
    x: float,
    y: float,
) -> float:
    data = candidate_stimulus_data(stimulus)
    application_one, application_two = data["links"][2]["child"], data["links"][3]["child"]
    boxes = {
        "Software": (x, y - 104, 76, 34),
        "1": (x + 110, y - 55, 112, 34),
        "System software": (x + 110, y - 155, 112, 34),
        application_one: (x + 258, y - 26, 112, 34),
        application_two: (x + 258, y - 70, 112, 34),
        "2": (x + 258, y - 126, 112, 34),
        "Translators": (x + 258, y - 170, 112, 34),
    }
    links = data["links"]
    for link in links:
        start, end = link["parent"], link["child"]
        sx, sy, sw, sh = boxes[start]
        ex, ey, _ew, eh = boxes[end]
        middle = (sx + sw + ex) / 2
        pdf.line(sx + sw, sy + sh / 2, middle, sy + sh / 2)
        pdf.line(middle, sy + sh / 2, middle, ey + eh / 2)
        pdf.line(middle, ey + eh / 2, ex, ey + eh / 2)
        pdf.line(ex - 4, ey + eh / 2 + 3, ex, ey + eh / 2)
        pdf.line(ex - 4, ey + eh / 2 - 3, ex, ey + eh / 2)
    for label, (bx, by, width, height) in boxes.items():
        pdf.rect(bx, by, width, height, stroke=1, fill=0)
        pdf.setFont(FONT_BOLD if label in {"Software", "1", "System software"} else FONT, 9.5)
        for line_index, line in enumerate(_wrap(label, 19)):
            pdf.drawCentredString(
                bx + width / 2,
                by + height / 2 + 3 - line_index * 10,
                line,
            )
    note_y = y - 190
    pdf.setFont(FONT, 9)
    for note in data["lines"]:
        for line in _wrap(note, 82):
            pdf.drawString(x, note_y, line)
            note_y -= 12
    return note_y - 12


def _draw_optical_diagram(
    pdf: canvas.Canvas,
    diagram: str,
    x: float,
    y: float,
) -> float:
    pdf.setFont(FONT, 8.5)
    pdf.drawString(x + 10, y - 16, f"Optical medium for {diagram}")
    pdf.circle(x + 190, y - 86, 66, stroke=1, fill=0)
    pdf.circle(x + 190, y - 86, 12, stroke=1, fill=0)
    pdf.arc(x + 138, y - 132, x + 242, y - 40, 20, 290)
    pdf.arc(x + 150, y - 120, x + 230, y - 52, 20, 290)
    pdf.line(x + 30, y - 154, x + 145, y - 104)
    pdf.line(x + 30, y - 154, x + 145, y - 73)
    pdf.setFont(FONT, 8)
    pdf.drawString(x + 2, y - 164, "laser")
    pdf.drawString(x + 250, y - 68, "spiral track")
    pdf.drawString(x + 250, y - 90, "pits and lands")
    return y - 182


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
    _draw_question_page_header(pdf, state.page, state.blueprint)
    return state


def _new_question_page(pdf: canvas.Canvas, state: _QuestionRenderState) -> _QuestionRenderState:
    pdf.setFont(FONT, 9)
    pdf.drawRightString(500, 62, "Turn over >")
    pdf.showPage()
    state.page += 1
    state.y = 724
    _draw_question_page_header(pdf, state.page, state.blueprint)
    return state


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


def _answer_lines_paginated(pdf: canvas.Canvas, state: _QuestionRenderState, count: int) -> _QuestionRenderState:
    remaining = count
    while remaining:
        available = int((state.y - (BOTTOM + 60)) // LINE_GAP)
        if available <= 0:
            state = _new_question_page(pdf, state)
            continue
        lines = min(remaining, available)
        draw_solid_answer_rules(
            pdf,
            first_y=state.y,
            count=lines,
            style=AQA_CS_ANSWER_RULES,
        )
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


def _draw_extra_answer_page(
    pdf: canvas.Canvas,
    page: int,
    blueprint: PaperBlueprint,
    *,
    legal_notice: bool,
) -> None:
    pdf.showPage()
    _draw_question_page_header(pdf, page, blueprint)
    draw_exam_page(
        pdf,
        ExamPageProfile(
            board="aqa",
            code=blueprint.paper_code,
            heading="Additional page, if required",
            variant="additional",
            legal_notice=legal_notice,
        ),
        width=AQA_A4[0],
        height=AQA_A4[1],
        font=FONT,
        bold_font=FONT_BOLD,
        page_number=0,
        include_footer=True,
    )


def _mark_scheme_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    draw_mark_scheme_cover(
        pdf,
        CoverProfile(
            board="aqa",
            subject="Computer Science",
            code=blueprint.paper_code,
            paper_title=(
                "Topic Question Bank"
                if blueprint.assessment_kind == "question-bank"
                else f"Paper {blueprint.paper_number}"
            ),
            duration=(
                f"{blueprint.duration_minutes // 60} hours "
                f"{blueprint.duration_minutes % 60} minutes"
            ),
            total_marks=blueprint.total_marks,
        ),
        width=AQA_A4[0],
        height=AQA_A4[1],
        font=FONT,
        bold_font=FONT_BOLD,
    )


def _mark_scheme_intro(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    _ms_header(pdf, page, blueprint)
    y = 754
    pdf.setFont(FONT, 10)
    paragraphs = [
        (
            "This independent mark scheme supports consistent marking of Paper Creator's A-level Computer Science topic question bank."
            if blueprint.assessment_kind == "question-bank"
            else f"This independent mark scheme supports consistent marking of Paper Creator's A-level Computer Science Paper {blueprint.paper_number} practice assessment."
        ),
        "Apply the guidance positively. Award credit for what a response demonstrates, and do not deduct marks for an omission unless the question or guidance explicitly requires that element.",
        "The listed answers describe responses that are likely to earn credit. They are not exhaustive. Credit a technically correct alternative when it answers the precise question and is consistent with the stated scenario.",
        "Judge each response against the published marking guidance rather than against another candidate's work. The same standard must be applied throughout the script.",
        "Where a point is followed by an explanation, award the explanation mark only when the reasoning is technically valid and linked to the point made. Do not award the same mark twice for equivalent wording.",
        "Accept established technical terminology, unambiguous pseudocode and logically equivalent expressions. Minor spelling or grammatical errors should not prevent credit when the intended technical meaning is clear.",
        "For calculations, accept a correct answer obtained from valid working. If an earlier arithmetic error is carried forward consistently, award subsequent method marks where the method remains valid.",
        "For context-based questions, award application marks only when the response uses the named system, data or stakeholder to establish the relevant consequence. A generic statement that could apply unchanged to any scenario is not contextual application.",
        "For programming and algorithm questions, judge the logic of the whole response. Equivalent control structures, identifiers and data representations should be credited when they preserve the required behaviour.",
        "For diagram and table questions, labels must be sufficiently clear to establish the intended relationship. Neatness is not assessed unless ambiguity prevents the response from being interpreted.",
        "A response that contradicts an otherwise valid point cannot receive credit for that point. Ignore additional material only where it does not undermine or contradict the credited answer.",
        "This document is independent practice material. It is not produced, endorsed or approved by an examination board.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 92):
            pdf.drawString(55, y, line)
            y -= 14
        y -= 10


def _mark_scheme_levels(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    _ms_header(pdf, page, blueprint)
    y = 754
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, y, "Level of response marking instructions")
    y -= 26
    pdf.setFont(FONT, 10)
    paragraphs = [
        "Level-of-response questions are assessed holistically. Each level describes the quality of knowledge, technical accuracy, analysis, application and judgement normally expected within that band.",
        "Begin with the lowest descriptor and work upwards. Select the highest level for which the response meets the descriptor as a whole; a response does not need to satisfy every phrase perfectly.",
        "Read the complete response before assigning a level. Isolated strengths or weaknesses should not outweigh the overall quality and consistency of the answer.",
        "A response may contain characteristics from adjacent levels. Use best fit: decide which descriptor most closely represents the answer, then use the mark within that level to reflect how securely it is met.",
        "Use the top of a level when the response meets the descriptor consistently, the middle when it meets it reasonably well, and the bottom when it only just satisfies the descriptor.",
        "Accurate knowledge alone is insufficient for the highest level where the question requires analysis or evaluation. The response must use that knowledge to address the particular issue or scenario.",
        "Developed analysis contains connected reasoning: a technical point is explained, its consequence is established and the consequence is related to the question.",
        "A balanced response considers material arguments on more than one side. Balance does not require equal space, but competing considerations must be treated seriously.",
        "A justified conclusion follows from the reasoning and evidence in the response. A conclusion that merely repeats the question or states an unsupported preference is not developed evaluation.",
        "Indicative content suggests valid routes through the question. It is not a checklist, and candidates may reach the highest level using different technically sound material.",
        "Do not cap a response because it uses terminology or examples different from those in the indicative content. Apply a cap only where the level descriptor itself is not met.",
        "When a response is on a boundary, consider precision, depth, relevance to the scenario and the extent to which its reasoning remains coherent from start to finish.",
        "If no part of a response is creditworthy, award zero. A blank response should be recorded as not attempted rather than as an attempted response worth zero.",
    ]
    for paragraph in paragraphs:
        for line in _wrap(paragraph, 94):
            pdf.drawString(55, y, line)
            y -= 14
        y -= 10


def _mark_scheme_annotations(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    _ms_header(pdf, page, blueprint)
    y = 754
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
        ("ECF", "error carried forward"),
        ("MAX", "maximum mark available"),
        ("AO1", "knowledge and understanding"),
        ("AO2", "application and analysis"),
        ("AO3", "programming or practical problem solving"),
    ]
    for code, meaning in rows:
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(70, y, code)
        pdf.setFont(FONT, 10)
        pdf.drawString(120, y, meaning)
        y -= 22
    y -= 10
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(55, y, "Using the guidance")
    y -= 22
    pdf.setFont(FONT, 10)
    notes = [
        "A semicolon separates independently creditworthy points.",
        "Alternatives separated by // are different ways of earning the same mark.",
        "An acceptable answer illustrates wording that may be credited; it does not exclude an equivalent response.",
        "A rejected answer identifies a specific misconception or an answer that does not meet the question.",
        "Where a maximum is stated, stop awarding marks when that maximum has been reached.",
        "Apply error carried forward only when the later method is valid for the candidate's earlier result.",
    ]
    for note in notes:
        for line in _wrap(note, 88):
            pdf.drawString(70, y, line)
            y -= 14
        y -= 4


def _mark_scheme_examiner_notes(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    _ms_header(pdf, page, blueprint)
    y = 754
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


def _mark_scheme_table_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> float:
    _ms_header(pdf, page, blueprint)
    y = AQA_A4[1] - 85
    pdf.setFont(FONT_BOLD, 11)
    pdf.rect(43, y - 29, 513, 29, stroke=1, fill=0)
    for x in (71, 100, 511):
        pdf.line(x, y - 29, x, y)
    pdf.drawString(49, y - 19, "Qu")
    pdf.drawString(80, y - 19, "Pt")
    pdf.drawCentredString(305, y - 19, "Marking guidance")
    pdf.drawCentredString(533, y - 12, "Total")
    pdf.drawCentredString(533, y - 24, "marks")
    return y - 44


def _render_mark_scheme_part(
    pdf: canvas.Canvas,
    question: Question,
    part: QuestionPart,
    y: float,
    *,
    show_total: bool = True,
    heading: str | None = None,
    include_answer_artifact: bool = True,
) -> float:
    start_y = y
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(49, y, f"{question.number:02d}")
    pdf.drawString(80, y, part.label)
    if show_total:
        pdf.drawRightString(548, y, str(part.marks))
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(105, y, heading or f"All marks {part.marking.ao}")
    y -= 15
    pdf.setFont(FONT, 11)
    for point in printed_credit_points(part.marking.model_dump(mode="json")):
        for line in _wrap_scheme_text(point):
            _draw_scheme_text(pdf, 105, y, line)
            y -= 15
    for item in part.marking.accept:
        for line in _wrap_scheme_text(f"A. {item}"):
            _draw_scheme_text(pdf, 105, y, line)
            y -= 15
    for item in part.marking.reject:
        for line in _wrap_scheme_text(f"R. {item}"):
            _draw_scheme_text(pdf, 105, y, line)
            y -= 15
    for item in part.marking.levels:
        for line in _wrap_scheme_text(item):
            pdf.drawString(105, y, line)
            y -= 15
    if include_answer_artifact:
        y = _draw_mark_scheme_answer_artifact(pdf, question, part, y)
    bottom = y - 5
    top = start_y + 10
    pdf.rect(43, bottom, 513, top - bottom, stroke=1, fill=0)
    for x in (71, 100, 511):
        pdf.line(x, bottom, x, top)
    return min(start_y - 34, y - 18)


def _draw_mark_scheme_answer_artifact(
    pdf: canvas.Canvas,
    question: Question,
    part: QuestionPart,
    y: float,
) -> float:
    if question.style_id == "recursive_graph_traversal" and part.label == "3":
        return _draw_adjacency_matrix_answers(pdf, y - 5)
    if question.style_id == "recursive_graph_traversal" and part.label == "5":
        return _draw_recursive_trace_answer(pdf, y - 5)
    if question.style_id == "finite_state_machine" and part.label == "1":
        return _draw_transition_table_answer(pdf, y - 5)
    if part.marking.ao == "AO3" and part.marks >= 7:
        return _draw_programming_mark_grid(pdf, part.marks, y - 6)
    return y


def _draw_adjacency_matrix_answers(pdf: canvas.Canvas, y: float) -> float:
    edges = {
        (1, 2), (1, 4), (2, 3), (2, 5), (3, 6), (4, 5), (5, 6)
    }
    cell = 16
    size = cell * 7
    matrices = [
        ("Completed adjacency matrix", False),
        ("Alternative valid matrix", False),
        ("Alternative lower-triangle representation", True),
    ]
    x = 245
    cursor = y
    for matrix_index, (title, lower_triangle_only) in enumerate(matrices):
        pdf.setFont(FONT, 9)
        pdf.drawString(145, cursor, title)
        top = cursor - 9
        for row in range(7):
            for column in range(7):
                x0 = x + column * cell
                y0 = top - (row + 1) * cell
                pdf.setFillColor(
                    colors.HexColor("#d9d9d9")
                    if row == 0 or column == 0
                    else colors.white
                )
                pdf.rect(x0, y0, cell, cell, stroke=1, fill=1)
                pdf.setFillColor(colors.black)
                value = ""
                if row == 0 and column > 0:
                    value = str(column)
                elif column == 0 and row > 0:
                    value = str(row)
                elif row > 0 and column > 0:
                    edge = (min(row, column), max(row, column))
                    if not lower_triangle_only or row >= column:
                        is_edge = edge in edges
                        if matrix_index == 1:
                            is_edge = (
                                min(7 - row, 7 - column),
                                max(7 - row, 7 - column),
                            ) in edges
                        value = "1" if is_edge else "0"
                pdf.setFont(FONT, 8)
                pdf.drawCentredString(x0 + cell / 2, y0 + 5, value)
        cursor -= size + 24
    pdf.setFont(FONT, 8)
    pdf.drawString(
        145,
        cursor + 8,
        "Award 1 mark for symmetry and 1 mark for every edge represented once.",
    )
    return cursor - 4


def _draw_recursive_trace_answer(pdf: canvas.Canvas, y: float) -> float:
    rows = [
        ("3 / 6", "{}", "{3}", ""),
        ("2 / 6", "{3}", "{2, 3}", ""),
        ("1 / 6", "{2, 3}", "{1, 2, 3}", ""),
        ("4 / 6", "{1, 2, 3}", "{1, 2, 3, 4}", ""),
        ("5 / 6", "{1, 2, 3, 4}", "{1, 2, 3, 4, 5}", ""),
        ("6 / 6", "{1, 2, 3, 4, 5}", "{1, 2, 3, 4, 5}", "True"),
    ]
    widths = [90, 110, 125, 50]
    headers = ["Current / target", "visited on entry", "visited after step", "Result"]
    row_height = 24
    x = 125
    pdf.setFont(FONT_BOLD, 9)
    for column, header in enumerate(headers):
        x0 = x + sum(widths[:column])
        pdf.setFillColor(colors.HexColor("#d9d9d9"))
        pdf.rect(x0, y - row_height, widths[column], row_height, stroke=1, fill=1)
        pdf.setFillColor(colors.black)
        pdf.drawString(x0 + 4, y - 16, header)
    pdf.setFont(FONT_MONO, 8)
    for row_index, row in enumerate(rows, start=1):
        for column, value in enumerate(row):
            x0 = x + sum(widths[:column])
            y0 = y - (row_index + 1) * row_height
            pdf.rect(x0, y0, widths[column], row_height, stroke=1, fill=0)
            pdf.drawString(x0 + 4, y0 + 8, value)
    return y - row_height * (len(rows) + 1) - 12


def _draw_transition_table_answer(pdf: canvas.Canvas, y: float) -> float:
    rows = [
        ("S0 (start)", "reject", "S1"),
        ("S1 (accept)", "S2", "S1"),
        ("S2", "S1", "S2"),
    ]
    widths = [132, 105, 105]
    headers = ["Current state", "Input 0", "Input 1"]
    row_height = 25
    x = 125
    for row_index, row in enumerate([headers, *rows]):
        for column, value in enumerate(row):
            x0 = x + sum(widths[:column])
            y0 = y - (row_index + 1) * row_height
            pdf.setFillColor(
                colors.HexColor("#d9d9d9") if row_index == 0 else colors.white
            )
            pdf.rect(x0, y0, widths[column], row_height, stroke=1, fill=1)
            pdf.setFillColor(colors.black)
            pdf.setFont(FONT_BOLD if row_index == 0 else FONT, 8.5)
            pdf.drawString(x0 + 4, y0 + 8, value)
    return y - row_height * 4 - 12


def _draw_programming_mark_grid(
    pdf: canvas.Canvas,
    marks: int,
    y: float,
) -> float:
    bands = 4 if marks >= 12 else 3
    descriptors = [
        "Complete, logically structured solution; all required behaviour is correct and robust.",
        "Substantial working solution; most requirements and important design decisions are correct.",
        "Partial solution with some appropriate constructs; important omissions or errors remain.",
        "Limited relevant attempt showing isolated programming or design features.",
    ][:bands]
    base = marks // bands
    remainder = marks % bands
    ranges: list[tuple[int, int]] = []
    lower = 1
    for index in range(bands):
        width = base + (1 if index >= bands - remainder else 0)
        upper = lower + width - 1
        ranges.append((lower, upper))
        lower = upper + 1
    ranges.reverse()
    row_height = 49 if bands == 4 else 55
    widths = [40, 275, 60]
    x = 120
    headers = ["Level", "Description", "Mark range"]
    for column, value in enumerate(headers):
        x0 = x + sum(widths[:column])
        pdf.setFillColor(colors.HexColor("#d9d9d9"))
        pdf.rect(x0, y - 23, widths[column], 23, stroke=1, fill=1)
        pdf.setFillColor(colors.black)
        pdf.setFont(FONT_BOLD, 8.5)
        pdf.drawCentredString(x0 + widths[column] / 2, y - 15, value)
    cursor = y - 23
    for index, descriptor in enumerate(descriptors):
        for column, width in enumerate(widths):
            x0 = x + sum(widths[:column])
            pdf.rect(
                x0,
                cursor - row_height,
                width,
                row_height,
                stroke=1,
                fill=0,
            )
        pdf.setFont(FONT, 8.5)
        pdf.drawCentredString(x + widths[0] / 2, cursor - 18, str(bands - index))
        text_y = cursor - 14
        for line in _wrap(descriptor, 58):
            pdf.drawString(x + widths[0] + 5, text_y, line)
            text_y -= 11
        low, high = ranges[index]
        pdf.drawCentredString(
            x + widths[0] + widths[1] + widths[2] / 2,
            cursor - 18,
            f"{low}\u2013{high}",
        )
        cursor -= row_height
    return cursor - 10


def _ms_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT, 11)
    pdf.drawRightString(
        556,
        794,
        "MARK SCHEME \u2013 A-LEVEL COMPUTER SCIENCE \u2013 "
        f"{blueprint.paper_code} \u2013 JUNE {_exam_date(blueprint).year}",
    )
    pdf.setLineWidth(0.6)
    pdf.line(0, 774, 553, 774)
    pdf.line(0, 51, 553, 51)
    pdf.setFont(FONT, 8)
    pdf.drawString(43, 35, str(page))


def _exam_date(blueprint: PaperBlueprint) -> date:
    return generation_date()


def _formatted_exam_date(blueprint: PaperBlueprint) -> str:
    return formatted_generation_date()


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


def _wrap_scheme_text(text: str) -> list[str]:
    """Wrap 11 pt guidance to the measured 400 pt printable column."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, FONT, 11) <= 400:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        while pdfmetrics.stringWidth(word, FONT, 11) > 400:
            cut = 1
            while (cut < len(word)
                   and pdfmetrics.stringWidth(word[: cut + 1], FONT, 11) <= 400):
                cut += 1
            lines.append(word[:cut])
            word = word[cut:]
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def _draw_scheme_text(pdf: canvas.Canvas, x: float, y: float, text: str) -> None:
    """Original vector Boolean glyphs, with accessible Unicode ActualText.

    Bundled Arial-compatible fonts do not contain these three operators. Keep
    the symbols and their meaning instead of silently painting .notdef blanks.
    """
    for chunk in re.split(r"([⊕⊼⊽])", text):
        if chunk not in {"⊕", "⊼", "⊽"}:
            pdf.drawString(x, y, chunk)
            x += pdfmetrics.stringWidth(chunk, FONT, 11)
            continue
        width, size = 9.0, 7.0
        pdf.saveState()
        pdf.addLiteral(f"/Span << /ActualText <FEFF{ord(chunk):04X}> >> BDC")
        # The space supplies a selectable text box; the vectors supply the ink.
        pdf.drawString(x, y, "  ")
        pdf.setLineWidth(.7)
        if chunk == "⊕":
            pdf.circle(x + width / 2, y + size / 2, size / 2, stroke=1, fill=0)
            pdf.line(x + 2, y + size / 2, x + width - 2, y + size / 2)
            pdf.line(x + width / 2, y + 1, x + width / 2, y + size - 1)
        else:
            low, high = (0, size - 1) if chunk == "⊼" else (size - 1, 0)
            pdf.line(x + 1, y + low, x + width / 2, y + high)
            pdf.line(x + width / 2, y + high, x + width - 1, y + low)
            pdf.line(x + 1, y + size + 1, x + width - 1, y + size + 1)
        pdf.addLiteral("EMC")
        pdf.restoreState()
        x += width
