from __future__ import annotations

import json
from pathlib import Path

from Backend.Core.layout_master import conform_pdf_to_box_template
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
        conform_pdf_to_box_template(
            generated_path,
            master.get("page_boxes") or master["boxes"],
            expected_page_count=master["page_count"],
            strict_page_count=generated_role == "question_paper",
        )
