from __future__ import annotations

import plistlib
from pathlib import Path

import pytest

from tools.release_compliance import _check_privacy_manifest, inspect_release_compliance

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_RUNTIME_REASONS = {
    "NSPrivacyAccessedAPICategoryUserDefaults": {"CA92.1"},
    "NSPrivacyAccessedAPICategoryFileTimestamp": {"C617.1", "3B52.1"},
    "NSPrivacyAccessedAPICategoryDiskSpace": {"E174.1", "85F4.1"},
    "NSPrivacyAccessedAPICategorySystemBootTime": {"35F9.1"},
}


def test_privacy_manifest_covers_actual_packaged_runtime_api_use():
    payload = plistlib.loads((ROOT / "macOS/Keldin/PrivacyInfo.xcprivacy").read_bytes())
    declared = {
        item["NSPrivacyAccessedAPIType"]: set(item["NSPrivacyAccessedAPITypeReasons"])
        for item in payload["NSPrivacyAccessedAPITypes"]
    }
    assert declared == REQUIRED_RUNTIME_REASONS


@pytest.mark.parametrize(
    ("category", "reason"),
    [
        (category, reason)
        for category, reasons in REQUIRED_RUNTIME_REASONS.items()
        for reason in sorted(reasons)
    ],
)
def test_preflight_rejects_missing_packaged_runtime_reason(
    tmp_path: Path, category: str, reason: str
):
    payload = plistlib.loads((ROOT / "macOS/Keldin/PrivacyInfo.xcprivacy").read_bytes())
    payload["NSPrivacyAccessedAPITypes"] = [
        {
            "NSPrivacyAccessedAPIType": name,
            "NSPrivacyAccessedAPITypeReasons": sorted(reasons - {reason})
            if name == category
            else sorted(reasons),
        }
        for name, reasons in REQUIRED_RUNTIME_REASONS.items()
    ]
    manifest = tmp_path / "macOS/Keldin/PrivacyInfo.xcprivacy"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(plistlib.dumps(payload))
    failures: list[str] = []
    assert not _check_privacy_manifest(tmp_path, failures)
    assert any(category in failure for failure in failures)


def test_sandbox_allows_the_apps_print_command():
    payload = plistlib.loads((ROOT / "macOS/Keldin/Keldin.entitlements").read_bytes())
    assert payload.get("com.apple.security.print") is True


def test_signed_build_settings_are_optional_and_forwarded():
    makefile = (ROOT / "macOS/Makefile").read_text()
    assert 'CODE_SIGN_IDENTITY="$(SIGNING_IDENTITY)"' in makefile
    assert 'DEVELOPMENT_TEAM="$(SIGNING_TEAM)"' in makefile
    assert 'CODE_SIGN_STYLE="$(SIGNING_STYLE)"' in makefile
    assert makefile.count("$(SIGNING_BUILD_SETTINGS)") == 2


def test_release_compliance_passes_for_the_repository() -> None:
    report = inspect_release_compliance(ROOT)

    assert report["passed"] is True
    assert report["failures"] == []
    assert report["checks"] == {
        "bounded_dependencies": True,
        "font_licences": True,
        "privacy_manifest": True,
        "sandbox_entitlements": True,
        "tracked_secrets": True,
    }


def test_release_compliance_detects_a_tracked_secret_signature(tmp_path: Path) -> None:
    report = inspect_release_compliance(
        ROOT,
        additional_text={"example.txt": "token = " + "ghp_" + ("a" * 36)},
    )

    assert report["passed"] is False
    assert any("example.txt" in failure for failure in report["failures"])


def test_release_compliance_rejects_unbounded_runtime_dependencies(
    tmp_path: Path,
) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("unsafe-package>=1\n", encoding="utf-8")

    report = inspect_release_compliance(ROOT, requirement_paths=(requirements,))

    assert report["passed"] is False
    assert any("upper bound" in failure for failure in report["failures"])


def test_release_compliance_is_part_of_local_and_ci_preflight() -> None:
    makefile = (ROOT / "macOS" / "Makefile").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "tools/release_compliance.py" in makefile
    assert "tools/release_compliance.py" in workflow
