#!/usr/bin/env python3
"""Track implementation-review scope, without treating inventory as review evidence.

Run with --write after adding tracked files. --include-path stages nothing; it
only includes explicitly named new files when preparing the next commit.
This ledger records pending work and exclusions, not completed semantic reviews.
"""

from __future__ import annotations

import argparse
import json
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
    if path.startswith("graphify-out/") or path in DERIVED:
        classification, status, reason = (
            "generated-metadata",
            "excluded",
            "Derived inventory or graph output; review its maintained producer instead.",
        )
    elif suffix in SOURCE_SUFFIXES:
        classification = (
            "test"
            if path.startswith(("tests/", "macOS/Tests/")) or "/tests/" in path
            else "maintained-source"
        )
        status = "pending"
        reason = "No file-level semantic implementation review recorded in this ledger."
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


def build_ledger(paths: Iterable[str]) -> dict[str, object]:
    checked = [_path(path) for path in paths]
    if len(set(checked)) != len(checked):
        raise ValueError("duplicate input coverage path")
    return {"schema_version": 1, "files": [_entry(path) for path in sorted(checked)]}


def validate_ledger(ledger: object, paths: Iterable[str]) -> list[str]:
    expected = set(_path(path) for path in paths)
    if (
        not isinstance(ledger, Mapping)
        or type(ledger.get("schema_version")) is not int
        or ledger.get("schema_version") != 1
    ):
        return ["unsupported coverage schema"]
    rows = ledger.get("files")
    if not isinstance(rows, list):
        return ["coverage files must be a list"]
    errors: list[str] = []
    seen: list[str] = []
    for row in rows:
        try:
            path = _path(row.get("path") if isinstance(row, Mapping) else None)
        except ValueError:
            errors.append("invalid repository-relative coverage entry")
            continue
        seen.append(path)
        if row != _entry(path):
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
        destination.write_text(
            json.dumps(build_ledger(paths), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    try:
        ledger = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Could not read coverage ledger: {type(error).__name__}")
        return 1
    errors = validate_ledger(ledger, paths)
    if errors:
        print("\n".join(errors))
        return 1
    counts = Counter(row["status"] for row in ledger["files"])
    print(
        f"Coverage inventory: {len(paths)} files; {counts['pending']} pending, {counts['excluded']} excluded; no semantic-review completion claim."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
