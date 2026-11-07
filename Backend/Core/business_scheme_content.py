"""Opt-in, source-bound pagination checks for generated Business Paper 2 credit."""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf as fitz

from Backend.Core.exam_blueprints import GeneratedPaper, GeneratedQuestion
from Backend.Core.layout_master import LayoutConformanceError
from Backend.Core.paths import REPO_ROOT
from Backend.Core.preview_presentation import preview_presentation

BUSINESS_SCHEME_PAGINATION = "generated-aqa-business-paper2-mark-scheme-content-v1"
BUSINESS_SCHEME_MARKER = "business_mark_scheme_pagination"
BUSINESS_SCHEME_DATE = "business_mark_scheme_generated_on"
_MAX_PACKAGE_BYTES = 8 * 1024 * 1024
_MAX_PDF_BYTES = 32 * 1024 * 1024
_MAX_RENDERED_CHARACTERS = 100_000
_MAX_PAGES = 128


def uses_business_scheme_policy(paper: GeneratedPaper) -> bool:
    questions = [q for s in paper.sections for o in s.options for q in o.questions]
    return (
        paper.paper_id == "paper_2"
        and bool(questions)
        and all(
            q.authoring_context.get(BUSINESS_SCHEME_MARKER)
            == BUSINESS_SCHEME_PAGINATION
            for q in questions
        )
    )


def business_scheme_generation_series(paper: GeneratedPaper) -> str | None:
    if not uses_business_scheme_policy(paper):
        return None
    dates = [
        q.authoring_context.get(BUSINESS_SCHEME_DATE)
        for s in paper.sections
        for o in s.options
        for q in o.questions
    ]
    if any(type(value) is not str for value in dates) or len(set(dates)) != 1:
        raise LayoutConformanceError(
            "Business scheme generated-on dates are missing or inconsistent"
        )
    try:
        value = date.fromisoformat(dates[0])
        if value.isoformat() != dates[0]:
            raise ValueError("noncanonical ISO date")
    except ValueError as error:
        raise LayoutConformanceError(
            "Business scheme generated-on date is malformed"
        ) from error
    return value.strftime("%B %Y")


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", html.unescape(value)))


def _body(page: fitz.Page) -> fitz.Rect:
    # Renderer-owned frame limits. Exclude only chrome above/below the body;
    # the cover and every guidance/appendix page still undergo comparison.
    return fitz.Rect(
        0, 25 * 72 / 25.4, page.rect.width, page.rect.height - 18 * 72 / 25.4
    )


def _fingerprints(path: Path) -> list[tuple[float, float, bytes]]:
    with fitz.open(path) as document:
        if not 1 <= len(document) <= _MAX_PAGES:
            raise LayoutConformanceError("Business scheme exceeds its render budget")
        result = []
        for page in document:
            if abs(page.rect.width - 595.32) > 1 or abs(page.rect.height - 841.92) > 1:
                raise LayoutConformanceError(
                    "Business scheme must retain its A4 portrait geometry"
                )
            bounds = _body(page)
            if not page.get_text(clip=bounds).strip():
                raise LayoutConformanceError(
                    "Business scheme contains a body-empty page"
                )
            raster = page.get_pixmap(
                clip=bounds, dpi=72, colorspace=fitz.csGRAY, alpha=False
            )
            result.append(
                (
                    page.rect.width,
                    page.rect.height,
                    hashlib.sha256(raster.samples).digest(),
                )
            )
        return result


def _printed_credit(pdf_path: Path, questions: list[GeneratedQuestion]) -> int:
    """Independently read table owners/credit, not the canonical PDF's text."""
    expected = {question.number: question for question in questions}
    by_question: dict[str, list[str]] = {number: [] for number in expected}
    owners: list[str] = []
    current = None
    appendix_started = False
    with fitz.open(pdf_path) as document:
        for page in document:
            body = page.get_text(clip=_body(page))
            if (
                re.search(r"Question\s+\d{2}\.\d\s+application and judgement", body)
                or "Assessment objectives grid" in body
            ):
                appendix_started = True
            if appendix_started:
                continue  # Appendices may repeat prompts, never substitute credit.
            words = page.get_text("words", clip=_body(page), sort=False)
            anchors = sorted(
                (
                    word
                    for word in words
                    if word[0] < 90
                    and re.fullmatch(r"\d{2}\.\d", word[4])
                    and any(
                        tariff[0] >= 496
                        and abs(tariff[1] - word[1]) < 6
                        and tariff[4].isdigit()
                        for tariff in words
                    )
                ),
                key=lambda word: word[1],
            )
            if not anchors:
                continue  # Front matter is independently bound by body rasters.
            for index, anchor in enumerate(anchors):
                number = anchor[4]
                if number not in expected:
                    raise LayoutConformanceError(
                        "Business scheme has a forged question owner"
                    )
                if current != number:
                    owners.append(number)
                    current = number
                bottom = (
                    anchors[index + 1][1] - 1
                    if index + 1 < len(anchors)
                    else _body(page).y1
                )
                lines: dict[tuple, list[str]] = {}
                for word in words:
                    if word[0] < 496 and anchor[1] - 2 <= word[1] < bottom:
                        lines.setdefault(word[5:7], []).append(word[4])
                text = "\n".join(" ".join(line) for line in lines.values())
                # Repeated table headers cannot satisfy an answer/credit point.
                text = _compact(text).replace(
                    _compact(f"{number} {expected[number].prompt}"), ""
                )
                by_question[number].append(text)
                if not any(
                    word[0] >= 496
                    and abs(word[1] - anchor[1]) < 6
                    and word[4] == str(expected[number].marks)
                    for word in words
                ):
                    raise LayoutConformanceError(
                        f"Business scheme omits the printed marks for {number}"
                    )
    if owners != list(expected):
        raise LayoutConformanceError(
            "Business scheme has missing, duplicated or reordered question tables"
        )
    for number, question in expected.items():
        text = "".join(by_question[number])
        cursor = 0
        for point in question.mark_scheme:
            value = _compact(point)
            found = text.find(value, cursor)
            if not value or found < 0:
                raise LayoutConformanceError(
                    f"Business scheme omits or reorders credit for {number}: {point}"
                )
            cursor = found + len(value)
        if text.replace("•", "") != "".join(
            _compact(point) for point in question.mark_scheme
        ):
            raise LayoutConformanceError(
                f"Business scheme has extra or duplicate credit for {number}"
            )
    return sum(len(question.mark_scheme) for question in questions)


def verify_business_paper_two_scheme(
    pdf_path: Path, assessment_path: Path | None, reference_count: int
) -> dict | None:
    """Historical unmarked packages retain the exact measured reference count."""
    if assessment_path is None:
        raise LayoutConformanceError(
            "Business scheme policy requires its assessment package"
        )
    if (
        assessment_path.stat().st_size > _MAX_PACKAGE_BYTES
        or pdf_path.stat().st_size > _MAX_PDF_BYTES
    ):
        raise LayoutConformanceError("Business scheme exceeds its input budget")
    from aqabizgen.configs import load_rule
    from aqabizgen.generator import build_paper, validate_paper
    from aqabizgen.render_pdf import render_mark_scheme
    from aqabizgen.syllabus import load_syllabus

    from Backend.Core.assessment_package import _extract_items

    try:
        package = json.loads(assessment_path.read_text(encoding="utf-8"))
        raw = package.get("blueprint") or {}
        questions_raw = [
            q
            for s in raw.get("sections", [])
            for o in s.get("options", [])
            for q in o.get("questions", [])
        ]
        markers = [
            q.get("authoring_context", {}).get(BUSINESS_SCHEME_MARKER)
            for q in questions_raw
        ]
        if (
            package.get("subject") != "business_aqa"
            or str(package.get("paper")) != "2"
            or type(package.get("preview")) is not bool
        ):
            raise ValueError("Business scheme package identity or mode differs")
        if markers and all(marker is None for marker in markers):
            return None
        if not markers or any(
            marker != BUSINESS_SCHEME_PAGINATION for marker in markers
        ):
            raise ValueError("missing, partial or unknown Business scheme marker")
        items = _extract_items(raw, subject="business_aqa", paper_number="2")
        if not items or items != package.get("items"):
            raise ValueError(
                "Business scheme requires complete matching assessed items"
            )
        paper = GeneratedPaper.model_validate(raw)
        business_scheme_generation_series(paper)
        syllabus = load_syllabus(
            REPO_ROOT / "Resources/business/aqa/generator/data/syllabus.json"
        )
        validate_paper(paper, load_rule("2"), syllabus)
        owned = build_paper(load_rule("2"), syllabus, paper.seed)
        questions = []
        for section, baseline_section in zip(
            paper.sections, owned.sections, strict=True
        ):
            for option, baseline in zip(
                section.options, baseline_section.options, strict=True
            ):
                if option.model_dump(exclude={"questions"}) != baseline.model_dump(
                    exclude={"questions"}
                ):
                    raise ValueError(
                        "Business source/chart facts differ from the owned case"
                    )
                for question, original in zip(
                    option.questions, baseline.questions, strict=True
                ):
                    if (question.number, question.topic_id) != (
                        original.number,
                        original.topic_id,
                    ):
                        raise ValueError(
                            "Business scheme has forged question identifiers or source owners"
                        )
                    if question.kind == "calculation":
                        keys = {
                            key
                            for key in original.authoring_context
                            if key.startswith("calculation_")
                            or key in {"source_data", "verified_answers"}
                        }
                        if question.mark_scheme != original.mark_scheme or any(
                            question.authoring_context.get(key)
                            != original.authoring_context[key]
                            for key in keys
                        ):
                            raise ValueError(
                                "Business immutable numeric credit or source contract differs"
                            )
                    questions.append(question)
        if len(questions) != 11:
            raise ValueError(
                "Business Paper 2 requires its complete assessed question set"
            )
        public_text = [
            (q.prompt, q.mark_scheme, q.authoring_context.get("task_context"))
            for q in questions
        ]
        if len(json.dumps(public_text)) > _MAX_RENDERED_CHARACTERS:
            raise ValueError("Business scheme exceeds its public-content render budget")
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise LayoutConformanceError(str(error)) from error
    actual = _fingerprints(pdf_path)
    checked_credit = _printed_credit(pdf_path, questions)
    with TemporaryDirectory(prefix="keldin-business-scheme-") as temporary:
        canonical = Path(temporary) / "scheme.pdf"
        with preview_presentation(package["preview"]):
            render_mark_scheme(paper, canonical)
        if actual != _fingerprints(canonical):
            raise LayoutConformanceError(
                "Business scheme bodies differ from the complete published blueprint"
            )
    return {
        "policy": BUSINESS_SCHEME_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": len(actual),
        "checked_parts": len(questions),
        "checked_credit_statements": checked_credit,
        "complete_printed_credit": True,
        "blank_padding_pages": 0,
    }
