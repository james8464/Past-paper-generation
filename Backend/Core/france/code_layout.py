"""Shared physical code-line limits, without modifying printable source."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth

from Backend.Core.fonts import register_font

CODE_LAYOUT_POLICY = "fr-nsi-v36-code-layout-v1"
CODE_FENCE_PATTERN = r"```(?:python|sql)?[ \t]*(?:\r?\n)?"
LEFT_MARGIN = 70
RIGHT_MARGIN = 54


class CodeLayoutError(ValueError):
    """An unchanged source line cannot fit the selected readable print mode."""


@dataclass(frozen=True)
class CodeLayout:
    font_name: str
    font_size: int
    content_width: float = A4[0] - LEFT_MARGIN - RIGHT_MARGIN - 12
    question_width: float = A4[0] - LEFT_MARGIN - RIGHT_MARGIN - 42

    def columns(self, width: float) -> int:
        return int(width // stringWidth("M", self.font_name, self.font_size))


def code_layout(large_print: bool) -> CodeLayout:
    if type(large_print) is not bool:
        raise ValueError("Le mode de mise en page doit être booléen")
    return CodeLayout(
        register_font("AQACourier", fallback="Courier"), 16 if large_print else 12
    )


def code_blocks(text: str) -> Iterator[str]:
    for block in re.split(CODE_FENCE_PATTERN, text)[1::2]:
        if block.strip():
            yield block.strip("\n")


def require_code_width(
    source: str,
    font_name: str,
    font_size: float,
    available_width: float,
    *,
    location: str = "code",
) -> None:
    for number, line in enumerate(source.splitlines(), 1):
        # Preserve the historical Preformatted source and its width measurement.
        width = stringWidth(line, font_name, font_size)
        if width > available_width:
            raise CodeLayoutError(
                f"Une ligne de code dépasse la largeur disponible ({location}, "
                f"ligne {number} : {width:.2f} pt > {available_width:.2f} pt). "
                "Rédiger un nouvel exercice avec des lignes plus courtes, sans "
                "modifier automatiquement le programme avant de publier le PDF."
            )
