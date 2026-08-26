from __future__ import annotations

from pathlib import Path

import pytest

from Backend.Core.board_profiles import board_profile, board_profile_ids
from Backend.Core.subject_plugins import (
    SubjectValidation,
    discover_subject_plugin,
    subject_plugin_ids,
)


def test_current_subject_and_board_plugins_are_discoverable() -> None:
    assert {"accounting", "business", "computer-science", "economics", "mathematics"} <= set(
        subject_plugin_ids()
    )
    assert {"aqa", "ocr", "pearson-edexcel"} <= set(board_profile_ids())

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
