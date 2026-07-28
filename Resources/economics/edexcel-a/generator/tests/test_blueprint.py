from pathlib import Path

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus


def test_blueprint_is_deterministic_for_seed():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    first = build_paper_blueprint(config, syllabus, seed=123)
    second = build_paper_blueprint(config, syllabus, seed=123)

    assert first.model_dump() == second.model_dump()


def test_blueprint_uses_only_allowed_theme_topics():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")

    blueprint = build_paper_blueprint(config, syllabus, seed=7)

    assert blueprint.total_marks == 100
    for question in blueprint.questions:
        topic = syllabus.get_topic(question.topic_id)
        assert topic.theme in config.allowed_themes


def test_blueprint_varies_topics_within_section_when_enough_topics_exist():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    section_a_topic_ids = [question.topic_id for question in blueprint.questions if question.section == "A"]

    assert len(section_a_topic_ids) == len(set(section_a_topic_ids))


def test_blueprint_contains_structured_mcq_and_mark_scheme_content():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    first = blueprint.questions[0]
    mcq_part = next(part for part in first.parts if part.marks == 1)

    assert first.source_reference == "Figure 1"
    assert first.mark_breakdown == "Knowledge 2, Application 2"
    assert len(mcq_part.options) == 4
    assert mcq_part.correct_option == "A"
    assert "removes the need" not in mcq_part.options[0].text
    assert mcq_part.mark_scheme
    assert "(4 marks)" not in first.prompt


def test_paper_3_uses_coherent_synoptic_case_studies():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_3")

    for seed in range(20):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for section in ("A", "B"):
            questions = [question for question in blueprint.questions if question.section == section]
            themes = {syllabus.get_topic(question.topic_id).theme for question in questions}

            assert len({question.source_title for question in questions}) == 1
            assert len(themes) == 4
            assert min(len(question.source_text) for question in questions) >= 360
            assert all(
                "microeconomic and macroeconomic" in question.prompt.lower()
                for question in questions
                if question.marks == 25
            )
