from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
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


PAGE_WIDTH, PAGE_HEIGHT = A4
OCR_MARK_SCHEME_FRONT_SIZE = (594.96, 842.04)
OCR_MARK_SCHEME_LANDSCAPE_SIZE = (841.92, 595.32)
OCR_MARK_SCHEME_FINAL_SIZE = (595.32, 841.92)
INK = colors.HexColor("#161616")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
FONT_MONO = "AQACourier"
register_fonts(FONT, FONT_BOLD, FONT_MONO)

QUESTION_PAGE_CHUNKS = {
    "paper_1": {
        "1": [2, 2, 2, 2],
        "2": [2, 2, 1, 1, 1],
        "3": [3, 2],
        "4": [3, 3],
        "5": [4, 0],
        "6": [1, 2, 1, 0],
        "7": [1, 0],
        "8": [2, 1],
        "9": [1],
        "10": [2],
    },
    "paper_2": {
        "1": [2, 2],
        "2": [1, 0],
        "3": [1, 1, 1, 0],
        "4": [3, 0],
        "5": [2, 1],
        "6": [4, 3],
        "7": [2, 2, 1, 0],
        "8": [3, 2],
        "9": [1, 2, 2, 1, 1, 1, 1, 0],
    },
}
BLANK_QUESTION_PAGES = {
    ("paper_1", "5"),
    ("paper_1", "6"),
    ("paper_2", "4"),
    ("paper_2", "7"),
}

# Each tuple is (top-level question index, part index, segment, segment count).
# The plans reproduce the June 2024 mark-scheme question boundaries page for page.
MARK_SCHEME_PAGE_PLANS = {
    "paper_1": [
        [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1)],
        [(0, 3, 1, 1), (0, 4, 1, 1), (0, 5, 1, 1)],
        [(0, 6, 1, 1), (0, 7, 1, 1)],
        [(1, 0, 1, 1), (1, 1, 1, 1)],
        [(1, 2, 1, 1)],
        [(1, 3, 1, 1)],
        [(1, 4, 1, 1)],
        [(1, 5, 1, 1)],
        [(1, 6, 1, 1)],
        [(2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)],
        [(2, 3, 1, 1), (2, 4, 1, 1)],
        [(3, index, 1, 1) for index in range(6)],
        [(4, 0, 1, 1), (4, 1, 1, 1)],
        [(4, 2, 1, 1), (4, 3, 1, 1)],
        [(5, 0, 1, 3)],
        [(5, 0, 2, 3)],
        [(5, 0, 3, 3)],
        [(5, 1, 1, 1)],
        [(5, 2, 1, 1)],
        [(5, 3, 1, 1)],
        [(6, 0, 1, 3)],
        [(6, 0, 2, 3)],
        [(6, 0, 3, 3)],
        [(7, index, 1, 1) for index in range(3)],
        [(8, 0, 1, 2)],
        [(8, 0, 2, 2)],
        [(9, 0, 1, 1), (9, 1, 1, 1)],
    ],
    "paper_2": [
        [(0, index, 1, 1) for index in range(4)],
        [(1, 0, 1, 1)],
        [(2, 0, 1, 1)],
        [(2, 1, 1, 1)],
        [(2, 2, 1, 1)],
        [(3, index, 1, 1) for index in range(3)],
        [(4, index, 1, 1) for index in range(3)],
        [(5, index, 1, 1) for index in range(7)],
        [(6, 0, 1, 1), (6, 1, 1, 1), (6, 2, 1, 1)],
        [(6, 3, 1, 2)],
        [(6, 3, 2, 2), (6, 4, 1, 1), (7, 0, 1, 1)],
        [(7, 1, 1, 1), (7, 2, 1, 1), (7, 3, 1, 1), (7, 4, 1, 1)],
        [(8, 0, 1, 1), (8, 1, 1, 1)],
        [(8, 2, 1, 1), (8, 3, 1, 1)],
        [(8, 4, 1, 1)],
        [(8, 5, 1, 1)],
        [(8, 6, 1, 1)],
        [(8, 7, 1, 1)],
        [(8, 8, 1, 2)],
        [(8, 8, 2, 2)],
    ],
}


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    if paper.paper_id == "paper_1":
        story.extend(
            [
                PageBreak(),
                Spacer(1, 55 * mm),
                Paragraph("BLANK PAGE", STYLES["centre_bold"]),
                Spacer(1, 18 * mm),
                Paragraph("Please do not write on this page.", STYLES["centre"]),
            ]
        )
    for section_index, section in enumerate(paper.sections):
        if paper.paper_id == "paper_2" and section_index == 0:
            section.options[0].title = "Section A · Question 1"
        elif paper.paper_id == "paper_2" and section_index == 8:
            story.extend(
                [
                    PageBreak(),
                    _banner("Section B"),
                    Spacer(1, 6 * mm),
                    Paragraph(
                        "Read the following independently written programming scenario. "
                        "Answer all parts of Question 9.",
                        STYLES["instruction"],
                    ),
                    Spacer(1, 6 * mm),
                    Paragraph(section.options[0].stimulus[0], STYLES["extract"]),
                    Spacer(1, 5 * mm),
                    _trace_table(section.options[0]),
                ]
            )
        story.extend(
            _question_group_pages(
                paper.paper_id,
                section.options[0],
                include_section_page=not (
                    paper.paper_id == "paper_2" and section_index == 8
                ),
            )
        )
    if paper.paper_id == "paper_1":
        story.extend(_additional_pages(1))
    else:
        story.extend(_additional_pages(3))
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Computer Science", STYLES["kicker"]),
        Paragraph("Independent practice mark scheme", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box(
            "Award valid technical alternatives. Apply level descriptors "
            "holistically to extended responses."
        ),
        PageBreak(),
        Paragraph("Marking instructions", STYLES["heading"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "Apply the mark scheme consistently. Credit technically correct "
            "alternatives and judge extended responses as a whole.",
            STYLES["body"],
        ),
        Spacer(1, 6 * mm),
        _box(
            "Indicative content is not exhaustive. Equivalent valid algorithms, "
            "explanations and terminology should be rewarded."
        ),
        NextPageTemplate("ocr-cs-mark-scheme-landscape"),
        PageBreak(),
        *_supplementary_marking_pages(
            6 if paper.paper_id == "paper_1" else 4
        ),
        PageBreak(),
    ]
    story.extend(_mark_scheme_content_pages(paper))
    story.extend(
        [
            NextPageTemplate("ocr-cs-mark-scheme-final"),
            PageBreak(),
            Paragraph("Independent practice material", STYLES["heading"]),
            Spacer(1, 5 * mm),
            Paragraph(
                "This mark scheme was created by Paper Creator for private revision. "
                "It is not produced, endorsed or approved by OCR or any examination board.",
                STYLES["body"],
            ),
        ]
    )
    doc.build(story)


def _mark_scheme_content_pages(paper: GeneratedPaper) -> list[Flowable]:
    pages: list[Flowable] = []
    plan = MARK_SCHEME_PAGE_PLANS[paper.paper_id]
    content_width = 268 * mm if paper.paper_id == "paper_1" else 260 * mm
    for page_index, items in enumerate(plan):
        if page_index:
            pages.append(PageBreak())
        questions = [
            (
                paper.sections[section_index].options[0].questions[question_index],
                segment,
                segment_count,
            )
            for section_index, question_index, segment, segment_count in items
        ]
        pages.append(_scheme_page_table(questions, content_width))
    return pages


def _scheme_page_table(
    items: list[tuple[GeneratedQuestion, int, int]],
    content_width: float,
) -> Table:
    rows: list[list[object]] = [
        [
            Paragraph("Question", STYLES["scheme_header"]),
            Paragraph("Answer", STYLES["scheme_header"]),
            Paragraph("Mark", STYLES["scheme_header"]),
            Paragraph("Guidance", STYLES["scheme_header"]),
        ]
    ]
    item_count = len(items)
    for question, segment, segment_count in items:
        rows.append(
            [
                Paragraph(
                    escape(question.number)
                    + (" continued" if segment > 1 else ""),
                    STYLES["scheme_small"],
                ),
                _scheme_answer(question, segment, segment_count, item_count),
                Paragraph(
                    str(question.marks) if segment == 1 else "",
                    STYLES["scheme_small_centre"],
                ),
                Paragraph(
                    _scheme_guidance(question, segment, segment_count),
                    STYLES["scheme_small"],
                ),
            ]
        )
    body_height = 148 * mm
    row_heights = [8 * mm, *([body_height / item_count] * item_count)]
    question_width = 22 * mm
    mark_width = 16 * mm
    guidance_width = 48 * mm
    answer_width = content_width - question_width - mark_width - guidance_width
    table = Table(
        rows,
        colWidths=[question_width, answer_width, mark_width, guidance_width],
        rowHeights=row_heights,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7e7e7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _scheme_answer(
    question: GeneratedQuestion,
    segment: int,
    segment_count: int,
    item_count: int,
) -> Paragraph:
    points = question.mark_scheme
    if segment_count > 1:
        chunk_size = max(1, math.ceil(len(points) / segment_count))
        start = (segment - 1) * chunk_size
        selected = points[start : start + chunk_size]
    else:
        limit = 2 if item_count >= 4 else 4 if item_count >= 2 else len(points)
        selected = points[:limit]
    prompt = escape(question.prompt) if segment == 1 else "<b>Indicative content continued</b>"
    bullets = "<br/>".join(f"• {escape(point)}" for point in selected)
    return Paragraph(
        f"{prompt}<br/><br/>{bullets}",
        STYLES["scheme_small"],
    )


def _scheme_guidance(
    question: GeneratedQuestion,
    segment: int,
    segment_count: int,
) -> str:
    if question.marks >= 9:
        text = (
            "Use the whole response. Start at the highest level and work down. "
            "Reward a supported technical judgement."
        )
    elif question.kind in {"programming", "trace", "calculation"}:
        text = (
            "Credit a technically correct equivalent method. Apply follow-through "
            "where the stated working remains coherent."
        )
    else:
        text = (
            "Credit an equivalent precise answer. Do not award the same technical "
            "point twice."
        )
    if segment_count > 1:
        text += f" Guidance segment {segment} of {segment_count}."
    return escape(text)


def _supplementary_marking_pages(count: int) -> list[Flowable]:
    topics = [
        (
            "Applying the mark scheme",
            "Read the whole response before awarding a mark. Match each credited point "
            "to the question set and do not award the same idea twice.",
            "Where a candidate carries an earlier error through consistently, award later "
            "method marks when the reasoning remains technically sound.",
        ),
        (
            "Algorithms and program code",
            "Accept equivalent pseudocode, structured English or program code when the "
            "logic is unambiguous and fulfils the stated requirements.",
            "Check boundary conditions, validation, loop termination, data types and the "
            "consistency of identifiers before awarding full technical credit.",
        ),
        (
            "Extended responses",
            "Place the response in the level that best describes it as a whole, then use "
            "the quality of technical evidence and judgement to select a mark.",
            "A balanced answer need not give equal space to every view, but its conclusion "
            "must follow from the reasoning and the supplied context.",
        ),
        (
            "Tables, diagrams and traces",
            "Credit correct labels, directions, intermediate values and final states. "
            "Ignore minor presentation differences that do not alter the technical meaning.",
            "For a trace, award a value only when it follows from the candidate's stated "
            "algorithm; for a diagram, require enough labels to remove ambiguity.",
        ),
        (
            "Levels of response",
            "Start at the highest level and work down until the response meets the "
            "descriptor. Use the response as a whole rather than counting isolated points.",
            "Use technical accuracy, application, development and the quality of the "
            "conclusion to decide where within the selected level the mark should sit.",
        ),
        (
            "Quality assurance",
            "Check every part, transferred total and level decision before completing the "
            "script. Apply the same threshold to equivalent answers throughout the cohort.",
            "Where an alternative answer is technically valid, record why it meets the "
            "question demand and award it consistently whenever the same reasoning occurs.",
        ),
    ]
    pages: list[Flowable] = []
    for index, (title, first, second) in enumerate(topics[:count]):
        if index:
            pages.append(PageBreak())
        pages.extend(
            [
                Paragraph(title, STYLES["heading"]),
                Spacer(1, 5 * mm),
                Paragraph(first, STYLES["body"]),
                Spacer(1, 5 * mm),
                Paragraph(second, STYLES["body"]),
            ]
        )
    return pages


def _question_group_pages(
    paper_id: str,
    option: GeneratedOption,
    *,
    include_section_page: bool,
) -> list[Flowable]:
    chunk_sizes = QUESTION_PAGE_CHUNKS[paper_id][option.id.removeprefix("Q")]
    chunks: list[list[GeneratedQuestion]] = []
    cursor = 0
    for size in chunk_sizes:
        chunks.append(option.questions[cursor : cursor + size])
        cursor += size
    if cursor != len(option.questions):
        raise ValueError(f"page allocation does not cover {option.title}")

    result: list[Flowable] = []
    for chunk_index, questions in enumerate(chunks):
        if chunk_index or include_section_page:
            result.append(PageBreak())
        if not questions:
            if (paper_id, option.id.removeprefix("Q")) in BLANK_QUESTION_PAGES:
                result.extend(
                    [
                        Spacer(1, 55 * mm),
                        Paragraph("BLANK PAGE", STYLES["centre_bold"]),
                        Spacer(1, 18 * mm),
                        Paragraph(
                            "PLEASE DO NOT WRITE ON THIS PAGE",
                            STYLES["centre"],
                        ),
                    ]
                )
            else:
                result.extend(
                    [
                        Paragraph(
                            f"{option.title} answer continued",
                            STYLES["centre_bold"],
                        ),
                        Spacer(1, 4 * mm),
                        AnswerLines(34),
                    ]
                )
            continue
        if chunk_index == 0:
            result.extend([_banner(option.title), Spacer(1, 3 * mm)])
            if include_section_page:
                result.extend(
                    [
                        Paragraph(option.stimulus[0], STYLES["extract"]),
                        Spacer(1, 3 * mm),
                    ]
                )
                topic_id = questions[0].topic_id
                if topic_id in {
                    "systems-1",
                    "systems-2",
                    "systems-4",
                    "systems-5",
                    "algorithms-2",
                    "algorithms-4",
                    "algorithms-5",
                }:
                    result.extend(
                        [
                            Preformatted(option.stimulus[1], STYLES["code"]),
                            Spacer(1, 2 * mm),
                        ]
                    )
                else:
                    result.extend([_trace_table(option), Spacer(1, 2 * mm)])
        else:
            result.extend(
                [
                    Paragraph(f"{option.title} continued", STYLES["centre_bold"]),
                    Spacer(1, 4 * mm),
                ]
            )
        for question in questions:
            result.extend(_question_block(question))
    return result


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    line_count = min(18, question.marks + (5 if question.marks >= 6 else 2))
    return [
        _question_table(question),
        Spacer(1, 2 * mm),
        *_response_space(question, line_count),
        Spacer(1, 4 * mm),
    ]


def _response_space(
    question: GeneratedQuestion,
    line_count: int,
) -> list[Flowable]:
    if question.kind == "trace":
        iterations = 6 if "6 iterations" in question.prompt else 5
        rows = [["Iteration", "Changed variables", "Output"]]
        rows.extend([[str(index), "", ""] for index in range(1, iterations + 1)])
        table = Table(
            rows,
            colWidths=[25 * mm, 90 * mm, 50 * mm],
            rowHeights=[8 * mm, *([7 * mm] * iterations)],
        )
        table.setStyle(_response_table_style())
        return [table]
    if question.kind == "table":
        rows = [["Feature", "First technology", "Second technology"]]
        rows.extend([["", "", ""] for _ in range(4)])
        table = Table(
            rows,
            colWidths=[55 * mm, 55 * mm, 55 * mm],
            rowHeights=[9 * mm, *([11 * mm] * 4)],
        )
        table.setStyle(_response_table_style())
        return [table]
    if question.kind == "diagram":
        table = Table(
            [[""]],
            colWidths=[165 * mm],
            rowHeights=[56 * mm],
            style=TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.55, INK),
                ]
            ),
        )
        return [table]
    if question.kind == "programming":
        row_count = min(12, max(6, question.marks + 3))
        rows = [[str(index), ""] for index in range(1, row_count + 1)]
        table = Table(
            rows,
            colWidths=[12 * mm, 153 * mm],
            rowHeights=[6.5 * mm] * row_count,
        )
        style = [
            ("BOX", (0, 0), (-1, -1), 0.5, INK),
            ("LINEAFTER", (0, 0), (0, -1), 0.45, INK),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (0, -1), FONT_MONO),
            ("FONTSIZE", (0, 0), (0, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 2),
        ]
        for row in range(row_count):
            style.append(("LINEBELOW", (1, row), (1, row), 0.3, colors.grey))
        table.setStyle(TableStyle(style))
        return [table]
    return [AnswerLines(line_count)]


def _response_table_style() -> TableStyle:
    return TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, INK),
            ("BACKGROUND", (0, 0), (-1, 0), GREY),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]
    )


def _question_table(question: GeneratedQuestion) -> Table:
    return Table(
        [
            [
                Paragraph(
                    f"<b>{question.number}</b> {question.prompt}", STYLES["body"]
                ),
                Paragraph(f"[{question.marks}]", STYLES["marks"]),
            ]
        ],
        colWidths=[155 * mm, 12 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _trace_table(option: GeneratedOption) -> Table:
    rows = [
        [Paragraph(option.chart_title, STYLES["small_bold"]), *option.chart_labels],
        ["Value", *[f"{value:.0f}" for value in option.chart_values]],
    ]
    table = Table(rows, colWidths=[40 * mm, *([21 * mm] * 6)])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, INK),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _scheme_block(
    question: GeneratedQuestion,
    *,
    cell_padding: float = 5,
) -> list[Flowable]:
    rows = [
        [
            Paragraph(
                f"<b>{question.number}</b> {question.prompt}", STYLES["body"]
            ),
            str(question.marks),
        ]
    ]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in question.mark_scheme]
    )
    table = Table(rows, colWidths=[245 * mm, 15 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), cell_padding),
            ]
        )
    )
    return [table, Spacer(1, 4 * mm)]


def _continued_pages(count: int, title: str) -> list[Flowable]:
    result: list[Flowable] = []
    for _ in range(count):
        result.extend(
            [PageBreak(), Paragraph(title, STYLES["centre_bold"]), AnswerLines(34)]
        )
    return result


def _additional_pages(count: int) -> list[Flowable]:
    pages: list[Flowable] = []
    for index in range(count):
        pages.extend(
            [
                PageBreak(),
                *_additional_answer_page(include_legal_notice=index == count - 1),
            ]
        )
    return pages


def _additional_answer_page(
    *,
    include_legal_notice: bool,
) -> list[Flowable]:
    row_count = 20 if include_legal_notice else 24
    rows: list[list[object]] = [
        [
            Paragraph("Question<br/>number", STYLES["small_bold"]),
            Paragraph("EXTRA ANSWER SPACE", STYLES["centre_bold"]),
        ],
        *[["", ""] for _ in range(row_count)],
    ]
    table = Table(
        rows,
        colWidths=[18 * mm, 147 * mm],
        rowHeights=[10 * mm, *([8.3 * mm] * row_count)],
    )
    style = [
        ("BOX", (0, 0), (-1, -1), 0.6, INK),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 2),
    ]
    for row in range(1, row_count + 1):
        style.append(("LINEBELOW", (1, row), (1, row), 0.35, colors.grey))
    table.setStyle(TableStyle(style))
    content: list[Flowable] = [table]
    if include_legal_notice:
        content.extend(
            [
                Spacer(1, 6 * mm),
                Paragraph(
                    "Independent practice material. Created by Paper Creator for private "
                    "revision; not produced or endorsed by OCR.",
                    STYLES["small"],
                ),
            ]
        )
    return content


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Computer Science", STYLES["kicker"]),
        Paragraph("Independent practice paper", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        Table(
            [
                ["Time allowed", "2 hours 30 minutes"],
                ["Maximum mark", "140"],
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
            "Answer all questions. Write answers in the spaces provided. "
            "Do not use a calculator.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Information", STYLES["heading"]),
        Paragraph(
            "The maximum mark is 140. Marks are shown in brackets. Quality of "
            "extended response is assessed where level descriptors are supplied. "
            "This independently created practice paper is mapped to OCR H446 but "
            "is not produced or endorsed by OCR.",
            STYLES["body"],
        ),
    ]


def _document(
    path: Path, paper: GeneratedPaper, kind: str
) -> BaseDocTemplate:
    if kind == "Question paper":
        left_margin = 17.5 * mm
        right_margin = 17.5 * mm
    elif paper.paper_id == "paper_1":
        left_margin = 15 * mm
        right_margin = 14 * mm
    else:
        left_margin = 20 * mm
        right_margin = 17 * mm
    page_size = OCR_MARK_SCHEME_FRONT_SIZE if kind == "Mark scheme" else A4
    doc = BaseDocTemplate(
        str(path),
        pagesize=page_size,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="Paper creator",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    templates = [
        PageTemplate(
            id="ocr-cs-practice",
            frames=[frame],
            onPage=lambda canvas, value: _chrome(
                canvas, value, paper.paper_code, kind
            ),
        )
    ]
    if kind == "Mark scheme":
        width, height = OCR_MARK_SCHEME_LANDSCAPE_SIZE
        landscape_frame = Frame(
            left_margin,
            18 * mm,
            width - left_margin - right_margin,
            height - 37 * mm,
            id="mark-scheme-body",
        )
        templates.append(
            PageTemplate(
                id="ocr-cs-mark-scheme-landscape",
                frames=[landscape_frame],
                pagesize=OCR_MARK_SCHEME_LANDSCAPE_SIZE,
                onPage=lambda canvas, value: _chrome(
                    canvas, value, paper.paper_code, kind
                ),
            )
        )
        final_width, final_height = OCR_MARK_SCHEME_FINAL_SIZE
        final_frame = Frame(
            left_margin,
            18 * mm,
            final_width - left_margin - right_margin,
            final_height - 37 * mm,
            id="mark-scheme-final-body",
        )
        templates.append(
            PageTemplate(
                id="ocr-cs-mark-scheme-final",
                frames=[final_frame],
                pagesize=OCR_MARK_SCHEME_FINAL_SIZE,
                onPage=lambda canvas, value: _chrome(
                    canvas, value, paper.paper_code, kind
                ),
            )
        )
    doc.addPageTemplates(templates)
    return doc


def _chrome(canvas, doc, code: str, kind: str) -> None:
    canvas.saveState()
    page_width, page_height = canvas._pagesize
    if kind == "Question paper" and doc.page > 1:
        canvas.setFillColor(INK)
        canvas.setFont(FONT, 9)
        canvas.drawCentredString(page_width / 2, page_height - 18 * mm, str(doc.page))
        canvas.setFont(FONT, 6)
        canvas.drawString(17.5 * mm, 18 * mm, code)
        if code in {"H446/1", "H446/01"} and doc.page == 27:
            canvas.setFont(FONT_BOLD, 9)
            canvas.drawCentredString(
                page_width / 2,
                18 * mm,
                "END OF QUESTION PAPER",
            )
        elif doc.page % 2 == 1:
            canvas.setFont(FONT_BOLD, 9)
            canvas.drawRightString(page_width - 17.5 * mm, 18 * mm, "Turn over")
        canvas.restoreState()
        return
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(
        20 * mm,
        page_height - 13 * mm,
        page_width - 17 * mm,
        page_height - 13 * mm,
    )
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(20 * mm, page_height - 15 * mm, f"{code} · {kind}")
    canvas.drawRightString(page_width - 17 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["banner"])]],
        colWidths=[165 * mm],
        style=TableStyle(
            [("BACKGROUND", (0, 0), (-1, -1), colors.white), ("PADDING", (0, 0), (-1, -1), 2)]
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
        self.width = 165 * mm
        self.height = count * 4.7 * mm
        self.count = count

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#666666"))
        self.canv.setLineWidth(0.5)
        self.canv.setDash(1, 1.7)
        for index in range(self.count):
            y = self.height - (index + 1) * 4.7 * mm
            self.canv.line(0, y, self.width, y)
        self.canv.setDash()


_base = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName=FONT, fontSize=9.2, leading=12),
    "small_bold": ParagraphStyle("small-bold", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.2, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=11, leading=14, textColor=INK, alignment=TA_CENTER),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName=FONT, fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_RIGHT),
    "code": ParagraphStyle("code", parent=_base["Code"], fontName=FONT_MONO, fontSize=8.8, leading=11, backColor=colors.HexColor("#f4f4f4"), borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "centre": ParagraphStyle("centre", parent=_base["BodyText"], fontName=FONT, fontSize=10.5, leading=14, alignment=TA_CENTER),
    "centre_bold": ParagraphStyle("centre-bold", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_CENTER),
    "scheme_header": ParagraphStyle("scheme-header", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=7.4, leading=8.5),
    "scheme_small": ParagraphStyle("scheme-small", parent=_base["BodyText"], fontName=FONT, fontSize=7.1, leading=8.5),
    "scheme_small_centre": ParagraphStyle("scheme-small-centre", parent=_base["BodyText"], fontName=FONT, fontSize=7.1, leading=8.5, alignment=TA_CENTER),
}
