"""Use the same font metrics and line breaks for measurement and drawing."""

import math

from reportlab.pdfbase import pdfmetrics


def wrap_text(text: str, *, font: str, size: float, width: float) -> tuple[str, ...]:
    if not math.isfinite(width) or width <= 0:
        raise ValueError("text width must be finite and positive")
    if not math.isfinite(size) or size <= 0:
        raise ValueError("text size must be finite and positive")

    lines: list[str] = []
    for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if pdfmetrics.stringWidth(candidate, font, size) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            while pdfmetrics.stringWidth(word, font, size) > width:
                # Find the longest fitting prefix without discarding any token text.
                lower, upper = 0, len(word)
                while lower < upper:
                    midpoint = (lower + upper + 1) // 2
                    if pdfmetrics.stringWidth(word[:midpoint], font, size) <= width:
                        lower = midpoint
                    else:
                        upper = midpoint - 1
                if lower == 0:
                    raise ValueError("a text glyph cannot fit the available width")
                lines.append(word[:lower])
                word = word[lower:]
            current = word
        lines.append(current)
    return tuple(lines)
