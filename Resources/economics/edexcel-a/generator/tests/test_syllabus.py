from pathlib import Path

from pastpapergen.syllabus import load_syllabus


def test_load_seed_syllabus_has_theme_topics():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))

    assert syllabus.topic_count >= 20
    assert syllabus.topic_ids_for_themes({1})
    assert syllabus.topic_ids_for_themes({2})
    assert syllabus.topic_ids_for_themes({3})
    assert syllabus.topic_ids_for_themes({4})


def test_topic_filter_only_returns_allowed_themes():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))

    topics = syllabus.topics_for_themes({1, 3})

    assert topics
    assert {topic.theme for topic in topics} <= {1, 3}
