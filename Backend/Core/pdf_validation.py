from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import pymupdf as fitz

from Backend.Core.paths import REPO_ROOT


CONTROLLED_FONT_PREFIXES = {
    "economics": (
        "HelveticaNeue",
        "Verdana",
        "Courier",
        "Helvetica",
        "Symbol",
        "Times",
        "ZapfDingbats",
    ),
    "default": (
        "Arial",
        "Courier",
        "CourierNew",
        "Helvetica",
        "Symbol",
        "Times",
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
INTENTIONAL_BLANK_PAGE_CONTRACTS = {
    # Pearson's Paper 2 mark scheme ends on a deliberately blank page. Keeping
    # that final leaf preserves the measured 36-page reference pagination.
    ("economics", "2", "mark_scheme"): frozenset({36}),
}


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
            or metadata.get("author", "").casefold()
            in {"", "anonymous", "unspecified"}
            or metadata.get("subject", "").casefold()
            in {"", "unspecified"}
        ):
            raise ValueError(
                f"{path.name} has placeholder or missing release metadata"
            )

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
            if not all(
                math.isfinite(value) and value > 0
                for value in (width, height)
            ):
                raise ValueError(f"{path.name} page {page_index} has an invalid page box")
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
                raise ValueError(
                    f"{path.name} page {page_index} is unexpectedly empty"
                )
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
                    "text_occupancy": round(
                        _text_occupancy(text_spans, page.rect), 4
                    ),
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
            font
            for font in fonts
            if font and not font.startswith(allowed)
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
            "minimum_image_dpi": (
                round(min(image_dpi), 1) if image_dpi else None
            ),
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
        _normalise_font(str(item["family"]))
        for item in profile.get("fonts", [])[:8]
    }
    generated_fonts = {
        _normalise_font(name)
        for name, _count in font_characters.most_common(8)
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
        round(float(item["size"]), 1)
        for item in profile.get("fonts", [])[:8]
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
    name = value.casefold()
    for token in (
        "bold",
        "italic",
        "regular",
        "psmt",
        "mt",
        ",",
        "-",
        "_",
        " ",
    ):
        name = name.replace(token, "")
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
