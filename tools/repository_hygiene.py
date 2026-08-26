#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

BINARY_SUFFIXES = {
    ".app",
    ".dmg",
    ".doc",
    ".docx",
    ".exe",
    ".mov",
    ".mp4",
    ".pdf",
    ".pkg",
    ".ppt",
    ".pptx",
    ".pyc",
    ".tar",
    ".tgz",
    ".wav",
    ".xls",
    ".xlsx",
    ".zip",
}
ROOT_FILES = {
    ".gitignore": "build-release-configuration",
    ".graphifyignore": "durable-derived-configuration",
    "AGENTS.md": "documentation",
    "README.md": "documentation",
    "bridge.py": "runtime-source",
    "conftest.py": "test",
    "pytest.ini": "test-configuration",
    "requirements-build.txt": "build-release-configuration",
    "requirements-test.txt": "test-configuration",
}


@dataclass(frozen=True)
class Classification:
    category: str | None = None
    error: str | None = None


def classify_path(value: str) -> Classification:
    path = PurePosixPath(value)
    parts = path.parts
    lowered = {part.casefold() for part in parts}
    if parts and parts[0] == "tmp":
        return Classification(error="generated output path")
    if lowered & {"build", "deriveddata", "dist"} or any(
        part.casefold().endswith(".app") for part in parts
    ):
        return Classification(error="build output path")
    if lowered & {"__pycache__", ".pytest_cache", ".ruff_cache", "cache"}:
        return Classification(error="cache path")
    if path.name == ".DS_Store":
        return Classification(error="system metadata")

    suffix = path.suffix.casefold()
    approved_image = (
        parts[:2] == ("Design", "AppIcon")
        or "Assets.xcassets" in value
        or value.startswith("docs/project-analysis/ui-audit-")
    )
    if suffix in BINARY_SUFFIXES or (suffix in {".png", ".jpg", ".jpeg"} and not approved_image):
        return Classification(error="unapproved binary artifact")

    if value in ROOT_FILES:
        return Classification(category=ROOT_FILES[value])
    if value.startswith("Backend/"):
        return Classification(category="runtime-source")
    if value.startswith("Resources/"):
        category = "test" if "/tests/" in value else "runtime-resource"
        return Classification(category=category)
    if value.startswith("macOS/Tests/"):
        return Classification(category="test")
    if value.startswith("macOS/PaperCreator/"):
        category = "runtime-resource" if "Assets.xcassets" in value else "runtime-source"
        return Classification(category=category)
    if value.startswith("macOS/"):
        return Classification(category="build-release-configuration")
    if value.startswith("tests/"):
        return Classification(category="test")
    if value.startswith("tools/"):
        return Classification(category="tooling")
    if value.startswith("docs/"):
        return Classification(category="documentation")
    if value.startswith("graphify-out/"):
        return Classification(category="durable-derived-metadata")
    if value.startswith(".github/"):
        return Classification(category="build-release-configuration")
    if value.startswith(".codex/"):
        return Classification(category="development-configuration")
    if value.startswith("Design/"):
        return Classification(category="design-resource")
    return Classification(error="unclassified tracked file")


def inspect_repository(root: Path) -> dict[str, object]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = [value.decode() for value in completed.stdout.split(b"\0") if value]
    counts: Counter[str] = Counter()
    forbidden: list[dict[str, str]] = []
    unclassified: list[str] = []
    for path in paths:
        result = classify_path(path)
        if result.category:
            counts[result.category] += 1
        elif result.error == "unclassified tracked file":
            unclassified.append(path)
        else:
            forbidden.append({"path": path, "reason": result.error or "forbidden"})
    return {
        "schema_version": 1,
        "tracked_files": len(paths),
        "counts": dict(sorted(counts.items())),
        "unclassified": sorted(unclassified),
        "forbidden": sorted(forbidden, key=lambda value: value["path"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify tracked files and reject generated repository debris."
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = inspect_repository(args.root.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if report["unclassified"] or report["forbidden"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
