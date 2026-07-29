from __future__ import annotations

import math
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.exam_blueprints import GeneratedOption, GeneratedPaper, GeneratedQuestion
from Backend.Core.exam_cover import (
    CoverProfile,
    aqa_question_cover,
    mark_scheme_cover,
)
from Backend.Core.fonts import register_fonts
from Backend.Core.generation_date import formatted_generation_date
from Backend.Core.reportlab_theme import themed_table_class

BLACK = colors.HexColor("#171717")
GREY = colors.HexColor("#ececec")
MID_GREY = colors.HexColor("#666666")
AQA_A4 = (595.32, 841.92)
PAGE_WIDTH, PAGE_HEIGHT = AQA_A4
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)
Table = themed_table_class(Table, FONT)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    if paper.paper_id == "paper_3":
        story.extend(_paper_three_pages(paper))
        doc.build(story)
        return
    for section in paper.sections:
        story.extend([PageBreak(), *_section_intro(section.id, section.title, section.instructions)])
        if paper.paper_id in {"paper_1", "paper_2"} and section.id == "A":
            for index, option in enumerate(section.options):
                if index:
                    story.extend([PageBreak(), *_section_intro(section.id, section.title, section.instructions)])
                story.extend(_context_first_page(option))
                story.extend(
                    [
                        PageBreak(),
                        *_context_second_page(option),
                        *_option_questions(option),
                    ]
                )
        elif paper.paper_id in {"paper_1", "paper_2"}:
            first, second, third = section.options
            story.extend(_written_option(first))
            story.extend(
                [
                    Paragraph("OR", STYLES["continuation"]),
                    Spacer(1, 3 * mm),
                    *_written_option(second),
                    PageBreak(),
                    *_section_intro(
                        section.id, section.title, section.instructions
                    ),
                    *_written_option(third),
                    PageBreak(),
                    *_no_questions_page(),
                ]
            )
        elif section.id == "A":
            for option in section.options:
                story.extend(_mcq_block(option))
        else:
            option = section.options[0]
            story.extend(_stimulus_page(option))
            story.extend(
                [
                    PageBreak(),
                    _section_banner(f"Section {section.id}: Case-study questions"),
                    Spacer(1, 5 * mm),
                    *_option_questions(option, count=2),
                    PageBreak(),
                    _section_banner(f"Section {section.id}: Case-study questions continued"),
                    Spacer(1, 5 * mm),
                    *_option_questions(option, start=2),
                ]
            )
    doc.build(story)


def render_source_booklet(paper: GeneratedPaper, path: Path) -> None:
    if paper.paper_id != "paper_3":
        raise ValueError("only Paper 3 has a separate source booklet")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Insert")
    option = paper.sections[1].options[0]
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Economics", STYLES["cover_kicker"]),
        Paragraph("Paper 3 source insert", STYLES["cover_title"]),
        Spacer(1, 5 * mm),
        Paragraph(option.title, STYLES["cover_subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["cover_subtitle"]),
        Spacer(1, 10 * mm),
        _info_box(
            "Questions 31 to 33 refer to the independently created extracts in this insert. "
            "Do not write answers in this insert."
        ),
        Spacer(1, 10 * mm),
        Paragraph("• Extract A: Changes in economic activity", STYLES["body"]),
        Paragraph("• Extract B: Evidence and indicators", STYLES["body"]),
        Paragraph("• Extract C: Policy options", STYLES["body"]),
        Paragraph("• Extract D: Reasons for caution", STYLES["body"]),
        PageBreak(),
        Paragraph("There are no sources printed on this page.", STYLES["centred_note"]),
    ]
    extract_labels = "ABCD"
    for index in range(4):
        story.extend(
            [
                PageBreak(),
                Paragraph(f"Extract {extract_labels[index]}", STYLES["option_title"]),
                Spacer(1, 4 * mm),
                Paragraph(
                    option.stimulus[index].split(": ", 1)[-1],
                    STYLES["source_extract"],
                ),
            ]
        )
        if index in {0, 1} and option.chart_values:
            story.extend(
                [
                    Spacer(1, 7 * mm),
                    _line_chart(option.chart_title, option.chart_labels, option.chart_values),
                ]
            )
    story.extend(
        [
            PageBreak(),
            Paragraph("Notes", STYLES["option_title"]),
            Paragraph(
                "All organisations, economies, statistics and quotations in this practice insert "
                "are fictional. Candidates should assess the reliability and limitations of the "
                "evidence as part of their evaluation.",
                STYLES["source_extract"],
            ),
            PageBreak(),
            Paragraph("There are no sources printed on this page.", STYLES["centred_note"]),
        ]
    )
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = mark_scheme_cover(
        _cover_profile(paper),
        FONT,
        FONT_BOLD,
    )
    pages = (
        _paper_three_mark_scheme_pages(paper)
        if paper.paper_id == "paper_3"
        else _paper_one_two_mark_scheme_pages(paper)
    )
    for page in pages:
        story.append(PageBreak())
        story.extend(page)
    doc.build(story)


def _paper_one_two_mark_scheme_pages(
    paper: GeneratedPaper,
) -> list[list[Flowable]]:
    context_section, essay_section = paper.sections
    pages: list[list[Flowable]] = [
        _general_marking_page(),
        _levels_page(),
        _section_levels_page(
            "Section A",
            "For 9- and 25-mark responses, determine the level first and then "
            "select the mark using accuracy, application and development.",
        ),
    ]
    for option in context_section.options:
        questions = option.questions
        pages.extend(
            [
                _scheme_question_page(
                    questions[0], heading=option.title, total_marks=40
                ),
                _scheme_question_page(questions[1]),
                _scheme_question_page(questions[2], segment=1, segment_count=2),
                _scheme_question_page(questions[2], segment=2, segment_count=2),
                _scheme_question_page(questions[3]),
            ]
        )
    pages.append(
        _section_levels_page(
            "Section B",
            "Each essay carries 40 marks. Apply the 15-mark and 25-mark level "
            "descriptors independently and reward a supported economic judgement.",
        )
    )
    for option in essay_section.options:
        for question_index, question in enumerate(option.questions):
            pages.append(
                _scheme_question_page(
                    question,
                    heading=option.title if question_index == 0 else None,
                    total_marks=40 if question_index == 0 else None,
                )
            )
    return pages


def _paper_three_mark_scheme_pages(
    paper: GeneratedPaper,
) -> list[list[Flowable]]:
    mcq_section, written_section = paper.sections
    questions = written_section.options[0].questions
    pages: list[list[Flowable]] = [
        _general_marking_page(),
        _mcq_key_page(mcq_section.options),
        _levels_page(),
    ]
    for question, page_count in zip(questions, (3, 2, 2), strict=True):
        for segment in range(1, page_count + 1):
            pages.append(
                _scheme_question_page(
                    question,
                    segment=segment,
                    segment_count=page_count,
                    heading=(
                        "Section B · Investigation"
                        if question.number == "31" and segment == 1
                        else None
                    ),
                    total_marks=50 if question.number == "31" and segment == 1 else None,
                )
            )
    return pages


def _general_marking_page() -> list[Flowable]:
    return [
        Paragraph("Marking guidance", STYLES["cover_kicker"]),
        Spacer(1, 6 * mm),
        Paragraph(
            "Apply the mark scheme consistently. Credit accurate economic reasoning "
            "that answers the question and accept a valid alternative analytical route.",
            STYLES["body"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Assessment objectives", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _assessment_objectives_table(),
        Spacer(1, 6 * mm),
        Paragraph(
            "Read the whole response before awarding a mark. Do not reward the same "
            "developed point twice. Apply error carried forward where later reasoning "
            "remains economically and mathematically valid.",
            STYLES["body"],
        ),
    ]


def _assessment_objectives_table() -> Table:
    rows = [
        ["AO1", "Demonstrate precise knowledge and understanding."],
        ["AO2", "Apply knowledge to the supplied context and evidence."],
        ["AO3", "Analyse issues using complete chains of reasoning."],
        ["AO4", "Evaluate evidence and reach a supported judgement."],
    ]
    table = Table(rows, colWidths=[22 * mm, 143 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
                ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
                ("FONTNAME", (1, 0), (1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _levels_page() -> list[Flowable]:
    rows = [
        ["Level", "Characteristics of the response"],
        [
            "Highest",
            "Precise knowledge, sustained application, complete analytical chains "
            "and a judgement supported by the preceding argument.",
        ],
        [
            "Middle",
            "Sound knowledge and some developed analysis; application or evaluation "
            "may be uneven but remains relevant to the question.",
        ],
        [
            "Lowest",
            "Isolated relevant knowledge or short reasoning chains with limited "
            "application and little supported evaluation.",
        ],
        ["0", "No creditworthy material."],
    ]
    table = Table(rows, colWidths=[28 * mm, 137 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [
        Paragraph("Level of response marking instructions", STYLES["cover_kicker"]),
        Spacer(1, 5 * mm),
        Paragraph(
            "Start at the highest level and work down until the response meets the "
            "descriptor. Then use the quality and consistency of the response to "
            "select a mark within that level.",
            STYLES["body"],
        ),
        Spacer(1, 6 * mm),
        table,
    ]


def _section_levels_page(title: str, guidance: str) -> list[Flowable]:
    return [
        _section_banner(title),
        Spacer(1, 5 * mm),
        Paragraph("Levels of response", STYLES["cover_kicker"]),
        Spacer(1, 5 * mm),
        Paragraph(guidance, STYLES["body"]),
        Spacer(1, 6 * mm),
        *_levels_page()[2:],
    ]


def _mcq_key_page(options: list[GeneratedOption]) -> list[Flowable]:
    pairs = [
        (
            option.questions[0].number,
            "ABCD"[option.questions[0].correct_choice or 0],
        )
        for option in options
    ]
    rows: list[list[str]] = [["Question", "Key", "Question", "Key", "Question", "Key"]]
    for index in range(10):
        row: list[str] = []
        for column in range(3):
            number, key = pairs[index + column * 10]
            row.extend([number, key])
        rows.append(row)
    table = Table(
        rows,
        colWidths=[28 * mm, 18 * mm, 28 * mm, 18 * mm, 28 * mm, 18 * mm],
        rowHeights=[9 * mm] * len(rows),
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return [
        Paragraph("Section A · Key list", STYLES["cover_kicker"]),
        Spacer(1, 6 * mm),
        table,
    ]


def _scheme_question_page(
    question: GeneratedQuestion,
    *,
    segment: int = 1,
    segment_count: int = 1,
    heading: str | None = None,
    total_marks: int | None = None,
) -> list[Flowable]:
    chunk_size = max(1, math.ceil(len(question.mark_scheme) / segment_count))
    start = (segment - 1) * chunk_size
    points = question.mark_scheme[start : start + chunk_size]
    title = (
        f"{heading} · Total: {total_marks} marks"
        if heading and total_marks is not None
        else heading
    )
    flowables: list[Flowable] = []
    if title:
        flowables.extend([Paragraph(title, STYLES["option_title"]), Spacer(1, 4 * mm)])
    flowables.extend(
        [
            _mark_scheme_question_header(
                question,
                continued=segment > 1,
            ),
            Spacer(1, 4 * mm),
        ]
    )
    if question.kind == "diagram_analysis" and segment == 2:
        flowables.extend(
            [
                Paragraph("Expected diagram", STYLES["heading"]),
                Spacer(1, 2 * mm),
                _economic_diagram(question.topic_id, question.number),
                Spacer(1, 3 * mm),
            ]
        )
    flowables.extend(
        [
            Paragraph("Indicative content", STYLES["heading"]),
            Spacer(1, 2 * mm),
            *[
                Paragraph(f"• {point}", STYLES["scheme_compact"])
                for point in points
            ],
        ]
    )
    if segment_count > 1:
        flowables.extend(
            [
                Spacer(1, 3 * mm),
                Paragraph(
                    f"Question {question.number}: guidance page {segment} of "
                    f"{segment_count}.",
                    STYLES["scheme_note"],
                ),
            ]
        )
    return flowables


def _mark_scheme_question_header(
    question: GeneratedQuestion,
    *,
    continued: bool,
) -> Table:
    prompt = (
        f"<b>{question.number} continued</b>"
        if continued
        else f"<b>{question.number}</b> {question.prompt}"
    )
    table = Table(
        [[Paragraph(prompt, STYLES["question"]), Paragraph(str(question.marks), STYLES["marks"])]],
        colWidths=[153 * mm, 12 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, -1), GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _document(path: Path, paper: GeneratedPaper, document_type: str) -> BaseDocTemplate:
    is_answer_booklet = document_type == "Question paper" and paper.paper_id == "paper_3"
    doc = BaseDocTemplate(
        str(path),
        pagesize=AQA_A4,
        leftMargin=16 * mm,
        rightMargin=17 * mm,
        topMargin=(25 * mm if is_answer_booklet else 18 * mm),
        bottomMargin=(26 * mm if is_answer_booklet else 15 * mm),
        title=f"{paper.paper_code} {paper.title} — {document_type}",
        author="Paper creator",
        subject="Independent A-level Economics practice material",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(
        PageTemplate(
            id="practice",
            frames=[frame],
            onPage=lambda canvas, value: _page_chrome(
                canvas, value, paper.paper_code, document_type
            ),
        )
    )
    return doc


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return aqa_question_cover(_cover_profile(paper), FONT, FONT_BOLD)


def _cover_profile(paper: GeneratedPaper) -> CoverProfile:
    hours, minutes = divmod(paper.duration_minutes, 60)
    duration = f"{hours} hours" if not minutes else f"{hours} hours {minutes} minutes"
    return CoverProfile(
        board="aqa",
        subject="Economics",
        code=paper.paper_code,
        paper_title=f"Paper {paper.paper_id[-1]}  {paper.title}",
        duration=duration,
        total_marks=paper.total_marks,
        candidate_fields=paper.paper_id == "paper_3",
        materials=(
            "You may use a calculator.",
            "For this paper you must have an answer booklet.",
        ),
        instructions=(
            "Use black ink or black ball-point pen.",
            "Use pencil only for drawing.",
            "Answer the questions specified in each section.",
            "Answer in the spaces provided and do not write outside the box around each page.",
            "Show all working and use diagrams where appropriate.",
        ),
        information=(
            "The marks for questions are shown in brackets.",
        ),
        mark_rows=(
            tuple(
                (
                    section.id,
                    sum(
                        question.marks
                        for question in section.options[0].questions
                    ),
                )
                for section in paper.sections
            )
            if paper.paper_id == "paper_3"
            else ()
        ),
    )


def _written_option(option: GeneratedOption) -> list[Flowable]:
    display_title = (
        option.title.split(":", 1)[0]
        if option.title.startswith("Essay ")
        else option.title
    )
    flowables: list[Flowable] = [
        Paragraph(display_title, STYLES["option_title"]),
        Spacer(1, 2 * mm),
    ]
    stimulus_style = "essay_context" if option.title.startswith("Essay ") else "extract"
    for paragraph in option.stimulus:
        flowables.extend(
            [Paragraph(paragraph, STYLES[stimulus_style]), Spacer(1, 2 * mm)]
        )
    if option.chart_values:
        flowables.extend(
            [
                _line_chart(option.chart_title, option.chart_labels, option.chart_values),
                Spacer(1, 3 * mm),
            ]
        )
    for question in option.questions:
        flowables.extend(_question_block(question))
    flowables.append(Spacer(1, 7 * mm))
    return flowables


def _paper_three_pages(paper: GeneratedPaper) -> list[Flowable]:
    mcq_section, case_section = paper.sections
    flowables: list[Flowable] = []
    cursor = 0
    mcq_page_counts = [
        1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1,
        1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 2, 1,
    ]
    for page_index, question_count in enumerate(mcq_page_counts):
        flowables.append(PageBreak())
        if page_index == 0:
            flowables.extend(
                _section_intro(mcq_section.id, mcq_section.title, mcq_section.instructions)
            )
        for option in mcq_section.options[cursor : cursor + question_count]:
            flowables.extend(
                _mcq_block(option, include_visual=question_count == 1)
            )
        cursor += question_count

    questions = case_section.options[0].questions
    page_plan = [
        (questions[0], 3),
        (questions[1], 3),
        (questions[2], 5),
    ]
    for question, continuation_pages in page_plan:
        flowables.extend(
            [
                PageBreak(),
                _section_banner(
                    f"Section {case_section.id}: {case_section.title}"
                    if question.number == "31"
                    else f"Question {question.number}"
                ),
                Spacer(1, 4 * mm),
            ]
        )
        if question.number == "31":
            flowables.extend(
                [
                    Paragraph(
                        "Answer all questions. Refer to the separate source insert for Extracts A–D.",
                        STYLES["instruction"],
                    ),
                    Spacer(1, 4 * mm),
                ]
            )
        flowables.extend([_question_table(question), Spacer(1, 4 * mm), AnswerLines(28)])
        for _ in range(continuation_pages):
            flowables.extend(
                [
                    PageBreak(),
                    Paragraph(f"Question {question.number} continued", STYLES["continuation"]),
                    Spacer(1, 3 * mm),
                    AnswerLines(34),
                ]
            )

    flowables.extend(
        [
            PageBreak(),
            Paragraph(
                "There are no questions printed on this page.", STYLES["centred_note"]
            ),
            Spacer(1, 8 * mm),
            Paragraph("DO NOT WRITE ON THIS PAGE", STYLES["continuation"]),
        ]
    )
    for _ in range(3):
        flowables.extend(
            [
                PageBreak(),
                Paragraph("Additional page, if required", STYLES["continuation"]),
                Paragraph(
                    "Write the question number in the margin before continuing your answer.",
                    STYLES["body"],
                ),
                Spacer(1, 3 * mm),
                AnswerLines(33),
            ]
        )
    flowables.extend(
        [
            PageBreak(),
            Paragraph(
                "There are no questions printed on this page.", STYLES["centred_note"]
            ),
        ]
    )
    return flowables


def _section_intro(section_id: str, title: str, instructions: str) -> list[Flowable]:
    return [
        _section_banner(f"Section {section_id}"),
        Spacer(1, 4 * mm),
        Paragraph(instructions, STYLES["instruction"]),
        Spacer(1, 5 * mm),
    ]


def _stimulus_page(option: GeneratedOption) -> list[Flowable]:
    flowables: list[Flowable] = [
        Paragraph(option.title, STYLES["option_title"]),
        Spacer(1, 2 * mm),
    ]
    for paragraph in option.stimulus:
        flowables.extend([Paragraph(paragraph, STYLES["extract"]), Spacer(1, 2 * mm)])
    if option.chart_values:
        flowables.append(_line_chart(option.chart_title, option.chart_labels, option.chart_values))
    return flowables


def _context_first_page(option: GeneratedOption) -> list[Flowable]:
    flowables: list[Flowable] = [
        Paragraph(option.title, STYLES["option_title"]),
        Spacer(1, 2 * mm),
    ]
    for paragraph in option.stimulus[:2]:
        flowables.extend(
            [Paragraph(paragraph, STYLES["extract"]), Spacer(1, 2 * mm)]
        )
    if option.chart_values:
        flowables.extend(
            [
                _context_data_table(option),
                Spacer(1, 4 * mm),
                _line_chart(
                    option.chart_title,
                    option.chart_labels,
                    option.chart_values,
                ),
            ]
        )
    return flowables


def _context_second_page(option: GeneratedOption) -> list[Flowable]:
    flowables: list[Flowable] = []
    for paragraph in option.stimulus[2:]:
        flowables.extend(
            [Paragraph(paragraph, STYLES["extract"]), Spacer(1, 3 * mm)]
        )
    return flowables


def _context_data_table(option: GeneratedOption) -> Table:
    values = option.chart_values
    rows = [
        ["Indicator", option.chart_labels[0], option.chart_labels[-1]],
        ["Activity index", f"{values[0]:.1f}", f"{values[-1]:.1f}"],
        ["Highest recorded index", "–", f"{max(values):.1f}"],
        ["Lowest recorded index", "–", f"{min(values):.1f}"],
    ]
    table = Table(
        rows,
        colWidths=[75 * mm, 38 * mm, 38 * mm],
        rowHeights=[8 * mm] * 4,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, BLACK),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    table.hAlign = "CENTER"
    return table


def _no_questions_page() -> list[Flowable]:
    height = 204 * mm
    drawing = Drawing(165 * mm, height)
    drawing.add(
        Line(
            0,
            0,
            165 * mm,
            height,
            strokeColor=BLACK,
            strokeWidth=0.7,
        )
    )
    drawing.add(
        String(
            82.5 * mm,
            height / 2,
            "DO NOT WRITE ON THIS PAGE",
            fontName=FONT_BOLD,
            fontSize=10,
            textAnchor="middle",
        )
    )
    drawing.add(
        String(
            82.5 * mm,
            height / 2 - 6 * mm,
            "ANSWER IN THE SPACES PROVIDED",
            fontName=FONT_BOLD,
            fontSize=10,
            textAnchor="middle",
        )
    )
    return [
        Paragraph(
            "There are no questions printed on this page.",
            STYLES["centred_note"],
        ),
        Spacer(1, 4 * mm),
        drawing,
    ]


def _option_questions(
    option: GeneratedOption,
    *,
    start: int = 0,
    count: int | None = None,
) -> list[Flowable]:
    questions = option.questions[start:] if count is None else option.questions[start : start + count]
    flowables: list[Flowable] = []
    for question in questions:
        flowables.extend(_question_block(question))
    return flowables


def _mcq_block(
    option: GeneratedOption,
    *,
    include_visual: bool = False,
) -> list[Flowable]:
    question = option.questions[0]
    contents: list[Flowable] = [
        _question_table(question),
        Spacer(1, 3 * mm),
    ]
    if include_visual and int(question.number) % 3 != 1:
        contents.extend([_mcq_visual(question), Spacer(1, 3 * mm)])
    contents.extend([_mcq_choice_table(question), Spacer(1, 5 * mm)])
    return [
        KeepTogether(contents)
    ]


def _mcq_choice_table(question: GeneratedQuestion) -> Table:
    rows = [
        [
            Paragraph(f"<b>{letter}</b>", STYLES["mcq_choices"]),
            Paragraph(choice, STYLES["mcq_choices"]),
            Paragraph("○", STYLES["mcq_answer"]),
        ]
        for letter, choice in zip("ABCD", question.choices, strict=True)
    ]
    table = Table(rows, colWidths=[10 * mm, 142 * mm, 9 * mm], rowHeights=[9 * mm] * 4)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("BOX", (2, 0), (2, -1), 0.45, BLACK),
                ("INNERGRID", (2, 0), (2, -1), 0.45, BLACK),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ]
        )
    )
    return table


def _mcq_visual(question: GeneratedQuestion) -> Flowable:
    if int(question.number) % 5:
        return _economic_diagram(question.topic_id, question.number)
    values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", question.prompt)]
    base = values[-2] if len(values) >= 2 else 100.0
    change = values[-1] if values else 10.0
    table = Table(
        [
            ["Indicator", "Base value", "Percentage change"],
            ["Selected economic index", f"{base:.0f}", f"+{change:.0f}%"],
        ],
        colWidths=[78 * mm, 38 * mm, 45 * mm],
        rowHeights=[10 * mm, 12 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, BLACK),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    return [
        _question_table(question),
        Spacer(1, 4 * mm),
    ]


def _question_table(question: GeneratedQuestion) -> Table:
    mark_label = "mark" if question.marks == 1 else "marks"
    return Table(
        [
            [
                _question_reference(question.number),
                Paragraph(question.prompt, STYLES["question"]),
                Paragraph(
                    f"[{question.marks} {mark_label}]",
                    STYLES["marks"],
                ),
            ]
        ],
        colWidths=[14 * mm, 134 * mm, 19 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _question_reference(number: str) -> Table:
    compact = "".join(character for character in number if character.isdigit())
    cells = list(compact.zfill(2)) if len(compact) <= 2 else [number]
    return Table(
        [cells],
        colWidths=[5.5 * mm] * len(cells),
        rowHeights=[5.5 * mm],
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.55, BLACK),
                ("FONT", (0, 0), (-1, -1), FONT_BOLD, 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _mark_scheme_question(question: GeneratedQuestion) -> list[Flowable]:
    rows = [
        [
            Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["question"]),
            Paragraph(str(question.marks), STYLES["marks"]),
        ]
    ]
    rows.extend(
        [
            [Paragraph(f"• {point}", STYLES["scheme"]), ""]
            for point in question.mark_scheme
        ]
    )
    table = Table(rows, colWidths=[157 * mm, 12 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [table, Spacer(1, 4 * mm)]


def _line_chart(title: str, labels: list[str], values: list[float]) -> Drawing:
    drawing = Drawing(165 * mm, 55 * mm)
    x0, y0, width, height = 32, 25, 410, 95
    drawing.add(String(32, 138, title, fontName=FONT_BOLD, fontSize=9))
    drawing.add(Line(x0, y0, x0, y0 + height, strokeWidth=0.8))
    drawing.add(Line(x0, y0, x0 + width, y0, strokeWidth=0.8))
    low, high = min(values), max(values)
    span = max(1.0, high - low)
    points: list[float] = []
    for index, value in enumerate(values):
        x = x0 + index * width / max(1, len(values) - 1)
        y = y0 + 8 + (value - low) / span * (height - 16)
        points.extend([x, y])
        drawing.add(String(x - 10, y0 - 14, labels[index], fontName=FONT, fontSize=7))
        drawing.add(Rect(x - 2, y - 2, 4, 4, fillColor=BLACK, strokeColor=BLACK))
        drawing.add(String(x + 4, y + 3, f"{value:.1f}", fontName=FONT, fontSize=7))
    drawing.add(PolyLine(points, strokeColor=BLACK, strokeWidth=1.2))
    return drawing


def _economic_diagram(topic_id: str, number: str) -> Drawing:
    drawing = Drawing(165 * mm, 55 * mm)
    x0, y0, width, height = 78, 28, 330, 112
    drawing.add(
        String(
            243,
            145,
            f"Figure {number}",
            fontName=FONT_BOLD,
            fontSize=9,
            textAnchor="middle",
        )
    )
    drawing.add(Line(x0, y0, x0, y0 + height, strokeWidth=0.8))
    drawing.add(Line(x0, y0, x0 + width, y0, strokeWidth=0.8))
    drawing.add(
        PolyLine(
            [
                x0 + 18,
                y0 + 100,
                x0 + 92,
                y0 + 78,
                x0 + 180,
                y0 + 52,
                x0 + 300,
                y0 + 15,
            ],
            strokeColor=BLACK,
            strokeWidth=1.1,
        )
    )
    drawing.add(
        PolyLine(
            [
                x0 + 24,
                y0 + 16,
                x0 + 106,
                y0 + 43,
                x0 + 202,
                y0 + 75,
                x0 + 294,
                y0 + 104,
            ],
            strokeColor=BLACK,
            strokeWidth=1.1,
        )
    )
    if topic_id.startswith("4.2"):
        drawing.add(String(x0 + 286, y0 + 12, "AD", fontName=FONT, fontSize=8))
        drawing.add(String(x0 + 286, y0 + 106, "AS", fontName=FONT, fontSize=8))
        drawing.add(String(x0 - 32, y0 + height, "Price level", fontName=FONT, fontSize=8))
        drawing.add(String(x0 + width - 34, y0 - 14, "Real output", fontName=FONT, fontSize=8))
    else:
        drawing.add(String(x0 + 290, y0 + 12, "D", fontName=FONT, fontSize=8))
        drawing.add(String(x0 + 292, y0 + 106, "S", fontName=FONT, fontSize=8))
        drawing.add(String(x0 - 22, y0 + height, "Price", fontName=FONT, fontSize=8))
        drawing.add(String(x0 + width - 24, y0 - 14, "Quantity", fontName=FONT, fontSize=8))
    return drawing


def _section_banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["section"])]],
        colWidths=[169 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )


def _info_box(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["body"])]],
        colWidths=[150 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.7, BLACK),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )


def _page_chrome(canvas, doc, paper_code: str, document_type: str) -> None:
    canvas.saveState()
    if document_type == "Question paper":
        canvas.setFillColor(BLACK)
        if doc.page > 1:
            canvas.setFont(FONT, 11)
            canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 13 * mm, str(doc.page))
            if paper_code == "7136/3":
                frame_x = 14 * mm
                frame_y = 27 * mm
                frame_width = 172 * mm
                frame_height = 244 * mm
                canvas.setStrokeColor(colors.HexColor("#777777"))
                canvas.setLineWidth(0.45)
                canvas.rect(frame_x, frame_y, frame_width, frame_height)
                canvas.setFont(FONT, 5.8)
                canvas.drawString(
                    frame_x + frame_width + 2.5 * mm,
                    frame_y + frame_height - 2 * mm,
                    "Do not write",
                )
                canvas.drawString(
                    frame_x + frame_width + 2.5 * mm,
                    frame_y + frame_height - 5 * mm,
                    "outside the box",
                )
                if doc.page % 2 == 1 and doc.page < 44:
                    canvas.setFont(FONT_BOLD, 9)
                    canvas.drawRightString(
                        frame_x + frame_width,
                        frame_y - 8 * mm,
                        "Turn over >",
                    )
            else:
                canvas.setStrokeColor(colors.HexColor("#777777"))
                canvas.setLineWidth(0.45)
                canvas.line(
                    14 * mm,
                    PAGE_HEIGHT - 18 * mm,
                    PAGE_WIDTH - 15 * mm,
                    PAGE_HEIGHT - 18 * mm,
                )
            if doc.page % 2 == 1:
                canvas.setFont(FONT_BOLD, 9)
                if paper_code != "7136/3":
                    canvas.drawRightString(
                        PAGE_WIDTH - 15 * mm,
                        10 * mm,
                        "Turn over >",
                    )
        canvas.setFont(FONT, 6.5)
        canvas.drawString(14 * mm, 5 * mm, f"PRACTICE/{paper_code}")
        canvas.restoreState()
        return
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.setLineWidth(0.45)
    canvas.line(16 * mm, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 12 * mm)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(16 * mm, PAGE_HEIGHT - 9 * mm, f"{paper_code} · {document_type}")
    canvas.drawRightString(PAGE_WIDTH - 17 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


class AnswerLines(Flowable):
    def __init__(self, line_count: int) -> None:
        self.line_count = line_count
        super().__init__()
        self.width = 165 * mm
        self.height = line_count * 6.2 * mm

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#666666"))
        self.canv.setLineWidth(0.5)
        self.canv.setDash(1, 1.7)
        for index in range(self.line_count):
            y = self.height - ((index + 1) * 6.2 * mm)
            self.canv.line(0, y, self.width, y)
        self.canv.setDash()


_sample = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle(
        "Body", parent=_sample["BodyText"], fontName=FONT, fontSize=11, leading=14
    ),
    "heading": ParagraphStyle(
        "Heading", parent=_sample["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14
    ),
    "cover_kicker": ParagraphStyle(
        "CoverKicker",
        parent=_sample["Heading2"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=18,
    ),
    "cover_title": ParagraphStyle(
        "CoverTitle",
        parent=_sample["Title"],
        fontName=FONT_BOLD,
        fontSize=24,
        leading=28,
        spaceAfter=6,
    ),
    "cover_subtitle": ParagraphStyle(
        "CoverSubtitle",
        parent=_sample["Heading2"],
        fontName=FONT,
        fontSize=14,
        leading=18,
    ),
    "section": ParagraphStyle(
        "Section",
        parent=_sample["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=BLACK,
        alignment=TA_CENTER,
    ),
    "instruction": ParagraphStyle(
        "Instruction",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
    ),
    "option_title": ParagraphStyle(
        "OptionTitle",
        parent=_sample["Heading3"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        spaceBefore=3,
    ),
    "extract": ParagraphStyle(
        "Extract",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=9.5,
        leading=12.5,
        borderWidth=0.4,
        borderColor=colors.HexColor("#aaaaaa"),
        borderPadding=5,
    ),
    "essay_context": ParagraphStyle(
        "EssayContext",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=11,
        leading=14,
    ),
    "question": ParagraphStyle(
        "Question",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=11,
        leading=14,
    ),
    "marks": ParagraphStyle(
        "Marks",
        parent=_sample["BodyText"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT,
    ),
    "mcq_choices": ParagraphStyle(
        "MCQChoices",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=10.5,
        leading=14,
        leftIndent=24,
    ),
    "mcq_answer": ParagraphStyle(
        "MCQAnswer",
        parent=_sample["BodyText"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    ),
    "scheme": ParagraphStyle(
        "Scheme",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=9.5,
        leading=12,
    ),
    "scheme_compact": ParagraphStyle(
        "SchemeCompact",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=9.5,
        leading=11.2,
        spaceAfter=0.8,
    ),
    "scheme_note": ParagraphStyle(
        "SchemeNote",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=7.5,
        leading=9,
        textColor=MID_GREY,
    ),
    "source_extract": ParagraphStyle(
        "SourceExtract",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=10.5,
        leading=15,
    ),
    "continuation": ParagraphStyle(
        "Continuation",
        parent=_sample["Heading3"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    ),
    "centred_note": ParagraphStyle(
        "CentredNote",
        parent=_sample["BodyText"],
        fontName=FONT,
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    ),
}
