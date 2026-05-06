from pathlib import Path

import pytest

from cspapergen.notes import cache_notes, discover_note_pdfs


LOCAL_NOTES = Path("/Users/james/Downloads/CS Notes")


def test_discovers_local_cs_notes_folder():
    if not LOCAL_NOTES.exists():
        pytest.skip("local CS notes folder not available")

    notes = discover_note_pdfs(LOCAL_NOTES)

    assert len(notes) >= 20
    assert any("5.1. Number Systems" in path.name for path in notes)
    assert any("12.2. Writing Functional Programs" in path.name for path in notes)


def test_cache_notes_extracts_text_into_project_cache(tmp_path):
    if not LOCAL_NOTES.exists():
        pytest.skip("local CS notes folder not available")

    manifest = cache_notes(LOCAL_NOTES, tmp_path)

    assert manifest.pdf_count >= 20
    assert manifest.text_count >= 20
    assert (tmp_path / "raw").exists()
    assert (tmp_path / "text").exists()
