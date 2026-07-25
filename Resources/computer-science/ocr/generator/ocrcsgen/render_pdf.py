from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
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


PAGE_WIDTH, PAGE_HEIGHT = A4
INK = colors.HexColor("#161616")
GREY = colors.HexColor("#eeeeee")


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
                section.options[0],
                include_section_page=not (
                    paper.paper_id == "paper_2" and section_index == 8
                ),
            )
        )
    if paper.paper_id == "paper_1":
        story.extend(_additional_pages(2))
    else:
        story.extend(_continued_pages(3, "Question 9 answer continued"))
        story.extend(_additional_pages(1))
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = [
        Spacer(1, 12 * mm),
        Paragraph("A-level Computer Science", STYLES["kicker"]),
        Paragraph("Independent practice mark scheme", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
        Spacer(1, 8 * mm),
        _box(
            "Award valid technical alternatives. Apply level descriptors "
            "holistically to extended responses."
        ),
        PageBreak(),
    ]
    for section in paper.sections:
        story.extend(
            [
                _banner(section.title),
                Spacer(1, 4 * mm),
            ]
        )
        for question in section.options[0].questions:
            story.extend(_scheme_block(question))
        story.append(PageBreak())
    story.pop()
    doc.build(story)


def _question_group_pages(
    option: GeneratedOption, *, include_section_page: bool
) -> list[Flowable]:
    chunks: list[list[GeneratedQuestion]] = []
    pending: list[GeneratedQuestion] = []
    for question in option.questions:
        if question.marks >= 6:
            if pending:
                chunks.append(pending)
                pending = []
            chunks.append([question])
        else:
            pending.append(question)
            if len(pending) == 2:
                chunks.append(pending)
                pending = []
    if pending:
        chunks.append(pending)

    result: list[Flowable] = []
    for chunk_index, questions in enumerate(chunks):
        result.append(PageBreak())
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
        AnswerLines(line_count),
        Spacer(1, 4 * mm),
    ]


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


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
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


def _continued_pages(count: int, title: str) -> list[Flowable]:
    result: list[Flowable] = []
    for _ in range(count):
        result.extend(
            [PageBreak(), Paragraph(title, STYLES["centre_bold"]), AnswerLines(34)]
        )
    return result


def _additional_pages(count: int) -> list[Flowable]:
    return _continued_pages(count, "Additional page, if required")


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return [
        Spacer(1, 10 * mm),
        Paragraph("A-level Computer Science", STYLES["kicker"]),
        Paragraph("Independent practice paper", STYLES["title"]),
        Paragraph(f"{paper.paper_code} · {paper.title}", STYLES["subtitle"]),
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
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
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
        Spacer(1, 8 * mm),
        _box(f"Generation seed: {paper.seed}"),
    ]


def _document(
    path: Path, paper: GeneratedPaper, kind: str
) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="ExamForge",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(
        PageTemplate(
            id="ocr-cs-practice",
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
        20 * mm, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 13 * mm
    )
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(20 * mm, PAGE_HEIGHT - 10 * mm, f"{code} · {kind}")
    canvas.drawRightString(PAGE_WIDTH - 17 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["banner"])]],
        colWidths=[165 * mm],
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
        self.width = 165 * mm
        self.height = count * 4.7 * mm
        self.count = count

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#b5b5b5"))
        self.canv.setLineWidth(0.35)
        for index in range(self.count):
            y = self.height - (index + 1) * 4.7 * mm
            self.canv.line(0, y, self.width, y)


_base = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12),
    "small_bold": ParagraphStyle("small-bold", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=9.2, leading=12),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName="Helvetica", fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.white),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=10.5, leading=14),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName="Helvetica", fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, alignment=TA_RIGHT),
    "code": ParagraphStyle("code", parent=_base["Code"], fontName="Courier", fontSize=8.8, leading=11, backColor=colors.HexColor("#f4f4f4"), borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "centre": ParagraphStyle("centre", parent=_base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14, alignment=TA_CENTER),
    "centre_bold": ParagraphStyle("centre-bold", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, alignment=TA_CENTER),
}
