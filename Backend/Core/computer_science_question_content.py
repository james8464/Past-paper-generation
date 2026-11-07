"""Bound generated CS1 pagination to its published candidate content, not a count."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import cast

import pymupdf

from Backend.Core.layout_master import LayoutConformanceError

AQA_CS_PAPER1_QUESTION_PAGINATION = "generated-aqa-cs-paper1-question-content-v1"
# Same resource ceilings as the existing bounded Business content verifier.
_MAX_PACKAGE_BYTES = 8 * 1024 * 1024
_MAX_PDF_BYTES = 32 * 1024 * 1024
_MAX_SOURCE_CHARACTERS = 100_000
_MAX_PAGES = 128


def _normalise(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _markers(
    words: list[tuple[float, float, float, float, str, int, int, int]],
) -> list[tuple[float, int, str | None]]:
    """Read the existing two-digit question boxes and optional part box."""
    result = []
    for word in words:
        if not (52 <= word[0] < 69 and 70 <= word[1] < 770):
            continue
        if not re.fullmatch(r"\d", word[4]):
            continue
        same_row = [w for w in words if abs(w[1] - word[1]) < 1]
        ones = [w[4] for w in same_row if 69 <= w[0] < 86]
        parts = [w[4] for w in same_row if 96 <= w[0] < 113]
        if len(ones) != 1 or not ones[0].isdigit() or len(parts) > 1:
            raise LayoutConformanceError("CS1 has a malformed printed question owner")
        if parts and not parts[0].isdigit():
            raise LayoutConformanceError("CS1 has a malformed printed part owner")
        # The box digits sit 12pt below the associated prompt baseline.
        result.append(
            (word[1] - 14, int(word[4] + ones[0]), parts[0] if parts else None)
        )
    return sorted(result)


def verify_cs_paper1_questions(
    pdf_path: Path, assessment_path: Path | None, reference_count: int
) -> dict[str, object]:
    from cspapergen.models import PaperBlueprint
    from cspapergen.render_pdf import PAPER1_SECTIONS, candidate_stimulus_data
    from cspapergen.syllabus import load_syllabus
    from cspapergen.validation import validate_blueprint

    from Backend.Core.assessment_package import _extract_items

    try:
        if (
            assessment_path is None
            or assessment_path.stat().st_size > _MAX_PACKAGE_BYTES
        ):
            raise ValueError("CS1 requires a bounded complete assessment package")
        if pdf_path.stat().st_size > _MAX_PDF_BYTES:
            raise ValueError("CS1 question PDF exceeds the existing content budget")
        package = json.loads(assessment_path.read_text(encoding="utf-8"))
        if (package.get("subject"), package.get("paper")) != ("computer_science", "1"):
            raise ValueError("CS1 content package identity differs")
        raw = package["blueprint"]
        items = _extract_items(raw, subject="computer_science", paper_number="1")
        if not items or items != package.get("items"):
            raise ValueError("CS1 requires complete matching assessed items")
        blueprint = PaperBlueprint.model_validate(raw)
        validate_blueprint(blueprint, load_syllabus())
        if (
            blueprint.paper_number != "1"
            or blueprint.paper_code != "7517/1"
            or blueprint.delivery_mode != "on-screen"
            or blueprint.total_marks != 100
            or [q.number for q in blueprint.questions] != list(range(1, 13))
        ):
            raise ValueError("CS1 content policy requires the complete on-screen paper")
        public = [
            (q.stem, [p.prompt for p in q.parts], candidate_stimulus_data(q.stimulus))
            for q in blueprint.questions
        ]
        if len(json.dumps(public)) > _MAX_SOURCE_CHARACTERS:
            raise ValueError("CS1 source exceeds the existing public-content budget")
        if any(
            q.stimulus and q.stimulus.kind not in {"code", "table", "fsm"}
            for q in blueprint.questions
        ):
            raise ValueError(
                "CS1 content policy has no adapter for this declared material"
            )
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise LayoutConformanceError(str(error)) from error

    owners = {q.number: q for q in blueprint.questions}
    expected_prompts = {
        question.number: [
            question.stem,
            *(
                value
                for part in question.parts
                for value in (
                    part.prompt.replace("{q}", f"{question.number:02d}"),
                    *(f"{option.label} {option.text}" for option in part.options),
                )
            ),
        ]
        for question in blueprint.questions
    }
    source_text = {}
    for question in blueprint.questions:
        components = list(expected_prompts[question.number])
        if question.stimulus:
            declared = question.stimulus
            components.extend(
                [
                    declared.title,
                    declared.code,
                    *declared.lines,
                    " ".join(declared.headers),
                    *(" ".join(row) for row in declared.rows),
                ]
            )
        source_text[question.number] = [
            _normalise(value) for value in components if value.strip()
        ]
    printed: dict[int, list[str]] = {number: [] for number in owners}
    code: dict[int, list[str]] = {number: [] for number in owners}
    circles: dict[int, list[tuple[float, float]]] = {number: [] for number in owners}
    starts: list[int] = []
    parts: list[tuple[int, str]] = []
    marks: list[int] = []
    bodies: set[bytes] = set()
    current = None
    body_text = []
    with pymupdf.open(pdf_path) as document:  # type: ignore[no-untyped-call]
        actual_count = len(document)
        if not 2 <= actual_count <= _MAX_PAGES:
            raise LayoutConformanceError(
                "CS1 exceeds the existing bounded PDF page budget"
            )
        for index, page in enumerate(document):
            if (
                page.rotation
                or abs(page.rect.width - 595.32) > 1
                or abs(page.rect.height - 841.92) > 1
            ):
                raise LayoutConformanceError("CS1 requires unrotated A4 pages")
            text = page.get_text()
            if (
                not text.strip()
                or "There are no questions printed on this page" in text
            ):
                raise LayoutConformanceError(
                    "CS1 contains an empty or invented blank page"
                )
            if index == 0:
                if not all(
                    value in _normalise(text)
                    for value in (
                        blueprint.paper_code,
                        "Paper 1",
                        "COMPUTER SCIENCE",
                        str(blueprint.total_marks),
                    )
                ):
                    raise LayoutConformanceError(
                        "CS1 cover identity differs from its source"
                    )
                continue  # Identified, nonempty cover; no assessed rows live here.
            words = page.get_text("words")
            anchors = _markers(words)
            for _y, number, label in anchors:
                if number not in owners:
                    raise LayoutConformanceError("CS1 has an unassessed printed owner")
                if label is None:
                    starts.append(number)
                else:
                    parts.append((number, label))
            body = _normalise(page.get_text(clip=pymupdf.Rect(40, 70, 550, 770)))  # type: ignore[no-untyped-call]
            fingerprint = hashlib.sha256(body.encode()).digest()
            if not body or body == "END OF QUESTIONS" or fingerprint in bodies:
                raise LayoutConformanceError("CS1 has body-empty or duplicate padding")
            bodies.add(fingerprint)
            body_text.append(body)
            if not any(
                len(_normalise(line)) >= 8
                and any(
                    _normalise(line) in component
                    for components in source_text.values()
                    for component in components
                )
                for line in page.get_text(
                    clip=pymupdf.Rect(118, 70, 550, 770)  # type: ignore[no-untyped-call]
                ).splitlines()
            ):
                raise LayoutConformanceError(
                    "CS1 page has no declared candidate content"
                )
            spans = [
                s
                for b in page.get_text("dict")["blocks"]
                for line in b.get("lines", [])
                for s in line["spans"]
            ]
            boundaries = [
                (70.0, current),
                *[(y, number) for y, number, _label in anchors],
                (770.0, None),
            ]
            for position in range(len(boundaries) - 1):
                top, owner = boundaries[position]
                bottom = boundaries[position + 1][0]
                if owner is None:
                    continue
                selected = [
                    s
                    for s in spans
                    if top <= s["bbox"][1] < bottom and s["bbox"][0] >= 118
                ]
                printed[owner].extend(
                    s["text"] for s in selected if abs(s["size"] - 7.4) > 0.1
                )
                code[owner].extend(
                    s["text"].rstrip()
                    for s in selected
                    if abs(s["bbox"][0] - 154) < 0.5
                    and abs(s["size"] - 8.5) < 0.1
                    and s["text"].strip()
                )
                for drawing in page.get_drawings():
                    rect = drawing["rect"]
                    if (
                        top <= rect.y0 < bottom
                        and len(drawing["items"]) == 4
                        and all(item[0] == "c" for item in drawing["items"])
                    ):
                        circles[owner].append((rect.width, rect.height))
            if anchors:
                current = anchors[-1][1]
            for span in spans:
                value = span["text"].strip()
                if (
                    not value
                    or value.startswith("Keldin /")
                    or value == "Turn over >"
                    or span["bbox"][3] < 54
                ):
                    continue
                x0, y0, x1, y1 = span["bbox"]
                if not (
                    40 <= x0 <= x1 <= 550 and 54 <= y0 <= y1 <= page.rect.height - 70
                ):
                    raise LayoutConformanceError(
                        "CS1 candidate content escapes its body bounds"
                    )
            marks.extend(int(value) for value in re.findall(r"\[(\d+) marks?\]", body))
    if starts != list(owners) or parts != [
        (q.number, p.label)
        for q in blueprint.questions
        if len(q.parts) != 1
        for p in q.parts
    ]:
        raise LayoutConformanceError(
            "CS1 printed question/part owners are missing or duplicated"
        )
    expected_marks = [p.marks for q in blueprint.questions for p in q.parts]
    if marks != expected_marks or sum(marks) != 100:
        raise LayoutConformanceError("CS1 printed mark allocations differ from source")
    whole = " ".join(body_text)
    if whole.count("END OF QUESTIONS") != 1 or "END OF QUESTIONS" not in body_text[-1]:
        raise LayoutConformanceError("CS1 end marker or trailing content differs")
    for title, _timing in PAPER1_SECTIONS.values():
        if whole.count(title) != 1:
            raise LayoutConformanceError("CS1 section headings differ")
    for timing, count in Counter(t for _title, t in PAPER1_SECTIONS.values()).items():
        if whole.count(timing) != count:
            raise LayoutConformanceError("CS1 section timing differs")
    for question in blueprint.questions:
        text = _normalise(" ".join(printed[question.number]))
        # A copied prompt cannot be hidden under another valid question owner.
        for prompt in {
            value for values in expected_prompts.values() for value in values
        }:
            value = _normalise(prompt)
            if not value:  # Single-part questions may have no separate stem.
                continue
            expected_count = sum(
                component.count(value) for component in source_text[question.number]
            )
            if text.count(value) != expected_count:
                raise LayoutConformanceError(
                    "CS1 source prompt is missing or duplicated in its owner"
                )
        position = 0
        for prompt in expected_prompts[question.number]:
            value = _normalise(prompt)
            if not value:
                continue
            found = text.find(value, position)
            if found < 0:
                raise LayoutConformanceError(
                    f"CS1 omits/truncates source prompt for {question.number}"
                )
            position = found + len(value)
        stimulus = question.stimulus
        if stimulus is None:
            if code[question.number] or circles[question.number]:
                raise LayoutConformanceError(
                    "CS1 has undeclared code or diagram material"
                )
            continue
        if stimulus.title.strip() and _normalise(stimulus.title) not in text:
            raise LayoutConformanceError("CS1 declared material title is missing")
        if stimulus.kind == "code":
            if code[question.number] != [
                line.rstrip() for line in stimulus.code.splitlines() if line.strip()
            ]:
                raise LayoutConformanceError(
                    "CS1 printed code differs from declared source"
                )
        else:
            position = 0
            for row in [stimulus.headers, *stimulus.rows]:
                value = _normalise(" ".join(row))
                found = text.find(value, position)
                if not value or found < 0:
                    raise LayoutConformanceError(
                        "CS1 omits/truncates declared source table"
                    )
                position = found + len(value)
        if stimulus.kind == "fsm":
            source = candidate_stimulus_data(stimulus)
            states = {
                cast(str, source["start_state"]),
                *(
                    state
                    for transition in cast(list[list[str]], source["transitions"])
                    for state in (transition[0], transition[2])
                ),
            }
            outer = sum(
                abs(w - 44) < 0.1 and abs(h - 44) < 0.1
                for w, h in circles[question.number]
            )
            inner = sum(
                abs(w - 36) < 0.1 and abs(h - 36) < 0.1
                for w, h in circles[question.number]
            )
            if outer != len(states) or inner != len(
                cast(list[str], source["accepting_states"])
            ):
                raise LayoutConformanceError(
                    "CS1 declared FSM material is missing or duplicated"
                )
    return {
        "policy": AQA_CS_PAPER1_QUESTION_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": actual_count,
        "checked_questions": len(owners),
        "checked_parts": len(items),
        "checked_marks": sum(marks),
        "blank_padding_pages": 0,
        "independent_source_projection": True,
    }
