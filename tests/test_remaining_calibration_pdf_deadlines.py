from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "name", ["ocr_computer_science_calibration", "difficulty_calibration"]
)
@pytest.mark.parametrize("scenario", ["timeout", "zero-pages", "success"])
def test_remaining_calibration_tools_use_the_bounded_pdf_boundary(
    name, scenario, monkeypatch
):
    module = importlib.import_module(f"tools.{name}")
    path = Path("candidate document.pdf")

    def run(command, **kwargs):
        if scenario == "timeout":
            raise subprocess.TimeoutExpired(command, 30)
        if scenario == "zero-pages":
            return SimpleNamespace(stdout="Pages: 0\n")
        assert kwargs["timeout"] == 30
        assert command == ["pdftotext", "-layout", str(path), "-"]
        return SimpleNamespace(stdout=" retained  layout \n")

    monkeypatch.setattr(subprocess, "run", run)
    if scenario == "timeout":
        with pytest.raises(ValueError, match=r"timed out.*candidate document"):
            module._pdf_text(path)
    elif scenario == "zero-pages":
        with pytest.raises(ValueError, match="invalid page count"):
            module._page_count(path)
    else:
        assert module._pdf_text(path) == " retained  layout \n"
