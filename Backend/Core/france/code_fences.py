"""Recognise standalone code delimiters without changing their source contents."""

import re
from dataclasses import dataclass


class CodeFenceError(ValueError):
    """A real opening delimiter has no matching standalone closing line."""


@dataclass(frozen=True)
class FencedPart:
    text: str
    language: str | None = None
    closed: bool = True


_DELIMITER = re.compile(r"[ \t]*```(?P<language>python|sql)?[ \t]*(?:\r?\n)?", re.I)


def fenced_parts(text: str, *, require_closed: bool = True) -> list[FencedPart]:
    parts = []
    opening = None
    prose_start = offset = 0
    for line in text.splitlines(keepends=True):
        match = _DELIMITER.fullmatch(line)
        if opening is None:
            if match:
                parts.append(FencedPart(text[prose_start:offset]))
                opening = (offset + len(line), (match["language"] or "").lower())
        elif match and match["language"] is None:
            start, language = opening
            parts.append(FencedPart(text[start:offset], language))
            prose_start = offset + len(line)
            opening = None
        offset += len(line)
    if opening is not None:
        if require_closed:
            raise CodeFenceError(
                "Un bloc de code ne possède pas de délimiteur final sur sa propre ligne."
            )
        start, language = opening
        parts.append(FencedPart(text[start:], language, closed=False))
    else:
        parts.append(FencedPart(text[prose_start:]))
    return parts


def printed_text(text: str) -> str:
    return "".join(part.text for part in fenced_parts(text))
