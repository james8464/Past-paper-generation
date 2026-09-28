"""Content-preserving pagination checks for OCR Economics marking tables."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pymupdf

from Backend.Core.layout_master import LayoutConformanceError

OCR_ECONOMICS_SCHEME_PAGINATION = "generated-ocr-economics-mark-scheme-content-v1"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def _contains_credit(text: str, point: str, prefix: str = "") -> bool:
    value = _normalise(point)
    if not value:
        return False
    if re.fullmatch(
        r"[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)(?:/[+\-]?\d+(?:\.\d*)?)?[;.]?", value
    ):
        expected = _normalise(f"{prefix}: {point}" if prefix else point)
        return any(
            _normalise(line).lstrip("•") == expected for line in text.splitlines()
        )
    if prefix:
        value = _normalise(f"{prefix}: {point}")
    pattern = r"(?<!\w)" + r"\s*".join(map(re.escape, value)) + r"(?!\w)"
    return re.search(pattern, unicodedata.normalize("NFKC", text)) is not None


def verify_ocr_scheme_content(
    pdf_path: Path, assessment_path: Path | None, *, paper: str, reference_count: int
) -> dict:
    from Backend.Core.assessment_package import _extract_items

    if assessment_path is None:
        raise LayoutConformanceError(
            "OCR scheme pagination requires its assessment package"
        )
    package = json.loads(assessment_path.read_text(encoding="utf-8"))
    if package.get("subject") != "economics_ocr" or str(package.get("paper")) != paper:
        raise LayoutConformanceError("OCR scheme assessment package identity differs")
    blueprint = package.get("blueprint") or {}
    items = _extract_items(blueprint, subject="economics_ocr", paper_number=paper)
    if not items or package.get("items") != items:
        raise LayoutConformanceError(
            "OCR scheme requires complete matching assessed items"
        )
    expected: dict[str, list[tuple[str, str]]] = {}
    prompts: dict[str, str] = {}
    for section in blueprint.get("sections", []):
        for option in section.get("options", []):
            for question in option.get("questions", []):
                identifier = question["number"]
                if identifier in expected:
                    raise LayoutConformanceError(
                        "OCR scheme has duplicate assessed identifiers"
                    )
                prompts[identifier] = question.get("prompt") or ""
                points = [(point, "") for point in question.get("mark_scheme") or []]
                for point in question.get("structured_mark_scheme") or []:
                    points.append((point["text"], ""))
                    for field, prefix in (
                        ("alternatives", "Accept"),
                        ("allow", "Allow"),
                        ("do_not_accept", "Do not accept"),
                        ("ignore", "Ignore"),
                    ):
                        for value in point.get(field) or []:
                            points.append((value, prefix))
                if not points:
                    raise LayoutConformanceError("OCR scheme has no assessed credit")
                expected[identifier] = list(dict.fromkeys(points))
    if len(expected) != len(items):
        raise LayoutConformanceError("OCR scheme package omits assessed questions")

    by_question: dict[str, list[str]] = {key: [] for key in expected}
    seen_pages: set[str] = set()
    diagram_questions: set[str] = set()
    objectives_seen = False
    with pymupdf.open(pdf_path) as document:
        count = len(document)
        if count < 12:
            raise LayoutConformanceError(
                "OCR scheme omits front matter, assessed content or colophon"
            )
        for page_number, page in enumerate(document):
            text = page.get_text(sort=True)
            if page_number < 10:
                if (page.rect.width < page.rect.height) != (page_number < 2) or len(
                    re.findall(r"[A-Za-z]", text)
                ) < 12:
                    raise LayoutConformanceError(
                        "OCR scheme has missing or invalid front matter"
                    )
                continue
            if page_number == count - 1:
                if (
                    page.rect.width > page.rect.height
                    or "Independent practice material" not in text
                    or "examination board" not in text
                ):
                    raise LayoutConformanceError("OCR scheme has an invalid final page")
                continue
            if page.rect.width < page.rect.height:
                raise LayoutConformanceError(
                    "OCR assessed scheme page must remain landscape"
                )
            body = page.get_text(clip=pymupdf.Rect(30, 45, 800, page.rect.height - 35))
            fingerprint = _normalise(body)
            if fingerprint in seen_pages:
                raise LayoutConformanceError("OCR scheme has duplicate body pages")
            seen_pages.add(fingerprint)
            words = page.get_text("words", sort=False)
            anchors = sorted(
                (word for word in words if 40 <= word[0] < 114 and word[4] in expected),
                key=lambda word: word[1],
            )
            if not anchors and (
                "Assessment objective" in text or "Assessment Objective" in text
            ):
                if objectives_seen:
                    raise LayoutConformanceError(
                        "OCR scheme has duplicate objective appendices"
                    )
                objectives_seen = True
                continue
            diagram = re.search(
                r"Question\s+(\d+(?:\([a-z]\))?)\s+diagram guidance", text
            )
            if diagram and not anchors:
                identifier = diagram[1]
                if identifier not in expected or identifier in diagram_questions:
                    raise LayoutConformanceError(
                        "OCR scheme has an unassessed or repeated diagram appendix"
                    )
                diagram_questions.add(identifier)
                continue
            if not anchors:
                raise LayoutConformanceError(
                    "OCR scheme has blank or unassessed padding"
                )
            for index, anchor in enumerate(anchors):
                bottom = (
                    anchors[index + 1][1] - 1
                    if index + 1 < len(anchors)
                    else page.rect.height - 35
                )
                lines: dict[tuple, list[tuple]] = {}
                for word in words:
                    if 114 <= word[0] < 775 and anchor[1] - 1 <= word[1] < bottom:
                        lines.setdefault(word[5:7], []).append(word)
                # Level descriptors span the answer, tariff and guidance columns.
                # Preserve those complete lines, but never treat a tariff-only
                # line as a numeric answer credit.
                credit_lines = [
                    " ".join(word[4] for word in line)
                    for line in lines.values()
                    if any(word[0] < 417 or word[0] >= 467 for word in line)
                ]
                by_question[anchor[4]].append("\n".join(credit_lines))
    for identifier, points in expected.items():
        text = "\n".join(by_question[identifier])
        # The first answer-column row repeats the prompt for examiner context.
        # Remove that occurrence, preserving an independently printed answer even
        # when it happens to use exactly the same words as the question.
        prompt = _normalise(prompts[identifier])
        if prompt:
            pattern = r"\s*".join(map(re.escape, prompt))
            text = re.sub(pattern, "", unicodedata.normalize("NFKC", text), count=1)
        if any(not _contains_credit(text, point, prefix) for point, prefix in points):
            raise LayoutConformanceError(
                f"OCR scheme omits or truncates marking guidance for {identifier}"
            )
    return {
        "policy": OCR_ECONOMICS_SCHEME_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": count,
        "checked_parts": len(expected),
        "checked_credit_statements": sum(map(len, expected.values())),
        "complete_printed_credit": True,
        "blank_padding_pages": 0,
    }
