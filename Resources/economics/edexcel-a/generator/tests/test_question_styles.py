import random
from pathlib import Path

from pastpapergen.generator import _build_part, build_paper_blueprint
from pastpapergen.models import SyllabusTopic
from pastpapergen.ollama_client import _merge_question_text
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.stimulus_data import line_chart_data, review_table_rows
from pastpapergen.syllabus import load_syllabus


def test_paper_1_uses_edexcel_command_word_pattern():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = build_paper_blueprint(config, syllabus, seed=10)
    section_b = [question for question in blueprint.questions if question.section == "B"]
    section_c = [question for question in blueprint.questions if question.section == "C"]

    section_a = [question for question in blueprint.questions if question.section == "A"]
    assert [question.number for question in section_a] == ["1", "2", "3", "4", "5"]
    assert [[part.marks for part in question.parts] for question in section_a] == [[4, 1]] * 5
    assert [[part.command_word for part in question.parts] for question in section_a] == [
        ["explain", "mcq"],
        ["explain", "mcq"],
        ["draw", "mcq"],
        ["explain", "mcq"],
        ["explain", "mcq"],
    ]
    one_mark_parts = [part for question in section_a for part in question.parts if part.marks == 1]
    assert one_mark_parts
    assert all(part.command_word == "mcq" for part in one_mark_parts)
    assert all("which one of the following" in part.prompt.casefold() for part in one_mark_parts)
    assert len({question.stimulus_kind for question in section_a}) == 5
    assert [question.number for question in section_b] == ["6(a)", "6(b)", "6(c)", "6(d)", "6(e)"]
    assert [question.number for question in section_c] == ["7", "8"]
    assert [(q.marks, q.command_word) for q in section_b] == [
        (5, "explain"),
        (8, "examine"),
        (10, "assess"),
        (12, "discuss"),
        (15, "discuss"),
    ]
    assert [(q.marks, q.command_word) for q in section_c] == [
        (25, "evaluate"),
        (25, "evaluate"),
    ]
    assert section_c[0].choice_group == section_c[1].choice_group
    assert section_c[0].topic_id != section_c[1].topic_id


def test_paper_one_business_objectives_guidance_is_bound_to_extract_a() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[5]
    guidance = " ".join(question.mark_scheme).casefold()

    assert question.number == "6(a)" and question.topic_id == "3.2"
    assert question.source_reference == "Extract A"
    assert "john lewis" in question.source_text.casefold()
    assert len(question.mark_scheme) == 5
    assert "employee-owned" in guidance
    assert "service quality" in guidance
    assert "satisfactory level of profit" in guidance
    assert "amazon" not in guidance and "netflix" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_one_business_objectives_examination_has_two_developed_conflicts() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[6]
    guidance = " ".join(question.indicative_content).casefold()

    assert question.number == "6(b)" and question.marks == 8
    assert question.prompt.startswith("With reference to the evidence")
    assert question.assessment_contract["scheme_mode"] == "points"
    assert guidance.count("ao1 (1 mark)") == 2
    assert guidance.count("ao3 (1 mark)") == 2
    assert "two distinct relevant qualifications" in guidance
    assert "amazon" in guidance and "logistics" in guidance
    assert "pressure on workers" in guidance
    assert "economies of scale" in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_one_regulation_assessment_is_water_case_specific() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[7]
    guidance = " ".join(question.indicative_content).casefold()

    assert question.number == "6(c)" and question.marks == 10
    assert question.assessment_contract["kaa_marks"] == 6 and question.assessment_contract["evaluation_marks"] == 4
    assert "water companies" in guidance
    assert "pollution standards" in guidance
    assert "infrastructure" in guidance
    assert "monitoring is poor" in guidance
    assert "supported judgement" in guidance
    assert "amazon" not in guidance and "netflix" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_one_long_discussions_are_calibrated_and_source_bound() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    water, objectives = blueprint.questions[8:10]
    water_guidance = " ".join(water.mark_scheme).casefold()
    objective_guidance = " ".join(objectives.mark_scheme).casefold()

    assert len(water.mark_scheme) >= 12
    assert "regulated water companies" in water.prompt
    assert "dividends" in water_guidance and "third-party costs" in water_guidance
    assert "supported judgement" in water_guidance
    assert len(objectives.mark_scheme) >= 15
    assert "satisficing" in objective_guidance
    assert "separation of ownership and control" in objective_guidance
    assert "consumers, workers, owners and rival firms" in objective_guidance
    assert water.mark_scheme == water.indicative_content
    assert objectives.mark_scheme == objectives.indicative_content


def test_paper_one_section_c_essays_compare_policies_and_stakeholders() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    tax, price = blueprint.questions[10:12]
    tax_guidance = " ".join(tax.mark_scheme).casefold()
    price_guidance = " ".join(price.mark_scheme).casefold()

    assert len(tax.mark_scheme) >= 25
    assert "£0.12" in tax.source_text and "ped was −0.6" in tax.source_text.casefold()
    assert "reusable standard" in tax_guidance
    assert "compares effectiveness against regulation" in tax_guidance
    assert "most effective" in tax_guidance
    assert len(price.mark_scheme) >= 24
    assert "consumer and producer surplus" in price.prompt
    assert "reduced domestic tomato supply by 12%" in price.source_text
    assert "£2.40 to £3.00" in price.source_text
    assert "consumer surplus" in price_guidance and "producer surplus" in price_guidance
    assert "examples, not a checklist" in price_guidance
    assert tax.mark_scheme == tax.indicative_content
    assert price.mark_scheme == price.indicative_content


def test_current_account_chart_has_exact_options_and_marking() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")
    question = next(
        question
        for seed in range(1000)
        for question in build_paper_blueprint(config, syllabus, seed=seed).questions
        if question.section == "A"
        and question.stimulus_kind == "current_account_line_chart"
        and [part.marks for part in question.parts] == [1, 2, 2]
    )
    mcq, calculation, explanation = question.parts

    assert _merge_question_text(question, question.source_text) == question.prompt
    keyed = next(option.text for option in mcq.options if option.label == mcq.correct_option)
    assert keyed == "The current account was in deficit in every year shown"
    assert question.mark_breakdown == ""
    assert "Do not award a mark for any other option." in mcq.mark_scheme
    assert "size of the current-account deficit" in calculation.prompt
    assert any("1 AO2 mark" in point for point in calculation.mark_scheme)
    assert "deficit was wider in Year 10" in explanation.prompt
    assert any("AO3 (1 mark)" in point for point in explanation.mark_scheme)
    assert any("net exports" in point for point in explanation.mark_scheme)
    assert explanation.assessment_objectives == {"AO1": 1, "AO3": 1}
    assert question.mark_scheme == []
    assert all(part.assessment_contract["published_scheme"] == part.mark_scheme for part in question.parts)
    _, x_label, values = line_chart_data("current_account_line_chart")
    assert x_label == "Year"
    assert len(values) == 10
    assert values[0] == -3.8 and values[-1] == -4.3


def test_inequality_chart_has_visible_data_and_source_bound_marking() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    question = blueprint.questions[1]
    mcq, explanation = question.parts
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert question.topic_id == "4.2"
    assert question.stimulus_kind == "inequality_line_chart"
    assert question.source_reference == "Figure 1"
    assert question.mark_breakdown == ""
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert "fall in the Gini coefficient from 0.42 to 0.33" in explanation.prompt
    assert "targeted transfers" in question.source_text
    assert "a decrease of 0.09" in guidance
    assert "material living standards" in guidance
    assert "do not award" not in guidance
    keyed = next(option.text for option in mcq.options if option.label == mcq.correct_option)
    assert keyed == "The Gini coefficient fell by 0.09 over the period shown"
    y_label, x_label, values = line_chart_data(question.stimulus_kind)
    assert (y_label, x_label) == ("Gini coefficient", "Year")
    assert values == [0.42, 0.40, 0.38, 0.35, 0.33]


def test_state_policy_context_replaces_unrelated_consumer_choice_case() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    question = blueprint.questions[2]
    explanation, mcq = question.parts
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert question.topic_id == "4.5"
    assert question.stimulus_kind == "state_policy_context"
    assert "preventive healthcare" in question.prompt
    assert "£12 billion" in question.source_text
    assert "working days lost" in question.source_text
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert "productive capacity" in explanation.prompt
    assert "long-run aggregate supply" in guidance
    keyed = next(option.text for option in mcq.options if option.label == mcq.correct_option)
    assert keyed == "The next-best public programme that cannot now be funded"
    assert "first event ticket" not in question.source_text.casefold()


def test_trade_cycle_item_has_specific_recovery_analysis() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    question = blueprint.questions[3]
    mcq, explanation = question.parts
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert question.topic_id == "2.1" and question.stimulus_kind == "trade_cycle"
    assert "recession, trough, recovery and boom" in question.prompt
    assert question.mark_breakdown == ""
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert "cyclical unemployment" in explanation.prompt
    assert "derived demand for labour" in guidance
    assert "structural unemployment may remain" in guidance
    keyed = next(option.text for option in mcq.options if option.label == mcq.correct_option)
    assert keyed == "Real GDP rises and cyclical unemployment is likely to fall"


def test_paper_two_policy_case_has_calibrated_questions_and_schemes() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    questions = blueprint.questions[5:10]

    assert len(questions[0].mark_scheme) == 5
    assert questions[1].assessment_contract["scheme_mode"] == "points"
    assert all(
        len(question.mark_scheme) >= question.marks
        for question in questions[2:]
    )
    assert "higher Bank Rate on inflation" in questions[0].prompt
    assert "one likely effect" in questions[0].prompt
    assert "reduces demand-pull inflation" in " ".join(questions[0].mark_scheme)
    assert "5.25%" in " ".join(questions[0].mark_scheme)
    assert "expansionary fiscal policy" in questions[1].prompt
    assert "current-account deficit" in " ".join(questions[1].mark_scheme)
    assert "supply-side policies" in questions[2].prompt
    assert "childcare" in " ".join(questions[2].mark_scheme).casefold()
    assert "training, childcare and infrastructure" in questions[3].prompt
    assert "supported judgement" in " ".join(questions[3].mark_scheme).casefold()
    assert "tighter anti-inflation policy" in questions[4].prompt
    assert "firms and consumers" in " ".join(questions[4].mark_scheme)
    assert all(question.mark_scheme == question.indicative_content for question in questions)


def test_custom_extended_schemes_include_standardisation_guidance() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))

    paper_one = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    ten_marker = next(
        question
        for question in paper_one.questions
        if question.number == "6(c)"
    )
    paper_three = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    welfare_marker = paper_three.questions[2]

    for question in (ten_marker, welfare_marker):
        guidance = " ".join(question.mark_scheme).casefold()
        assert question.assessment_contract["kaa_bands"][0] == [1, 2]
        assert len(question.assessment_contract["evaluation_descriptors"]) >= 2
        assert "accept an equivalent valid" in guidance
        assert "do not award" in guidance


def test_every_extended_response_has_complete_standardisation_guidance() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    extended_commands = {
        "analyse",
        "analyze",
        "assess",
        "advise",
        "discuss",
        "evaluate",
        "justify",
    }

    for paper_id, seed in (
        ("paper_1", 26080122),
        ("paper_2", 26080123),
        ("paper_3", 26080124),
    ):
        blueprint = build_paper_blueprint(
            load_builtin_paper_config(paper_id), syllabus, seed=seed
        )
        for question in blueprint.questions:
            if (
                question.parts
                or question.marks < 8
                or question.command_word.casefold() not in extended_commands
            ):
                continue
            guidance = " ".join(question.mark_scheme).casefold()
            assert question.assessment_contract["scheme_mode"] == "levels", question.number
            assert "accept an equivalent valid" in guidance, question.number
            assert "do not award" in guidance, question.number


def test_tariff_item_uses_price_output_chain_and_matching_mcq() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    question = blueprint.questions[4]
    explanation, mcq = question.parts
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert question.stimulus_kind == "tariff_context"
    assert "£100" in question.source_text and "£20 tariff" in question.source_text
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert "imported solar panels" in explanation.prompt
    assert "40,000 panels" in guidance
    assert "elasticities" in guidance
    keyed = next(option.text for option in mcq.options if option.label == mcq.correct_option)
    assert keyed == "UK panel prices rise and imports are likely to fall"
    assert question.mark_scheme == []
    assert all(part.assessment_contract["published_scheme"] == part.mark_scheme for part in question.parts)


def test_paper_two_section_c_has_evidenced_comparative_evaluation() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    trade, inequality = blueprint.questions[10:12]
    trade_guidance = " ".join(trade.mark_scheme).casefold()
    inequality_guidance = " ".join(inequality.mark_scheme).casefold()

    assert "£900" in trade.source_text and "20% tariff" in trade.source_text
    assert "retaliation" in trade_guidance and "comparative advantage" in trade_guidance
    assert trade.assessment_contract["evaluation_marks"] == 9
    assert "gini coefficient is 0.39" in inequality.source_text.casefold()
    assert "childcare" in inequality_guidance and "wealth taxation" in inequality_guidance
    assert inequality.assessment_contract["evaluation_marks"] == 9
    assert trade.mark_scheme == trade.indicative_content
    assert inequality.mark_scheme == inequality.indicative_content


def test_pes_table_guidance_is_bound_to_elasticity_and_source_constraints() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    question = next(
        question
        for seed in range(1000)
        for question in build_paper_blueprint(config, syllabus, seed=seed).questions
        if question.section == "A"
        and question.stimulus_kind == "pes_data_table"
    )
    explanation = next(
        part for part in question.parts if part.command_word == "explain"
    )
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert len(explanation.mark_scheme) == 4
    assert "price elasticity of supply" in guidance
    assert "spare capacity" in guidance
    assert "lower pes" in guidance


def test_ped_table_guidance_is_bound_to_age_group_data() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    question = next(
        question
        for seed in range(1000)
        for question in build_paper_blueprint(config, syllabus, seed=seed).questions
        if question.section == "A" and question.stimulus_kind == "ped_data_table"
    )
    explanation = next(
        part for part in question.parts if part.command_word == "explain"
    )
    guidance = " ".join(explanation.mark_scheme).casefold()

    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert len(explanation.mark_scheme) == 4
    assert "-0.7" in guidance and "-0.4" in guidance
    assert "larger proportional response" in guidance
    assert "exact phrase 'proportional response' is not required" in guidance
    assert "premium coffee" in question.source_text
    multiple_choice = next(part for part in question.parts if part.options)
    assert "statements is correct" in multiple_choice.prompt
    assert multiple_choice.correct_option in {
        option.label for option in multiple_choice.options
    }
    keyed_text = next(
        option.text
        for option in multiple_choice.options
        if option.label == multiple_choice.correct_option
    )
    assert keyed_text == "The 16–18 group has more price elastic demand because |−0.7| > |−0.4|"
    assert not any(
        "change in income" in option.text.casefold()
        for option in multiple_choice.options
    )


def test_cost_revenue_draw_has_exact_objective_marking_and_context() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[2]
    drawing, multiple_choice = question.parts
    guidance = " ".join(drawing.mark_scheme)

    assert question.stimulus_kind == "cost_revenue_graph"
    assert drawing.mark_breakdown == "AO1 2, AO2 2"
    assert len(drawing.mark_scheme) == 4
    assert "AR curve" in guidance and "MR curve" in guidance
    assert "MC = MR" in guidance and "MR = 0" in guidance
    assert "Qp" in guidance and "Qr" in guidance
    assert "imperfectly competitive firm" in question.prompt
    assert "imperfectly competitive firm" in drawing.prompt
    assert "fictional imperfectly competitive firm" in question.source_text
    assert "AR and MR curves downwards" in question.source_text
    assert "imperfectly competitive firm in the previous diagram" in multiple_choice.prompt
    keyed = next(
        option.text
        for option in multiple_choice.options
        if option.label == multiple_choice.correct_option
    )
    assert keyed == "The AR and MR curves both shift downwards"
    assert "Netflix" not in guidance and "Spotify" not in guidance


def test_rational_choice_item_has_source_bound_marginal_reasoning() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[3]
    explanation, multiple_choice = question.parts
    guidance = " ".join(explanation.mark_scheme)

    assert question.topic_id == "1.2.1"
    assert question.source_reference == ""
    assert "first event ticket costs £18" in question.source_text
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert len(explanation.mark_scheme) == 4
    assert "marginal net benefit of £6" in guidance
    assert "second ticket" in guidance and "below its £18 marginal cost" in guidance
    assert not any("perfect information" in option.text for option in multiple_choice.options)
    assert question.mark_scheme == []
    assert all(part.assessment_contract["published_scheme"] == part.mark_scheme for part in question.parts)


def test_costs_item_uses_exact_short_run_shutdown_data() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[4]
    explanation, multiple_choice = question.parts
    guidance = " ".join(explanation.mark_scheme)

    assert question.topic_id == "3.3"
    assert question.stimulus_kind == "shutdown_cost_table"
    assert question.source_reference == "Table 1"
    assert explanation.mark_breakdown == "AO1 2, AO2 1, AO3 1"
    assert len(explanation.mark_scheme) == 4
    assert "price £18 exceeds AVC £14 but is below AC £22" in guidance
    assert "£2,000 operating loss" in guidance
    assert "£4,000 fixed-cost loss" in guidance
    keyed = next(
        option.text
        for option in multiple_choice.options
        if option.label == multiple_choice.correct_option
    )
    assert keyed == "The firm covers its variable costs but makes a loss overall"


def test_supply_data_uses_the_matching_pes_stimulus_and_source() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[0]

    assert question.topic_id == "1.2.3"
    assert question.stimulus_kind == "pes_data_table"
    assert "producers" in question.source_text
    assert "price" in question.source_text
    assert "limited spare capacity" in question.source_text
    assert review_table_rows(question.stimulus_kind) == [
        ["Region", "PES coefficient"],
        ["Urban", "0.5"],
        ["Rural", "1.8"],
    ]
    mcq = next(part for part in question.parts if part.command_word == "mcq")
    assert "quantity supplied rises by 3.6%" in mcq.prompt


def test_mcq_shuffle_preserves_the_economically_correct_option() -> None:
    topic = SyllabusTopic(
        id="1.2.3",
        theme=1,
        title="Supply",
        points=["supply curves", "price elasticity of supply", "production costs"],
    )
    part = _build_part("b", 1, "mcq", topic, "", 1, random.Random(26080122))
    selected = next(
        option.text for option in part.options if option.label == part.correct_option
    )

    assert selected == "Higher production costs may shift the supply curve to the left"


def test_paper_three_supply_guidance_is_bound_to_figure_and_extract() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[0]
    guidance = " ".join(question.mark_scheme).casefold()

    assert question.topic_id == "1.2.3"
    assert "relatively price inelastic" in question.prompt
    assert question.source_text.startswith("Figure 1 shows")
    assert "Extract A reports" in question.source_text
    assert "15%" in guidance and "6%" in guidance
    assert "capacity" in guidance and "contracts" in guidance
    assert "price-inelastic supply" in guidance
    assert "6%" in guidance and "15%" in guidance
    assert "qualitative comparison is sufficient" in guidance
    assert "more elastic over time" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_three_healthcare_externality_is_source_bound() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[5]
    guidance = " ".join(question.mark_scheme)

    assert question.topic_id == "1.3" and question.marks == 5
    assert question.source_reference == "Figure 3 and Extract D"
    assert question.source_text.startswith("Figure 3 compares")
    assert "Extract D reports" in question.source_text
    assert "untreated chemical waste" in question.source_text
    assert "negative production externality" in question.prompt
    assert "market output is 117 million doses" in guidance
    assert "socially efficient 100 million doses" in guidance
    assert "external marginal clean-up and health cost of £6 per dose" in guidance
    assert "Marginal social cost includes marginal private cost plus marginal external cost" in guidance
    assert "deadweight welfare loss" in guidance
    assert "streetlights" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_three_healthcare_section_remains_case_bound() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    labour, intervention, capacity, state = blueprint.questions[6:10]

    labour_guidance = " ".join(labour.mark_scheme).casefold()
    assert labour.source_text.startswith("Extract E reports")
    assert "vacancies" in labour.source_text and "14 weeks" in labour.source_text
    assert labour.assessment_contract["scheme_mode"] == "points"
    assert "occupational immobility" in labour_guidance
    assert "annual staff turnover reached 12%" in labour_guidance

    intervention_guidance = " ".join(intervention.mark_scheme).casefold()
    assert len(intervention.mark_scheme) >= 12
    assert "prices changed by 28%" in intervention_guidance
    assert "healthcare and pharmaceuticals" in intervention_guidance
    assert "inelastic demand" in intervention_guidance
    assert "government failure" in intervention_guidance

    capacity_guidance = " ".join(capacity.mark_scheme).casefold()
    assert "productive capacity in healthcare and pharmaceuticals" in capacity.prompt
    assert "output in healthcare and pharmaceuticals changed by 16%" in capacity_guidance
    assert "4% planned-investment increase" in capacity_guidance
    assert "energy-sector" not in capacity_guidance
    assert "extract e" in capacity_guidance
    assert capacity.assessment_contract["evaluation_marks"] == 9
    assert "limited maintenance staff and college places may delay effective use of capital" in capacity_guidance
    assert "imported machinery creates a leakage" in capacity_guidance
    assert "no particular condition is prescribed" in capacity_guidance
    assert "Imported component invoices and negotiated wages both rose" in capacity.source_text
    assert "short-run aggregate supply left" not in capacity.source_text

    state_guidance = " ".join(state.mark_scheme).casefold()
    assert "greater state intervention in healthcare and pharmaceuticals" in state.prompt
    assert "13% international-price movement" in state_guidance
    assert "healthcare" in state_guidance
    assert "extract f" in state_guidance
    assert "energy" not in state_guidance
    assert state.assessment_contract["evaluation_marks"] == 9
    assert "no named instrument or condition is compulsory" in state_guidance


def test_paper_three_business_growth_guidance_examines_two_cost_factors() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[1]
    guidance = " ".join(question.mark_scheme).casefold()

    assert question.topic_id == "3.1" and question.marks == 8
    assert question.assessment_contract["scheme_mode"] == "points"
    assert question.source_text.startswith("Figure 2 shows")
    assert "Extract A reports" in question.source_text
    assert "unit input costs by 4%" in question.source_text
    assert "capital spending increased by 5%" in guidance
    assert guidance.count("ao1 (1 mark)") == 2
    assert guidance.count("ao3 (1 mark)") == 2
    assert "two distinct relevant qualifications" in guidance
    assert "long-run average cost" in guidance and "reducing lrac" in guidance
    assert "capacity utilisation uncertain" in guidance
    assert "coordination diseconomies" in guidance
    assert "unit input costs by 4%" in guidance
    assert "diseconomies" in guidance
    assert "lego" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_three_market_failure_discussion_is_welfare_focused() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[2]
    guidance = " ".join(question.indicative_content).casefold()

    assert question.topic_id == "1.3" and question.marks == 12
    assert "significant loss of economic welfare" in question.prompt
    assert "respiratory treatment without reimbursement" in question.source_text
    assert "premises which paid no fee" in question.source_text
    assert "msc > mpc" in guidance
    assert "msb > mpb" in guidance
    assert "deadweight welfare loss" in guidance
    assert question.assessment_contract["kaa_marks"] == 8
    assert question.assessment_contract["evaluation_marks"] == 4
    assert "without the service necessarily being a pure public good" in guidance
    assert "must not replace" in guidance
    assert "contracts, reputation, property rights" in guidance
    assert question.assessment_contract["kaa_bands"][-1] == [6, 8]
    assert question.assessment_contract["evaluation_bands"][-1] == [3, 4]
    assert "streetlights" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_three_capacity_essay_balances_micro_and_macro_routes() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[3]
    guidance = " ".join(question.mark_scheme)

    assert question.topic_id == "2.3" and question.marks == 25
    assert "energy-sector productive capacity" in question.prompt
    assert "productive potential, output and price level of the UK economy" in question.prompt
    assert question.assessment_objectives == {"AO1": 4, "AO2": 4, "AO3": 8, "AO4": 9}
    assert question.assessment_contract["kaa_marks"] == 16
    assert question.assessment_contract["evaluation_marks"] == 9
    assert "microeconomic and macroeconomic" in guidance
    assert "not additive" in guidance
    assert "supported conclusion" in guidance
    assert "11%" in guidance and "5%" in guidance
    assert "strongest answer integrates relevant microeconomic and macroeconomic effects" in guidance
    assert "classical view" not in guidance
    assert question.mark_scheme == question.indicative_content


def test_paper_three_state_essay_balances_policy_scopes() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[4]
    guidance = " ".join(question.mark_scheme)

    assert question.topic_id == "4.5" and question.marks == 25
    assert "greater state intervention" in question.prompt
    assert "public investment, taxation, regulation or trade policy" in question.prompt
    assert question.assessment_objectives == {"AO1": 4, "AO2": 4, "AO3": 8, "AO4": 9}
    assert question.assessment_contract["kaa_marks"] == 16
    assert question.assessment_contract["evaluation_marks"] == 9
    assert "microeconomic and macroeconomic" in guidance
    assert "not additive" in guidance
    assert "supported conclusion" in guidance
    assert "14%" in guidance
    assert "strongest answer integrates relevant microeconomic and macroeconomic effects" in guidance
    assert "defence (6%)" not in guidance and "health care (18%)" not in guidance
    assert question.mark_scheme == question.indicative_content


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


def test_section_a_structure_is_fixed_but_stimuli_remain_variable():
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
    assert q5_part_orders == {("explain", "mcq")}


def test_section_a_stimulus_pool_is_wide_and_random():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    seen_stimuli = set()
    for seed in range(100):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        seen_stimuli.update(question.stimulus_kind for question in blueprint.questions if question.section == "A")

    assert len(seen_stimuli) >= 20
    assert {
        "ped_data_table",
        "pes_data_table",
        "marginal_utility_table",
        "opportunity_cost_ppc_table",
        "market_share_bar_chart",
        "business_objective_context",
        "xed_context",
        "imperfect_information_context",
        "minimum_wage_context",
        "payoff_matrix",
        "line_graph",
        "concentration_ratio_table",
        "contestability_barrier_table",
        "shutdown_cost_table",
        "context_extract",
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
        "opportunity_cost_ppc_table",
        "shutdown_cost_table",
        "wage_rate_table",
        "income_tax_schedule_table",
        "public_spending_pie_table",
        "household_savings_line_chart",
        "investment_line_chart",
        "current_account_line_chart",
        "inequality_line_chart",
        "gdp_growth_bar_chart",
        "unemployment_rate_bar_chart",
        "terms_of_trade_index_chart",
        "exchange_rate_index_chart",
        "macro_chart",
        "bar_chart",
        "line_graph",
        "index_number_chart",
    }

    for paper_id in ("paper_1", "paper_2"):
        config = load_builtin_paper_config(paper_id)
        for seed in range(120):
            blueprint = build_paper_blueprint(config, syllabus, seed=seed)
            section_a = [question for question in blueprint.questions if question.section == "A"]
            for question in section_a:
                if any(part.command_word == "calculate" for part in question.parts):
                    assert question.stimulus_kind in numeric_stimuli


def test_household_savings_calculation_is_answerable_from_the_chart() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"),
        syllabus,
        seed=26082919,
    )
    question = blueprint.questions[0]
    calculation = question.parts[1]
    explanation = question.parts[2]

    assert question.stimulus_kind == "household_savings_line_chart"
    assert "range" in calculation.prompt.casefold()
    values = question.source_instance.values
    assert f"Working: {max(values)} − {min(values)}" in calculation.mark_scheme
    assert f"Saving rate range: {max(values) - min(values):.1f} percentage points" in calculation.mark_scheme
    assert any("precautionary" in point.casefold() for point in explanation.mark_scheme)
    assert set(calculation.mark_scheme).isdisjoint(explanation.mark_scheme)


def test_paper_two_three_part_guidance_stays_distinct_across_seed_pool() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")

    for seed in range(200):
        question = build_paper_blueprint(config, syllabus, seed=seed).questions[0]
        written_parts = [part for part in question.parts if part.command_word != "mcq"]
        points = [
            point
            for part in written_parts
            for point in part.mark_scheme
            if point.strip()
        ]
        assert len(points) == len(set(points)), (seed, question.stimulus_kind)


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
    config.sections[0].part_command_words[0] = ["calculate", "mcq"]
    config.sections[0].stimulus_slots[0] = ["pes_data_table"]

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
    observed_plans = set()
    for seed in range(160):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        section_a = [question for question in blueprint.questions if question.section == "A"]
        observed_plans.add(
            tuple(tuple((part.command_word, part.marks) for part in question.parts) for question in section_a)
        )
        for question in blueprint.questions:
            if question.section == "A":
                seen_stimuli.add(question.stimulus_kind)

    assert {
        "household_savings_line_chart",
        "investment_line_chart",
        "financial_market_context",
        "current_account_line_chart",
        "terms_of_trade_index_chart",
        "labour_inactivity_context",
        "multiplier_context",
        "tariff_context",
        "exchange_rate_index_chart",
    } <= seen_stimuli
    assert observed_plans == {
        (
            (("mcq", 1), ("calculate", 2), ("explain", 2)),
            (("mcq", 1), ("explain", 4)),
            (("explain", 4), ("mcq", 1)),
            (("mcq", 1), ("explain", 4)),
            (("explain", 4), ("mcq", 1)),
        )
    }


def test_section_a_can_cover_all_allowed_paper_1_topics_across_random_seeds():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    expected_topic_ids = syllabus.topic_ids_for_themes(config.allowed_themes) - {"1.2.1"}

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

    assert "digital-games" in section_b_text and "development" in section_b_text
    assert "A UK market linked to market structures" not in section_b_text
    assert "average prices changed" not in section_b_text


def test_paper_1_labour_market_sources_are_exam_like_not_generic():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "3.5")
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
    assert "bakery" in section_b_text and "flour" in section_b_text
    assert all(q.source_instance.provenance == "illustrative-generated" for q in blueprint.questions)
    assert max(len(source) for source in section_b_sources) - min(len(source) for source in section_b_sources) > 80
    assert sum(any(token in source for token in ["£", "%", "2023", "2024"]) for source in section_b_sources) >= 3


def test_paper_2_sources_use_real_world_macro_data_and_varied_lengths():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "2.1")
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]
    section_b_text = " ".join(section_b_sources)

    assert "A UK case study on" not in section_b_text
    assert "monthly orders fall from 120 to 100" in section_b_text
    assert "capacity is 160" in section_b_text
    assert all(q.source_instance.provenance == "illustrative-generated" for q in blueprint.questions)
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
    assert any("bakery" in source or "own-brand" in source for source in section_c_sources)


def test_low_level_section_b_supply_sources_are_long_enough_for_extract_pages():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "1.2.3")
    section_b_sources = [question.source_text for question in blueprint.questions if question.section == "B"]

    assert min(len(source) for source in section_b_sources[:4]) >= 300
    assert "semiconductor" in " ".join(section_b_sources).casefold()
    assert "specialist components" in " ".join(section_b_sources)


def test_low_level_section_b_supply_questions_are_not_bare_topic_prompts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")

    blueprint = _blueprint_with_section_b_topic(config, syllabus, "1.2.3")
    section_b_prompts = [question.prompt for question in blueprint.questions if question.section == "B"]
    prompt_text = " ".join(section_b_prompts).lower()

    assert "effect of supply" not in prompt_text
    assert "likely effects of supply" not in prompt_text
    assert "affecting supply" not in prompt_text
    assert "capacity and input constraints" in prompt_text
    assert "short-run supply response" in prompt_text
    assert "short-run and long-run" in prompt_text


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
