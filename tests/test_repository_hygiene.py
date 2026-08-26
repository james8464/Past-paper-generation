from __future__ import annotations

from pathlib import Path

from tools.repository_hygiene import classify_path, inspect_repository

ROOT = Path(__file__).resolve().parents[1]


def test_every_tracked_file_has_a_durable_classification() -> None:
    report = inspect_repository(ROOT)

    assert report["unclassified"] == []
    assert report["forbidden"] == []
    assert sum(report["counts"].values()) == report["tracked_files"]


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
