from __future__ import annotations

import json
from pathlib import Path

import pymupdf as fitz

from Backend.Core.pdf_accessibility import add_page_structure_tree
from Backend.Core.pdf_validation import extract_pdf_evidence
from tools.paper_fidelity_audit import (
    PrintProfile,
    _print_policy_failures,
    load_print_profile,
)

ROOT = Path(__file__).resolve().parents[1]


def test_print_profiles_define_ci_and_final_qualification_resolutions() -> None:
    profiles = json.loads(
        (ROOT / "Resources" / "print-profiles.json").read_text(encoding="utf-8")
    )

    assert profiles["schema_version"] == 1
    assert profiles["profiles"]["ci"]["dpi"] == 300
    assert profiles["profiles"]["qualification"]["dpi"] == 600
    assert profiles["profiles"]["qualification"]["scale_percent"] == 100
    assert profiles["profiles"]["qualification"]["non_printable_margin_mm"] > 0
    assert profiles["profiles"]["qualification"]["minimum_rule_pt"] > 0

    loaded = load_print_profile(
        ROOT / "Resources" / "print-profiles.json",
        "qualification",
    )
    assert loaded == PrintProfile(
        dpi=600,
        scale_percent=100,
        non_printable_margin_mm=5.0,
        monochrome=True,
        minimum_rule_pt=0.35,
        minimum_contrast_ratio=4.5,
        minimum_reading_order_score=0.95,
        require_embedded_fonts=True,
        require_tags=True,
    )


def test_tagged_misorder_still_fails_the_existing_print_profile(tmp_path: Path) -> None:
    path = tmp_path / "tagged-misorder.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 170), "Lower block first")
        page.insert_text((72, 72), "Upper block second")
        document.save(path)
    profile = load_print_profile(
        ROOT / "Resources" / "print-profiles.json", "qualification"
    )
    before = extract_pdf_evidence(path)
    add_page_structure_tree(path)
    after = extract_pdf_evidence(path)

    assert before["tagged"] is False
    assert after["tagged"] is True
    assert (
        before["pages"][0]["reading_order_score"]
        == after["pages"][0]["reading_order_score"]
    )
    assert (
        "page 1 has unstable content-block geometric order; manual reading-order review required"
        in _print_policy_failures(after, profile)
    )
    assert "document has no PDF structure tree" not in _print_policy_failures(
        after, profile
    )
