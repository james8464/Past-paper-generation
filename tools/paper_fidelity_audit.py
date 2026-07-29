from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageOps

from tools.build_supported_layout_masters import REFERENCES


ROOT = Path(__file__).resolve().parents[1]
LINE_MARK = re.compile(
    r"(?:\[|\()(\d{1,2})(?:\s+marks?)?(?:\]|\))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
GRID_COLUMNS = 96
GRID_ROWS = 136
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
for (subject, paper), (family, reference_question, reference_scheme) in REFERENCES.items():
    generated_dir, question_name, scheme_name = GENERATED_DOCUMENTS[subject]
    FAMILIES[f"{family}-paper-{paper}"] = {
        "generated_dir": generated_dir,
        "question": question_name.format(paper=paper),
        "scheme": scheme_name.format(paper=paper),
        "reference_question": f"Reference Corpus/a-level/{reference_question}",
        "reference_scheme": f"Reference Corpus/a-level/{reference_scheme}",
    }

def _median(values: list[float]) -> float:
    return round(statistics.median(values), 2) if values else 0.0


def _font_inventory(document: fitz.Document) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, float]] = Counter()
    for page in document:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if text.strip():
                        counts[(span.get("font", "unknown"), round(span.get("size", 0), 1))] += len(text)
    return [
        {"family": family, "size": size, "characters": count}
        for (family, size), count in counts.most_common(8)
    ]


def _mark_grid(
    grid: list[int],
    bbox: tuple[float, float, float, float],
    width: float,
    height: float,
) -> None:
    x0, y0, x1, y1 = bbox
    left = max(0, min(GRID_COLUMNS - 1, int(x0 / width * GRID_COLUMNS)))
    right = max(left + 1, min(GRID_COLUMNS, math.ceil(x1 / width * GRID_COLUMNS)))
    top = max(0, min(GRID_ROWS - 1, int(y0 / height * GRID_ROWS)))
    bottom = max(top + 1, min(GRID_ROWS, math.ceil(y1 / height * GRID_ROWS)))
    for row in range(top, bottom):
        start = row * GRID_COLUMNS
        for column in range(left, right):
            grid[start + column] = 1


def _geometry_page(
    page: fitz.Page,
    allowed_diagnostics: frozenset[str],
) -> dict[str, Any]:
    width = page.rect.width
    height = page.rect.height
    text_grid = [0] * (GRID_COLUMNS * GRID_ROWS)
    drawing_grid = [0] * (GRID_COLUMNS * GRID_ROWS)
    image_grid = [0] * (GRID_COLUMNS * GRID_ROWS)
    content_boxes: list[tuple[float, float, float, float]] = []
    for block in page.get_text("blocks"):
        if not block[4].strip():
            continue
        bbox = tuple(float(value) for value in block[:4])
        content_boxes.append(bbox)
        _mark_grid(text_grid, bbox, width, height)
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect:
            _mark_grid(drawing_grid, tuple(rect), width, height)
    for image in page.get_image_info(hashes=False):
        _mark_grid(image_grid, tuple(image["bbox"]), width, height)
    ink_grid = [
        int(text or drawing or image)
        for text, drawing, image in zip(
            text_grid,
            drawing_grid,
            image_grid,
            strict=True,
        )
    ]
    pixmap = _render_page_pixmap(page, width, height, allowed_diagnostics)
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
) -> fitz.Pixmap:
    """Render static paper content and reject unknown MuPDF diagnostics."""

    show_errors = bool(fitz.TOOLS.mupdf_display_errors())
    show_warnings = bool(fitz.TOOLS.mupdf_display_warnings())
    diagnostics = ""
    fitz.TOOLS.reset_mupdf_warnings()
    fitz.TOOLS.mupdf_display_errors(False)
    fitz.TOOLS.mupdf_display_warnings(False)
    try:
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(GRID_COLUMNS / width, GRID_ROWS / height),
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
            "MuPDF could not render a paper cleanly: "
            + "; ".join(sorted(unexpected))
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
    for page in document:
        text = page.get_text("text")
        texts.append(text)
        blocks = [block for block in page.get_text("blocks") if block[4].strip()]
        if blocks:
            left.append(min(block[0] for block in blocks))
            top.append(min(block[1] for block in blocks))
            right.append(page.rect.width - max(block[2] for block in blocks))
            bottom.append(page.rect.height - max(block[3] for block in blocks))
        drawings.append(len(page.get_drawings()))
        images.append(len(page.get_images(full=True)))
        geometry.append(_geometry_page(page, allowed_diagnostics))
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
            [
                float(sum(page["render_grid"]) / 255)
                for page in geometry
            ]
        ),
        "fonts": _font_inventory(document),
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
            row[index] = previous + 1 if left_value == right_value else max(row[index], row[index - 1])
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
    shared = sum(
        left * right
        for left, right in zip(first, second, strict=True)
    )
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
        drawings.append(
            _grid_similarity(left["drawing_grid"], right["drawing_grid"])
        )
        images.append(_grid_similarity(left["image_grid"], right["image_grid"]))
        ink.append(_grid_similarity(left["ink_grid"], right["ink_grid"]))
        render.append(_shade_similarity(left["render_grid"], right["render_grid"]))
        if left["content_box"] and right["content_box"]:
            difference = statistics.mean(
                abs(a - b)
                for a, b in zip(
                    left["content_box"], right["content_box"], strict=True
                )
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
    size_overlap = len(generated_sizes & reference_sizes) / max(len(generated_sizes | reference_sizes), 1)
    generated_families = {_font_family(item["family"]) for item in generated["fonts"][:5]}
    reference_families = {_font_family(item["family"]) for item in reference["fonts"][:5]}
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
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    count = max(len(generated), len(reference))
    for index in range(count):
        if index >= len(generated) or index >= len(reference):
            result.append(
                {
                    "page": index + 1,
                    "missing": "generated" if index >= len(generated) else "reference",
                    "overall": 0.0,
                }
            )
            continue
        scores = _geometry_scores([generated[index]], [reference[index]])
        scored = {
            "render_placement": scores["render_placement"],
            "text_placement": scores["text_placement"],
            "drawing_placement": scores["drawing_placement"],
            "image_placement": scores["image_placement"],
            "content_envelope": scores["content_envelope"],
        }
        result.append(
            {
                "page": index + 1,
                "overall": round(statistics.mean(scored.values()), 3),
                "scores": {name: round(value, 3) for name, value in scored.items()},
            }
        )
    return result


def _font_family(name: str) -> str:
    value = name.casefold().replace("psmt", "").replace("mt", "")
    for suffix in ("-bolditalic", "-bold", "-italic", "-regular", "-0", "-1"):
        value = value.replace(suffix, "")
    return value.replace(" ", "")


def audit(generated_root: Path) -> dict[str, Any]:
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
        required = [generated_question, generated_scheme, reference_question, reference_scheme]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            families[family] = {"missing": missing}
            continue
        question_profiles = {
            "generated": profile(generated_question),
            "reference": profile(
                reference_question,
                tolerate_reference_diagnostics=True,
            ),
        }
        scheme_profiles = {
            "generated": profile(generated_scheme),
            "reference": profile(
                reference_scheme,
                tolerate_reference_diagnostics=True,
            ),
        }
        families[family] = {
            "question_paper": _document_result(
                generated_question,
                reference_question,
                question_profiles,
            ),
            "mark_scheme": _document_result(
                generated_scheme,
                reference_scheme,
                scheme_profiles,
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
    return {
        "schema_version": 2,
        "generated_root": str(generated_root),
        "families": families,
        "overall": round(overall, 3),
    }


def _document_result(
    generated_path: Path,
    reference_path: Path,
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pages = _page_comparisons(
        profiles["generated"]["geometry"],
        profiles["reference"]["geometry"],
    )
    return {
        "generated_path": str(generated_path),
        "reference_path": str(reference_path),
        "generated": _compact_profile(profiles["generated"]),
        "reference": _compact_profile(profiles["reference"]),
        "comparison": compare(**profiles),
        "page_comparisons": pages,
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


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Paper fidelity audit",
        "",
        "| Family | Question paper | Mark scheme | Weakest question pages | Weakest scheme pages |",
        "|---|---:|---:|---|---|",
    ]
    for family, result in report["families"].items():
        if "missing" in result:
            rows.append(f"| {family} | missing | missing | - | - |")
        else:
            question = result["question_paper"]["comparison"]["overall"]
            scheme = result["mark_scheme"]["comparison"]["overall"]
            question_pages = ", ".join(
                str(item["page"]) for item in result["question_paper"]["worst_pages"]
            )
            scheme_pages = ", ".join(
                str(item["page"]) for item in result["mark_scheme"]["worst_pages"]
            )
            rows.append(
                f"| {family} | {question:.1%} | {scheme:.1%} | "
                f"{question_pages} | {scheme_pages} |"
            )
    rows.extend(["", f"Aggregate structural/visual similarity: **{report['overall']:.1%}**", ""])
    return "\n".join(rows)


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
) -> list[Path]:
    generated = fitz.open(generated_path)
    reference = fitz.open(reference_path)
    outputs: list[Path] = []
    try:
        count = max(generated.page_count, reference.page_count)
        for sheet_start in range(0, count, CONTACT_PAGES_PER_SHEET):
            rows: list[Image.Image] = []
            for index in range(
                sheet_start,
                min(sheet_start + CONTACT_PAGES_PER_SHEET, count),
            ):
                reference_image = (
                    _fit_page(_render_page_image(reference[index], dpi))
                    if index < reference.page_count
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
                    _labelled_panel(reference_image, f"Reference p{index + 1}"),
                    _labelled_panel(generated_image, f"Generated p{index + 1}"),
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare generated papers with official references.")
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--artifacts",
        type=Path,
        help="Write side-by-side reference/generated/difference contact sheets.",
    )
    parser.add_argument("--dpi", type=int, default=96)
    args = parser.parse_args()
    report = audit(args.generated_root.resolve())
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
