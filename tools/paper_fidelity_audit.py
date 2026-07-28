from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

from tools.build_supported_layout_masters import REFERENCES


ROOT = Path(__file__).resolve().parents[1]
LINE_MARK = re.compile(
    r"(?:\[|\()(\d{1,2})(?:\s+marks?)?(?:\]|\))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
GRID_COLUMNS = 96
GRID_ROWS = 136
KNOWN_REFERENCE_MUPDF_DIAGNOSTICS = {
    "bogus font ascent/descent values (3117 / -2464)",
    "format error: No common ancestor in structure tree",
    "premature end of data in flate filter",
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


def _font_family(name: str) -> str:
    value = name.casefold().replace("psmt", "").replace("mt", "")
    for suffix in ("-bolditalic", "-bold", "-italic", "-regular", "-0", "-1"):
        value = value.replace(suffix, "")
    return value.replace(" ", "")


def audit(generated_root: Path) -> dict[str, Any]:
    families: dict[str, Any] = {}
    for family, paths in FAMILIES.items():
        generated_dir = generated_root / paths["generated_dir"]
        generated_question = generated_dir / paths["question"]
        generated_scheme = generated_dir / paths["scheme"]
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
            "question_paper": {
                **question_profiles,
                "comparison": compare(**question_profiles),
            },
            "mark_scheme": {
                **scheme_profiles,
                "comparison": compare(**scheme_profiles),
            },
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
        "schema_version": 1,
        "generated_root": str(generated_root),
        "families": families,
        "overall": round(overall, 3),
    }


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Paper fidelity audit",
        "",
        "| Family | Question paper | Mark scheme |",
        "|---|---:|---:|",
    ]
    for family, result in report["families"].items():
        if "missing" in result:
            rows.append(f"| {family} | missing | missing |")
        else:
            question = result["question_paper"]["comparison"]["overall"]
            scheme = result["mark_scheme"]["comparison"]["overall"]
            rows.append(f"| {family} | {question:.1%} | {scheme:.1%} |")
    rows.extend(["", f"Aggregate structural/visual similarity: **{report['overall']:.1%}**", ""])
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare generated papers with official references.")
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
