from pathlib import Path

import pytest

from cspapergen.notes import cache_notes, discover_note_pdfs


LOCAL_NOTES = Path(__file__).resolve().parents[2] / "notes"


def test_discovers_local_cs_notes_folder():
    notes = discover_note_pdfs(LOCAL_NOTES)
    if not notes:
        pytest.skip("local CS notes folder has not been populated")

    assert len(notes) >= 20
    assert any("5.1. Number Systems" in path.name for path in notes)
    assert any("12.2. Writing Functional Programs" in path.name for path in notes)


def test_cache_notes_extracts_text_into_project_cache(tmp_path):
    manifest = cache_notes(LOCAL_NOTES, tmp_path)
    if manifest.pdf_count == 0:
        pytest.skip("local CS notes folder has not been populated")

    assert manifest.pdf_count >= 20
    assert manifest.text_count >= 20
    assert (tmp_path / "raw").exists()
    assert (tmp_path / "text").exists()
