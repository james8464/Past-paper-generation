from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf as fitz
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageOps,
    ImageStat,
)

from Backend.Core.pdf_validation import compare_page_evidence, extract_pdf_evidence
from tools.build_supported_layout_masters import REFERENCES

ROOT = Path(__file__).resolve().parents[1]
LINE_MARK = re.compile(
    r"(?:\[|\()(\d{1,2})(?:\s+marks?)?(?:\]|\))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
STRUCTURAL_GRID_DPI = 12
CONTACT_PAGE_WIDTH = 240
CONTACT_PAGES_PER_SHEET = 8
OVERVIEW_DOCUMENTS_PER_SHEET = 6
KNOWN_REFERENCE_MUPDF_DIAGNOSTICS = {
    "bogus font ascent/descent values (3117 / -2464)",
    "format error: No common ancestor in structure tree",
    "premature end of data in flate filter",
    "Repairing missing parent (P) in parent tree nodes",
    "structure tree broken, assume tree is missing",
}
ROLE_WEIGHTS = {
    "cover": {"structural": 0.5, "perceptual": 0.3, "print": 0.2},
    "question_content": {"structural": 0.4, "perceptual": 0.3, "print": 0.3},
    "mark_scheme_content": {"structural": 0.4, "perceptual": 0.3, "print": 0.3},
    "additional_answer": {"structural": 0.45, "perceptual": 0.3, "print": 0.25},
    "ruled_continuation": {"structural": 0.45, "perceptual": 0.3, "print": 0.25},
    "intentional_blank": {"structural": 0.7, "perceptual": 0.2, "print": 0.1},
    "end_page": {"structural": 0.55, "perceptual": 0.3, "print": 0.15},
}

GENERATED_DOCUMENTS = {
    "accounting_aqa": (
        "aqa-accounting",
        "aqa-accounting-paper-{paper}-question-paper.pdf",
        "aqa-accounting-paper-{paper}-mark-scheme.pdf",
    ),
    "business_aqa": (
        "aqa-business",
        "aqa-business-paper-{paper}-question-paper.pdf",
        "aqa-business-paper-{paper}-mark-scheme.pdf",
    ),
    "economics_aqa": (
        "aqa-economics",
        "aqa-economics-paper-{paper}-question-paper.pdf",
        "aqa-economics-paper-{paper}-mark-scheme.pdf",
    ),
    "computer_science": (
        "aqa-computer-science",
        "cs-paper-{paper}-question-paper.pdf",
        "cs-paper-{paper}-mark-scheme.pdf",
    ),
    "computer_science_ocr": (
        "ocr-computer-science",
        "ocr-computer-science-paper-{paper}-question-paper.pdf",
        "ocr-computer-science-paper-{paper}-mark-scheme.pdf",
    ),
    "economics_ocr": (
        "ocr-economics",
        "ocr-economics-paper-{paper}-question-paper.pdf",
        "ocr-economics-paper-{paper}-mark-scheme.pdf",
    ),
    "economics": (
        "edexcel-economics",
        "paper-{paper}-question-paper.pdf",
        "paper-{paper}-mark-scheme.pdf",
    ),
}

FAMILIES: dict[str, dict[str, str]] = {}
for (subject, paper), (
    family,
    reference_question,
    reference_scheme,
) in REFERENCES.items():
    generated_dir, question_name, scheme_name = GENERATED_DOCUMENTS[subject]
    FAMILIES[f"{family}-paper-{paper}"] = {
        "generated_dir": generated_dir,
        "question": question_name.format(paper=paper),
        "scheme": scheme_name.format(paper=paper),
        "reference_question": f"Reference Corpus/a-level/{reference_question}",
        "reference_scheme": f"Reference Corpus/a-level/{reference_scheme}",
    }


def _reference_peers(reference: Path, *, maximum: int = 3) -> list[Path]:
    """Return same-paper documents from different sessions, newest first.

    Board archives use unrelated naming schemes, so matching is intentionally
    conservative. A false peer is worse than a smaller evidence range.
    """

    if maximum < 1:
        raise ValueError("maximum reference peers must be positive")
    name = reference.name.casefold()
    candidates = [
        path
        for path in reference.parent.iterdir()
        if path.is_file() and path.suffix.casefold() == ".pdf"
    ]
    aqa = re.search(r"aqa-(\d{5})-(qp|ms)-", name)
    edexcel = re.search(r"9ec0[-_](0[123])[-_](que|rms)", name)
    ocr = re.search(r"-(question-paper|mark-scheme)-(.+)\.pdf$", name)
    if aqa:
        token = f"aqa-{aqa.group(1)}-{aqa.group(2)}-"
        candidates = [path for path in candidates if token in path.name.casefold()]
    elif edexcel:
        paper, kind = edexcel.groups()
        candidates = [
            path
            for path in candidates
            if re.search(
                rf"9ec0[-_]{paper}[-_]{kind}",
                path.name.casefold(),
            )
        ]
    elif ocr:
        kind, title = ocr.groups()
        token = f"-{kind}-{title}.pdf"
        candidates = [
            path for path in candidates if path.name.casefold().endswith(token)
        ]
    else:
        candidates = [reference]
    ordered = sorted(candidates, key=lambda path: path.name.casefold(), reverse=True)
    if reference in ordered:
        ordered.remove(reference)
    return [reference, *ordered][:maximum]


@dataclass(frozen=True)
class PageEvidence:
    index: int
    role: str
    content_box: tuple[float, float, float, float] | None
    source: str | None = None
    geometry: dict[str, Any] | None = None


@dataclass(frozen=True)
class RoleMatch:
    generated_index: int
    reference_index: int
    role: str
    score: float
    reference_source: str | None = None


@dataclass(frozen=True)
class PrintProfile:
    dpi: int
    scale_percent: int
    non_printable_margin_mm: float
    monochrome: bool
    minimum_rule_pt: float
    minimum_contrast_ratio: float
    minimum_reading_order_score: float
    require_embedded_fonts: bool
    require_tags: bool


def load_print_profile(path: Path, name: str) -> PrintProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported print profile schema")
    try:
        value = payload["profiles"][name]
    except KeyError as error:
        raise ValueError(f"unknown print profile: {name}") from error
    profile = PrintProfile(
        dpi=int(value["dpi"]),
        scale_percent=int(value["scale_percent"]),
        non_printable_margin_mm=float(value["non_printable_margin_mm"]),
        monochrome=bool(value["monochrome"]),
        minimum_rule_pt=float(value["minimum_rule_pt"]),
        minimum_contrast_ratio=float(value["minimum_contrast_ratio"]),
        minimum_reading_order_score=float(value["minimum_reading_order_score"]),
        require_embedded_fonts=bool(value["require_embedded_fonts"]),
        require_tags=bool(value["require_tags"]),
    )
    if (
        profile.dpi <= 0
        or profile.scale_percent != 100
        or profile.non_printable_margin_mm < 0
        or profile.minimum_rule_pt <= 0
        or profile.minimum_contrast_ratio < 1
        or not 0 <= profile.minimum_reading_order_score <= 1
    ):
        raise ValueError(f"invalid print profile: {name}")
    return profile


def _print_policy_failures(
    evidence: dict[str, Any],
    profile: PrintProfile,
) -> list[str]:
    failures: list[str] = []
    if profile.require_tags and not evidence["tagged"]:
        failures.append("document has no PDF structure tree")
    if profile.require_embedded_fonts:
        missing = [
            item["embedded_name"] for item in evidence["fonts"] if not item["embedded"]
        ]
        if missing:
            failures.append("unembedded fonts: " + ", ".join(sorted(set(missing))))
    for page in evidence["pages"]:
        number = page["page"]
        if not page["safe_print"]:
            failures.append(f"page {number} crosses the safe-print boundary")
        if page["reading_order_score"] < profile.minimum_reading_order_score:
            failures.append(f"page {number} has unstable reading order")
        if (
            profile.monochrome
            and page["monochrome_minimum_contrast"] < profile.minimum_contrast_ratio
        ):
            failures.append(f"page {number} has insufficient monochrome contrast")
        rule_width = page["minimum_rule_width"]
        if rule_width is not None and rule_width < profile.minimum_rule_pt:
            failures.append(
                f"page {number} contains a {rule_width:g} pt rule below the "
                f"{profile.minimum_rule_pt:g} pt print minimum"
            )
    return failures


class PageRoleMatcher:
    @staticmethod
    def match(
        generated: PageEvidence,
        references: list[PageEvidence],
    ) -> RoleMatch:
        candidates = [item for item in references if item.role == generated.role]
        if not candidates:
            candidates = references
        if not candidates:
            raise ValueError("at least one reference page is required")

        def score(reference: PageEvidence) -> float:
            role_score = 1.0 if reference.role == generated.role else 0.0
            geometry_score = _content_box_similarity(
                generated.content_box,
                reference.content_box,
            )
            if generated.geometry and reference.geometry:
                measured = _geometry_scores(
                    [generated.geometry],
                    [reference.geometry],
                )
                detailed_geometry = statistics.mean(
                    float(measured[name])
                    for name in (
                        "render_placement",
                        "text_placement",
                        "drawing_placement",
                        "content_envelope",
                    )
                )
            else:
                detailed_geometry = geometry_score
            distance_score = 1 / (1 + abs(generated.index - reference.index))
            return (
                role_score * 0.62
                + detailed_geometry * 0.28
                + geometry_score * 0.07
                + distance_score * 0.03
            )

        reference = max(candidates, key=lambda item: (score(item), -item.index))
        return RoleMatch(
            generated_index=generated.index,
            reference_index=reference.index,
            role=generated.role,
            score=round(score(reference), 4),
            reference_source=reference.source,
        )


def _role_matches(
    generated: list[PageEvidence],
    references: list[PageEvidence],
) -> list[RoleMatch]:
    available = list(references)
    matches: list[RoleMatch] = []
    matched_generated: set[int] = set()

    def assign(page: PageEvidence) -> None:
        nonlocal available
        match = PageRoleMatcher.match(page, available)
        matches.append(match)
        matched_generated.add(page.index)
        available = [
            item
            for item in available
            if (item.source, item.index)
            != (match.reference_source, match.reference_index)
        ]

    # Reserve scarce semantic roles before pages without a same-role reference
    # are allowed to use geometry-only fallback matches.
    for page in generated:
        if not available:
            break
        if any(reference.role == page.role for reference in available):
            assign(page)
    for page in generated:
        if not available:
            break
        if page.index not in matched_generated:
            assign(page)
    return sorted(matches, key=lambda item: item.generated_index)


def _content_box_similarity(
    first: tuple[float, float, float, float] | None,
    second: tuple[float, float, float, float] | None,
) -> float:
    if first is None and second is None:
        return 1.0
    if first is None or second is None:
        return 0.0
    difference = statistics.mean(
        abs(left - right) for left, right in zip(first, second, strict=True)
    )
    return max(0.0, 1.0 - difference / 0.12)


def _grid_dimensions(*, width: float, height: float, dpi: int) -> tuple[int, int]:
    if width <= 0 or height <= 0 or dpi <= 0:
        raise ValueError("page dimensions and structural DPI must be positive")
    return max(1, round(width * dpi / 72)), max(1, round(height * dpi / 72))


def _median(values: list[float]) -> float:
    return round(statistics.median(values), 2) if values else 0.0


def _font_inventory(
    counts: Counter[tuple[str, float]],
) -> list[dict[str, Any]]:
    return [
        {"family": family, "size": size, "characters": count}
        for (family, size), count in counts.most_common(8)
    ]


def _mark_grid(
    grid: list[int],
    bbox: tuple[float, float, float, float],
    width: float,
    height: float,
    columns: int,
    rows: int,
) -> None:
    x0, y0, x1, y1 = bbox
    left = max(0, min(columns - 1, int(x0 / width * columns)))
    right = max(left + 1, min(columns, math.ceil(x1 / width * columns)))
    top = max(0, min(rows - 1, int(y0 / height * rows)))
    bottom = max(top + 1, min(rows, math.ceil(y1 / height * rows)))
    for row in range(top, bottom):
        start = row * columns
        for column in range(left, right):
            grid[start + column] = 1


def _geometry_page(
    page: fitz.Page,
    allowed_diagnostics: frozenset[str],
    *,
    text_boxes: list[tuple[float, float, float, float]],
    page_drawings: list[dict[str, Any]],
    page_images: list[dict[str, Any]],
) -> dict[str, Any]:
    width = page.rect.width
    height = page.rect.height
    columns, rows = _grid_dimensions(
        width=width,
        height=height,
        dpi=STRUCTURAL_GRID_DPI,
    )
    text_grid = [0] * (columns * rows)
    drawing_grid = [0] * (columns * rows)
    image_grid = [0] * (columns * rows)
    content_boxes: list[tuple[float, float, float, float]] = []
    for bbox in text_boxes:
        content_boxes.append(bbox)
        _mark_grid(text_grid, bbox, width, height, columns, rows)
    for drawing in page_drawings:
        rect = drawing.get("rect")
        if rect:
            _mark_grid(drawing_grid, tuple(rect), width, height, columns, rows)
    for image in page_images:
        _mark_grid(image_grid, tuple(image["bbox"]), width, height, columns, rows)
    ink_grid = [
        int(text or drawing or image)
        for text, drawing, image in zip(
            text_grid,
            drawing_grid,
            image_grid,
            strict=True,
        )
    ]
    pixmap = _render_page_pixmap(
        page,
        width,
        height,
        allowed_diagnostics,
        columns=columns,
        rows=rows,
    )
    render_grid = [255 - value for value in pixmap.samples]
    content_box = None
    if content_boxes:
        content_box = [
            round(min(box[0] for box in content_boxes) / width, 4),
            round(min(box[1] for box in content_boxes) / height, 4),
            round(max(box[2] for box in content_boxes) / width, 4),
            round(max(box[3] for box in content_boxes) / height, 4),
        ]
    return {
        "media_box": [round(float(value), 2) for value in page.mediabox],
        "crop_box": [round(float(value), 2) for value in page.cropbox],
        "content_box": content_box,
        "grid_size": [columns, rows],
        "text_grid": text_grid,
        "drawing_grid": drawing_grid,
        "image_grid": image_grid,
        "ink_grid": ink_grid,
        "render_grid": render_grid,
    }


def _render_page_pixmap(
    page: fitz.Page,
    width: float,
    height: float,
    allowed_diagnostics: frozenset[str],
    *,
    columns: int | None = None,
    rows: int | None = None,
) -> fitz.Pixmap:
    """Render static paper content and reject unknown MuPDF diagnostics."""

    if columns is None or rows is None:
        columns, rows = _grid_dimensions(
            width=width,
            height=height,
            dpi=STRUCTURAL_GRID_DPI,
        )
    show_errors = bool(fitz.TOOLS.mupdf_display_errors())
    show_warnings = bool(fitz.TOOLS.mupdf_display_warnings())
    diagnostics = ""
    fitz.TOOLS.reset_mupdf_warnings()
    fitz.TOOLS.mupdf_display_errors(False)
    fitz.TOOLS.mupdf_display_warnings(False)
    try:
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(columns / width, rows / height),
            colorspace=fitz.csGRAY,
            alpha=False,
            annots=True,
        )
    finally:
        diagnostics = fitz.TOOLS.mupdf_warnings()
        fitz.TOOLS.reset_mupdf_warnings()
        fitz.TOOLS.mupdf_display_errors(show_errors)
        fitz.TOOLS.mupdf_display_warnings(show_warnings)

    unexpected = {
        line
        for line in diagnostics.splitlines()
        if line not in allowed_diagnostics
        and not re.fullmatch(r"\.\.\. repeated \d+ times\.\.\.", line)
    }
    if unexpected:
        raise RuntimeError(
            "MuPDF could not render a paper cleanly: " + "; ".join(sorted(unexpected))
        )
    return pixmap


def profile(
    path: Path,
    *,
    tolerate_reference_diagnostics: bool = False,
) -> dict[str, Any]:
    document = fitz.open(path)
    allowed_diagnostics = (
        frozenset(KNOWN_REFERENCE_MUPDF_DIAGNOSTICS)
        if tolerate_reference_diagnostics
        else frozenset()
    )
    texts: list[str] = []
    left: list[float] = []
    top: list[float] = []
    right: list[float] = []
    bottom: list[float] = []
    drawings: list[int] = []
    images: list[int] = []
    geometry: list[dict[str, Any]] = []
    font_counts: Counter[tuple[str, float]] = Counter()
    for page in document:
        text = page.get_text("text")
        texts.append(text)
        text_boxes: list[tuple[float, float, float, float]] = []
        for block in page.get_text("dict").get("blocks", []):
            has_text = False
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if span_text.strip():
                        has_text = True
                        font_counts[
                            (
                                span.get("font", "unknown"),
                                round(span.get("size", 0), 1),
                            )
                        ] += len(span_text)
            if has_text:
                text_boxes.append(tuple(float(value) for value in block["bbox"]))
        if text_boxes:
            left.append(min(block[0] for block in text_boxes))
            top.append(min(block[1] for block in text_boxes))
            right.append(page.rect.width - max(block[2] for block in text_boxes))
            bottom.append(page.rect.height - max(block[3] for block in text_boxes))
        page_drawings = page.get_drawings()
        page_images = page.get_image_info(hashes=False)
        drawings.append(len(page_drawings))
        images.append(len(page.get_images(full=True)))
        geometry.append(
            _geometry_page(
                page,
                allowed_diagnostics,
                text_boxes=text_boxes,
                page_drawings=page_drawings,
                page_images=page_images,
            )
        )
    full_text = "\n".join(texts)
    result = {
        "pages": len(document),
        "page_size": {
            "width": round(document[0].rect.width, 2),
            "height": round(document[0].rect.height, 2),
        },
        "text_margins": {
            "left": _median(left),
            "top": _median(top),
            "right": _median(right),
            "bottom": _median(bottom),
        },
        "word_count": len(WORD.findall(full_text)),
        "printed_mark_sequence": [int(value) for value in LINE_MARK.findall(full_text)],
        "drawings_per_page": _median([float(value) for value in drawings]),
        "images_per_page": _median([float(value) for value in images]),
        "graphics_cells_per_page": _median(
            [float(sum(page["render_grid"]) / 255) for page in geometry]
        ),
        "fonts": _font_inventory(font_counts),
        "geometry": geometry,
    }
    document.close()
    return result


def _ratio_score(first: float, second: float) -> float:
    if first == second == 0:
        return 1.0
    if first <= 0 or second <= 0:
        return 0.0
    return min(first, second) / max(first, second)


def _sequence_score(generated: list[int], reference: list[int]) -> float | None:
    if not generated or not reference:
        return None
    row = [0] * (len(reference) + 1)
    for left_value in generated:
        previous = 0
        for index, right_value in enumerate(reference, 1):
            saved = row[index]
            row[index] = (
                previous + 1
                if left_value == right_value
                else max(row[index], row[index - 1])
            )
            previous = saved
    return row[-1] / max(len(generated), len(reference))


def _grid_similarity(first: list[int], second: list[int]) -> float:
    first_total = sum(first)
    second_total = sum(second)
    if first_total == second_total == 0:
        return 1.0
    intersection = sum(
        left and right for left, right in zip(first, second, strict=True)
    )
    return 2 * intersection / max(first_total + second_total, 1)


def _shade_similarity(first: list[int], second: list[int]) -> float:
    first_energy = sum(value * value for value in first)
    second_energy = sum(value * value for value in second)
    if first_energy == second_energy == 0:
        return 1.0
    if first_energy == 0 or second_energy == 0:
        return 0.0
    shared = sum(left * right for left, right in zip(first, second, strict=True))
    return shared / math.sqrt(first_energy * second_energy)


def _geometry_scores(
    generated: list[dict[str, Any]],
    reference: list[dict[str, Any]],
) -> dict[str, float]:
    pairs = list(zip(generated, reference))
    if not pairs:
        return {
            "page_boxes": 0.0,
            "text_placement": 0.0,
            "drawing_placement": 0.0,
            "image_placement": 0.0,
            "ink_placement": 0.0,
            "render_placement": 0.0,
            "content_envelope": 0.0,
        }
    page_boxes = []
    text = []
    drawings = []
    images = []
    ink = []
    render = []
    envelopes = []
    for left, right in pairs:
        page_boxes.append(
            float(
                all(
                    abs(a - b) <= 0.1
                    for name in ("media_box", "crop_box")
                    for a, b in zip(left[name], right[name], strict=True)
                )
            )
        )
        text.append(_grid_similarity(left["text_grid"], right["text_grid"]))
        drawings.append(_grid_similarity(left["drawing_grid"], right["drawing_grid"]))
        images.append(_grid_similarity(left["image_grid"], right["image_grid"]))
        ink.append(_grid_similarity(left["ink_grid"], right["ink_grid"]))
        render.append(_shade_similarity(left["render_grid"], right["render_grid"]))
        if left["content_box"] and right["content_box"]:
            difference = statistics.mean(
                abs(a - b)
                for a, b in zip(left["content_box"], right["content_box"], strict=True)
            )
            envelopes.append(max(0.0, 1.0 - difference / 0.12))
        elif left["content_box"] == right["content_box"]:
            envelopes.append(1.0)
        else:
            envelopes.append(0.0)
    return {
        "page_boxes": statistics.mean(page_boxes),
        "text_placement": statistics.mean(text),
        "drawing_placement": statistics.mean(drawings),
        "image_placement": statistics.mean(images),
        "ink_placement": statistics.mean(ink),
        "render_placement": statistics.mean(render),
        "content_envelope": statistics.mean(envelopes),
    }


def compare(generated: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    margin_scores = [
        _ratio_score(generated["text_margins"][side], reference["text_margins"][side])
        for side in ("left", "top", "right", "bottom")
    ]
    generated_sizes = {item["size"] for item in generated["fonts"][:5]}
    reference_sizes = {item["size"] for item in reference["fonts"][:5]}
    size_overlap = len(generated_sizes & reference_sizes) / max(
        len(generated_sizes | reference_sizes), 1
    )
    generated_families = {
        _font_family(item["family"]) for item in generated["fonts"][:5]
    }
    reference_families = {
        _font_family(item["family"]) for item in reference["fonts"][:5]
    }
    family_overlap = len(generated_families & reference_families) / max(
        len(generated_families | reference_families), 1
    )
    scores = {
        "page_count": _ratio_score(generated["pages"], reference["pages"]),
        "word_count": _ratio_score(generated["word_count"], reference["word_count"]),
        "mark_pattern": _sequence_score(
            generated["printed_mark_sequence"], reference["printed_mark_sequence"]
        ),
        "text_margins": sum(margin_scores) / len(margin_scores),
        "font_families": family_overlap,
        "font_sizes": size_overlap,
        "graphics_density": _ratio_score(
            generated["graphics_cells_per_page"],
            reference["graphics_cells_per_page"],
        ),
        **_geometry_scores(generated["geometry"], reference["geometry"]),
    }
    weights = {
        "page_count": 0.1,
        "word_count": 0.08,
        "mark_pattern": 0.14,
        "text_margins": 0.06,
        "font_families": 0.04,
        "font_sizes": 0.04,
        "graphics_density": 0.04,
        "page_boxes": 0.12,
        "ink_placement": 0.0,
        "render_placement": 0.21,
        "text_placement": 0.09,
        "drawing_placement": 0.0,
        "image_placement": 0.0,
        "content_envelope": 0.08,
    }
    available = {name: value for name, value in scores.items() if value is not None}
    available_weight = sum(weights[name] for name in available)
    return {
        "scores": {
            name: round(value, 3) if value is not None else None
            for name, value in scores.items()
        },
        "overall": round(
            sum(value * weights[name] for name, value in available.items())
            / available_weight,
            3,
        ),
        "top_generated_fonts": generated["fonts"][:3],
        "top_reference_fonts": reference["fonts"][:3],
    }


def _compact_profile(value: dict[str, Any]) -> dict[str, Any]:
    """Keep report JSON useful without serialising page raster grids.

    The former report embedded six grids per page and reached multiple
    gigabytes for the supported matrix. Geometry remains in memory while
    comparing, then only compact page scores and document summaries are saved.
    """

    return {key: item for key, item in value.items() if key != "geometry"}


def _page_comparisons(
    generated: list[dict[str, Any]],
    reference: list[dict[str, Any]],
    matches: list[RoleMatch] | None = None,
    reference_sources: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if matches is None:
        matches = [
            RoleMatch(index, index, "unclassified", 1.0)
            for index in range(min(len(generated), len(reference)))
        ]
    paired_generated = {item.generated_index for item in matches}
    paired_reference = {
        (item.reference_source, item.reference_index) for item in matches
    }
    for match in matches:
        left = generated[match.generated_index]
        right_pages = (
            reference_sources.get(match.reference_source, reference)
            if reference_sources and match.reference_source
            else reference
        )
        right = right_pages[match.reference_index]
        scores = _geometry_scores([left], [right])
        scored = {
            "render_placement": scores["render_placement"],
            "text_placement": scores["text_placement"],
            "drawing_placement": scores["drawing_placement"],
            "image_placement": scores["image_placement"],
            "content_envelope": scores["content_envelope"],
        }
        result.append(
            {
                "page": match.generated_index + 1,
                "reference_page": match.reference_index + 1,
                "reference_path": match.reference_source,
                "role_match_score": match.score,
                "overall": round(statistics.mean(scored.values()), 3),
                "scores": {name: round(value, 3) for name, value in scored.items()},
            }
        )
    for index in range(len(generated)):
        if index not in paired_generated:
            result.append(
                {
                    "page": index + 1,
                    "missing": "reference",
                    "overall": 0.0,
                }
            )
    if not reference_sources:
        next_page = len(generated) + 1
        for index in range(len(reference)):
            if (None, index) in paired_reference:
                continue
            result.append(
                {
                    "page": next_page,
                    "reference_page": index + 1,
                    "missing": "generated",
                    "overall": 0.0,
                }
            )
            next_page += 1
    return sorted(result, key=lambda item: int(item["page"]))


def classify_page_role(
    text: str,
    *,
    document_role: str,
    page_number: int,
) -> str:
    """Classify stable page furniture without retaining source-paper text."""

    if page_number == 1:
        return "cover"
    words = " ".join(WORD.findall(text.casefold()))
    if "end of question paper" in words:
        return "end_page"
    if "additional page" in words or "extra answer space" in words:
        return "additional_answer"
    if (
        "blank page" in words
        or "there are no questions printed on this page" in words
        or "do not write on this page" in words
    ):
        return "intentional_blank"
    if "continued" in words:
        return "ruled_continuation"
    return (
        "mark_scheme_content" if document_role == "mark_scheme" else "question_content"
    )


def _document_page_roles(path: Path, document_role: str) -> list[str]:
    with fitz.open(path) as document:
        roles = []
        for index, page in enumerate(document, start=1):
            text = page.get_text("text")
            role = classify_page_role(
                text,
                document_role=document_role,
                page_number=index,
            )
            words = WORD.findall(text)
            if (
                index > 1
                and document_role == "question_paper"
                and role == "question_content"
                and len(words) < 100
                and _full_width_horizontal_rules(page) >= 10
            ):
                role = "ruled_continuation"
            if role == "mark_scheme_content" and any(
                phrase in text.casefold()
                for phrase in (
                    "need to get in touch",
                    "cambridge university press",
                    "independent practice material",
                )
            ):
                role = "end_page"
            roles.append(role)
        return roles


def _full_width_horizontal_rules(page: fitz.Page) -> int:
    count = 0
    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue
            start, end = item[1], item[2]
            if (
                abs(start.y - end.y) < 0.5
                and abs(start.x - end.x) >= page.rect.width * 0.65
            ):
                count += 1
    return count


def _role_scores(pages: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for page in pages:
        grouped.setdefault(str(page["role"]), []).append(page)
    result: dict[str, dict[str, float | int]] = {}
    metrics = (
        "overall",
        "structural_overall",
        "perceptual_overall",
        "qualified_overall",
        "print_overall",
        "registered_masked_render",
        "registered_text_layout",
        "stable_area",
    )
    for role, role_pages in sorted(grouped.items()):
        summary: dict[str, float | int] = {"pages": len(role_pages)}
        for metric in metrics:
            values = [float(page[metric]) for page in role_pages if metric in page]
            if values:
                summary[metric] = round(statistics.mean(values), 4)
        result[role] = summary
    return result


def _normalised_block_text(value: str) -> str:
    return " ".join(WORD.findall(value.casefold()))


def _text_blocks(page: fitz.Page) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for block in page.get_text("blocks"):
        text = _normalised_block_text(str(block[4]))
        if not text:
            continue
        result.append(
            {
                "bbox": tuple(float(value) for value in block[:4]),
                "text": text,
            }
        )
    return result


def _grayscale_page(page: fitz.Page, dpi: int) -> Image.Image:
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(dpi / 72, dpi / 72),
        colorspace=fitz.csGRAY,
        alpha=False,
        annots=True,
    )
    return Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)


def _translated(
    image: Image.Image,
    *,
    offset_x: int,
    offset_y: int,
    fill: int = 255,
) -> Image.Image:
    translated = Image.new(image.mode, image.size, fill)
    translated.paste(image, (offset_x, offset_y))
    return translated


def _registration_shift(
    reference: Image.Image,
    generated: Image.Image,
    *,
    dpi: int,
) -> tuple[int, int]:
    """Find a small whole-page translation without deforming either page."""

    generated = generated.resize(reference.size, Image.Resampling.LANCZOS)
    thumbnail_width = min(420, reference.width)
    scale = thumbnail_width / reference.width
    thumbnail_size = (
        thumbnail_width,
        max(1, round(reference.height * scale)),
    )
    reference_edge = (
        reference.resize(thumbnail_size, Image.Resampling.LANCZOS)
        .filter(ImageFilter.GaussianBlur(0.6))
        .filter(ImageFilter.FIND_EDGES)
    )
    generated_edge = (
        generated.resize(thumbnail_size, Image.Resampling.LANCZOS)
        .filter(ImageFilter.GaussianBlur(0.6))
        .filter(ImageFilter.FIND_EDGES)
    )
    maximum = max(1, round(7 * dpi / 72 * scale))
    coarse = sorted({-maximum, -maximum // 2, 0, maximum // 2, maximum})

    def error(offset_x: int, offset_y: int) -> float:
        moved = _translated(
            generated_edge,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        border = maximum + 2
        box = (
            border,
            border,
            reference_edge.width - border,
            reference_edge.height - border,
        )
        difference = ImageChops.difference(
            reference_edge.crop(box),
            moved.crop(box),
        )
        return ImageStat.Stat(difference).mean[0]

    candidates = [
        (error(offset_x, offset_y), offset_x, offset_y)
        for offset_x in coarse
        for offset_y in coarse
    ]
    _score, best_x, best_y = min(candidates)
    refined = [
        (error(offset_x, offset_y), offset_x, offset_y)
        for offset_x in range(max(-maximum, best_x - 1), min(maximum, best_x + 1) + 1)
        for offset_y in range(max(-maximum, best_y - 1), min(maximum, best_y + 1) + 1)
    ]
    _score, best_x, best_y = min(refined)
    full_scale = 1 / scale
    return round(best_x * full_scale), round(best_y * full_scale)


def _block_mask(
    size: tuple[int, int],
    blocks: list[dict[str, Any]],
    page_rect: fitz.Rect,
    *,
    fill: int,
    background: int,
    padding: int = 2,
) -> Image.Image:
    mask = Image.new("L", size, background)
    draw = ImageDraw.Draw(mask)
    scale_x = size[0] / page_rect.width
    scale_y = size[1] / page_rect.height
    for block in blocks:
        x0, y0, x1, y1 = block["bbox"]
        draw.rectangle(
            (
                round(x0 * scale_x) - padding,
                round(y0 * scale_y) - padding,
                round(x1 * scale_x) + padding,
                round(y1 * scale_y) + padding,
            ),
            fill=fill,
        )
    return mask


def _unstable_blocks(
    first: list[dict[str, Any]],
    second: list[dict[str, Any]],
    *,
    first_rect: fitz.Rect,
    second_rect: fitz.Rect,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Mask question-specific prose while keeping matching boilerplate visible."""

    def is_stable(
        block: dict[str, Any],
        candidates: list[dict[str, Any]],
        source_rect: fitz.Rect,
        candidate_rect: fitz.Rect,
    ) -> bool:
        text = block["text"]
        if len(text) < 5:
            return False
        x0, y0, x1, y1 = block["bbox"]
        centre = ((x0 + x1) / 2 / source_rect.width, (y0 + y1) / 2 / source_rect.height)
        for candidate in candidates:
            if candidate["text"] != text:
                continue
            cx0, cy0, cx1, cy1 = candidate["bbox"]
            candidate_centre = (
                (cx0 + cx1) / 2 / candidate_rect.width,
                (cy0 + cy1) / 2 / candidate_rect.height,
            )
            if (
                abs(centre[0] - candidate_centre[0]) <= 0.04
                and abs(centre[1] - candidate_centre[1]) <= 0.04
            ):
                return True
        return False

    return (
        [
            block
            for block in first
            if not is_stable(block, second, first_rect, second_rect)
        ],
        [
            block
            for block in second
            if not is_stable(block, first, second_rect, first_rect)
        ],
    )


def _mask_mean(mask: Image.Image) -> float:
    return ImageStat.Stat(mask).mean[0] / 255


def _dice_masks(first: Image.Image, second: Image.Image) -> float:
    first_total = sum(index * count for index, count in enumerate(first.histogram()))
    second_total = sum(index * count for index, count in enumerate(second.histogram()))
    if first_total == second_total == 0:
        return 1.0
    shared = ImageChops.multiply(first, second)
    shared_total = sum(index * count for index, count in enumerate(shared.histogram()))
    return 2 * shared_total / max(first_total + second_total, 1)


def _registered_page_comparison(
    reference_page: fitz.Page,
    generated_page: fitz.Page,
    *,
    dpi: int,
) -> dict[str, Any]:
    reference = _grayscale_page(reference_page, dpi)
    generated = _grayscale_page(generated_page, dpi).resize(
        reference.size,
        Image.Resampling.LANCZOS,
    )
    offset_x, offset_y = _registration_shift(reference, generated, dpi=dpi)
    registered = _translated(
        generated,
        offset_x=offset_x,
        offset_y=offset_y,
    )
    reference_blocks = _text_blocks(reference_page)
    generated_blocks = _text_blocks(generated_page)
    unstable_reference, unstable_generated = _unstable_blocks(
        reference_blocks,
        generated_blocks,
        first_rect=reference_page.rect,
        second_rect=generated_page.rect,
    )
    comparison_mask = Image.new("L", reference.size, 255)
    reference_variable = _block_mask(
        reference.size,
        unstable_reference,
        reference_page.rect,
        fill=0,
        background=255,
        padding=max(2, round(dpi / 36)),
    )
    generated_variable = _block_mask(
        reference.size,
        unstable_generated,
        generated_page.rect,
        fill=0,
        background=255,
        padding=max(2, round(dpi / 36)),
    )
    generated_variable = _translated(
        generated_variable,
        offset_x=offset_x,
        offset_y=offset_y,
        fill=0,
    )
    comparison_mask = ImageChops.multiply(
        comparison_mask,
        ImageChops.multiply(reference_variable, generated_variable),
    )
    # Ignore the sliver introduced by registration rather than treating it as
    # missing design content.
    valid_area = Image.new("L", reference.size, 255)
    valid_area = _translated(
        valid_area,
        offset_x=offset_x,
        offset_y=offset_y,
        fill=0,
    )
    comparison_mask = ImageChops.multiply(comparison_mask, valid_area)
    reference_blurred = reference.filter(ImageFilter.GaussianBlur(dpi / 144))
    registered_blurred = registered.filter(ImageFilter.GaussianBlur(dpi / 144))
    difference = ImageChops.difference(reference_blurred, registered_blurred)
    rms = ImageStat.Stat(difference, mask=comparison_mask).rms[0]
    render_similarity = max(0.0, 1 - rms / 255)

    reference_layout = _block_mask(
        reference.size,
        reference_blocks,
        reference_page.rect,
        fill=255,
        background=0,
    )
    generated_layout = _block_mask(
        reference.size,
        generated_blocks,
        generated_page.rect,
        fill=255,
        background=0,
    )
    generated_layout = _translated(
        generated_layout,
        offset_x=offset_x,
        offset_y=offset_y,
        fill=0,
    )
    return {
        "registered_masked_render": round(render_similarity, 4),
        "registered_text_layout": round(
            _dice_masks(reference_layout, generated_layout),
            4,
        ),
        "stable_area": round(_mask_mean(comparison_mask), 4),
        "registration_points": [
            round(offset_x * 72 / dpi, 2),
            round(offset_y * 72 / dpi, 2),
        ],
    }


def _perceptual_page_comparisons(
    generated_path: Path,
    reference_path: Path,
    *,
    dpi: int,
    matches: list[RoleMatch] | None = None,
    reference_paths: dict[str, Path] | None = None,
) -> list[dict[str, Any]]:
    if dpi <= 0:
        return []
    with fitz.open(generated_path) as generated:
        with fitz.open(reference_path) as default_reference:
            default_reference_count = default_reference.page_count
        pairs = matches or [
            RoleMatch(index, index, "unclassified", 1.0)
            for index in range(min(generated.page_count, default_reference_count))
        ]
        documents: dict[str, fitz.Document] = {}
        try:
            result = []
            for match in pairs:
                source = match.reference_source or str(reference_path)
                path = (reference_paths or {}).get(source, Path(source))
                reference = documents.setdefault(source, fitz.open(path))
                result.append(
                    {
                        "page": match.generated_index + 1,
                        "reference_page": match.reference_index + 1,
                        "reference_path": source,
                        **_registered_page_comparison(
                            reference[match.reference_index],
                            generated[match.generated_index],
                            dpi=dpi,
                        ),
                    }
                )
            return result
        finally:
            for document in documents.values():
                document.close()


def _font_family(name: str) -> str:
    value = name.casefold().replace("psmt", "").replace("mt", "")
    for suffix in ("-bolditalic", "-bold", "-italic", "-regular", "-0", "-1"):
        value = value.replace(suffix, "")
    value = value.replace(" ", "")
    return {
        "arimo": "arial",
        "tinos": "timesnewroman",
        "timesnewromanps": "timesnewroman",
    }.get(value, value)


def audit(
    generated_root: Path,
    *,
    perceptual_dpi: int = 0,
    print_profile: PrintProfile | None = None,
) -> dict[str, Any]:
    families: dict[str, Any] = {}
    for family, paths in FAMILIES.items():
        generated_dir = generated_root / paths["generated_dir"]
        generated_question = _generated_document(
            generated_dir,
            paths["question"],
            search_root=generated_root,
        )
        generated_scheme = _generated_document(
            generated_dir,
            paths["scheme"],
            search_root=generated_root,
        )
        reference_question = ROOT / paths["reference_question"]
        reference_scheme = ROOT / paths["reference_scheme"]
        required = [
            generated_question,
            generated_scheme,
            reference_question,
            reference_scheme,
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            families[family] = {"missing": missing}
            continue
        question_references = _reference_peers(reference_question, maximum=3)
        scheme_references = _reference_peers(reference_scheme, maximum=3)
        question_profiles = {
            "generated": profile(generated_question),
            "reference": profile(
                reference_question,
                tolerate_reference_diagnostics=True,
            ),
            "reference_sources": {
                str(path): profile(path, tolerate_reference_diagnostics=True)
                for path in question_references
            },
        }
        scheme_profiles = {
            "generated": profile(generated_scheme),
            "reference": profile(
                reference_scheme,
                tolerate_reference_diagnostics=True,
            ),
            "reference_sources": {
                str(path): profile(path, tolerate_reference_diagnostics=True)
                for path in scheme_references
            },
        }
        families[family] = {
            "question_paper": _document_result(
                generated_question,
                reference_question,
                question_profiles,
                perceptual_dpi=perceptual_dpi,
                reference_paths=question_references,
                print_profile=print_profile,
            ),
            "mark_scheme": _document_result(
                generated_scheme,
                reference_scheme,
                scheme_profiles,
                perceptual_dpi=perceptual_dpi,
                reference_paths=scheme_references,
                print_profile=print_profile,
            ),
        }
    comparable = [value for value in families.values() if "missing" not in value]
    overall = (
        statistics.mean(
            [
                value[document]["comparison"]["overall"]
                for value in comparable
                for document in ("question_paper", "mark_scheme")
            ]
        )
        if comparable
        else 0.0
    )
    print_failures = (
        [
            f"{family}/{document}: {failure}"
            for family, value in families.items()
            if "missing" not in value
            for document in ("question_paper", "mark_scheme")
            for failure in value[document]["print_evidence"]["failures"]
        ]
        if print_profile
        else []
    )
    return {
        "schema_version": 3,
        "perceptual_dpi": perceptual_dpi,
        "generated_root": str(generated_root),
        "families": families,
        "overall": round(overall, 3),
        "print_failures": print_failures,
    }


def _document_result(
    generated_path: Path,
    reference_path: Path,
    profiles: dict[str, dict[str, Any]],
    *,
    perceptual_dpi: int,
    reference_paths: list[Path] | None = None,
    print_profile: PrintProfile | None = None,
) -> dict[str, Any]:
    document_role = (
        "mark_scheme"
        if "mark-scheme" in generated_path.name.casefold()
        else "question_paper"
    )
    generated_roles = _document_page_roles(generated_path, document_role)
    reference_paths = reference_paths or [reference_path]
    reference_sources: dict[str, dict[str, Any]] = profiles.get(
        "reference_sources",
        {str(reference_path): profiles["reference"]},
    )
    generated_evidence = [
        PageEvidence(
            index=index,
            role=role,
            content_box=(
                tuple(profiles["generated"]["geometry"][index]["content_box"])
                if profiles["generated"]["geometry"][index]["content_box"]
                else None
            ),
            geometry=profiles["generated"]["geometry"][index],
        )
        for index, role in enumerate(generated_roles)
    ]
    reference_roles_by_source = {
        str(path): _document_page_roles(path, document_role) for path in reference_paths
    }
    reference_evidence = [
        PageEvidence(
            index=index,
            role=role,
            content_box=(
                tuple(reference_sources[source]["geometry"][index]["content_box"])
                if reference_sources[source]["geometry"][index]["content_box"]
                else None
            ),
            source=source,
            geometry=reference_sources[source]["geometry"][index],
        )
        for source, roles in reference_roles_by_source.items()
        for index, role in enumerate(roles)
    ]
    matches = _role_matches(generated_evidence, reference_evidence)
    margin_mm = print_profile.non_printable_margin_mm if print_profile else 4.2
    generated_print = extract_pdf_evidence(
        generated_path,
        non_printable_margin_mm=margin_mm,
    )
    reference_print = {
        str(path): extract_pdf_evidence(
            path,
            non_printable_margin_mm=margin_mm,
        )
        for path in reference_paths
    }
    pages = _page_comparisons(
        profiles["generated"]["geometry"],
        profiles["reference"]["geometry"],
        matches,
        reference_sources={
            source: value["geometry"] for source, value in reference_sources.items()
        },
    )
    matches_by_generated = {item.generated_index: item for item in matches}
    for page in pages:
        index = int(page["page"]) - 1
        match = matches_by_generated.get(index)
        generated_role = (
            generated_roles[index] if index < len(generated_roles) else None
        )
        reference_roles = (
            reference_roles_by_source.get(match.reference_source or "", [])
            if match
            else []
        )
        reference_role = (
            reference_roles[match.reference_index]
            if match and match.reference_index < len(reference_roles)
            else None
        )
        page["generated_role"] = generated_role
        page["reference_role"] = reference_role
        page["role"] = reference_role or generated_role or document_role
        page["structural_overall"] = page["overall"]
        if match:
            source = match.reference_source or str(reference_path)
            print_scores = compare_page_evidence(
                generated_print["pages"][index],
                reference_print[source]["pages"][match.reference_index],
            )
            page["print_scores"] = print_scores
            page["print_overall"] = round(
                statistics.mean(print_scores.values()),
                4,
            )
    perceptual = _perceptual_page_comparisons(
        generated_path,
        reference_path,
        dpi=perceptual_dpi,
        matches=matches,
        reference_paths={str(path): path for path in reference_paths},
    )
    by_page = {item["page"]: item for item in perceptual}
    for page in pages:
        measured = by_page.get(page["page"])
        if not measured:
            continue
        page.update(measured)
        page["perceptual_overall"] = round(
            statistics.mean(
                (
                    measured["registered_masked_render"],
                    measured["registered_text_layout"],
                )
            ),
            4,
        )
        page["overall"] = round(
            page["overall"] * 0.72
            + measured["registered_masked_render"] * 0.18
            + measured["registered_text_layout"] * 0.10,
            3,
        )
    for page in pages:
        if "print_overall" not in page:
            continue
        role = str(page.get("role", document_role))
        weights = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["question_content"])
        components = {
            "structural": float(page["structural_overall"]),
            "print": float(page["print_overall"]),
        }
        if "perceptual_overall" in page:
            components["perceptual"] = float(page["perceptual_overall"])
        available_weight = sum(weights[name] for name in components)
        page["qualified_overall"] = round(
            sum(components[name] * weights[name] for name in components)
            / available_weight,
            4,
        )
    comparison_profiles = {
        "generated": {
            **profiles["generated"],
            "geometry": [
                profiles["generated"]["geometry"][item.generated_index]
                for item in matches
            ],
        },
        "reference": {
            **profiles["reference"],
            "geometry": [
                profiles["reference"]["geometry"][item.reference_index]
                if item.reference_source is None
                else reference_sources[item.reference_source]["geometry"][
                    item.reference_index
                ]
                for item in matches
            ],
        },
    }
    comparison = compare(**comparison_profiles)
    if perceptual:
        masked_render = statistics.mean(
            item["registered_masked_render"] for item in perceptual
        )
        text_layout = statistics.mean(
            item["registered_text_layout"] for item in perceptual
        )
        stable_area = statistics.mean(item["stable_area"] for item in perceptual)
        comparison["scores"].update(
            {
                "registered_masked_render": round(masked_render, 3),
                "registered_text_layout": round(text_layout, 3),
                "stable_area": round(stable_area, 3),
            }
        )
        comparison["overall"] = round(
            comparison["overall"] * 0.72 + masked_render * 0.18 + text_layout * 0.10,
            3,
        )
    print_failures = (
        _print_policy_failures(generated_print, print_profile) if print_profile else []
    )
    return {
        "generated_path": str(generated_path),
        "reference_path": str(reference_path),
        "reference_paths": [str(path) for path in reference_paths],
        "reference_document_count": len(reference_paths),
        "page_count_policy": {
            "kind": (
                "exact"
                if len({value["pages"] for value in reference_sources.values()}) == 1
                else "range"
            ),
            "minimum": min(value["pages"] for value in reference_sources.values()),
            "maximum": max(value["pages"] for value in reference_sources.values()),
        },
        "print_evidence": {
            "passed": not print_failures,
            "failures": print_failures,
            "tagged": generated_print["tagged"],
            "all_fonts_embedded": all(
                item["embedded"] for item in generated_print["fonts"]
            ),
            "safe_print_pages": sum(
                bool(page["safe_print"]) for page in generated_print["pages"]
            ),
            "page_count": len(generated_print["pages"]),
            "minimum_monochrome_contrast": min(
                (
                    float(page["monochrome_minimum_contrast"])
                    for page in generated_print["pages"]
                ),
                default=21.0,
            ),
            "minimum_rule_width": min(
                (
                    float(page["minimum_rule_width"])
                    for page in generated_print["pages"]
                    if page["minimum_rule_width"] is not None
                ),
                default=None,
            ),
        },
        "generated": _compact_profile(profiles["generated"]),
        "reference": _compact_profile(profiles["reference"]),
        "comparison": comparison,
        "page_comparisons": pages,
        "role_scores": _role_scores(pages),
        "worst_pages": sorted(
            pages,
            key=lambda item: (item["overall"], item["page"]),
        )[:5],
    }


def _generated_document(
    directory: Path,
    filename: str,
    *,
    search_root: Path | None = None,
) -> Path:
    direct = directory / filename
    if direct.exists():
        return direct
    root = directory if directory.exists() else search_root
    matches = sorted(root.rglob(filename)) if root and root.exists() else []
    if len(matches) == 1:
        return matches[0]
    return direct


def validate_thresholds(
    report: dict[str, Any],
    thresholds: dict[str, Any],
) -> list[str]:
    """Return stable, human-readable release-gate failures."""
    errors: list[str] = []
    if thresholds.get("schema_version") != 1:
        return [
            "thresholds/schema/document: expected schema version 1; "
            f"observed {thresholds.get('schema_version', 'missing')}"
        ]
    expected_audit_schema = thresholds.get("audit_schema_version")
    observed_audit_schema = report.get("schema_version")
    if expected_audit_schema != observed_audit_schema:
        return [
            "thresholds/audit/document: "
            f"expected schema version {expected_audit_schema}; "
            f"observed {observed_audit_schema}"
        ]

    report_families = report.get("families", {})
    threshold_families = thresholds.get("families", {})
    for family in sorted(report_families.keys() - threshold_families.keys()):
        errors.append(
            f"{family}/question_paper/document: "
            "expected configured minimum; observed unqualified"
        )
    for family, documents in threshold_families.items():
        result = report_families.get(family)
        if not isinstance(result, dict) or "missing" in result:
            first_document = next(iter(documents), "question_paper")
            minimum = float(documents[first_document]["minimum"])
            errors.append(
                f"{family}/{first_document}/document: "
                f"expected >= {minimum:.3f}; observed missing"
            )
            continue

        for document, requirement in documents.items():
            observed_document = result.get(document)
            minimum = float(requirement["minimum"])
            if not isinstance(observed_document, dict):
                errors.append(
                    f"{family}/{document}/document: "
                    f"expected >= {minimum:.3f}; observed missing"
                )
                continue
            observed = observed_document.get("comparison", {}).get("overall")
            if observed is None:
                errors.append(
                    f"{family}/{document}/document: "
                    f"expected >= {minimum:.3f}; observed missing"
                )
            elif float(observed) < minimum:
                errors.append(
                    f"{family}/{document}/document: "
                    f"expected >= {minimum:.3f}; observed {float(observed):.3f}"
                )

            observed_roles = observed_document.get("role_scores", {})
            for role, role_minimum_value in requirement.get("roles", {}).items():
                role_minimum = float(role_minimum_value)
                role_observed = observed_roles.get(role, {}).get("overall")
                if role_observed is None:
                    errors.append(
                        f"{family}/{document}/{role}: "
                        f"expected >= {role_minimum:.3f}; observed missing"
                    )
                elif float(role_observed) < role_minimum:
                    errors.append(
                        f"{family}/{document}/{role}: "
                        f"expected >= {role_minimum:.3f}; "
                        f"observed {float(role_observed):.3f}"
                    )
    return errors


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Paper fidelity audit",
        "",
        "| Family | Question paper | Mark scheme | Weakest question pages | Weakest scheme pages | Weakest question role | Weakest scheme role |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for family, result in report["families"].items():
        if "missing" in result:
            rows.append(f"| {family} | missing | missing | - | - | - | - |")
        else:
            question = result["question_paper"]["comparison"]["overall"]
            scheme = result["mark_scheme"]["comparison"]["overall"]
            question_pages = ", ".join(
                str(item["page"]) for item in result["question_paper"]["worst_pages"]
            )
            scheme_pages = ", ".join(
                str(item["page"]) for item in result["mark_scheme"]["worst_pages"]
            )
            question_role = _weakest_role(result["question_paper"]["role_scores"])
            scheme_role = _weakest_role(result["mark_scheme"]["role_scores"])
            rows.append(
                f"| {family} | {question:.1%} | {scheme:.1%} | "
                f"{question_pages} | {scheme_pages} | {question_role} | {scheme_role} |"
            )
    rows.extend(
        ["", f"Aggregate structural/visual similarity: **{report['overall']:.1%}**", ""]
    )
    return "\n".join(rows)


def _weakest_role(role_scores: dict[str, dict[str, float | int]]) -> str:
    scored = [
        (float(summary["overall"]), role)
        for role, summary in role_scores.items()
        if "overall" in summary
    ]
    if not scored:
        return "-"
    score, role = min(scored)
    return f"{role} {score:.1%}"


def _render_page_image(page: fitz.Page, dpi: int) -> Image.Image:
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(dpi / 72, dpi / 72),
        colorspace=fitz.csRGB,
        alpha=False,
        annots=True,
    )
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def _fit_page(image: Image.Image, width: int = CONTACT_PAGE_WIDTH) -> Image.Image:
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _difference_panel(reference: Image.Image, generated: Image.Image) -> Image.Image:
    width = min(reference.width, generated.width)
    height = min(reference.height, generated.height)
    reference = reference.resize((width, height), Image.Resampling.LANCZOS)
    generated = generated.resize((width, height), Image.Resampling.LANCZOS)
    difference = ImageChops.difference(reference, generated).convert("L")
    difference = ImageEnhance.Contrast(ImageOps.autocontrast(difference)).enhance(2.2)
    red = Image.new("RGB", difference.size, (220, 28, 28))
    background = Image.new("RGB", difference.size, "white")
    return Image.composite(red, background, difference)


def _overlay_panel(reference: Image.Image, generated: Image.Image) -> Image.Image:
    size = (
        min(reference.width, generated.width),
        min(reference.height, generated.height),
    )
    reference = reference.resize(size, Image.Resampling.LANCZOS).convert("L")
    generated = generated.resize(size, Image.Resampling.LANCZOS).convert("L")
    red = Image.merge("RGB", (reference, Image.new("L", size), Image.new("L", size)))
    cyan = Image.merge("RGB", (Image.new("L", size), generated, generated))
    return Image.blend(red, cyan, 0.5)


def _labelled_panel(image: Image.Image, label: str) -> Image.Image:
    label_height = 24
    panel = Image.new("RGB", (image.width, image.height + label_height), "white")
    panel.paste(image, (0, label_height))
    ImageDraw.Draw(panel).text((6, 5), label, fill="black")
    return panel


def write_contact_sheets(
    generated_path: Path,
    reference_path: Path,
    output_prefix: Path,
    *,
    dpi: int = 96,
    page_comparisons: list[dict[str, Any]] | None = None,
) -> list[Path]:
    generated = fitz.open(generated_path)
    reference_documents: dict[str, fitz.Document] = {
        str(reference_path): fitz.open(reference_path)
    }
    outputs: list[Path] = []
    try:
        comparisons = {int(item["page"]): item for item in (page_comparisons or [])}
        primary_reference = reference_documents[str(reference_path)]
        count = max(generated.page_count, primary_reference.page_count)
        for sheet_start in range(0, count, CONTACT_PAGES_PER_SHEET):
            rows: list[Image.Image] = []
            for index in range(
                sheet_start,
                min(sheet_start + CONTACT_PAGES_PER_SHEET, count),
            ):
                measured = comparisons.get(index + 1, {})
                selected_path = str(measured.get("reference_path") or reference_path)
                if selected_path not in reference_documents:
                    reference_documents[selected_path] = fitz.open(selected_path)
                reference = reference_documents[selected_path]
                reference_index = int(measured.get("reference_page", index + 1)) - 1
                reference_image = (
                    _fit_page(_render_page_image(reference[reference_index], dpi))
                    if reference_index < reference.page_count
                    else Image.new("RGB", (CONTACT_PAGE_WIDTH, 340), "white")
                )
                generated_image = (
                    _fit_page(_render_page_image(generated[index], dpi))
                    if index < generated.page_count
                    else Image.new("RGB", reference_image.size, "white")
                )
                if generated_image.size != reference_image.size:
                    generated_image = generated_image.resize(
                        reference_image.size,
                        Image.Resampling.LANCZOS,
                    )
                panels = (
                    _labelled_panel(
                        reference_image,
                        f"Reference p{reference_index + 1} ({Path(selected_path).name})",
                    ),
                    _labelled_panel(generated_image, f"Generated p{index + 1}"),
                    _labelled_panel(
                        _overlay_panel(reference_image, generated_image),
                        f"Overlay • {measured.get('role', 'unclassified')} • "
                        f"{float(measured.get('qualified_overall', measured.get('overall', 0))):.1%}",
                    ),
                    _labelled_panel(
                        _difference_panel(reference_image, generated_image),
                        f"Difference p{index + 1}",
                    ),
                )
                gap = 8
                row = Image.new(
                    "RGB",
                    (
                        sum(panel.width for panel in panels) + gap * 2,
                        max(panel.height for panel in panels),
                    ),
                    (235, 235, 235),
                )
                x = 0
                for panel in panels:
                    row.paste(panel, (x, 0))
                    x += panel.width + gap
                rows.append(row)
            if not rows:
                continue
            sheet = Image.new(
                "RGB",
                (max(row.width for row in rows), sum(row.height for row in rows)),
                "white",
            )
            y = 0
            for row in rows:
                sheet.paste(row, (0, y))
                y += row.height
            destination = output_prefix.with_name(
                f"{output_prefix.name}-{sheet_start + 1:02d}-"
                f"{min(sheet_start + CONTACT_PAGES_PER_SHEET, count):02d}.png"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(destination, optimize=True)
            outputs.append(destination)
    finally:
        generated.close()
        for reference in reference_documents.values():
            reference.close()
    return outputs


def write_visual_artifacts(
    report: dict[str, Any],
    output_dir: Path,
    *,
    dpi: int = 96,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cards: list[str] = []
    for family, result in report["families"].items():
        if "missing" in result:
            cards.append(
                f"<section><h2>{html.escape(family)}</h2>"
                f"<p>Missing: {html.escape(', '.join(result['missing']))}</p></section>"
            )
            continue
        for role in ("question_paper", "mark_scheme"):
            document = result[role]
            prefix = output_dir / f"{family}-{role.replace('_', '-')}"
            sheets = write_contact_sheets(
                Path(document["generated_path"]),
                Path(document["reference_path"]),
                prefix,
                dpi=dpi,
                page_comparisons=document.get("page_comparisons"),
            )
            links = "".join(
                f'<a href="{html.escape(path.name)}">'
                f'<img src="{html.escape(path.name)}" loading="lazy"></a>'
                for path in sheets
            )
            cards.append(
                f"<section><h2>{html.escape(family)} — "
                f"{html.escape(role.replace('_', ' '))}</h2>"
                f"<p>Score: {document['comparison']['overall']:.1%}; "
                f"weakest pages: "
                f"{', '.join(str(item['page']) for item in document['worst_pages'])}</p>"
                f'<div class="sheets">{links}</div></section>'
            )
    page = """<!doctype html>
<meta charset="utf-8">
<title>Paper fidelity visual review</title>
<style>
body { font: 14px -apple-system, BlinkMacSystemFont, sans-serif; margin: 24px; }
section { border-top: 1px solid #ccc; padding: 18px 0; }
.sheets { display: flex; gap: 12px; overflow-x: auto; align-items: flex-start; }
img { width: 300px; height: auto; border: 1px solid #aaa; }
</style>
<h1>Paper fidelity visual review</h1>
""" + "\n".join(cards)
    (output_dir / "index.html").write_text(page, encoding="utf-8")


def write_overview_sheets(
    report: dict[str, Any],
    output_dir: Path,
    *,
    dpi: int = 96,
) -> list[Path]:
    """Write compact first-page comparisons spanning the full support matrix."""

    rows: list[Image.Image] = []
    for family, result in report["families"].items():
        if "missing" in result:
            continue
        for role in ("question_paper", "mark_scheme"):
            document = result[role]
            with fitz.open(document["reference_path"]) as reference:
                reference_image = _fit_page(_render_page_image(reference[0], dpi))
            with fitz.open(document["generated_path"]) as generated:
                generated_image = _fit_page(_render_page_image(generated[0], dpi))
            generated_image = generated_image.resize(
                reference_image.size,
                Image.Resampling.LANCZOS,
            )
            title = f"{family} — {role.replace('_', ' ')}"
            panels = (
                _labelled_panel(reference_image, f"{title}: reference"),
                _labelled_panel(generated_image, f"{title}: generated"),
                _labelled_panel(
                    _difference_panel(reference_image, generated_image),
                    f"{title}: difference",
                ),
            )
            gap = 8
            row = Image.new(
                "RGB",
                (
                    sum(panel.width for panel in panels) + gap * 2,
                    max(panel.height for panel in panels),
                ),
                (235, 235, 235),
            )
            x = 0
            for panel in panels:
                row.paste(panel, (x, 0))
                x += panel.width + gap
            rows.append(row)

    outputs: list[Path] = []
    for start in range(0, len(rows), OVERVIEW_DOCUMENTS_PER_SHEET):
        selected = rows[start : start + OVERVIEW_DOCUMENTS_PER_SHEET]
        sheet = Image.new(
            "RGB",
            (
                max(row.width for row in selected),
                sum(row.height for row in selected),
            ),
            "white",
        )
        y = 0
        for row in selected:
            sheet.paste(row, (0, y))
            y += row.height
        destination = output_dir / (
            f"overview-{start + 1:02d}-{start + len(selected):02d}.png"
        )
        sheet.save(destination, optimize=True)
        outputs.append(destination)
    return outputs


def write_worst_page_sheets(
    report: dict[str, Any],
    output_dir: Path,
    *,
    dpi: int = 96,
) -> list[Path]:
    """Write the weakest page from every primary document on compact sheets."""

    rows: list[Image.Image] = []
    for family, result in report["families"].items():
        if "missing" in result:
            continue
        for role in ("question_paper", "mark_scheme"):
            document = result[role]
            worst_pages = document.get("worst_pages", [])
            if not worst_pages:
                continue
            page_number = int(worst_pages[0]["page"])
            page_index = page_number - 1
            reference_path = Path(
                worst_pages[0].get("reference_path") or document["reference_path"]
            )
            reference_index = int(worst_pages[0].get("reference_page", page_number)) - 1
            with fitz.open(reference_path) as reference:
                reference_image = (
                    _fit_page(_render_page_image(reference[reference_index], dpi))
                    if reference_index < reference.page_count
                    else Image.new("RGB", (CONTACT_PAGE_WIDTH, 340), "white")
                )
            with fitz.open(document["generated_path"]) as generated:
                generated_image = (
                    _fit_page(_render_page_image(generated[page_index], dpi))
                    if page_index < generated.page_count
                    else Image.new("RGB", reference_image.size, "white")
                )
            generated_image = generated_image.resize(
                reference_image.size,
                Image.Resampling.LANCZOS,
            )
            title = f"{family} — {role.replace('_', ' ')} p{page_number}"
            panels = (
                _labelled_panel(reference_image, f"{title}: reference"),
                _labelled_panel(generated_image, f"{title}: generated"),
                _labelled_panel(
                    _difference_panel(reference_image, generated_image),
                    f"{title}: difference",
                ),
            )
            gap = 8
            row = Image.new(
                "RGB",
                (
                    sum(panel.width for panel in panels) + gap * 2,
                    max(panel.height for panel in panels),
                ),
                (235, 235, 235),
            )
            x = 0
            for panel in panels:
                row.paste(panel, (x, 0))
                x += panel.width + gap
            rows.append(row)

    outputs: list[Path] = []
    for start in range(0, len(rows), OVERVIEW_DOCUMENTS_PER_SHEET):
        selected = rows[start : start + OVERVIEW_DOCUMENTS_PER_SHEET]
        sheet = Image.new(
            "RGB",
            (
                max(row.width for row in selected),
                sum(row.height for row in selected),
            ),
            "white",
        )
        y = 0
        for row in selected:
            sheet.paste(row, (0, y))
            y += row.height
        destination = output_dir / (
            f"worst-overview-{start + 1:02d}-{start + len(selected):02d}.png"
        )
        sheet.save(destination, optimize=True)
        outputs.append(destination)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare generated papers with official references."
    )
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--thresholds",
        type=Path,
        help="Fail when a versioned document or page-role minimum is missed.",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        help="Write side-by-side reference/generated/difference contact sheets.",
    )
    parser.add_argument("--dpi", type=int, default=96)
    parser.add_argument(
        "--perceptual-dpi",
        type=int,
        default=96,
        help=(
            "DPI for registered, variable-content-masked page comparison; "
            "use 0 to disable."
        ),
    )
    parser.add_argument(
        "--print-profile",
        choices=("ci", "qualification"),
        help="Use a versioned 100%%-scale print profile for perceptual comparison.",
    )
    parser.add_argument(
        "--print-profiles",
        type=Path,
        default=ROOT / "Resources" / "print-profiles.json",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    print_profile = (
        load_print_profile(args.print_profiles, args.print_profile)
        if args.print_profile
        else None
    )
    report = audit(
        args.generated_root.resolve(),
        perceptual_dpi=(print_profile.dpi if print_profile else args.perceptual_dpi),
        print_profile=print_profile,
    )
    if print_profile:
        report["print_profile"] = {
            "name": args.print_profile,
            **print_profile.__dict__,
        }
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report), encoding="utf-8")
    if args.artifacts:
        artifact_root = args.artifacts.resolve()
        write_visual_artifacts(report, artifact_root, dpi=args.dpi)
        write_overview_sheets(report, artifact_root, dpi=args.dpi)
        write_worst_page_sheets(report, artifact_root, dpi=args.dpi)
    if args.thresholds:
        thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
        failures = validate_thresholds(report, thresholds)
        if failures:
            for failure in failures:
                print(f"fidelity threshold failed: {failure}", file=sys.stderr)
            return 1
    if print_profile and report["print_failures"]:
        for failure in report["print_failures"][:50]:
            print(f"print qualification failed: {failure}", file=sys.stderr)
        remaining = len(report["print_failures"]) - 50
        if remaining > 0:
            print(
                f"print qualification failed: {remaining} additional failure(s)",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
