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


def test_section_b_sources_are_article_length_for_source_booklets():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    for seed in range(80):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]
        assert min(len(source) for source in section_b_sources) >= 360


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

    assert len(seen_stimuli) >= 28
    assert {
        "ped_data_table",
        "pes_data_table",
        "market_share_bar_chart",
        "business_objective_context",
        "xed_context",
        "imperfect_information_context",
        "minimum_wage_context",
        "payoff_matrix",
        "line_graph",
        "externality_diagram",
        "monopsony_diagram",
    } <= seen_stimuli


def test_section_a_calculation_questions_only_use_visible_numeric_stimuli():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    numeric_stimuli = {
        "ped_data_table",
        "pes_data_table",
        "market_share_bar_chart",
        "data_table",
        "elasticity_data_table",
        "concentration_ratio_table",
        "development_data_table",
        "balance_payments_table",
        "inflation_index_table",
        "labour_inactivity_context",
    }

    for paper_id in ("paper_1", "paper_2"):
        config = load_builtin_paper_config(paper_id)
        for seed in range(120):
            blueprint = build_paper_blueprint(config, syllabus, seed=seed)
            section_a = [question for question in blueprint.questions if question.section == "A"]
            for question in section_a:
                if any(part.command_word == "calculate" for part in question.parts):
                    assert question.stimulus_kind in numeric_stimuli


def test_section_a_calculation_prompts_are_specific_to_visible_data():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))

    for paper_id in ("paper_1", "paper_2"):
        config = load_builtin_paper_config(paper_id)
        for seed in range(180):
            blueprint = build_paper_blueprint(config, syllabus, seed=seed)
            for question in blueprint.questions:
                if question.section != "A":
                    continue
                for part in question.parts:
                    if part.command_word == "calculate":
                        lowered = part.prompt.lower()
                        assert "calculate" in lowered
                        assert "change shown in the data" not in lowered


def test_pes_calculation_prompt_names_the_market_used():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    for seed in range(1000):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for question in blueprint.questions:
            if question.stimulus_kind != "pes_data_table":
                continue
            for part in question.parts:
                if part.command_word == "calculate":
                    lowered = part.prompt.lower()
                    assert "rural" in lowered or "urban" in lowered
                    return
    raise AssertionError("No PES calculation question generated")


def test_paper_2_section_a_covers_reference_three_part_styles_and_macro_data():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")

    seen_stimuli = set()
    seen_shapes = set()
    for seed in range(160):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for question in blueprint.questions:
            if question.section == "A":
                seen_stimuli.add(question.stimulus_kind)
                seen_shapes.add(tuple((part.command_word, part.marks) for part in question.parts))

    assert {
        "household_savings_line_chart",
        "investment_line_chart",
        "financial_market_context",
        "development_data_table",
        "current_account_line_chart",
        "gdp_growth_bar_chart",
        "terms_of_trade_index_chart",
        "labour_inactivity_context",
        "multiplier_context",
        "tariff_context",
    } <= seen_stimuli
    assert (("mcq", 1), ("calculate", 2), ("explain", 2)) in seen_shapes
    assert (("explain", 2), ("mcq", 1), ("explain", 2)) in seen_shapes
    assert (("calculate", 2), ("explain", 2), ("mcq", 1)) in seen_shapes


def test_section_a_can_cover_all_allowed_paper_1_topics_across_random_seeds():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    expected_topic_ids = syllabus.topic_ids_for_themes(config.allowed_themes)

    seen_topic_ids = set()
    for seed in range(120):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        seen_topic_ids.update(question.topic_id for question in blueprint.questions if question.section == "A")

    assert seen_topic_ids == expected_topic_ids


def test_section_a_uses_note_context_for_generic_topics():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    section_a_text = " ".join(
        " ".join(question.source_text for question in build_paper_blueprint(config, syllabus, seed=seed).questions if question.section == "A")
        for seed in range(20)
    )

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

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "3.4")
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

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "3.3")
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

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "2.1")
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]
    section_b_text = " ".join(section_b_sources)

    assert "A UK case study on" not in section_b_text
    assert any(name in section_b_text for name in ["ONS", "Bank of England", "World Bank", "IMF", "UK trade"])
    assert max(len(source) for source in section_b_sources) - min(len(source) for source in section_b_sources) > 80
    assert sum(any(token in source for token in ["£", "%", "$", "2023", "2024"]) for source in section_b_sources) >= 3


def test_section_c_extracts_are_short_realistic_and_not_formulaic():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    section_c_sources = [
        question.source_text
        for seed in range(20)
        for blueprint in [build_paper_blueprint(config, syllabus, seed=seed)]
        for question in blueprint.questions
        if question.section == "C"
    ]

    assert all(80 <= len(source) <= 360 for source in section_c_sources)
    assert all("In 2025, a UK report highlighted an issue" not in source for source in section_c_sources)
    assert any(name in " ".join(section_c_sources) for name in ["HS2", "TikTok", "Ofgem", "Low Pay Commission", "CMA", "ULEZ", "John Lewis"])


def test_low_level_section_b_supply_sources_are_long_enough_for_extract_pages():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "1.2.3")
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]

    assert min(len(source) for source in section_b_sources[:4]) >= 300
    assert any(name in " ".join(section_b_sources) for name in ["semiconductor", "SMMT", "housebuilding", "National Grid"])


def test_low_level_section_b_supply_questions_are_not_bare_topic_prompts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "1.2.3")
    section_b_prompts = [question.prompt for question in blueprint.questions if question.section == "B"]
    prompt_text = " ".join(section_b_prompts).lower()

    assert "effect of supply" not in prompt_text
    assert "likely effects of supply" not in prompt_text
    assert "affecting supply" not in prompt_text
    assert "semiconductors" in prompt_text
    assert "price elasticity of supply" in prompt_text
    assert "production costs" in prompt_text


def test_section_a_prompts_and_mcqs_use_topic_specific_language():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    text = " ".join(
        item
        for seed in range(40)
        for blueprint in [build_paper_blueprint(config, syllabus, seed=seed)]
        for item in (
            [question.prompt for question in blueprint.questions if question.section == "A"]
            + [part.prompt for question in blueprint.questions if question.section == "A" for part in question.parts]
            + [option.text for question in blueprint.questions if question.section == "A" for part in question.parts for option in part.options]
        )
    ).lower()

    assert "market affected by rational decision making" not in text
    assert "correct about rational decision making" not in text
    assert "production costs" in text or "marginal benefit" in text or "utility" in text
    assert "subsidy" in text or "external costs" in text
    assert "opportunity cost no longer exists" not in text
    assert "price elasticity of supply" in text
    assert "vacancies" in text or "barriers to entry" in text


def test_section_a_stimuli_keep_topic_specific_exam_language():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    for seed in range(120):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for question in blueprint.questions:
            if question.section != "A":
                continue
            combined = " ".join([question.prompt, *(part.prompt for part in question.parts)]).lower()
            assert "market structure or labour market" not in combined
            assert "changes in fixed costs, variable costs and profit" not in combined
            if question.stimulus_kind == "concentration_ratio_table":
                assert question.topic_id == "3.4"
            if question.stimulus_kind == "elasticity_data_table":
                assert question.topic_id == "1.2.2"


def test_section_a_draw_questions_use_diagram_suitable_topics():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    unsuitable = {"1.1", "1.2.1"}

    for seed in range(80):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        draw_questions = [
            question
            for question in blueprint.questions
            if question.section == "A" and question.parts and question.parts[0].command_word == "draw"
        ]

        assert all(question.topic_id not in unsuitable for question in draw_questions)


def test_ollama_accepts_new_extract_d_section_b_15_marker_style():
    from pastpapergen.ollama_client import _matches_expected_question_style

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=7)
    question = [question for question in blueprint.questions if question.section == "B"][-1]

    assert _matches_expected_question_style(question, question.prompt)


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


def _blueprint_with_section_b_topic(config, syllabus, topic_id: str):
    for seed in range(500):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        if any(question.section == "B" and question.topic_id == topic_id for question in blueprint.questions):
            return blueprint
    raise AssertionError(f"No Section B blueprint found for topic {topic_id}")
