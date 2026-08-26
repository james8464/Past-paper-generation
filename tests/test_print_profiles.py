from __future__ import annotations

import json
from pathlib import Path

from tools.paper_fidelity_audit import PrintProfile, load_print_profile

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
