from __future__ import annotations

import os
import time
from pathlib import Path

import pymupdf as fitz
import pytest

from Backend.Core import render_transaction
from Backend.Core.pdf_accessibility import add_page_structure_tree
from Backend.Core.pdf_validation import extract_pdf_evidence
from Backend.Core.render_transaction import (
    InvalidRenderOutput,
    RenderTimeout,
    render_pdf_atomically,
)


def _write_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.set_metadata({"title": text})
    document.save(path)
    document.close()


def _text(path: Path) -> str:
    with fitz.open(path) as document:
        return "".join(page.get_text() for page in document)


def test_render_pdf_atomically_promotes_a_readable_document(tmp_path: Path) -> None:
    output = tmp_path / "paper.pdf"

    result = render_pdf_atomically(
        output,
        lambda temporary: _write_pdf(temporary, "New paper"),
        role="question paper",
    )

    assert result.path == output
    assert result.pages == 1
    assert result.elapsed_seconds >= 0
    assert "New paper" in _text(output)
    evidence = extract_pdf_evidence(output)
    assert evidence["tagged"] is True
    assert evidence["pages"][0]["reading_order_score"] == 1.0
    with fitz.open(output) as document:
        catalog = document.pdf_catalog()
        assert document.xref_get_key(catalog, "MarkInfo")[1] == "<</Marked true>>"
        assert b"/MCID 0" in document[0].read_contents()
    assert list(tmp_path.glob(".paper.pdf.*.tmp")) == []


def test_render_failure_preserves_an_existing_document(tmp_path: Path) -> None:
    output = tmp_path / "paper.pdf"
    _write_pdf(output, "Existing paper")
    before = output.read_bytes()

    def fail(_temporary: Path) -> None:
        raise RuntimeError("renderer failed")

    with pytest.raises(RuntimeError, match="renderer failed"):
        render_pdf_atomically(output, fail, role="mark scheme")

    assert output.read_bytes() == before
    assert list(tmp_path.glob(".paper.pdf.*.tmp")) == []


def test_invalid_render_output_is_rejected_without_promotion(tmp_path: Path) -> None:
    output = tmp_path / "paper.pdf"

    def write_invalid(temporary: Path) -> None:
        temporary.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(InvalidRenderOutput, match="source booklet"):
        render_pdf_atomically(output, write_invalid, role="source booklet")

    assert not output.exists()
    assert list(tmp_path.glob(".paper.pdf.*.tmp")) == []


def test_render_timeout_is_typed_and_removes_partial_output(tmp_path: Path) -> None:
    output = tmp_path / "paper.pdf"

    def stall(temporary: Path) -> None:
        temporary.write_bytes(b"partial")
        time.sleep(1)

    with pytest.raises(RenderTimeout, match=r"mark scheme.*0.05 seconds"):
        render_pdf_atomically(
            output,
            stall,
            role="mark scheme",
            timeout_seconds=0.05,
        )

    assert not output.exists()
    assert list(tmp_path.glob(".paper.pdf.*.tmp")) == []


def test_success_replaces_an_existing_document(tmp_path: Path) -> None:
    output = tmp_path / "paper.pdf"
    _write_pdf(output, "Old paper")

    render_pdf_atomically(
        output,
        lambda temporary: _write_pdf(temporary, "Replacement paper"),
        role="question paper",
    )

    assert "Replacement paper" in _text(output)
    assert "Old paper" not in _text(output)


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), -float("inf")])
def test_render_rejects_nonfinite_deadlines_before_files_or_signals(
    tmp_path, monkeypatch, timeout
):
    output = tmp_path / "not-created" / "paper.pdf"

    def unexpected_deadline(*_args):
        raise AssertionError("invalid timeout reached signal setup")

    monkeypatch.setattr(render_transaction, "_render_deadline", unexpected_deadline)
    with pytest.raises(ValueError, match="finite"):
        render_pdf_atomically(
            output, lambda _path: None, role="paper", timeout_seconds=timeout
        )
    assert not output.parent.exists()


def test_deadline_setup_failure_restores_previous_handler_and_timer(monkeypatch):
    previous_handler = object()
    state = {"handler": previous_handler, "timer": (12.0, 0.0)}
    calls = []

    def install_handler(_signal, handler):
        state["handler"] = handler

    def arm_timer(_timer, seconds, interval=0.0):
        calls.append((seconds, interval))
        if len(calls) == 1:
            raise OSError("timer setup failed")
        state["timer"] = (seconds, interval)

    monkeypatch.setattr(
        render_transaction.signal, "getsignal", lambda _signal: state["handler"]
    )
    monkeypatch.setattr(
        render_transaction.signal, "getitimer", lambda _timer: state["timer"]
    )
    monkeypatch.setattr(render_transaction.signal, "signal", install_handler)
    monkeypatch.setattr(render_transaction.signal, "setitimer", arm_timer)
    with (
        pytest.raises(OSError, match="timer setup failed"),
        render_transaction._render_deadline("paper", 30),
    ):
        pytest.fail("failed deadline entered its body")
    assert state["handler"] is previous_handler
    assert len(calls) >= 2
    assert 0 < state["timer"][0] <= 12
    assert state["timer"][1] == 0


@pytest.mark.parametrize("operation", ["render", "tag"])
def test_pdf_publication_does_not_unlink_after_success(
    tmp_path, monkeypatch, operation
):
    output = tmp_path / "paper.pdf"
    _write_pdf(output, "Existing paper")
    original_replace = os.replace
    original_unlink = Path.unlink
    committed = False

    def replace(source, destination):
        nonlocal committed
        original_replace(source, destination)
        if Path(destination) == output:
            committed = True

    def unlink(path, *args, **kwargs):
        if committed and path.suffix in {".tmp", ".tagged"}:
            raise PermissionError("cleanup denied after commit")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "replace", replace)
    monkeypatch.setattr(Path, "unlink", unlink)
    if operation == "render":
        render_pdf_atomically(
            output, lambda path: _write_pdf(path, "Replacement paper"), role="paper"
        )
        assert "Replacement paper" in _text(output)
    else:
        add_page_structure_tree(output)
        assert "Existing paper" in _text(output)
    assert committed


@pytest.mark.parametrize("operation", ["render", "tag"])
@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_pdf_cleanup_failure_preserves_original_exception(
    tmp_path, monkeypatch, operation, failure
):
    output = tmp_path / "paper.pdf"
    _write_pdf(output, "Existing paper")
    before = output.read_bytes()
    primary = failure("original PDF operation failed")
    original_unlink = Path.unlink
    failed = False

    def fail(*_args, **_kwargs):
        nonlocal failed
        failed = True
        raise primary

    def unlink(path, *args, **kwargs):
        if failed and path.suffix in {".tmp", ".tagged"}:
            raise PermissionError("cleanup denied")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises(failure) as caught:
        if operation == "render":
            render_pdf_atomically(output, fail, role="paper")
        else:
            monkeypatch.setattr(fitz.Document, "save", fail)
            add_page_structure_tree(output)
    assert caught.value is primary
    assert "cleanup denied" in " ".join(caught.value.__notes__)
    assert output.read_bytes() == before


def test_deadline_rollback_attempts_every_step_and_preserves_setup_failure(monkeypatch):
    previous_handler = object()
    primary = OSError("timer setup failed")
    operations = []
    timer_calls = 0

    def handler(_signal, value):
        operations.append(
            "previous handler" if value is previous_handler else "new handler"
        )
        if value is previous_handler:
            raise PermissionError("handler restoration denied")

    def timer(_timer, _seconds, _interval=0.0):
        nonlocal timer_calls
        timer_calls += 1
        operations.append(f"timer {timer_calls}")
        if timer_calls == 1:
            raise primary
        raise OSError("timer restoration denied")

    monkeypatch.setattr(
        render_transaction.signal, "getsignal", lambda _signal: previous_handler
    )
    monkeypatch.setattr(
        render_transaction.signal, "getitimer", lambda _timer: (12.0, 0.0)
    )
    monkeypatch.setattr(render_transaction.signal, "signal", handler)
    monkeypatch.setattr(render_transaction.signal, "setitimer", timer)
    with (
        pytest.raises(OSError) as caught,
        render_transaction._render_deadline("paper", 30),
    ):
        pytest.fail("failed setup entered body")
    assert caught.value is primary
    assert operations == [
        "new handler",
        "timer 1",
        "timer 2",
        "previous handler",
        "timer 3",
    ]
    notes = " ".join(primary.__notes__)
    assert "handler restoration denied" in notes
    assert "timer restoration denied" in notes


def test_directory_sync_failure_remains_a_real_publication_error(tmp_path, monkeypatch):
    output = tmp_path / "paper.pdf"
    primary = OSError("directory synchronization failed")

    def fail_sync(_path):
        raise primary

    monkeypatch.setattr(render_transaction, "_sync_directory", fail_sync)
    with pytest.raises(OSError) as caught:
        render_pdf_atomically(
            output, lambda path: _write_pdf(path, "Committed paper"), role="paper"
        )
    assert caught.value is primary
    assert "Committed paper" in _text(output)
