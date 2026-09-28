from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, TableStyle


def themed_table_class[TableType](
    base: type[TableType], font_name: str
) -> type[TableType]:
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


class AQAAnswerLines(AnswerLineFlowable):
    def __init__(self, count: int) -> None:
        super().__init__(
            count,
            spacing_mm=6,
            colour="#b5b5b5",
            line_width=0.35,
            dashed=False,
        )


class AQACompactAnswerLines(AnswerLineFlowable):
    def __init__(self, count: int) -> None:
        super().__init__(count, width_mm=165, spacing_mm=6.2, colour="#666666")


class OCRAnswerLines(AnswerLineFlowable):
    """OCR dotted writing rules inside the existing allocated answer area.

    Reviewed 2024 H446/02 p29 and H460/01 p17 use Arial 11 full stops,
    #231f20 ink and 26.004pt baseline pitch, not pale dashed vector strokes.
    Legacy count/spacing still determines the area, so matching the printed
    ruling pitch does not move questions or create extra pages.
    """

    def __init__(self, count: int, *, spacing_mm: float = 6.0, width_mm: float = 167) -> None:
        super().__init__(count, width_mm=width_mm, spacing_mm=spacing_mm, colour="#231f20", dashed=False)

    def draw(self) -> None:
        from reportlab.pdfbase.pdfmetrics import stringWidth

        from Backend.Core.fonts import register_fonts

        register_fonts("AQAArial", "AQAArial-Bold")
        self.canv.setFont("AQAArial", 11)
        self.canv.setFillColor(self.colour)
        dots = "." * int(self.width / stringWidth(".", "AQAArial", 11))
        pitch = 26.0
        rows = max(1, int(self.height / pitch))
        first_offset = min(self.height, pitch)
        for index in range(rows):
            self.canv.drawString(0, self.height - first_offset - index * pitch, dots)


class OCRComputerScienceAnswerLines(OCRAnswerLines):
    def __init__(self, count: int) -> None:
        super().__init__(count, width_mm=165, spacing_mm=4.7)
