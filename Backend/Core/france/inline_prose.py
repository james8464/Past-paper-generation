"""Narrow display-only inline grammar shared by current V36 PDF checks.

No HTML is interpreted except exact balanced single-line underline delimiters.
Single backticks mark opaque inline code in body typography, not fenced code.
Malformed/crossed inline syntax remains literal; raw model values never change.
"""

from xml.sax.saxutils import escape

from Backend.Core.france.code_fences import fenced_parts


def _tag_end(line: str, start: int) -> int:
    """Skip unknown tag-looking text, including delimiters inside attributes."""
    quote = ""
    for index in range(start + 1, len(line)):
        value = line[index]
        if quote:
            if value == quote:
                quote = ""
        elif value in {"'", '"'}:
            quote = value
        elif value == ">":
            return index + 1
    return len(line)


def _single_backtick_end(line: str, start: int) -> int | None:
    index = start + 1
    while index < len(line):
        found = line.find("`", index)
        if found < 0:
            return None
        end = found + 1
        while end < len(line) and line[end] == "`":
            end += 1
        if end == found + 1:
            return found
        index = end
    return None


def _line_parts(line: str) -> list[tuple[str, bool]]:
    parts: list[tuple[str, bool]] = []
    literal: list[str] = []
    underlined = False
    index = 0

    def flush() -> None:
        if literal:
            parts.append(("".join(literal), underlined))
            literal.clear()

    while index < len(line):
        if line.startswith("<u>", index):
            if underlined:
                return [(line, False)]
            flush()
            underlined = True
            index += 3
        elif line.startswith("</u>", index):
            if not underlined or not literal:
                return [(line, False)]
            flush()
            underlined = False
            index += 4
        elif line[index] == "`":
            end = index + 1
            while end < len(line) and line[end] == "`":
                end += 1
            if end > index + 1:
                literal.append(line[index:end])
                index = end
                continue
            # Nesting/crossing with underline is deliberately unsupported.
            close = _single_backtick_end(line, index)
            if underlined or close is None:
                return [(line, False)]
            flush()
            parts.append((line[index + 1 : close], False))
            index = close + 1
        elif (
            line[index] == "<"
            and index + 1 < len(line)
            and (line[index + 1].isalpha() or line[index + 1] in {"/", "!", "?"})
        ):
            end = _tag_end(line, index)
            literal.append(line[index:end])
            index = end
        else:
            literal.append(line[index])
            index += 1
    if underlined:
        return [(line, False)]
    flush()
    return parts


def _unfenced_parts(text: str) -> list[tuple[str, bool]]:
    result = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        result.extend(_line_parts(body))
        result.append((line[len(body) :], False))
    return result


def _parts(text: str) -> list[tuple[str, bool]]:
    result = []
    for index, part in enumerate(
        fenced_parts(text, require_closed=False, include_delimiters=True)
    ):
        # Direct prose fields (notably credits and scope) retain delimiters as
        # literal text. Unsupported and unclosed fences are equally opaque.
        if index % 2:
            result.append((part.text, False))
        else:
            result.extend(_unfenced_parts(part.text))
    return result


def inline_text(text: str) -> str:
    """Visible prose text; entities and complete fenced spans stay literal."""
    return "".join(value for value, _ in _parts(text))


def inline_markup(text: str) -> str:
    """Escaped ReportLab prose with only fixed underline tags enabled."""
    return "".join(
        f"<u>{escape(value)}</u>" if underline else escape(value)
        for value, underline in _parts(text)
    ).replace("\n", "<br/>")


def printed_prose(text: str) -> str:
    """Normalise only unfenced prose; retain every fenced listing byte."""
    return "".join(
        # The parser retains empty segments and alternates prose/fence/prose.
        # Unsupported fences have language=None too, but remain opaque here.
        inline_text(part.text) if index % 2 == 0 else part.text
        for index, part in enumerate(fenced_parts(text))
    )
