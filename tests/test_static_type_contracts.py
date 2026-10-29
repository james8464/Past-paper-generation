from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = """
from collections.abc import Callable
from Backend.Core.json_client import JSONGenerationClient

class MinimalClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {"prompt": prompt}

class WrongReturn:
    def generate_json(self, prompt: str) -> int:
        return 1

class ExtraArgument:
    def generate_json(self, prompt: str, required: str) -> dict[str, object]:
        return {}
"""


def _check(tmp_path: Path, assignment: str) -> subprocess.CompletedProcess[str]:
    checker = shutil.which("mypy")
    assert checker is not None, "Install requirements-test.txt; mypy is a required gate"
    fixture = tmp_path / "client_contract.py"
    fixture.write_text(CLIENTS + assignment, encoding="utf-8")
    return subprocess.run(
        [
            checker,
            "--config-file",
            str(ROOT / "tools/typecheck.ini"),
            "--cache-dir",
            str(tmp_path / "cache"),
            str(fixture),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_minimal_client_and_factory_satisfy_static_contract(tmp_path):
    result = _check(
        tmp_path,
        """
client: JSONGenerationClient = MinimalClient()
def factory(model: str, endpoint: str) -> MinimalClient:
    return MinimalClient()
client_factory: Callable[[str, str], JSONGenerationClient] = factory
""",
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "assignment",
    [
        "client: JSONGenerationClient = WrongReturn()\n",
        "client: JSONGenerationClient = ExtraArgument()\n",
        "def factory(model: str, endpoint: str) -> WrongReturn:\n"
        "    return WrongReturn()\n"
        "client_factory: Callable[[str, str], JSONGenerationClient] = factory\n",
    ],
)
def test_incompatible_client_or_factory_is_rejected_statically(tmp_path, assignment):
    result = _check(tmp_path, assignment)
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.count("error:") == 1, result.stdout
    assert "[assignment]" in result.stdout
