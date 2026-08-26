#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
)
TEXT_SUFFIXES = {
    "",
    ".json",
    ".md",
    ".plist",
    ".py",
    ".sh",
    ".swift",
    ".toml",
    ".txt",
    ".xcprivacy",
    ".yml",
    ".yaml",
}


def inspect_release_compliance(
    root: Path,
    *,
    requirement_paths: Iterable[Path] | None = None,
    additional_text: Mapping[str, str] | None = None,
) -> dict[str, object]:
    root = root.resolve()
    failures: list[str] = []
    requirements = tuple(requirement_paths or (
        root / "requirements-build.txt",
        root / "requirements-test.txt",
    ))

    checks = {
        "bounded_dependencies": _check_dependencies(requirements, failures),
        "font_licences": _check_font_licences(root, failures),
        "privacy_manifest": _check_privacy_manifest(root, failures),
        "sandbox_entitlements": _check_entitlements(root, failures),
        "tracked_secrets": _check_secrets(root, failures, additional_text or {}),
    }
    return {
        "schema_version": 1,
        "passed": not failures,
        "checks": checks,
        "failures": sorted(failures),
    }


def _check_dependencies(paths: Iterable[Path], failures: list[str]) -> bool:
    before = len(failures)
    for path in paths:
        if not path.is_file():
            failures.append(f"missing dependency manifest: {path}")
            continue
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.split("#", 1)[0].strip()
            if not line or line.startswith(("-e ", "--")):
                continue
            requirement = line.split(";", 1)[0].strip()
            if "<" not in requirement and "==" not in requirement:
                failures.append(
                    f"{path.name}:{line_number} dependency requires an upper bound"
                )
    return len(failures) == before


def _check_font_licences(root: Path, failures: list[str]) -> bool:
    before = len(failures)
    font_root = root / "Backend" / "Core" / "fonts"
    for font in sorted(font_root.rglob("*.ttf")):
        licence = font.parent / "OFL.txt"
        if not licence.is_file() or "SIL OPEN FONT LICENSE" not in licence.read_text(
            encoding="utf-8", errors="ignore"
        ).upper():
            failures.append(f"font has no bundled SIL OFL licence: {font.relative_to(root)}")
    return len(failures) == before


def _load_plist(path: Path, failures: list[str]) -> dict[str, object] | None:
    try:
        with path.open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as error:
        failures.append(f"invalid plist {path.name}: {error}")
        return None
    if not isinstance(payload, dict):
        failures.append(f"plist root is not a dictionary: {path.name}")
        return None
    return payload


def _check_privacy_manifest(root: Path, failures: list[str]) -> bool:
    before = len(failures)
    payload = _load_plist(
        root / "macOS" / "PaperCreator" / "PrivacyInfo.xcprivacy",
        failures,
    )
    if payload is not None:
        if payload.get("NSPrivacyTracking") is not False:
            failures.append("privacy manifest must explicitly disable tracking")
        if not isinstance(payload.get("NSPrivacyCollectedDataTypes"), list):
            failures.append("privacy manifest must declare collected-data types")
        accessed = payload.get("NSPrivacyAccessedAPITypes")
        if not isinstance(accessed, list) or not accessed:
            failures.append("privacy manifest must declare required-reason APIs")
    return len(failures) == before


def _check_entitlements(root: Path, failures: list[str]) -> bool:
    before = len(failures)
    app = _load_plist(
        root / "macOS" / "PaperCreator" / "PaperCreator.entitlements",
        failures,
    )
    helper = _load_plist(
        root / "macOS" / "PaperCreator" / "PaperCreatorBackend.entitlements",
        failures,
    )
    if app is not None:
        required = {
            "com.apple.security.app-sandbox": True,
            "com.apple.security.files.user-selected.read-write": True,
            "com.apple.security.network.client": True,
        }
        for key, expected in required.items():
            if app.get(key) is not expected:
                failures.append(f"app entitlement {key} must be {expected}")
    if helper is not None:
        for key in ("com.apple.security.app-sandbox", "com.apple.security.inherit"):
            if helper.get(key) is not True:
                failures.append(f"helper entitlement {key} must be true")
    return len(failures) == before


def _tracked_paths(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        root / value.decode()
        for value in completed.stdout.split(b"\0")
        if value
    ]


def _check_secrets(
    root: Path,
    failures: list[str],
    additional_text: Mapping[str, str],
) -> bool:
    before = len(failures)
    candidates: list[tuple[str, str]] = []
    for path in _tracked_paths(root):
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        relative = str(path.relative_to(root))
        if relative.startswith("graphify-out/"):
            continue
        candidates.append((relative, path.read_text(encoding="utf-8", errors="ignore")))
    candidates.extend(additional_text.items())
    for name, text in candidates:
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            failures.append(f"possible tracked secret: {name}")
    return len(failures) == before


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify dependency, licence, privacy, entitlement, and secret release gates."
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = inspect_release_compliance(args.root)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
