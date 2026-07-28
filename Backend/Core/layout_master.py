from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class LayoutConformanceError(ValueError):
    pass


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_value(cls, value: Iterable[float]) -> "Rect":
        values = tuple(float(item) for item in value)
        if len(values) != 4:
            raise ValueError("a rectangle requires four coordinates")
        rect = cls(*values)
        if rect.x1 < rect.x0 or rect.y1 < rect.y0:
            raise ValueError("rectangle coordinates are inverted")
        return rect

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def close_to(self, other: "Rect", tolerance: float = 0.1) -> bool:
        return all(
            math.isclose(left, right, abs_tol=tolerance)
            for left, right in zip(
                (self.x0, self.y0, self.x1, self.y1),
                (other.x0, other.y0, other.x1, other.y1),
                strict=True,
            )
        )


@dataclass(frozen=True)
class TextSlot:
    rect: Rect
    font_name: str
    font_size: float
    leading: float
    align: str = "left"
    minimum_font_size: float | None = None

    def __post_init__(self) -> None:
        if self.font_size <= 0 or self.leading <= 0:
            raise ValueError("font size and leading must be positive")
        if self.align not in {"left", "centre", "right"}:
            raise ValueError(f"unsupported alignment: {self.align}")


@dataclass(frozen=True)
class PageMaster:
    number: int
    role: str
    media_box: Rect
    crop_box: Rect
    trim_box: Rect
    bleed_box: Rect
    art_box: Rect
    content_box: Rect | None
    text_lines: tuple[dict[str, Any], ...]
    drawings: tuple[dict[str, Any], ...]
    images: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class PaperMaster:
    family: str
    paper: str
    document_role: str
    source_sha256: str
    pages: tuple[PageMaster, ...]
    recurring_furniture: tuple[dict[str, Any], ...]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def load_layout_master(path: Path) -> PaperMaster:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError(f"unsupported layout-master schema: {payload.get('schema_version')}")
    pages = tuple(_page_from_payload(item) for item in payload["pages"])
    if tuple(page.number for page in pages) != tuple(range(1, len(pages) + 1)):
        raise ValueError("layout-master pages must be sequential")
    return PaperMaster(
        family=str(payload["family"]),
        paper=str(payload["paper"]),
        document_role=str(payload["document_role"]),
        source_sha256=str(payload["source_sha256"]),
        pages=pages,
        recurring_furniture=tuple(payload.get("recurring_furniture", ())),
    )


def _page_from_payload(payload: dict[str, Any]) -> PageMaster:
    boxes = payload["boxes"]
    content = payload.get("content_box")
    return PageMaster(
        number=int(payload["number"]),
        role=str(payload["role"]),
        media_box=Rect.from_value(boxes["media"]),
        crop_box=Rect.from_value(boxes["crop"]),
        trim_box=Rect.from_value(boxes["trim"]),
        bleed_box=Rect.from_value(boxes["bleed"]),
        art_box=Rect.from_value(boxes["art"]),
        content_box=Rect.from_value(content) if content else None,
        text_lines=tuple(payload.get("text_lines", ())),
        drawings=tuple(payload.get("drawings", ())),
        images=tuple(payload.get("images", ())),
    )


def wrap_text(text: str, font_name: str, font_size: float, width: float) -> list[str]:
    from reportlab.pdfbase import pdfmetrics

    paragraphs = text.splitlines() or [""]
    lines: list[str] = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words.pop(0)
        for word in words:
            candidate = f"{current} {word}"
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= width:
                current = candidate
            else:
                if pdfmetrics.stringWidth(word, font_name, font_size) > width:
                    raise LayoutConformanceError(f"word does not fit fixed slot: {word!r}")
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_text_slot(pdf: Any, page_height: float, slot: TextSlot, text: str) -> float:
    """Draw in a PyMuPDF-style top-origin slot on a ReportLab canvas.

    Returns the font size used. Text is never clipped: an impossible fit raises.
    """

    minimum = slot.minimum_font_size or slot.font_size
    size = slot.font_size
    while size + 1e-6 >= minimum:
        leading = slot.leading * (size / slot.font_size)
        lines = wrap_text(text, slot.font_name, size, slot.rect.width)
        if len(lines) * leading <= slot.rect.height + 1e-6:
            break
        size = round(size - 0.25, 2)
    else:
        raise LayoutConformanceError(
            f"text overflows fixed slot {slot.rect}; minimum font size is {minimum}"
        )

    pdf.saveState()
    pdf.setFont(slot.font_name, size)
    baseline = page_height - slot.rect.y0 - size
    for line in lines:
        if slot.align == "centre":
            pdf.drawCentredString((slot.rect.x0 + slot.rect.x1) / 2, baseline, line)
        elif slot.align == "right":
            pdf.drawRightString(slot.rect.x1, baseline, line)
        else:
            pdf.drawString(slot.rect.x0, baseline, line)
        baseline -= leading
    pdf.restoreState()
    return size


def validate_pdf_geometry(
    pdf_path: Path,
    master: PaperMaster,
    *,
    tolerance: float = 0.1,
) -> list[str]:
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("PyMuPDF is required for layout validation") from error

    document = fitz.open(pdf_path)
    try:
        errors: list[str] = []
        if document.page_count != master.page_count:
            errors.append(
                f"page count {document.page_count} does not match measured master "
                f"{master.page_count}"
            )
        for index in range(min(document.page_count, master.page_count)):
            page = document[index]
            expected = master.pages[index]
            actual_boxes = {
                "media": Rect.from_value(page.mediabox),
                "crop": Rect.from_value(page.cropbox),
                "trim": Rect.from_value(page.trimbox),
                "bleed": Rect.from_value(page.bleedbox),
                "art": Rect.from_value(page.artbox),
            }
            for name, expected_box in (
                ("media", expected.media_box),
                ("crop", expected.crop_box),
                ("trim", expected.trim_box),
                ("bleed", expected.bleed_box),
                ("art", expected.art_box),
            ):
                if not actual_boxes[name].close_to(expected_box, tolerance):
                    errors.append(
                        f"page {index + 1} {name} box {actual_boxes[name]} does not match "
                        f"{expected_box}"
                    )
        return errors
    finally:
        document.close()


def _rect_values(rect: Rect) -> tuple[float, float, float, float]:
    return rect.x0, rect.y0, rect.x1, rect.y1


def _clamp_fitz_rect(rect: Any, media: Any) -> Any:
    import fitz

    return fitz.Rect(
        max(rect.x0, media.x0),
        max(rect.y0, media.y0),
        min(rect.x1, media.x1),
        min(rect.y1, media.y1),
    )


def conform_pdf_page_boxes(
    pdf_path: Path,
    master: PaperMaster,
    *,
    strict_page_count: bool = True,
) -> None:
    """Apply measured page boxes without importing any reference artwork or text."""

    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("PyMuPDF is required for page-box conformance") from error

    source = fitz.open(pdf_path)
    actual_page_count = source.page_count
    if strict_page_count and actual_page_count != master.page_count:
        source.close()
        raise LayoutConformanceError(
            f"{pdf_path.name} has {actual_page_count} pages; expected {master.page_count}"
        )
    rewritten = fitz.open()
    temporary = pdf_path.with_name(f"{pdf_path.stem}.layout-tmp{pdf_path.suffix}")
    try:
        for index, source_page in enumerate(source):
            expected = master.pages[min(index, master.page_count - 1)]
            media = fitz.Rect(*_rect_values(expected.media_box))
            crop = fitz.Rect(*_rect_values(expected.crop_box))
            page = rewritten.new_page(width=media.width, height=media.height)
            actual_media = page.mediabox
            actual_crop = _clamp_fitz_rect(crop, actual_media)
            page.show_pdf_page(actual_crop, source, index, clip=source_page.rect)
            page.set_cropbox(actual_crop)
            page.set_trimbox(
                _clamp_fitz_rect(
                    fitz.Rect(*_rect_values(expected.trim_box)), actual_media
                )
            )
            page.set_bleedbox(
                _clamp_fitz_rect(
                    fitz.Rect(*_rect_values(expected.bleed_box)), actual_media
                )
            )
            page.set_artbox(
                _clamp_fitz_rect(
                    fitz.Rect(*_rect_values(expected.art_box)), actual_media
                )
            )
        rewritten.save(temporary, garbage=4, deflate=True)
    finally:
        rewritten.close()
        source.close()
    os.replace(temporary, pdf_path)


def conform_pdf_to_box_template(
    pdf_path: Path,
    boxes: dict[str, Iterable[float]] | list[dict[str, Iterable[float]]],
    *,
    expected_page_count: int | None = None,
    strict_page_count: bool = True,
) -> None:
    """Apply measured box sets without importing reference artwork or text.

    A single mapping is repeated. A list follows the reference page sequence;
    generated overflow pages use the final measured box set.
    """

    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("PyMuPDF is required for page-box conformance") from error

    box_sequence = boxes if isinstance(boxes, list) else [boxes]
    if not box_sequence:
        raise LayoutConformanceError("at least one page-box template is required")

    source = fitz.open(pdf_path)
    actual_page_count = source.page_count
    if (
        strict_page_count
        and expected_page_count is not None
        and actual_page_count != expected_page_count
    ):
        source.close()
        raise LayoutConformanceError(
            f"{pdf_path.name} has {actual_page_count} pages; expected {expected_page_count}"
        )
    rewritten = fitz.open()
    temporary = pdf_path.with_name(f"{pdf_path.stem}.layout-tmp{pdf_path.suffix}")
    try:
        direct_update = all(
            abs(source_page.rect.width - fitz.Rect(
                *box_sequence[min(index, len(box_sequence) - 1)]["media"]
            ).width) <= 1
            and abs(source_page.rect.height - fitz.Rect(
                *box_sequence[min(index, len(box_sequence) - 1)]["media"]
            ).height) <= 1
            for index, source_page in enumerate(source)
        )
        if direct_update:
            for index, page in enumerate(source):
                page_boxes = box_sequence[min(index, len(box_sequence) - 1)]
                media = fitz.Rect(*page_boxes["media"])
                page.set_mediabox(media)
                actual_media = page.mediabox
                page.set_cropbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["crop"]), actual_media)
                )
                page.set_trimbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["trim"]), actual_media)
                )
                page.set_bleedbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["bleed"]), actual_media)
                )
                page.set_artbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["art"]), actual_media)
                )
            source.save(temporary, garbage=4, deflate=True)
        else:
            for index, source_page in enumerate(source):
                page_boxes = box_sequence[min(index, len(box_sequence) - 1)]
                media = fitz.Rect(*page_boxes["media"])
                crop = fitz.Rect(*page_boxes["crop"])
                page = rewritten.new_page(width=media.width, height=media.height)
                actual_media = page.mediabox
                actual_crop = _clamp_fitz_rect(crop, actual_media)
                page.show_pdf_page(actual_crop, source, index, clip=source_page.rect)
                page.set_cropbox(actual_crop)
                page.set_trimbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["trim"]), actual_media)
                )
                page.set_bleedbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["bleed"]), actual_media)
                )
                page.set_artbox(
                    _clamp_fitz_rect(fitz.Rect(*page_boxes["art"]), actual_media)
                )
            rewritten.save(temporary, garbage=4, deflate=True)
    finally:
        rewritten.close()
        source.close()
    os.replace(temporary, pdf_path)
