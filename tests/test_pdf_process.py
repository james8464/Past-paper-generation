from __future__ import annotations

import importlib
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

CALIBRATIONS = [
    ("tools.aqa_accounting_calibration", "_text", "_pages"),
    ("tools.aqa_business_calibration", "_pdf_text", "_page_count"),
    ("tools.ocr_economics_calibration", "_pdf_text", "_page_count"),
]
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("module_name", "text_name", "pages_name"), CALIBRATIONS)
@pytest.mark.parametrize("operation", ["text", "pages"])
def test_calibration_pdf_tools_keep_their_output_and_have_a_finite_deadline(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    text_name: str,
    pages_name: str,
    operation: str,
) -> None:
    path = Path("reference papers") / "exam.pdf"
    output = (
        "Épreuve\n  aligned content\n"
        if operation == "text"
        else "Title: Fixture\nPages: 36\n"
    )
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout=output)

    monkeypatch.setattr(subprocess, "run", run)
    module = importlib.import_module(module_name)
    function = getattr(module, text_name if operation == "text" else pages_name)
    assert function(path) == (output if operation == "text" else 36)
    command, settings = calls[0]
    assert list(command) == (
        ["pdftotext", "-layout", str(path), "-"]
        if operation == "text"
        else ["pdfinfo", str(path)]
    )
    timeout = settings.get("timeout")
    assert isinstance(timeout, (int, float)) and not isinstance(timeout, bool)
    assert math.isfinite(timeout) and timeout > 0
    assert settings["check"] is True
    assert settings["capture_output"] is True
    assert settings["text"] is True


@pytest.mark.parametrize(("module_name", "text_name", "pages_name"), CALIBRATIONS)
@pytest.mark.parametrize("operation", ["text", "pages"])
@pytest.mark.parametrize("failure", ["timeout", "missing", "failed"])
def test_calibration_pdf_failures_identify_the_document_and_tool(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    text_name: str,
    pages_name: str,
    operation: str,
    failure: str,
) -> None:
    path = Path("reference papers") / "damaged exam.pdf"
    tool = "pdftotext" if operation == "text" else "pdfinfo"

    def run(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, timeout=30)
        if failure == "missing":
            raise FileNotFoundError("No such executable")
        raise subprocess.CalledProcessError(1, command, stderr="Cannot open PDF")

    monkeypatch.setattr(subprocess, "run", run)
    module = importlib.import_module(module_name)
    function = getattr(module, text_name if operation == "text" else pages_name)
    with pytest.raises(ValueError) as caught:
        function(path)
    message = str(caught.value)
    assert tool in message
    assert str(path) in message
    assert {
        "timeout": "timed out",
        "missing": "not found",
        "failed": "Cannot open PDF",
    }[failure] in message


@pytest.mark.parametrize(("module_name", "text_name", "pages_name"), CALIBRATIONS)
@pytest.mark.parametrize("output", ["Pages: unknown\n", "Pages: 0\n", "Pages: -1\n"])
def test_invalid_pdf_page_counts_fail_with_document_and_command_context(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    text_name: str,
    pages_name: str,
    output: str,
) -> None:
    path = Path("reference papers") / "invalid.pdf"
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=output)
    )
    function = getattr(importlib.import_module(module_name), pages_name)
    with pytest.raises(ValueError) as caught:
        function(path)
    assert "pdfinfo" in str(caught.value)
    assert str(path) in str(caught.value)


@pytest.mark.parametrize(("module_name", "text_name", "pages_name"), CALIBRATIONS)
def test_calibration_direct_script_help_still_works_outside_the_repository(
    tmp_path: Path,
    module_name: str,
    text_name: str,
    pages_name: str,
) -> None:
    script = ROOT / (module_name.replace(".", "/") + ".py")
    result = subprocess.run(
        [sys.executable, "-E", str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--corpus-root" in result.stdout
