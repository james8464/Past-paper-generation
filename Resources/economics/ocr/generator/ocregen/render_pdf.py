from __future__ import annotations

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
    for section in paper.sections:
        story.extend([_banner(f"Section {section.id}: {section.title}"), Spacer(1, 4 * mm)])
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
    topics = [
        (
            "Applying the mark scheme",
            "Read the whole response before awarding a mark. Credit only material that "
            "answers the question and do not reward the same developed point twice.",
            "Where a candidate carries an earlier numerical error through consistently, "
            "award later method marks when the economic reasoning remains valid.",
        ),
        (
            "Using assessment objectives",
            "Knowledge must be accurate; application must use the supplied context; "
            "analysis must show a connected chain of reasoning.",
            "Evaluation should test assumptions, scale, time period and likely effects "
            "before reaching a conclusion supported by the preceding analysis.",
        ),
        (
            "Levels-based responses",
            "Place the answer in the level that best describes it as a whole. Use the "
            "breadth, depth and consistency of the response to select a mark in that level.",
            "A balanced answer need not give equal space to every view, but its judgement "
            "must follow from the argument and evidence presented.",
        ),
        (
            "Diagrams, data and calculations",
            "Credit correctly labelled axes, curves, shifts and equilibria when they "
            "support the written answer. Do not award a diagram that contradicts it.",
            "Require working for method marks and appropriate units for a final numerical "
            "answer. Accept a different valid route to the same economic conclusion.",
        ),
        (
            "Annotation conventions",
            "Use a consistent annotation for correct knowledge, application, developed "
            "analysis and evaluation. Record where a chain of reasoning earns its final mark.",
            "Do not let the frequency of annotations determine the mark. The awarded total "
            "must follow the question-specific guidance and any stated maximum.",
        ),
        (
            "Short-answer responses",
            "Award one mark for each separate creditworthy point unless the guidance requires "
            "development. A list cannot earn an explanation mark without a valid link.",
            "Accept concise definitions that contain the essential economic meaning. Do not "
            "require the exact wording used in the indicative content.",
        ),
        (
            "Quantitative skills",
            "Check the method before the final value. Accept correct equivalent working and "
            "apply error carried forward where a later step remains economically and mathematically valid.",
            "Units, signs, direction of change and the requested degree of accuracy form part "
            "of a complete numerical answer when the question requires them.",
        ),
        (
            "Quality assurance",
            "Review totals, level placement and the treatment of alternative answers before "
            "finishing the script. Resolve any inconsistency using the stated assessment objectives.",
            "Apply the same threshold to every response. Where judgement is required, record "
            "the evidence that places the answer at the selected level and mark.",
        ),
    ]
    pages: list[Flowable] = []
    for index, (title, first, second) in enumerate(topics):
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


MARK_SCHEME_EXTENSION_PAGE_COUNTS = {
    "paper_1": 8,
    "paper_2": 11,
    "paper_3": 8,
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
        if index == count - 2:
            pages.extend(_assessment_objectives_page(paper, questions))
            continue
        if index == count - 1:
            pages.extend(_scheme_quality_page())
            continue
        question = extended[index % len(extended)]
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


def _assessment_objectives_page(
    paper: GeneratedPaper,
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    rows = [["Question", "Marks", "Primary assessment focus"]]
    for question in questions:
        focus = (
            "AO1, AO2, AO3 and AO4"
            if question.marks >= 8
            else "AO1 and AO2"
        )
        rows.append([question.number, str(question.marks), focus])
    table = Table(rows, colWidths=[45 * mm, 28 * mm, 187 * mm], repeatRows=1)
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
            f"The question marks shown total the available marks across all printed options; "
            f"candidates answer the combinations specified on the question paper. "
            f"The paper maximum is {paper.total_marks}.",
            STYLES["body"],
        ),
    ]


def _scheme_quality_page() -> list[Flowable]:
    return [
        Paragraph("Final marking checks", STYLES["heading"]),
        Spacer(1, 5 * mm),
        _box(
            "Check every attempted response, the arithmetic of each subtotal, the selected "
            "level for extended answers and the final paper total."
        ),
        Spacer(1, 6 * mm),
        Paragraph(
            "Confirm that alternative valid reasoning has been treated consistently, "
            "quantitative answers include the required working and units, and no point has "
            "received credit twice. Review any response placed at a level boundary.",
            STYLES["body"],
        ),
    ]


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
    pages.extend([[Paragraph("Section B answer continued", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(3)])
    pages.append([*_intro(section_c), *_choice_prompts(section_c)])
    pages.extend([[Paragraph("Section C answer continued", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(3)])
    pages.extend(
        [
            [
                Paragraph("EXTRA ANSWER SPACE", STYLES["centre_bold"]),
                Paragraph(
                    "Write the question number clearly in the margin.",
                    STYLES["centre"],
                ),
                AnswerLines(32),
            ],
            [
                Paragraph("BLANK PAGE", STYLES["centre_bold"]),
                Spacer(1, 8 * mm),
                Paragraph("PLEASE DO NOT WRITE ON THIS PAGE", STYLES["centre_bold"]),
            ],
            [
                Paragraph("BLANK PAGE", STYLES["centre_bold"]),
                Spacer(1, 8 * mm),
                Paragraph("PLEASE DO NOT WRITE ON THIS PAGE", STYLES["centre_bold"]),
            ],
            _question_paper_legal_page(),
        ]
    )
    assert len(pages) == 19
    return _page_sequence(pages)


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
        Spacer(1, 205 * mm),
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


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
    rows = [[Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]), str(question.marks)]]
    rows.extend([[Paragraph(f"• {point}", STYLES["small"]), ""] for point in question.mark_scheme])
    table = Table(rows, colWidths=[245 * mm, 15 * mm], repeatRows=1)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 5)]))
    return [table, Spacer(1, 4 * mm)]


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
