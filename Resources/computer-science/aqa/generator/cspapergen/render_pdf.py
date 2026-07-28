from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen import canvas

from Backend.Core.fonts import register_fonts as _rf
from cspapergen.exam_dates import (
    formatted_paper1_exam_date,
    formatted_paper2_exam_date,
    paper1_exam_date,
    paper2_exam_date,
)
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
PAPER2_MARK_SCHEME_PAGE_RANGES = {
    1: (6, 8),
    2: (9, 11),
    3: (12, 13),
    4: (14, 14),
    5: (15, 15),
    6: (16, 20),
    7: (20, 23),
    8: (24, 25),
    9: (26, 27),
    10: (27, 27),
    11: (28, 29),
    12: (30, 32),
    13: (33, 34),
    14: (35, 35),
}
PAPER2_MARK_SCHEME_PART_PAGE_OFFSETS = {
    1: (0, 0, 2),
    2: (0, 0, 1, 2),
    3: (0, 1),
    4: (0,),
    5: (0,),
    6: (0, 0, 1, 3, 4),
    7: (0, 1, 1, 3),
    8: (0,),
    9: (0, 0, 1),
    10: (0, 0),
    11: (0, 0, 1, 1),
    12: (0, 0, 1, 1, 2, 2),
    13: (0,),
    14: (0,),
}
PAPER1_MARK_SCHEME_PAGE_RANGES = {
    1: (6, 7),
    2: (7, 7),
    3: (7, 9),
    4: (10, 12),
    5: (13, 13),
    6: (14, 15),
    7: (16, 16),
    8: (16, 16),
    9: (17, 17),
    10: (20, 21),
    11: (22, 23),
    12: (24, 25),
}
PAPER1_REFERENCE_SOLUTION_PAGE_RANGES = {
    4: (26, 27),
    9: (28, 29),
    10: (30, 32),
    11: (33, 36),
    12: (37, 41),
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
    for _index in range(extra_pages):
        _draw_extra_answer_page(pdf, state.page + 1, blueprint)
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
    _draw_intentionally_blank_page(pdf, state)
    for _index in range(EXTRA_ANSWER_PAGES):
        _draw_extra_answer_page(pdf, state.page + 1, blueprint)
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
    _answer_lines(pdf, 680, 25)
    state.y = 160


def _render_paper1_question_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    state: _QuestionRenderState,
) -> _QuestionRenderState:
    _draw_paper1_section_intro(pdf, state, *PAPER1_SECTIONS[1])
    state = _new_question_page(pdf, state)

    for index, question in enumerate(blueprint.questions):
        if question.number in PAPER1_SECTIONS and question.number != 1:
            state = _new_question_page(pdf, state)
            _draw_paper1_section_intro(pdf, state, *PAPER1_SECTIONS[question.number])
            state = _new_question_page(pdf, state)
        elif index and question.number not in PAPER1_SHARE_PAGE_WITH_PREVIOUS:
            state = _new_question_page(pdf, state)

        state = _render_question(
            pdf,
            question,
            state,
            show_answer_space=False,
            allow_current_page=question.number in PAPER1_SHARE_PAGE_WITH_PREVIOUS,
        )
        interstitial = PAPER1_INTERSTITIAL_AFTER.get(question.number)
        if interstitial:
            state = _new_question_page(pdf, state)
            if interstitial == "support":
                _draw_paper1_support_page(pdf, state, question)
            else:
                _draw_intentionally_blank_page(pdf, state)

    state = _ensure_space(pdf, state, 72)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(282, state.y - 18, "END OF QUESTIONS")
    for _index in range(PAPER1_TRAILING_BLANK_PAGES):
        state = _new_question_page(pdf, state)
        _draw_intentionally_blank_page(pdf, state)
    return state


def _draw_paper1_section_intro(
    pdf: canvas.Canvas,
    state: _QuestionRenderState,
    title: str,
    timing: str,
) -> None:
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawCentredString(289, 700, title)
    pdf.setFont(FONT, 11)
    pdf.drawCentredString(289, 670, "Answer all questions in this section.")
    pdf.drawCentredString(289, 647, timing)
    pdf.setFont(FONT, 9.5)
    pdf.drawCentredString(289, 605, "Enter your answers in the supplied Electronic Answer Document")
    pdf.drawCentredString(289, 590, "or complete the programming task in your development environment.")
    state.y = 548


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


def _draw_intentionally_blank_page(pdf: canvas.Canvas, state: _QuestionRenderState) -> None:
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawCentredString(289, 430, "There are no questions printed on this page")
    pdf.setFont(FONT, 9)
    pdf.drawCentredString(289, 408, "DO NOT WRITE ON THIS PAGE")
    state.y = 380


def render_mark_scheme(blueprint: PaperBlueprint, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=AQA_A4, pageCompression=0)
    _mark_scheme_cover(pdf, blueprint)
    pdf.showPage()
    _mark_scheme_intro(pdf, 2, blueprint)
    pdf.showPage()
    _mark_scheme_levels(pdf, 3, blueprint)
    pdf.showPage()
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
    page = 6
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
    pdf.save()


def _render_paper1_mark_scheme_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
) -> None:
    if [question.number for question in blueprint.questions] != list(range(1, 13)):
        raise ValueError("Paper 1 mark scheme requires Questions 1 to 12")

    page = 6
    y = _mark_scheme_table_header(pdf, page, blueprint)
    for question in blueprint.questions:
        start_page, end_page = PAPER1_MARK_SCHEME_PAGE_RANGES[question.number]
        while page < start_page:
            pdf.showPage()
            page += 1
            if page in {18, 19}:
                _ms_header(pdf, page, blueprint)
                y = 710
            else:
                y = _mark_scheme_table_header(pdf, page, blueprint)
        if page != start_page:
            raise ValueError(
                f"Question {question.number} missed its mark-scheme start page {start_page}"
            )

        continuation_index = 0
        span = end_page - start_page + 1
        part_count = len(question.parts)
        for part_index, part in enumerate(question.parts):
            desired_page = start_page
            if part_count > 1:
                desired_page += round(part_index * (span - 1) / (part_count - 1))
            while page < desired_page:
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
                if page < desired_page:
                    y = _draw_mark_scheme_continuation_frame(
                        pdf,
                        question,
                        y,
                        continuation_index,
                    )
                    continuation_index += 1
            needed = _mark_scheme_part_height(part)
            if y - needed < 70:
                if page >= end_page:
                    raise ValueError(
                        f"Question {question.number} overflowed its mark-scheme page range"
                    )
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
            y = _render_mark_scheme_part(pdf, question, part, y)

        next_start = (
            PAPER1_MARK_SCHEME_PAGE_RANGES[question.number + 1][0]
            if question.number < 12
            else None
        )
        while page < end_page:
            pdf.showPage()
            page += 1
            y = _mark_scheme_table_header(pdf, page, blueprint)
            if page != next_start:
                y = _draw_mark_scheme_continuation_frame(
                    pdf,
                    question,
                    y,
                    continuation_index,
                )
                continuation_index += 1

    question_by_number = {question.number: question for question in blueprint.questions}
    for question_number, (first_page, last_page) in PAPER1_REFERENCE_SOLUTION_PAGE_RANGES.items():
        question = question_by_number[question_number]
        for solution_page in range(first_page, last_page + 1):
            pdf.showPage()
            page += 1
            if page != solution_page:
                raise ValueError(f"Paper 1 reference solution missed page {solution_page}")
            _draw_paper1_reference_solution_page(
                pdf,
                blueprint,
                question,
                page,
                solution_page - first_page,
            )


def _draw_paper1_reference_solution_page(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
    question: Question,
    page: int,
    page_offset: int,
) -> None:
    _ms_header(pdf, page, blueprint)
    pdf.setFont(FONT_BOLD, 13)
    title = "Example Python 3 solution" if page_offset == 0 else "Example solution guidance continued"
    pdf.drawString(55, 720, f"Question {question.number:02d}: {title}")
    y = 690
    if page_offset == 0:
        pdf.setFont(FONT, 10)
        for line in _wrap(question.parts[0].prompt, 88):
            pdf.drawString(55, y, line)
            y -= 14
        y -= 10
        code = _paper1_reference_code(question.number)
        pdf.setFont(FONT_MONO, 10)
        for line in code.splitlines():
            pdf.drawString(62, y, line[:86])
            y -= 13
    else:
        sections = _paper1_reference_guidance(question, page_offset)
        for heading, lines in sections:
            pdf.setFont(FONT_BOLD, 11)
            pdf.drawString(55, y, heading)
            y -= 19
            pdf.setFont(FONT, 11)
            for item in lines:
                for line_index, line in enumerate(_wrap(item, 82)):
                    pdf.drawString(67 if line_index == 0 else 80, y, ("• " if line_index == 0 else "") + line)
                    y -= 15
                y -= 3
            y -= 8


def _paper1_reference_guidance(
    question: Question,
    page_offset: int,
) -> list[tuple[str, list[str]]]:
    points = [
        point.rstrip(";.")
        for part in question.parts
        for point in part.marking.points
    ]
    if page_offset % 3 == 1:
        return [
            ("Mark allocation", points),
            (
                "Testing",
                [
                    "Use a normal case that exercises the main successful path.",
                    "Use boundary values and at least one malformed or rejected input.",
                    "Compare the actual result with a stated expected result.",
                ],
            ),
        ]
    if page_offset % 3 == 2:
        return [
            (
                "Alternative implementations",
                [
                    "Credit a logically equivalent solution with different identifiers or control structures.",
                    "The solution must preserve every stated validation rule and required output.",
                    "Do not require the exact formatting shown in the example.",
                ],
            ),
            ("Technical checks", points),
        ]
    return [
        (
            "Robustness and maintainability",
            [
                "Inputs are validated before the program mutates existing data.",
                "Exceptional input is handled without corrupting state or terminating unexpectedly.",
                "The implementation is decomposed clearly and avoids duplicated logic.",
                "Names and control flow make the algorithm straightforward to verify.",
            ],
        ),
        ("Question-specific checks", points),
    ]


def _paper1_reference_code(question_number: int) -> str:
    examples = {
        4: """from time import perf_counter

def timed(function, values, trials=5):
    results = []
    for _ in range(trials):
        data = values.copy()
        started = perf_counter()
        function(data)
        results.append(perf_counter() - started)
    return sum(results) / len(results)

def select_algorithm(values):
    merge_time = timed(merge_sort, values)
    bubble_time = timed(bubble_sort, values)
    return \"merge\" if merge_time < bubble_time else \"bubble\"""",
        9: """VALID_CATEGORIES = {\"GRASSLAND\", \"WETLAND\", \"WOODLAND\"}

def valid_entry(category, value_text):
    category = category.strip().upper()
    if category not in VALID_CATEGORIES:
        return False
    try:
        value = int(value_text)
    except ValueError:
        return False
    return 0 <= value <= 100""",
        10: """def safe_adjusted_value(row):
    try:
        identifier, category, value_text = row.strip().split(\",\")
        value = int(value_text)
    except (ValueError, TypeError):
        return None, \"Malformed input\"

    if value < 0 or value > 100:
        return None, \"Value out of range\"
    adjusted = value * MULTIPLIER if value >= THRESHOLD else value
    return adjusted, None""",
        11: """def add_record(records):
    try:
        identifier = int(input(\"Identifier: \"))
        if any(item.identifier == identifier for item in records):
            print(\"Identifier already used\")
            return
        category = input(\"Category: \").strip().upper()
        if category not in CATEGORIES:
            print(\"Invalid category\")
            return
        value = int(input(\"Value: \"))
        if not 0 <= value <= 100:
            print(\"Value out of range\")
            return
    except ValueError:
        print(\"A whole number is required\")
        return
    records.append(Observation(identifier, category, value))""",
        12: """def print_report(records):
    totals = category_totals(records)
    ordered = sorted(totals, key=lambda name: (-totals[name], name))
    for category in ordered:
        members = [item for item in records if item.category == category]
        best = max(members, key=adjusted_value) if members else None
        print(category, totals[category], best.identifier if best else \"-\")

# A descending numeric key and ascending category key implement
# the required deterministic tie break.""",
    }
    return examples[question_number]


def _render_paper2_mark_scheme_pages(
    pdf: canvas.Canvas,
    blueprint: PaperBlueprint,
) -> None:
    if [question.number for question in blueprint.questions] != list(range(1, 15)):
        raise ValueError("Paper 2 mark scheme requires Questions 1 to 14")

    page = 6
    y = _mark_scheme_table_header(pdf, page, blueprint)
    for question_index, question in enumerate(blueprint.questions):
        start_page, end_page = PAPER2_MARK_SCHEME_PAGE_RANGES[question.number]
        while page < start_page:
            pdf.showPage()
            page += 1
            y = _mark_scheme_table_header(pdf, page, blueprint)
        if page != start_page:
            raise ValueError(
                f"Question {question.number} missed its mark-scheme start page {start_page}"
            )

        continuation_index = 0
        offsets = PAPER2_MARK_SCHEME_PART_PAGE_OFFSETS[question.number]
        if len(offsets) != len(question.parts):
            raise ValueError(
                f"Question {question.number} part count does not match its mark-scheme page plan"
            )
        for part_index, part in enumerate(question.parts):
            desired_page = start_page + offsets[part_index]
            if desired_page > end_page:
                raise ValueError(
                    f"Question {question.number} part page exceeds its mark-scheme range"
                )
            while page < desired_page:
                pdf.showPage()
                page += 1
                y = _mark_scheme_table_header(pdf, page, blueprint)
                if page < desired_page:
                    y = _draw_mark_scheme_continuation_frame(
                        pdf,
                        question,
                        y,
                        continuation_index,
                    )
                    continuation_index += 1
            needed = _mark_scheme_part_height(part)
            if y - needed < 70:
                if page >= end_page:
                    raise ValueError(
                        f"Question {question.number} overflowed its mark-scheme page range"
                    )
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
            y = _render_mark_scheme_part(pdf, question, part, y)

        next_start = (
            PAPER2_MARK_SCHEME_PAGE_RANGES[question.number + 1][0]
            if question.number < 14
            else None
        )
        while page < end_page:
            pdf.showPage()
            page += 1
            y = _mark_scheme_table_header(pdf, page, blueprint)
            if page != next_start:
                y = _draw_mark_scheme_continuation_frame(
                    pdf,
                    question,
                    y,
                    continuation_index,
                )
                continuation_index += 1


def _mark_scheme_part_height(part: QuestionPart) -> float:
    wrapped_lines = 1
    wrapped_lines += sum(len(_wrap(point, 62)) for point in part.marking.points)
    wrapped_lines += sum(len(_wrap(item, 59)) for item in part.marking.accept)
    wrapped_lines += sum(len(_wrap(item, 59)) for item in part.marking.reject)
    wrapped_lines += sum(len(_wrap(item, 62)) for item in part.marking.levels)
    return 38 + 15 * wrapped_lines


def _draw_mark_scheme_continuation_frame(
    pdf: canvas.Canvas,
    question: Question,
    y: float,
    continuation_index: int,
) -> float:
    bottom = 70
    top = y + 10
    pdf.setLineWidth(0.7)
    pdf.rect(45, bottom, 505, top - bottom, stroke=1, fill=0)
    pdf.line(73, bottom, 73, top)
    pdf.line(106, bottom, 106, top)
    pdf.line(500, bottom, 500, top)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(52, y, f"{question.number:02d}")
    lines = _continuation_guidance_lines(question, continuation_index)
    cursor = y
    for line_index, item in enumerate(lines):
        wrapped = _wrap(item, 62)
        pdf.setFont(FONT_BOLD if line_index == 0 else FONT, 11)
        for line in wrapped:
            pdf.drawString(125, cursor, line)
            cursor -= 15
            if cursor < bottom + 18:
                return bottom
    return bottom


def _continuation_guidance_lines(
    question: Question,
    continuation_index: int,
) -> list[str]:
    points = [
        point.rstrip(";.")
        for part in question.parts
        for point in part.marking.points
    ]
    levels = [
        level
        for part in question.parts
        for level in part.marking.levels
    ]
    if continuation_index % 3 == 0:
        return [
            "Indicative content continued",
            *(f"• {point}." for point in points),
            "Credit any technically correct equivalent that answers the question.",
            "Do not award the same technical point more than once.",
        ]
    if continuation_index % 3 == 1:
        return [
            "Assessment guidance",
            f"Question focus: {question.stem}",
            "Credit accurate terminology and reasoning that is applied to the stated context.",
            "Where a consequence is required, the response must establish a valid technical link.",
            "For a balanced answer, both benefits and limitations must be considered before the conclusion.",
            *(levels or ["Award each available mark independently unless the guidance states otherwise."]),
        ]
    return [
        "Level and judgement guidance",
        *(levels or [
            "A stronger response selects relevant technical material and develops it coherently.",
            "A mid-range response contains relevant knowledge but has incomplete application or reasoning.",
            "A limited response presents isolated points with little technical development.",
        ]),
        "The final mark should reflect the response as a whole.",
        "A supported conclusion must follow from the technical arguments presented.",
    ]


class _QuestionRenderState:
    def __init__(self, page: int, y: float, blueprint: PaperBlueprint) -> None:
        self.page = page
        self.y = y
        self.blueprint = blueprint


def _cover_page(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT, 11)
    candidate_instruction = (
        "Complete the candidate details and save all electronic work clearly."
        if blueprint.delivery_mode == "on-screen"
        else "Please write clearly in block capitals."
    )
    pdf.drawString(55, 790, candidate_instruction)
    _candidate_fields(pdf)

    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(55, 535, "A-level")
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(55, 508, "COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 16)
    pdf.drawString(55, 483, f"Paper {blueprint.paper_number}")
    pdf.setFont(FONT, 11)
    pdf.drawString(55, 458, _formatted_exam_date(blueprint))
    pdf.drawString(225, 458, blueprint.session)
    pdf.setFont(FONT, 9.5)
    pdf.drawString(302, 458, "Time allowed: 2 hours 30 minutes")

    y = 430
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

    _examiner_table(pdf, len(blueprint.questions), y_top=420)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(55, 35, f"*PRACTICE{blueprint.paper_code.replace('/', '')}01*")
    pdf.setFont(FONT, 9)
    pdf.drawRightString(535, 35, blueprint.paper_code)


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


def _draw_question_page_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
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
        instruction = (
            "Use the Electronic Answer Document and development environment."
            if blueprint.delivery_mode == "on-screen"
            else "Answer all questions."
        )
        pdf.drawCentredString(289, 768, instruction)
    pdf.setFont(FONT, 8)
    _draw_footer_barcode(pdf, 52, 14, page)
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
        pdf.setFont(FONT, 8.5)
        pdf.drawString(118, state.y, "Respond in the supplied Electronic Answer Document or development environment.")
        state.y -= 22
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
    elif stimulus.kind == "classification":
        state.y = _draw_classification_diagram(pdf, stimulus.diagram, 118, state.y)
    elif stimulus.kind == "optical":
        state.y = _draw_optical_diagram(pdf, stimulus.diagram, 118, state.y)
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


def _draw_classification_diagram(
    pdf: canvas.Canvas,
    diagram: str,
    x: float,
    y: float,
) -> float:
    application_one, application_two, utility, translator = diagram.split("|")
    boxes = {
        "Software": (x, y - 104, 76, 34),
        "Application software": (x + 110, y - 55, 112, 34),
        "System software": (x + 110, y - 155, 112, 34),
        application_one: (x + 258, y - 26, 112, 34),
        application_two: (x + 258, y - 70, 112, 34),
        "Utility software": (x + 258, y - 126, 112, 34),
        "Translators": (x + 258, y - 170, 112, 34),
    }
    links = [
        ("Software", "Application software"),
        ("Software", "System software"),
        ("Application software", application_one),
        ("Application software", application_two),
        ("System software", "Utility software"),
        ("System software", "Translators"),
    ]
    for start, end in links:
        sx, sy, sw, sh = boxes[start]
        ex, ey, _ew, eh = boxes[end]
        pdf.line(sx + sw, sy + sh / 2, ex, ey + eh / 2)
    display_labels = {
        "Application software": "1",
        "Utility software": "2",
    }
    for label, (bx, by, width, height) in boxes.items():
        pdf.rect(bx, by, width, height, stroke=1, fill=0)
        pdf.setFont(FONT_BOLD if label in {"Software", "Application software", "System software"} else FONT, 8)
        for line_index, line in enumerate(_wrap(display_labels.get(label, label), 19)):
            pdf.drawCentredString(
                bx + width / 2,
                by + height / 2 + 3 - line_index * 10,
                line,
            )
    return y - 192


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


def _draw_extra_answer_page(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    pdf.showPage()
    _draw_question_page_header(pdf, page, blueprint)
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


def _mark_scheme_cover(pdf: canvas.Canvas, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(55, 720, "A-level")
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(55, 690, "COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 15)
    pdf.drawString(55, 665, blueprint.paper_code)
    pdf.drawString(55, 640, f"Paper {blueprint.paper_number}")
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(55, 585, "Mark scheme")
    pdf.setFont(FONT, 13)
    pdf.drawString(55, 555, f"June {_exam_date(blueprint).year}")
    pdf.drawString(55, 530, "Version: 1.0")
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(55, 40, f"PC{blueprint.paper_code}/MS")


def _mark_scheme_intro(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    _ms_header(pdf, page, blueprint)
    y = 705
    pdf.setFont(FONT, 10)
    paragraphs = [
        f"This independent mark scheme supports consistent marking of Paper Creator's A-level Computer Science Paper {blueprint.paper_number} practice assessment.",
        "Apply the guidance positively. Award credit for what a response demonstrates, and do not deduct marks for an omission unless the question or guidance explicitly requires that element.",
        "The listed answers describe responses that are likely to earn credit. They are not exhaustive. Credit a technically correct alternative when it answers the precise question and is consistent with the stated scenario.",
        "Judge each response against the published marking guidance rather than against another candidate's work. The same standard must be applied throughout the script.",
        "Where a point is followed by an explanation, award the explanation mark only when the reasoning is technically valid and linked to the point made. Do not award the same mark twice for equivalent wording.",
        "Accept established technical terminology, unambiguous pseudocode and logically equivalent expressions. Minor spelling or grammatical errors should not prevent credit when the intended technical meaning is clear.",
        "For calculations, accept a correct answer obtained from valid working. If an earlier arithmetic error is carried forward consistently, award subsequent method marks where the method remains valid.",
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
    y = 705
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


def _mark_scheme_table_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> float:
    _ms_header(pdf, page, blueprint)
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


def _render_mark_scheme_part(
    pdf: canvas.Canvas,
    question: Question,
    part: QuestionPart,
    y: float,
    *,
    show_total: bool = True,
    heading: str | None = None,
) -> float:
    start_y = y
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(52, y, f"{question.number:02d}")
    pdf.drawString(86, y, part.label)
    if show_total:
        pdf.drawRightString(528, y, str(part.marks))
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(125, y, heading or f"All marks {part.marking.ao}")
    y -= 15
    pdf.setFont(FONT, 11)
    for point in part.marking.points:
        for line in _wrap(point, 62):
            pdf.drawString(125, y, line)
            y -= 15
    for item in part.marking.accept:
        for line in _wrap(f"A. {item}", 59):
            pdf.drawString(125, y, line)
            y -= 15
    for item in part.marking.reject:
        for line in _wrap(f"R. {item}", 59):
            pdf.drawString(125, y, line)
            y -= 15
    for item in part.marking.levels:
        for line in _wrap(item, 62):
            pdf.drawString(125, y, line)
            y -= 15
    bottom = y - 5
    top = start_y + 10
    pdf.rect(45, bottom, 505, top - bottom, stroke=1, fill=0)
    pdf.line(73, bottom, 73, top)
    pdf.line(106, bottom, 106, top)
    pdf.line(500, bottom, 500, top)
    return min(start_y - 34, y - 18)


def _ms_header(pdf: canvas.Canvas, page: int, blueprint: PaperBlueprint) -> None:
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawCentredString(
        297,
        800,
        "MARK SCHEME \u2013 A-LEVEL COMPUTER SCIENCE \u2013 "
        f"{blueprint.paper_code} \u2013 JUNE {_exam_date(blueprint).year}",
    )
    pdf.setFont(FONT, 9)
    pdf.drawCentredString(297, 32, str(page))


def _exam_date(blueprint: PaperBlueprint) -> date:
    return paper1_exam_date() if blueprint.paper_number == "1" else paper2_exam_date()


def _formatted_exam_date(blueprint: PaperBlueprint) -> str:
    return formatted_paper1_exam_date() if blueprint.paper_number == "1" else formatted_paper2_exam_date()


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
