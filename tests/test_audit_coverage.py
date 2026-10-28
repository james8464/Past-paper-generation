from __future__ import annotations

import hashlib
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
    paths.append("graphify-out/hidden.py")
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


def reviewed_fixture(tmp_path: Path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    source = tmp_path / "example.py"
    source.write_text("value = 1\n", encoding="utf-8")
    evidence = tmp_path / "docs" / "quality" / "review.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(
        "Reviewed example.py input handling and ownership.\n", encoding="utf-8"
    )
    paths = ["example.py", "docs/quality/review.md"]
    subprocess.run(["git", "add", *paths], cwd=tmp_path, check=True)
    ledger = build_ledger(paths)
    row = next(row for row in ledger["files"] if row["path"] == "example.py")
    row.update(
        status="reviewed",
        reason="Reviewed entry points, failures and ownership; no open finding in this fixture.",
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        review_evidence="docs/quality/review.md",
        review_evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
    )
    return ledger, paths, row


def test_explicit_hash_bound_review_is_valid_and_preserved(tmp_path: Path):
    ledger, paths, row = reviewed_fixture(tmp_path)
    assert validate_ledger(ledger, paths, root=tmp_path) == []
    assert build_ledger(paths, previous=ledger, root=tmp_path) == ledger
    assert row["status"] == "reviewed"


def test_changed_source_invalidates_review_and_regeneration_returns_pending(
    tmp_path: Path,
):
    ledger, paths, _ = reviewed_fixture(tmp_path)
    (tmp_path / "example.py").write_text("value = 2\n", encoding="utf-8")
    assert "stale reviewed source: example.py" in validate_ledger(
        ledger, paths, root=tmp_path
    )
    rebuilt = build_ledger(paths, previous=ledger, root=tmp_path)
    assert rebuilt == build_ledger(paths)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", " "),
        ("source_sha256", "no hash"),
        ("review_evidence_sha256", "0" * 64),
        ("review_evidence", "../outside.md"),
        ("review_evidence", "docs/quality/missing.md"),
        ("review_evidence", None),
        ("classification", "historical-evidence"),
        ("unknown_claim", True),
    ],
)
def test_invalid_review_attestations_refuse_regeneration(tmp_path: Path, field, value):
    ledger, paths, row = reviewed_fixture(tmp_path)
    row[field] = value
    assert validate_ledger(ledger, paths, root=tmp_path)
    with pytest.raises(ValueError):
        build_ledger(paths, previous=ledger, root=tmp_path)


def test_evidence_must_remain_tracked_and_unchanged(tmp_path: Path):
    ledger, paths, _ = reviewed_fixture(tmp_path)
    subprocess.run(
        ["git", "rm", "--cached", "docs/quality/review.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert validate_ledger(ledger, paths, root=tmp_path)
    subprocess.run(["git", "add", "docs/quality/review.md"], cwd=tmp_path, check=True)
    (tmp_path / "docs/quality/review.md").write_text(
        "Different evidence\n", encoding="utf-8"
    )
    assert validate_ledger(ledger, paths, root=tmp_path)


def test_reviewed_status_requires_a_real_repository_root(tmp_path: Path):
    ledger, paths, _ = reviewed_fixture(tmp_path)
    assert validate_ledger(ledger, paths)


def test_source_symlink_cannot_attest_external_bytes(tmp_path: Path):
    ledger, paths, row = reviewed_fixture(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    outside.write_text("outside = True\n", encoding="utf-8")
    try:
        (tmp_path / "example.py").unlink()
        (tmp_path / "example.py").symlink_to(outside)
        row["source_sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
        assert validate_ledger(ledger, paths, root=tmp_path)
    finally:
        outside.unlink()


def test_symlink_loop_is_a_validation_error_not_a_crash(tmp_path: Path):
    ledger, paths, _ = reviewed_fixture(tmp_path)
    source = tmp_path / "example.py"
    source.unlink()
    source.symlink_to("example.py")
    assert validate_ledger(ledger, paths, root=tmp_path)


def test_unknown_ledger_fields_do_not_promote_review_claims(tmp_path: Path):
    ledger, paths, _ = reviewed_fixture(tmp_path)
    ledger["all_approved"] = True
    assert validate_ledger(ledger, paths, root=tmp_path)
    with pytest.raises(ValueError):
        build_ledger(paths, previous=ledger, root=tmp_path)


def test_cli_write_preserves_valid_review_then_invalidates_changed_source(
    tmp_path: Path, monkeypatch
):
    ledger, _, _ = reviewed_fixture(tmp_path)
    destination = tmp_path / LEDGER_PATH
    destination.parent.mkdir()
    ledger = {
        **ledger,
        "files": sorted(
            [*ledger["files"], *build_ledger([LEDGER_PATH])["files"]],
            key=lambda row: row["path"],
        ),
    }
    destination.write_text(json.dumps(ledger), encoding="utf-8")
    subprocess.run(["git", "add", LEDGER_PATH], cwd=tmp_path, check=True)
    monkeypatch.setattr(sys, "argv", ["audit_coverage", str(tmp_path), "--write"])
    assert main() == 0
    assert json.loads(destination.read_text())["files"] == ledger["files"]
    (tmp_path / "example.py").write_text("value = 2\n", encoding="utf-8")
    assert main() == 0
    updated = json.loads(destination.read_text())
    assert (
        next(row for row in updated["files"] if row["path"] == "example.py")["status"]
        == "pending"
    )


def test_cli_write_refuses_invalid_existing_review_without_overwrite(
    tmp_path: Path, monkeypatch
):
    ledger, _, row = reviewed_fixture(tmp_path)
    row["review_evidence"] = "docs/quality/fabricated.md"
    destination = tmp_path / LEDGER_PATH
    destination.parent.mkdir()
    destination.write_text(json.dumps(ledger), encoding="utf-8")
    original = destination.read_bytes()
    monkeypatch.setattr(sys, "argv", ["audit_coverage", str(tmp_path), "--write"])
    assert main() == 1
    assert destination.read_bytes() == original
