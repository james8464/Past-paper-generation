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


def test_note_points_are_complete_clean_bullets():
    points = note_points_for_topic("1.4", title="government intervention", keywords=["regulation", "taxation"], limit=6)

    assert points
    assert all(not point.startswith(("●", "•", "-", "o ")) for point in points)
    assert all(point[-1] in ".;)" for point in points)
    assert all(len(point.split()) >= 8 for point in points)
