from __future__ import annotations

import ast
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = {"Backend", "Resources", "tools", "tests", "bridge.py", "conftest.py"}
CATALOGUES = (
    "tree_case_authoring.py",
    "system_case_authoring.py",
    "database_case_authoring.py",
    "synthesized_authoring.py",
    "extended_pipeline.py",
    "expanded_pipeline.py",
)


def _configuration():
    return tomllib.loads((ROOT / "ruff.toml").read_text(encoding="utf-8"))


def test_formatter_exclusions_match_exact_raw_byte_catalogue_inputs():
    root = ROOT / "Backend/Core/france"
    expected = set()
    for name in CATALOGUES:
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        expected.update(
            "Backend/Core/france/" + node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.endswith(".py")
        )
    excluded = _configuration().get("format", {}).get("exclude", [])
    assert len(expected) == 29
    assert len(excluded) == len(set(excluded))
    assert set(excluded) == expected


def test_ci_format_and_lint_cover_maintained_roots_and_root_entrypoints():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    commands = [
        shlex.split(line.strip().removeprefix("run: "))
        for line in workflow.splitlines()
        if line.strip().startswith("run: ruff ")
    ]
    assert any(
        command[:3] == ["ruff", "format", "--check"] and set(command[3:]) == SCOPE
        for command in commands
    )
    assert any(
        command[:2] == ["ruff", "check"] and set(command[2:]) == SCOPE
        for command in commands
    )


def test_formatter_exclusions_do_not_remove_historical_code_from_lint():
    configuration = _configuration()
    assert configuration["lint"]["select"] == [
        "E4",
        "E7",
        "E9",
        "F",
        "I",
        "UP",
        "B",
        "SIM",
        "RUF",
    ]
    excluded = configuration.get("format", {}).get("exclude", [])
    assert excluded, (
        "formatter boundary must be configured before checking lint coverage"
    )
    listed = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--show-files", *excluded],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert {
        Path(line).relative_to(ROOT).as_posix() for line in listed.stdout.splitlines()
    } == set(excluded)
