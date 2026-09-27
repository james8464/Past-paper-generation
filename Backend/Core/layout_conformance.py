from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf as fitz

from Backend.Core.layout_master import (
    LayoutConformanceError,
    PageCountPolicy,
    conform_pdf_to_box_template,
)
from Backend.Core.paths import REPO_ROOT

REGISTRY_PATH = REPO_ROOT / "Resources" / "layout-master-runtime.json"
EDEXCEL_SCHEME_PAGINATION = "generated-edexcel-mark-scheme-content-v1"
AQA_CS_SCHEME_PAGINATION = "generated-aqa-cs-paper2-mark-scheme-content-v1"


def runtime_page_count_policy(
    family: str, role: str, reference_count: int, *, paper: str | None = None
) -> dict:
    """Generated-content policy is not an observed reference-count range."""
    if family == "edexcel-economics" and role == "mark-scheme":
        return {"kind": EDEXCEL_SCHEME_PAGINATION}
    if family == "aqa-computer-science" and role == "mark-scheme" and paper == "2":
        return {"kind": AQA_CS_SCHEME_PAGINATION}
    return {"kind": "exact", "minimum": reference_count, "maximum": reference_count}


def _aqa_cs_printed_credit(
    pdf_path: Path, assessment_path: Path | None, reference_count: int
) -> dict:
    """Content-driven pagination must preserve every published marking statement."""
    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.open_credit import printed_credit_points

    if assessment_path is None:
        raise LayoutConformanceError("Content-driven CS pagination requires its assessment package")
    package = json.loads(assessment_path.read_text(encoding="utf-8"))
    if package.get("subject") != "computer_science" or str(package.get("paper")) != "2":
        raise LayoutConformanceError("Content-driven CS pagination package identity differs")
    blueprint = package.get("blueprint") or {}
    items = _extract_items(blueprint, subject="computer_science", paper_number="2")
    if not items or package.get("items") != items:
        raise LayoutConformanceError("Content-driven CS pagination requires matching assessed items")
    expected = {}
    levels = {}
    for question in blueprint.get("questions", []):
        for part in question["parts"]:
            identifier = (f"{int(question['number']):02d}", str(part["label"]))
            if identifier in expected:
                raise LayoutConformanceError("Content-driven CS package has duplicate assessed parts")
            marking = part["marking"]
            expected[identifier] = [
                *printed_credit_points(marking),
                *marking.get("accept", []),
                *marking.get("reject", []),
            ]
            levels[identifier] = marking.get("levels", [])
    if len(expected) != len(items):
        raise LayoutConformanceError("Content-driven CS package omits assessed parts")

    def normalise(text: str) -> str:
        return re.sub(r"\s+", "", text)

    def contains_credit(text: str, point: str) -> bool:
        # Keep the extracted word boundaries: removing all whitespace lets
        # "8;" match "18;". Optional internal spacing still accommodates line
        # wrapping and separately drawn mathematical symbols in the PDF.
        characters = normalise(point)
        if not characters:
            return False
        if re.fullmatch(r"[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?(?:/[+\-]?\d+(?:\.\d*)?)?[;.]?", characters):
            # A bare numerical answer is a whole printed statement, not a
            # suffix of a signed value, decimal, fraction or expression. Keep
            # physical lines so a preceding row heading does not become part
            # of the number, while A./R. prefixes remain valid guidance.
            return any(
                normalise(re.sub(r"^[AR]\.\s*", "", line.strip())) == characters
                for line in text.splitlines()
            )
        pattern = r"(?<!\w)" + r"\s*".join(map(re.escape, characters)) + r"(?!\w)"
        return re.search(pattern, text) is not None

    printed_rows = {}
    continued_levels = {}
    previous = None
    previous_page = None
    with fitz.open(pdf_path) as document:
        actual_count = len(document)
        # The five front-matter pages are followed by the renderer's Qu / Pt /
        # guidance columns. Use those columns, not standalone digits in answers
        # or page furniture, to recover the owner of each credit statement.
        for page_number in range(5, actual_count):
            page = document[page_number]
            words = page.get_text("words", sort=False)
            anchors = sorted(
                (word for word in words if 45 <= word[0] < 73
                 and re.fullmatch(r"\d{2}", word[4])),
                key=lambda word: word[1],
            )
            if not anchors:
                raise LayoutConformanceError("Content-driven CS scheme has blank or unassessed padding")
            for index, anchor in enumerate(anchors):
                bottom = anchors[index + 1][1] - 2 if index + 1 < len(anchors) else page.rect.height - 65
                part = "".join(word[4] for word in words
                               if 73 <= word[0] < 106 and abs(word[1] - anchor[1]) < 2)
                guidance_lines = {}
                for word in words:
                    if 106 <= word[0] < 500 and anchor[1] - 2 <= word[1] < bottom:
                        guidance_lines.setdefault(word[5:7], []).append(word[4])
                text = "\n".join(" ".join(line) for line in guidance_lines.values())
                identifier = (anchor[4], part)
                if not part:
                    if (index != 0 or previous is None or previous_page != page_number - 1
                            or anchor[4] != previous[0] or not levels[previous]
                            or previous in continued_levels
                            or not text.startswith("Extended response levels")):
                        raise LayoutConformanceError("Content-driven CS scheme has invalid or duplicate continuation")
                    identifier = previous
                    continued_levels[identifier] = text
                    row_points = levels[identifier]
                else:
                    if identifier not in expected:
                        raise LayoutConformanceError("Content-driven CS scheme has an unassessed question row")
                    if identifier in printed_rows:
                        raise LayoutConformanceError("Content-driven CS scheme has duplicate question rows or pages")
                    printed_rows[identifier] = text
                    row_points = [*expected[identifier], *levels[identifier]]
                if not any(contains_credit(text, point) for point in row_points):
                    raise LayoutConformanceError("Content-driven CS scheme has blank or unassessed padding")
                previous, previous_page = identifier, page_number
    for identifier, points in expected.items():
        printed = printed_rows.get(identifier, "")
        level_text = continued_levels.get(identifier, printed)
        if (any(not contains_credit(printed, point) for point in points)
                or any(not contains_credit(level_text, point) for point in levels[identifier])
                or identifier not in printed_rows):
            raise LayoutConformanceError(
                f"Content-driven CS scheme omits or truncates marking guidance for {'.'.join(identifier)}"
            )
        if identifier in continued_levels and any(contains_credit(printed, point) for point in levels[identifier]):
            raise LayoutConformanceError("Content-driven CS scheme has duplicate levels guidance")
    return {
        "policy": AQA_CS_SCHEME_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": actual_count,
        "checked_parts": len(items),
        "checked_credit_statements": sum(len(expected[key]) + len(levels[key]) for key in expected),
    }


def _edexcel_printed_credit(
    pdf_path: Path, assessment_path: Path | None, paper: str, reference_count: int
) -> dict:
    if assessment_path is None:
        raise LayoutConformanceError(
            "Content-driven Edexcel pagination requires its assessment package"
        )
    package = json.loads(assessment_path.read_text(encoding="utf-8"))
    if package.get("subject") != "economics" or str(package.get("paper")) != paper:
        raise LayoutConformanceError(
            "Content-driven pagination package identity differs"
        )
    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.subjects.economics_contracts import ECONOMICS_CONTRACT_VERSION

    blueprint = package.get("blueprint") or {}
    extracted = _extract_items(blueprint, subject="economics", paper_number=paper)
    if not extracted or package.get("items") != extracted:
        raise LayoutConformanceError(
            "Content-driven pagination requires complete matching assessed items"
        )
    expected = {}
    for question in blueprint.get("questions", []):
        for item in question.get("parts") or [question]:
            identifier = (
                f"{question['number']}({item['label']})"
                if question.get("parts")
                else question["number"]
            )
            contract = item.get("assessment_contract") or {}
            if (
                contract.get("version") != ECONOMICS_CONTRACT_VERSION
                or contract.get("published_scheme") != item.get("mark_scheme")
                or not item.get("mark_scheme")
            ):
                raise LayoutConformanceError(
                    "Content-driven pagination needs complete versioned Edexcel credit"
                )
            expected[identifier] = [
                "Question focus: " + item["prompt"],
                "Allocation: " + item["mark_breakdown"],
                *item["mark_scheme"],
            ]
    if len(expected) != len(extracted):
        raise LayoutConformanceError(
            "Content-driven pagination has missing or duplicate assessed part identifiers"
        )

    def normalise(text: str) -> str:
        return " ".join(text.split())

    by_part = {identifier: [] for identifier in expected}
    with fitz.open(pdf_path) as document:
        page_texts = [page.get_text(sort=False) for page in document]
        actual_count = document.page_count
    current = None
    for page_number, text in enumerate(page_texts, 1):
        if not re.search(r"[A-Za-z]{3}", text):
            raise LayoutConformanceError(
                f"Content-driven scheme has blank padding on page {page_number}"
            )
        # The first three pages are the existing cover and general guidance.
        colophon = (
            normalise(text)
            == "Paper Creator. Independent practice material. Not produced, endorsed or approved by any examination board."
        )
        if (
            page_number > 3
            and not (colophon and page_number == actual_count)
            and not any(
                normalise(point) in normalise(text)
                for points in expected.values()
                for point in points[2:]
            )
        ):
            raise LayoutConformanceError(
                f"Content-driven scheme page {page_number} has no assessed credit"
            )
        for line in text.splitlines():
            if line.strip().endswith(" cont.") and line.strip()[:-6] in expected:
                current = line.strip()[:-6]
                continue
            if line.strip() in expected:
                current = line.strip()
            elif current is not None:
                by_part[current].append(line)
    for identifier, points in expected.items():
        printed = normalise(" ".join(by_part[identifier]))
        for point in points:
            if normalise(point) not in printed:
                raise LayoutConformanceError(
                    f"Content-driven scheme omits or truncates credit for {identifier}: {point}"
                )
    return {
        "policy": EDEXCEL_SCHEME_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": actual_count,
        "checked_parts": len(expected),
        "checked_credit_statements": sum(
            len(points) - 2 for points in expected.values()
        ),
        "complete_printed_credit": True,
        "blank_padding_pages": 0,
    }


def conform_generated_documents(
    subject: str,
    paper: str,
    paths: dict[str, Path],
) -> dict[str, dict]:
    results = {}
    if not REGISTRY_PATH.exists():
        return results
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    record = registry.get("papers", {}).get(f"{subject}:{paper}")
    if not record:
        return results
    for generated_role, master_role in (
        ("question_paper", "question-paper"),
        ("mark_scheme", "mark-scheme"),
        ("source_booklet", "source-booklet"),
    ):
        generated_path = paths.get(generated_role)
        master = record.get(master_role)
        if not generated_path or not master:
            continue
        policy_payload = master.get("page_count_policy")
        if policy_payload and policy_payload.get("kind") == AQA_CS_SCHEME_PAGINATION:
            if subject != "computer_science" or paper != "2" or generated_role != "mark_scheme":
                raise LayoutConformanceError("CS scheme pagination policy cannot apply to this document")
            conform_pdf_to_box_template(
                generated_path, master.get("page_boxes") or master["boxes"],
                expected_page_count=master["page_count"], strict_page_count=False,
            )
            results[generated_role] = _aqa_cs_printed_credit(
                generated_path, paths.get("assessment_package"), int(master["page_count"])
            )
            continue
        if policy_payload and policy_payload.get("kind") == EDEXCEL_SCHEME_PAGINATION:
            if (
                subject != "economics"
                or record.get("family") != "edexcel-economics"
                or generated_role != "mark_scheme"
            ):
                raise LayoutConformanceError(
                    "Edexcel scheme pagination policy cannot apply to this document"
                )
            conform_pdf_to_box_template(
                generated_path,
                master.get("page_boxes") or master["boxes"],
                expected_page_count=master["page_count"],
                strict_page_count=False,
            )
            results[generated_role] = _edexcel_printed_credit(
                generated_path,
                paths.get("assessment_package"),
                paper,
                int(master["page_count"]),
            )
            continue
        policy = (
            PageCountPolicy(
                int(policy_payload["minimum"]),
                int(policy_payload["maximum"]),
            )
            if policy_payload
            else PageCountPolicy.exact(int(master["page_count"]))
        )
        with fitz.open(generated_path) as document:
            actual_page_count = document.page_count
        if not policy.accepts(actual_page_count):
            raise LayoutConformanceError(
                f"{generated_path.name} has {actual_page_count} pages; expected "
                f"{policy.minimum}"
                + (
                    ""
                    if policy.kind == "exact"
                    else f"–{policy.maximum} from the measured multi-year range"
                )
            )
        conform_pdf_to_box_template(
            generated_path,
            master.get("page_boxes") or master["boxes"],
            expected_page_count=master["page_count"],
            strict_page_count=policy.kind == "exact",
        )
    return results
