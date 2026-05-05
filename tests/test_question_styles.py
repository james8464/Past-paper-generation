from pathlib import Path

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus


def test_paper_1_uses_edexcel_command_word_pattern():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=10)
    section_b = [question for question in blueprint.questions if question.section == "B"]
    section_c = [question for question in blueprint.questions if question.section == "C"]

    section_a = [question for question in blueprint.questions if question.section == "A"]
    assert [question.number for question in section_a] == ["1", "2", "3", "4", "5"]
    assert [[part.marks for part in question.parts] for question in section_a] == [
        [4, 1],
        [4, 1],
        [1, 4],
        [4, 1],
        [4, 1],
    ]
    one_mark_parts = [part for question in section_a for part in question.parts if part.marks == 1]
    assert one_mark_parts
    assert all(part.command_word == "mcq" for part in one_mark_parts)
    assert all("Which one of the following" in part.prompt for part in one_mark_parts)
    assert [question.stimulus_kind for question in section_a] == [
        "cost_revenue_graph",
        "data_table",
        "market_diagram",
        "context_extract",
        "bar_chart",
    ]
    assert [question.number for question in section_b] == ["6(a)", "6(b)", "6(c)", "6(d)", "6(e)"]
    assert [question.number for question in section_c] == ["7", "8"]
    assert [(q.marks, q.command_word) for q in section_b] == [
        (5, "explain"),
        (8, "examine"),
        (12, "discuss"),
        (10, "assess"),
        (15, "discuss"),
    ]
    assert [(q.marks, q.command_word) for q in section_c] == [
        (25, "evaluate"),
        (25, "evaluate"),
    ]
    assert section_c[0].choice_group == section_c[1].choice_group
    assert section_c[0].topic_id != section_c[1].topic_id


def test_paper_3_has_choice_25_marker_per_section():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_3")

    blueprint = build_paper_blueprint(config, syllabus, seed=10)

    for section in ["A", "B"]:
        questions = [question for question in blueprint.questions if question.section == section]
        assert [question.number for question in questions] == (
            ["1(a)", "1(b)", "1(c)", "1(d)", "1(e)"]
            if section == "A"
            else ["2(a)", "2(b)", "2(c)", "2(d)", "2(e)"]
        )
        assert [(q.marks, q.command_word) for q in questions] == [
            (5, "explain"),
            (8, "examine"),
            (12, "discuss"),
            (25, "evaluate"),
            (25, "evaluate"),
        ]
        assert questions[3].choice_group == questions[4].choice_group
        assert questions[3].topic_id != questions[4].topic_id


def test_choice_pairs_do_not_repeat_topic_for_seed_that_would_duplicate():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_3")

    blueprint = build_paper_blueprint(config, syllabus, seed=123)
    section_b = [question for question in blueprint.questions if question.section == "B"]

    assert section_b[3].choice_group == section_b[4].choice_group
    assert section_b[3].topic_id != section_b[4].topic_id
