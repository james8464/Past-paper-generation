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
    assert sorted([[part.marks for part in question.parts] for question in section_a]) == sorted([
        [4, 1],
        [4, 1],
        [1, 4],
        [4, 1],
        [4, 1],
    ])
    one_mark_parts = [part for question in section_a for part in question.parts if part.marks == 1]
    assert one_mark_parts
    assert all(part.command_word == "mcq" for part in one_mark_parts)
    assert all("Which one of the following" in part.prompt for part in one_mark_parts)
    assert len({question.stimulus_kind for question in section_a}) == 5
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


def test_paper_1_presented_marks_are_balanced_between_themes():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    for seed in range(30):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        presented = {1: 0, 3: 0}
        for question in blueprint.questions:
            theme = syllabus.get_topic(question.topic_id).theme
            presented[theme] += question.marks

        assert abs(presented[1] - presented[3]) <= 5


def test_paper_1_section_b_and_section_c_use_opposite_themes_with_extracts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=7)
    section_b_themes = {syllabus.get_topic(question.topic_id).theme for question in blueprint.questions if question.section == "B"}
    section_c = [question for question in blueprint.questions if question.section == "C"]
    section_c_themes = {syllabus.get_topic(question.topic_id).theme for question in section_c}

    assert len(section_b_themes) == 1
    assert len(section_c_themes) == 1
    assert section_b_themes != section_c_themes
    assert all(len(question.source_text) > 90 for question in section_c)


def test_section_a_templates_are_not_fixed_to_question_positions():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    first_stimuli = {
        build_paper_blueprint(config, syllabus, seed=seed).questions[0].stimulus_kind
        for seed in range(20)
    }
    q5_part_orders = {
        tuple(part.command_word for part in build_paper_blueprint(config, syllabus, seed=seed).questions[4].parts)
        for seed in range(20)
    }

    assert len(first_stimuli) > 1
    assert len(q5_part_orders) > 1


def test_section_a_stimulus_pool_is_wide_and_random():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    seen_stimuli = set()
    for seed in range(100):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        seen_stimuli.update(question.stimulus_kind for question in blueprint.questions if question.section == "A")

    assert len(seen_stimuli) >= 18
    assert {"payoff_matrix", "line_graph", "externality_diagram", "monopsony_diagram"} <= seen_stimuli


def test_section_a_can_cover_all_allowed_paper_1_topics_across_random_seeds():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    expected_topic_ids = syllabus.topic_ids_for_themes(config.allowed_themes)

    seen_topic_ids = set()
    for seed in range(50):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        seen_topic_ids.update(question.topic_id for question in blueprint.questions if question.section == "A")

    assert seen_topic_ids == expected_topic_ids


def test_section_a_uses_note_context_for_generic_topics():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8)
    section_a_text = " ".join(question.source_text for question in blueprint.questions if question.section == "A")

    assert "The evidence highlights changes in" not in section_a_text
    assert "ceteris paribus" in section_a_text.lower() or "price elasticity" in section_a_text.lower()


def test_section_a_note_contexts_are_rewritten_as_exam_evidence():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    section_a_text = " ".join(question.source_text for question in blueprint.questions if question.section == "A")

    assert "unable to gain through organic growth" not in section_a_text
    assert "A market report on" in section_a_text


def test_deterministic_questions_use_exam_like_contexts_not_generic_placeholders():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=8464)
    text = " ".join(
        [question.prompt for question in blueprint.questions]
        + [part.prompt for question in blueprint.questions for part in question.parts]
        + [option.text for question in blueprint.questions for part in question.parts for option in part.options]
        + [question.source_text for question in blueprint.questions]
    )

    assert "The following data relates to" not in text
    assert "A key concept in" not in text
    assert "removes the need for opportunity cost" not in text
    assert "constructed data" not in text
    assert "A UK market linked to" not in text
    assert "market affected by labour market" not in text
    assert "linked to labour market" not in text
    assert "effect of labour market" not in text
    assert "with reference to Extract A" in text or "With reference to Extract A" in text


def test_paper_1_section_b_uses_coherent_source_case_and_references():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=8464)
    section_b = [question for question in blueprint.questions if question.section == "B"]

    assert len({question.topic_id for question in section_b}) == 1
    assert [question.source_reference for question in section_b] == [
        "Extract A",
        "",
        "",
        "Extract C",
        "Extract D",
    ]
    assert len({question.source_text for question in section_b}) >= 4


def test_section_b_15_marker_references_extract_d_like_reference_papers():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=7)
    section_b = [question for question in blueprint.questions if question.section == "B"]

    assert section_b[-1].prompt.startswith("With reference to Extract D, discuss ")


def test_market_structure_sources_are_specific_not_template_like():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=7)
    section_b_text = " ".join(question.source_text for question in blueprint.questions if question.section == "B")

    assert "video games" in section_b_text or "digital" in section_b_text
    assert "A UK market linked to market structures" not in section_b_text
    assert "average prices changed" not in section_b_text


def test_paper_1_labour_market_sources_are_exam_like_not_generic():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=24)
    section_b_text = " ".join(question.source_text for question in blueprint.questions if question.section == "B")

    assert "vacancies" in section_b_text
    assert "hourly pay" in section_b_text
    assert "monopsony" in section_b_text
    assert "average prices changed" not in section_b_text


def test_section_b_sources_use_realistic_named_cases_not_generic_templates():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=5)
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]
    section_b_text = " ".join(section_b_sources)

    assert "A UK case study on" not in section_b_text
    assert "changed their behaviour over three years" not in section_b_text
    assert any(name in section_b_text for name in ["Ryanair", "Tesco", "CMA", "Ofgem", "Bank of England"])
    assert max(len(source) for source in section_b_sources) - min(len(source) for source in section_b_sources) > 80
    assert sum(any(token in source for token in ["£", "%", "2023", "2024"]) for source in section_b_sources) >= 3


def test_paper_2_sources_use_real_world_macro_data_and_varied_lengths():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")

    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]
    section_b_text = " ".join(section_b_sources)

    assert "A UK case study on" not in section_b_text
    assert any(name in section_b_text for name in ["ONS", "Bank of England", "World Bank", "IMF", "UK trade"])
    assert max(len(source) for source in section_b_sources) - min(len(source) for source in section_b_sources) > 80
    assert sum(any(token in source for token in ["£", "%", "$", "2023", "2024"]) for source in section_b_sources) >= 3


def test_section_c_extracts_are_short_realistic_and_not_formulaic():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    section_c_sources = [question.source_text for question in blueprint.questions if question.section == "C"]

    assert all(80 <= len(source) <= 360 for source in section_c_sources)
    assert all("In 2025, a UK report highlighted an issue" not in source for source in section_c_sources)
    assert any(name in " ".join(section_c_sources) for name in ["HS2", "TikTok", "Ofgem", "Low Pay Commission", "CMA"])


def test_low_level_section_b_supply_sources_are_long_enough_for_extract_pages():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]

    assert min(len(source) for source in section_b_sources[:4]) >= 300
    assert any(name in " ".join(section_b_sources) for name in ["semiconductor", "SMMT", "housebuilding", "National Grid"])


def test_essay_questions_do_not_use_shallow_nature_of_economics_topic():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    for seed in range(200):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        essay_topic_ids = [question.topic_id for question in blueprint.questions if question.marks >= 15]

        assert "1.1" not in essay_topic_ids


def test_essay_question_prompts_are_broad_enough_for_extended_answers():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=13)
    essays = [question for question in blueprint.questions if question.marks >= 15]
    essay_text = " ".join(question.prompt for question in essays)

    assert "positive and normative" not in essay_text.lower()
    assert "likely effects" in essay_text or "benefits and drawbacks" in essay_text or "contestability" in essay_text


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
