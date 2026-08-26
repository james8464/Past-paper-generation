from __future__ import annotations

import json
from pathlib import Path

import pymupdf as fitz

from Backend.Core.layout_master import (
    LayoutConformanceError,
    PageCountPolicy,
    conform_pdf_to_box_template,
)
from Backend.Core.paths import REPO_ROOT

REGISTRY_PATH = REPO_ROOT / "Resources" / "layout-master-runtime.json"


def conform_generated_documents(
    subject: str,
    paper: str,
    paths: dict[str, Path],
) -> None:
    if not REGISTRY_PATH.exists():
        return
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    record = registry.get("papers", {}).get(f"{subject}:{paper}")
    if not record:
        return
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
