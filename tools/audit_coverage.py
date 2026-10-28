#!/usr/bin/env python3
"""Track implementation-review scope, without treating inventory as review evidence.

Run with --write after adding tracked files. --include-path stages nothing; it
only includes explicitly named new files when preparing the next commit.
Reviews require explicit source and tracked evidence hashes. Inventory and
formatting never create semantic-review attestations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath

LEDGER_PATH = "Resources/implementation-audit-coverage.json"
DERIVED = {LEDGER_PATH, "Resources/repository-inventory.json"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".icns", ".ttf", ".otf"}
SOURCE_SUFFIXES = {
    ".py",
    ".swift",
    ".sh",
    ".command",
    ".js",
    ".ts",
    ".c",
    ".h",
    ".m",
    ".mm",
}


def _path(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or PurePosixPath(value).is_absolute()
        or ".." in PurePosixPath(value).parts
        or str(PurePosixPath(value)) != value
    ):
        raise ValueError("coverage paths must be canonical repository-relative paths")
    return value


def _entry(path: str) -> dict[str, str]:
    suffix = PurePosixPath(path).suffix.casefold()
    if suffix in SOURCE_SUFFIXES:
        classification = (
            "test"
            if path.startswith(("tests/", "macOS/Tests/")) or "/tests/" in path
            else "maintained-source"
        )
        status = "pending"
        reason = "No file-level semantic implementation review recorded in this ledger."
    elif path.startswith("graphify-out/") or path in DERIVED:
        classification, status, reason = (
            "generated-metadata",
            "excluded",
            "Derived inventory or graph output; review its maintained producer instead.",
        )
    elif path.startswith("docs/quality/"):
        classification, status, reason = (
            "historical-evidence",
            "excluded",
            "Retained diagnostic/review evidence, not maintained executable implementation; exclusion does not certify its claims.",
        )
    elif path.startswith("Design/") or suffix in ASSET_SUFFIXES:
        classification, status, reason = (
            "design-asset",
            "excluded",
            "Visual/font asset requires a separate design, rendering and rights review, not a code-practice review.",
        )
    elif path.startswith("docs/") or (
        suffix in {".md", ".txt"}
        and not PurePosixPath(path).name.startswith("requirements")
    ):
        classification, status, reason = (
            "documentation",
            "excluded",
            "Prose/reference material is outside implementation review; content and publication claims are not certified.",
        )
    else:
        status = "pending"
        reason = "No file-level semantic implementation review recorded in this ledger."
        if path.startswith(("tests/", "macOS/Tests/")) or "/tests/" in path:
            classification = "test"
        else:
            classification = "configuration-or-runtime-data"
    return {
        "path": path,
        "classification": classification,
        "status": status,
        "reason": reason,
    }


def build_ledger(
    paths: Iterable[str], *, previous: object = None, root: Path | None = None
) -> dict[str, object]:
    checked = [_path(path) for path in paths]
    if len(set(checked)) != len(checked):
        raise ValueError("duplicate input coverage path")
    reviews: dict[str, Mapping[str, object]] = {}
    if previous is not None:
        prior_paths = (
            [
                row.get("path") if isinstance(row, Mapping) else None
                for row in previous.get("files", [])
            ]
            if isinstance(previous, Mapping) and isinstance(previous.get("files"), list)
            else []
        )
        try:
            errors = validate_ledger(previous, prior_paths, root=root)
        except ValueError as error:
            raise ValueError("invalid prior coverage ledger") from error
        # Source changes require a new review; every other invalid attestation
        # is refused instead of silently laundering it into a clean inventory.
        invalid = [
            error for error in errors if not error.startswith("stale reviewed source: ")
        ]
        if invalid:
            raise ValueError("; ".join(invalid))
        stale = {error.removeprefix("stale reviewed source: ") for error in errors}
        reviews = {
            row["path"]: row
            for row in previous["files"]
            if row.get("status") == "reviewed" and row["path"] not in stale
        }
    return {
        "schema_version": 1,
        "files": [
            dict(reviews[path]) if path in reviews else _entry(path)
            for path in sorted(checked)
        ],
    }


def _review_errors(
    row: Mapping[str, object], path: str, root: Path | None, tracked: set[str]
) -> list[str]:
    baseline = _entry(path)
    fields = set(baseline) | {
        "source_sha256",
        "review_evidence",
        "review_evidence_sha256",
    }
    if (
        set(row) != fields
        or baseline["status"] != "pending"
        or row.get("classification") != baseline["classification"]
        or not isinstance(row.get("reason"), str)
        or not row["reason"].strip()
        or len(row["reason"]) > 4000
        or any(
            not isinstance(row.get(key), str)
            or re.fullmatch(r"[0-9a-f]{64}", row[key]) is None
            for key in ("source_sha256", "review_evidence_sha256")
        )
    ):
        return [f"invalid reviewed attestation: {path}"]
    if root is None:
        return [f"review validation requires repository root: {path}"]
    try:
        evidence = _path(row["review_evidence"])
        if (
            path not in tracked
            or evidence not in tracked
            or PurePosixPath(evidence).suffix.casefold() != ".md"
            or _entry(evidence)["classification"]
            not in {"historical-evidence", "documentation"}
        ):
            raise ValueError("review source and Markdown evidence must be tracked")
        for relative in (path, evidence):
            candidate = root / relative
            if (
                not candidate.resolve().is_relative_to(root.resolve())
                or not candidate.is_file()
            ):
                raise ValueError("review files must exist inside the repository")
        evidence_hash = hashlib.sha256((root / evidence).read_bytes()).hexdigest()
        source_hash = hashlib.sha256((root / path).read_bytes()).hexdigest()
    except (OSError, RuntimeError, ValueError):
        return [f"invalid reviewed evidence: {path}"]
    if evidence_hash != row["review_evidence_sha256"]:
        return [f"changed reviewed evidence: {path}"]
    if source_hash != row["source_sha256"]:
        return [f"stale reviewed source: {path}"]
    return []


def validate_ledger(
    ledger: object, paths: Iterable[str], *, root: Path | None = None
) -> list[str]:
    expected = set(_path(path) for path in paths)
    if (
        not isinstance(ledger, Mapping)
        or set(ledger) != {"schema_version", "files"}
        or type(ledger.get("schema_version")) is not int
        or ledger.get("schema_version") != 1
    ):
        return ["unsupported coverage schema"]
    rows = ledger.get("files")
    if not isinstance(rows, list):
        return ["coverage files must be a list"]
    errors: list[str] = []
    tracked = (
        set(tracked_paths(root))
        if root is not None
        and any(
            isinstance(row, Mapping) and row.get("status") == "reviewed" for row in rows
        )
        else set()
    )
    seen: list[str] = []
    for row in rows:
        try:
            path = _path(row.get("path") if isinstance(row, Mapping) else None)
        except ValueError:
            errors.append("invalid repository-relative coverage entry")
            continue
        seen.append(path)
        if row.get("status") == "reviewed":
            errors.extend(_review_errors(row, path, root, tracked))
        elif row != _entry(path):
            errors.append(f"invalid classification/status/reason: {path}")
    counts = Counter(seen)
    errors.extend(
        f"duplicate coverage: {path}"
        for path, count in sorted(counts.items())
        if count > 1
    )
    errors.extend(
        f"missing coverage: {path}" for path in sorted(expected - counts.keys())
    )
    errors.extend(
        f"untracked coverage: {path}" for path in sorted(counts.keys() - expected)
    )
    if seen != sorted(seen):
        errors.append("coverage entries must be sorted")
    return errors


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    return [path.decode("utf-8") for path in result.stdout.split(b"\0") if path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--include-path", action="append", default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    paths = set(tracked_paths(root))
    for path in args.include_path:
        path = _path(path)
        if not (root / path).is_file():
            parser.error(f"included path is not a file: {path}")
        paths.add(path)
    destination = root / LEDGER_PATH
    if args.write:
        paths.add(LEDGER_PATH)
        try:
            previous = (
                json.loads(destination.read_text(encoding="utf-8"))
                if destination.exists()
                else None
            )
            updated = build_ledger(paths, previous=previous, root=root)
        except (OSError, ValueError) as error:
            print(f"Could not regenerate coverage ledger: {error}")
            return 1
        destination.write_text(
            json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    try:
        ledger = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Could not read coverage ledger: {type(error).__name__}")
        return 1
    errors = validate_ledger(ledger, paths, root=root)
    if errors:
        print("\n".join(errors))
        return 1
    counts = Counter(row["status"] for row in ledger["files"])
    print(
        f"Coverage inventory: {len(paths)} files; {counts['pending']} pending, {counts['excluded']} excluded, {counts['reviewed']} explicitly reviewed; no whole-project semantic-review completion claim."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
