"""Opt-in presentation for newly rendered UK offline previews, never model data."""

import math
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import pymupdf as fitz

from Backend.Core.pdf_validation import text_trace_is_occluded

PREVIEW_PRESENTATION = "uk-layout-preview-v2-raster-order"
PREVIEW_NOTICE = "LAYOUT PREVIEW · Unreviewed sample content · Unofficial"
_preview: ContextVar[bool] = ContextVar("uk_layout_preview", default=False)


@contextmanager
def preview_presentation(enabled: bool) -> Iterator[None]:
    token = _preview.set(enabled)
    try:
        yield
    finally:
        _preview.reset(token)


def preview_copy(original: str) -> str:
    """Replace an existing cover subtitle without adding a flowable or page."""
    return PREVIEW_NOTICE if _preview.get() else original


def is_layout_preview() -> bool:
    return _preview.get()


def preview_font_size(original: float) -> float:
    """Keep long preview subtitles inside their existing fixed cover slots."""
    return min(original, 14) if _preview.get() else original


def preview_paragraph(original: str) -> str:
    """Retain the source-cover subject in its existing single-line kicker slot."""
    if not _preview.get():
        return original
    return f'<font size="10">{escape(original)} · {PREVIEW_NOTICE}</font>'


def _notice_is_occluded(span: dict[str, Any], drawings: list[dict[str, Any]]) -> bool:
    text = "".join(chr(char[0]) for char in span["chars"])
    start = text.index(PREVIEW_NOTICE)
    return any(
        not chr(char[0]).isspace()
        and text_trace_is_occluded({**span, "bbox": char[3]}, drawings)
        for char in span["chars"][start : start + len(PREVIEW_NOTICE)]
    )


def _notice_raster_order_unverifiable(span: dict[str, Any], artwork: list[Any]) -> bool:
    try:
        sequence = span.get("seqno")
        known_sequence = (
            type(sequence) is int
            and 0 <= sequence < len(artwork)
            and artwork[sequence][0] in {"fill-text", "stroke-text", "ignore-text"}
        )
        rasters = [
            bounds
            for index, (kind, bounds) in enumerate(artwork)
            if kind == "fill-image" and (not known_sequence or index > sequence)
        ]
        if not rasters:
            return False
        text = "".join(chr(char[0]) for char in span["chars"])
        start = text.index(PREVIEW_NOTICE)
        glyphs = [
            fitz.Rect(char[3])
            for char in span["chars"][start : start + len(PREVIEW_NOTICE)]
            if not chr(char[0]).isspace()
        ]
        images = [fitz.Rect(bounds) for bounds in rasters]
        if any(
            rect.is_empty
            or rect.is_infinite
            or not all(math.isfinite(value) for value in rect)
            for rect in (*glyphs, *images)
        ):
            return True
    except (TypeError, ValueError, IndexError, OverflowError):
        return True
    # Transparency and masks do not prove the original glyph is still visible.
    # This is an ordering certificate, not a claim that every image is opaque.
    return any(image.intersects(glyph) for image in images for glyph in glyphs)


def validate_preview_pdf(path: Path) -> dict[str, object]:
    """Require an actually printed, legible first-page notice before publication."""
    with fitz.open(path) as document:
        page = document[0]
        boxes = [
            page.search_for(text)
            for text in ("LAYOUT PREVIEW", "Unreviewed sample content")
        ]
        if any(len(matches) != 1 for matches in boxes):
            raise ValueError(f"{path.name}: missing or duplicate layout-preview notice")
        notice_boxes = [rect for matches in boxes for rect in matches]
        printable = fitz.Rect(page.rect)
        printable.x0 += 12
        printable.y0 += 12
        printable.x1 -= 12
        printable.y1 -= 12
        if any(
            not printable.contains(rect) or rect.height < 7 for rect in notice_boxes
        ):
            raise ValueError(
                f"{path.name}: layout-preview notice is clipped or too small"
            )
        spans = [
            span
            for span in page.get_texttrace()
            if PREVIEW_NOTICE in "".join(chr(char[0]) for char in span["chars"])
        ]
        drawings = page.get_drawings()
        if not spans or any(
            span["type"] == 3
            or span["opacity"] < 0.8
            or span["size"] < 8
            or all(value > 0.95 for value in span["color"])
            # A single hidden word/character invalidates the printed notice.
            or _notice_is_occluded(span, drawings)
            for span in spans
        ):
            raise ValueError(
                f"{path.name}: layout-preview notice is not visibly printed"
            )
        artwork = page.get_bboxlog()
        # Bound our analysis, not the work PyMuPDF did to obtain its display list.
        if len(artwork) > 10_000 or any(
            _notice_raster_order_unverifiable(span, artwork) for span in spans
        ):
            raise ValueError(
                f"{path.name}: layout-preview notice visibility cannot be verified after raster artwork"
            )
    return {"policy": PREVIEW_PRESENTATION, "first_page_notice": True}
