from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "Resources/computer-science/aqa/generator"


def _isolated_python(script: str, cwd: Path):
    return subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": ""},
        text=True,
        capture_output=True,
        timeout=15,
    )


def test_editable_cspapergen_console_help_resolves_checkout_runtime_away_from_cwd(
    tmp_path,
):
    # An editable package exposes its own source root, not the shared Backend.
    # Isolated Python also removes pytest's root and ambient PYTHONPATH help.
    script = (
        "import importlib.util,sys; "
        "assert importlib.util.find_spec('Backend') is None; "
        f"sys.path.insert(0, {str(GENERATOR)!r}); "
        "from cspapergen.cli import main; raise SystemExit(main(['--help']))"
    )
    result = _isolated_python(script, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "--paper" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_pure_cspapergen_package_import_does_not_bootstrap_runtime(tmp_path):
    script = (
        "import importlib.util,sys; "
        "assert importlib.util.find_spec('Backend') is None; "
        f"sys.path.insert(0, {str(GENERATOR)!r}); "
        "before=list(sys.path); import cspapergen; "
        "assert sys.path == before; assert 'Backend' not in sys.modules"
    )
    result = _isolated_python(script, tmp_path)
    assert result.returncode == 0, result.stderr


def test_detached_cspapergen_command_reports_shared_runtime_requirement(tmp_path):
    copied = tmp_path / "detached"
    shutil.copytree(
        GENERATOR / "cspapergen",
        copied / "cspapergen",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    script = (
        "import importlib.util,sys; "
        "assert importlib.util.find_spec('Backend') is None; "
        f"sys.path.insert(0, {str(copied)!r}); "
        "from cspapergen.cli import main; raise SystemExit(main(['--help']))"
    )
    result = _isolated_python(script, tmp_path)
    assert result.returncode != 0
    assert "needs the shared Keldin Backend runtime" in result.stderr
    assert "not standalone" in result.stderr
