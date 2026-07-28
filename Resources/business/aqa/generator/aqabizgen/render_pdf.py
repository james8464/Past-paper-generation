from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Ellipse, Line, PolyLine, Rect, String
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

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
)
from Backend.Core.fonts import register_fonts
from Backend.Core.generation_date import formatted_generation_date
from Backend.Core.mark_scheme_front_matter import aqa_front_matter_pages


AQA_A4 = (595.32, 841.92)
PAGE_WIDTH, PAGE_HEIGHT = AQA_A4
INK = colors.HexColor("#161616")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    if paper.paper_id == "paper_1":
        story.extend(_paper_one_pages(paper))
    elif paper.paper_id == "paper_2":
        story.extend(_paper_two_pages(paper))
    else:
        story.extend(_paper_three_pages(paper))
    doc.build(story)


def render_source_booklet(paper: GeneratedPaper, path: Path) -> None:
    if paper.paper_id != "paper_3":
        raise ValueError("only AQA Business Paper 3 has a source booklet")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Source booklet")
    option = paper.sections[0].options[0]
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Business", STYLES["kicker"]),
        Paragraph("Independent practice source booklet", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box(
            "Use these independently written fictional sources for all questions. "
            "This booklet contains no official AQA text or branding."
        ),
    ]
    for index, extract in enumerate(option.stimulus, start=1):
        story.extend(
            [
                PageBreak(),
                _banner(f"Extract {index}"),
                Spacer(1, 5 * mm),
                Paragraph(extract, STYLES["extract"]),
                Spacer(1, 7 * mm),
                _source_table(option, index),
                Spacer(1, 8 * mm),
                _chart(option, offset=index),
                Spacer(1, 6 * mm),
                Paragraph(
                    "Source note: all organisations, quotations, figures and events "
                    "on this page are independently invented for practice.",
                    STYLES["small"],
                ),
            ]
        )
    story.extend(
        [
            PageBreak(),
            Paragraph("Notes", STYLES["centre_bold"]),
            AnswerLines(34),
        ]
    )
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Business", STYLES["kicker"]),
        Paragraph("Independent practice mark scheme", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box(
            "Reward valid alternative business reasoning. Apply level descriptors "
            "holistically and credit supported judgements."
        ),
        PageBreak(),
        *aqa_front_matter_pages(
            "business",
            heading_style=STYLES["kicker"],
            body_style=STYLES["body"],
        ),
    ]
    if paper.paper_id == "paper_1":
        pages = _paper_one_mark_scheme_pages(paper)
        for index, page in enumerate(pages):
            story.extend(page)
            if index < len(pages) - 1:
                story.append(PageBreak())
        doc.build(story)
        return
    for section in paper.sections:
        story.extend([_banner(f"Section {section.id}"), Spacer(1, 4 * mm)])
        for option in section.options:
            for question in option.questions:
                story.extend(_scheme_block(question))
        story.append(PageBreak())
    story.pop()
    story.extend(_mark_scheme_extension_pages(paper))
    doc.build(story)


def _paper_one_mark_scheme_pages(paper: GeneratedPaper) -> list[list[Flowable]]:
    multiple_choice, section_b, section_c, section_d = paper.sections
    mcq_questions = [option.questions[0] for option in multiple_choice.options]
    question_16, question_17, question_18, question_19, question_20 = (
        section_b.options[0].questions
    )
    question_21, question_22 = [
        option.questions[0] for option in section_c.options
    ]
    question_23, question_24 = [
        option.questions[0] for option in section_d.options
    ]
    return [
        _objective_test_answers(mcq_questions),
        [
            Paragraph("Section B", STYLES["kicker"]),
            Spacer(1, 4 * mm),
            _financial_position_extract(section_b.options[0]),
            Spacer(1, 5 * mm),
            *_question_block(question_16),
        ],
        _calculation_marking_page(
            question_16,
            [
                "Current assets = inventories + receivables + cash.",
                "Current liabilities = payables.",
                "Current ratio = current assets ÷ current liabilities.",
                "Accept a correctly rounded ratio with or without :1.",
            ],
        ),
        _calculation_marking_page(
            question_17,
            [
                "Capital employed = total equity + non-current liabilities.",
                "ROCE = operating profit ÷ capital employed × 100.",
                "Operating profit = ROCE × capital employed ÷ 100.",
                "Credit the correct figure with the £m unit.",
            ],
        ),
        [
            _restructuring_table(section_b.options[0]),
            Spacer(1, 5 * mm),
            *_question_block(question_18),
            *_nine_mark_levels(),
        ],
        _indicative_content_page(question_18, "Question 18 marking guidance"),
        [
            *_question_block(question_19),
            *_nine_mark_levels(),
        ],
        _indicative_content_page(question_19, "Question 19 marking guidance"),
        [
            *_question_block(question_20),
            *_nine_mark_levels(),
            Spacer(1, 5 * mm),
            *_indicative_points(question_20),
        ],
        [
            Paragraph("Section C", STYLES["kicker"]),
            Spacer(1, 4 * mm),
            *_question_block(question_21),
            *_twenty_five_mark_levels(high_levels=True),
        ],
        _twenty_five_mark_continuation(question_21, "Lower-level descriptors"),
        _indicative_content_page(question_21, "Question 21 indicative content"),
        [
            *_question_block(question_22),
            *_twenty_five_mark_levels(high_levels=True),
        ],
        _twenty_five_mark_continuation(question_22, "Question 22 marking guidance"),
        [
            Paragraph("Section D", STYLES["kicker"]),
            Spacer(1, 4 * mm),
            *_question_block(question_23),
            *_twenty_five_mark_levels(high_levels=True),
        ],
        _twenty_five_mark_continuation(question_23, "Question 23 marking guidance"),
        [
            *_question_block(question_24),
            *_twenty_five_mark_levels(high_levels=True),
        ],
        _twenty_five_mark_continuation(question_24, "Lower-level descriptors"),
        [
            *_indicative_content_page(question_24, "Evaluation"),
            Spacer(1, 14 * mm),
            Paragraph("Independent practice material", STYLES["small"]),
            Paragraph(
                "Created by Paper Creator for private revision. This mark scheme is not "
                "produced, endorsed or approved by AQA or any examination board.",
                STYLES["small"],
            ),
        ],
    ]


def _objective_test_answers(
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    rows: list[list[object]] = [["Question number", "Answer"]]
    for question in questions:
        choice_index = question.correct_choice or 0
        rows.append(
            [
                question.number,
                f"{'ABCD'[choice_index]}  {question.choices[choice_index]}",
            ]
        )
    table = Table(rows, colWidths=[35 * mm, 132 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph("Section A", STYLES["kicker"]),
        Paragraph("Objective Test Answers", STYLES["heading"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 4 * mm),
        Paragraph("Total for this section: 15 marks", STYLES["answer"]),
    ]


def _calculation_marking_page(
    question: GeneratedQuestion,
    points: list[str],
) -> list[Flowable]:
    rows: list[list[object]] = [["Marking guidance", "Marks"]]
    rows.extend(
        [
            [Paragraph(point, STYLES["body"]), "1"]
            for point in points
        ]
    )
    table = Table(rows, colWidths=[148 * mm, 19 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        *_question_block(question),
        Paragraph(
            "Marks for this question: AO1 = 1 and AO2 = 3",
            STYLES["small"],
        ),
        Spacer(1, 5 * mm),
        table,
    ]


def _nine_mark_levels() -> list[Flowable]:
    rows = [
        ["Level", "Descriptor", "Marks"],
        [
            "3",
            Paragraph(
                "Developed analysis uses accurate knowledge and relevant application "
                "to form a coherent chain of reasoning.",
                STYLES["small"],
            ),
            "7–9",
        ],
        [
            "2",
            Paragraph(
                "Some relevant application and linked analysis, although development "
                "or focus is uneven.",
                STYLES["small"],
            ),
            "4–6",
        ],
        [
            "1",
            Paragraph(
                "Limited knowledge or application with isolated analytical links.",
                STYLES["small"],
            ),
            "1–3",
        ],
        ["0", "No creditworthy material.", "0"],
    ]
    table = Table(
        rows,
        colWidths=[18 * mm, 129 * mm, 20 * mm],
        rowHeights=[9 * mm, 22 * mm, 22 * mm, 22 * mm, 10 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph(
            "Marks for this question: AO1 = 2, AO2 = 3 and AO3 = 4",
            STYLES["small"],
        ),
        Spacer(1, 4 * mm),
        table,
    ]


def _twenty_five_mark_levels(
    *,
    high_levels: bool,
) -> list[Flowable]:
    levels = (
        [
            ("5", "Excellent analysis and sustained, balanced evaluation with a fully supported judgement.", "21–25"),
            ("4", "Good developed analysis and relevant evaluation with a supported judgement.", "16–20"),
            ("3", "Sound analysis and some evaluation, with uneven context or balance.", "11–15"),
        ]
        if high_levels
        else [
            ("2", "Limited analytical chains and weak or generic evaluation.", "6–10"),
            ("1", "Isolated relevant points or unsupported assertions.", "1–5"),
            ("0", "No creditworthy material.", "0"),
        ]
    )
    rows: list[list[object]] = [["Level", "Descriptor", "Marks"]]
    rows.extend(
        [
            [level, Paragraph(descriptor, STYLES["small"]), marks]
            for level, descriptor, marks in levels
        ]
    )
    descriptor_heights = (
        [9 * mm, 30 * mm, 30 * mm, 30 * mm]
        if high_levels
        else [9 * mm, 30 * mm, 30 * mm, 18 * mm]
    )
    table = Table(
        rows,
        colWidths=[18 * mm, 129 * mm, 20 * mm],
        rowHeights=descriptor_heights,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        Paragraph(
            "25-mark evaluative question: AO1 = 4, AO2 = 4, AO3 = 9 and AO4 = 8",
            STYLES["small"],
        ),
        Spacer(1, 4 * mm),
        table,
    ]


def _indicative_points(
    question: GeneratedQuestion,
    *,
    limit: int = 6,
) -> list[Flowable]:
    return [
        Paragraph(f"• {point}", STYLES["body"])
        for point in question.mark_scheme[:limit]
    ]


def _indicative_content_page(
    question: GeneratedQuestion,
    heading: str,
) -> list[Flowable]:
    return [
        Paragraph(heading, STYLES["heading"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "The demands of this question are to apply accurate business knowledge, "
            "develop connected reasoning and answer the precise issue set.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        *_indicative_points(question, limit=10),
    ]


def _twenty_five_mark_continuation(
    question: GeneratedQuestion,
    heading: str,
) -> list[Flowable]:
    return [
        Paragraph(heading, STYLES["heading"]),
        Spacer(1, 4 * mm),
        *_twenty_five_mark_levels(high_levels=False),
        Spacer(1, 6 * mm),
        *_indicative_points(question, limit=8),
    ]


MARK_SCHEME_EXTENSION_PAGE_COUNTS = {
    "paper_1": 7,
    "paper_2": 5,
    "paper_3": 3,
}


def _mark_scheme_extension_pages(paper: GeneratedPaper) -> list[Flowable]:
    count = MARK_SCHEME_EXTENSION_PAGE_COUNTS[paper.paper_id]
    questions = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
    ]
    extended = [question for question in questions if question.marks >= 9]
    pages: list[Flowable] = []
    for index in range(count):
        pages.append(PageBreak())
        if index == count - 2:
            pages.extend(_assessment_objectives_page(paper, questions))
        elif index == count - 1:
            pages.extend(_independent_practice_page())
        else:
            question = extended[index % len(extended)]
            pages.extend(_continued_marking_guidance(question, index))
    return pages


def _continued_marking_guidance(
    question: GeneratedQuestion,
    page_index: int,
) -> list[Flowable]:
    points = question.mark_scheme
    chunk_size = 9
    start = (page_index * chunk_size) % max(len(points), 1)
    chunk = (points + points)[start : start + chunk_size]
    rows = [["Indicative content and level guidance", ""]]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in chunk]
    )
    table = Table(rows, colWidths=[155 * mm, 12 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph(f"Question {question.number} guidance continued", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(question.prompt, STYLES["body"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 5 * mm),
        Paragraph(
            "Credit a different but valid business argument when it is developed, "
            "applied to the case and supports the judgement reached.",
            STYLES["body"],
        ),
    ]


def _assessment_objectives_page(
    paper: GeneratedPaper,
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    rows = [["Question", "Marks", "Assessment focus"]]
    for question in questions:
        focus = (
            "AO1, AO2, AO3 and AO4"
            if question.marks >= 9
            else "AO1 and AO2"
        )
        rows.append([question.number, str(question.marks), focus])
    table = Table(rows, colWidths=[38 * mm, 25 * mm, 104 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph("Assessment objectives grid", STYLES["heading"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 5 * mm),
        Paragraph(
            f"The candidate paper maximum is {paper.total_marks}. Verify the question "
            "subtotals and the selected level before recording the final mark.",
            STYLES["body"],
        ),
    ]


def _independent_practice_page() -> list[Flowable]:
    return [
        Spacer(1, 205 * mm),
        Paragraph("Independent practice material", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Created by Paper Creator for private revision. This mark scheme is not "
            "produced, endorsed or approved by AQA or any examination board.",
            STYLES["small"],
        ),
    ]


def _paper_one_pages(paper: GeneratedPaper) -> list[Flowable]:
    mcq, section_b, section_c, section_d = paper.sections
    pages: list[list[Flowable]] = []
    mcq_ranges = [(0, 2), (2, 5), (5, 6), (6, 8), (8, 10), (10, 12), (12, 14), (14, 15)]
    for start, stop in mcq_ranges:
        content: list[Flowable] = []
        if start == 0:
            content.extend(_intro(mcq))
        for option in mcq.options[start:stop]:
            content.extend(_mcq_block(option.questions[0]))
        pages.append(content)
    case = section_b.options[0]
    question_16, question_17, question_18, question_19, question_20 = case.questions
    pages.extend(
        [
            [
                *_intro(section_b),
                _financial_position_extract(case),
                Spacer(1, 4 * mm),
                *_question_block(question_16),
                Paragraph("Answer", STYLES["small"]),
                AnswerLines(2),
                Paragraph("Working", STYLES["small"]),
                AnswerLines(5),
            ],
            [
                *_question_block(question_17),
                Spacer(1, 4 * mm),
                Paragraph("Answer", STYLES["small"]),
                AnswerLines(2),
                Paragraph("Working", STYLES["small"]),
                AnswerLines(7),
                Spacer(1, 16 * mm),
                Paragraph("Turn over for the next question", STYLES["centre_bold"]),
            ],
            [
                _restructuring_table(case),
                Spacer(1, 5 * mm),
                *_question_block(question_18),
                AnswerLines(23),
            ],
            [
                Paragraph("Extra space", STYLES["small"]),
                AnswerLines(24),
                Spacer(1, 8 * mm),
                Paragraph("Turn over for the next question", STYLES["centre_bold"]),
            ],
            [*_question_block(question_19), AnswerLines(29)],
            [*_question_block(question_20), AnswerLines(29)],
            [*_intro(section_c), *_choice_prompts(section_c)],
        ]
    )
    pages.extend(
        [[AnswerLines(34)] for _ in range(5)]
    )
    pages.append([*_intro(section_d), *_choice_prompts(section_d)])
    pages.extend(
        [[AnswerLines(34)] for _ in range(5)]
    )
    pages.extend(
        [
            _no_questions_page(),
            _additional_answer_page(),
            _additional_answer_page(),
            _additional_answer_page(),
            _no_questions_page(include_legal_notice=True),
        ]
    )
    assert len(pages) == 31
    return _page_sequence(pages)


def _paper_two_pages(paper: GeneratedPaper) -> list[Flowable]:
    pages: list[list[Flowable]] = []
    for section in paper.sections:
        option = section.options[0]
        questions = option.questions
        pages.extend(
            [
                [
                    *_intro(section),
                    Paragraph(option.title, STYLES["option"]),
                    Paragraph(option.stimulus[0], STYLES["extract"]),
                    Spacer(1, 3 * mm),
                    Paragraph(option.stimulus[1], STYLES["extract"]),
                ],
                [
                    Paragraph(option.stimulus[2], STYLES["extract"]),
                    Spacer(1, 4 * mm),
                    _chart(option),
                    *_question_block(questions[0]),
                    AnswerLines(5),
                    *(
                        [*_question_block(questions[1]), AnswerLines(7)]
                        if len(questions) == 4
                        else []
                    ),
                ],
            ]
        )
        analysis_index = 2 if len(questions) == 4 else 1
        evaluation_index = 3 if len(questions) == 4 else 2
        pages.extend(
            [
                [
                    _banner(f"Question {questions[analysis_index].number}"),
                    *_question_block(questions[analysis_index]),
                    AnswerLines(24),
                ],
                [
                    _banner(f"Question {questions[evaluation_index].number}"),
                    *_question_block(questions[evaluation_index]),
                    AnswerLines(25),
                ],
                [
                    Paragraph(
                        f"Question {questions[evaluation_index].number} continued",
                        STYLES["centre_bold"],
                    ),
                    AnswerLines(34),
                ],
            ]
        )
    pages.extend(
        [[Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(8)]
    )
    assert len(pages) == 23
    return _page_sequence(pages)


def _paper_three_pages(paper: GeneratedPaper) -> list[Flowable]:
    option = paper.sections[0].options[0]
    allocations = [3, 3, 4, 4, 5, 6]
    pages: list[list[Flowable]] = []
    for question, allocation in zip(option.questions, allocations, strict=True):
        pages.append(
            [
                _banner(f"Question {question.number}"),
                Spacer(1, 4 * mm),
                *_question_block(question),
                AnswerLines(25),
            ]
        )
        pages.extend(
            [
                [
                    Paragraph(
                        f"Question {question.number} continued",
                        STYLES["centre_bold"],
                    ),
                    AnswerLines(34),
                ]
                for _ in range(allocation - 1)
            ]
        )
    pages.extend(
        [[Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(2)]
    )
    assert len(pages) == 27
    return _page_sequence(pages)


def _page_sequence(pages: list[list[Flowable]]) -> list[Flowable]:
    result: list[Flowable] = []
    for page in pages:
        result.append(PageBreak())
        result.extend(page)
    return result


def _intro(section) -> list[Flowable]:
    return [
        Table(
            [
                [Paragraph(f"<b>Section {section.id}</b>", STYLES["centre_bold"])],
                [Paragraph(section.instructions, STYLES["instruction"])],
            ],
            colWidths=[167 * mm],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, -1), (-1, -1), 0.65, INK),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 4 * mm),
    ]


def _choice_prompts(section) -> list[Flowable]:
    option_numbers = [option.questions[0].number for option in section.options]
    result: list[Flowable] = [
        Paragraph(
            "Shade the lozenge below to indicate which optional question you have answered.",
            STYLES["body"],
        ),
        Spacer(1, 3 * mm),
        Table(
            [
                [
                    Paragraph(
                        f"<b>Question {option_numbers[0]}</b>",
                        STYLES["body"],
                    ),
                    _lozenge(),
                    Spacer(1, 10 * mm),
                    Paragraph(
                        f"<b>Question {option_numbers[1]}</b>",
                        STYLES["body"],
                    ),
                    _lozenge(),
                ],
            ],
            colWidths=[40 * mm, 18 * mm, 14 * mm, 40 * mm, 18 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 2),
                ]
            ),
        ),
        Spacer(1, 5 * mm),
    ]
    for index, option in enumerate(section.options):
        if index:
            result.extend(
                [Spacer(1, 7 * mm), Paragraph("OR", STYLES["centre_bold"]), Spacer(1, 7 * mm)]
            )
        result.extend(_question_block(option.questions[0]))
    return result


def _financial_position_extract(option: GeneratedOption) -> Table:
    values = [int(round(value)) for value in option.chart_values]
    inventories = values[0]
    receivables = int(values[1] * 0.42)
    cash = int(values[2] * 0.35)
    payables = int(values[3] * 0.66)
    rows = [
        ["Extract from statement of financial position", "£m", "£m"],
        ["Non-current assets", "", f"{int(values[4] * 3.35)}"],
        ["Inventories", f"{inventories}", ""],
        ["Receivables", f"{receivables}", ""],
        ["Cash", f"{cash}", ""],
        ["Payables", f"({payables})", ""],
        [
            "Net current assets",
            "",
            f"{inventories + receivables + cash - payables}",
        ],
        ["Non-current liabilities", "", f"{int(values[2] * 2.3)}"],
        ["Total equity", "", f"{int(values[1] * 1.9)}"],
    ]
    table = Table(
        rows,
        colWidths=[92 * mm, 25 * mm, 25 * mm],
        rowHeights=[9 * mm, *([8 * mm] * 8)],
        style=TableStyle(
            [
                ("SPAN", (0, 0), (0, 0)),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, INK),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
                ("LINEBELOW", (1, -1), (-1, -1), 0.5, INK),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    table.hAlign = "CENTER"
    return table


def _restructuring_table(option: GeneratedOption) -> Table:
    values = [int(round(value)) for value in option.chart_values]
    rows = [
        ["Feature", "Before restructuring", "After restructuring"],
        ["Number of staff", str(values[4] * 34), str(values[3] * 31)],
        ["Average span of control", "5", "15"],
        ["Levels of hierarchy", "6", "4"],
    ]
    table = Table(
        rows,
        colWidths=[72 * mm, 40 * mm, 40 * mm],
        rowHeights=[10 * mm] * 4,
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    table.hAlign = "CENTER"
    return table


def _mcq_context(question: GeneratedQuestion) -> list[Flowable]:
    number = int("".join(character for character in question.number if character.isdigit()))
    if number == 6:
        return [_break_even_diagram(), Spacer(1, 3 * mm)]
    if number == 7:
        return [
            _compact_data_table(
                [
                    ["Financial data", "£m"],
                    ["Sales revenue", "20"],
                    ["Cost of sales", "6"],
                    ["Operating expenses", "4"],
                    ["Taxation", "7"],
                ],
                [72 * mm, 28 * mm],
            ),
            Spacer(1, 3 * mm),
        ]
    if number == 10:
        return [
            _compact_data_table(
                [
                    ["Factory", "Output", "Employees"],
                    ["Factory A", "900", "60"],
                    ["Factory B", "840", "40"],
                    ["Factory C", "800", "50"],
                    ["Factory D", "750", "50"],
                ],
                [48 * mm, 35 * mm, 35 * mm],
            ),
            Spacer(1, 3 * mm),
        ]
    if number == 12:
        return [
            _compact_data_table(
                [
                    ["Option", "External change", "Strategic change"],
                    ["A", "High", "High"],
                    ["B", "High", "Low"],
                    ["C", "Low", "High"],
                    ["D", "Low", "Low"],
                ],
                [30 * mm, 48 * mm, 48 * mm],
            ),
            Spacer(1, 3 * mm),
        ]
    if number == 13:
        return [
            _compact_data_table(
                [
                    ["Measure of performance", "Target", "Actual"],
                    ["Capacity utilisation", "90%", "88%"],
                    ["Labour turnover", "12%", "17%"],
                    ["Market share", "13%", "15%"],
                    ["ROCE", "16%", "12%"],
                ],
                [70 * mm, 30 * mm, 30 * mm],
            ),
            Spacer(1, 3 * mm),
        ]
    return []


def _compact_data_table(rows: list[list[str]], widths: list[float]) -> Table:
    table = Table(rows, colWidths=widths, rowHeights=[7 * mm] * len(rows))
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    table.hAlign = "CENTER"
    return table


def _break_even_diagram() -> Drawing:
    drawing = Drawing(155 * mm, 62 * mm)
    x0, y0, width, height = 75, 25, 330, 120
    drawing.add(
        String(
            x0,
            y0 + height + 18,
            "Figure 1: change in the break-even point",
            fontName=FONT_BOLD,
            fontSize=9,
        )
    )
    drawing.add(Line(x0, y0, x0, y0 + height, strokeColor=INK))
    drawing.add(Line(x0, y0, x0 + width, y0, strokeColor=INK))
    drawing.add(String(x0 - 50, y0 + height - 4, "Costs /", fontName=FONT, fontSize=8))
    drawing.add(String(x0 - 50, y0 + height - 14, "revenue", fontName=FONT, fontSize=8))
    drawing.add(String(x0 + width - 30, y0 - 18, "Output", fontName=FONT, fontSize=8))
    drawing.add(Line(x0, y0 + 35, x0 + width, y0 + 105, strokeColor=INK))
    drawing.add(Line(x0, y0 + 35, x0 + width, y0 + 82, strokeColor=INK))
    drawing.add(Line(x0, y0, x0 + width, y0 + 115, strokeColor=INK))
    drawing.add(Line(x0, y0, x0 + width, y0 + 92, strokeColor=INK))
    drawing.add(String(x0 + width - 8, y0 + 106, "TR1", fontName=FONT, fontSize=7))
    drawing.add(String(x0 + width - 8, y0 + 83, "TR2", fontName=FONT, fontSize=7))
    drawing.add(String(x0 + width - 8, y0 + 116, "TC1", fontName=FONT, fontSize=7))
    drawing.add(String(x0 + width - 8, y0 + 93, "TC2", fontName=FONT, fontSize=7))
    drawing.add(String(x0 + 150, y0 + 53, "M", fontName=FONT_BOLD, fontSize=8))
    drawing.add(String(x0 + 220, y0 + 70, "N", fontName=FONT_BOLD, fontSize=8))
    return drawing


def _do_not_write_drawing(height: float = 226 * mm) -> Drawing:
    drawing = Drawing(167 * mm, height)
    drawing.add(Line(0, 0, 167 * mm, height, strokeColor=INK, strokeWidth=0.7))
    drawing.add(
        String(
            83.5 * mm,
            height / 2,
            "DO NOT WRITE ON THIS PAGE",
            fontName=FONT_BOLD,
            fontSize=10,
            textAnchor="middle",
        )
    )
    drawing.add(
        String(
            83.5 * mm,
            height / 2 - 6 * mm,
            "ANSWER IN THE SPACES PROVIDED",
            fontName=FONT_BOLD,
            fontSize=10,
            textAnchor="middle",
        )
    )
    return drawing


def _no_questions_page(
    *,
    include_legal_notice: bool = False,
) -> list[Flowable]:
    height = 178 * mm if include_legal_notice else 226 * mm
    content: list[Flowable] = [
        Paragraph(
            "There are no questions printed on this page",
            STYLES["centre_bold"],
        ),
        Spacer(1, 3 * mm),
        _do_not_write_drawing(height),
    ]
    if include_legal_notice:
        content.extend(
            [
                Spacer(1, 7 * mm),
                Paragraph("Independent practice material", STYLES["small"]),
                Paragraph(
                    "Created by Paper Creator for private revision. This paper is not "
                    "produced, endorsed or approved by AQA or any examination board.",
                    STYLES["small"],
                ),
            ]
        )
    return content


def _additional_answer_page() -> list[Flowable]:
    row_count = 25
    rows: list[list[object]] = [
        [
            Paragraph("Question<br/>number", STYLES["marks"]),
            Paragraph(
                "<b>Additional page, if required</b><br/>"
                "Write the question numbers in the left-hand margin.",
                STYLES["centre_bold"],
            ),
        ],
        *[["", ""] for _ in range(row_count)],
    ]
    table = Table(
        rows,
        colWidths=[14 * mm, 153 * mm],
        rowHeights=[10 * mm, *([8.2 * mm] * row_count)],
    )
    style = [
        ("BOX", (0, 0), (-1, -1), 0.65, INK),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 2),
    ]
    for row in range(1, row_count + 1):
        style.append(("LINEBELOW", (1, row), (1, row), 0.35, colors.grey))
    table.setStyle(TableStyle(style))
    return [table]


def _mcq_block(question: GeneratedQuestion) -> list[Flowable]:
    choices = Table(
        [
            [
                Paragraph(f"<b>{'ABCD'[index]}</b>", STYLES["choices"]),
                Paragraph(text, STYLES["choices"]),
                _lozenge(),
            ]
            for index, text in enumerate(question.choices)
        ],
        colWidths=[9 * mm, 119 * mm, 12 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]),
    )
    return [
        KeepTogether(
            [
                _question_table(question),
                Spacer(1, 2 * mm),
                *_mcq_context(question),
                choices,
                Spacer(1, 5 * mm),
            ]
        )
    ]


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    return [_question_table(question), Spacer(1, 3 * mm)]


def _question_table(question: GeneratedQuestion) -> Table:
    mark_label = "mark" if question.marks == 1 else "marks"
    return Table(
        [
            [
                _question_reference(question.number),
                Paragraph(question.prompt, STYLES["body"]),
                Paragraph(f"[{question.marks} {mark_label}]", STYLES["marks"]),
            ]
        ],
        colWidths=[14 * mm, 134 * mm, 19 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
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
        style=TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.55, INK),
            ("FONT", (0, 0), (-1, -1), FONT_BOLD, 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 0),
        ]),
    )


def _lozenge() -> Drawing:
    drawing = Drawing(25, 15)
    drawing.add(Rect(1, 1, 22, 13, strokeColor=INK, fillColor=None, strokeWidth=0.7))
    drawing.add(Ellipse(12, 7.5, 4, 2.2, strokeColor=INK, fillColor=None, strokeWidth=0.6))
    return drawing


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
    rows = [
        [
            Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]),
            str(question.marks),
        ]
    ]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in question.mark_scheme]
    )
    table = Table(rows, colWidths=[155 * mm, 12 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [table, Spacer(1, 4 * mm)]


def _source_table(option: GeneratedOption, index: int) -> Table:
    values = _source_values(option, index)
    rows = [
        ["Measure", "2023", "2024", "2025"],
        [
            "Performance index",
            f"{values[2]:.1f}",
            f"{values[3]:.1f}",
            f"{values[4]:.1f}",
        ],
        ["Employee engagement", f"{54 + index}%", f"{57 + index}%", f"{59 + index}%"],
        ["Capacity utilisation", f"{68 + index}%", f"{72 + index}%", f"{70 + index}%"],
    ]
    table = Table(rows, colWidths=[60 * mm, 32 * mm, 32 * mm, 32 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, INK),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _chart(option: GeneratedOption, offset: int = 0) -> Drawing:
    drawing = Drawing(165 * mm, 45 * mm)
    x0, y0, width, height = 30, 22, 420, 78
    drawing.add(
        String(30, 116, option.chart_title, fontName=FONT_BOLD, fontSize=9)
    )
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    values = (
        _source_values(option, offset)
        if offset
        else list(option.chart_values)
    )
    low, high = min(values), max(values)
    span = max(1.0, high - low)
    points: list[float] = []
    for index, value in enumerate(values):
        x = x0 + index * width / 4
        y = y0 + 7 + (value - low) / span * (height - 14)
        points.extend([x, y])
        drawing.add(Rect(x - 2, y - 2, 4, 4, fillColor=INK))
        drawing.add(String(x - 8, y0 - 13, option.chart_labels[index], fontSize=7))
        drawing.add(String(x + 4, y + 2, f"{value:.1f}", fontSize=7))
    drawing.add(PolyLine(points, strokeColor=INK, strokeWidth=1.2))
    return drawing


def _source_values(option: GeneratedOption, index: int) -> list[float]:
    multiplier = 1 + (index - 1) * 0.03
    return [round(value * multiplier, 1) for value in option.chart_values]


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Business", STYLES["kicker"]),
        Paragraph("Independent practice paper", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        Table(
            [
                ["Time allowed", "2 hours"],
                ["Maximum mark", "100"],
                ["Paper reference", paper.paper_code],
            ],
            colWidths=[45 * mm, 90 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.6, INK),
                    ("BACKGROUND", (0, 0), (0, -1), GREY),
                    ("FONT", (0, 0), (0, -1), FONT_BOLD),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 9 * mm),
        Paragraph("Instructions", STYLES["heading"]),
        Paragraph(
            "Answer the questions specified in each section. Use a calculator where "
            "appropriate. Show working and use the evidence supplied.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Information", STYLES["heading"]),
        Paragraph(
            "The maximum mark is 100. Marks are shown in brackets. This independently "
            "created practice paper is mapped to AQA 7132 but is not produced or "
            "endorsed by AQA.",
            STYLES["body"],
        ),
    ]


def _document(path: Path, paper: GeneratedPaper, kind: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path),
        pagesize=AQA_A4,
        leftMargin=18 * mm,
        rightMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="Paper creator",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(
        PageTemplate(
            id="aqa-business-practice",
            frames=[frame],
            onPage=lambda canvas, value: _chrome(
                canvas, value, paper.paper_code, kind
            ),
        )
    )
    return doc


def _chrome(canvas, doc, code: str, kind: str) -> None:
    canvas.saveState()
    if kind == "Question paper" and doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#666666"))
        canvas.setLineWidth(0.45)
        canvas.rect(14 * mm, 15 * mm, 184 * mm, 267 * mm, stroke=1, fill=0)
        canvas.setFillColor(INK)
        canvas.setFont(FONT, 9)
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 10 * mm, str(doc.page))
        canvas.setFont(FONT, 5.8)
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 19 * mm, "Do not write")
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 22 * mm, "outside the")
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 25 * mm, "box")
        canvas.setFont(FONT_BOLD, 9)
        if code == "7132/1" and doc.page == 27:
            canvas.drawCentredString(PAGE_WIDTH / 2, 17 * mm, "END OF QUESTIONS")
        elif code != "7132/1" or doc.page < 27:
            canvas.drawRightString(PAGE_WIDTH - 13 * mm, 11 * mm, "Turn over >")
        canvas.setFont(FONT, 6.5)
        canvas.drawString(14 * mm, 9 * mm, f"PRACTICE/{code}")
        canvas.restoreState()
        return
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(
        18 * mm, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 13 * mm
    )
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, PAGE_HEIGHT - 10 * mm, f"{code} · {kind}")
    canvas.drawRightString(PAGE_WIDTH - 17 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["banner"])]],
        colWidths=[167 * mm],
        style=TableStyle(
            [("BACKGROUND", (0, 0), (-1, -1), INK), ("PADDING", (0, 0), (-1, -1), 7)]
        ),
    )


def _box(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["body"])]],
        colWidths=[150 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, INK),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )


class AnswerLines(Flowable):
    def __init__(self, count: int) -> None:
        super().__init__()
        self.width = 167 * mm
        self.height = count * 6.0 * mm
        self.count = count

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#b5b5b5"))
        self.canv.setLineWidth(0.35)
        for index in range(self.count):
            y = self.height - (index + 1) * 6.0 * mm
            self.canv.line(0, y, self.width, y)


_base = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName=FONT, fontSize=9.2, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=12, leading=15, textColor=colors.white),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "option": ParagraphStyle("option", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11.5, leading=15),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName=FONT, fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=13, alignment=TA_RIGHT),
    "choices": ParagraphStyle("choices", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=17, leftIndent=22),
    "answer": ParagraphStyle("answer", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=12, alignment=TA_RIGHT),
    "centre_bold": ParagraphStyle("centre", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_CENTER),
}
