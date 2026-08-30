from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle


class QuestionHeaderData(Protocol):
    number: str
    prompt: str
    marks: int


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
