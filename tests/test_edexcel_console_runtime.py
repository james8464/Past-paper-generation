from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "Resources/economics/edexcel-a/generator"


@pytest.mark.parametrize("module", ["pastpapergen", "keldin_edexcel"])
def test_console_script_from_editable_source_resolves_runtime_without_pythonpath(
    tmp_path, module
):
    # An editable installation exposes the generator root, not the checkout's
    # shared Backend package. Model that .pth contract independently of pytest.
    site = tmp_path / "site"
    site.mkdir()
    (site / "editable.pth").write_text(str(GENERATOR) + "\n")
    launcher = tmp_path / module
    launcher.write_text(
        "import site, sys\n"
        f"site.addsitedir({str(site)!r})\n"
        f"from {module}.cli import main\n"
        "sys.exit(main())\n"
    )
    environment = {**os.environ, "PYTHONPATH": ""}
    result = subprocess.run(
        [sys.executable, str(launcher), "--help"],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--paper" in result.stdout
    assert not (tmp_path / "output").exists()


def test_pure_package_import_does_not_bootstrap_shared_runtime(tmp_path):
    script = (
        "import sys; "
        f"sys.path.insert(0, {str(GENERATOR)!r}); "
        "before = list(sys.path); import pastpapergen, keldin_edexcel; "
        "assert sys.path == before; assert 'Backend' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": ""},
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_detached_generator_without_core_reports_runtime_requirement(tmp_path):
    copied = tmp_path / "generator"
    for package in ("pastpapergen", "keldin_edexcel"):
        shutil.copytree(
            GENERATOR / package,
            copied / package,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    script = f"import sys; sys.path.insert(0, {str(copied)!r}); from keldin_edexcel.cli import main; main(['--help'])"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": ""},
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "needs the shared Keldin Backend runtime" in result.stderr
    assert "wheel alone is not standalone" in result.stderr
