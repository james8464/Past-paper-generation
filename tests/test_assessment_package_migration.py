from __future__ import annotations

import json
from pathlib import Path

import pytest

from Backend.Core.assessment_package import (
    AssessmentPackageCompatibilityError,
    load_assessment_package,
)
from Backend.Core.assessment_quality import item_fingerprint


def test_schema_zero_assessment_package_upgrades_deterministically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 0,
                "subject": "economics_aqa",
                "paper": "1",
                "seed": 42,
                "preview": True,
                "provider": None,
                "model": None,
                "items": [
                    {
                        "id": "1",
                        "prompt": "Explain one effect of a higher interest rate.",
                        "marks": 4,
                        "mark_scheme": ["Identifies and develops one valid effect."],
                    }
                ],
                "blueprint": {"seed": 42},
            }
        ),
        encoding="utf-8",
    )

    first = load_assessment_package(path)
    second = load_assessment_package(path)

    assert first == second
    assert first["schema_version"] == 1
    assert first["form_id"]
    assert first["items"][0]["fingerprint"] == item_fingerprint(
        first["items"][0]["prompt"]
    )


def test_future_assessment_package_version_has_actionable_error(tmp_path: Path) -> None:
    path = tmp_path / "future.json"
    path.write_text('{"schema_version": 99}', encoding="utf-8")

    with pytest.raises(
        AssessmentPackageCompatibilityError,
        match=r"schema version 99.*update Paper Creator",
    ):
        load_assessment_package(path)
