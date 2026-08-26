from __future__ import annotations

from typing import Any, TypeVar

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, TableStyle

TableType = TypeVar("TableType")


def themed_table_class(base: type[TableType], font_name: str) -> type[TableType]:
    """Return a Table subclass whose raw string cells use the controlled font.

    ReportLab otherwise silently draws raw table values in built-in Helvetica,
    even when every Paragraph and canvas operation uses the board font.
    """

    class ThemedTable(base):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name)]))

    ThemedTable.__name__ = f"{base.__name__}_{font_name.replace('-', '_')}"
    return ThemedTable


class AnswerLineFlowable(Flowable):
    """Shared, measured answer-line primitive used by every board renderer."""

    def __init__(
        self,
        count: int,
        *,
        width_mm: float = 167,
        spacing_mm: float = 6,
        colour: str = "#777777",
        line_width: float = 0.5,
        dashed: bool = True,
    ) -> None:
        if count < 1:
            raise ValueError("answer lines require a positive count")
        if spacing_mm <= 0 or width_mm <= 0:
            raise ValueError("answer-line geometry must be positive")
        super().__init__()
        self.count = count
        self.line_count = count
        self.spacing = spacing_mm * mm
        self.width = width_mm * mm
        self.height = count * self.spacing
        self.colour = colors.HexColor(colour)
        self.rule_width = line_width
        self.dashed = dashed

    def draw(self) -> None:
        self.canv.setStrokeColor(self.colour)
        self.canv.setLineWidth(self.rule_width)
        if self.dashed:
            self.canv.setDash(1, 1.7)
        for index in range(self.count):
            y = self.height - (index + 1) * self.spacing
            self.canv.line(0, y, self.width, y)
        if self.dashed:
            self.canv.setDash()
