from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import fitz


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "Resources" / "layout-masters"
PAGE_NUMBER = re.compile(r"^(?:page\s+)?\d+(?:\s+of\s+\d+)?$", re.IGNORECASE)
MARK = re.compile(r"^[\[(]?\d{1,3}(?:\s+marks?)?[\])]?$", re.IGNORECASE)
QUESTION = re.compile(r"^\d{1,2}(?:[.\s][0-9a-z]{1,3})*$", re.IGNORECASE)


def _round_rect(value: Iterable[float], places: int = 2) -> list[float]:
    return [round(float(item), places) for item in value]


def _colour(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, int):
        return [
            round(((value >> shift) & 255) / 255, 3)
            for shift in (16, 8, 0)
        ]
    return [round(float(item), 3) for item in value]


def _line_role(text: str, bbox: list[float], page: fitz.Page, size: float) -> str:
    value = " ".join(text.split())
    if PAGE_NUMBER.fullmatch(value) and (
        bbox[1] < 55 or bbox[3] > page.rect.height - 55
    ):
        return "page-number"
    if MARK.fullmatch(value) and bbox[0] > page.rect.width * 0.72:
        return "mark"
    if QUESTION.fullmatch(value) and bbox[0] < page.rect.width * 0.22:
        return "question-number"
    if bbox[1] < 55 or bbox[3] > page.rect.height - 45:
        return "furniture"
    if size >= 14:
        return "heading"
    return "body"


def _text_lines(page: fitz.Page) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for block in page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT).get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = [span for span in line.get("spans", []) if span.get("text", "").strip()]
            if not spans:
                continue
            text = "".join(span["text"] for span in spans)
            bbox = _round_rect(
                (
                    min(span["bbox"][0] for span in spans),
                    min(span["bbox"][1] for span in spans),
                    max(span["bbox"][2] for span in spans),
                    max(span["bbox"][3] for span in spans),
                )
            )
            dominant = max(spans, key=lambda item: len(item.get("text", "")))
            size = round(float(dominant.get("size", 0)), 2)
            result.append(
                {
                    "bbox": bbox,
                    "origin": _round_rect((*dominant.get("origin", (bbox[0], bbox[3])), 0, 0))[:2],
                    "font": str(dominant.get("font", "unknown")),
                    "size": size,
                    "flags": int(dominant.get("flags", 0)),
                    "colour": _colour(dominant.get("color")),
                    "characters": len(text.strip()),
                    "role": _line_role(text, bbox, page, size),
                }
            )
    return result


def _drawing_kind(items: list[Any]) -> str:
    kinds = {str(item[0]) for item in items if item}
    if kinds == {"l"}:
        return "line"
    if kinds <= {"re", "qu"}:
        return "box"
    if "c" in kinds:
        return "curve"
    return "mixed"


def _drawings(page: fitz.Page) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if not rect:
            continue
        result.append(
            {
                "bbox": _round_rect(rect),
                "kind": _drawing_kind(drawing.get("items", [])),
                "width": round(float(drawing.get("width") or 0), 2),
                "dashes": str(drawing.get("dashes") or ""),
                "stroke": _colour(drawing.get("color")),
                "fill": _colour(drawing.get("fill")),
                "close": bool(drawing.get("closePath")),
            }
        )
    return result


def _images(page: fitz.Page) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in page.get_image_info(hashes=False):
        result.append(
            {
                "bbox": _round_rect(item["bbox"]),
                "width": int(item.get("width", 0)),
                "height": int(item.get("height", 0)),
                "colorspace": int(item.get("colorspace", 0)),
            }
        )
    return result


def _content_box(lines: list[dict[str, Any]]) -> list[float] | None:
    boxes = [
        line["bbox"]
        for line in lines
        if line["role"] not in {"furniture", "page-number"}
    ]
    if not boxes:
        return None
    return [
        round(min(box[0] for box in boxes), 2),
        round(min(box[1] for box in boxes), 2),
        round(max(box[2] for box in boxes), 2),
        round(max(box[3] for box in boxes), 2),
    ]


def _page_role(
    number: int,
    lines: list[dict[str, Any]],
    drawings: list[dict[str, Any]],
) -> str:
    if number == 1:
        return "cover"
    body = [line for line in lines if line["role"] not in {"furniture", "page-number"}]
    if not body and len(drawings) < 4:
        return "blank"
    line_count = sum(item["kind"] == "line" for item in drawings)
    if line_count >= 12:
        return "answer"
    if any(line["role"] == "heading" for line in body):
        return "section"
    return "question"


def _box(page: fitz.Page, name: str) -> list[float]:
    return _round_rect(getattr(page, f"{name}box"))


def _furniture_signature(item: dict[str, Any]) -> tuple[Any, ...]:
    bbox = tuple(round(float(value), 1) for value in item["bbox"])
    return (
        item["kind"],
        bbox,
        round(float(item["width"]), 1),
        item["dashes"],
        tuple(item["stroke"] or ()),
        tuple(item["fill"] or ()),
    )


def _recurring_furniture(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    occurrences: Counter[tuple[Any, ...]] = Counter()
    examples: dict[tuple[Any, ...], dict[str, Any]] = {}
    for page in pages:
        seen: set[tuple[Any, ...]] = set()
        for drawing in page["drawings"]:
            signature = _furniture_signature(drawing)
            examples[signature] = drawing
            seen.add(signature)
        occurrences.update(seen)
    threshold = max(2, math.ceil(len(pages) * 0.2))
    result = []
    for signature, count in occurrences.most_common():
        if count < threshold:
            continue
        result.append({**examples[signature], "pages": count})
    return result


def extract_layout_master(
    source: Path,
    *,
    family: str,
    paper: str,
    document_role: str,
) -> dict[str, Any]:
    document = fitz.open(source)
    try:
        pages: list[dict[str, Any]] = []
        for number, page in enumerate(document, 1):
            lines = _text_lines(page)
            drawings = _drawings(page)
            pages.append(
                {
                    "number": number,
                    "role": _page_role(number, lines, drawings),
                    "boxes": {
                        "media": _box(page, "media"),
                        "crop": _box(page, "crop"),
                        "trim": _box(page, "trim"),
                        "bleed": _box(page, "bleed"),
                        "art": _box(page, "art"),
                    },
                    "content_box": _content_box(lines),
                    "text_lines": lines,
                    "drawings": drawings,
                    "images": _images(page),
                }
            )
    finally:
        document.close()
    return {
        "schema_version": 2,
        "family": family,
        "paper": paper,
        "document_role": document_role,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "copyrighted_text_included": False,
        "coordinate_system": "PDF points, top-left origin for content geometry",
        "pages": pages,
        "recurring_furniture": _recurring_furniture(pages),
    }


def write_layout_master(
    source: Path,
    output: Path,
    *,
    family: str,
    paper: str,
    document_role: str,
) -> None:
    payload = extract_layout_master(
        source,
        family=family,
        paper=paper,
        document_role=document_role,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract coordinate-preserving, text-free layout masters."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--family", required=True)
    parser.add_argument("--paper", required=True)
    parser.add_argument(
        "--document-role",
        choices=("question-paper", "mark-scheme", "source-booklet"),
        required=True,
    )
    args = parser.parse_args()
    write_layout_master(
        args.source.resolve(),
        args.output.resolve(),
        family=args.family,
        paper=args.paper,
        document_role=args.document_role,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
