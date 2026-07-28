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
INK = colors.HexColor("#181818")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    pages = _paper_pages(paper)
    assert len(pages) == 35
    for page in pages:
        story.append(PageBreak())
        story.extend(page)
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        Spacer(1, 10 * mm),
        Paragraph("A-level Accounting", STYLES["kicker"]),
        Paragraph("Independent practice mark scheme", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box(
            "Credit valid alternative accounting treatments and workings. "
            "Apply extended-response levels holistically."
        ),
        PageBreak(),
        *aqa_front_matter_pages(
            "accounting",
            heading_style=STYLES["kicker"],
            body_style=STYLES["body"],
        ),
    ]
    for section in paper.sections:
        story.extend([_banner(f"Section {section.id}"), Spacer(1, 4 * mm)])
        for question in section.options[0].questions:
            story.extend(_scheme_block(question))
        story.append(PageBreak())
    story.pop()
    story.extend(_mark_scheme_extension_pages(paper))
    doc.build(story)


MARK_SCHEME_EXTENSION_PAGE_COUNTS = {
    "paper_1": 7,
    "paper_2": 8,
}


def _mark_scheme_extension_pages(paper: GeneratedPaper) -> list[Flowable]:
    count = MARK_SCHEME_EXTENSION_PAGE_COUNTS[paper.paper_id]
    questions = [
        question
        for section in paper.sections
        for question in section.options[0].questions
    ]
    extended = [question for question in questions if question.marks >= 6]
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
    rows = [["Indicative marking guidance", ""]]
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
            "Credit a valid alternative accounting treatment when the method is applied "
            "consistently, the workings are shown and the resulting figures follow from it.",
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
            "AO1, AO2 and AO3"
            if question.marks >= 6
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
            f"The candidate paper maximum is {paper.total_marks}. Verify each subtotal "
            "against the marks printed beside the corresponding question.",
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


def _paper_pages(paper: GeneratedPaper) -> list[list[Flowable]]:
    section_a, section_b, section_c = paper.sections
    a_option = section_a.options[0]
    pages: list[list[Flowable]] = []
    for start, stop in ((0, 2), (2, 5), (5, 8), (8, 10)):
        content: list[Flowable] = []
        if start == 0:
            content.extend(_intro(section_a))
        for question in a_option.questions[start:stop]:
            content.extend(_mcq_block(question))
        pages.append(content)
    for index, question in enumerate(a_option.questions[10:]):
        content = []
        if index == 0:
            content.extend(
                [
                    Paragraph(a_option.title, STYLES["option"]),
                    Paragraph(a_option.stimulus[0], STYLES["extract"]),
                    Spacer(1, 4 * mm),
                ]
            )
        content.extend(_question_page(question, a_option, lines=18))
        pages.append(content)
        if index == 0:
            pages.append(
                [Paragraph("Turn over for the next question", STYLES["centre_bold"])]
            )
    pages.append(
        [Paragraph("Section A answer continued", STYLES["centre_bold"]), AnswerLines(34)]
    )
    assert len(pages) == 10

    b_option = section_b.options[0]
    if paper.paper_id == "paper_1":
        for index, question in enumerate(b_option.questions):
            first = [*_intro(section_b)] if index == 0 else []
            if index == 0:
                first.extend(
                    [
                        Paragraph(b_option.title, STYLES["option"]),
                        Paragraph(b_option.stimulus[0], STYLES["extract"]),
                        Spacer(1, 3 * mm),
                    ]
                )
            first.extend(_question_page(question, b_option, lines=18))
            pages.append(first)
            pages.append(
                [
                    Paragraph(
                        f"Question {question.number} continued",
                        STYLES["centre_bold"],
                    ),
                    AnswerLines(34),
                ]
            )
    else:
        for index, question in enumerate(b_option.questions):
            content = [*_intro(section_b)] if index == 0 else []
            if index == 0:
                content.extend(
                    [
                        Paragraph(b_option.title, STYLES["option"]),
                        Paragraph(b_option.stimulus[0], STYLES["extract"]),
                        Spacer(1, 3 * mm),
                    ]
                )
            content.extend(_question_page(question, b_option, lines=18))
            pages.append(content)
    expected_before_c = 20 if paper.paper_id == "paper_1" else 18
    assert len(pages) == expected_before_c

    c_option = section_c.options[0]
    allocation = 7 if paper.paper_id == "paper_1" else 8
    for index, question in enumerate(c_option.questions):
        content: list[Flowable] = []
        if index == 0:
            content.extend(
                [
                    *_intro(section_c),
                    Paragraph(c_option.title, STYLES["option"]),
                    Paragraph(c_option.stimulus[index], STYLES["extract"]),
                    Spacer(1, 3 * mm),
                ]
            )
        else:
            content.extend(
                [
                    Paragraph(c_option.stimulus[index], STYLES["extract"]),
                    Spacer(1, 4 * mm),
                ]
            )
        content.extend(_question_page(question, c_option, lines=17))
        pages.append(content)
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
    pages.append(
        [Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)]
    )
    return pages


def _question_page(
    question: GeneratedQuestion, option: GeneratedOption, lines: int
) -> list[Flowable]:
    content: list[Flowable] = [
        _question_table(question),
        Spacer(1, 4 * mm),
    ]
    if question.kind == "calculation":
        content.extend([_accounting_table(option), Spacer(1, 4 * mm)])
    content.append(AnswerLines(lines))
    return content


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
                choices,
                Spacer(1, 6 * mm),
            ]
        )
    ]


def _question_table(question: GeneratedQuestion) -> Table:
    label = "mark" if question.marks == 1 else "marks"
    return Table(
        [[
            _question_reference(question.number),
            Paragraph(question.prompt, STYLES["body"]),
            Paragraph(f"[{question.marks} {label}]", STYLES["marks"]),
        ]],
        colWidths=[14 * mm, 134 * mm, 19 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
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


def _accounting_table(option: GeneratedOption) -> Table:
    values = option.chart_values
    rows = [
        ["Accounting information", "£000"],
        ["Revenue / activity index", f"{values[4]:.1f}"],
        ["Variable-cost index", f"{values[2]:.1f}"],
        ["Fixed-cost index", f"{values[1]:.1f}"],
        ["Comparative figure", f"{values[0]:.1f}"],
    ]
    table = Table(rows, colWidths=[110 * mm, 45 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, INK),
        ("BACKGROUND", (0, 0), (-1, 0), GREY),
        ("FONT", (0, 0), (-1, 0), FONT_BOLD),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
    rows = [[
        Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]),
        str(question.marks),
    ]]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in question.mark_scheme]
    )
    table = Table(rows, colWidths=[155 * mm, 12 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return [table, Spacer(1, 4 * mm)]


def _intro(section) -> list[Flowable]:
    return [
        _banner(f"Section {section.id}: {section.title}"),
        Spacer(1, 3 * mm),
        Paragraph(section.instructions, STYLES["instruction"]),
        Spacer(1, 4 * mm),
    ]


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Accounting", STYLES["kicker"]),
        Paragraph("Independent practice paper", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Paragraph(formatted_generation_date(), STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        Table(
            [
                ["Time allowed", "3 hours"],
                ["Maximum mark", "120"],
                ["Paper reference", paper.paper_code],
            ],
            colWidths=[45 * mm, 90 * mm],
            style=TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.6, INK),
                ("BACKGROUND", (0, 0), (0, -1), GREY),
                ("FONT", (0, 0), (0, -1), FONT_BOLD),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]),
        ),
        Spacer(1, 9 * mm),
        Paragraph("Instructions", STYLES["heading"]),
        Paragraph(
            "Answer all questions. Show all workings. You may use a calculator.",
            STYLES["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Information", STYLES["heading"]),
        Paragraph(
            "The maximum mark is 120. Marks are shown in brackets. This independently "
            "created practice paper is mapped to AQA 7127 but is not produced or "
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
            id="aqa-accounting-practice",
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
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), INK),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]),
    )


def _box(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["body"])]],
        colWidths=[150 * mm],
        style=TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, INK),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]),
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
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName=FONT, fontSize=9.0, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=12, leading=15, textColor=colors.white),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=10.5, leading=14),
    "option": ParagraphStyle("option", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11.5, leading=15),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName=FONT, fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=13, alignment=TA_RIGHT),
    "choices": ParagraphStyle("choices", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=17, leftIndent=22),
    "answer": ParagraphStyle("answer", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=12, alignment=TA_RIGHT),
    "centre_bold": ParagraphStyle("centre", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_CENTER),
}
