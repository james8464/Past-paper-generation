from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from Backend.Core.board_profiles import board_profile, board_profile_ids
from Backend.Core.subject_plugins import (
    SubjectValidation,
    discover_subject_plugin,
    subject_plugin_ids,
)


@pytest.mark.parametrize("registry_first", [False, True])
@pytest.mark.parametrize(
    ("module", "class_name", "identifier"),
    [
        ("biology", "BiologyPlugin", "biology"),
        ("chemistry", "ChemistryPlugin", "chemistry"),
        ("computer_science", "ComputerSciencePlugin", "computer-science"),
        ("essay", "EssaySubjectPlugin", "history"),
        ("mathematics", "MathematicsPlugin", "mathematics"),
        ("mathematics", "FurtherMathematicsPlugin", "further-mathematics"),
        ("physics", "PhysicsPlugin", "physics"),
    ],
)
def test_subject_import_order_preserves_discovery(
    module: str, class_name: str, identifier: str, registry_first: bool
) -> None:
    # A clean interpreter prevents pytest's collection order from hiding cycles.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib
import sys

module, class_name, identifier, registry_first = sys.argv[1:]
if registry_first == "True":
    importlib.import_module("Backend.Core.subject_plugins")
subject = importlib.import_module(f"Backend.Core.subjects.{module}")
from Backend.Core.subject_plugins import (
    SubjectPlugin, SubjectValidation, discover_subject_plugin, subject_plugin_ids,
)

plugin = discover_subject_plugin(identifier)
assert isinstance(plugin, getattr(subject, class_name))
assert isinstance(plugin, SubjectPlugin)
assert isinstance(plugin.validate_item(None), SubjectValidation)
assert plugin.validate_item(None).passed is False
assert {
    "accounting", "biology", "business", "chemistry", "computer-science",
    "economics", "english-literature", "further-mathematics", "geography",
    "history", "mathematics", "physics", "psychology", "sociology",
} <= set(subject_plugin_ids())
""",
            module,
            class_name,
            identifier,
            str(registry_first),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_current_subject_and_board_plugins_are_discoverable() -> None:
    assert {"accounting", "business", "computer-science", "economics", "mathematics"} <= set(
        subject_plugin_ids()
    )
    assert {"aqa", "cambridge-international", "ocr", "pearson-edexcel"} <= set(
        board_profile_ids()
    )

    plugin = discover_subject_plugin("economics")
    result = plugin.validate_item(
        {"question": "Explain one effect of a higher interest rate.", "marks": 4}
    )

    assert isinstance(result, SubjectValidation)
    assert result.passed is True
    assert board_profile("aqa").page_size == "A4"


@pytest.mark.parametrize(
    "identifier",
    ["../economics", "/tmp/plugin.py", "module:factory", "economics.py"],
)
def test_plugin_discovery_never_imports_arbitrary_paths(identifier: str) -> None:
    with pytest.raises(ValueError, match="unknown subject plugin"):
        discover_subject_plugin(identifier)


def test_board_profile_loader_rejects_traversal() -> None:
    with pytest.raises(ValueError, match="unknown board profile"):
        board_profile(str(Path("..") / "aqa"))
