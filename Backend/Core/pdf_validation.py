from __future__ import annotations

import json
import math
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Any

import pymupdf as fitz

from Backend.Core.paths import REPO_ROOT
from Backend.Core.pdf_accessibility import has_logical_page_order

CONTROLLED_FONT_PREFIXES = {
    "economics": (
        "Arimo",
        "HelveticaNeue",
        "Verdana",
        "Courier",
        "Helvetica",
        "Symbol",
        "Times",
        "Tinos",
        "ZapfDingbats",
    ),
    "default": (
        "Arimo",
        "Arial",
        "Courier",
        "CourierNew",
        "Helvetica",
        "Symbol",
        "Times",
        "Tinos",
        "ZapfDingbats",
    ),
}
STANDARD_PDF_FAMILIES = {
    "courier",
    "helvetica",
    "symbol",
    "times",
    "zapfdingbats",
}
LAYOUT_PROFILES_PATH = REPO_ROOT / "Resources" / "layout-profiles.json"
PROFILE_KEYS = {
    "accounting_aqa": ("aqa", "accounting"),
    "business_aqa": ("aqa", "business"),
    "computer_science": ("aqa", "computer-science"),
    "computer_science_ocr": ("ocr", "computer-science"),
    "economics_aqa": ("aqa", "economics"),
    "economics_ocr": ("ocr", "economics"),
}
LINE_MARK = re.compile(r"(?:\[|\()(\d{1,2})(?:\s+marks?)?(?:\]|\))\s*$", re.IGNORECASE)
MARGIN_FURNITURE = re.compile(
    r"(?:do\s+not\s+write|outside\s+the|in\s+this\s+area)",
    re.IGNORECASE,
)
INTENTIONAL_BLANK_PAGE_CONTRACTS = {
    # Pearson's Paper 2 mark scheme ends on a deliberately blank page. Keeping
    # that final leaf preserves the measured 36-page reference pagination.
    ("economics", "2", "mark_scheme"): frozenset({36}),
}


@dataclass(frozen=True)
class GlyphMetric:
    """A compact, serialisable sample of one rendered PDF glyph."""

    font_file: str | None
    embedded_name: str
    baseline: float
    bbox: tuple[float, float, float, float]
    advance: float
    line_height: float


def extract_pdf_evidence(
    path: Path,
    *,
    non_printable_margin_mm: float = 4.2,
    maximum_glyphs_per_page: int = 2048,
) -> dict[str, Any]:
    """Extract print and accessibility evidence without retaining source prose.

    Glyph characters are deliberately omitted. Geometry remains useful for
    regression comparisons while examination content does not leak into audit
    reports.
    """

    margin_points = non_printable_margin_mm * 72 / 25.4
    with fitz.open(path) as document:
        fonts = _font_evidence(document)
        font_files = {
            _normalise_font(str(item["embedded_name"])): item.get("font_file")
            for item in fonts
        }
        catalog = document.pdf_catalog()
        tagged = catalog > 0 and document.xref_get_key(catalog, "StructTreeRoot")[
            0
        ] not in {"null", "none"}
        pages = [
            _page_print_evidence(
                page,
                font_files=font_files,
                margin_points=margin_points,
                maximum_glyphs=maximum_glyphs_per_page,
                logical_order=has_logical_page_order(document, page),
            )
            for page in document
        ]
    return {
        "schema_version": 1,
        "path": str(path),
        "tagged": tagged,
        "fonts": fonts,
        "pages": pages,
    }


def compare_page_evidence(
    generated: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, float]:
    """Compare typography and print geometry on a stable zero-to-one scale."""

    return {
        "font_identity": _set_score(
            {_normalise_font(name) for name in generated.get("font_names", [])},
            {_normalise_font(name) for name in reference.get("font_names", [])},
        ),
        "baseline": _sequence_closeness(
            generated.get("baselines", []),
            reference.get("baselines", []),
            tolerance=6.0,
        ),
        "glyph_bbox": _sequence_closeness(
            generated.get("glyph_box_heights", []),
            reference.get("glyph_box_heights", []),
            tolerance=2.0,
        ),
        "leading": _sequence_closeness(
            generated.get("line_leading", []),
            reference.get("line_leading", []),
            tolerance=3.0,
        ),
        "minimum_rule_width": _scalar_closeness(
            generated.get("minimum_rule_width"),
            reference.get("minimum_rule_width"),
            tolerance=0.1,
        ),
        "rule_count": _count_score(
            len(generated.get("rules", [])), len(reference.get("rules", []))
        ),
        "answer_line_spacing": _sequence_closeness(
            generated.get("answer_line_spacing", []),
            reference.get("answer_line_spacing", []),
            tolerance=2.0,
        ),
        "mark_box_placement": _point_sequence_score(
            generated.get("mark_positions", []),
            reference.get("mark_positions", []),
            tolerance=0.025,
        ),
        "reading_order": _scalar_closeness(
            generated.get("reading_order_score"),
            reference.get("reading_order_score"),
            tolerance=0.05,
        ),
        "safe_print": 1.0 if generated.get("safe_print") else 0.0,
        "monochrome_contrast": min(
            float(generated.get("monochrome_minimum_contrast", 0)) / 4.5,
            1.0,
        ),
    }


def _font_evidence(document: fitz.Document) -> list[dict[str, Any]]:
    records: dict[tuple[int, str], dict[str, Any]] = {}
    for page in document:
        used_fonts = {
            _normalise_font(str(span.get("font", "")))
            for block in page.get_text("dict").get("blocks", [])
            if block.get("type") == 0
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if str(span.get("text", "")).strip()
        }
        for font in page.get_fonts(full=True):
            xref, extension, font_type, base_name, resource_name, encoding, *_ = font
            if _normalise_font(str(base_name)) not in used_fonts:
                continue
            embedded, font_file = _font_embedding(document, int(xref), str(extension))
            key = (int(xref), str(base_name))
            records[key] = {
                "xref": int(xref),
                "embedded_name": str(base_name),
                "resource_name": str(resource_name),
                "type": str(font_type),
                "encoding": str(encoding),
                "embedded": embedded,
                "font_file": font_file,
            }
    return sorted(
        records.values(), key=lambda item: (item["embedded_name"], item["xref"])
    )


def _font_embedding(
    document: fitz.Document,
    xref: int,
    extension: str,
) -> tuple[bool, str | None]:
    if xref <= 0:
        return False, None
    descriptor_kind, descriptor_value = document.xref_get_key(xref, "FontDescriptor")
    descriptor_match = re.search(r"(\d+)\s+0\s+R", descriptor_value)
    if descriptor_kind == "xref" and descriptor_match:
        descriptor = int(descriptor_match.group(1))
        for key in ("FontFile", "FontFile2", "FontFile3"):
            kind, value = document.xref_get_key(descriptor, key)
            match = re.search(r"(\d+)\s+0\s+R", value)
            if kind == "xref" and match:
                return True, f"xref:{match.group(1)}.{extension}"
    return False, None


def _page_print_evidence(
    page: fitz.Page,
    *,
    font_files: dict[str, str | None],
    margin_points: float,
    maximum_glyphs: int,
    logical_order: bool,
) -> dict[str, Any]:
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()
    glyphs: list[GlyphMetric] = []
    baselines: list[float] = []
    glyph_heights: list[float] = []
    font_names: set[str] = set()
    line_origins: list[float] = []
    content_rects: list[fitz.Rect] = []
    contrasts = _page_text_contrasts(page, drawings)
    mark_positions: list[tuple[float, float]] = []
    glyph_count = 0
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            if "bbox" in block:
                bounds = fitz.Rect(block["bbox"])
                if not _is_decorative_bleed(bounds, page.rect):
                    content_rects.append(bounds)
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if spans:
                line_origins.append(float(spans[0].get("origin", (0, 0))[1]))
            for span in spans:
                font = str(span.get("font", ""))
                font_names.add(font)
                baseline = float(span.get("origin", (0, 0))[1])
                baselines.append(round(baseline, 3))
                span_bbox = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                chars = span.get("chars", [])
                span_text = "".join(str(char.get("c", "")) for char in chars)
                if not _is_margin_furniture(span_text, span_bbox, page.rect):
                    content_rects.append(span_bbox)
                if LINE_MARK.search(span_text.strip()):
                    mark_positions.append(
                        (
                            round(span_bbox.x1 / page.rect.width, 4),
                            round(span_bbox.y0 / page.rect.height, 4),
                        )
                    )
                for char_index, char in enumerate(chars):
                    bbox = fitz.Rect(char.get("bbox", (0, 0, 0, 0)))
                    glyph_count += 1
                    glyph_heights.append(round(bbox.height, 3))
                    if len(glyphs) >= maximum_glyphs:
                        continue
                    origin = char.get("origin", (bbox.x0, baseline))
                    next_origin = (
                        chars[char_index + 1].get("origin", (bbox.x1, baseline))
                        if char_index + 1 < len(chars)
                        else (bbox.x1, baseline)
                    )
                    glyphs.append(
                        GlyphMetric(
                            font_file=font_files.get(_normalise_font(font)),
                            embedded_name=font,
                            baseline=round(float(origin[1]), 3),
                            bbox=tuple(round(float(value), 3) for value in bbox),
                            advance=round(float(next_origin[0]) - float(origin[0]), 3),
                            line_height=round(span_bbox.height, 3),
                        )
                    )

    rules: list[dict[str, Any]] = []
    for drawing in drawings:
        width = float(drawing.get("width") or 0)
        if drawing.get("color") is None or width <= 0:
            continue
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue
            start, end = item[1], item[2]
            length = math.hypot(end.x - start.x, end.y - start.y)
            rules.append(
                {
                    "width": round(width, 3),
                    "start": (round(start.x, 3), round(start.y, 3)),
                    "end": (round(end.x, 3), round(end.y, 3)),
                    "length": round(length, 3),
                }
            )
    horizontal_lines = sorted(
        rule["start"][1]
        for rule in rules
        if abs(rule["start"][1] - rule["end"][1]) < 0.5
        and rule["length"] >= page.rect.width * 0.45
    )
    answer_spacing = [
        round(right - left, 3)
        for left, right in pairwise(horizontal_lines)
        if right - left > 2
    ]
    content_rect = _union_rects(content_rects)
    images = [
        {
            "bbox": tuple(round(float(value), 3) for value in image["bbox"]),
            "pixel_width": int(image["width"]),
            "pixel_height": int(image["height"]),
        }
        for image in page.get_image_info(hashes=False)
    ]
    safe_box = fitz.Rect(
        page.rect.x0 + margin_points,
        page.rect.y0 + margin_points,
        page.rect.x1 - margin_points,
        page.rect.y1 - margin_points,
    )
    return {
        "page": page.number + 1,
        "page_box": tuple(round(float(value), 3) for value in page.rect),
        "content_box": (
            tuple(round(float(value), 3) for value in content_rect)
            if content_rect is not None
            else None
        ),
        "font_names": sorted(font_names),
        "glyph_count": glyph_count,
        "glyphs": [asdict(item) for item in glyphs],
        "baselines": _representative_values(baselines),
        "glyph_box_heights": _representative_values(glyph_heights),
        "line_leading": _leading(line_origins),
        "rules": rules,
        "drawing_count": len(drawings),
        "images": images,
        "table_geometry": _table_geometry(rules),
        "minimum_rule_width": min((item["width"] for item in rules), default=None),
        "answer_line_spacing": answer_spacing,
        "mark_positions": mark_positions,
        "reading_order_score": 1.0 if logical_order else _reading_order_score(page),
        "safe_print": content_rect is None or safe_box.contains(content_rect),
        "safe_print_box": tuple(round(float(value), 3) for value in safe_box),
        "monochrome_minimum_contrast": round(min(contrasts), 3) if contrasts else 21.0,
    }


def _union_rects(rects: list[fitz.Rect]) -> fitz.Rect | None:
    valid = [rect for rect in rects if not rect.is_empty and not rect.is_infinite]
    if not valid:
        return None
    result = fitz.Rect(valid[0])
    for rect in valid[1:]:
        result.include_rect(rect)
    return result


def _is_decorative_bleed(bounds: fitz.Rect, page_bounds: fitz.Rect) -> bool:
    """Return whether an image is a full-bleed background rather than content."""
    if bounds.is_empty or page_bounds.is_empty:
        return False
    coverage = bounds.get_area() / page_bounds.get_area()
    touches_edge = (
        bounds.x0 <= page_bounds.x0 + 1
        and bounds.y0 <= page_bounds.y0 + 1
        and bounds.x1 >= page_bounds.x1 - 1
        and bounds.y1 >= page_bounds.y1 - 1
    )
    return touches_edge and coverage >= 0.9


def _is_margin_furniture(
    text: str,
    bounds: fitz.Rect,
    page_bounds: fitz.Rect,
) -> bool:
    """Exclude repeated non-answerable printer furniture from the safety box."""
    near_vertical_edge = (
        bounds.x0 <= page_bounds.x0 + 18 or bounds.x1 >= page_bounds.x1 - 18
    )
    return near_vertical_edge and MARGIN_FURNITURE.search(text) is not None


def _table_geometry(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    horizontal = [
        item for item in rules if abs(item["start"][1] - item["end"][1]) < 0.5
    ]
    vertical = [item for item in rules if abs(item["start"][0] - item["end"][0]) < 0.5]
    if len(horizontal) < 2 or len(vertical) < 2:
        return []
    x_values = [
        point for item in vertical for point in (item["start"][0], item["end"][0])
    ]
    y_values = [
        point for item in horizontal for point in (item["start"][1], item["end"][1])
    ]
    return [
        {
            "bbox": (
                round(min(x_values), 3),
                round(min(y_values), 3),
                round(max(x_values), 3),
                round(max(y_values), 3),
            ),
            "rows": len({round(value, 1) for value in y_values}) - 1,
            "columns": len({round(value, 1) for value in x_values}) - 1,
        }
    ]


def _reading_order_score(page: fitz.Page) -> float:
    origins = [
        (float(block[1]), float(block[0]))
        for block in page.get_text("blocks", sort=False)
        if str(block[4]).strip()
    ]
    if len(origins) < 2:
        return 1.0
    visual_order = sorted(range(len(origins)), key=lambda index: origins[index])
    position = {item: index for index, item in enumerate(visual_order)}
    inversions = sum(
        position[left] > position[right]
        for left in range(len(origins))
        for right in range(left + 1, len(origins))
    )
    maximum = len(origins) * (len(origins) - 1) / 2
    return round(1.0 - inversions / maximum, 4)


def _contrast_against_white(rgb_value: int) -> float:
    channels = ((rgb_value >> 16) & 255, (rgb_value >> 8) & 255, rgb_value & 255)
    return _contrast_ratio(channels, (255, 255, 255))


def _page_text_contrasts(
    page: fitz.Page,
    drawings: list[dict[str, Any]],
) -> list[float]:
    contrasts: list[float] = []
    for trace in page.get_texttrace():
        if trace.get("type") != 0:
            continue
        bounds = fitz.Rect(trace.get("bbox", (0, 0, 0, 0)))
        text = "".join(chr(int(char[0])) for char in trace.get("chars", []))
        if not text.strip() or _is_margin_furniture(text, bounds, page.rect):
            continue
        sequence = int(trace.get("seqno", -1))
        if any(
            int(drawing.get("seqno", -1)) > sequence
            and float(drawing.get("fill_opacity") or 0) >= 0.99
            and drawing.get("fill") is not None
            and fitz.Rect(drawing.get("rect", (0, 0, 0, 0))).contains(bounds)
            for drawing in drawings
        ):
            continue
        centre = fitz.Point(
            (bounds.x0 + bounds.x1) / 2,
            (bounds.y0 + bounds.y1) / 2,
        )
        covering_fills = [
            drawing
            for drawing in drawings
            if drawing.get("fill") is not None
            and int(drawing.get("seqno", -1)) < sequence
            and fitz.Rect(drawing.get("rect", (0, 0, 0, 0))).contains(centre)
        ]
        background = (255, 255, 255)
        if covering_fills:
            nearest = max(
                covering_fills,
                key=lambda drawing: int(drawing.get("seqno", -1)),
            )
            background = tuple(
                round(float(channel) * 255) for channel in nearest["fill"][:3]
            )
        color = trace.get("color", (0.0, 0.0, 0.0))
        foreground = tuple(round(float(channel) * 255) for channel in color[:3])
        contrasts.append(_contrast_ratio(foreground, background))
    return contrasts


def _contrast_ratio(
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
) -> float:

    def linear(channel: int) -> float:
        value = channel / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    def luminance(channels: tuple[int, int, int]) -> float:
        return (
            0.2126 * linear(channels[0])
            + 0.7152 * linear(channels[1])
            + 0.0722 * linear(channels[2])
        )

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _representative_values(values: list[float], limit: int = 256) -> list[float]:
    if len(values) <= limit:
        return values
    step = len(values) / limit
    return [values[min(int(index * step), len(values) - 1)] for index in range(limit)]


def _leading(origins: list[float]) -> list[float]:
    ordered = sorted({round(value, 2) for value in origins})
    return [round(right - left, 3) for left, right in pairwise(ordered) if right > left]


def _set_score(first: set[str], second: set[str]) -> float:
    if not first and not second:
        return 1.0
    return round(len(first & second) / max(len(first | second), 1), 4)


def _scalar_closeness(first: Any, second: Any, *, tolerance: float) -> float:
    if first is None and second is None:
        return 1.0
    if first is None or second is None:
        return 0.0
    return round(max(0.0, 1.0 - abs(float(first) - float(second)) / tolerance), 4)


def _sequence_closeness(
    first: list[Any], second: list[Any], *, tolerance: float
) -> float:
    if not first and not second:
        return 1.0
    if not first or not second:
        return 0.0
    count = min(len(first), len(second))
    closeness = [
        max(0.0, 1.0 - abs(float(first[index]) - float(second[index])) / tolerance)
        for index in range(count)
    ]
    coverage = count / max(len(first), len(second))
    return round(statistics.mean(closeness) * coverage, 4)


def _point_sequence_score(
    first: list[Any], second: list[Any], *, tolerance: float
) -> float:
    if not first and not second:
        return 1.0
    if not first or not second:
        return 0.0
    count = min(len(first), len(second))
    scores = []
    for index in range(count):
        distance = math.dist(first[index], second[index])
        scores.append(max(0.0, 1.0 - distance / tolerance))
    return round(statistics.mean(scores) * count / max(len(first), len(second)), 4)


def _count_score(first: int, second: int) -> float:
    if first == second == 0:
        return 1.0
    return round(min(first, second) / max(first, second), 4)


def validate_pdf_for_release(
    path: Path,
    *,
    subject: str,
    paper_number: str | None = None,
    role: str | None = None,
) -> dict[str, Any]:
    """Fail closed on malformed, substituted, annotated, or low-resolution PDFs."""

    document = fitz.open(path)
    try:
        if document.page_count < 1:
            raise ValueError(f"{path.name} contains no pages")
        metadata = document.metadata or {}
        if not metadata.get("title"):
            raise ValueError(f"{path.name} has no PDF title metadata")
        if role and (
            metadata.get("title", "").casefold() in {"untitled", "unspecified"}
            or metadata.get("author", "").casefold() in {"", "anonymous", "unspecified"}
            or metadata.get("subject", "").casefold() in {"", "unspecified"}
        ):
            raise ValueError(f"{path.name} has placeholder or missing release metadata")

        fonts: set[str] = set()
        font_characters: Counter[str] = Counter()
        font_sizes: Counter[float] = Counter()
        image_dpi: list[float] = []
        page_layout_metrics: list[dict[str, Any]] = []
        total_overlapping_pairs = 0
        intentional_blank_pages = INTENTIONAL_BLANK_PAGE_CONTRACTS.get(
            (subject, str(paper_number), role),
            frozenset(),
        )
        for page_index, page in enumerate(document, start=1):
            width, height = page.rect.width, page.rect.height
            if not all(math.isfinite(value) and value > 0 for value in (width, height)):
                raise ValueError(
                    f"{path.name} page {page_index} has an invalid page box"
                )
            if page.first_annot is not None:
                raise ValueError(
                    f"{path.name} page {page_index} contains an annotation"
                )
            page_has_text = False
            page_characters = 0
            text_spans: list[tuple[str, fitz.Rect]] = []
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = str(span.get("text", ""))
                        if text.strip():
                            page_has_text = True
                            page_characters += len(text.strip())
                            if "\ufffd" in text:
                                raise ValueError(
                                    f"{path.name} page {page_index} contains "
                                    "a missing-glyph replacement character"
                                )
                            font = str(span.get("font", ""))
                            size = round(float(span.get("size", 0)), 1)
                            fonts.add(font)
                            font_characters[font] += len(text)
                            font_sizes[size] += len(text)
                            if size < 5.0:
                                raise ValueError(
                                    f"{path.name} page {page_index} uses "
                                    f"illegibly small {size:g} pt text"
                                )
                            bbox = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                            text_spans.append((text.strip(), bbox))
                            if (
                                bbox.x0 < page.rect.x0 - 2
                                or bbox.y0 < page.rect.y0 - 2
                                or bbox.x1 > page.rect.x1 + 2
                                or bbox.y1 > page.rect.y1 + 2
                            ):
                                raise ValueError(
                                    f"{path.name} page {page_index} contains "
                                    "text outside the page box"
                                )
            image_info = page.get_image_info(hashes=False)
            for image in image_info:
                bbox = fitz.Rect(image["bbox"])
                if bbox.width <= 0 or bbox.height <= 0:
                    continue
                horizontal = image["width"] / (bbox.width / 72)
                vertical = image["height"] / (bbox.height / 72)
                image_dpi.append(min(horizontal, vertical))
            vector_objects = sum(
                1
                for operation, _bounds in page.get_bboxlog()
                if operation in {"stroke-path", "fill-path", "fill-stroke-path"}
            )
            page_has_content = page_has_text or bool(image_info) or vector_objects > 0
            intentional_blank = page_index in intentional_blank_pages
            if not page_has_content and not intentional_blank:
                raise ValueError(f"{path.name} page {page_index} is unexpectedly empty")
            if (
                page_characters < 8
                and not image_info
                and vector_objects < 3
                and not intentional_blank
            ):
                raise ValueError(
                    f"{path.name} page {page_index} has too little content to "
                    "represent a document page"
                )
            overlapping_pairs = _overlapping_text_pairs(text_spans)
            if overlapping_pairs:
                raise ValueError(
                    f"{path.name} contains overlapping text on page {page_index} "
                    f"({len(overlapping_pairs)} pair(s)); first pair: "
                    f"{overlapping_pairs[0]}"
                )
            total_overlapping_pairs += len(overlapping_pairs)
            page_layout_metrics.append(
                {
                    "page": page_index,
                    "characters": page_characters,
                    "text_occupancy": round(_text_occupancy(text_spans, page.rect), 4),
                    "vector_objects": vector_objects,
                    "images": len(image_info),
                    "intentional_blank": intentional_blank,
                    "overlapping_text_pairs": len(overlapping_pairs),
                }
            )

        allowed = CONTROLLED_FONT_PREFIXES[
            "economics" if subject == "economics" else "default"
        ]
        unexpected_fonts = sorted(
            font for font in fonts if font and not font.startswith(allowed)
        )
        if unexpected_fonts:
            raise ValueError(
                f"{path.name} uses uncontrolled font substitutions: "
                + ", ".join(unexpected_fonts)
            )
        typography = _validate_typography_profile(
            subject=subject,
            role=role,
            font_characters=font_characters,
            font_sizes=font_sizes,
            filename=path.name,
        )
        low_resolution = [dpi for dpi in image_dpi if dpi < 150]
        if low_resolution:
            raise ValueError(
                f"{path.name} contains an image below 150 DPI "
                f"({min(low_resolution):.0f} DPI)"
            )
        return {
            "pages": document.page_count,
            "fonts": sorted(fonts),
            "minimum_image_dpi": (round(min(image_dpi), 1) if image_dpi else None),
            "annotations": 0,
            "metadata_title": metadata["title"],
            "metadata_author": metadata.get("author"),
            "metadata_subject": metadata.get("subject"),
            "typography_profile": typography,
            "layout_metrics": {
                "pages": page_layout_metrics,
                "median_text_occupancy": round(
                    statistics.median(
                        page["text_occupancy"] for page in page_layout_metrics
                    ),
                    4,
                ),
                "overlapping_text_pairs": total_overlapping_pairs,
            },
        }
    finally:
        document.close()


def _validate_typography_profile(
    *,
    subject: str,
    role: str | None,
    font_characters: Counter[str],
    font_sizes: Counter[float],
    filename: str,
) -> dict[str, Any] | None:
    if role != "question_paper" or subject not in PROFILE_KEYS:
        return None
    profiles = _layout_profiles()
    key = PROFILE_KEYS[subject]
    profile = profiles.get(key)
    if profile is None:
        raise ValueError(f"no typography profile is available for {subject}")

    reference_fonts = {
        _normalise_font(str(item["family"])) for item in profile.get("fonts", [])[:8]
    }
    generated_fonts = {
        _normalise_font(name) for name, _count in font_characters.most_common(8)
    }
    uses_standard_fallback = bool(generated_fonts) and all(
        any(font.startswith(family) for family in STANDARD_PDF_FAMILIES)
        for font in generated_fonts
    )
    family_overlap = (
        1.0
        if uses_standard_fallback
        else len(reference_fonts & generated_fonts) / max(len(generated_fonts), 1)
    )
    reference_sizes = {
        round(float(item["size"]), 1) for item in profile.get("fonts", [])[:8]
    }
    generated_sizes = {size for size, _count in font_sizes.most_common(10)}
    size_overlap = len(reference_sizes & generated_sizes) / max(
        min(len(reference_sizes), len(generated_sizes)), 1
    )
    if family_overlap < 0.5:
        raise ValueError(
            f"{filename} typography does not match the measured board font "
            f"profile ({family_overlap:.0%} family overlap)"
        )
    if size_overlap < 0.4:
        raise ValueError(
            f"{filename} typography does not match the measured board size "
            f"profile ({size_overlap:.0%} size overlap)"
        )
    return {
        "board": key[0],
        "subject": key[1],
        "font_family_overlap": round(family_overlap, 3),
        "uses_standard_pdf_fallback": uses_standard_fallback,
        "font_size_overlap": round(size_overlap, 3),
        "dominant_fonts": [
            {"family": family, "characters": count}
            for family, count in font_characters.most_common(5)
        ],
        "dominant_sizes": [
            {"size": size, "characters": count}
            for size, count in font_sizes.most_common(8)
        ],
    }


@lru_cache(maxsize=1)
def _layout_profiles() -> dict[tuple[str, str], dict[str, Any]]:
    payload = json.loads(LAYOUT_PROFILES_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported layout profile schema")
    return {
        (str(profile["board"]), str(profile["subject"])): profile
        for profile in payload.get("profiles", [])
        if isinstance(profile, dict)
    }


def _normalise_font(value: str) -> str:
    name = value.rsplit("+", 1)[-1].casefold()
    for token in (
        "bold",
        "italic",
        "regular",
        "ps",
        "psmt",
        "mt",
        ",",
        "-",
        "_",
        " ",
    ):
        name = name.replace(token, "")
    if name == "arimo":
        return "arial"
    if name == "tinos":
        return "timesnewroman"
    return name


def _overlapping_text_pairs(spans: list[tuple[str, fitz.Rect]]) -> list[str]:
    ordered = sorted(spans, key=lambda item: (item[1].y0, item[1].x0))
    pairs: list[str] = []
    for index, (text, bounds) in enumerate(ordered):
        if bounds.is_empty or len(text) < 2:
            continue
        for other_text, other_bounds in ordered[index + 1 :]:
            if other_bounds.y0 >= bounds.y1 - 0.5:
                break
            if other_bounds.is_empty or len(other_text) < 2:
                continue
            intersection = bounds & other_bounds
            if intersection.is_empty:
                continue
            smaller_area = min(bounds.get_area(), other_bounds.get_area())
            if smaller_area and intersection.get_area() / smaller_area >= 0.65:
                pairs.append(f"{text!r} over {other_text!r}")
    return pairs


def _text_occupancy(
    spans: list[tuple[str, fitz.Rect]],
    page_bounds: fitz.Rect,
) -> float:
    if page_bounds.is_empty:
        return 0.0
    occupied = sum(
        (bounds & page_bounds).get_area()
        for _text, bounds in spans
        if not bounds.is_empty
    )
    return min(occupied / page_bounds.get_area(), 1.0)
