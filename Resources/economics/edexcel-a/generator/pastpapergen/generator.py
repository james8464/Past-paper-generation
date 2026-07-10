from __future__ import annotations

import random

from pastpapergen.models import (
    MultipleChoiceOption,
    PaperBlueprint,
    PaperConfig,
    QuestionBlueprint,
    QuestionPart,
    Syllabus,
)
from pastpapergen.notes import essay_capable_topic_ids, note_points_for_topic
from pastpapergen.source_cases import data_response_extract, section_c_extract


def build_paper_blueprint(
    config: PaperConfig,
    syllabus: Syllabus,
    seed: int | None = None,
) -> PaperBlueprint:
    rng = random.Random(seed)
    topics = syllabus.topics_for_themes(config.allowed_themes)
    if not topics:
        raise ValueError("No syllabus topics available for this paper.")
    essay_topic_ids = essay_capable_topic_ids({topic.id for topic in topics})
    theme_plan = _theme_plan(config, rng)

    questions: list[QuestionBlueprint] = []
    absolute_question_number = 1
    for section in config.sections:
        choice_lookup = _choice_lookup(section.choice_groups)
        choice_group_topics: dict[int, set[str]] = {}
        section_topic_ids: set[str] = set()
        section_templates = _section_templates(section, rng)
        section_theme_targets = theme_plan.get(section.name, [])
        source_context_topic = (
            _choose_topic(
                rng,
                _topics_for_theme(_topics_matching(topics, essay_topic_ids), section_theme_targets[0])
                if section_theme_targets
                else _topics_matching(topics, essay_topic_ids),
                set(),
            )
            if _uses_single_source_context(config.id, section.name)
            else None
        )
        if source_context_topic:
            section_topic_ids.add(source_context_topic.id)
        for index, marks in enumerate(section.question_marks):
            group_index = choice_lookup.get(index)
            excluded_ids = set(section_topic_ids)
            if group_index is not None:
                excluded_ids.update(choice_group_topics.get(group_index, set()))
            part_marks, part_commands, stimulus_kind = _section_template(section, section_templates, index)
            available_topics = _topic_pool_for_question(topics, essay_topic_ids, marks, section.name)
            if index < len(section_theme_targets):
                available_topics = _topics_for_theme(available_topics, section_theme_targets[index])
            stimulus_kind = _compatible_stimulus_kind(
                section.stimulus_kinds,
                part_commands,
                available_topics,
                excluded_ids,
                stimulus_kind,
                rng,
            )
            available_topics = _topics_suitable_for_template(available_topics, part_commands, stimulus_kind)
            topic = source_context_topic or _choose_topic(rng, available_topics, excluded_ids)
            command_word = section.command_words[index]
            number = _question_number(config.id, section.name, absolute_question_number, index)
            parts = _build_parts(part_marks, part_commands, topic.title, stimulus_kind, rng)
            source_reference = _source_reference(config.id, section.name, index)
            if group_index is not None:
                choice_group_topics.setdefault(group_index, set()).add(topic.id)
            section_topic_ids.add(topic.id)
            questions.append(
                QuestionBlueprint(
                    section=section.name,
                    number=number,
                    marks=marks,
                    command_word=command_word,
                    topic_id=topic.id,
                    prompt=_question_prompt(
                        config.id,
                        section.name,
                        command_word,
                        marks,
                        topic.title,
                        parts,
                        stimulus_kind,
                        source_reference,
                    ),
                    parts=parts,
                    stimulus_kind=stimulus_kind,
                    choice_group=_choice_group_name(config.id, section.name, group_index),
                    source_reference=source_reference,
                    source_title=_source_title(topic.title, section.name),
                    source_text=_source_text(topic.id, topic.title, topic.points, section.name, index, stimulus_kind),
                    mark_breakdown=_mark_breakdown(marks, parts),
                    mark_scheme=_mark_scheme(command_word, marks, topic.title),
                    indicative_content=_indicative_content(topic.id, topic.title, topic.points),
                )
            )
        absolute_question_number += _section_question_increment(config.id, section.name)

    return PaperBlueprint(
        paper_id=config.id,
        paper_code=config.code,
        title=config.title,
        duration_minutes=config.duration_minutes,
        total_marks=config.total_marks,
        questions=questions,
    )


def _choice_lookup(choice_groups: list[list[int]]) -> dict[int, int]:
    lookup: dict[int, int] = {}
    for group_index, group in enumerate(choice_groups, start=1):
        for question_index in group:
            lookup[question_index] = group_index
    return lookup


def _choose_topic(rng: random.Random, topics, excluded_ids: set[str]):
    available = [topic for topic in topics if topic.id not in excluded_ids]
    return rng.choice(available or topics)


def _theme_plan(config: PaperConfig, rng: random.Random) -> dict[str, list[int]]:
    if config.id not in {"paper_1", "paper_2"}:
        return {}
    themes = sorted(config.allowed_themes)
    data_response_theme = rng.choice(themes)
    essay_theme = next(theme for theme in themes if theme != data_response_theme)
    section_a_themes = [data_response_theme, data_response_theme, essay_theme, essay_theme, essay_theme]
    rng.shuffle(section_a_themes)
    return {
        "A": section_a_themes,
        "B": [data_response_theme] * 5,
        "C": [essay_theme] * 2,
    }


def _topics_for_theme(topics, theme: int):
    matched = [topic for topic in topics if topic.theme == theme]
    return matched or topics


def _section_templates(section, rng: random.Random) -> list[tuple[list[int], list[str], str]]:
    if not section.part_marks:
        return []
    templates = list(zip(section.part_marks, section.part_command_words, strict=True))
    rng.shuffle(templates)
    stimulus_kinds = _selected_stimulus_kinds(section.stimulus_kinds, len(templates), rng)
    return [
        (list(part_marks), list(part_commands), stimulus_kinds[index])
        for index, (part_marks, part_commands) in enumerate(templates)
    ]


def _selected_stimulus_kinds(stimulus_kinds: list[str], count: int, rng: random.Random) -> list[str]:
    if not stimulus_kinds:
        return [""] * count
    if len(stimulus_kinds) >= count:
        return rng.sample(stimulus_kinds, count)
    return [rng.choice(stimulus_kinds) for _ in range(count)]


def _section_template(section, templates: list[tuple[list[int], list[str], str]], index: int) -> tuple[list[int], list[str], str]:
    if templates:
        return templates[index]
    return [], [], _stimulus_kind(section, index)


def _topics_matching(topics, topic_ids: set[str]):
    matched = [topic for topic in topics if topic.id in topic_ids]
    return matched or topics


def _topic_pool_for_question(topics, essay_topic_ids: set[str], marks: int, section_name: str):
    if marks >= 15 or section_name in {"B", "C"}:
        return _topics_matching(topics, essay_topic_ids)
    return topics


def _topics_suitable_for_template(topics, part_commands: list[str], stimulus_kind: str):
    suitable_ids = _STIMULUS_TOPIC_IDS.get(stimulus_kind)
    if suitable_ids:
        matched = [topic for topic in topics if topic.id in suitable_ids]
        if matched:
            return matched
        if part_commands and part_commands[0] == "draw":
            draw_matched = [topic for topic in topics if topic.id in _DRAW_CAPABLE_TOPIC_IDS]
            return draw_matched or topics
        return topics
    if part_commands and part_commands[0] == "draw":
        matched = [topic for topic in topics if topic.id in _DRAW_CAPABLE_TOPIC_IDS]
        return matched or topics
    return topics


def _compatible_stimulus_kind(
    stimulus_kinds: list[str],
    part_commands: list[str],
    topics,
    excluded_ids: set[str],
    preferred_kind: str,
    rng: random.Random,
) -> str:
    if not stimulus_kinds:
        return preferred_kind
    candidates = [preferred_kind, *rng.sample(stimulus_kinds, len(stimulus_kinds))]
    seen: set[str] = set()
    for kind in candidates:
        if kind in seen:
            continue
        seen.add(kind)
        if not _stimulus_matches_commands(kind, part_commands):
            continue
        suitable_ids = _STIMULUS_TOPIC_IDS.get(kind)
        if suitable_ids and not any(topic.id in suitable_ids and topic.id not in excluded_ids for topic in topics):
            continue
        if not suitable_ids and not any(topic.id not in excluded_ids for topic in topics):
            continue
        return kind
    command_compatible = [kind for kind in stimulus_kinds if _stimulus_matches_commands(kind, part_commands)]
    return rng.choice(command_compatible or [preferred_kind])


def _stimulus_matches_commands(stimulus_kind: str, part_commands: list[str]) -> bool:
    if any(command == "calculate" for command in part_commands):
        return stimulus_kind in _CALCULATION_STIMULI
    if part_commands and part_commands[0] == "draw":
        return stimulus_kind in _DRAW_FIRST_STIMULI
    return stimulus_kind not in _DRAW_ONLY_CONTEXTS


def _uses_single_source_context(paper_id: str, section_name: str) -> bool:
    return paper_id in {"paper_1", "paper_2"} and section_name == "B"


def _choice_group_name(paper_id: str, section_name: str, group_index: int | None) -> str | None:
    if group_index is None:
        return None
    return f"{paper_id}-{section_name}-choice-{group_index}"


def _section_question_increment(paper_id: str, section_name: str) -> int:
    if paper_id in {"paper_1", "paper_2"} and section_name == "A":
        return 5
    return 1


def _question_number(
    paper_id: str,
    section_name: str,
    absolute_question_number: int,
    section_index: int,
) -> str:
    if paper_id in {"paper_1", "paper_2"}:
        if section_name == "A":
            return str(absolute_question_number + section_index)
        if section_name == "B":
            return f"{absolute_question_number}({chr(97 + section_index)})"
        return str(absolute_question_number + section_index)
    section_number = 1 if section_name == "A" else 2
    return f"{section_number}({chr(97 + section_index)})"


_EXAM_FOCUS = {
    "rational decision making": "consumers comparing marginal benefit and marginal cost",
    "demand": "a change in consumer demand",
    "supply": "changes in production costs and the availability of inputs",
    "price determination": "changes in equilibrium price and quantity",
    "market failure": "external costs and the socially efficient level of output",
    "government intervention": "indirect taxes, subsidies or regulation",
    "government intervention in markets": "a government policy affecting prices and output",
    "business growth": "a firm expanding to achieve economies of scale",
    "business objectives": "a firm choosing between profit maximisation and growth",
    "revenues, costs and profits": "a firm's costs, revenues and profit",
    "market structures": "market concentration, barriers to entry and contestability",
    "labour market": "wage rates, vacancies and labour market flexibility",
    "measures of economic performance": "changes in inflation, GDP, unemployment and living standards",
    "aggregate demand": "changes in consumption, investment and aggregate demand",
    "aggregate supply": "changes in costs, productivity and productive capacity",
    "national income": "changes in injections, leakages and the multiplier",
    "economic growth": "changes in real GDP and productive potential",
    "macroeconomic objectives and policies": "conflicts between inflation, growth, unemployment and the current account",
    "international economics": "changes in trade, exchange rates and protectionism",
    "poverty and inequality": "changes in income inequality and living standards",
    "emerging and developing economies": "barriers to development and strategies to reduce poverty",
    "financial sector": "credit creation, regulation and financial market failure",
    "role of the state in the macroeconomy": "taxation, public spending and regulation",
}


_DRAW_CAPABLE_TOPIC_IDS = {
    "1.2.2",
    "1.2.3",
    "1.2.4",
    "1.3",
    "1.4",
    "2.2",
    "2.3",
    "2.5",
    "2.6",
    "3.1",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "4.1",
    "4.2",
    "4.4",
    "4.5",
}


_DRAW_FIRST_STIMULI = {
    "business_objective_context",
    "minimum_wage_context",
    "context_extract",
    "cost_revenue_graph",
    "market_diagram",
    "demand_shift_graph",
    "supply_shift_graph",
    "tax_subsidy_diagram",
    "externality_diagram",
    "consumer_surplus_diagram",
    "producer_surplus_diagram",
    "minimum_price_diagram",
    "maximum_price_diagram",
    "production_possibility_frontier",
    "perfect_competition_diagram",
    "monopoly_diagram",
    "monopsony_diagram",
    "labour_market_diagram",
}


_DRAW_ONLY_CONTEXTS = set()


_CALCULATION_STIMULI = {
    "ped_data_table",
    "pes_data_table",
    "market_share_bar_chart",
    "data_table",
    "elasticity_data_table",
    "concentration_ratio_table",
    "opportunity_cost_ppc_table",
    "shutdown_cost_table",
    "wage_rate_table",
    "development_data_table",
    "balance_payments_table",
    "inflation_index_table",
    "income_tax_schedule_table",
    "public_spending_pie_table",
    "labour_inactivity_context",
}


_STIMULUS_TOPIC_IDS = {
    "ped_data_table": {"1.2.2"},
    "pes_data_table": {"1.2.3"},
    "market_share_bar_chart": {"3.4"},
    "marginal_utility_table": {"1.1"},
    "opportunity_cost_ppc_table": {"1.1"},
    "business_objective_context": {"3.2"},
    "xed_context": {"1.2.2"},
    "imperfect_information_context": {"1.3"},
    "minimum_wage_context": {"3.5"},
    "household_savings_line_chart": {"2.1", "2.2"},
    "investment_line_chart": {"2.2"},
    "financial_market_context": {"4.4"},
    "development_data_table": {"2.1", "4.2", "4.3"},
    "current_account_line_chart": {"4.1", "2.6"},
    "gdp_growth_bar_chart": {"2.1", "2.5"},
    "terms_of_trade_index_chart": {"4.1"},
    "exchange_rate_index_chart": {"4.1"},
    "unemployment_rate_bar_chart": {"2.1", "2.6"},
    "income_tax_schedule_table": {"4.5"},
    "public_spending_pie_table": {"4.5", "2.6"},
    "labour_inactivity_context": {"2.1", "2.6"},
    "multiplier_context": {"2.4", "2.2"},
    "tariff_context": {"4.1"},
    "cost_revenue_graph": {"3.2", "3.3", "3.4"},
    "elasticity_data_table": {"1.2.2"},
    "concentration_ratio_table": {"3.4"},
    "shutdown_cost_table": {"3.3"},
    "wage_rate_table": {"3.5"},
    "contestability_barrier_table": {"3.4"},
    "data_table": {"1.2.2", "1.2.3", "1.2.4", "2.1", "4.1", "4.2", "4.3"},
    "market_diagram": {"1.2.2", "1.2.3", "1.2.4", "1.3", "1.4", "3.6"},
    "demand_shift_graph": {"1.2.2", "1.2.4"},
    "supply_shift_graph": {"1.2.3", "1.2.4"},
    "perfect_competition_diagram": {"3.3", "3.4"},
    "monopoly_diagram": {"3.3", "3.4"},
    "monopsony_diagram": {"3.5"},
    "labour_market_diagram": {"3.5"},
    "payoff_matrix": {"3.2", "3.4"},
    "externality_diagram": {"1.3", "1.4", "3.6"},
    "consumer_surplus_diagram": {"1.2.2", "1.2.3", "1.2.4", "1.3", "1.4", "3.6"},
    "producer_surplus_diagram": {"1.2.2", "1.2.3", "1.2.4", "1.3", "1.4", "3.6"},
    "minimum_price_diagram": {"1.4", "3.6", "3.5"},
    "maximum_price_diagram": {"1.4", "3.6"},
    "tax_subsidy_diagram": {"1.4", "3.6", "1.3"},
    "tax_incidence_diagram": {"1.2.2", "1.2.3", "1.4"},
    "macro_chart": {"2.2", "2.3", "2.5", "2.6"},
    "trade_cycle": {"2.1", "2.5"},
    "balance_payments_table": {"4.1", "2.6"},
    "inflation_index_table": {"2.1", "2.6"},
    "ad_as_diagram": {"2.2", "2.3", "2.5", "2.6"},
    "keynesian_as_diagram": {"2.2", "2.3", "2.5", "2.6"},
    "phillips_curve": {"2.1", "2.6"},
    "lorenz_curve": {"4.2"},
    "exchange_rate_diagram": {"4.1"},
    "tariff_diagram": {"4.1"},
    "money_market_diagram": {"4.4"},
    "laffer_curve": {"4.5"},
    "poverty_trap_diagram": {"4.2", "4.3"},
    "index_number_chart": {"1.2.4", "2.1", "3.1", "3.3", "4.1"},
    "line_graph": {"1.2.2", "1.2.3", "1.2.4", "2.1", "2.5", "3.1", "3.3", "3.4", "3.5", "4.1", "4.2"},
    "bar_chart": {"2.1", "2.5", "3.4", "4.2"},
}


_STIMULUS_PART_PROMPTS = {
    "ped_data_table": {
        (None, "explain", 4): "With reference to the data above, explain one likely reason for the difference in price elasticity of demand.",
        (None, "calculate", 4): "Calculate the likely percentage change in quantity demanded following the price change. You are advised to show your working.",
    },
    "pes_data_table": {
        (None, "explain", 4): "With reference to the data above, explain one likely reason for the difference in price elasticity of supply.",
        (None, "calculate", 4): "Using the PES value for the rural market, calculate the percentage increase in price if quantity supplied increases by 3.6%. You are advised to show your working.",
    },
    "market_share_bar_chart": {
        (None, "explain", 4): "With reference to the information above, explain the market structure of the industry shown.",
        (None, "calculate", 4): "Calculate the value of the largest firm's sales from the market share shown. You are advised to show your working.",
    },
    "data_table": {
        (None, "calculate", 2): "Using the data above, calculate the difference between the quantity demanded index and the average price index in 2023. You are advised to show your working.",
        (None, "calculate", 4): "Using the data above, calculate the percentage change in the quantity demanded index between 2021 and 2023. You are advised to show your working.",
    },
    "elasticity_data_table": {
        (None, "calculate", 4): "Assume the price of cinema tickets falls by 5%. Using the PED value shown, calculate the expected percentage change in quantity demanded. You are advised to show your working.",
    },
    "concentration_ratio_table": {
        (None, "calculate", 4): "Using the data above, calculate the three-firm concentration ratio. You are advised to show your working.",
    },
    "marginal_utility_table": {
        (None, "explain", 4): "With reference to the data above, explain why a rational consumer may stop buying additional units.",
    },
    "opportunity_cost_ppc_table": {
        (None, "calculate", 4): "Using the data above, calculate the opportunity cost of increasing production of capital goods from 20 to 40 units. You are advised to show your working.",
        (None, "explain", 4): "With reference to the data above, explain what is meant by opportunity cost.",
    },
    "shutdown_cost_table": {
        (None, "calculate", 4): "Using the data above, calculate the firm's total profit or loss at the current output. You are advised to show your working.",
        (None, "explain", 4): "With reference to the data above, explain whether the firm should continue producing in the short run.",
    },
    "wage_rate_table": {
        (None, "calculate", 4): "Using the data above, calculate the percentage change in the average hourly wage. You are advised to show your working.",
        (None, "explain", 4): "With reference to the data above, explain one likely reason for a change in labour supply.",
    },
    "contestability_barrier_table": {
        (None, "explain", 4): "With reference to the data above, explain one factor that may affect the contestability of this market.",
    },
    "balance_payments_table": {
        (None, "calculate", 2): "Using the data provided, calculate the change in exports between 2021 and 2023. You are advised to show your working.",
        (None, "calculate", 4): "Using the data provided, calculate the trade deficit in 2023. You are advised to show your working.",
    },
    "inflation_index_table": {
        (None, "calculate", 2): "Using the CPI index, calculate the index-point increase between 2021 and 2023. You are advised to show your working.",
        (None, "calculate", 4): "Using the CPI index, calculate the percentage increase between 2021 and 2023. You are advised to show your working.",
    },
    "cost_revenue_graph": {
        (None, "calculate", 4): "Calculate the change in total supernormal profit if the firm changes output. You are advised to show your working.",
        (None, "explain", 4): "Explain one likely reason why the firm may choose the output shown in the diagram.",
    },
    "perfect_competition_diagram": {
        (None, "draw", 4): "Draw a cost and revenue diagram to show a firm in perfect competition making normal profit.",
        (None, "explain", 4): "Explain one likely reason why firms in perfect competition may make only normal profit in the long run.",
    },
    "monopoly_diagram": {
        (None, "draw", 4): "Draw a cost and revenue diagram to show a profit-maximising monopoly making supernormal profit.",
        (None, "explain", 4): "Explain one likely reason why the firm in the diagram may earn supernormal profit.",
    },
    "monopsony_diagram": {
        (None, "draw", 4): "Draw a labour market diagram to show the wage and employment level set by a monopsonist.",
        (None, "explain", 4): "Explain one likely effect of monopsony power in a labour market.",
    },
    "labour_market_diagram": {
        (None, "draw", 4): "Draw a labour market diagram to show the likely impact of an increase in demand for labour.",
        (None, "explain", 4): "Explain one likely reason why wage rates may differ between labour markets.",
    },
    "business_objective_context": {
        (None, "draw", 4): "Draw a cost and revenue diagram to illustrate profit maximisation and revenue maximisation.",
        (None, "explain", 4): "With reference to the information above, explain one reason why a firm may prioritise sales growth.",
    },
    "xed_context": {
        (None, "explain", 4): "With reference to the data above, explain the likely relationship between the two goods.",
    },
    "imperfect_information_context": {
        (None, "explain", 4): "With reference to the data above, explain how imperfect market information may lead to a misallocation of resources.",
    },
    "minimum_wage_context": {
        (None, "draw", 4): "Draw a labour market diagram to show the likely impact of the increase in the National Minimum Wage.",
        (None, "explain", 4): "Explain one likely effect of the increase in the National Minimum Wage on firms.",
    },
    "household_savings_line_chart": {
        (1, "calculate", 2): "Calculate the total amount saved by the average household. You are advised to show your working.",
        (2, "explain", 2): "Explain one likely reason for the change in household savings over the period shown.",
    },
    "investment_line_chart": {
        (None, "explain", 4): "With reference to the data, explain one likely effect of the fall in investment on aggregate demand.",
    },
    "financial_market_context": {
        (None, "explain", 4): "With reference to the information above, explain what is meant by market rigging.",
    },
    "development_data_table": {
        (None, "calculate", 2): "Using the data provided, calculate the difference in HDI between Morocco and Pakistan. You are advised to show your working.",
        (None, "calculate", 4): "Using the data provided, calculate the difference in GDP per capita between Morocco and Pakistan. You are advised to show your working.",
        (None, "explain", 4): "With reference to the data provided, explain one limitation of using GDP to compare living standards between countries.",
    },
    "current_account_line_chart": {
        (None, "explain", 4): "With reference to the chart above, explain one likely reason for the change in the current account balance.",
    },
    "gdp_growth_bar_chart": {
        (1, "explain", 2): "Explain one likely disadvantage of a decline in GDP for workers.",
        (2, "explain", 2): "Explain one likely disadvantage of a decline in GDP for the government.",
    },
    "terms_of_trade_index_chart": {
        (0, "explain", 2): "Explain what is meant by terms of trade.",
        (2, "explain", 2): "Explain the likely impact of the change in the terms of trade on the current account.",
    },
    "labour_inactivity_context": {
        (None, "calculate", 2): "Calculate the total number of inactive workers. You are advised to show your working.",
        (0, "calculate", 2): "Calculate the total number of inactive workers. You are advised to show your working.",
        (1, "explain", 2): "Explain one likely reason for the high level of inactivity in the labour force.",
    },
    "multiplier_context": {
        (None, "calculate", 4): "Calculate the total increase in aggregate demand from an increase in government spending. You are advised to show your working.",
    },
    "tariff_context": {
        (None, "explain", 4): "Explain the likely impact of this tariff on the market for the imported good.",
    },
    "exchange_rate_index_chart": {
        (None, "explain", 4): "With reference to the chart above, explain one likely effect of the change in the exchange rate on exporters.",
    },
    "income_tax_schedule_table": {
        (None, "calculate", 2): "Using the data above, calculate the marginal tax rate for income between £50 271 and £125 140. You are advised to show your working.",
        (None, "explain", 2): "Explain one likely effect of a progressive income tax system on income inequality.",
    },
    "public_spending_pie_table": {
        (None, "calculate", 2): "Using the data above, calculate the percentage point difference between health and education spending. You are advised to show your working.",
        (None, "explain", 2): "Explain one likely opportunity cost of increased public spending on health.",
    },
    "unemployment_rate_bar_chart": {
        (None, "explain", 4): "With reference to the chart above, explain one likely macroeconomic effect of rising unemployment.",
    },
}


_STIMULUS_MCQ_PROMPTS = {
    "ped_data_table": "With reference to the table above, which one of the following is most likely to be correct?",
    "pes_data_table": "Which one of the following is the percentage increase in price implied by the data?",
    "market_share_bar_chart": "Which one of the following is the value of the largest firm's market share?",
    "marginal_utility_table": "With reference to the table above, which one of the following is most likely to be correct?",
    "opportunity_cost_ppc_table": "With reference to the table above, which one of the following is the opportunity cost of increasing capital goods output from 20 to 40 units?",
    "cost_revenue_graph": "Refer to the previous diagram. Which one of the following is most likely after a fall in demand?",
    "business_objective_context": "Which one of the following is most likely to occur if the firm changes to sales maximisation?",
    "xed_context": "Which one of the following is the most likely impact if the price of the substitute falls?",
    "imperfect_information_context": "Which one of the following is the most likely explanation of this behaviour?",
    "minimum_wage_context": "Which one of the following is the most likely cause of a decrease in the supply of workers?",
    "household_savings_line_chart": "With reference to the chart above, which one of the following is correct?",
    "investment_line_chart": "Which one of the following is the percentage point fall in investment between the two dates shown?",
    "financial_market_context": "Which one of the following is a role of financial markets?",
    "development_data_table": "With reference to the table above, which one of the following is correct?",
    "current_account_line_chart": "With reference to the chart above, which one of the following is correct?",
    "gdp_growth_bar_chart": "With reference to the chart above, which one of the following is correct?",
    "terms_of_trade_index_chart": "Which one of the following is the percentage change in the terms of trade?",
    "labour_inactivity_context": "Which one of the following would be the most likely result of an increase in labour force inactivity?",
    "multiplier_context": "Which one point on the trade cycle diagram above illustrates a boom?",
    "tariff_context": "Which one of the following is likely to give a country a comparative advantage in production?",
    "shutdown_cost_table": "With reference to the table above, which one of the following is most likely to be correct?",
    "wage_rate_table": "With reference to the table above, which one of the following is the percentage change in hourly wages?",
    "contestability_barrier_table": "With reference to the table above, which one of the following is most likely to increase contestability?",
    "exchange_rate_index_chart": "With reference to the chart above, which one of the following is most likely after an appreciation of sterling?",
    "income_tax_schedule_table": "With reference to the table above, which one of the following describes a progressive tax system?",
    "public_spending_pie_table": "With reference to the table above, which one of the following is an opportunity cost of increased health spending?",
    "unemployment_rate_bar_chart": "With reference to the chart above, which one of the following is a likely effect of rising unemployment?",
}


_STIMULUS_MCQ_OPTIONS = {
    "ped_data_table": [
        ("A", "Demand is more price elastic for the younger age group shown"),
        ("B", "Demand is perfectly price inelastic for both age groups"),
        ("C", "A rise in price always increases total revenue for both groups"),
        ("D", "Adults are more responsive to price changes than students"),
    ],
    "pes_data_table": [
        ("A", "2%"),
        ("B", "6.5%"),
        ("C", "15%"),
        ("D", "23.6%"),
    ],
    "market_share_bar_chart": [
        ("A", "£426 billion"),
        ("B", "£126 billion"),
        ("C", "£312 billion"),
        ("D", "£920 billion"),
    ],
    "marginal_utility_table": [
        ("A", "Marginal utility falls as additional units are consumed"),
        ("B", "Total utility always falls when consumption rises"),
        ("C", "Consumers never compare benefits and costs"),
        ("D", "Marginal utility is identical for every unit consumed"),
    ],
    "opportunity_cost_ppc_table": [
        ("A", "15 consumer goods"),
        ("B", "20 consumer goods"),
        ("C", "40 consumer goods"),
        ("D", "85 consumer goods"),
    ],
    "cost_revenue_graph": [
        ("A", "Average revenue and marginal revenue both fall"),
        ("B", "Average revenue rises and marginal revenue stays the same"),
        ("C", "Average revenue falls and marginal revenue increases"),
        ("D", "Average revenue increases and marginal revenue falls"),
    ],
    "business_objective_context": [
        ("A", "Average cost equals average revenue"),
        ("B", "Average cost is minimised"),
        ("C", "Price elasticity of demand is equal to -1"),
        ("D", "Price equals marginal cost"),
    ],
    "xed_context": [
        ("A", "Demand for the substitute good is likely to fall"),
        ("B", "Demand for the substitute good is likely to rise"),
        ("C", "Supply of the substitute good is likely to fall"),
        ("D", "Supply of the substitute good is likely to rise"),
    ],
    "imperfect_information_context": [
        ("A", "A firm is attempting to maximise sales or profit using market power"),
        ("B", "A firm is demonstrating allocative efficiency"),
        ("C", "A firm is removing information failure completely"),
        ("D", "A firm is operating in perfect competition"),
    ],
    "minimum_wage_context": [
        ("A", "Improved productivity in other industries"),
        ("B", "Higher net migration of workers into the industry"),
        ("C", "More workers retraining for the occupation"),
        ("D", "Lower real wages in the occupation"),
    ],
    "household_savings_line_chart": [
        ("A", "The savings rate was highest during the period of economic uncertainty"),
        ("B", "The savings rate was unchanged throughout the period"),
        ("C", "The savings rate was lowest at the end of the period"),
        ("D", "The savings rate was negative in every quarter shown"),
    ],
    "investment_line_chart": [
        ("A", "2.1"),
        ("B", "4.6"),
        ("C", "8.0"),
        ("D", "21.6"),
    ],
    "financial_market_context": [
        ("A", "To provide forward markets and credit"),
        ("B", "To promote moral hazard"),
        ("C", "To remove all risk from borrowers"),
        ("D", "To restrict trade"),
    ],
    "development_data_table": [
        ("A", "The country with the higher GNI per head also has the higher HDI"),
        ("B", "Life expectancy is shown directly in the table"),
        ("C", "Both countries have identical living standards"),
        ("D", "The country with lower GDP per capita has no economic activity"),
    ],
    "current_account_line_chart": [
        ("A", "The current account deficit narrowed during part of the period shown"),
        ("B", "The current account was always in surplus"),
        ("C", "The deficit was unchanged in every year"),
        ("D", "Exports must have been zero throughout the period"),
    ],
    "gdp_growth_bar_chart": [
        ("A", "Real GDP growth was negative in one of the quarters shown"),
        ("B", "Real GDP growth increased in every quarter shown"),
        ("C", "Real GDP growth was exactly zero in every quarter shown"),
        ("D", "The chart shows nominal GDP only"),
    ],
    "terms_of_trade_index_chart": [
        ("A", "12%"),
        ("B", "18%"),
        ("C", "35%"),
        ("D", "52%"),
    ],
    "labour_inactivity_context": [
        ("A", "A decrease in the productive potential of the economy"),
        ("B", "An increase in the labour force participation rate"),
        ("C", "A fall in the dependency ratio"),
        ("D", "A rightward shift of aggregate supply"),
    ],
    "multiplier_context": [
        ("A", "C"),
        ("B", "A"),
        ("C", "B"),
        ("D", "D"),
    ],
    "tariff_context": [
        ("A", "Higher productivity of workers"),
        ("B", "Higher corporation tax"),
        ("C", "Higher unit labour costs"),
        ("D", "Lower investment in capital goods"),
    ],
    "shutdown_cost_table": [
        ("A", "The firm covers its variable costs but makes a loss overall"),
        ("B", "The firm earns supernormal profit"),
        ("C", "Total revenue is zero"),
        ("D", "Average variable cost exceeds price by £18"),
    ],
    "wage_rate_table": [
        ("A", "16.7%"),
        ("B", "6.0%"),
        ("C", "2.4%"),
        ("D", "60.0%"),
    ],
    "contestability_barrier_table": [
        ("A", "Lower sunk costs"),
        ("B", "Higher legal barriers to entry"),
        ("C", "Exclusive access to key inputs"),
        ("D", "Stronger brand loyalty for incumbents"),
    ],
    "exchange_rate_index_chart": [
        ("A", "Exports may become more expensive to overseas buyers"),
        ("B", "Imports must become more expensive for UK consumers"),
        ("C", "The current account must immediately improve"),
        ("D", "Inflation must always rise"),
    ],
    "income_tax_schedule_table": [
        ("A", "The average tax rate tends to rise as taxable income rises"),
        ("B", "Every taxpayer pays the same cash amount of tax"),
        ("C", "The marginal tax rate is zero for high-income earners"),
        ("D", "Indirect taxes are always progressive"),
    ],
    "public_spending_pie_table": [
        ("A", "Less funding may be available for other areas of spending"),
        ("B", "All economic resources become unlimited"),
        ("C", "Private sector opportunity cost is removed"),
        ("D", "Tax revenue must fall to zero"),
    ],
    "unemployment_rate_bar_chart": [
        ("A", "Government spending on welfare benefits may increase"),
        ("B", "Tax revenue from income tax must rise"),
        ("C", "The economy must be producing beyond full capacity"),
        ("D", "The labour force participation rate must be 100%"),
    ],
}


_EXAM_CONTEXT = {
    "rational decision making": "consumer choice where marginal benefit is compared with marginal cost",
    "business objectives": "a firm deciding whether to prioritise profit, growth or sales revenue",
    "market failure": "a market where external costs may cause overproduction",
    "government intervention in markets": "a market where a price control, tax or subsidy may change incentives",
    "business growth": "a firm considering whether expansion will reduce average costs",
}


_TOPIC_MCQ_OPTIONS = {
    "demand": [
        ("A", "A rise in consumer income may increase demand for a normal good"),
        ("B", "A movement along the demand curve is caused by a change in advertising"),
        ("C", "An increase in demand always reduces equilibrium price"),
        ("D", "Demand is price inelastic when price elasticity of demand is greater than one"),
    ],
    "supply": [
        ("A", "Higher production costs may shift the supply curve to the left"),
        ("B", "Price elasticity of supply measures responsiveness of demand to income"),
        ("C", "An increase in supply always increases equilibrium price"),
        ("D", "Supply is perfectly elastic when firms cannot change output"),
    ],
    "rational decision making": [
        ("A", "Consumers may compare marginal benefit with marginal cost when making choices"),
        ("B", "Sunk costs should always determine current decisions"),
        ("C", "Rational consumers must have perfect information"),
        ("D", "Opportunity cost is zero when a consumer makes a choice"),
    ],
    "market failure": [
        ("A", "External costs may cause free-market output to exceed the socially efficient level"),
        ("B", "Indirect taxes always increase consumer surplus"),
        ("C", "Public goods are usually overprovided by the free market"),
        ("D", "Positive externalities mean marginal social cost is zero"),
    ],
    "government intervention in markets": [
        ("A", "A subsidy may lower production costs and increase market supply"),
        ("B", "A maximum price is always set above the market equilibrium"),
        ("C", "An indirect tax shifts the demand curve to the right"),
        ("D", "Regulation always eliminates government failure"),
    ],
    "business objectives": [
        ("A", "A firm may prioritise sales growth instead of short-run profit maximisation"),
        ("B", "Revenue maximisation always occurs where marginal cost is zero"),
        ("C", "Profit maximisation means output is produced where price is lowest"),
        ("D", "Satisficing means a firm always makes a loss"),
    ],
    "business growth": [
        ("A", "Internal growth may allow a firm to exploit economies of scale"),
        ("B", "External growth always reduces market concentration"),
        ("C", "Diseconomies of scale only occur in perfectly competitive markets"),
        ("D", "A merger always reduces barriers to entry"),
    ],
    "market structures": [
        ("A", "High barriers to entry may allow incumbent firms to maintain market power"),
        ("B", "A high concentration ratio proves that a market is perfectly competitive"),
        ("C", "Contestability falls when sunk costs become lower"),
        ("D", "Product differentiation is impossible in oligopoly"),
    ],
    "labour market": [
        ("A", "A rise in job vacancies may increase pressure on firms to raise wages"),
        ("B", "Monopsony power means there are many buyers of labour"),
        ("C", "Occupational immobility always increases labour supply immediately"),
        ("D", "A minimum wage is always set below the equilibrium wage"),
    ],
}


_SECTION_B_PROMPTS = {
    "demand": {
        5: "With reference to {reference}, explain one likely reason why demand for own-brand food increased.",
        8: "Examine two likely factors affecting the price elasticity of demand for rail travel.",
        10: "With reference to {reference}, assess whether demand for electronic devices is likely to be price inelastic.",
        12: "Discuss whether changes in real income are the main cause of changes in demand for consumer goods.",
        15: "With reference to {reference}, discuss the likely effects of a significant change in demand on firms and consumers.",
    },
    "supply": {
        5: "With reference to {reference}, explain one reason why shortages of semiconductors may affect the supply of cars.",
        8: "Examine two factors that may influence price elasticity of supply in the housebuilding market.",
        10: "With reference to {reference}, assess whether time lags are the main reason why renewable energy supply is slow to respond.",
        12: "Discuss whether investment in transmission infrastructure is likely to increase renewable energy supply.",
        15: "With reference to {reference}, discuss the likely effects of higher production costs on producers and consumers.",
    },
    "market structures": {
        5: "With reference to {reference}, explain one reason why a merger may affect market concentration.",
        8: "Examine two barriers to entry that may affect independent firms in digital games markets.",
        10: "With reference to {reference}, assess whether economies of scale are the main reason for large firms' market power.",
        12: "Discuss whether exclusive content is likely to reduce contestability in this market.",
        15: "With reference to {reference}, discuss the likely benefits and drawbacks of mergers for consumers.",
    },
    "labour market": {
        5: "With reference to {reference}, explain one likely effect of a rise in hourly pay on firms.",
        8: "Examine two factors that might influence the supply of labour in hospitality or care markets.",
        10: "With reference to {reference}, assess whether monopsony power is likely to reduce wage rates.",
        12: "Discuss whether labour shortages are likely to increase wages in low-paid occupations.",
        15: "With reference to {reference}, discuss the likely effects of a higher National Minimum Wage on workers and firms.",
    },
    "revenues, costs and profits": {
        5: "With reference to {reference}, explain one reason why high fixed costs may affect airline pricing.",
        8: "Examine two factors that may influence a firm's profit margins during a period of rising costs.",
        10: "With reference to {reference}, assess whether price discounts are likely to increase total revenue.",
        12: "Discuss whether economies of scale are likely to reduce average costs for growing firms.",
        15: "With reference to {reference}, discuss the likely effects of rising production costs on firms and consumers.",
    },
    "market failure": {
        5: "With reference to {reference}, explain one reason why imperfect information may cause market failure.",
        8: "Examine two external costs that may arise from road transport.",
        10: "With reference to {reference}, assess whether regulation is likely to improve consumer welfare.",
        12: "Discuss whether behavioural biases reduce the effectiveness of competition in this market.",
        15: "With reference to {reference}, discuss the likely effects of government intervention to correct market failure.",
    },
    "government intervention": {
        5: "With reference to {reference}, explain one likely effect of an energy price cap on consumers.",
        8: "Examine two reasons why a tax on sugary drinks may affect producer behaviour.",
        10: "With reference to {reference}, assess whether charges on polluting vehicles are likely to reduce external costs.",
        12: "Discuss whether government intervention is likely to improve welfare in this market.",
        15: "With reference to {reference}, discuss the likely costs and benefits of subsidies for consumers and firms.",
    },
    "business growth": {
        5: "With reference to {reference}, explain one reason why business growth may reduce average costs.",
        8: "Examine two problems a firm may experience when expanding rapidly.",
        10: "With reference to {reference}, assess whether mergers are likely to reduce competition.",
        12: "Discuss whether external growth is more beneficial to firms than organic growth.",
        15: "With reference to {reference}, discuss the likely effects of business growth on consumers and firms.",
    },
    "business objectives": {
        5: "With reference to {reference}, explain one reason why a firm may pursue objectives other than profit maximisation.",
        8: "Examine two possible conflicts between profit and non-profit objectives.",
        10: "With reference to {reference}, assess whether regulation is likely to change business objectives.",
        12: "Discuss whether firms are likely to prioritise sales growth over profit maximisation.",
        15: "With reference to {reference}, discuss the likely effects of firms pursuing objectives other than profit maximisation.",
    },
    "measures of economic performance": {
        5: "With reference to {reference}, explain one reason why CPI inflation may not fully measure changes in living standards.",
        8: "Examine two limitations of using real GDP to compare economic performance.",
        10: "With reference to {reference}, assess whether unemployment data understate weakness in the labour market.",
        12: "Discuss whether GDP per head is the best measure of economic welfare.",
        15: "With reference to {reference}, discuss the usefulness of economic indicators for government policy.",
    },
    "aggregate demand": {
        5: "With reference to {reference}, explain one likely effect of higher interest rates on consumption.",
        8: "Examine two factors that may affect consumer spending during a period of high inflation.",
        10: "With reference to {reference}, assess whether government spending is likely to increase aggregate demand.",
        12: "Discuss whether a fall in consumer confidence is likely to reduce real output.",
        15: "With reference to {reference}, discuss the likely macroeconomic effects of a fall in aggregate demand.",
    },
    "international economics": {
        5: "With reference to {reference}, explain one reason why the UK may run a trade deficit in goods.",
        8: "Examine two factors that may affect the price elasticity of demand for UK exports.",
        10: "With reference to {reference}, assess whether a depreciation is likely to improve the current account.",
        12: "Discuss whether protectionism is likely to improve domestic economic performance.",
        15: "With reference to {reference}, discuss the likely effects of increased trade barriers on an economy.",
    },
    "poverty and inequality": {
        5: "With reference to {reference}, explain one reason why inflation may worsen poverty.",
        8: "Examine two causes of income inequality in an advanced economy.",
        10: "With reference to {reference}, assess whether progressive taxation is likely to reduce inequality.",
        12: "Discuss whether welfare payments improve incentives for low-income households.",
        15: "With reference to {reference}, discuss the likely effects of policies designed to reduce poverty.",
    },
    "emerging and developing economies": {
        5: "With reference to {reference}, explain one reason why extreme poverty may persist in developing economies.",
        8: "Examine two ways foreign direct investment may affect development.",
        10: "With reference to {reference}, assess whether rapid growth is likely to reduce poverty.",
        12: "Discuss whether aid is likely to promote economic development.",
        15: "With reference to {reference}, discuss the likely benefits and drawbacks of foreign direct investment.",
    },
}


def _placeholder_prompt(command_word: str, marks: int, topic_title: str) -> str:
    phrase = _exam_focus(topic_title)
    if command_word == "mcq":
        return f"Which one of the following is correct about {_topic_phrase(topic_title)}?"
    if command_word == "calculate":
        return f"Calculate the change shown in the data for {phrase}. You are advised to show your working."
    if command_word == "draw":
        return f"Draw a diagram to show the likely impact of {phrase}."
    if command_word == "explain":
        return f"Explain one likely effect of {phrase}."
    if command_word == "examine":
        return f"Examine two likely factors affecting {phrase}."
    if command_word == "discuss":
        if marks == 12:
            return f"Discuss whether the evidence supports one interpretation of {phrase}."
        return f"Discuss the likely effects of {phrase}."
    if command_word == "assess":
        return f"Assess whether {phrase} is significant in this context."
    return _essay_question_prompt(topic_title)


def _essay_question_prompt(topic_title: str) -> str:
    topic = topic_title.lower()
    if topic == "demand":
        return "Evaluate the likely microeconomic effects of a significant increase in demand for a product."
    if topic == "supply":
        return "Evaluate the likely microeconomic effects of rising production costs in a market of your choice."
    if topic == "price determination":
        return "Evaluate the likely effects of a change in equilibrium price on consumers and producers."
    if topic == "market failure":
        return "Evaluate whether government intervention is likely to correct market failure."
    if topic == "government intervention":
        return "Evaluate the view that indirect taxation is the most effective way to correct market failure."
    if topic == "government intervention in markets":
        return "Evaluate the likely microeconomic effects of a maximum price in a market of your choice."
    if topic == "business growth":
        return "Evaluate the likely benefits and drawbacks of business growth for firms and consumers."
    if topic == "business objectives":
        return "Evaluate whether profit maximisation is likely to be the most important objective for firms."
    if topic == "revenues, costs and profits":
        return "Evaluate the likely effects of economies of scale on firms and consumers in a market."
    if topic == "market structures":
        return "Evaluate the level of contestability in a market or industry of your choice."
    if topic == "labour market":
        return "Evaluate the likely effects of a significant increase in the National Minimum Wage."
    if topic == "international economics":
        return "Evaluate the likely effects of increased protectionism on an economy."
    if topic == "poverty and inequality":
        return "Evaluate the likely effects of policies designed to reduce income inequality."
    if topic == "emerging and developing economies":
        return "Evaluate the likely effects of rapid economic growth on an emerging economy."
    if topic == "financial sector":
        return "Evaluate the likely effects of financial market failure on an economy."
    if topic == "role of the state in the macroeconomy":
        return "Evaluate the likely macroeconomic effects of increased government intervention."
    return f"Evaluate the likely effects of changes in {topic_title.lower()} on economic agents."


def _build_parts(
    part_marks: list[int],
    part_commands: list[str],
    topic_title: str,
    stimulus_kind: str,
    rng: random.Random,
) -> list[QuestionPart]:
    if not part_marks:
        return []
    return [
        _build_part(chr(97 + part_index), marks, command, topic_title, stimulus_kind, part_index, rng)
        for part_index, (marks, command) in enumerate(zip(part_marks, part_commands, strict=True))
    ]


def _build_part(
    label: str,
    marks: int,
    command: str,
    topic_title: str,
    stimulus_kind: str,
    part_index: int,
    rng: random.Random,
) -> QuestionPart:
    if command == "mcq":
        options = _mcq_options(topic_title, stimulus_kind)
        correct_label = options[0].label
        if len(options) >= 2:
            labels = [opt.label for opt in options]
            rng.shuffle(options)
            for idx, opt in enumerate(options):
                opt.label = labels[idx]
                if idx == 0:
                    correct_label = opt.label
        return QuestionPart(
            label=label,
            marks=marks,
            command_word=command,
            prompt=_mcq_prompt(topic_title, stimulus_kind),
            options=options,
            correct_option=correct_label,
            mark_breakdown="1 mark",
            mark_scheme=[
                f"The only correct answer is {correct_label}",
                *[
                    f"{option.label} is not correct because it does not accurately describe {topic_title.lower()}."
                    for option in options
                    if option.label != correct_label
                ],
            ],
        )
    return QuestionPart(
        label=label,
        marks=marks,
        command_word=command,
        prompt=_part_prompt(command, marks, topic_title, stimulus_kind, part_index),
        mark_breakdown=_part_mark_breakdown(marks, command),
        mark_scheme=_mark_scheme(command, marks, topic_title),
        indicative_content=_indicative_content("", topic_title, []),
    )


def _part_prompt(command: str, marks: int, topic_title: str, stimulus_kind: str, part_index: int) -> str:
    stimulus_prompts = _STIMULUS_PART_PROMPTS.get(stimulus_kind, {})
    return stimulus_prompts.get((part_index, command, marks)) or stimulus_prompts.get((None, command, marks)) or _placeholder_prompt(
        command,
        marks,
        topic_title,
    )


def _mcq_options(topic_title: str, stimulus_kind: str = "") -> list[MultipleChoiceOption]:
    stimulus_options = _STIMULUS_MCQ_OPTIONS.get(stimulus_kind)
    if stimulus_options:
        return [MultipleChoiceOption(label=label, text=text) for label, text in stimulus_options]
    topic = _topic_phrase(topic_title)
    topic_key = topic_title.lower()
    topic_options = _TOPIC_MCQ_OPTIONS.get(topic_key)
    if topic_options:
        return [MultipleChoiceOption(label=label, text=text) for label, text in topic_options]
    sentence_topic = topic[0].upper() + topic[1:]
    return [
        MultipleChoiceOption(label="A", text=f"Changes in {topic} can alter incentives and resource allocation"),
        MultipleChoiceOption(label="B", text=f"{sentence_topic} means economic agents no longer face trade-offs"),
        MultipleChoiceOption(label="C", text=f"{sentence_topic} only affects consumers and never affects firms"),
        MultipleChoiceOption(label="D", text=f"{sentence_topic} always leaves market price unchanged"),
    ]


def _mcq_prompt(topic_title: str, stimulus_kind: str = "") -> str:
    stimulus_prompt = _STIMULUS_MCQ_PROMPTS.get(stimulus_kind)
    if stimulus_prompt:
        return stimulus_prompt
    topic = _normal_topic_key(topic_title)
    prompts = {
        "demand": "Which one of the following is likely to increase demand for a normal good?",
        "supply": "Which one of the following is a likely cause of a decrease in market supply?",
        "rational decision making": "Which one of the following is most likely to influence a rational consumer's choice?",
        "market failure": "Which one of the following is a likely cause of market failure?",
        "government intervention in markets": "Which one of the following is a likely effect of a subsidy?",
        "business objectives": "Which one of the following is a possible business objective?",
        "business growth": "Which one of the following is a possible benefit of internal growth?",
        "market structures": "Which one of the following is a likely source of market power?",
        "labour market": "Which one of the following is likely to affect wage rates in a labour market?",
    }
    return prompts.get(topic, f"Which one of the following is correct about {_topic_phrase(topic_title)}?")


def _stimulus_kind(section, index: int) -> str:
    if not section.stimulus_kinds:
        return ""
    return section.stimulus_kinds[index]


def _group_prompt(
    command_word: str,
    marks: int,
    topic_title: str,
    parts: list[QuestionPart],
) -> str:
    if parts:
        return f"The following data relates to {topic_title.lower()}."
    return _placeholder_prompt(command_word, marks, topic_title)


def _question_prompt(
    paper_id: str,
    section_name: str,
    command_word: str,
    marks: int,
    topic_title: str,
    parts: list[QuestionPart],
    stimulus_kind: str,
    source_reference: str,
) -> str:
    topic = _topic_phrase(topic_title)
    if parts:
        if parts[0].command_word == "draw":
            return _section_a_draw_stem(topic_title)
        return _section_a_stem(topic_title, stimulus_kind)
    if section_name in {"A", "B"} and paper_id == "paper_3":
        return _source_question_prompt(command_word, marks, topic, source_reference)
    if section_name == "B":
        return _source_question_prompt(command_word, marks, topic, source_reference)
    return _placeholder_prompt(command_word, marks, topic_title)


def _section_a_draw_stem(topic_title: str) -> str:
    return f"Read the information below about {_exam_context(topic_title)}."


def _section_a_stem(topic_title: str, stimulus_kind: str) -> str:
    topic = _topic_phrase(topic_title)
    focus = _exam_focus(topic_title)
    if stimulus_kind == "ped_data_table":
        return "The table below shows price elasticity of demand for selected consumer groups."
    if stimulus_kind == "pes_data_table":
        return "The table below shows price elasticity of supply for selected regional markets."
    if stimulus_kind == "market_share_bar_chart":
        return "The graph below shows the largest firms in a UK market by market share."
    if stimulus_kind == "marginal_utility_table":
        return "The table below shows total and marginal utility from consuming a good."
    if stimulus_kind == "opportunity_cost_ppc_table":
        return "The table below shows possible combinations of output for an economy."
    if stimulus_kind == "business_objective_context":
        return "Read the information below about a firm changing its business objectives."
    if stimulus_kind == "xed_context":
        return "Read the information below about cross elasticity of demand for two related goods."
    if stimulus_kind == "imperfect_information_context":
        return "Read the information below about imperfect information in a consumer market."
    if stimulus_kind == "minimum_wage_context":
        return "Read the information below about changes in the National Minimum Wage."
    if stimulus_kind == "household_savings_line_chart":
        return "The chart below shows household saving as a percentage of disposable income."
    if stimulus_kind == "investment_line_chart":
        return "The chart below shows investment as a percentage of GDP over time."
    if stimulus_kind == "financial_market_context":
        return "Read the information below about firms operating in financial markets."
    if stimulus_kind == "development_data_table":
        return "The table below shows selected economic development indicators for two countries."
    if stimulus_kind == "current_account_line_chart":
        return "The chart below shows the current account of the balance of payments as a percentage of GDP."
    if stimulus_kind == "gdp_growth_bar_chart":
        return "The chart below shows real GDP percentage growth over recent quarters."
    if stimulus_kind == "terms_of_trade_index_chart":
        return "The chart below shows a terms of trade index over time."
    if stimulus_kind == "labour_inactivity_context":
        return "Read the information below about the labour force inactivity rate."
    if stimulus_kind == "multiplier_context":
        return "The diagram below shows a trade cycle and information about the multiplier."
    if stimulus_kind == "tariff_context":
        return "Read the information below about a tariff on imported goods."
    if stimulus_kind == "cost_revenue_graph":
        return f"The diagram below shows cost and revenue curves for a firm affected by {focus}."
    if stimulus_kind in {
        "data_table",
        "elasticity_data_table",
        "concentration_ratio_table",
        "shutdown_cost_table",
        "wage_rate_table",
        "contestability_barrier_table",
        "balance_payments_table",
        "inflation_index_table",
        "income_tax_schedule_table",
        "public_spending_pie_table",
    }:
        return f"The table below shows selected economic data linked to {focus}."
    if stimulus_kind in {"market_diagram", "demand_shift_graph", "supply_shift_graph"}:
        return f"The diagram below shows demand and supply in a market affected by {focus}."
    if stimulus_kind in {"tax_subsidy_diagram", "tax_incidence_diagram", "externality_diagram", "minimum_price_diagram", "maximum_price_diagram"}:
        return f"The diagram below shows a possible intervention or market failure linked to {focus}."
    if stimulus_kind in {"consumer_surplus_diagram", "producer_surplus_diagram"}:
        return f"The diagram below shows welfare effects in a market affected by {focus}."
    if stimulus_kind == "perfect_competition_diagram":
        return "The diagram below shows cost and revenue curves for a firm in perfect competition."
    if stimulus_kind == "monopoly_diagram":
        return "The diagram below shows cost and revenue curves for a firm with monopoly power."
    if stimulus_kind == "monopsony_diagram":
        return "The diagram below shows a monopsonist in a labour market."
    if stimulus_kind == "labour_market_diagram":
        return "The diagram below shows demand for and supply of labour in a labour market."
    if stimulus_kind in {"macro_chart", "ad_as_diagram", "keynesian_as_diagram", "trade_cycle", "phillips_curve", "lorenz_curve", "exchange_rate_diagram", "tariff_diagram", "money_market_diagram", "laffer_curve", "poverty_trap_diagram", "production_possibility_frontier"}:
        return f"The diagram below shows an economic relationship linked to {focus}."
    if stimulus_kind == "payoff_matrix":
        return f"The pay-off matrix below shows possible outcomes for firms affected by {focus}."
    if stimulus_kind in {"line_graph", "index_number_chart", "exchange_rate_index_chart"}:
        return f"The line graph below shows changes in data linked to {focus}."
    if stimulus_kind == "unemployment_rate_bar_chart":
        return "The bar chart below shows unemployment rates in selected economies."
    if stimulus_kind == "context_extract":
        return f"Read the information below about {_exam_context(topic_title)}."
    if stimulus_kind == "bar_chart":
        return f"The information below concerns changes in {focus}."
    return f"The information below concerns {topic}."


def _source_question_prompt(command_word: str, marks: int, topic: str, source_reference: str) -> str:
    reference = "the source material" if source_reference == "source material" else source_reference
    topic_prompt = _SECTION_B_PROMPTS.get(_normal_topic_key(topic), {}).get(marks)
    if topic_prompt:
        prompt = topic_prompt.format(reference=reference or "the evidence")
        if reference and not prompt.lower().startswith("with reference"):
            return f"With reference to {reference}, {prompt[:1].lower()}{prompt[1:]}"
        return prompt
    if marks == 5:
        if reference:
            return f"With reference to {reference}, explain one likely effect of {topic}."
        return f"Explain one likely effect of {_exam_focus(topic)}."
    if marks == 8:
        if not reference:
            return f"Examine two likely factors affecting {_exam_focus(topic)}."
        return f"With reference to {reference}, examine two likely factors affecting {topic}."
    if marks == 10:
        if not reference:
            return f"Assess whether {_exam_focus(topic)} is significant in this context."
        return f"With reference to {reference}, assess whether {topic} is significant in this context."
    if marks == 12:
        if not reference:
            return f"Discuss whether the evidence supports one interpretation of {_exam_focus(topic)}."
        return f"With reference to {reference}, discuss whether the evidence supports one interpretation of {topic}."
    if marks == 15:
        prompt = _section_b_15_marker_prompt(topic)
        if reference:
            return f"With reference to {reference}, {prompt[:1].lower()}{prompt[1:]}"
        return prompt
    return f"Evaluate the view that {topic} is the most important issue in this market."


def _section_b_15_marker_prompt(topic: str) -> str:
    title = topic.lower()
    if title == "market structures":
        return "Discuss the likely benefits of mergers for firms in this market."
    if title == "labour market":
        return "Discuss the likely effects of changes in the National Minimum Wage on workers and firms."
    if title == "market failure":
        return "Discuss the likely effects of government intervention in this market."
    return f"Discuss the likely effects of {topic} on firms and consumers."


def _source_reference(paper_id: str, section_name: str, index: int) -> str:
    if section_name == "A" and paper_id in {"paper_1", "paper_2"}:
        return "Figure 1"
    if section_name == "B" and paper_id in {"paper_1", "paper_2"}:
        return ["Extract A", "", "", "Extract C", "Extract D"][index]
    if paper_id == "paper_3":
        return ["Extract A", "Extract A", "Extract B", "Extract C", "source material"][index]
    return ""


def _source_title(topic_title: str, section_name: str) -> str:
    return f"{topic_title}: economic context" if section_name in {"B", "A"} else topic_title


def _source_text(
    topic_id: str,
    topic_title: str,
    points: list[str],
    section_name: str,
    index: int,
    stimulus_kind: str,
) -> str:
    focus = ", ".join(points[:3]) if points else _topic_phrase(topic_title)
    if section_name == "C":
        return _section_c_extract(topic_id, topic_title, points, index)
    if section_name == "B":
        extract_index = [0, 1, 2, 2, 3][min(index, 4)]
        return _data_response_extract(topic_title, points, extract_index)
    if section_name == "A":
        return _section_a_context(topic_id, topic_title, focus, points, stimulus_kind)
    if stimulus_kind == "data_table":
        return (
            f"The table shows how indicators linked to {topic_title.lower()} changed over time. "
            f"The data may be used to analyse {focus} and to support short-run and long-run judgements."
        )
    return (
        f"The evidence on {topic_title.lower()} suggests changes in {focus}. Firms, consumers and policy makers "
        f"may respond differently depending on incentives, market conditions and the time period considered."
    )


def _data_response_extract(topic_title: str, points: list[str], index: int) -> str:
    return data_response_extract(topic_title, points, index)


def _section_c_extract(topic_id: str, topic_title: str, points: list[str], index: int) -> str:
    return section_c_extract(topic_title, points, index)


def _section_a_context(
    topic_id: str,
    topic_title: str,
    focus: str,
    points: list[str],
    stimulus_kind: str = "",
) -> str:
    stimulus_contexts = {
        "ped_data_table": "The data compares responsiveness to a price change for two groups of consumers using the same service.",
        "pes_data_table": "The data compares how quickly producers in two regional markets can respond to changes in price.",
        "market_share_bar_chart": "The figures show market shares for the largest firms in an industry where brand recognition and scale may matter.",
        "marginal_utility_table": "A consumer records the additional satisfaction gained from each extra unit consumed during a week.",
        "opportunity_cost_ppc_table": "An economy can switch resources between consumer goods and capital goods, but each change has an opportunity cost.",
        "business_objective_context": "A firm selling a consumer product is considering whether to prioritise revenue growth rather than maximum profit.",
        "xed_context": "The cross elasticity of demand for one good with respect to the price of a related good is positive.",
        "imperfect_information_context": "A regulator received complaints from consumers who could not accurately judge product quality before purchase.",
        "minimum_wage_context": "The statutory minimum wage increased, raising hourly pay for low-paid workers and changing firms' labour costs.",
        "household_savings_line_chart": "Households changed their saving behaviour during a period of uncertainty about future income and prices.",
        "investment_line_chart": "Investment changed as firms responded to weaker confidence, higher costs and expectations about future demand.",
        "financial_market_context": "Several banks were fined after traders shared information that could distort prices in a foreign exchange market.",
        "development_data_table": "The data can be used to compare living standards and economic development in two emerging economies.",
        "current_account_line_chart": "The balance changed as export revenue, import spending and exchange rates altered over time.",
        "gdp_growth_bar_chart": "Quarterly real GDP growth varied as consumption, investment and government spending changed.",
        "terms_of_trade_index_chart": "The index compares average export prices with average import prices, using a base year of 100.",
        "labour_inactivity_context": "A higher share of working-age people were neither in work nor actively seeking employment.",
        "multiplier_context": "A survey estimates the marginal propensity to consume after households receive extra income.",
        "tariff_context": "A government imposed an import tariff to protect domestic producers from overseas competition.",
        "shutdown_cost_table": "A firm compares price, average revenue and average variable cost when deciding whether to continue production in the short run.",
        "wage_rate_table": "Average hourly pay changed in an occupation where vacancies and training requirements affected labour supply.",
        "contestability_barrier_table": "A regulator is examining sunk costs, brand loyalty and switching costs in a concentrated market.",
        "exchange_rate_index_chart": "Sterling appreciated against a basket of currencies, changing export prices and import costs.",
        "income_tax_schedule_table": "The income tax schedule shows how marginal rates rise as taxable income increases.",
        "public_spending_pie_table": "Government spending priorities changed, creating trade-offs between health, education and debt interest.",
        "unemployment_rate_bar_chart": "Unemployment rates differ between economies due to changes in growth, skills and labour mobility.",
    }
    if stimulus_kind in stimulus_contexts:
        return stimulus_contexts[stimulus_kind]
    topic = topic_title.lower()
    if topic == "labour market":
        return (
            "The National Minimum Wage increased for workers aged 21 and over. Some firms report higher wage costs, "
            "while others say vacancies remain difficult to fill."
        )
    if topic == "market failure":
        return (
            "A market creates external costs for third parties. Policy makers are considering whether output is above "
            "the socially efficient level."
        )
    if topic.startswith("government intervention"):
        return (
            "The government is considering a new policy to influence market outcomes. The policy may affect prices, "
            "output, consumer surplus and producer incentives."
        )
    note_points = note_points_for_topic(topic_id, title=topic_title, keywords=points, limit=8) if topic_id else []
    context_point = _best_section_a_context_point(note_points)
    if context_point:
        return (
            f"A market report on {_topic_phrase(topic_title)} states: {context_point} "
            f"The evidence can be used to analyse {focus}."
        )
    return (
        f"A market report on {_topic_phrase(topic_title)} includes evidence on {focus}. The information can be used "
        "to consider incentives, opportunity cost and likely market outcomes."
    )


def _best_section_a_context_point(note_points: list[str]) -> str:
    weak_endings = {
        "a",
        "and",
        "after",
        "from",
        "in",
        "new",
        "of",
        "or",
        "that",
        "the",
        "to",
        "where",
        "which",
        "who",
        "with",
        "word",
    }
    for point in note_points:
        cleaned = point.lstrip("●•-– ").strip()
        if not cleaned or cleaned[0].islower() or cleaned.startswith("("):
            continue
        if cleaned.endswith(":") or cleaned[0].isdigit():
            continue
        candidate = _first_sentence(cleaned)
        if candidate.rstrip(".").endswith(","):
            continue
        if candidate.rstrip(".").split()[-1].lower() in weak_endings:
            continue
        return _sentence(candidate)
    return ""


def _first_sentence(text: str) -> str:
    for delimiter in [". ", "? ", "! "]:
        if delimiter in text:
            return text.split(delimiter, 1)[0] + delimiter[0]
    return text


def _sentence(text: str) -> str:
    cleaned = text.strip()
    return cleaned if cleaned.endswith((".", "?", "!")) else f"{cleaned}."


def _topic_phrase(topic_title: str) -> str:
    topic = topic_title.lower()
    if topic in {"labour market", "financial sector"}:
        return f"the {topic}"
    if topic == "role of the state in the macroeconomy":
        return "the role of the state in the macroeconomy"
    return topic


def _normal_topic_key(topic_title: str) -> str:
    topic = topic_title.lower().strip()
    return topic[4:] if topic.startswith("the ") else topic


def _exam_focus(topic_title: str) -> str:
    topic = _normal_topic_key(topic_title)
    return _EXAM_FOCUS.get(topic, _topic_phrase(topic_title))


def _exam_context(topic_title: str) -> str:
    topic = _normal_topic_key(topic_title)
    return _EXAM_CONTEXT.get(topic, f"a market affected by {_exam_focus(topic_title)}")


def _mark_breakdown(marks: int, parts: list[QuestionPart]) -> str:
    if parts:
        return "Knowledge 2, Application 2"
    return _part_mark_breakdown(marks, "")


def _part_mark_breakdown(marks: int, command_word: str) -> str:
    if marks == 1:
        return "1 mark"
    if marks == 4:
        return "Knowledge 2, Application 2"
    if marks == 5:
        return "Knowledge 1, Application 2, Analysis 2"
    if marks == 8:
        return "Knowledge 2, Application 2, Analysis 4"
    if marks == 10:
        return "Knowledge 2, Application 2, Analysis 3, Evaluation 3"
    if marks == 12:
        return "Knowledge 2, Application 2, Analysis 4, Evaluation 4"
    if marks == 15:
        return "Knowledge 3, Application 3, Analysis 4, Evaluation 5"
    if marks == 25:
        return "Knowledge 4, Application 4, Analysis 8, Evaluation 9"
    return f"{marks} marks"


def _mark_scheme(command_word: str, marks: int, topic_title: str) -> list[str]:
    topic = topic_title.lower()
    if marks == 1:
        return ["Award 1 mark for the correct answer."]
    if marks <= 5:
        return [
            f"Knowledge/Understanding: accurate identification or definition linked to {topic}.",
            f"Application: relevant use of the data, figure, extract or example for {topic}.",
            "Analysis: clear chain of reasoning showing cause and effect.",
        ]
    return [
        "Indicative content should be rewarded where it is relevant and developed.",
        f"Knowledge and understanding of {topic}.",
        "Application to the source material or a relevant economic example.",
        "Analysis using logical chains of reasoning.",
        "Evaluation supported by judgement where required by the command word.",
    ]


def _indicative_content(topic_id: str, topic_title: str, points: list[str]) -> list[str]:
    note_points = note_points_for_topic(topic_id, title=topic_title, keywords=points, limit=4) if topic_id else []
    content = [*note_points, *points[:4]]
    unique_content = []
    for item in content:
        if item not in unique_content:
            unique_content.append(item)
    content = unique_content[:6]
    return content or [
        f"Definition and core features of {topic_title.lower()}",
        "Relevant source evidence",
        "Likely short-run and long-run effects",
        "Supported judgement",
    ]
