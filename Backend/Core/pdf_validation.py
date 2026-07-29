from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import fitz


CONTROLLED_FONT_PREFIXES = {
    "economics": (
        "HelveticaNeue",
        "Verdana",
        "Times",
    ),
    "default": (
        "Arial",
        "CourierNew",
    ),
}


def validate_pdf_for_release(
    path: Path,
    *,
    subject: str,
) -> dict[str, Any]:
    """Fail closed on malformed, substituted, annotated, or low-resolution PDFs."""

    document = fitz.open(path)
    try:
        if document.page_count < 1:
            raise ValueError(f"{path.name} contains no pages")
        metadata = document.metadata or {}
        if not metadata.get("title"):
            raise ValueError(f"{path.name} has no PDF title metadata")

        fonts: set[str] = set()
        image_dpi: list[float] = []
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
            page_has_content = False
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            page_has_content = True
                            fonts.add(str(span.get("font", "")))
            drawings = page.get_drawings()
            page_has_content = page_has_content or bool(drawings)
            for image in page.get_image_info(hashes=False):
                bbox = fitz.Rect(image["bbox"])
                if bbox.width <= 0 or bbox.height <= 0:
                    continue
                horizontal = image["width"] / (bbox.width / 72)
                vertical = image["height"] / (bbox.height / 72)
                image_dpi.append(min(horizontal, vertical))
            if not page_has_content:
                raise ValueError(
                    f"{path.name} page {page_index} is unexpectedly empty"
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
        }
    finally:
        document.close()
