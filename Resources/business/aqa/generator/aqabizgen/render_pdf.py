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

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
)


PAGE_WIDTH, PAGE_HEIGHT = A4
INK = colors.HexColor("#161616")
GREY = colors.HexColor("#eeeeee")


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
        Spacer(1, 8 * mm),
        _box(
            "Reward valid alternative business reasoning. Apply level descriptors "
            "holistically and credit supported judgements."
        ),
        PageBreak(),
    ]
    for section in paper.sections:
        story.extend([_banner(f"Section {section.id}"), Spacer(1, 4 * mm)])
        for option in section.options:
            for question in option.questions:
                story.extend(_scheme_block(question))
        story.append(PageBreak())
    story.pop()
    doc.build(story)


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
    pages.extend(
        [
            [
                *_intro(section_b),
                Paragraph(case.title, STYLES["option"]),
                Paragraph(case.stimulus[0], STYLES["extract"]),
                Spacer(1, 4 * mm),
                *_question_block(case.questions[0]),
                AnswerLines(7),
            ],
            [
                Paragraph(case.stimulus[1], STYLES["extract"]),
                Spacer(1, 4 * mm),
                _chart(case),
                Spacer(1, 4 * mm),
                *_question_block(case.questions[1]),
                AnswerLines(7),
            ],
            [_banner("Question 18"), *_question_block(case.questions[2]), AnswerLines(25)],
            [Paragraph("Question 18 continued", STYLES["centre_bold"]), AnswerLines(34)],
            [_banner("Question 19"), *_question_block(case.questions[3]), AnswerLines(25)],
            [_banner("Question 20"), *_question_block(case.questions[4]), AnswerLines(25)],
            [*_intro(section_c), *_choice_prompts(section_c)],
        ]
    )
    pages.extend(
        [[Paragraph("Section C answer continued", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(5)]
    )
    pages.append([*_intro(section_d), *_choice_prompts(section_d)])
    pages.extend(
        [[Paragraph("Section D answer continued", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(5)]
    )
    pages.extend(
        [[Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)] for _ in range(5)]
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
                [Spacer(1, 7 * mm), Paragraph("OR", STYLES["centre_bold"]), Spacer(1, 7 * mm)]
            )
        result.extend(_question_block(option.questions[0]))
    return result


def _mcq_block(question: GeneratedQuestion) -> list[Flowable]:
    choices = "<br/>".join(
        f"<b>{'ABCD'[index]}</b> {text}"
        for index, text in enumerate(question.choices)
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


def _question_block(question: GeneratedQuestion) -> list[Flowable]:
    return [_question_table(question), Spacer(1, 3 * mm)]


def _question_table(question: GeneratedQuestion) -> Table:
    mark_label = "mark" if question.marks == 1 else "marks"
    return Table(
        [
            [
                Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]),
                Paragraph(f"[{question.marks} {mark_label}]", STYLES["marks"]),
            ]
        ],
        colWidths=[148 * mm, 19 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


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
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
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
        String(30, 116, option.chart_title, fontName="Helvetica-Bold", fontSize=9)
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
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
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
        Spacer(1, 8 * mm),
        _box(f"Generation seed: {paper.seed}"),
    ]


def _document(path: Path, paper: GeneratedPaper, kind: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="ExamForge",
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
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(
        18 * mm, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 13 * mm
    )
    canvas.setFont("Helvetica", 7.5)
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
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName="Helvetica", fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.white),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=10.5, leading=14),
    "option": ParagraphStyle("option", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=15),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName="Helvetica", fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=9.5, leading=13, alignment=TA_RIGHT),
    "choices": ParagraphStyle("choices", parent=_base["BodyText"], fontName="Helvetica", fontSize=9.8, leading=13, leftIndent=22),
    "answer": ParagraphStyle("answer", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=9.5, leading=12, alignment=TA_RIGHT),
    "centre_bold": ParagraphStyle("centre", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, alignment=TA_CENTER),
}
