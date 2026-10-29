from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path

import pytest

from tools.scaffold_generator_family import ScaffoldRequest, scaffold_family
from tools.validate_generator_migration import MigrationValidator


@pytest.mark.parametrize("version", [4.0, 5.0, [], {}, True, False])
def test_registry_schema_requires_an_exact_supported_integer(tmp_path, version):
    path = tmp_path / "Resources/generator-registry.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps({"schema_version": version, "families": [{"advertised": True}]})
    )
    with pytest.raises(ValueError, match="registry"):
        MigrationValidator(tmp_path, run_preview=False).advertised_capabilities()


@pytest.mark.parametrize(
    "content",
    [
        None,
        "{broken",
        "[]",
        '{"families": []}',
        '{"schema_version":5,"families":[{"advertised":false}]}',
    ],
)
def test_migration_all_refuses_missing_malformed_or_empty_advertised_registry(
    tmp_path, content
):
    if content is not None:
        path = tmp_path / "Resources/generator-registry.json"
        path.parent.mkdir()
        path.write_text(content)
    with pytest.raises(ValueError, match=r"registry|advertised"):
        MigrationValidator(tmp_path, run_preview=False).validate_all()


@pytest.mark.parametrize(
    "subject,papers",
    [
        ("123", ("1",)),
        ("geology", ("1", "1")),
        ("geology", (" 1", "2")),
        ("geology", (1,)),
    ],
)
def test_scaffold_refuses_invalid_module_identifiers_and_paper_ids(
    tmp_path, subject, papers
):
    with pytest.raises(ValueError):
        ScaffoldRequest(
            subject=subject, board="aqa", papers=papers, destination=tmp_path
        )
    assert list(tmp_path.iterdir()) == []


def test_generated_fail_closed_test_actually_calls_the_adapter(tmp_path, monkeypatch):
    root = scaffold_family(
        ScaffoldRequest(
            subject="geology",
            board="aqa",
            papers=("1",),
            destination=tmp_path / "families",
        )
    )
    monkeypatch.syspath_prepend(str(root / "generator"))
    test_path = root / "generator/tests/test_preview.py"
    specification = importlib.util.spec_from_file_location(
        "scaffold_guard_test", test_path
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.generate_package = lambda **_kwargs: {}
    arguments = (
        {"tmp_path": tmp_path / "output"}
        if "tmp_path"
        in inspect.signature(module.test_scaffold_is_fail_closed).parameters
        else {}
    )
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        module.test_scaffold_is_fail_closed(**arguments)


def test_dependency_gate_states_its_actual_manifest_scope():
    from tools.release_compliance import inspect_release_compliance

    root = Path(__file__).resolve().parents[1]
    report = inspect_release_compliance(root)
    assert report["dependency_scope"]["editable_project_constraints_checked"] is False
    assert report["dependency_scope"]["transitive_resolution_checked"] is False
    assert report["dependency_scope"]["manifests"] == [
        "requirements-build.txt",
        "requirements-test.txt",
    ]


def test_current_advertised_inventory_still_validates_without_preview_generation():
    root = Path(__file__).resolve().parents[1]
    reports = MigrationValidator(root, run_preview=False).validate_all()
    assert len(reports) == 7
    assert all(report.passed for report in reports)
