from __future__ import annotations

from functools import partial
from html import escape
from itertools import zip_longest
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
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.document_dsl import (
    DocumentRole,
    OCRQuestionHeaderFactory,
    SingleCellPanelFactory,
    flowable_question_block,
    page_sequence,
    renderer_contract,
)
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
)
from Backend.Core.exam_cover import (
    CoverProfile,
    mark_scheme_cover,
    ocr_question_cover,
)
from Backend.Core.exam_pages import ExamPage, ExamPageProfile
from Backend.Core.fonts import register_fonts
from Backend.Core.reportlab_theme import OCRAnswerLines as AnswerLines
from Backend.Core.reportlab_theme import themed_table_class

PAGE_WIDTH, PAGE_HEIGHT = A4
OCR_MARK_SCHEME_FRONT_SIZE = (594.96, 842.04)
OCR_MARK_SCHEME_LANDSCAPE_SIZE = (841.92, 595.32)
OCR_MARK_SCHEME_FINAL_SIZE = (595.32, 841.92)
INK = colors.HexColor("#151515")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)
Table = themed_table_class(Table, FONT)
RENDERER_CONTRACT = renderer_contract(
    "ocr",
    roles=(DocumentRole.QUESTION_PAPER, DocumentRole.MARK_SCHEME),
    vector_components=("economic-curve", "statistical-chart"),
)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = ocr_question_cover(_cover_profile(paper), FONT, FONT_BOLD)
    story.extend(
        _paper_three_pages(paper)
        if paper.paper_id == "paper_3"
        else _paper_one_two_pages(paper)
    )
    doc.build(story)


def render_mark_scheme(
    paper: GeneratedPaper,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        *mark_scheme_cover(_cover_profile(paper), FONT, FONT_BOLD),
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
        Spacer(1, 6 * mm),
        Paragraph("Question-specific checks", STYLES["heading"]),
        Spacer(1, 2 * mm),
        Paragraph(
            "Before awarding credit, identify the command word and required context, "
            "then check that each marking point answers the precise task. Credit a "
            "calculation only when the response shows a valid method and units where "
            "they are required. A diagram must use appropriate axes, curves, labels "
            "and equilibrium points; written analysis must explain the economic "
            "mechanism rather than merely naming it.",
            STYLES["body"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "For extended responses, use the response as a whole to select the "
            "best-fit level. Place it higher within that level only when accuracy, "
            "application, analysis and evaluation are sustained. Do not reward a "
            "memorised conclusion that is unsupported by the reasoning presented.",
            STYLES["body"],
        ),
        NextPageTemplate("ocr-mark-scheme-landscape"),
        PageBreak(),
        *_supplementary_marking_pages(),
        NextPageTemplate("ocr-mark-scheme-content"),
        PageBreak(),
    ]
    for section in paper.sections:
        for option in section.options:
            for question in option.questions:
                story.extend(_scheme_block(question))
    questions = [q for s in paper.sections for o in s.options for q in o.questions]
    diagram_focuses: set[str] = set()
    for question in questions:
        focus = _question_focus(question)
        if question.marks >= 8 and focus not in diagram_focuses:
            story.extend([PageBreak(), *_extended_diagram_page(question)])
            diagram_focuses.add(focus)
    story.extend([PageBreak(), *_assessment_objectives_page(paper, questions)])
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
        _annotation_conventions_page,
        _diagrams_and_calculations_page,
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
        (
            "1",
            "Read the complete question paper, source material and mark scheme before marking any response.",
        ),
        (
            "2",
            "Apply the published criteria directly. Do not compare one candidate with another.",
        ),
        (
            "3",
            "Mark positively: award credit for relevant economic knowledge, application, analysis and evaluation.",
        ),
        (
            "4",
            "Credit a valid alternative route when it answers the precise question and is economically coherent.",
        ),
        (
            "5",
            "Where a response is crossed out, mark a clearly presented replacement. Otherwise mark the legible original response.",
        ),
        (
            "6",
            "Do not award a point that is contradicted elsewhere in the same response.",
        ),
        (
            "7",
            "Check additional answer space before recording no response or completing a question total.",
        ),
        (
            "8",
            "For calculations, apply error carried forward only where the later method remains valid.",
        ),
        (
            "9",
            "For levels questions, read the whole response before selecting the best-fit level and mark.",
        ),
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
        (
            "AO1",
            "Knowledge and understanding",
            "Accurate economic ideas, principles, models and terminology.",
        ),
        (
            "AO2",
            "Application",
            "Relevant use of the supplied context, figures, constraints and evidence.",
        ),
        (
            "AO3",
            "Analysis",
            "A connected chain of reasoning that establishes causes, mechanisms and consequences.",
        ),
        (
            "AO4",
            "Evaluation",
            "Testing assumptions and significance before reaching a supported judgement.",
        ),
    ]
    notes = [
        (
            "Accurate",
            "The response is economically correct and uses terminology precisely.",
        ),
        (
            "Applied",
            "The response selects contextual material and uses it to answer the question set.",
        ),
        (
            "Developed",
            "Each link in the analysis is explained rather than merely asserted.",
        ),
        (
            "Supported",
            "The final judgement follows from the analysis and evaluation presented.",
        ),
    ]
    return [
        Paragraph("MARKING INSTRUCTIONS CONTINUED", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
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
        (
            "1",
            "Read the response as a whole and identify the highest descriptor it meets securely.",
        ),
        ("2", "Use best fit when a response shows qualities from adjacent levels."),
        (
            "3",
            "Select the top of a level when its qualities are sustained; select the bottom when they are only just demonstrated.",
        ),
        (
            "4",
            "Do not count isolated points. Consider accuracy, relevance, development and coherence together.",
        ),
        (
            "5",
            "A balanced response need not give equal space to every view, but material counterarguments must be considered.",
        ),
        (
            "6",
            "A judgement earns evaluation credit only when it is supported by the preceding reasoning.",
        ),
        ("7", "If no material is worthy of credit, award zero."),
    ]
    bands = [
        (
            "Top",
            "Descriptor is met consistently; analysis is secure and judgement is fully supported.",
        ),
        (
            "Middle",
            "Descriptor is met reasonably well; development is sound but not sustained throughout.",
        ),
        (
            "Bottom",
            "Response just enters the level; relevant qualities are present but uneven or incomplete.",
        ),
    ]
    return [
        Paragraph("LEVELS-BASED RESPONSES", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(["", "Procedure"], rows, [12 * mm, 248 * mm]),
        Spacer(1, 6 * mm),
        _guidance_table(
            ["Position", "How to place the mark"], bands, [32 * mm, 228 * mm]
        ),
    ]


def _diagrams_and_calculations_page() -> list[Flowable]:
    rows = [
        (
            "Economic diagram",
            "Correct axes, curves, labels, shift and equilibrium relevant to the question.",
            "A diagram that contradicts the written analysis or has ambiguous axes.",
        ),
        (
            "Calculation",
            "Valid method, substituted figures, correct answer, units and requested accuracy.",
            "An unsupported answer where working is required or a value with the wrong sign/unit.",
        ),
        (
            "Data comparison",
            "Accurate figures, direction, magnitude and a comparison tied to the question.",
            "Copying a figure without using it or describing two values independently.",
        ),
        (
            "Chain of reasoning",
            "A cause linked through a mechanism to a relevant economic consequence.",
            "A list of effects with no explained connection.",
        ),
        (
            "Judgement",
            "A conclusion supported by criteria such as scale, time, assumptions or distribution.",
            "An unsupported assertion or repetition of the question.",
        ),
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
        (
            "DEV",
            "Developed analysis",
            "A valid consequence is linked to the preceding economic point.",
        ),
        (
            "APP",
            "Application",
            "The response uses a supplied figure, fact or contextual feature.",
        ),
        (
            "EVAL",
            "Evaluation",
            "A relevant limitation, condition or counterargument is developed.",
        ),
        ("J", "Judgement", "A supported conclusion answers the precise question."),
        ("BOD", "Benefit of doubt", "Meaning is clear despite minor imprecision."),
        (
            "ECF",
            "Error carried forward",
            "A later valid method follows an earlier numerical error.",
        ),
        ("REP", "Repeated point", "Do not award the same developed idea twice."),
        (
            "CON",
            "Contradiction",
            "Withhold credit where the response reverses a valid point.",
        ),
        ("MAX", "Maximum", "Stop awarding when the stated maximum is reached."),
        (
            "0",
            "Attempted, no credit",
            "Some response is present but it does not meet the criteria.",
        ),
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
        (
            "State / identify",
            "Award one mark for each distinct correct item up to the stated maximum.",
        ),
        (
            "Define",
            "Require the essential economic meaning; exact wording is not necessary.",
        ),
        (
            "Explain",
            "Award the explanation mark only where a valid link or mechanism is established.",
        ),
        (
            "Calculate",
            "Follow the question-specific allocation for method, substitution and final answer.",
        ),
        ("Compare", "Require a relative statement using both values, trends or cases."),
        ("Analyse", "Reward developed, connected reasoning applied to the question."),
        (
            "Evaluate",
            "Reward a relevant counterargument or condition and a supported conclusion.",
        ),
    ]
    examples = [
        ("Two valid points where two are requested", "2"),
        ("Three listed points where only two are requested", "Maximum 2"),
        ("Correct point followed by a contradiction", "0 for that point"),
        (
            "Correct method with a carried-forward arithmetic error",
            "Method credit as specified",
        ),
    ]
    return [
        Paragraph("SHORT-ANSWER QUESTIONS", STYLES["centre_bold"]),
        Spacer(1, 4 * mm),
        _guidance_table(["Command", "Marking approach"], rows, [45 * mm, 215 * mm]),
        Spacer(1, 6 * mm),
        _guidance_table(["Response", "Treatment"], examples, [190 * mm, 70 * mm]),
        Spacer(1, 5 * mm),
        Paragraph(
            "For diagrams and calculations, require the relevant axes, curves, labels, "
            "method, units and requested accuracy. Credit a coherent error-carried-forward "
            "method where the question-specific guidance permits it.",
            STYLES["small"],
        ),
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
        [[Paragraph(escape(value), STYLES["small"]) for value in row] for row in rows]
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


def _level_bands(marks: int) -> list[tuple[int, str]]:
    if marks >= 20:
        return [
            (5, "21\u201325"),
            (4, "16\u201320"),
            (3, "11\u201315"),
            (2, "6\u201310"),
            (1, "1\u20135"),
        ]
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
    topic_focuses = {
        "micro-1": "resource allocation and opportunity cost",
        "micro-2": "demand, supply and market equilibrium",
        "micro-3": "business objectives, costs and revenue",
        "micro-4": "market structures and contestability",
        "micro-5": "the labour market",
        "micro-6": "market failure and government intervention",
        "macro-1": "aggregate demand and aggregate supply",
        "macro-2": "macroeconomic performance and policy objectives",
        "macro-3": "fiscal, monetary and supply-side policy",
        "macro-4": "international trade and exchange rates",
        "macro-5": "money, credit and the financial sector",
    }
    if question.topic_id in topic_focuses:
        return topic_focuses[question.topic_id]

    prompt = question.prompt.casefold()
    focuses = [
        ("objectives of firms", "business objectives, costs and revenue"),
        ("costs, revenues", "business objectives, costs and revenue"),
        ("opportunity cost", "resource allocation and opportunity cost"),
        ("production possibility", "resource allocation and opportunity cost"),
        ("contestab", "market structures and contestability"),
        ("concentrat", "market structures and concentration"),
        ("price discrimination", "market structures and price discrimination"),
        ("externalit", "market failure and government intervention"),
        ("public goods", "market failure and government intervention"),
        ("aggregate demand", "aggregate demand and aggregate supply"),
        ("monetary policy", "fiscal, monetary and supply-side policy"),
        ("fiscal policy", "fiscal, monetary and supply-side policy"),
        ("financial", "money, credit and the financial sector"),
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
    if "business objectives" in focus:
        _add_firm_objectives_diagram(
            drawing,
            x0=x0,
            y0=y0,
            width=width,
            height=height,
            alternative_objective=shifted,
            compact=compact,
        )
        return
    if "resource allocation" in focus:
        _add_ppf_diagram(
            drawing,
            x0=x0,
            y0=y0,
            width=width,
            height=height,
            shifted=shifted,
            compact=compact,
        )
        return

    if "labour" in focus:
        y_label, x_label, down_label, up_label = "Wage", "Employment", "DL", "SL"
    elif "aggregate" in focus or "macroeconomic" in focus or "policy" in focus:
        y_label, x_label, down_label, up_label = (
            "Price level",
            "Real output",
            "AD",
            "SRAS",
        )
    elif "exchange" in focus or "international" in focus:
        y_label, x_label, down_label, up_label = "Exchange rate", "Currency", "D", "S"
    elif "financial" in focus or "credit" in focus:
        y_label, x_label, down_label, up_label = "Interest rate", "Credit", "D", "S"
    elif "market failure" in focus:
        y_label, x_label, down_label, up_label = (
            "Price / cost",
            "Quantity",
            "MPB",
            "MPC",
        )
    else:
        y_label, x_label, down_label, up_label = "Price", "Quantity", "D", "S"

    shift_titles = [
        ("market structures", "Entry increases competitive supply"),
        ("labour", "Change in labour supply"),
        ("market failure", "Social cost changes equilibrium"),
        ("aggregate", "Aggregate supply shifts"),
        ("macroeconomic", "Aggregate supply shifts"),
        ("policy", "Policy changes aggregate supply"),
        ("financial", "Credit supply changes"),
        ("international", "Currency supply changes"),
    ]
    title = focus.capitalize()
    if shifted:
        title = next(
            (label for token, label in shift_titles if token in focus),
            "Change in market supply",
        )
    title_size = 6 if compact else 9
    label_size = 5 if compact else 7
    inset = 10 if compact else 18
    drawing.add(
        String(
            x0,
            y0 + height + (10 if compact else 28),
            title,
            fontName=FONT_BOLD,
            fontSize=title_size,
        )
    )
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    drawing.add(
        String(x0 - 3, y0 + height + 3, y_label, fontName=FONT, fontSize=label_size)
    )
    drawing.add(
        String(x0 + width - 15, y0 - 9, x_label, fontName=FONT, fontSize=label_size)
    )

    drawing.add(Line(x0 + inset, y0 + height - inset, x0 + width - inset, y0 + inset))
    drawing.add(Line(x0 + inset, y0 + inset, x0 + width - inset, y0 + height - inset))
    drawing.add(
        String(
            x0 + width - inset + 1,
            y0 + inset - 3,
            down_label,
            fontName=FONT,
            fontSize=label_size,
        )
    )
    drawing.add(
        String(
            x0 + width - inset + 1,
            y0 + height - inset - 2,
            up_label,
            fontName=FONT,
            fontSize=label_size,
        )
    )

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
        shifted_supply_label = "MSC" if up_label == "MPC" else f"{up_label}1"
        drawing.add(
            String(
                x0 + width - inset + shift,
                y0 + height - inset - 2,
                shifted_supply_label,
                fontName=FONT,
                fontSize=label_size,
            )
        )
        equilibrium_x += shift / 2
        equilibrium_y -= shift * height / (2 * width)
        equilibrium_label = "E1"

    dash = [2, 2] if compact else [3, 2]
    drawing.add(
        Line(equilibrium_x, y0, equilibrium_x, equilibrium_y, strokeDashArray=dash)
    )
    drawing.add(
        Line(x0, equilibrium_y, equilibrium_x, equilibrium_y, strokeDashArray=dash)
    )
    drawing.add(
        String(
            equilibrium_x + 3,
            equilibrium_y + 3,
            equilibrium_label,
            fontName=FONT_BOLD,
            fontSize=label_size,
        )
    )


def _add_firm_objectives_diagram(
    drawing: Drawing,
    *,
    x0: float,
    y0: float,
    width: float,
    height: float,
    alternative_objective: bool,
    compact: bool,
) -> None:
    title = (
        "Revenue maximisation: MR = 0"
        if alternative_objective
        else "Profit maximisation: MC = MR"
    )
    title_size = 6 if compact else 9
    label_size = 5 if compact else 7
    inset = 10 if compact else 18
    left = x0 + inset
    right = x0 + width - inset
    bottom = y0 + inset
    top = y0 + height - inset

    drawing.add(
        String(
            x0,
            y0 + height + (10 if compact else 28),
            title,
            fontName=FONT_BOLD,
            fontSize=title_size,
        )
    )
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    drawing.add(
        String(
            x0 - 3,
            y0 + height + 3,
            "Cost / revenue",
            fontName=FONT,
            fontSize=label_size,
        )
    )
    drawing.add(
        String(x0 + width - 15, y0 - 9, "Output", fontName=FONT, fontSize=label_size)
    )

    drawing.add(Line(left, top, right, bottom))
    mr_end_x = x0 + width * 0.62
    drawing.add(Line(left, top, mr_end_x, y0))
    drawing.add(Line(left, bottom, right, top))
    drawing.add(String(right + 1, bottom - 2, "AR", fontName=FONT, fontSize=label_size))
    drawing.add(String(mr_end_x - 18, y0 + 6, "MR", fontName=FONT, fontSize=label_size))
    drawing.add(String(right + 1, top - 2, "MC", fontName=FONT, fontSize=label_size))

    plot_width = right - left
    plot_height = top - bottom
    quantity_fraction = 0.62 if alternative_objective else 0.375
    quantity_x = left + plot_width * quantity_fraction
    price_y = top - plot_height * quantity_fraction
    dash = [2, 2] if compact else [3, 2]
    drawing.add(Line(quantity_x, y0, quantity_x, price_y, strokeDashArray=dash))
    drawing.add(Line(x0, price_y, quantity_x, price_y, strokeDashArray=dash))
    drawing.add(
        String(
            quantity_x + 3,
            y0 + 3,
            "Qr" if alternative_objective else "Qp",
            fontName=FONT_BOLD,
            fontSize=label_size,
        )
    )
    drawing.add(
        String(
            x0 + 3,
            price_y + 3,
            "Pr" if alternative_objective else "Pp",
            fontName=FONT_BOLD,
            fontSize=label_size,
        )
    )


def _add_ppf_diagram(
    drawing: Drawing,
    *,
    x0: float,
    y0: float,
    width: float,
    height: float,
    shifted: bool,
    compact: bool,
) -> None:
    title = (
        "Outward shift in productive capacity"
        if shifted
        else "Production possibility frontier"
    )
    title_size = 6 if compact else 9
    label_size = 5 if compact else 7
    drawing.add(
        String(
            x0,
            y0 + height + (10 if compact else 28),
            title,
            fontName=FONT_BOLD,
            fontSize=title_size,
        )
    )
    drawing.add(Line(x0, y0, x0, y0 + height))
    drawing.add(Line(x0, y0, x0 + width, y0))
    drawing.add(
        String(x0 - 3, y0 + height + 3, "Good Y", fontName=FONT, fontSize=label_size)
    )
    drawing.add(
        String(x0 + width - 15, y0 - 9, "Good X", fontName=FONT, fontSize=label_size)
    )

    def frontier(scale: float) -> list[float]:
        points: list[float] = []
        for x_fraction, y_fraction in (
            (0.06, 0.94),
            (0.22, 0.89),
            (0.40, 0.76),
            (0.58, 0.58),
            (0.77, 0.34),
            (0.94, 0.06),
        ):
            points.extend(
                [
                    x0 + width * min(x_fraction * scale, 0.98),
                    y0 + height * min(y_fraction * scale, 0.98),
                ]
            )
        return points

    drawing.add(PolyLine(frontier(0.88 if shifted else 1.0)))
    drawing.add(
        String(
            x0 + width * 0.68,
            y0 + height * 0.42,
            "PPF",
            fontName=FONT,
            fontSize=label_size,
        )
    )
    if shifted:
        drawing.add(PolyLine(frontier(1.0)))
        drawing.add(
            String(
                x0 + width * 0.76,
                y0 + height * 0.52,
                "PPF1",
                fontName=FONT,
                fontSize=label_size,
            )
        )


def _extended_diagram_page(
    question: GeneratedQuestion,
) -> list[Flowable]:
    return [
        Paragraph(f"Question {question.number} diagram guidance", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(question.prompt, STYLES["body"]),
        Spacer(1, 3 * mm),
        _economics_diagram_pair([question, question]),
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
        totals = [
            total + value for total, value in zip(totals, allocation, strict=True)
        ]
        if question.marks >= 20:
            quantitative = 8 if extended_group_index == 0 else 0
            extended_group_index += 1
        elif (
            question.kind == "calculation"
            or "compare" in question.command_word.casefold()
        ):
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
        multiple_choice = [
            question for question in questions if question.kind == "multiple_choice"
        ]
        written = [
            question for question in questions if question.kind != "multiple_choice"
        ]
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
    if question.kind in {"calculation", "data"} or question.command_word.casefold() in {
        "calculate",
        "compare",
    }:
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
            *[
                flowable
                for question in data.questions[:3]
                for flowable in _question_block(question)
            ],
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
        _continuation_page(paper.paper_code, "Question 1 continued"),
    ]
    if paper.paper_id == "paper_1":
        pages.extend(
            [
                _section_transition_page(paper.paper_code, "Section B", blank=True),
                [*_intro(section_b), *_choice_prompts(section_b)],
                _continuation_page(paper.paper_code),
                _continuation_page(paper.paper_code),
                _section_transition_page(paper.paper_code, "Section C"),
                [*_intro(section_c), *_choice_prompts(section_c)],
                _continuation_page(paper.paper_code),
                _continuation_page(paper.paper_code),
                _end_of_paper_page(line_count=10, spacer=70 * mm),
                _extra_answer_page(paper.paper_code),
                _extra_answer_page(paper.paper_code, show_heading=False),
                _question_paper_legal_page(),
            ]
        )
    else:
        pages.extend(
            [
                [*_intro(section_b), *_choice_prompts(section_b)],
                _continuation_page(paper.paper_code),
                _continuation_page(paper.paper_code),
                _section_transition_page(paper.paper_code, "Section C"),
                [*_intro(section_c), *_choice_prompts(section_c)],
                _continuation_page(paper.paper_code),
                _continuation_page(paper.paper_code),
                _end_of_paper_page(line_count=6, spacer=95 * mm),
                _extra_answer_page(paper.paper_code),
                _blank_question_page(paper.paper_code),
                _blank_question_page(paper.paper_code),
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
    paper_code: str,
    *,
    show_heading: bool = True,
) -> list[Flowable]:
    return [
        ExamPage(
            ExamPageProfile(
                board="ocr",
                code=paper_code,
                heading="EXTRA ANSWER SPACE" if show_heading else "",
                variant="additional" if show_heading else "continuation",
            ),
            font=FONT,
            bold_font=FONT_BOLD,
        )
    ]


def _section_transition_page(
    paper_code: str,
    section: str,
    *,
    blank: bool = False,
) -> list[Flowable]:
    if blank:
        return [
            ExamPage(
                ExamPageProfile(
                    board="ocr",
                    code=paper_code,
                    heading="BLANK PAGE",
                    variant="blank",
                    do_not_write=True,
                    message=f"{section} starts on the next page",
                ),
                font=FONT,
                bold_font=FONT_BOLD,
            )
        ]
    return [
        AnswerLines(6),
        Spacer(1, 70 * mm),
        Paragraph(f"{section} starts on the next page", STYLES["centre_bold"]),
    ]


def _end_of_paper_page(*, line_count: int, spacer: float) -> list[Flowable]:
    return [
        AnswerLines(line_count),
        Spacer(1, spacer),
        Paragraph("END OF QUESTION PAPER", STYLES["centre_bold"]),
    ]


def _blank_question_page(paper_code: str) -> list[Flowable]:
    return [
        ExamPage(
            ExamPageProfile(
                board="ocr",
                code=paper_code,
                heading="BLANK PAGE",
                variant="blank",
                do_not_write=True,
            ),
            font=FONT,
            bold_font=FONT_BOLD,
        )
    ]


def _continuation_page(
    paper_code: str,
    heading: str = "",
) -> list[Flowable]:
    return [
        ExamPage(
            ExamPageProfile(
                board="ocr",
                code=paper_code,
                heading=heading,
                variant="continuation",
            ),
            font=FONT,
            bold_font=FONT_BOLD,
        )
    ]


def _paper_three_pages(paper: GeneratedPaper) -> list[Flowable]:
    mcq, data_section = paper.sections
    data = data_section.options[0]
    pages: list[list[Flowable]] = []
    cursor = 0
    mcq_page_counts = (3, *([2] * 12), 3)
    for page_index, question_count in enumerate(mcq_page_counts):
        content: list[Flowable] = []
        if page_index == 0:
            content.extend(_intro(mcq))
        for option in mcq.options[cursor : cursor + question_count]:
            content.extend(_mcq_block(option.questions[0]))
        cursor += question_count
        pages.append(content)
    assert cursor == len(mcq.options)
    pages.extend(
        [
            [
                *_intro(data_section),
                Paragraph(data.stimulus[0], STYLES["extract"]),
                Spacer(1, 3 * mm),
                _paper_three_figure(data, 1),
            ],
            [
                *_question_with_answer_lines(
                    data.questions[0],
                    6,
                    spacing_mm=8.0,
                ),
                *_question_with_answer_lines(
                    data.questions[1],
                    9,
                    spacing_mm=8.0,
                ),
            ],
            [*_question_block(data.questions[2]), AnswerLines(28, spacing_mm=8.0)],
            [
                Paragraph("Question 33 continued", STYLES["centre_bold"]),
                AnswerLines(28, spacing_mm=8.0),
            ],
            [
                _banner("Extract 2"),
                Spacer(1, 3 * mm),
                Paragraph(data.stimulus[1], STYLES["extract"]),
                Spacer(1, 3 * mm),
                _paper_three_figure(data, 2),
            ],
            [
                *_question_with_answer_lines(
                    data.questions[3],
                    9,
                    spacing_mm=8.0,
                ),
                *_question_with_answer_lines(
                    data.questions[4],
                    6,
                    spacing_mm=8.0,
                ),
                Spacer(1, 3 * mm),
                Paragraph("Turn over for the next question", STYLES["centre_bold"]),
            ],
            [*_question_block(data.questions[5]), AnswerLines(28, spacing_mm=8.0)],
            [
                Paragraph("Question 36 continued", STYLES["centre_bold"]),
                AnswerLines(28, spacing_mm=8.0),
            ],
            [
                _banner("Extract 3"),
                Spacer(1, 3 * mm),
                Paragraph(data.stimulus[2], STYLES["extract"]),
                Spacer(1, 3 * mm),
                _paper_three_figure(data, 3),
                *_question_with_answer_lines(
                    data.questions[6],
                    6,
                    spacing_mm=8.0,
                ),
            ],
            [
                _question_table(data.questions[7], show_marks=False),
                Spacer(1, 4 * mm),
                AnswerLines(27, spacing_mm=8.0),
                _answer_mark(data.questions[7]),
                Paragraph("END OF QUESTION PAPER", STYLES["centre_bold"]),
            ],
            _extra_answer_page(paper.paper_code),
            _extra_answer_page(paper.paper_code, show_heading=False),
            _question_paper_legal_page(),
        ]
    )
    assert len(pages) == 27
    return _page_sequence(pages)


def _paper_three_figure(option: GeneratedOption, extract_number: int) -> Drawing:
    question_index = {1: 0, 2: 3, 3: 6}[extract_number]
    context = option.questions[question_index].authoring_context
    figure = context.get("figure", {})
    labels = [str(label) for label in figure.get("labels", option.chart_labels)]
    series = figure.get("series", [])
    if not labels or not series:
        return _chart(option)

    drawing = Drawing(165 * mm, 66 * mm)
    x0, y0, width, height = 42, 32, 380, 108
    drawing.add(
        String(
            x0,
            173,
            f"Fig. {figure.get('number', f'{extract_number}.1')}",
            fontName=FONT_BOLD,
            fontSize=9,
        )
    )
    drawing.add(
        String(
            x0,
            158,
            str(figure.get("title", option.chart_title)),
            fontName=FONT_BOLD,
            fontSize=9,
        )
    )
    all_values = [float(value) for item in series for value in item.get("values", [])]
    low = min(all_values)
    high = max(all_values)
    padding = max(2.0, (high - low) * 0.12)
    low -= padding
    high += padding
    span = max(1.0, high - low)
    for grid_index in range(5):
        y = y0 + grid_index * height / 4
        drawing.add(
            Line(
                x0,
                y,
                x0 + width,
                y,
                strokeColor=colors.HexColor("#c6c6c6"),
                strokeWidth=0.35,
            )
        )
        value = low + grid_index * span / 4
        drawing.add(
            String(
                x0 - 7,
                y - 2,
                f"{value:.0f}",
                fontName=FONT,
                fontSize=6.5,
                textAnchor="end",
            )
        )
    drawing.add(Line(x0, y0, x0, y0 + height, strokeColor=INK))
    drawing.add(Line(x0, y0, x0 + width, y0, strokeColor=INK))
    strokes = [INK, colors.HexColor("#666666")]
    for series_index, item in enumerate(series[:2]):
        values = [float(value) for value in item.get("values", [])]
        points: list[float] = []
        for index, value in enumerate(values):
            x = x0 + index * width / max(1, len(values) - 1)
            y = y0 + (value - low) / span * height
            points.extend([x, y])
            drawing.add(
                Rect(
                    x - 1.8,
                    y - 1.8,
                    3.6,
                    3.6,
                    fillColor=strokes[series_index],
                    strokeColor=strokes[series_index],
                )
            )
        line = PolyLine(
            points,
            strokeColor=strokes[series_index],
            strokeWidth=1.2,
        )
        if series_index == 1:
            line.strokeDashArray = [5, 3]
        drawing.add(line)
        legend_x = x0 + series_index * 190
        drawing.add(
            Line(
                legend_x,
                15,
                legend_x + 20,
                15,
                strokeColor=strokes[series_index],
                strokeWidth=1.2,
            )
        )
        drawing.add(
            String(
                legend_x + 25,
                12,
                str(item.get("label", f"Series {series_index + 1}")),
                fontName=FONT,
                fontSize=6.5,
            )
        )
    for index, label in enumerate(labels):
        x = x0 + index * width / max(1, len(labels) - 1)
        drawing.add(
            String(
                x,
                y0 - 12,
                label,
                fontName=FONT,
                fontSize=6.5,
                textAnchor="middle",
            )
        )
    return drawing


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
    return [
        _banner(f"Section {section.id}: {section.title}"),
        Spacer(1, 3 * mm),
        Paragraph(section.instructions, STYLES["instruction"]),
        Spacer(1, 4 * mm),
    ]


def _choice_prompts(section) -> list[Flowable]:
    result: list[Flowable] = []
    for index, option in enumerate(section.options):
        if index:
            result.extend(
                [
                    Spacer(1, 6 * mm),
                    Paragraph("OR", STYLES["centre_bold"]),
                    Spacer(1, 6 * mm),
                ]
            )
        result.extend(_question_block(option.questions[0]))
    return result


def _mcq_block(question: GeneratedQuestion) -> list[Flowable]:
    choices = "<br/>".join(
        f"<b>{'ABCD'[index]}</b> {text}" for index, text in enumerate(question.choices)
    )
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


def _question_with_answer_lines(
    question: GeneratedQuestion,
    line_count: int,
    *,
    spacing_mm: float = 6.0,
) -> list[Flowable]:
    return [
        _question_table(question, show_marks=False),
        Spacer(1, 2 * mm),
        AnswerLines(line_count, spacing_mm=spacing_mm),
        _answer_mark(question),
        Spacer(1, 4 * mm),
    ]


def _answer_mark(question: GeneratedQuestion) -> Table:
    return Table(
        [[Paragraph(f"[{question.marks}]", STYLES["marks"])]],
        colWidths=[167 * mm],
        style=TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


class _CreditTable(Table):
    """Carry the visible question label into an in-row continuation."""

    @staticmethod
    def _cell_text(value):
        if isinstance(value, (tuple, list)):
            return "".join(_CreditTable._cell_text(part) for part in value)
        return (
            value.getPlainText() if hasattr(value, "getPlainText") else str(value or "")
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._question_number = next(
            (
                self._cell_text(row[0])
                for row in self._cellvalues[1:]
                if self._cell_text(row[0]).strip()
            ),
            "",
        )

    def split(self, availWidth, availHeight):
        pieces = super().split(availWidth, availHeight)
        if len(pieces) == 2:
            following = pieces[1]._cellvalues[1][0]
            for piece in pieces:
                piece._question_number = self._question_number
            if not self._cell_text(following).strip() and self._question_number:
                pieces[1]._cellvalues[1][0] = Paragraph(
                    escape(self._question_number), STYLES["scheme"]
                )
        return pieces


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
    # One visible labelled row per complete marking statement. The paginator
    # can continue rows; no point budgets, clipping or target-page padding.
    style = STYLES["scheme"]

    def cell(text: str) -> Paragraph:
        return Paragraph(escape(text), style)

    rows = [[cell(label) for label in ("Question", "Answer", "Mark", "Guidance")]]
    rows.append(
        [
            cell(question.number),
            cell(question.prompt),
            cell(str(question.marks)),
            cell(""),
        ]
    )
    seen: set[str] = set()
    seen_labelled_guidance: set[tuple[str, str]] = set()
    answers: list[str] = []
    guidance: list[str] = []
    for point in question.mark_scheme:
        if point in seen:
            continue
        seen.add(point)
        target = (
            guidance
            if point.casefold().startswith(
                (
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
            )
            else answers
        )
        target.append(point)
    for point in question.structured_mark_scheme:
        if point.text not in seen:
            answers.append(point.text)
            seen.add(point.text)
        for prefix, values in (
            ("Accept", point.alternatives),
            ("Allow", point.allow),
            ("Do not accept", point.do_not_accept),
            ("Ignore", point.ignore),
        ):
            for value in values:
                identity = (prefix, value)
                if identity in seen_labelled_guidance:
                    continue
                seen_labelled_guidance.add(identity)
                guidance.append(f"{prefix}: {value}")
    guidance.extend(_question_guidance(question))
    for answer, note in zip_longest(answers, guidance, fillvalue=""):
        rows.append([cell(question.number), cell(answer), cell(""), cell(note)])
    descriptor_spans: list[tuple] = []
    if question.scheme_mode == "levels":
        bands = _level_bands(question.marks)
        for level, mark_range in bands:
            descriptor = _level_descriptor_text(question, level, len(bands))
            descriptor_spans.append(("SPAN", (1, len(rows)), (3, len(rows))))
            rows.append(
                [
                    cell(question.number),
                    cell(f"Level {level} ({mark_range} marks): {descriptor}"),
                    cell(""),
                    cell(""),
                ]
            )
        rows.append(
            [
                cell(question.number),
                cell("0 marks: Response is not worthy of credit."),
                cell(""),
                cell(""),
            ]
        )
    for row in rows[2:]:
        row[0] = cell("")
    table = _CreditTable(
        rows,
        colWidths=[72.0, 302.44, 49.62, 302.90],
        repeatRows=1,
        splitByRow=1,
        splitInRow=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.48, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.48, colors.black),
                ("LINEBEFORE", (1, 0), (1, -1), 0.48, colors.black),
                (
                    "LINEBEFORE",
                    (2, 0),
                    (2, descriptor_spans[0][1][1] - 1 if descriptor_spans else -1),
                    0.48,
                    colors.black,
                ),
                (
                    "LINEBEFORE",
                    (3, 0),
                    (3, descriptor_spans[0][1][1] - 1 if descriptor_spans else -1),
                    0.48,
                    colors.black,
                ),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("NOSPLIT", (0, 0), (-1, 2)),
                *descriptor_spans,
            ]
        )
    )
    result: list[Flowable] = [table, Spacer(1, 12)]
    if question.kind == "diagram_analysis":
        result.extend(
            [
                Paragraph(
                    f"Question {escape(question.number)} diagram guidance",
                    STYLES["heading"],
                ),
                _compact_economics_diagram_pair([question, question]),
                Spacer(1, 12),
            ]
        )
    return result


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
        drawing.add(
            String(
                x - 8, y0 - 13, option.chart_labels[index], fontName=FONT, fontSize=7
            )
        )
        drawing.add(String(x + 4, y + 2, f"{value:.1f}", fontName=FONT, fontSize=7))
    drawing.add(PolyLine(points, strokeColor=INK, strokeWidth=1.2))
    return drawing


def _cover_profile(paper: GeneratedPaper) -> CoverProfile:
    return CoverProfile(
        board="ocr",
        subject="Economics",
        code=paper.paper_code,
        paper_title=paper.title,
        duration="2 hours",
        total_marks=paper.total_marks,
        materials=("You may use an appropriate calculator.",),
        instructions=(
            "Use black ink. You can use an HB pencil for diagrams.",
            "Answer all questions in Section A and one question in Sections B and C.",
            "Write your answers in the spaces provided.",
        ),
        information=(
            "The quality of extended responses will be assessed where indicated.",
            "This is independently authored and is not produced or endorsed by OCR.",
        ),
    )


def _document(path: Path, paper: GeneratedPaper, kind: str) -> BaseDocTemplate:
    page_size = OCR_MARK_SCHEME_FRONT_SIZE if kind == "Mark scheme" else A4
    doc = BaseDocTemplate(
        str(path),
        pagesize=page_size,
        leftMargin=18 * mm,
        rightMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="Paper creator",
        subject="Independent A-level Economics practice material",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")

    if kind == "Question paper":
        def record_question_end(flowable) -> None:
            if isinstance(flowable, Paragraph) and flowable.getPlainText() == "END OF QUESTION PAPER":
                doc._question_paper_end_page = doc.page
        doc.afterFlowable = record_question_end

    def draw_chrome(canvas, value) -> None:
        _chrome(canvas, value, paper.paper_code, kind)

    chrome_callbacks = (
        {"onPageEnd": draw_chrome}
        if kind == "Question paper"
        else {"onPage": draw_chrome}
    )
    templates = [
        PageTemplate(
            id="ocr-practice",
            frames=[frame],
            **chrome_callbacks,
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
        templates.append(
            PageTemplate(
                id="ocr-mark-scheme-content",
                frames=[
                    Frame(
                        42.54,
                        38,
                        726.96,
                        height - 56.16 - 38,
                        leftPadding=0,
                        rightPadding=0,
                        topPadding=0,
                        bottomPadding=0,
                        id="mark-scheme-content",
                    )
                ],
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
    if doc.page == 1:
        canvas.restoreState()
        return
    if kind == "Question paper" and doc.page > 1:
        canvas.setFillColor(INK)
        canvas.setFont(FONT, 11)
        canvas.drawCentredString(page_width / 2, page_height - 18.8 * mm, str(doc.page))
        canvas.setFont(FONT, 6)
        canvas.drawString(21.5 * mm, 20.2 * mm, code)
        if doc.page % 2 == 1 and getattr(doc, "_question_paper_end_page", None) != doc.page:
            canvas.setFont(FONT_BOLD, 10)
            canvas.drawRightString(page_width - 23 * mm, 21.2 * mm, "Turn over")
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


_base = getSampleStyleSheet()
STYLES = {
    "scheme": ParagraphStyle(
        "scheme",
        fontName=FONT,
        fontSize=11,
        leading=13,
    ),
    "body": ParagraphStyle(
        "body", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14
    ),
    "small": ParagraphStyle(
        "small", parent=_base["BodyText"], fontName=FONT, fontSize=10, leading=12
    ),
    "heading": ParagraphStyle(
        "heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14
    ),
    "kicker": ParagraphStyle(
        "kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18
    ),
    "title": ParagraphStyle(
        "title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27
    ),
    "subtitle": ParagraphStyle(
        "subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18
    ),
    "banner": ParagraphStyle(
        "banner",
        parent=_base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=INK,
        alignment=TA_CENTER,
    ),
    "instruction": ParagraphStyle(
        "instruction",
        parent=_base["BodyText"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
    ),
    "option": ParagraphStyle(
        "option",
        parent=_base["Heading3"],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=15,
    ),
    "extract": ParagraphStyle(
        "extract", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14
    ),
    "marks": ParagraphStyle(
        "marks",
        parent=_base["BodyText"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT,
    ),
    "choices": ParagraphStyle(
        "choices",
        parent=_base["BodyText"],
        fontName=FONT,
        fontSize=9.8,
        leading=13,
        leftIndent=22,
    ),
    "answer": ParagraphStyle(
        "answer",
        parent=_base["BodyText"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        alignment=TA_RIGHT,
    ),
    "centre": ParagraphStyle(
        "centre",
        parent=_base["BodyText"],
        fontName=FONT,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
    ),
    "centre_bold": ParagraphStyle(
        "centre",
        parent=_base["Heading3"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    ),
}
_question_table = OCRQuestionHeaderFactory(
    body_style=STYLES["body"],
    marks_style=STYLES["marks"],
    extended_response_threshold=15,
    mark_column_width=20 * mm,
    table_class=Table,
).question_table
_banner = SingleCellPanelFactory(
    paragraph_style=STYLES["banner"],
    width=167 * mm,
    background=colors.white,
    padding=2,
    table_class=Table,
).panel
_box = SingleCellPanelFactory(
    paragraph_style=STYLES["body"],
    width=150 * mm,
    background=colors.HexColor("#f7f7f7"),
    padding=8,
    border_width=0.6,
    border_color=INK,
    table_class=Table,
).panel
_page_sequence = page_sequence
_question_block = partial(flowable_question_block, question_table=_question_table)
