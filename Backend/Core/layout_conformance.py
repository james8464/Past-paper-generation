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


def runtime_page_count_policy(family: str, role: str, reference_count: int) -> dict:
    """Generated-content policy is not an observed reference-count range."""
    if family == "edexcel-economics" and role == "mark-scheme":
        return {"kind": EDEXCEL_SCHEME_PAGINATION}
    return {"kind": "exact", "minimum": reference_count, "maximum": reference_count}


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
