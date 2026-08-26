from __future__ import annotations

import json
from pathlib import Path

import pytest

from Backend.Core.paths import REPO_ROOT
from tools.scaffold_generator_family import ScaffoldRequest, scaffold_family
from tools.validate_generator_migration import MigrationValidator


def test_all_current_families_pass_declarative_migration_validation() -> None:
    validator = MigrationValidator(REPO_ROOT)

    reports = validator.validate_all()

    assert len(reports) == 7
    assert all(report.passed for report in reports), {
        report.family_id: [issue.code for issue in report.issues]
        for report in reports
        if report.issues
    }

    for capability in validator.advertised_capabilities():
        source = validator.entry_point_source(capability)
        assert "Backend.Core.family_adapter" in source
        assert "HostedLLMClient" not in source
        assert "AssessmentCheckpointStore" not in source
        assert "render_pdf_atomically" not in source


def test_broken_fixture_reports_every_onboarding_surface(tmp_path: Path) -> None:
    resources = tmp_path / "Resources"
    family = resources / "example" / "missing-board"
    (family / "generator").mkdir(parents=True)
    (resources / "generator-registry.json").write_text(
        json.dumps(
            {
                "schema_version": 4,
                "qualification": "a-level",
                "families": [
                    {
                        "manifest_version": 1,
                        "id": "missing-board/example",
                        "board": "missing-board",
                        "subject": "example",
                        "app_subject": "example",
                        "app_board": "missing-board",
                        "backend_subject": "example_missing",
                        "resource_path": "example/missing-board",
                        "python_path": "example/missing-board/generator",
                        "package": "examplegen",
                        "entry_point": "examplegen.cli:generate_package",
                        "syllabus_path": "example/missing-board/generator/data/syllabus.json",
                        "subject_plugin": "missing-plugin",
                        "board_profile": "missing-profile",
                        "specification_version": "test",
                        "blueprint_version": "test",
                        "content_mode": "ai-assisted",
                        "supported_providers": ["ollama"],
                        "advertised": True,
                        "declared_papers": ["1"],
                        "outputs_by_paper": {"1": ["question_paper"]},
                        "papers": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = MigrationValidator(tmp_path).validate(family)

    codes = {issue.code for issue in report.issues}
    assert {
        "schema",
        "catalog",
        "package",
        "paper-mapping",
        "syllabus",
        "blueprint",
        "subject-plugin",
        "output-role",
        "layout-profile",
        "fidelity-threshold",
        "matrix",
        "packaging",
        "swift-decoding",
        "backend-dispatch",
    } <= codes


def test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    request = ScaffoldRequest(
        subject="geology",
        board="aqa",
        papers=("1", "2"),
        destination=tmp_path,
    )

    root = scaffold_family(request)

    assert (root / "generator" / "capability.json").is_file()
    assert (root / "generator" / "data" / "syllabus.json").is_file()
    assert (root / "generator" / "geologyaqagen" / "cli.py").is_file()
    assert (root / "generator" / "tests" / "test_preview.py").is_file()
    payload = json.loads((root / "generator" / "capability.json").read_text())
    assert payload["advertised"] is False
    assert payload["declared_papers"] == ["1", "2"]

    with pytest.raises(FileExistsError, match="already exists"):
        scaffold_family(request)
