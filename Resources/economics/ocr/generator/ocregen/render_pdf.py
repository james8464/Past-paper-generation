from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String, Wedge
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
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.exam_blueprints import GeneratedOption, GeneratedPaper, GeneratedQuestion
from Backend.Core.fonts import register_fonts
from Backend.Core.generation_date import formatted_generation_date

PAGE_WIDTH, PAGE_HEIGHT = A4
OCR_MARK_SCHEME_FRONT_SIZE = (594.96, 842.04)
OCR_MARK_SCHEME_LANDSCAPE_SIZE = (841.92, 595.32)
OCR_MARK_SCHEME_FINAL_SIZE = (595.32, 841.92)
INK = colors.HexColor("#151515")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    story.extend(_paper_three_pages(paper) if paper.paper_id == "paper_3" else _paper_one_two_pages(paper))
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Economics", STYLES["kicker"]),
        Paragraph("Independent practice mark scheme", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box("Reward valid alternative reasoning. Apply the level descriptors holistically for extended responses."),
        PageBreak(),
        Paragraph("Marking instructions", STYLES["heading"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "Apply the mark scheme consistently. Credit valid economic analysis and "
            "well-supported alternative conclusions. Use the whole response when "
            "placing extended answers within a level.",
            STYLES["body"],
        ),
        Spacer(1, 6 * mm),
        _box(
            "Indicative content is not exhaustive. Award equivalent valid reasoning "
            "when it answers the question set."
        ),
        NextPageTemplate("ocr-mark-scheme-landscape"),
        PageBreak(),
        *_supplementary_marking_pages(),
        PageBreak(),
    ]
    if paper.paper_id in {"paper_1", "paper_2"}:
        story.extend(_paper_one_two_mark_scheme_content(paper))
    else:
        for section in paper.sections:
            story.extend(
                [_banner(f"Section {section.id}: {section.title}"), Spacer(1, 4 * mm)]
            )
            for option in section.options:
                for question in option.questions:
                    story.extend(_scheme_block(question))
            story.append(PageBreak())
        story.pop()
    story.extend(_mark_scheme_extension_pages(paper))
    story.extend(
        [
            NextPageTemplate("ocr-mark-scheme-final"),
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


def _supplementary_marking_pages() -> list[Flowable]:
    pages: list[Flowable] = []
    page_builders = [
        _preparation_for_marking_page,
        _assessment_objectives_guidance_page,
        _levels_application_page,
        _diagrams_and_calculations_page,
        _annotation_conventions_page,
        _short_answer_guidance_page,
        _strong_levels_descriptor_page,
        _limited_levels_descriptor_page,
    ]
    for index, builder in enumerate(page_builders):
        if index:
            pages.append(PageBreak())
        pages.extend(builder())
    return pages


def _preparation_for_marking_page() -> list[Flowable]:
    rows = [
        ("1", "Read the complete question paper, source material and mark scheme before marking any response."),
        ("2", "Apply the published criteria directly. Do not compare one candidate with another."),
        ("3", "Mark positively: award credit for relevant economic knowledge, application, analysis and evaluation."),
        ("4", "Credit a valid alternative route when it answers the precise question and is economically coherent."),
        ("5", "Where a response is crossed out, mark a clearly presented replacement. Otherwise mark the legible original response."),
        ("6", "Do not award a point that is contradicted elsewhere in the same response."),
        ("7", "Check additional answer space before recording no response or completing a question total."),
        ("8", "For calculations, apply error carried forward only where the later method remains valid."),
        ("9", "For levels questions, read the whole response before selecting the best-fit level and mark."),
    ]
    return [
        Paragraph("MARKING INSTRUCTIONS", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        Paragraph("PREPARATION FOR MARKING", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _guidance_table(["", "Instruction"], rows, [12 * mm, 248 * mm]),
    ]


def _assessment_objectives_guidance_page() -> list[Flowable]:
    rows = [
        ("AO1", "Knowledge and understanding", "Accurate economic ideas, principles, models and terminology."),
        ("AO2", "Application", "Relevant use of the supplied context, figures, constraints and evidence."),
        ("AO3", "Analysis", "A connected chain of reasoning that establishes causes, mechanisms and consequences."),
        ("AO4", "Evaluation", "Testing assumptions and significance before reaching a supported judgement."),
    ]
    notes = [
        ("Accurate", "The response is economically correct and uses terminology precisely."),
        ("Applied", "The response selects contextual material and uses it to answer the question set."),
        ("Developed", "Each link in the analysis is explained rather than merely asserted."),
        ("Supported", "The final judgement follows from the analysis and evaluation presented."),
    ]
    return [
        Paragraph("USING THE ASSESSMENT OBJECTIVES", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(
            ["Objective", "Focus", "Evidence required"],
            rows,
            [24 * mm, 54 * mm, 182 * mm],
        ),
        Spacer(1, 7 * mm),
        Paragraph("Applying the standard", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _guidance_table(["Term", "Meaning"], notes, [34 * mm, 226 * mm]),
    ]


def _levels_application_page() -> list[Flowable]:
    rows = [
        ("1", "Read the response as a whole and identify the highest descriptor it meets securely."),
        ("2", "Use best fit when a response shows qualities from adjacent levels."),
        ("3", "Select the top of a level when its qualities are sustained; select the bottom when they are only just demonstrated."),
        ("4", "Do not count isolated points. Consider accuracy, relevance, development and coherence together."),
        ("5", "A balanced response need not give equal space to every view, but material counterarguments must be considered."),
        ("6", "A judgement earns evaluation credit only when it is supported by the preceding reasoning."),
        ("7", "If no material is worthy of credit, award zero."),
    ]
    bands = [
        ("Top", "Descriptor is met consistently; analysis is secure and judgement is fully supported."),
        ("Middle", "Descriptor is met reasonably well; development is sound but not sustained throughout."),
        ("Bottom", "Response just enters the level; relevant qualities are present but uneven or incomplete."),
    ]
    return [
        Paragraph("LEVELS-BASED RESPONSES", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(["", "Procedure"], rows, [12 * mm, 248 * mm]),
        Spacer(1, 6 * mm),
        _guidance_table(["Position", "How to place the mark"], bands, [32 * mm, 228 * mm]),
    ]


def _diagrams_and_calculations_page() -> list[Flowable]:
    rows = [
        ("Economic diagram", "Correct axes, curves, labels, shift and equilibrium relevant to the question.", "A diagram that contradicts the written analysis or has ambiguous axes."),
        ("Calculation", "Valid method, substituted figures, correct answer, units and requested accuracy.", "An unsupported answer where working is required or a value with the wrong sign/unit."),
        ("Data comparison", "Accurate figures, direction, magnitude and a comparison tied to the question.", "Copying a figure without using it or describing two values independently."),
        ("Chain of reasoning", "A cause linked through a mechanism to a relevant economic consequence.", "A list of effects with no explained connection."),
        ("Judgement", "A conclusion supported by criteria such as scale, time, assumptions or distribution.", "An unsupported assertion or repetition of the question."),
    ]
    return [
        Paragraph("DIAGRAMS, DATA AND CALCULATIONS", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(
            ["Response feature", "Credit", "Do not credit"],
            rows,
            [38 * mm, 111 * mm, 111 * mm],
        ),
    ]


def _annotation_conventions_page() -> list[Flowable]:
    rows = [
        ("✓", "Creditworthy point", "A distinct valid point earns the available mark."),
        ("DEV", "Developed analysis", "A valid consequence is linked to the preceding economic point."),
        ("APP", "Application", "The response uses a supplied figure, fact or contextual feature."),
        ("EVAL", "Evaluation", "A relevant limitation, condition or counterargument is developed."),
        ("J", "Judgement", "A supported conclusion answers the precise question."),
        ("BOD", "Benefit of doubt", "Meaning is clear despite minor imprecision."),
        ("ECF", "Error carried forward", "A later valid method follows an earlier numerical error."),
        ("REP", "Repeated point", "Do not award the same developed idea twice."),
        ("CON", "Contradiction", "Withhold credit where the response reverses a valid point."),
        ("MAX", "Maximum", "Stop awarding when the stated maximum is reached."),
        ("0", "Attempted, no credit", "Some response is present but it does not meet the criteria."),
        ("NR", "No response", "Nothing relevant is written in the answer space."),
    ]
    return [
        Paragraph("ANNOTATION CONVENTIONS", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(
            ["Annotation", "Meaning", "Use"],
            rows,
            [28 * mm, 58 * mm, 174 * mm],
        ),
    ]


def _short_answer_guidance_page() -> list[Flowable]:
    rows = [
        ("State / identify", "Award one mark for each distinct correct item up to the stated maximum."),
        ("Define", "Require the essential economic meaning; exact wording is not necessary."),
        ("Explain", "Award the explanation mark only where a valid link or mechanism is established."),
        ("Calculate", "Follow the question-specific allocation for method, substitution and final answer."),
        ("Compare", "Require a relative statement using both values, trends or cases."),
        ("Analyse", "Reward developed, connected reasoning applied to the question."),
        ("Evaluate", "Reward a relevant counterargument or condition and a supported conclusion."),
    ]
    examples = [
        ("Two valid points where two are requested", "2"),
        ("Three listed points where only two are requested", "Maximum 2"),
        ("Correct point followed by a contradiction", "0 for that point"),
        ("Correct method with a carried-forward arithmetic error", "Method credit as specified"),
    ]
    return [
        Paragraph("SHORT-ANSWER QUESTIONS", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(["Command", "Marking approach"], rows, [45 * mm, 215 * mm]),
        Spacer(1, 6 * mm),
        _guidance_table(["Response", "Treatment"], examples, [190 * mm, 70 * mm]),
    ]


def _strong_levels_descriptor_page() -> list[Flowable]:
    rows = [
        (
            "Strong",
            "Precise knowledge and understanding of relevant economic ideas, principles and models.",
            "Focused application using relevant contextual evidence and well-selected data.",
            "Consistently developed chains of reasoning; diagrams are accurate and integrated.",
            "Counterarguments are developed and the supported judgement weighs material factors.",
        ),
        (
            "Good",
            "Mainly accurate knowledge and sound understanding of the relevant economics.",
            "Relevant application with some focused use of the context and supplied evidence.",
            "Causes and consequences are explained through mostly complete analytical links.",
            "Alternative views are considered and a supported conclusion is attempted.",
        ),
        (
            "Reasonable",
            "Some accurate knowledge, though coverage or precision may be uneven.",
            "Some application to the context, but examples or data may not be fully integrated.",
            "Relevant analysis is present but chains are incomplete or contain unsupported links.",
            "Some evaluation is present; the conclusion has limited support.",
        ),
    ]
    return _levels_descriptor_table(rows)


def _limited_levels_descriptor_page() -> list[Flowable]:
    rows = [
        (
            "Limited",
            "Limited awareness of relevant economic meaning, ideas, principles or models.",
            "Very little ability to apply economic ideas to the supplied context.",
            "Simple statements of cause and consequence with little developed reasoning.",
            "Counterarguments are asserted; any conclusion is unsupported.",
        ),
        (
            "No credit",
            "No relevant knowledge or understanding demonstrated.",
            "No relevant application.",
            "No creditworthy analysis.",
            "No creditworthy evaluation or judgement.",
        ),
    ]
    return [
        *_levels_descriptor_table(rows),
        Spacer(1, 6 * mm),
        Paragraph(
            "Use the question-specific level and mark ranges printed with each extended-response item.",
            STYLES["small"],
        ),
    ]


def _levels_descriptor_table(rows: list[tuple[str, ...]]) -> list[Flowable]:
    return [
        Paragraph("LEVELS OF RESPONSE", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(
            [
                "Level descriptor",
                "Knowledge and understanding (AO1)",
                "Application (AO2)",
                "Analysis (AO3)",
                "Evaluation (AO4)",
            ],
            rows,
            [40 * mm, 55 * mm, 55 * mm, 55 * mm, 55 * mm],
        ),
    ]


def _guidance_table(
    headers: list[str],
    rows: list[tuple[str, ...]],
    widths: list[float],
) -> Table:
    data: list[list[object]] = [
        [Paragraph(f"<b>{escape(value)}</b>", STYLES["small"]) for value in headers]
    ]
    data.extend(
        [
            [Paragraph(escape(value), STYLES["small"]) for value in row]
            for row in rows
        ]
    )
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#555555")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _paper_one_two_mark_scheme_content(paper: GeneratedPaper) -> list[Flowable]:
    data_questions = paper.sections[0].options[0].questions
    section_b = [option.questions[0] for option in paper.sections[1].options]
    section_c = [option.questions[0] for option in paper.sections[2].options]
    choice_questions = [*section_b, *section_c]
    pages: list[list[Flowable]] = [
        [
            _banner(f"Section {paper.sections[0].id}: {paper.sections[0].title}"),
            Spacer(1, 3 * mm),
            *_scheme_block(data_questions[0]),
            *_scheme_block(
                data_questions[1],
                diagram_questions=[data_questions[1], data_questions[1]],
            ),
        ],
        [
            *_scheme_block(data_questions[2], body_height=62 * mm),
            *_scheme_block(data_questions[3], body_height=66 * mm),
        ],
        _level_descriptor_page(data_questions[4]),
        _indicative_guidance_page(data_questions[4]),
        _level_descriptor_page(data_questions[5]),
        _indicative_guidance_page(data_questions[5]),
        _choice_level_descriptor_page(choice_questions, range(0, 3)),
        [
            *_choice_level_descriptor_page(choice_questions, range(3, 5)),
            Spacer(1, 4 * mm),
            *_compact_indicative_guidance(section_b[0], 6),
        ],
        _diagram_guidance_page(section_b),
    ]
    result: list[Flowable] = []
    for index, page in enumerate(pages):
        if index:
            result.append(PageBreak())
        result.extend(page)
    return result


def _level_descriptor_page(question: GeneratedQuestion) -> list[Flowable]:
    return [
        Paragraph(
            f"<b>{escape(question.number)}</b> {escape(question.prompt)}",
            STYLES["small"],
        ),
        Spacer(1, 3 * mm),
        _level_descriptor_table(question, range(len(_level_bands(question.marks)))),
    ]


def _choice_level_descriptor_page(
    questions: list[GeneratedQuestion],
    band_indexes: range,
) -> list[Flowable]:
    first = questions[0]
    alternatives = " OR ".join(
        f"{escape(question.number)} {escape(question.prompt)}"
        for question in questions
    )
    return [
        Paragraph("SECTION B AND SECTION C", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        Paragraph(alternatives, STYLES["small"]),
        Spacer(1, 3 * mm),
        _level_descriptor_table(first, band_indexes),
    ]


def _level_descriptor_table(
    question: GeneratedQuestion,
    band_indexes: range,
) -> Table:
    bands = _level_bands(question.marks)
    rows: list[list[object]] = [
        [
            Paragraph("<b>Level / mark</b>", STYLES["small"]),
            Paragraph("<b>Descriptor</b>", STYLES["small"]),
        ]
    ]
    for index in band_indexes:
        level, mark_range = bands[index]
        rows.append(
            [
                Paragraph(
                    f"<b>Level {level}</b><br/>({mark_range} marks)",
                    STYLES["small"],
                ),
                Paragraph(
                    escape(_level_descriptor_text(question, level, len(bands))),
                    STYLES["small"],
                ),
            ]
        )
    if band_indexes.stop == len(bands):
        rows.append(
            [
                Paragraph("<b>0 marks</b>", STYLES["small"]),
                Paragraph("Response is not worthy of credit.", STYLES["small"]),
            ]
        )
    table = Table(rows, colWidths=[31 * mm, 229 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#555555")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _level_bands(marks: int) -> list[tuple[int, str]]:
    if marks >= 20:
        return [(5, "21\u201325"), (4, "16\u201320"), (3, "11\u201315"), (2, "6\u201310"), (1, "1\u20135")]
    if marks >= 12:
        return [(3, "9\u201312"), (2, "5\u20138"), (1, "1\u20134")]
    return [(3, "6\u20138"), (2, "3\u20135"), (1, "1\u20132")]


def _level_descriptor_text(
    question: GeneratedQuestion,
    level: int,
    level_count: int,
) -> str:
    strength = level / level_count
    topic = _question_focus(question)
    if strength >= 0.8:
        return (
            f"Knowledge of {topic} is precise, wide-ranging and expressed with secure economic "
            "terminology. Application is focused on the scope of the question and makes effective "
            "use of relevant figures, examples or institutional detail. Analysis contains "
            "consistently developed chains of reasoning; any relevant diagram is accurate, fully "
            "labelled and integrated into the argument. Evaluation tests assumptions, magnitude, "
            "time and distribution, weighs material alternatives and supports a clear judgement."
        )
    if strength >= 0.55:
        return (
            f"Knowledge of {topic} is mainly accurate and shows sound understanding of the "
            "relevant concepts. Application uses the context and some appropriate evidence, "
            "although it may not be sustained. Analysis develops causes and consequences beyond "
            "simple links and any diagram is broadly accurate. Evaluation considers a relevant "
            "alternative, limitation or condition, and the conclusion has reasonable support."
        )
    if strength >= 0.3:
        return (
            f"Some accurate knowledge of {topic} is demonstrated, though coverage or precision "
            "is uneven. There is some application to the context, but examples or data may be "
            "generic or only partly used. Analytical links are relevant but incomplete, and a "
            "diagram may contain omissions. Evaluation is relevant but limited; the judgement "
            "is asserted or only partly supported by the preceding reasoning."
        )
    return (
        f"Knowledge of {topic} is limited and may contain imprecision. Application is generic, "
        "partial or absent. Reasoning consists mainly of isolated statements of cause or "
        "consequence, with no sustained chain and no effective use of a diagram. Counterarguments "
        "are undeveloped and any conclusion is asserted rather than supported."
    )


def _question_focus(question: GeneratedQuestion) -> str:
    prompt = question.prompt.casefold()
    focuses = [
        ("contestab", "market structures and contestability"),
        ("concentrat", "market structures and concentration"),
        ("price discrimination", "market structures and price discrimination"),
        ("labour", "the labour market"),
        ("competition", "market structures and competition"),
        ("monopoly", "market structures and monopoly"),
        ("inflation", "inflation and macroeconomic performance"),
        ("growth", "economic growth"),
        ("trade", "international trade"),
        ("exchange", "exchange rates"),
        ("tax", "taxation and government intervention"),
        ("market failure", "market failure"),
    ]
    for token, label in focuses:
        if token in prompt:
            return label
    return "the economic issue in the question"


def _indicative_guidance_page(question: GeneratedQuestion) -> list[Flowable]:
    return [
        *_compact_indicative_guidance(question, 12),
        Spacer(1, 4 * mm),
        Paragraph(
            "The side of the argument presented first may be credited as analysis, with a "
            "developed counterargument credited as evaluation.",
            STYLES["small"],
        ),
    ]


def _compact_indicative_guidance(
    question: GeneratedQuestion,
    limit: int,
) -> list[Flowable]:
    points = list(dict.fromkeys(question.mark_scheme))
    while len(points) < limit:
        points.extend(_generated_guidance_points(question))
        points = list(dict.fromkeys(points))
        if len(points) == len(question.mark_scheme):
            break
    rows: list[list[object]] = [
        [
            Paragraph(
                f"<b>Question {escape(question.number)} guidance</b>",
                STYLES["small"],
            )
        ]
    ]
    rows.extend(
        [[Paragraph(f"• {escape(point)}", STYLES["small"])] for point in points[:limit]]
    )
    table = Table(rows, colWidths=[260 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#555555")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return [table]


def _generated_guidance_points(question: GeneratedQuestion) -> list[str]:
    focus = _question_focus(question)
    return [
        f"Knowledge and understanding should be accurate and specific to {focus}.",
        "Application should use the supplied figures, institutional detail or named context.",
        "Analysis should identify the relevant agent, incentive and transmission mechanism.",
        "A developed chain should link the initial change to a measurable economic outcome.",
        "Evaluation may test assumptions, magnitude, time period and distributional effects.",
        "A supported judgement should answer the precise wording of the question.",
    ]


def _diagram_guidance_page(
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    return [
        Paragraph(
            f"Question {escape(questions[0].number)} / {escape(questions[1].number)} diagram guidance",
            STYLES["heading"],
        ),
        Spacer(1, 3 * mm),
        _economics_diagram_pair(questions),
        Spacer(1, 3 * mm),
        Paragraph(
            "Credit a different correctly labelled diagram when it is relevant, internally "
            "consistent and integrated into the written analysis.",
            STYLES["small"],
        ),
        Spacer(1, 3 * mm),
        *_compact_indicative_guidance(questions[1], 6),
    ]


def _economics_diagram_pair(
    questions: list[GeneratedQuestion],
) -> Drawing:
    drawing = Drawing(245 * mm, 76 * mm)
    for index, question in enumerate(questions[:2]):
        _add_economics_diagram(
            drawing,
            question,
            x0=28 + index * 360,
            y0=38,
            width=250,
            height=145,
            shifted=index == 1,
            compact=False,
        )
    return drawing


def _compact_economics_diagram_pair(
    questions: list[GeneratedQuestion],
) -> Drawing:
    drawing = Drawing(98 * mm, 70 * mm)
    for index, question in enumerate(questions[:2]):
        _add_economics_diagram(
            drawing,
            question,
            x0=18,
            y0=107 - index * 89,
            width=235,
            height=63,
            shifted=index == 1,
            compact=True,
        )
    return drawing


def _add_economics_diagram(
    drawing: Drawing,
    question: GeneratedQuestion,
    *,
    x0: float,
    y0: float,
    width: float,
    height: float,
    shifted: bool,
    compact: bool,
) -> None:
    focus = _question_focus(question)
    if "labour" in focus:
        y_label, x_label, down_label, up_label = "Wage", "Employment", "DL", "SL"
    elif "inflation" in focus or "growth" in focus:
        y_label, x_label, down_label, up_label = "Price level", "Real output", "AD", "SRAS"
    elif "exchange" in focus:
        y_label, x_label, down_label, up_label = "Exchange rate", "Currency", "D", "S"
    else:
        y_label, x_label, down_label, up_label = "Price", "Quantity", "D", "S"

    title = focus.capitalize() if not shifted else "Entry increases competitive supply"
    title_size = 6 if compact else 9
    label_size = 5 if compact else 7
    inset = 10 if compact else 18
    drawing.add(String(x0, y0 + height + (10 if compact else 28), title, fontName=FONT_BOLD, fontSize=title_size))
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    drawing.add(String(x0 - 3, y0 + height + 3, y_label, fontName=FONT, fontSize=label_size))
    drawing.add(String(x0 + width - 15, y0 - 9, x_label, fontName=FONT, fontSize=label_size))

    drawing.add(Line(x0 + inset, y0 + height - inset, x0 + width - inset, y0 + inset))
    drawing.add(Line(x0 + inset, y0 + inset, x0 + width - inset, y0 + height - inset))
    drawing.add(String(x0 + width - inset + 1, y0 + inset - 3, down_label, fontName=FONT, fontSize=label_size))
    drawing.add(String(x0 + width - inset + 1, y0 + height - inset - 2, up_label, fontName=FONT, fontSize=label_size))

    equilibrium_x = x0 + width / 2
    equilibrium_y = y0 + height / 2
    equilibrium_label = "E"
    if shifted:
        shift = 14 if compact else 28
        drawing.add(
            Line(
                x0 + inset + shift,
                y0 + inset,
                x0 + width - inset + shift,
                y0 + height - inset,
            )
        )
        drawing.add(
            String(
                x0 + width - inset + shift,
                y0 + height - inset - 2,
                f"{up_label}1",
                fontName=FONT,
                fontSize=label_size,
            )
        )
        equilibrium_x += shift / 2
        equilibrium_y -= shift * height / (2 * width)
        equilibrium_label = "E1"

    dash = [2, 2] if compact else [3, 2]
    drawing.add(Line(equilibrium_x, y0, equilibrium_x, equilibrium_y, strokeDashArray=dash))
    drawing.add(Line(x0, equilibrium_y, equilibrium_x, equilibrium_y, strokeDashArray=dash))
    drawing.add(
        String(
            equilibrium_x + 3,
            equilibrium_y + 3,
            equilibrium_label,
            fontName=FONT_BOLD,
            fontSize=label_size,
        )
    )


MARK_SCHEME_EXTENSION_PAGE_COUNTS = {
    "paper_1": 10,
    "paper_2": 13,
    "paper_3": 9,
}


def _mark_scheme_extension_pages(paper: GeneratedPaper) -> list[Flowable]:
    count = MARK_SCHEME_EXTENSION_PAGE_COUNTS[paper.paper_id]
    questions = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
    ]
    extended = [question for question in questions if question.marks >= 8]
    pages: list[Flowable] = []
    for index in range(count):
        pages.append(PageBreak())
        if paper.paper_id == "paper_3" and index < 3:
            pages.extend(_mcq_rationale_page(questions[index * 10 : (index + 1) * 10]))
            continue
        if index == count - 1:
            pages.extend(_assessment_objectives_page(paper, questions))
            continue
        question = extended[index % len(extended)]
        if paper.paper_id in {"paper_1", "paper_2"} and index == 1:
            pages.extend(_extended_diagram_page(question))
        else:
            pages.extend(_extended_guidance_page(question, index))
    return pages


def _mcq_rationale_page(questions: list[GeneratedQuestion]) -> list[Flowable]:
    rows = [["Question", "Answer and rationale"]]
    for question in questions:
        answer = "ABCD"[question.correct_choice or 0]
        rationale = question.mark_scheme[0] if question.mark_scheme else "Credit the keyed answer."
        rows.append(
            [
                Paragraph(question.number, STYLES["small"]),
                Paragraph(
                    f"<b>{answer}</b> — {rationale} {question.prompt}",
                    STYLES["small"],
                ),
            ]
        )
    table = Table(rows, colWidths=[24 * mm, 236 * mm], repeatRows=1)
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
    return [Paragraph("Multiple-choice rationale", STYLES["heading"]), Spacer(1, 4 * mm), table]


def _extended_guidance_page(
    question: GeneratedQuestion,
    page_index: int,
) -> list[Flowable]:
    points = question.mark_scheme
    chunk_size = 10
    start = (page_index * chunk_size) % max(len(points), 1)
    chunk = (points + points)[start : start + chunk_size]
    rows = [[Paragraph("Indicative content and level guidance", STYLES["body"]), ""]]
    rows.extend([[Paragraph(f"• {point}", STYLES["small"]), ""] for point in chunk])
    table = Table(rows, colWidths=[245 * mm, 15 * mm])
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
    return [
        Paragraph(f"Question {question.number} guidance continued", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(question.prompt, STYLES["body"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 4 * mm),
        Paragraph(
            "Credit a different but economically valid route when it is developed, "
            "applied to the question and supports the judgement reached.",
            STYLES["body"],
        ),
    ]


def _extended_diagram_page(
    question: GeneratedQuestion,
) -> list[Flowable]:
    return [
        Paragraph(f"Question {question.number} diagram guidance", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(question.prompt, STYLES["body"]),
        Spacer(1, 3 * mm),
        _economics_diagram_pair([question, question]),
        Spacer(1, 3 * mm),
        *_compact_indicative_guidance(question, 6),
    ]


def _assessment_objectives_page(
    paper: GeneratedPaper,
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    rows: list[list[str]] = [
        ["Question", "AO1", "AO2", "AO3", "AO4", "TOTAL", "Quantitative skills"]
    ]
    grouped = _assessment_grid_groups(paper, questions)
    totals = [0, 0, 0, 0]
    quantitative_total = 0
    extended_group_index = 0
    for label, question in grouped:
        allocation = _assessment_allocation(question)
        totals = [total + value for total, value in zip(totals, allocation, strict=True)]
        if question.marks >= 20:
            quantitative = 8 if extended_group_index == 0 else 0
            extended_group_index += 1
        elif question.kind == "calculation":
            quantitative = question.marks
        elif "compare" in question.command_word.casefold():
            quantitative = question.marks
        elif "diagram" in question.prompt.casefold():
            quantitative = min(question.marks, 4)
        else:
            quantitative = 0
        quantitative_total += quantitative
        rows.append(
            [
                label,
                *(str(value) if value else "" for value in allocation),
                str(question.marks),
                f"({quantitative})" if quantitative else "",
            ]
        )
    rows.append(
        [
            "TOTAL",
            *(str(value) for value in totals),
            str(paper.total_marks),
            f"({quantitative_total})" if quantitative_total else "",
        ]
    )
    table = Table(
        rows,
        colWidths=[38 * mm, 31 * mm, 31 * mm, 31 * mm, 31 * mm, 38 * mm, 60 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("BACKGROUND", (0, -1), (-1, -1), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        Paragraph("ASSESSMENT OBJECTIVES GRID", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        table,
    ]


def _assessment_grid_groups(
    paper: GeneratedPaper,
    questions: list[GeneratedQuestion],
) -> list[tuple[str, GeneratedQuestion]]:
    if paper.paper_id == "paper_3":
        multiple_choice = [question for question in questions if question.kind == "multiple_choice"]
        written = [question for question in questions if question.kind != "multiple_choice"]
        grouped: list[tuple[str, GeneratedQuestion]] = []
        if multiple_choice:
            combined = multiple_choice[0].model_copy(
                update={
                    "number": f"{multiple_choice[0].number}\u2013{multiple_choice[-1].number}",
                    "marks": sum(question.marks for question in multiple_choice),
                }
            )
            grouped.append((combined.number, combined))
        grouped.extend((question.number, question) for question in written)
        return grouped

    grouped = []
    index = 0
    while index < len(questions):
        question = questions[index]
        if (
            question.marks >= 20
            and index + 1 < len(questions)
            and questions[index + 1].marks == question.marks
        ):
            grouped.append(
                (f"{question.number}*/{questions[index + 1].number}*", question)
            )
            index += 2
            continue
        grouped.append((question.number, question))
        index += 1
    return grouped


def _assessment_allocation(question: GeneratedQuestion) -> tuple[int, int, int, int]:
    if question.kind == "multiple_choice":
        ao1 = (question.marks + 1) // 2
        return ao1, question.marks - ao1, 0, 0
    fixed = {
        25: (6, 6, 6, 7),
        15: (3, 3, 4, 5),
        12: (1, 1, 5, 5),
        8: (1, 1, 3, 3),
        4: (2, 2, 0, 0),
        3: (1, 2, 0, 0),
    }
    if question.marks in fixed:
        return fixed[question.marks]
    if (
        question.kind in {"calculation", "data"}
        or question.command_word.casefold() in {"calculate", "compare"}
    ):
        return 0, question.marks, 0, 0
    return question.marks, 0, 0, 0


def _paper_one_two_pages(paper: GeneratedPaper) -> list[Flowable]:
    section_a, section_b, section_c = paper.sections
    data = section_a.options[0]
    pages: list[list[Flowable]] = [
        [
            *_intro(section_a),
            Paragraph(data.title, STYLES["option"]),
            Paragraph(data.stimulus[0], STYLES["extract"]),
            Spacer(1, 3 * mm),
            _chart(data),
        ],
        [
            Paragraph(data.title, STYLES["option"]),
            Paragraph(data.stimulus[1], STYLES["extract"]),
            Spacer(1, 3 * mm),
            Paragraph(data.stimulus[2], STYLES["extract"]),
            Spacer(1, 4 * mm),
            _market_share_chart(data),
        ],
        [
            _banner("Question 1"),
            Spacer(1, 3 * mm),
            *sum((_question_block(question) for question in data.questions[:3]), []),
            AnswerLines(10),
        ],
        [
            _banner("Question 1 continued"),
            Spacer(1, 4 * mm),
            *_question_block(data.questions[3]),
            AnswerLines(20),
        ],
        [
            _banner("Question 1 continued"),
            Spacer(1, 4 * mm),
            *_question_block(data.questions[4]),
            AnswerLines(25),
        ],
        [
            _banner("Question 1 continued"),
            Spacer(1, 4 * mm),
            *_question_block(data.questions[5]),
            AnswerLines(25),
        ],
        [
            Paragraph("Question 1 continued", STYLES["centre_bold"]),
            AnswerLines(34),
        ],
        [
            Paragraph("BLANK PAGE", STYLES["centre_bold"]),
            Spacer(1, 8 * mm),
            Paragraph(
                "DO NOT WRITE ON THIS PAGE",
                STYLES["centre_bold"],
            ),
            Spacer(1, 8 * mm),
            Paragraph(
                "Section B starts on the next page",
                STYLES["centre"],
            ),
        ],
        [*_intro(section_b), *_choice_prompts(section_b)],
    ]
    pages.extend([[AnswerLines(34)] for _ in range(3)])
    pages.append([*_intro(section_c), *_choice_prompts(section_c)])
    pages.extend([[AnswerLines(34)] for _ in range(3)])
    pages.extend(
        [
            _extra_answer_page(),
            _extra_answer_page(continued=True),
            _question_paper_legal_page(),
        ]
    )
    assert len(pages) == 19
    return _page_sequence(pages)


def _market_share_chart(option: GeneratedOption) -> Drawing:
    values = [max(1.0, value) for value in option.chart_values[:5]]
    total = sum(values)
    drawing = Drawing(165 * mm, 55 * mm)
    centre_x, centre_y, radius = 105, 78, 62
    start = 0.0
    shades = [
        colors.HexColor("#333333"),
        colors.HexColor("#666666"),
        colors.HexColor("#999999"),
        colors.HexColor("#bbbbbb"),
        colors.HexColor("#dddddd"),
    ]
    for index, (value, shade) in enumerate(zip(values, shades, strict=True)):
        angle = value / total * 360
        drawing.add(
            Wedge(
                centre_x,
                centre_y,
                radius,
                start,
                start + angle,
                strokeColor=INK,
                fillColor=shade,
                strokeWidth=0.5,
            )
        )
        legend_y = 128 - index * 23
        drawing.add(
            Rect(
                220,
                legend_y,
                12,
                12,
                fillColor=shade,
                strokeColor=INK,
                strokeWidth=0.4,
            )
        )
        drawing.add(
            String(
                240,
                legend_y + 2,
                f"Market group {index + 1}: {value / total * 100:.0f}%",
                fontName=FONT,
                fontSize=8,
            )
        )
        start += angle
    drawing.add(
        String(
            20,
            153,
            "Figure 2: distribution of measured activity",
            fontName=FONT_BOLD,
            fontSize=9,
        )
    )
    return drawing


def _extra_answer_page(
    *,
    continued: bool = False,
) -> list[Flowable]:
    row_count = 25
    heading = (
        "EXTRA ANSWER SPACE — continued"
        if continued
        else "EXTRA ANSWER SPACE"
    )
    rows: list[list[object]] = [
        [
            Paragraph("Question<br/>number", STYLES["small"]),
            Paragraph(heading, STYLES["centre_bold"]),
        ],
        *[["", ""] for _ in range(row_count)],
    ]
    table = Table(
        rows,
        colWidths=[18 * mm, 149 * mm],
        rowHeights=[10 * mm, *([8.2 * mm] * row_count)],
    )
    style = [
        ("BOX", (0, 0), (-1, -1), 0.55, INK),
        ("LINEAFTER", (0, 0), (0, -1), 0.45, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.45, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 2),
    ]
    for row in range(1, row_count + 1):
        style.append(("LINEBELOW", (1, row), (1, row), 0.35, colors.grey))
    table.setStyle(TableStyle(style))
    return [table]


def _paper_three_pages(paper: GeneratedPaper) -> list[Flowable]:
    mcq, data_section = paper.sections
    data = data_section.options[0]
    pages: list[list[Flowable]] = []
    cursor = 0
    for page_index in range(15):
        content: list[Flowable] = []
        if page_index == 0:
            content.extend(_intro(mcq))
        for option in mcq.options[cursor : cursor + 2]:
            content.extend(_mcq_block(option.questions[0]))
        cursor += 2
        pages.append(content)
    pages.extend(
        [
            [*_intro(data_section), Paragraph(data.stimulus[0], STYLES["extract"]), Spacer(1, 3 * mm), _chart(data), *_question_block(data.questions[0]), *_question_block(data.questions[1])],
            [_banner("Question 33"), Spacer(1, 4 * mm), *_question_block(data.questions[2]), AnswerLines(25)],
            [Paragraph("Question 33 continued", STYLES["centre_bold"]), AnswerLines(34)],
            [_banner("Extract 2"), Spacer(1, 3 * mm), Paragraph(data.stimulus[1], STYLES["extract"]), Spacer(1, 4 * mm), *_question_block(data.questions[3]), *_question_block(data.questions[4])],
            [_banner("Question 36"), Spacer(1, 4 * mm), *_question_block(data.questions[5]), AnswerLines(25)],
            [Paragraph("Question 36 continued", STYLES["centre_bold"]), AnswerLines(34)],
            [Paragraph("Question 36 continued", STYLES["centre_bold"]), AnswerLines(34)],
            [_banner("Extract 3"), Spacer(1, 3 * mm), Paragraph(data.stimulus[2], STYLES["extract"]), Spacer(1, 4 * mm), *_question_block(data.questions[6])],
            [_banner("Question 38"), Spacer(1, 4 * mm), *_question_block(data.questions[7]), AnswerLines(25)],
            [Paragraph("Question 38 continued", STYLES["centre_bold"]), AnswerLines(34)],
            [Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)],
            [Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)],
        ]
    )
    assert len(pages) == 27
    return _page_sequence(pages)


def _page_sequence(pages: list[list[Flowable]]) -> list[Flowable]:
    result: list[Flowable] = []
    for page in pages:
        result.append(PageBreak())
        result.extend(page)
    return result


def _question_paper_legal_page() -> list[Flowable]:
    return [
        Spacer(1, 105 * mm),
        Paragraph("DO NOT WRITE ON THIS PAGE", STYLES["centre_bold"]),
        Spacer(1, 92 * mm),
        Paragraph("Independent practice material", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Created by Paper Creator for private revision. This paper is not produced, "
            "endorsed or approved by OCR or any examination board. Any third-party names "
            "or scenarios are fictional unless explicitly stated otherwise.",
            STYLES["small"],
        ),
    ]


def _intro(section) -> list[Flowable]:
    return [_banner(f"Section {section.id}: {section.title}"), Spacer(1, 3 * mm), Paragraph(section.instructions, STYLES["instruction"]), Spacer(1, 4 * mm)]


def _choice_prompts(section) -> list[Flowable]:
    result: list[Flowable] = []
    for index, option in enumerate(section.options):
        if index:
            result.extend([Spacer(1, 6 * mm), Paragraph("OR", STYLES["centre_bold"]), Spacer(1, 6 * mm)])
        result.extend(_question_block(option.questions[0]))
    return result


def _mcq_block(question: GeneratedQuestion) -> list[Flowable]:
    choices = "<br/>".join(f"<b>{'ABCD'[index]}</b> {text}" for index, text in enumerate(question.choices))
    return [
        KeepTogether(
            [
                _question_table(question),
                Paragraph(choices, STYLES["choices"]),
                Paragraph("Answer: [ ] A  [ ] B  [ ] C  [ ] D", STYLES["answer"]),
                Spacer(1, 5 * mm),
            ]
        )
    ]


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    return [_question_table(question), Spacer(1, 4 * mm)]


def _question_table(question: GeneratedQuestion) -> Table:
    return Table(
        [[Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]), Paragraph(f"[{question.marks}]", STYLES["marks"])]],
        colWidths=[155 * mm, 12 * mm],
        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]),
    )


def _scheme_block(
    question: GeneratedQuestion,
    diagram_questions: list[GeneratedQuestion] | None = None,
    body_height: float | None = None,
) -> list[Flowable]:
    answer_points, guidance_points = _split_scheme_points(question)
    answer = (
        f"<b>{escape(question.prompt)}</b><br/><br/>"
        + "<br/>".join(f"• {escape(point)}" for point in answer_points)
    )
    answer_cell: list[Flowable] = [Paragraph(answer, STYLES["small"])]
    if diagram_questions:
        answer_cell.extend(
            [
                Spacer(1, 2 * mm),
                Paragraph(f"<b>Diagram guidance for {escape(question.number)}</b>", STYLES["small"]),
                _compact_economics_diagram_pair(diagram_questions),
            ]
        )
    guidance = "<br/>".join(
        f"• {escape(point)}"
        for point in [*_question_guidance(question), *guidance_points]
    )
    rows: list[list[object]] = [
        [
            Paragraph("<b>Question</b>", STYLES["small"]),
            Paragraph("<b>Answer</b>", STYLES["small"]),
            Paragraph("<b>Mark</b>", STYLES["small"]),
            Paragraph("<b>Guidance</b>", STYLES["small"]),
        ],
        [
            Paragraph(escape(question.number), STYLES["small"]),
            answer_cell,
            Paragraph(str(question.marks), STYLES["centre"]),
            Paragraph(guidance, STYLES["small"]),
        ],
    ]
    table = Table(
        rows,
        colWidths=[25 * mm, 112 * mm, 17 * mm, 106 * mm],
        rowHeights=[None, body_height] if body_height is not None else None,
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#555555")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [table, Spacer(1, 4 * mm)]


def _split_scheme_points(
    question: GeneratedQuestion,
) -> tuple[list[str], list[str]]:
    guidance_prefixes = (
        "ao1",
        "ao2",
        "ao3",
        "ao4",
        "level ",
        "levels-based",
        "marker check",
        "do not award",
        "maximum ",
    )
    answer: list[str] = []
    guidance: list[str] = []
    for point in question.mark_scheme:
        target = (
            guidance
            if point.casefold().startswith(guidance_prefixes)
            else answer
        )
        if point.casefold() != "indicative content":
            target.append(point)
    answer = answer or question.mark_scheme[:1]
    answer_limit = 8 if question.marks >= 20 else 6
    if question.marks >= 8:
        guidance_limit = 9
    elif question.kind == "diagram_analysis":
        guidance_limit = 4
    elif question.kind == "short_answer":
        guidance_limit = 1
    else:
        guidance_limit = 2
    return answer[:answer_limit], guidance[:guidance_limit]


def _question_guidance(question: GeneratedQuestion) -> list[str]:
    if question.kind == "calculation":
        return [
            "Award method credit for a valid formula and substitution.",
            "Accept a correctly rounded equivalent answer with working.",
            "Apply error carried forward where the later method remains valid.",
        ]
    if "diagram" in question.prompt.casefold():
        return [
            "Credit correctly labelled axes, curves, shifts and equilibrium.",
            "The diagram must support rather than contradict the written analysis.",
        ]
    if question.marks >= 8:
        return [
            "Use the whole response and apply the level descriptors by best fit.",
            "Reward contextual analysis, developed evaluation and a supported judgement.",
        ]
    return [
        "Credit an equivalent economically precise answer.",
        "Do not reward the same developed point twice.",
    ]


def _chart(option: GeneratedOption) -> Drawing:
    drawing = Drawing(165 * mm, 90 * mm)
    x0, y0, width, height = 30, 28, 420, 190
    drawing.add(String(30, 238, option.chart_title, fontName=FONT_BOLD, fontSize=11))
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    low, high = min(option.chart_values), max(option.chart_values)
    span = max(1.0, high - low)
    points: list[float] = []
    for index, value in enumerate(option.chart_values):
        x = x0 + index * width / 4
        y = y0 + 7 + (value - low) / span * (height - 14)
        points.extend([x, y])
        drawing.add(Rect(x - 2, y - 2, 4, 4, fillColor=INK))
        drawing.add(String(x - 8, y0 - 13, option.chart_labels[index], fontSize=7))
        drawing.add(String(x + 4, y + 2, f"{value:.1f}", fontSize=7))
    drawing.add(PolyLine(points, strokeColor=INK, strokeWidth=1.2))
    return drawing


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Economics", STYLES["kicker"]),
        Paragraph("Independent practice paper", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Paragraph("Practice session · 2 hours", STYLES["body"]),
        Spacer(1, 8 * mm),
        Table(
            [["Time allowed", "2 hours"], ["Maximum mark", "80"], ["Paper reference", paper.paper_code]],
            colWidths=[45 * mm, 90 * mm],
            style=TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("BACKGROUND", (0, 0), (0, -1), GREY), ("FONT", (0, 0), (0, -1), FONT_BOLD), ("PADDING", (0, 0), (-1, -1), 7)]),
        ),
        Spacer(1, 6 * mm),
        Table(
            [
                ["Centre number", "", "Candidate number", ""],
                ["Surname", "", "First name(s)", ""],
            ],
            colWidths=[30 * mm, 42 * mm, 36 * mm, 42 * mm],
            rowHeights=[10 * mm, 10 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.6, INK),
                    ("FONTNAME", (0, 0), (-1, -1), FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 9 * mm),
        Paragraph("Instructions", STYLES["heading"]),
        Paragraph("Answer the questions specified in each section. Use a calculator where appropriate. Show working and use economic diagrams where instructed.", STYLES["body"]),
        Spacer(1, 5 * mm),
        Paragraph("Information", STYLES["heading"]),
        Paragraph("The maximum mark is 80. Marks are shown in brackets. This independently created practice paper is mapped to OCR H460 but is not produced or endorsed by OCR.", STYLES["body"]),
    ]


def _document(path: Path, paper: GeneratedPaper, kind: str) -> BaseDocTemplate:
    page_size = OCR_MARK_SCHEME_FRONT_SIZE if kind == "Mark scheme" else A4
    doc = BaseDocTemplate(str(path), pagesize=page_size, leftMargin=18 * mm, rightMargin=17 * mm, topMargin=19 * mm, bottomMargin=18 * mm, title=f"{paper.paper_code} {paper.title} — {kind}", author="Paper creator")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    templates = [
        PageTemplate(
            id="ocr-practice",
            frames=[frame],
            onPage=lambda canvas, value: _chrome(
                canvas, value, paper.paper_code, kind
            ),
        )
    ]
    if kind == "Mark scheme":
        width, height = OCR_MARK_SCHEME_LANDSCAPE_SIZE
        landscape_frame = Frame(
            18 * mm,
            18 * mm,
            width - 35 * mm,
            height - 37 * mm,
            id="mark-scheme-body",
        )
        templates.append(
            PageTemplate(
                id="ocr-mark-scheme-landscape",
                frames=[landscape_frame],
                pagesize=OCR_MARK_SCHEME_LANDSCAPE_SIZE,
                onPage=lambda canvas, value: _chrome(
                    canvas, value, paper.paper_code, kind
                ),
            )
        )
        final_width, final_height = OCR_MARK_SCHEME_FINAL_SIZE
        final_frame = Frame(
            18 * mm,
            18 * mm,
            final_width - 35 * mm,
            final_height - 37 * mm,
            id="mark-scheme-final-body",
        )
        templates.append(
            PageTemplate(
                id="ocr-mark-scheme-final",
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
        if doc.page % 2 == 1:
            canvas.setFont(FONT_BOLD, 9)
            canvas.drawRightString(page_width - 18 * mm, 18 * mm, "Turn over")
        canvas.restoreState()
        return
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(
        18 * mm,
        page_height - 13 * mm,
        page_width - 17 * mm,
        page_height - 13 * mm,
    )
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, page_height - 10 * mm, f"{code} · {kind}")
    canvas.drawRightString(page_width - 17 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text: str) -> Table:
    return Table([[Paragraph(text, STYLES["banner"])]], colWidths=[167 * mm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white), ("PADDING", (0, 0), (-1, -1), 2)]))


def _box(text: str) -> Table:
    return Table([[Paragraph(text, STYLES["body"])]], colWidths=[150 * mm], style=TableStyle([("BOX", (0, 0), (-1, -1), 0.6, INK), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")), ("PADDING", (0, 0), (-1, -1), 8)]))


class AnswerLines(Flowable):
    def __init__(self, count: int) -> None:
        super().__init__()
        self.width = 167 * mm
        self.height = count * 6.0 * mm
        self.count = count

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#b8b8b8"))
        self.canv.setLineWidth(0.4)
        self.canv.setDash(1, 1.7)
        for index in range(self.count):
            y = self.height - (index + 1) * 6.0 * mm
            self.canv.line(0, y, self.width, y)
        self.canv.setDash()


_base = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName=FONT, fontSize=9.3, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=11, leading=14, textColor=INK, alignment=TA_CENTER),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "option": ParagraphStyle("option", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11.5, leading=15),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_RIGHT),
    "choices": ParagraphStyle("choices", parent=_base["BodyText"], fontName=FONT, fontSize=9.8, leading=13, leftIndent=22),
    "answer": ParagraphStyle("answer", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=12, alignment=TA_RIGHT),
    "centre": ParagraphStyle("centre", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14, alignment=TA_CENTER),
    "centre_bold": ParagraphStyle("centre", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_CENTER),
}
