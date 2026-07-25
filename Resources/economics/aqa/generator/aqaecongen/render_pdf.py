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
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.exam_blueprints import GeneratedOption, GeneratedPaper, GeneratedQuestion

BLACK = colors.HexColor("#171717")
GREY = colors.HexColor("#ececec")
MID_GREY = colors.HexColor("#666666")
PAGE_WIDTH, PAGE_HEIGHT = A4


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
                story.extend(_stimulus_page(option))
                story.extend(
                    [
                        PageBreak(),
                        _section_banner(f"Section {section.id}: Questions on {option.title}"),
                        Spacer(1, 5 * mm),
                        *_option_questions(option),
                    ]
                )
        elif paper.paper_id in {"paper_1", "paper_2"}:
            for index, option in enumerate(section.options):
                if index:
                    story.extend([PageBreak(), *_section_intro(section.id, section.title, section.instructions)])
                story.extend(_written_option(option))
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
    story: list[Flowable] = [
        Spacer(1, 14 * mm),
        Paragraph("A-level Economics", STYLES["cover_kicker"]),
        Paragraph("Practice mark scheme", STYLES["cover_title"]),
        Spacer(1, 6 * mm),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["cover_subtitle"]),
        Spacer(1, 10 * mm),
        _info_box(
            "This is an independently created practice mark scheme. Reward valid alternative "
            "economic arguments. For extended responses, assess the quality of knowledge, "
            "application, analysis and evaluation holistically."
        ),
        PageBreak(),
    ]
    for section in paper.sections:
        story.extend([_section_banner(f"Section {section.id}"), Spacer(1, 4 * mm)])
        for option in section.options:
            if paper.paper_id != "paper_3" or section.id != "A":
                story.append(Paragraph(option.title, STYLES["option_title"]))
            for question in option.questions:
                story.extend(_mark_scheme_question(question))
        story.append(PageBreak())
    if isinstance(story[-1], PageBreak):
        story.pop()
    doc.build(story)


def _document(path: Path, paper: GeneratedPaper, document_type: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=15 * mm,
        title=f"{paper.paper_code} {paper.title} — {document_type}",
        author="ExamForge",
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
    hours, minutes = divmod(paper.duration_minutes, 60)
    duration = f"{hours} hours" if not minutes else f"{hours} hours {minutes} minutes"
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Economics", STYLES["cover_kicker"]),
        Paragraph("Independent practice paper", STYLES["cover_title"]),
        Spacer(1, 5 * mm),
        Paragraph(f"Paper {paper.paper_id[-1]}: {paper.title}", STYLES["cover_subtitle"]),
        Spacer(1, 4 * mm),
        Table(
            [
                ["Paper reference", paper.paper_code],
                ["Time allowed", duration],
                ["Maximum mark", str(paper.total_marks)],
            ],
            colWidths=[45 * mm, 90 * mm],
            style=TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 11),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 11),
                    ("GRID", (0, 0), (-1, -1), 0.7, BLACK),
                    ("BACKGROUND", (0, 0), (0, -1), GREY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        ),
        Spacer(1, 10 * mm),
        Paragraph("Materials", STYLES["heading"]),
        Paragraph(
            "You may use a calculator. Write your answers in a separate answer booklet.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Instructions", STYLES["heading"]),
        Paragraph(
            "Answer the questions specified in each section. Show calculations and use diagrams "
            "where appropriate. The marks for questions are shown in brackets.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Information", STYLES["heading"]),
        Paragraph(
            f"The maximum mark is {paper.total_marks}. This paper is mapped to AQA 7136 but is "
            "not produced or endorsed by AQA. Names, figures and cases are fictional.",
            STYLES["body"],
        ),
        Spacer(1, 10 * mm),
        _info_box(f"Generation seed: {paper.seed}"),
    ]


def _written_option(option: GeneratedOption) -> list[Flowable]:
    flowables: list[Flowable] = [
        Paragraph(option.title, STYLES["option_title"]),
        Spacer(1, 2 * mm),
    ]
    for paragraph in option.stimulus:
        flowables.extend([Paragraph(paragraph, STYLES["extract"]), Spacer(1, 2 * mm)])
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
    for page_index, question_count in enumerate([2] * 10 + [1] * 10):
        flowables.append(PageBreak())
        if page_index == 0:
            flowables.extend(
                _section_intro(mcq_section.id, mcq_section.title, mcq_section.instructions)
            )
        for option in mcq_section.options[cursor : cursor + question_count]:
            flowables.extend(_mcq_block(option))
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
        _section_banner(f"Section {section_id}: {title}"),
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


def _mcq_block(option: GeneratedOption) -> list[Flowable]:
    question = option.questions[0]
    letters = "ABCD"
    choices = "<br/>".join(
        f"<b>{letters[index]}</b> {value}" for index, value in enumerate(question.choices)
    )
    return [
        KeepTogether(
            [
                _question_table(question),
                Spacer(1, 2 * mm),
                Paragraph(choices, STYLES["mcq_choices"]),
                Spacer(1, 2 * mm),
                Paragraph("Answer: [  ] A  [  ] B  [  ] C  [  ] D", STYLES["mcq_answer"]),
                Spacer(1, 5 * mm),
            ]
        )
    ]


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    return [
        _question_table(question),
        Spacer(1, 4 * mm),
    ]


def _question_table(question: GeneratedQuestion) -> Table:
    return Table(
        [
            [
                Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["question"]),
                Paragraph(f"[{question.marks}]", STYLES["marks"]),
            ]
        ],
        colWidths=[157 * mm, 12 * mm],
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
    drawing.add(String(32, 138, title, fontName="Helvetica-Bold", fontSize=9))
    drawing.add(Line(x0, y0, x0, y0 + height, strokeWidth=0.8))
    drawing.add(Line(x0, y0, x0 + width, y0, strokeWidth=0.8))
    low, high = min(values), max(values)
    span = max(1.0, high - low)
    points: list[float] = []
    for index, value in enumerate(values):
        x = x0 + index * width / max(1, len(values) - 1)
        y = y0 + 8 + (value - low) / span * (height - 16)
        points.extend([x, y])
        drawing.add(String(x - 10, y0 - 14, labels[index], fontSize=7))
        drawing.add(Rect(x - 2, y - 2, 4, 4, fillColor=BLACK, strokeColor=BLACK))
        drawing.add(String(x + 4, y + 3, f"{value:.1f}", fontSize=7))
    drawing.add(PolyLine(points, strokeColor=BLACK, strokeWidth=1.2))
    return drawing


def _section_banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["section"])]],
        colWidths=[169 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLACK),
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
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.setLineWidth(0.45)
    canvas.line(16 * mm, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 12 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(16 * mm, PAGE_HEIGHT - 9 * mm, f"{paper_code} · {document_type}")
    canvas.drawRightString(PAGE_WIDTH - 17 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


class AnswerLines(Flowable):
    def __init__(self, line_count: int) -> None:
        self.line_count = line_count
        super().__init__()
        self.width = 169 * mm
        self.height = line_count * 6.2 * mm

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#b8b8b8"))
        self.canv.setLineWidth(0.35)
        for index in range(self.line_count):
            y = self.height - ((index + 1) * 6.2 * mm)
            self.canv.line(0, y, self.width, y)


_sample = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle(
        "Body", parent=_sample["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14
    ),
    "heading": ParagraphStyle(
        "Heading", parent=_sample["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14
    ),
    "cover_kicker": ParagraphStyle(
        "CoverKicker",
        parent=_sample["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
    ),
    "cover_title": ParagraphStyle(
        "CoverTitle",
        parent=_sample["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        spaceAfter=6,
    ),
    "cover_subtitle": ParagraphStyle(
        "CoverSubtitle",
        parent=_sample["Heading2"],
        fontName="Helvetica",
        fontSize=14,
        leading=18,
    ),
    "section": ParagraphStyle(
        "Section",
        parent=_sample["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.white,
    ),
    "instruction": ParagraphStyle(
        "Instruction",
        parent=_sample["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
    ),
    "option_title": ParagraphStyle(
        "OptionTitle",
        parent=_sample["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=3,
    ),
    "extract": ParagraphStyle(
        "Extract",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12.5,
        borderWidth=0.4,
        borderColor=colors.HexColor("#aaaaaa"),
        borderPadding=5,
    ),
    "question": ParagraphStyle(
        "Question",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
    ),
    "marks": ParagraphStyle(
        "Marks",
        parent=_sample["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT,
    ),
    "mcq_choices": ParagraphStyle(
        "MCQChoices",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        leftIndent=24,
    ),
    "mcq_answer": ParagraphStyle(
        "MCQAnswer",
        parent=_sample["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    ),
    "scheme": ParagraphStyle(
        "Scheme",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
    ),
    "source_extract": ParagraphStyle(
        "SourceExtract",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
    ),
    "continuation": ParagraphStyle(
        "Continuation",
        parent=_sample["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    ),
    "centred_note": ParagraphStyle(
        "CentredNote",
        parent=_sample["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    ),
}
