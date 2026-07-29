from __future__ import annotations

from typing import Any, TypeVar

from reportlab.platypus import TableStyle


TableType = TypeVar("TableType")


def themed_table_class(base: type[TableType], font_name: str) -> type[TableType]:
    """Return a Table subclass whose raw string cells use the controlled font.

    ReportLab otherwise silently draws raw table values in built-in Helvetica,
    even when every Paragraph and canvas operation uses the board font.
    """

    class ThemedTable(base):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.setStyle(
                TableStyle(
                    [("FONTNAME", (0, 0), (-1, -1), font_name)]
                )
            )

    ThemedTable.__name__ = f"{base.__name__}_{font_name.replace('-', '_')}"
    return ThemedTable
