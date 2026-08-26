from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True, order=True)
class Length:
    """A measured distance stored in PDF points."""

    pt: float

    def __post_init__(self) -> None:
        if self.pt < 0:
            raise ValueError("length cannot be negative")

    @classmethod
    def mm(cls, value: float) -> Length:
        return cls(value * 72.0 / 25.4)


@dataclass(frozen=True)
class Size:
    width: Length
    height: Length


@dataclass(frozen=True)
class Frame:
    x: Length
    y: Length
    width: Length
    height: Length

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)


@dataclass(frozen=True)
class FontToken:
    name: str
    size: Length
    leading: Length


@dataclass(frozen=True)
class FontTokens:
    body: FontToken
    bold: FontToken
    small: FontToken
    title: FontToken


@dataclass(frozen=True)
class RuleToken:
    width: Length
    grey: float = 0.0


@dataclass(frozen=True)
class RuleTokens:
    hairline: RuleToken
    standard: RuleToken
    heavy: RuleToken


@dataclass(frozen=True)
class BoardProfile:
    id: str
    page_width: Length
    page_height: Length
    content_frame: Frame
    safe_print_insets: tuple[Length, Length, Length, Length]
    fonts: FontTokens
    rules: RuleTokens
    answer_line_height: Length
    component_gap: Length

    def __post_init__(self) -> None:
        top, right, bottom, left = self.safe_print_insets
        safe_x1 = self.page_width.pt - right.pt
        safe_y1 = self.page_height.pt - top.pt
        if (
            self.content_frame.x.pt < left.pt
            or self.content_frame.y.pt < bottom.pt
            or self.content_frame.x.pt + self.content_frame.width.pt > safe_x1
            or self.content_frame.y.pt + self.content_frame.height.pt > safe_y1
        ):
            raise ValueError("content frame lies outside the safe-print area")

    @classmethod
    def testing(cls, *, content_left: float = 18.0) -> BoardProfile:
        from Backend.Core.document_dsl.profiles import _profile

        return _profile("testing", left_mm=content_left)


class DocumentRole(StrEnum):
    QUESTION_PAPER = "question-paper"
    MARK_SCHEME = "mark-scheme"
    SOURCE_BOOKLET = "source-booklet"
    INSERT = "insert"


class PageRole(StrEnum):
    COVER = "cover"
    INSTRUCTIONS = "instructions"
    QUESTION = "question"
    SOURCE = "source"
    CONTINUATION = "continuation"
    BLANK = "blank"
    SCHEME = "scheme"
    LEVELS = "levels"


@dataclass(frozen=True)
class DocumentMetadata:
    title: str
    author: str
    subject: str = ""
    keywords: tuple[str, ...] = ()
    language: str = "en-GB"
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PageSpec:
    role: PageRole
    components: tuple[object, ...]
    label: str = ""


@dataclass(frozen=True)
class DocumentSpec:
    profile_id: str
    role: DocumentRole
    pages: tuple[PageSpec, ...]
    metadata: DocumentMetadata

    def __post_init__(self) -> None:
        if not self.pages:
            raise ValueError("a document must declare at least one page")


@dataclass(frozen=True)
class LayoutBox:
    component: object
    x: Length
    y: Length
    width: Length
    height: Length


@dataclass(frozen=True)
class LayoutPage:
    number: int
    role: PageRole
    boxes: tuple[LayoutBox, ...]
    label: str = ""


@dataclass(frozen=True)
class LayoutPlan:
    profile: BoardProfile
    role: DocumentRole
    pages: tuple[LayoutPage, ...]
    metadata: DocumentMetadata


@dataclass(frozen=True)
class RenderEvidence:
    destination: str
    sha256: str
    page_count: int
    elapsed_seconds: float
    selectable_text: bool
    atomic_publication: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RendererContract:
    """Versioned capabilities declared by a family renderer."""

    profile: BoardProfile
    document_roles: tuple[DocumentRole, ...]
    vector_components: tuple[str, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.document_roles:
            raise ValueError("a renderer must support at least one document role")
        if len(set(self.vector_components)) != len(self.vector_components):
            raise ValueError("renderer vector components must be unique")
