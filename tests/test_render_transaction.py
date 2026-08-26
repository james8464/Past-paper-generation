from __future__ import annotations

import time
from pathlib import Path

import pymupdf as fitz
import pytest

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
