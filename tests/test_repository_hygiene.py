from __future__ import annotations

import json
from pathlib import Path

from tools.repository_hygiene import classify_path, inspect_repository

ROOT = Path(__file__).resolve().parents[1]


def test_every_tracked_file_has_a_durable_classification() -> None:
    report = inspect_repository(ROOT)

    assert report["unclassified"] == []
    assert report["forbidden"] == []
    assert sum(report["counts"].values()) == report["tracked_files"]


def test_committed_inventory_matches_the_current_repository() -> None:
    committed = json.loads(
        (ROOT / "Resources" / "repository-inventory.json").read_text(
            encoding="utf-8"
        )
    )

    assert committed == inspect_repository(ROOT)


def test_generated_and_binary_outputs_are_rejected() -> None:
    assert classify_path("tmp/paper.pdf").error == "generated output path"
    assert classify_path("macOS/build/PaperCreator.app/data").error == "build output path"
    assert classify_path("Backend/Core/__pycache__/module.pyc").error == "cache path"
    assert classify_path("release/PaperCreator.dmg").error == "unapproved binary artifact"


def test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs() -> None:
    assert classify_path("Design/AppIcon/icon.png").category == "design-resource"
    assert classify_path(
        "macOS/PaperCreator/Assets.xcassets/AppIcon.appiconset/icon.png"
    ).category == "runtime-resource"
    assert classify_path("screenshots/random.png").error == "unapproved binary artifact"


def test_root_lint_configuration_is_release_configuration() -> None:
    assert classify_path("ruff.toml").category == "build-release-configuration"


def test_macos_build_tools_do_not_carry_an_unused_ios_simulator_path() -> None:
    makefile = (ROOT / "macOS" / "Makefile").read_text(encoding="utf-8")

    assert "APP_PLATFORM := macos" not in makefile
    assert "APP_PLATFORM),ios" not in makefile
    assert "SIM_NAME" not in makefile
    assert not (ROOT / "macOS" / "scripts" / "resolve_sim_destination.sh").exists()
    assert not (ROOT / "macOS" / "scripts" / "run_app_ios_sim.sh").exists()
