from pathlib import Path

from pastpapergen.notes import note_context_for_topic, note_file_for_topic, note_points_for_topic


def test_notes_are_included_in_project_and_mapped_to_subtopics():
    assert Path("data/notes/text/3.4. Market Structures.txt").exists()

    assert note_file_for_topic("1.2.3").name.startswith("1.2.")


def test_note_context_and_points_are_relevant_to_topic():
    context = note_context_for_topic("3.4", title="Market structures", keywords=["perfect competition"])
    points = note_points_for_topic("3.4", title="Market structures", keywords=["efficiency"])

    assert "perfect competition" in context.lower()
    assert any("efficiency" in point.lower() for point in points)
