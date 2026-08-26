from __future__ import annotations

from pathlib import Path

from tools.release_compliance import inspect_release_compliance

ROOT = Path(__file__).resolve().parents[1]


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


def test_release_compliance_rejects_unbounded_runtime_dependencies(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("unsafe-package>=1\n", encoding="utf-8")

    report = inspect_release_compliance(ROOT, requirement_paths=(requirements,))

    assert report["passed"] is False
    assert any("upper bound" in failure for failure in report["failures"])


def test_release_compliance_is_part_of_local_and_ci_preflight() -> None:
    makefile = (ROOT / "macOS" / "Makefile").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "tools/release_compliance.py" in makefile
    assert "tools/release_compliance.py" in workflow
