from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from reportlab.graphics.shapes import Drawing, Ellipse, Rect
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer, Table, TableStyle


class QuestionHeaderData(Protocol):
    number: str
    prompt: str
    marks: int


class SectionHeaderData(Protocol):
    id: str
    instructions: str


def page_sequence(pages: Iterable[Sequence[Flowable]]) -> list[Flowable]:
    """Flatten explicit pages while preserving the leading-break contract."""

    result: list[Flowable] = []
    for page in pages:
        result.append(PageBreak())
        result.extend(page)
    return result


def aqa_section_intro(
    section: SectionHeaderData,
    *,
    styles: Mapping[str, ParagraphStyle],
    ink: Color,
    table_class: type[Table] = Table,
) -> list[Flowable]:
    """Build the measured AQA section heading shared by AQA families."""

    return [
        table_class(
            [
                [Paragraph(f"<b>Section {section.id}</b>", styles["centre_bold"])],
                [Paragraph(section.instructions, styles["instruction"])],
            ],
            colWidths=[167 * mm],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, -1), (-1, -1), 0.65, ink),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 4 * mm),
    ]


def independent_practice_page(
    *,
    styles: Mapping[str, ParagraphStyle],
) -> list[Flowable]:
    """Return the neutral-branding page shared by AQA mark schemes."""

    return [
        Spacer(1, 205 * mm),
        Paragraph("Independent practice material", styles["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Created by Paper Creator for private revision. This mark scheme is not "
            "produced, endorsed or approved by AQA or any examination board.",
            styles["small"],
        ),
    ]


def aqa_lozenge(ink: Color) -> Drawing:
    """Return the measured AQA option-selection lozenge."""

    drawing = Drawing(25, 15)
    drawing.add(Rect(1, 1, 22, 13, strokeColor=ink, fillColor=None, strokeWidth=0.7))
    drawing.add(
        Ellipse(12, 7.5, 4, 2.2, strokeColor=ink, fillColor=None, strokeWidth=0.6)
    )
    return drawing


def flowable_question_block(
    question: QuestionHeaderData,
    *,
    question_table: Callable[[QuestionHeaderData], Flowable],
    spacing_mm: float = 4.0,
) -> list[Flowable]:
    """Pair a family-profiled question header with measured trailing space."""

    return [question_table(question), Spacer(1, spacing_mm * mm)]


@dataclass(frozen=True)
class AQAQuestionHeaderFactory:
    """Measured AQA question-number, prompt, and tariff flowables."""

    body_style: ParagraphStyle
    marks_style: ParagraphStyle
    bold_font: str
    ink: Color
    vertical_padding: float | None = None
    table_class: type[Table] = Table

    def question_table(self, question: QuestionHeaderData) -> Table:
        mark_label = "mark" if question.marks == 1 else "marks"
        commands: list[tuple[object, ...]] = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
        if self.vertical_padding is not None:
            commands.extend(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), self.vertical_padding),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), self.vertical_padding),
                ]
            )
        return self.table_class(
            [
                [
                    self.question_reference(question.number),
                    Paragraph(question.prompt, self.body_style),
                    Paragraph(f"[{question.marks} {mark_label}]", self.marks_style),
                ]
            ],
            colWidths=[14 * mm, 134 * mm, 19 * mm],
            style=TableStyle(commands),
        )

    def question_reference(self, number: str) -> Table:
        compact = "".join(character for character in number if character.isdigit())
        cells = list(compact.zfill(2)) if len(compact) <= 2 else [number]
        return self.table_class(
            [cells],
            colWidths=[5.5 * mm] * len(cells),
            rowHeights=[5.5 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.55, self.ink),
                    ("FONT", (0, 0), (-1, -1), self.bold_font, 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )


@dataclass(frozen=True)
class OCRQuestionHeaderFactory:
    """Measured OCR question-number, prompt, and tariff flowables."""

    body_style: ParagraphStyle
    marks_style: ParagraphStyle
    extended_response_threshold: int | None = None
    table_class: type[Table] = Table

    def question_table(
        self,
        question: QuestionHeaderData,
        *,
        show_marks: bool = True,
    ) -> Table:
        display_number = question.number
        if (
            self.extended_response_threshold is not None
            and question.marks >= self.extended_response_threshold
        ):
            display_number = f"{display_number}*"
        return self.table_class(
            [
                [
                    Paragraph(
                        f"<b>{display_number}</b> {question.prompt}",
                        self.body_style,
                    ),
                    Paragraph(
                        f"[{question.marks}]" if show_marks else "",
                        self.marks_style,
                    ),
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


@dataclass(frozen=True)
class SingleCellPanelFactory:
    """Create measured section banners and information panels."""

    paragraph_style: ParagraphStyle
    width: float
    background: Color
    padding: float | None = None
    horizontal_padding: float | None = None
    vertical_padding: float | None = None
    border_width: float | None = None
    border_color: Color | None = None
    table_class: type[Table] = Table

    def panel(self, text: str) -> Table:
        commands: list[tuple[object, ...]] = [
            ("BACKGROUND", (0, 0), (-1, -1), self.background)
        ]
        if self.padding is not None:
            commands.append(("PADDING", (0, 0), (-1, -1), self.padding))
        if self.horizontal_padding is not None:
            commands.extend(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), self.horizontal_padding),
                    ("RIGHTPADDING", (0, 0), (-1, -1), self.horizontal_padding),
                ]
            )
        if self.vertical_padding is not None:
            commands.extend(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), self.vertical_padding),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), self.vertical_padding),
                ]
            )
        if self.border_width is not None and self.border_color is not None:
            commands.append(
                ("BOX", (0, 0), (-1, -1), self.border_width, self.border_color)
            )
        return self.table_class(
            [[Paragraph(text, self.paragraph_style)]],
            colWidths=[self.width],
            style=TableStyle(commands),
        )
