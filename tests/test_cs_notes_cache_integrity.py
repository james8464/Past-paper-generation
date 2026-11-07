from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from cspapergen import notes


@pytest.fixture
def cached_notes(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    pdf = source / "5.1. Number Systems.pdf"
    pdf.write_bytes(b"original context")
    cache = tmp_path / "cache"
    extracted = []

    def extract(pdf_path, text_path):
        extracted.append(pdf_path.read_bytes())
        text_path.write_bytes(pdf_path.read_bytes())

    monkeypatch.setattr(notes, "_extract_text", extract)
    assert notes.cache_notes(source, cache).text_count == 1
    return source, pdf, cache, extracted


@pytest.mark.parametrize("preserve_mtime", [False, True])
def test_equal_size_changed_source_refreshes_raw_text_and_context(
    cached_notes, preserve_mtime
):
    source, pdf, cache, extracted = cached_notes
    before = pdf.stat()
    pdf.write_bytes(b"replaced context")
    if preserve_mtime:
        os.utime(pdf, ns=(before.st_atime_ns, before.st_mtime_ns))

    assert notes.cache_notes(source, cache).text_count == 1
    assert extracted == [b"original context", b"replaced context"]
    assert (cache / "raw" / pdf.name).read_bytes() == b"replaced context"
    assert (cache / "text" / f"{pdf.stem}.txt").read_bytes() == b"replaced context"
    assert notes.note_context_for_topic("4.5", "Number systems", cache) == (
        "replaced context"
    )


def test_unchanged_content_does_not_reextract_after_source_timestamp_change(
    cached_notes,
):
    source, pdf, cache, extracted = cached_notes
    before = pdf.stat()
    os.utime(pdf, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
    assert notes.cache_notes(source, cache).text_count == 1
    assert extracted == [b"original context"]


def test_changed_length_source_refreshes(cached_notes):
    source, pdf, cache, extracted = cached_notes
    pdf.write_bytes(b"a different length")
    assert notes.cache_notes(source, cache).text_count == 1
    assert extracted[-1] == b"a different length"


def test_cancelled_refresh_preserves_old_pair_and_next_call_retries(
    cached_notes, monkeypatch
):
    source, pdf, cache, extracted = cached_notes
    pdf.write_bytes(b"a different length")
    before = pdf.stat()
    os.utime(pdf, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
    original_extract = notes._extract_text

    def cancel(_pdf_path, text_path):
        text_path.write_bytes(b"partial extraction")
        raise KeyboardInterrupt

    monkeypatch.setattr(notes, "_extract_text", cancel)
    with pytest.raises(KeyboardInterrupt):
        notes.cache_notes(source, cache)
    assert (cache / "raw" / pdf.name).read_bytes() == b"original context"
    assert (cache / "text" / f"{pdf.stem}.txt").read_bytes() == b"original context"
    assert sorted(path.name for path in cache.iterdir()) == ["raw", "text"]

    monkeypatch.setattr(notes, "_extract_text", original_extract)
    assert notes.cache_notes(source, cache).text_count == 1
    assert extracted[-1] == b"a different length"


def test_raw_publication_failure_leaves_old_hash_so_next_call_retries(
    cached_notes, monkeypatch
):
    source, pdf, cache, extracted = cached_notes
    pdf.write_bytes(b"replaced context")
    replace = Path.replace

    def fail_raw(path, target):
        if target == cache / "raw" / pdf.name:
            raise OSError("raw publication refused")
        return replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_raw)
    with pytest.raises(OSError, match="raw publication refused"):
        notes.cache_notes(source, cache)
    assert (cache / "raw" / pdf.name).read_bytes() == b"original context"
    assert (cache / "text" / f"{pdf.stem}.txt").read_bytes() == b"replaced context"
    assert sorted(path.name for path in cache.iterdir()) == ["raw", "text"]

    monkeypatch.setattr(Path, "replace", replace)
    assert notes.cache_notes(source, cache).text_count == 1
    assert extracted == [b"original context", b"replaced context", b"replaced context"]
    assert (cache / "raw" / pdf.name).read_bytes() == b"replaced context"


def test_missing_extraction_output_does_not_publish_raw(cached_notes, monkeypatch):
    source, pdf, cache, _extracted = cached_notes
    pdf.write_bytes(b"replaced context")
    monkeypatch.setattr(notes, "_extract_text", lambda *_args: None)
    with pytest.raises(FileNotFoundError):
        notes.cache_notes(source, cache)
    assert (cache / "raw" / pdf.name).read_bytes() == b"original context"
    assert (cache / "text" / f"{pdf.stem}.txt").read_bytes() == b"original context"
    assert sorted(path.name for path in cache.iterdir()) == ["raw", "text"]


@pytest.mark.parametrize(
    "error",
    [OSError("missing extractor"), subprocess.CalledProcessError(1, "pdftotext")],
)
def test_existing_extractor_failure_semantics_remain_empty(
    tmp_path, monkeypatch, error
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "5.1.pdf").write_bytes(b"malformed PDF fixture")

    def fail(command, **_kwargs):
        Path(command[-1]).write_text("partial output", encoding="utf-8")
        raise error

    monkeypatch.setattr(notes.subprocess, "run", fail)
    cache = tmp_path / "cache"
    assert notes.cache_notes(source, cache).text_count == 0
    assert (cache / "text" / "5.1.txt").read_bytes() == b""
    assert notes.note_context_for_topic("4.5", "Number systems", cache) == ""


def test_existing_keyboard_interrupt_propagates_without_success_manifest(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "5.1.pdf").write_bytes(b"PDF fixture")

    def cancel(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(notes.subprocess, "run", cancel)
    with pytest.raises(KeyboardInterrupt):
        notes.cache_notes(source, tmp_path / "cache")


def test_real_extractor_interruption_preserves_exact_exception_and_old_pair(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    pdf = source / "5.1.pdf"
    pdf.write_bytes(b"replaced context")
    cache = tmp_path / "cache"
    raw = cache / "raw" / pdf.name
    text = cache / "text" / "5.1.txt"
    raw.parent.mkdir(parents=True)
    text.parent.mkdir()
    raw.write_bytes(b"original context")
    text.write_bytes(b"original context")
    interruption = InterruptedError("owned extraction cancelled")

    def cancel(command, **_kwargs):
        Path(command[-1]).write_bytes(b"partial extraction")
        raise interruption

    monkeypatch.setattr(notes.subprocess, "run", cancel)
    with pytest.raises(InterruptedError) as caught:
        notes.cache_notes(source, cache)
    assert caught.value is interruption
    assert raw.read_bytes() == b"original context"
    assert text.read_bytes() == b"original context"
    assert sorted(path.name for path in cache.iterdir()) == ["raw", "text"]
