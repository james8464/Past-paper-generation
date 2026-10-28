from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.audit_coverage import LEDGER_PATH, build_ledger, main, validate_ledger


def test_ledger_is_sorted_and_does_not_invent_reviewed_code() -> None:
    paths = ["tests/test_example.py", "Backend/Core/example.py", "ruff.toml"]
    ledger = build_ledger(paths)
    assert ledger == build_ledger(reversed(paths))
    assert [row["path"] for row in ledger["files"]] == sorted(paths)
    assert all(row["status"] == "pending" for row in ledger["files"])
    assert validate_ledger(ledger, paths) == []


def test_future_tracked_file_requires_an_explicit_ledger_entry() -> None:
    ledger = build_ledger(["Backend/Core/old.py"])
    errors = validate_ledger(ledger, ["Backend/Core/old.py", "Backend/Core/new.py"])
    assert "missing coverage: Backend/Core/new.py" in errors


def test_duplicate_and_removed_entries_fail() -> None:
    ledger = build_ledger(["tools/check.py"])
    ledger["files"].append(dict(ledger["files"][0]))
    errors = validate_ledger(ledger, [])
    assert "duplicate coverage: tools/check.py" in errors
    assert "untracked coverage: tools/check.py" in errors


def test_exclusions_are_explicit_and_cannot_hide_runtime_source() -> None:
    paths = [
        "graphify-out/graph.json",
        "Resources/repository-inventory.json",
        "Resources/implementation-audit-coverage.json",
        "Design/AppIcon/front.svg",
        "docs/quality/old-live-diagnostic.md",
        "Backend/Core/france/extended_pipeline.py",
    ]
    ledger = build_ledger(paths)
    rows = {row["path"]: row for row in ledger["files"]}
    assert rows["graphify-out/graph.json"]["status"] == "excluded"
    assert rows["Design/AppIcon/front.svg"]["classification"] == "design-asset"
    assert (
        rows["docs/quality/old-live-diagnostic.md"]["classification"]
        == "historical-evidence"
    )
    assert rows["Backend/Core/france/extended_pipeline.py"]["status"] == "pending"
    assert all(row["reason"].strip() for row in rows.values())
    rows["Backend/Core/france/extended_pipeline.py"]["status"] = "excluded"
    assert (
        "invalid classification/status/reason: Backend/Core/france/extended_pipeline.py"
        in validate_ledger(ledger, paths)
    )


@pytest.mark.parametrize(
    "path",
    ["/tmp/file.py", "../file.py", "a/../file.py", "a\\file.py", "./file.py", ""],
)
def test_paths_must_be_portable_repository_relative(path: str) -> None:
    with pytest.raises(ValueError, match="repository-relative"):
        build_ledger([path])


def test_schema_and_malformed_rows_fail_without_crashing() -> None:
    assert validate_ledger({"schema_version": 9, "files": []}, [])
    assert validate_ledger({"schema_version": 1, "files": [None, {"path": []}]}, [])


def test_build_rejects_duplicate_input_paths() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        build_ledger(["a.py", "a.py"])


def test_source_cannot_be_hidden_by_a_documentation_or_design_directory() -> None:
    paths = ["Design/render.py", "docs/quality/check.sh", "docs/example.js"]
    assert all(row["status"] == "pending" for row in build_ledger(paths)["files"])


def test_cli_checks_actual_tracked_files_and_detects_new_additions(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    ledger = tmp_path / LEDGER_PATH
    ledger.parent.mkdir()
    ledger.write_text(json.dumps(build_ledger([LEDGER_PATH])), encoding="utf-8")
    subprocess.run(["git", "add", LEDGER_PATH], cwd=tmp_path, check=True)
    monkeypatch.setattr(sys, "argv", ["audit_coverage", str(tmp_path)])
    assert main() == 0
    (tmp_path / "new.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "new.py"], cwd=tmp_path, check=True)
    assert main() == 1
    assert "missing coverage: new.py" in capsys.readouterr().out


def test_regeneration_is_deterministic_and_does_not_stage_files(
    tmp_path: Path, monkeypatch
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "Resources").mkdir()
    (tmp_path / "new.py").write_text("value = 1\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["audit_coverage", str(tmp_path), "--write", "--include-path", "new.py"],
    )
    assert main() == 0
    first = (tmp_path / LEDGER_PATH).read_bytes()
    assert main() == 0
    assert (tmp_path / LEDGER_PATH).read_bytes() == first
    assert (
        subprocess.run(
            ["git", "ls-files"], cwd=tmp_path, check=True, capture_output=True
        ).stdout
        == b""
    )
