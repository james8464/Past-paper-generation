from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Protocol

from reportlab.pdfbase import pdfmetrics

from Backend.Core.document_dsl.model import BoardProfile, Length, Size


class Component(Protocol):
    keep_together: bool

    def measure(self, profile: BoardProfile, available: Size) -> Size: ...

    def split(
        self,
        profile: BoardProfile,
        available: Size,
    ) -> tuple[Component | None, Component | None]: ...


def _text_lines(text: str, profile: BoardProfile, width: float) -> int:
    font = profile.fonts.body
    words = text.split()
    if not words:
        return 1
    lines = 1
    current = ""
    for word in words:
        word_width = pdfmetrics.stringWidth(word, font.name, font.size.pt)
        if word_width > width:
            if current:
                lines += 1
                current = ""
            lines += max(1, math.ceil(word_width / width)) - 1
            continue
        candidate = word if not current else f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font.name, font.size.pt) <= width:
            current = candidate
        else:
            lines += 1
            current = word
    return lines


class BaseComponent:
    keep_together = True

    def split(self, profile: BoardProfile, available: Size):  # type: ignore[no-untyped-def]
        del profile, available
        return None, self


@dataclass(frozen=True)
class Cover(BaseComponent):
    title: str
    subtitle: str
    code: str
    board_label: str = "PAPER CREATOR"
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile
        return Size(
            available.width, Length(min(available.height.pt, Length.mm(105).pt))
        )


@dataclass(frozen=True)
class InstructionBlock(BaseComponent):
    heading: str
    items: tuple[str, ...]
    minimum_lines_after_heading: int = 2
    keep_together: bool = True

    @property
    def minimum_fragment_height(self) -> Length:
        return Length(12.4 * (1 + self.minimum_lines_after_heading) + 6)

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        lines = 1 + sum(
            _text_lines(item, profile, available.width.pt - 12) for item in self.items
        )
        return Size(available.width, Length(lines * profile.fonts.body.leading.pt + 8))

    def split(self, profile: BoardProfile, available: Size):  # type: ignore[no-untyped-def]
        capacity = int((available.height.pt - 8) // profile.fonts.body.leading.pt) - 1
        if capacity < self.minimum_lines_after_heading or len(self.items) < 2:
            return None, self
        used: list[str] = []
        lines = 0
        for item in self.items:
            item_lines = _text_lines(item, profile, available.width.pt - 12)
            if used and lines + item_lines > capacity:
                break
            used.append(item)
            lines += item_lines
        if not used or len(used) == len(self.items):
            return None, self
        return replace(self, items=tuple(used)), replace(
            self, items=self.items[len(used) :]
        )


@dataclass(frozen=True)
class QuestionBlock(BaseComponent):
    number: str
    prompt: str
    marks: int
    allow_split: bool = True
    keep_together: bool = True

    def __post_init__(self) -> None:
        if self.marks < 0:
            raise ValueError("marks cannot be negative")

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        lines = _text_lines(self.prompt, profile, max(20, available.width.pt - 115))
        return Size(
            available.width, Length(max(28, lines * profile.fonts.body.leading.pt + 10))
        )

    def split(self, profile: BoardProfile, available: Size):  # type: ignore[no-untyped-def]
        if not self.allow_split:
            return None, self
        words = self.prompt.split()
        if len(words) < 8:
            return None, self
        target_lines = max(
            2, int((available.height.pt - 10) // profile.fonts.body.leading.pt)
        )
        if target_lines < 2:
            return None, self
        used: list[str] = []
        for word in words:
            candidate = " ".join((*used, word))
            if (
                _text_lines(candidate, profile, max(20, available.width.pt - 115))
                > target_lines
            ):
                break
            used.append(word)
        if not used or len(used) == len(words):
            return None, self
        first = replace(self, prompt=" ".join(used), marks=0)
        rest = replace(
            self, number=f"{self.number} continued", prompt=" ".join(words[len(used) :])
        )
        return first, rest


@dataclass(frozen=True)
class AnswerSpace(BaseComponent):
    lines: int
    line_height: Length | None = None
    minimum_fragment_lines: int = 3
    keep_together: bool = False

    def __post_init__(self) -> None:
        if self.lines < 1:
            raise ValueError("answer space must contain at least one line")

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        height = self.line_height or profile.answer_line_height
        return Size(available.width, Length(self.lines * height.pt))

    def split(self, profile: BoardProfile, available: Size):  # type: ignore[no-untyped-def]
        height = self.line_height or profile.answer_line_height
        capacity = int(available.height.pt // height.pt)
        if capacity < self.minimum_fragment_lines:
            return None, self
        remaining = self.lines - capacity
        if remaining and remaining < self.minimum_fragment_lines:
            capacity -= self.minimum_fragment_lines - remaining
            remaining = self.lines - capacity
        if capacity < self.minimum_fragment_lines or capacity >= self.lines:
            return None, self
        return replace(self, lines=capacity), replace(self, lines=remaining)


@dataclass(frozen=True)
class MarkBox(BaseComponent):
    marks: int
    width: Length = field(default_factory=lambda: Length.mm(13))
    height: Length = field(default_factory=lambda: Length.mm(8))
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile, available
        return Size(self.width, self.height)


@dataclass(frozen=True)
class RuleSet(AnswerSpace):
    pass


@dataclass(frozen=True)
class Table(BaseComponent):
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    row_height: Length = field(default_factory=lambda: Length.mm(8))
    keep_together: bool = True

    def __post_init__(self) -> None:
        if not self.headers or any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("table rows must match non-empty headers")

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        column_widths = tuple(
            available.width.pt * weight for weight in self.column_weights()
        )
        maximum_lines = max(
            _text_lines(
                str(value),
                profile,
                max(20, column_widths[column_index] - 8),
            )
            for row in (self.headers, *self.rows)
            for column_index, value in enumerate(row)
        )
        effective_row_height = max(
            self.row_height.pt,
            maximum_lines * profile.fonts.small.leading.pt + 6,
        )
        return Size(
            available.width,
            Length((1 + len(self.rows)) * effective_row_height),
        )

    def column_weights(self) -> tuple[float, ...]:
        weight = 1 / len(self.headers)
        return tuple(weight for _ in self.headers)


@dataclass(frozen=True)
class Graph(BaseComponent):
    x_label: str
    y_label: str
    series: tuple[tuple[float, float], ...]
    height: Length = field(default_factory=lambda: Length.mm(70))
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile
        return Size(available.width, self.height)


@dataclass(frozen=True)
class Diagram(BaseComponent):
    kind: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[int, int], ...]
    height: Length = field(default_factory=lambda: Length.mm(55))
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile
        return Size(available.width, self.height)


@dataclass(frozen=True)
class SourcePanel(BaseComponent):
    title: str
    body: str
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        lines = _text_lines(self.body, profile, available.width.pt - 20)
        return Size(
            available.width, Length((lines + 2) * profile.fonts.body.leading.pt + 12)
        )


@dataclass(frozen=True)
class ContinuationPage(BaseComponent):
    heading: str = "Extra space"
    lines: int = 24
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile
        return available


@dataclass(frozen=True)
class BlankPage(BaseComponent):
    message: str = "BLANK PAGE"
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        del profile
        return available


@dataclass(frozen=True)
class SchemeGrid(Table):
    def column_weights(self) -> tuple[float, ...]:
        if len(self.headers) == 3:
            return (0.14, 0.74, 0.12)
        return super().column_weights()


@dataclass(frozen=True)
class LevelTable(BaseComponent):
    levels: tuple[tuple[str, str, str], ...]
    row_height: Length = field(default_factory=lambda: Length.mm(12))
    keep_together: bool = True

    def measure(self, profile: BoardProfile, available: Size) -> Size:
        column_widths = tuple(
            available.width.pt * weight for weight in self.column_weights()
        )
        maximum_lines = max(
            _text_lines(str(value), profile, max(20, column_widths[index] - 8))
            for row in (("Level", "Descriptor", "Marks"), *self.levels)
            for index, value in enumerate(row)
        )
        effective_row_height = max(
            self.row_height.pt,
            maximum_lines * profile.fonts.small.leading.pt + 6,
        )
        return Size(
            available.width, Length((1 + len(self.levels)) * effective_row_height)
        )

    def column_weights(self) -> tuple[float, float, float]:
        return (0.14, 0.72, 0.14)
