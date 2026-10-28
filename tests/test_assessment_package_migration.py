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
        match=r"schema version 99.*update Keldin",
    ):
        load_assessment_package(path)


def test_legacy_source_scope_remains_read_only_and_replayable(tmp_path, monkeypatch):
    from Backend.Core import assessment_package as package
    from tests.test_accounting_objectives import paper_for

    path = tmp_path / "legacy-scope.json"
    original = package._extract_items

    def legacy_extract(*args, **kwargs):
        return original(*args, **kwargs, scoped_shared_sources=False)

    legacy_paper = paper_for()
    # New P1 generation no longer invents shared planning extracts. Supply a
    # retained legacy extract explicitly to exercise that historical layout.
    legacy_paper.sections[0].options[0].stimulus = ["Retained legacy shared source."]
    with monkeypatch.context() as legacy:
        legacy.setattr(package, "_extract_items", legacy_extract)
        package.write_assessment_package(
            legacy_paper,
            path,
            subject="accounting",
            paper_number="1",
            preview=True,
            provider=None,
            model=None,
        )
    document = json.loads(path.read_text())
    document.pop("source_scope_version")
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    package.validate_assessment_package(
        path,
        subject="accounting",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )
    assert path.read_bytes() == before
    assert document["items"][0]["context"]


@pytest.mark.parametrize("version", [None, True, -1, 2, "1"])
def test_unknown_source_scope_version_cannot_reinterpret_a_package(tmp_path, version):
    from Backend.Core import assessment_package as package
    from tests.test_accounting_objectives import paper_for

    path = tmp_path / "scope.json"
    package.write_assessment_package(
        paper_for(),
        path,
        subject="accounting",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )
    document = json.loads(path.read_text())
    document["source_scope_version"] = version
    path.write_text(json.dumps(document))
    with pytest.raises(
        AssessmentPackageCompatibilityError, match="source-scope version"
    ):
        package.validate_assessment_package(
            path,
            subject="accounting",
            paper_number="1",
            preview=True,
            provider=None,
            model=None,
        )
