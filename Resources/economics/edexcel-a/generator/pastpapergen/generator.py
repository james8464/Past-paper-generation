from __future__ import annotations

import math
import random
import re

from pastpapergen.models import (
    MultipleChoiceOption,
    PaperBlueprint,
    PaperConfig,
    QuestionBlueprint,
    QuestionPart,
    Syllabus,
    SyllabusTopic,
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
    paper_3_contexts = _paper_3_context_plan(config.id, rng)
    paper_3_source_variants = {
        section: rng.randrange(10_000, 1_000_000)
        for section in paper_3_contexts
    }

    questions: list[QuestionBlueprint] = []
    absolute_question_number = 1
    for section in config.sections:
        choice_lookup = _choice_lookup(section.choice_groups)
        choice_group_topics: dict[int, set[str]] = {}
        section_topic_ids: set[str] = set()
        section_stimulus_kinds: set[str] = set()
        section_templates = _section_templates(section, rng)
        section_theme_targets = theme_plan.get(section.name, [])
        case_title = paper_3_contexts.get(section.name, "")
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
            if case_title:
                planned_topic_id = _PAPER_3_TOPIC_PLANS[case_title][index]
                planned_topics = [topic for topic in topics if topic.id == planned_topic_id]
                if planned_topics:
                    available_topics = planned_topics
            stimulus_kind = _compatible_stimulus_kind(
                _stimulus_pool(section, index),
                part_commands,
                available_topics,
                excluded_ids,
                stimulus_kind,
                rng,
                section_stimulus_kinds,
            )
            available_topics = _topics_suitable_for_template(available_topics, part_commands, stimulus_kind)
            topic = source_context_topic or _choose_topic(rng, available_topics, excluded_ids) or SyllabusTopic(id="unknown", theme=1, title="Economics", points=[])
            stimulus_kind = _specialize_stimulus_kind(stimulus_kind, topic.id)
            section_stimulus_kinds.add(stimulus_kind)
            command_word = section.command_words[index]
            number = _question_number(config.id, section.name, absolute_question_number, index)
            parts = _build_parts(
                part_marks,
                part_commands,
                topic,
                stimulus_kind,
                rng,
            )
            source_reference = _source_reference(
                config.id, section.name, index, stimulus_kind
            )
            question_mark_scheme, question_indicative_content = _question_guidance(
                config.id,
                marks,
                command_word,
                topic,
                case_title,
                source_reference,
            )
            question_mark_scheme = _complete_extended_guidance(
                question_mark_scheme, marks, command_word
            )
            question_indicative_content = _complete_extended_guidance(
                question_indicative_content, marks, command_word
            )
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
                        case_title,
                    ),
                    parts=parts,
                    stimulus_kind=stimulus_kind,
                    choice_group=_choice_group_name(config.id, section.name, group_index),
                    source_reference=source_reference,
                    source_title=case_title or _source_title(topic.title, section.name),
                    source_text=_source_text(
                        topic.id,
                        topic.title,
                        topic.points,
                        section.name,
                        index,
                        stimulus_kind,
                        paper_id=config.id,
                        case_title=case_title,
                        source_variant=paper_3_source_variants.get(section.name, 0),
                        source_reference=source_reference,
                    ),
                    mark_breakdown=_mark_breakdown(marks, parts, stimulus_kind),
                    mark_scheme=(
                        [
                            point
                            for part in parts
                            for point in part.mark_scheme
                            if point.strip()
                        ]
                        if parts
                        else question_mark_scheme
                    ),
                    indicative_content=(
                        [
                            point
                            for part in parts
                            for point in (part.indicative_content or part.mark_scheme)
                            if point.strip()
                        ]
                        if parts
                        else question_indicative_content
                    ),
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


def _complete_extended_guidance(
    points: list[str],
    marks: int,
    command_word: str,
) -> list[str]:
    """Add standardisation metadata omitted by a bespoke indicative scheme."""

    if marks < 8 or command_word.casefold() not in {
        "analyse",
        "analyze",
        "assess",
        "advise",
        "discuss",
        "evaluate",
        "justify",
    }:
        return points

    completed = list(points)
    combined = " ".join(points).casefold()
    additions: list[str] = []
    if not any(term in combined for term in ("level 1", "level 2", "best fit")):
        top_floor = max(2, math.ceil(marks * 0.75))
        middle_floor = max(2, math.ceil(marks * 0.4))
        additions.append(
            "Levels-based best fit: "
            f"Level 3 ({top_floor}–{marks}) precise, sustained and supported; "
            f"Level 2 ({middle_floor}–{top_floor - 1}) accurate with some development but uneven judgement; "
            f"Level 1 (1–{middle_floor - 1}) isolated or limited; Level 0 (0) no rewardable material."
        )
    if not re.search(
        r"\baccept\b.*\b(?:equivalent|alternative|valid)\b|\bvalid route\b|\bequivalent valid\b",
        combined,
    ):
        additions.append("Accept an equivalent valid contextual analytical route.")
    if not any(
        term in combined
        for term in ("do not", "reject", "no credit", "not award", "only award")
    ):
        additions.append(
            "Do not award duplicate developed points or top-level credit without context."
        )
    if additions:
        completed.append(" ".join(additions))
    return completed


def _choose_topic(rng: random.Random, topics, excluded_ids: set[str]):
    available = [topic for topic in topics if topic.id not in excluded_ids]
    if not available and not topics:
        return None
    pool = available or topics
    return rng.choice(pool)


def _specialize_stimulus_kind(stimulus_kind: str, topic_id: str) -> str:
    if topic_id == "3.3" and stimulus_kind in {"data_table", "line_graph"}:
        return "shutdown_cost_table"
    if topic_id == "4.2" and stimulus_kind == "line_graph":
        return "inequality_line_chart"
    if topic_id == "4.5" and stimulus_kind == "context_extract":
        return "state_policy_context"
    if stimulus_kind != "data_table":
        return stimulus_kind
    return {
        "1.2.2": "ped_data_table",
        "1.2.3": "pes_data_table",
    }.get(topic_id, stimulus_kind)


def _theme_plan(config: PaperConfig, rng: random.Random) -> dict[str, list[int]]:
    if config.id == "paper_3":
        plan: dict[str, list[int]] = {}
        for section in ("A", "B"):
            themes = [1, 2, 3, 4]
            rng.shuffle(themes)
            plan[section] = [*themes, rng.choice(themes)]
        return plan
    if config.id not in {"paper_1", "paper_2"}:
        return {}
    themes = sorted(config.allowed_themes)
    if not themes:
        return {}
    data_response_theme = rng.choice(themes)
    remaining = [t for t in themes if t != data_response_theme]
    essay_theme = remaining[0] if remaining else data_response_theme
    section_a_themes = [data_response_theme, data_response_theme, essay_theme, essay_theme, essay_theme]
    rng.shuffle(section_a_themes)
    return {
        "A": section_a_themes,
        "B": [data_response_theme] * 5,
        "C": [essay_theme] * 2,
    }


_PAPER_3_CONTEXTS = (
    "The energy and utilities market",
    "Housing and construction",
    "Food production and retail",
    "Digital platforms and communications",
    "Transport and aviation",
    "Healthcare and pharmaceuticals",
    "Electric vehicles and battery production",
    "Tourism and hospitality",
)

_PAPER_3_TOPIC_PLANS = {
    "The energy and utilities market": ("1.2.3", "3.1", "1.3", "2.3", "4.5"),
    "Housing and construction": ("1.2.3", "3.3", "1.4", "2.2", "4.2"),
    "Food production and retail": ("1.2.2", "3.4", "1.4", "2.1", "4.1"),
    "Digital platforms and communications": ("1.2.2", "3.4", "1.3", "2.5", "4.4"),
    "Transport and aviation": ("1.2.2", "3.3", "1.3", "2.3", "4.1"),
    "Healthcare and pharmaceuticals": ("1.3", "3.5", "1.4", "2.3", "4.5"),
    "Electric vehicles and battery production": ("1.2.3", "3.1", "1.3", "2.5", "4.1"),
    "Tourism and hospitality": ("1.2.2", "3.5", "1.4", "2.2", "4.1"),
}


def _paper_3_context_plan(paper_id: str, rng: random.Random) -> dict[str, str]:
    if paper_id != "paper_3":
        return {}
    section_a, section_b = rng.sample(_PAPER_3_CONTEXTS, 2)
    return {"A": section_a, "B": section_b}


def _topics_for_theme(topics, theme: int):
    matched = [topic for topic in topics if topic.theme == theme]
    return matched or topics


def _section_templates(section, rng: random.Random) -> list[tuple[list[int], list[str], str]]:
    if not section.part_marks:
        return []
    templates = list(zip(section.part_marks, section.part_command_words, strict=True))
    stimulus_kinds = [
        rng.choice(_stimulus_pool(section, index)) if _stimulus_pool(section, index) else ""
        for index in range(len(templates))
    ]
    return [
        (list(part_marks), list(part_commands), stimulus_kinds[index])
        for index, (part_marks, part_commands) in enumerate(templates)
    ]


def _stimulus_pool(section, index: int) -> list[str]:
    if index < len(section.stimulus_slots) and section.stimulus_slots[index]:
        return section.stimulus_slots[index]
    return section.stimulus_kinds


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
    excluded_kinds: set[str] | None = None,
) -> str:
    if not stimulus_kinds:
        return preferred_kind
    candidates = [preferred_kind, *rng.sample(stimulus_kinds, len(stimulus_kinds))]
    excluded_kinds = excluded_kinds or set()
    seen: set[str] = set()
    for kind in candidates:
        if kind in seen:
            continue
        seen.add(kind)
        if kind in excluded_kinds:
            continue
        if not _stimulus_matches_commands(kind, part_commands):
            continue
        suitable_ids = _STIMULUS_TOPIC_IDS.get(kind)
        if suitable_ids and not any(topic.id in suitable_ids and topic.id not in excluded_ids for topic in topics):
            continue
        if not suitable_ids and not any(topic.id not in excluded_ids for topic in topics):
            continue
        return kind
    command_compatible = [
        kind
        for kind in stimulus_kinds
        if kind not in excluded_kinds
        and _stimulus_matches_commands(kind, part_commands)
        and (
            not _STIMULUS_TOPIC_IDS.get(kind)
            or any(topic.id in _STIMULUS_TOPIC_IDS[kind] for topic in topics)
        )
    ]
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


_STIMULUS_TOPIC_IDS = {
    "ped_data_table": {"1.2.2"},
    "pes_data_table": {"1.2.3"},
    "market_share_bar_chart": {"3.4"},
    "marginal_utility_table": {"1.1"},
    "opportunity_cost_ppc_table": {"1.1"},
    "business_objective_context": {"3.2"},
    "state_policy_context": {"4.5"},
    "xed_context": {"1.2.2"},
    "imperfect_information_context": {"1.3"},
    "minimum_wage_context": {"3.5"},
    "household_savings_line_chart": {"2.1", "2.2"},
    "investment_line_chart": {"2.2"},
    "financial_market_context": {"4.4"},
    "development_data_table": {"2.1", "4.2", "4.3"},
    "current_account_line_chart": {"4.1", "2.6"},
    "inequality_line_chart": {"4.2"},
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
        (None, "explain", 4): "Using the age-group coefficients above, explain why demand from 16–18-year-old consumers may be more price responsive than demand from adults.",
        (None, "calculate", 4): "Calculate the likely percentage change in quantity demanded following the price change. You are advised to show your working.",
    },
    "pes_data_table": {
        (None, "explain", 4): "Using the regional coefficients above, explain why rural producers may be more able to expand supply after a price rise than urban producers.",
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
        (None, "draw", 4): "For an imperfectly competitive firm facing a downward-sloping AR curve, draw and label a cost and revenue diagram showing the distinct profit-maximising and revenue-maximising output levels.",
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
    "state_policy_context": {
        (None, "explain", 4): "With reference to the information above, explain one likely effect of the increase in preventive healthcare spending on the economy's productive capacity.",
    },
    "trade_cycle": {
        (None, "explain", 4): "With reference to Figure 1, explain one likely effect of a movement from the trough into recovery on cyclical unemployment.",
    },
    "development_data_table": {
        (None, "calculate", 2): "Using the data provided, calculate the difference in HDI between Morocco and Pakistan. You are advised to show your working.",
        (None, "calculate", 4): "Using the data provided, calculate the difference in GDP per capita between Morocco and Pakistan. You are advised to show your working.",
        (None, "explain", 4): "With reference to the data provided, explain one limitation of using GDP to compare living standards between countries.",
    },
    "current_account_line_chart": {
        (None, "calculate", 2): "Using the Year 1 and Year 10 values, calculate the increase in the size of the current account deficit, in percentage points. Treat the deficit size as its distance below zero (for example, −3.8% has a deficit size of 3.8%). Show your working.",
        (2, "explain", 2): "Explain one likely reason why the current account deficit was wider in Year 10 than in Year 1.",
        (None, "explain", 4): "With reference to the chart above, explain one likely reason for the change in the current account balance.",
    },
    "inequality_line_chart": {
        (None, "calculate", 2): "Using Figure 1, calculate the fall in the Gini coefficient from Year 1 to Year 5. Show your working.",
        (None, "calculate", 4): "Using Figure 1, calculate the percentage fall in the Gini coefficient from Year 1 to Year 5. Show your working and give your answer to one decimal place.",
        (None, "explain", 4): "With reference to Figure 1, explain one likely effect on living standards of the fall in the Gini coefficient from 0.42 to 0.33.",
    },
    "gdp_growth_bar_chart": {
        (None, "calculate", 2): "Calculate the percentage point change in GDP growth over the period shown. You are advised to show your working.",
        (1, "explain", 2): "Explain one likely disadvantage of a decline in GDP for workers.",
        (2, "explain", 2): "Explain one likely disadvantage of a decline in GDP for the government.",
    },
    "terms_of_trade_index_chart": {
        (None, "calculate", 2): "Calculate the percentage change in the terms of trade index over the period shown. You are advised to show your working.",
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
        (None, "explain", 4): "With reference to the information above, explain the likely effect of the tariff on the UK price of imported solar panels and on domestic panel output.",
    },
    "exchange_rate_index_chart": {
        (None, "calculate", 2): "Calculate the percentage change in the exchange rate index over the period shown. You are advised to show your working.",
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
        (None, "calculate", 2): "Calculate the percentage point change in unemployment over the period shown. You are advised to show your working.",
        (None, "explain", 4): "With reference to the chart above, explain one likely macroeconomic effect of rising unemployment.",
    },
    "macro_chart": {
        (None, "calculate", 2): "Calculate the percentage point change between the first and final observations shown. You are advised to show your working.",
    },
    "line_graph": {
        (None, "calculate", 2): "Calculate the percentage point change between the first and final observations shown. You are advised to show your working.",
    },
}


_STIMULUS_MCQ_PROMPTS = {
    "ped_data_table": "Which one of the following statements is correct? Refer to the table above.",
    "pes_data_table": "Using the rural market PES, which one of the following is the percentage increase in price if quantity supplied rises by 3.6%?",
    "market_share_bar_chart": "Which one of the following is the value of the largest firm's market share?",
    "marginal_utility_table": "Which one of the following is most likely to be correct? Refer to the table above.",
    "opportunity_cost_ppc_table": "Which one of the following is the opportunity cost of increasing capital goods output from 20 to 40 units? Refer to the table above.",
    "cost_revenue_graph": "For the imperfectly competitive firm in the previous diagram, which one of the following occurs when demand falls and its demand curve shifts downwards?",
    "business_objective_context": "Which one of the following is most likely to occur if the firm changes to sales maximisation?",
    "xed_context": "Which one of the following is the most likely impact if the price of the substitute falls?",
    "imperfect_information_context": "Which one of the following is the most likely explanation of this behaviour?",
    "minimum_wage_context": "Which one of the following is the most likely cause of a decrease in the supply of workers?",
    "household_savings_line_chart": "With reference to the chart above, which one of the following is correct?",
    "investment_line_chart": "Which one of the following is the percentage point fall in investment between the two dates shown?",
    "financial_market_context": "Which one of the following is a role of financial markets?",
    "state_policy_context": "Which one of the following is the opportunity cost of the additional healthcare spending?",
    "trade_cycle": "With reference to Figure 1, which one of the following is most likely during the recovery phase?",
    "development_data_table": "Which one of the following is correct? Refer to the table above.",
    "current_account_line_chart": "With reference to the chart above, which one of the following is correct?",
    "inequality_line_chart": "With reference to Figure 1, which one of the following is correct?",
    "gdp_growth_bar_chart": "With reference to the chart above, which one of the following is correct?",
    "terms_of_trade_index_chart": "Which one of the following is the percentage change in the terms of trade?",
    "labour_inactivity_context": "Which one of the following would be the most likely result of an increase in labour force inactivity?",
    "multiplier_context": "Which one of the following points on the trade cycle diagram above illustrates a boom?",
    "tariff_context": "Which one of the following is most likely after the tariff is imposed?",
    "shutdown_cost_table": "Which one of the following is most likely to be correct? Refer to the table above.",
    "wage_rate_table": "Which one of the following is the percentage change in hourly wages? Refer to the table above.",
    "contestability_barrier_table": "Which one of the following is most likely to increase contestability? Refer to the table above.",
    "exchange_rate_index_chart": "With reference to the chart above, which one of the following is most likely after an appreciation of sterling?",
    "income_tax_schedule_table": "Which one of the following describes a progressive tax system? Refer to the table above.",
    "public_spending_pie_table": "Which one of the following is an opportunity cost of increased health spending? Refer to the table above.",
    "unemployment_rate_bar_chart": "With reference to the chart above, which one of the following is a likely effect of rising unemployment?",
}


_STIMULUS_MCQ_OPTIONS = {
    "ped_data_table": [
        ("A", "The 16–18 group has more price elastic demand because |−0.7| > |−0.4|"),
        ("B", "Both age groups have unit price elasticity of demand"),
        ("C", "Both age groups have perfectly price-inelastic demand"),
        ("D", "The adult group is more responsive to price changes than the 16–18 group"),
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
        ("A", "The AR and MR curves both shift downwards"),
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
    "state_policy_context": [
        ("A", "The next-best public programme that cannot now be funded"),
        ("B", "The full £12 billion healthcare budget"),
        ("C", "Every benefit received by patients"),
        ("D", "The tax revenue collected to finance the policy"),
    ],
    "trade_cycle": [
        ("A", "Real GDP rises and cyclical unemployment is likely to fall"),
        ("B", "Real GDP falls and cyclical unemployment is likely to rise"),
        ("C", "The economy must remain permanently at the trough"),
        ("D", "The recovery phase eliminates every form of unemployment"),
    ],
    "current_account_line_chart": [
        ("A", "The current account was in deficit in every year shown"),
        ("B", "The current account was in surplus in the final year shown"),
        ("C", "The current account deficit widened in every year shown"),
        ("D", "The current account balance was positive in every year shown"),
    ],
    "inequality_line_chart": [
        ("A", "The Gini coefficient fell by 0.09 over the period shown"),
        ("B", "The Gini coefficient rose by 0.09 over the period shown"),
        ("C", "The Gini coefficient remained at 0.42"),
        ("D", "The chart proves that absolute poverty was eliminated"),
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
        ("A", "UK panel prices rise and imports are likely to fall"),
        ("B", "UK panel prices fall by the full value of the tariff"),
        ("C", "Domestic panel output must fall to zero"),
        ("D", "The tariff removes every opportunity cost from production"),
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
        ("C", "A utility-maximising consumer buys every unit they can afford regardless of marginal benefit"),
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
        8: "With reference to {reference}, examine two possible conflicts between profit and non-profit objectives.",
        10: "With reference to {reference}, assess whether regulation is likely to change business objectives.",
        12: "With reference to {reference}, discuss whether regulated water companies should prioritise profit maximisation over service quality and environmental objectives.",
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
    "macroeconomic objectives and policies": {
        5: "With reference to {reference}, explain one likely effect of the higher Bank Rate on inflation.",
        8: "With reference to {reference}, examine two reasons why expansionary fiscal policy may create conflicts between macroeconomic objectives.",
        10: "With reference to {reference}, assess whether supply-side policies can reduce conflicts between economic growth, inflation and unemployment.",
        12: "With reference to {reference}, discuss the likely effectiveness of training, childcare and infrastructure policies in improving growth without increasing inflation.",
        15: "With reference to {reference}, discuss the likely effects of tighter anti-inflation policy on firms and consumers.",
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
        return "Evaluate the likely effects of a change in equilibrium price on consumer and producer surplus."
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
    topic: SyllabusTopic,
    stimulus_kind: str,
    rng: random.Random,
) -> list[QuestionPart]:
    if not part_marks:
        return []
    return [
        _build_part(
            chr(97 + part_index),
            marks,
            command,
            topic,
            stimulus_kind,
            part_index,
            rng,
        )
        for part_index, (marks, command) in enumerate(zip(part_marks, part_commands, strict=True))
    ]


def _build_part(
    label: str,
    marks: int,
    command: str,
    topic: SyllabusTopic,
    stimulus_kind: str,
    part_index: int,
    rng: random.Random,
) -> QuestionPart:
    topic_title = topic.title
    if command == "mcq":
        options = _mcq_options(topic_title, stimulus_kind)
        correct_text = options[0].text
        if len(options) >= 2:
            labels = [opt.label for opt in options]
            rng.shuffle(options)
            for idx, opt in enumerate(options):
                opt.label = labels[idx]
        correct_label = next(
            option.label for option in options if option.text == correct_text
        )
        return QuestionPart(
            label=label,
            marks=marks,
            command_word=command,
            prompt=_mcq_prompt(topic_title, stimulus_kind),
            options=options,
            correct_option=correct_label,
            mark_breakdown="1 mark",
            mark_scheme=[
                f"The only correct answer is {correct_label}: "
                + next(
                    option.text
                    for option in options
                    if option.label == correct_label
                ),
                "Do not award a mark for any other option.",
            ],
        )
    mark_scheme, indicative_content = _part_guidance(
        command,
        marks,
        topic,
        stimulus_kind,
        part_index,
    )
    mark_breakdown = (
        "AO1 1, AO2 1, AO3 2"
        if (
            stimulus_kind
            in {
                "ped_data_table",
                "pes_data_table",
                "inequality_line_chart",
                "state_policy_context",
                "trade_cycle",
                "tariff_context",
            }
            or (stimulus_kind == "context_extract" and topic.id == "1.2.1")
            or stimulus_kind == "shutdown_cost_table"
        )
        and command == "explain"
        and marks == 4
        else _part_mark_breakdown(marks, command)
    )
    return QuestionPart(
        label=label,
        marks=marks,
        command_word=command,
        prompt=_part_prompt(command, marks, topic_title, stimulus_kind, part_index),
        mark_breakdown=mark_breakdown,
        mark_scheme=mark_scheme,
        indicative_content=indicative_content,
    )


def _part_guidance(
    command: str,
    marks: int,
    topic: SyllabusTopic,
    stimulus_kind: str,
    part_index: int,
) -> tuple[list[str], list[str]]:
    if stimulus_kind == "ped_data_table" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Defines price elasticity of demand as the responsiveness of quantity demanded to a change in price.",
            "AO2 (1 mark): Uses the table difference: PED is -0.7 for the younger group and -0.4 for adults.",
            "AO3 (1 mark): Explains one relevant reason, such as younger consumers having more close substitutes or spending a larger share of income on the product. Accept any other valid determinant of PED applied to the 16–18 group.",
            "AO3 (1 mark): Links that reason to a larger proportional response in quantity demanded and therefore |−0.7| > |−0.4|. Accept 'greater' or 'higher' when it clearly refers to absolute PED magnitude, and accept any clear causal link to greater responsiveness; the exact phrase 'proportional response' is not required.",
        ]
        return points, points
    if stimulus_kind == "pes_data_table" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Defines price elasticity of supply as the responsiveness of quantity supplied to a change in price.",
            "AO2 (1 mark): Uses one relevant difference from the table and source, such as urban PES of 0.5 with limited spare capacity, contracts or delayed input access.",
            "AO3 (1 mark): Explains how the chosen constraint prevents or delays producers increasing output after a price rise.",
            "AO3 (1 mark): Links the smaller proportional output response to the lower PES shown for the urban market.",
        ]
        return points, points
    if stimulus_kind == "current_account_line_chart":
        if command == "calculate" and marks == 2:
            points = [
                "1 mark for method: correctly find the difference between the absolute values of Year 10 and Year 1, for example |−4.3| − |−3.8| = 4.3 − 3.8.",
                "1 mark for an increase in deficit size of 0.5 percentage points. The final answer must state a positive size/widening of 0.5.",
            ]
            return points, points
        if command == "explain" and marks == 2 and part_index == 2:
            points = [
                "1 mark for identifying one valid factor or proximate change from the source: higher domestic income/stronger import spending, lower overseas demand/weaker export revenue, or weaker non-price competitiveness. Only one route is required.",
                "1 development mark for completing the chosen chain: higher domestic income raises imports; lower overseas demand reduces exports; or weaker non-price competitiveness makes foreign consumers buy fewer exports and/or domestic consumers buy more imports. As net exports (X − M) fall, the current account balance becomes more negative. A named factor without this link receives only the first mark.",
            ]
            return points, points
    if stimulus_kind == "inequality_line_chart" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): States that a lower Gini coefficient indicates a more equal distribution of income, with 0 representing complete equality and 1 complete inequality.",
            "AO2 (1 mark): Uses Figure 1 to identify that the Gini coefficient fell from 0.42 to 0.33, a decrease of 0.09.",
            "AO3 (1 mark): Explains that, if the fall reflects higher disposable incomes for lower-income households, their ability to afford essential goods and services may increase.",
            "AO3 (1 mark): Develops the chain to a likely improvement in material living standards; accept a reasoned limitation that the Gini coefficient does not show absolute income, so living standards need not rise if all incomes fall.",
        ]
        return points, points
    if stimulus_kind == "inequality_line_chart" and command == "calculate":
        if marks == 2:
            points = [
                "1 mark for method: 0.42 − 0.33.",
                "1 mark for a fall of 0.09 in the Gini coefficient.",
            ]
            return points, points
    if stimulus_kind == "state_policy_context" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Defines productive capacity as the maximum sustainable output the economy can produce with its available resources and technology.",
            "AO2 (1 mark): Uses the source evidence that preventive healthcare spending rises by £12 billion and is expected to reduce working days lost through illness.",
            "AO3 (1 mark): Explains that healthier workers may be absent less often and supply more effective labour, increasing labour productivity.",
            "AO3 (1 mark): Develops the chain to a rightward shift of long-run aggregate supply and a rise in the economy's productive capacity; accept that the effect depends on the healthcare programme being effective.",
        ]
        return points, points
    if stimulus_kind == "trade_cycle" and topic.id == "2.1" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Defines cyclical unemployment as unemployment caused by deficient aggregate demand during a downturn in the economic cycle.",
            "AO2 (1 mark): Applies Figure 1 by identifying that real output rises as the economy moves from the trough into the recovery phase.",
            "AO3 (1 mark): Explains that rising aggregate demand leads firms to increase production and derived demand for labour.",
            "AO3 (1 mark): Develops the chain: firms recruit or retain more workers, so cyclical unemployment is likely to fall, although structural unemployment may remain.",
        ]
        return points, points
    if stimulus_kind == "tariff_context" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Explains that a tariff is a tax on imports that raises the landed marginal cost of the imported product.",
            "AO2 (1 mark): Uses the source: the £20 tariff raises the pre-tariff world price of £100 per panel to as much as £120, before other costs.",
            "AO3 (1 mark): Explains that the higher UK price contracts quantity demanded and makes domestic panels relatively more competitive, so imports are likely to fall.",
            "AO3 (1 mark): Develops the chain to an expansion of domestic supply/output from 40,000 panels, although the exact price and quantity effects depend on demand and supply elasticities and overseas exporters absorbing part of the tariff.",
        ]
        return points, points
        if marks == 4:
            points = [
                "1 mark for identifying the fall: 0.42 − 0.33 = 0.09.",
                "1 mark for dividing by the initial value: 0.09 ÷ 0.42.",
                "1 mark for multiplying by 100.",
                "1 mark for 21.4% (accept 21.43% or a correctly rounded equivalent).",
            ]
            return points, points
    if stimulus_kind == "cost_revenue_graph" and command == "draw" and marks == 4:
        points = [
            "AO1 (1 mark): In Figure 1, draws and labels a downward-sloping AR curve and an MR curve below it on axes labelled costs/revenues and output.",
            "AO1 (1 mark): Draws and labels appropriate MC and AC curves.",
            "AO2 (1 mark): Labels the profit-maximising output Qp on the output axis directly below MC = MR.",
            "AO2 (1 mark): Labels the distinct revenue-maximising output Qr directly below MR = 0, with Qr to the right of Qp.",
        ]
        return points, points
    if stimulus_kind == "context_extract" and topic.id == "1.2.1" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): Explains that a rational consumer compares the marginal benefit of the next unit with its marginal cost, including opportunity cost.",
            "AO2 (1 mark): Uses the source values: the first ticket has marginal benefit £24 and price £18, giving positive marginal net benefit of £6.",
            "AO3 (1 mark): Concludes that the first ticket is purchased because its marginal benefit exceeds its marginal cost.",
            "AO3 (1 mark): Explains that the second ticket is not purchased because its marginal benefit is only £10, below its £18 marginal cost, so stopping after one ticket maximises utility at the margin.",
        ]
        return points, points
    if stimulus_kind == "shutdown_cost_table" and command == "explain" and marks == 4:
        points = [
            "AO1 (1 mark): States the short-run shutdown rule: continue producing when price/average revenue is at least average variable cost, even if price is below average cost.",
            "AO2 (1 mark): Uses the table: price £18 exceeds AVC £14 but is below AC £22 at output 500.",
            "AO3 (1 mark): Calculates or explains the £4 contribution per unit towards fixed cost, equal to £2,000 across 500 units.",
            "AO3 (1 mark): Concludes that the firm should continue in the short run because its £2,000 operating loss is smaller than the £4,000 fixed-cost loss from shutting down.",
        ]
        return points, points
    return (
        _mark_scheme(command, marks, topic.title),
        _indicative_content(topic.id, topic.title, topic.points),
    )


def _adapt_paper_three_case_guidance(
    points: list[str],
    case_title: str,
    source_reference: str,
    topic_id: str,
) -> list[str]:
    if "healthcare" not in case_title.casefold():
        return points
    replacements = {
        "Extract C": source_reference or "the extract",
        "energy and utilities": "healthcare and pharmaceuticals",
        "energy-sector": "healthcare-sector",
        "energy capital": "healthcare capital",
        "energy prices": "medicine prices",
        "energy supply": "healthcare supply",
        "energy infrastructure": "healthcare infrastructure",
        "energy market": "healthcare market",
        "imported-energy": "imported-medicine",
        "additional generation or network capacity": "additional clinic, laboratory or medicine-production capacity",
        "cheaper or more reliable energy": "more productive or reliable healthcare provision",
        "14%": "13%",
    }
    if topic_id == "2.3":
        replacements.update({"changed by 5%": "changed by 16%", "11%": "4%"})
    adapted: list[str] = []
    for point in points:
        for original, replacement in replacements.items():
            point = point.replace(original, replacement)
        adapted.append(point)
    return adapted


def _paper_two_policy_guidance(marks: int) -> list[str]:
    guidance = {
        5: [
            "AO1 (1 mark): Identifies Bank Rate as the policy interest rate set by the Bank of England. Accept 'interest rates' where the Extract A/Bank of England context makes the meaning unambiguous; no reference to saving is required.",
            "AO2 (1 mark): Uses Extract A evidence that Bank Rate reached 5.25% in August 2023 in response to inflation.",
            "AO3 (1 mark): Explains that the higher Bank Rate raises borrowing or debt-servicing costs for households or firms.",
            "AO3 (1 mark): Develops the same route: interest-sensitive consumption or investment falls, reducing aggregate demand.",
            "AO3 (1 mark): Completes that single chain: weaker aggregate demand reduces demand-pull inflation. Award full marks for this one developed route; no second transmission mechanism is required.",
        ],
        8: [
            "Factor 1 — AO1 (1 mark): Identifies that expansionary fiscal policy raises aggregate demand through higher government spending or lower taxation.",
            "Factor 1 — AO2 (1 mark): Applies the evidence that fiscal support can sustain demand during a downturn.",
            "Factor 1 — AO3 (1 mark): Analyses that the multiplier can raise real GDP and reduce cyclical unemployment.",
            "Factor 1 — AO3 (1 mark): Examines the conflict that, near full capacity, stronger demand may create demand-pull inflation.",
            "Factor 2 — AO1 (1 mark): Explains that fiscal expansion may increase government borrowing and import demand.",
            "Factor 2 — AO2 (1 mark): Applies the evidence that expansionary policy may increase borrowing or worsen external balance.",
            "Factor 2 — AO3 (1 mark): Analyses that higher income raises imports, reducing net exports and potentially widening the current-account deficit.",
            "Factor 2 — AO3 (1 mark): Examines the limit: spare capacity, targeted domestic spending and low import leakages can reduce inflation and external-balance conflicts.",
        ],
        10: [
            "AO1 (1 mark): Defines supply-side policy as action intended to improve productivity, incentives, labour mobility or productive capacity.",
            "AO1 (1 mark): Explains that a rightward LRAS shift permits higher potential output with less inflationary pressure.",
            "AO2 (1 mark): Applies the evidence on training and childcare support increasing skills and labour-force participation.",
            "AO2 (1 mark): Applies the evidence on infrastructure investment, implementation cost or time lags.",
            "AO3 (1 mark): Analyses training raising labour productivity and occupational mobility, lowering unit labour cost and structural unemployment.",
            "AO3 (1 mark): Analyses childcare raising effective labour supply, easing recruitment constraints and wage-driven inflation.",
            "AO3 (1 mark): Develops infrastructure investment to lower firms' transport or digital costs and shift LRAS right.",
            "AO4 (1 mark): Evaluates long time lags and uncertainty over whether training matches vacancies or infrastructure is used efficiently.",
            "AO4 (1 mark): Evaluates short-run fiscal cost and AD effects, which can raise inflation before supply capacity expands.",
            "AO4 (1 mark): Concludes that well-targeted policies can reduce the conflict in the long run, but cannot remove short-run trade-offs or demand-side shocks.",
        ],
        12: [
            "AO1 (1 mark): Explains how training increases human capital and labour productivity.",
            "AO1 (1 mark): Explains how childcare and infrastructure can increase labour supply and economy-wide productive capacity.",
            "AO2 (1 mark): Uses Extract C evidence on training and childcare support.",
            "AO2 (1 mark): Uses Extract C evidence on infrastructure, cost, financing or implementation lags.",
            "AO3 Route A (1 mark): Analyses better skills raising output per worker and reducing structural unemployment.",
            "AO3 Route A (1 mark): Develops the chain to lower unit cost, a rightward LRAS shift and non-inflationary growth.",
            "AO3 Route B (1 mark): Analyses childcare increasing participation and easing labour shortages.",
            "AO3 Route B (1 mark): Develops infrastructure reducing business costs, crowding in investment and raising potential output.",
            "AO4 (1 mark): Evaluates time lags, regional mismatch and the quality of training or infrastructure.",
            "AO4 (1 mark): Evaluates opportunity cost, taxation or borrowing and possible crowding out.",
            "AO4 (1 mark): Evaluates that strong AD may still create short-run inflation before capacity comes on stream.",
            "AO4 (1 mark): Reaches a supported judgement comparing the three policies and identifying targeting, spare capacity and time horizon as decisive.",
        ],
        15: [
            "AO1 (1 mark): Explains tighter anti-inflation policy through higher interest rates, lower government spending or higher taxation.",
            "AO1 (1 mark): Explains the monetary transmission mechanism from financing costs to consumption, investment and aggregate demand.",
            "AO1 (1 mark): Distinguishes demand-pull from cost-push inflation and identifies the short-run output-inflation trade-off.",
            "AO2 (1 mark): Uses Extract D evidence that policy makers face conflicts between inflation, growth and unemployment.",
            "AO2 (1 mark): Applies the extract's evidence about borrowing costs, confidence, household disposable income or distributional effects.",
            "AO2 (1 mark): Applies uncertainty over time lags and whether inflation originates from demand or supply.",
            "AO3 (1 mark): Analyses higher interest costs reducing firms' investment, inventories and interest-sensitive expansion.",
            "AO3 (1 mark): Analyses weaker consumption reducing firms' sales, output, labour demand and cyclical employment.",
            "AO3 (1 mark): Analyses effects on consumers: mortgage or credit payments rise while savers may receive higher returns.",
            "AO3 (1 mark): Develops lower AD to weaker price pressure and, through expectations or sterling, potentially lower inflation.",
            "AO4 (1 mark): Evaluates sectoral differences between indebted firms/households and cash-rich savers or exporters.",
            "AO4 (1 mark): Evaluates that policy is less effective against imported energy or other cost-push inflation.",
            "AO4 (1 mark): Evaluates long and variable lags and the risk of overtightening into recession.",
            "AO4 (1 mark): Evaluates credibility: anchored expectations may reduce the output cost of restoring price stability.",
            "AO4 (1 mark): Reaches a supported judgement on the net effects for firms and consumers, conditional on inflation's cause, indebtedness and the time horizon.",
        ],
    }
    return guidance.get(marks, [])


def _paper_one_section_c_guidance(topic_id: str) -> list[str]:
    if topic_id == "1.4":
        return [
            "AO1 (1 mark): Defines an indirect tax as a tax on expenditure that raises firms' marginal and average costs.",
            "AO1 (1 mark): Explains a negative externality and the divergence between marginal social cost and marginal private cost.",
            "AO1 (1 mark): Identifies the socially efficient output where marginal social benefit equals marginal social cost.",
            "AO1 (1 mark): Explains government failure and opportunity cost when intervention is poorly designed.",
            "AO2 (1 mark): Applies the source estimate of a £0.12 external clean-up cost per disposable cup.",
            "AO2 (1 mark): Applies the proposed £0.10 per-cup tax and the estimated PED of −0.6.",
            "AO2 (1 mark): Uses the source alternatives: a reusable-cup standard, information campaign or clean-technology subsidy.",
            "AO2 (1 mark): Applies the distributional evidence that takeaway purchases form a larger budget share for some low-income consumers.",
            "AO3 Tax (1 mark): Analyses the tax shifting supply upward/left by the amount charged and increasing market price.",
            "AO3 Tax (1 mark): Develops the price mechanism to lower quantity demanded and produced, reducing external clean-up costs.",
            "AO3 Tax (1 mark): Analyses tax revenue financing clean-up, monitoring or lower distortionary taxes elsewhere.",
            "AO3 Tax (1 mark): Analyses incidence using relative elasticities and the source's inelastic-demand estimate.",
            "AO3 Alternative (1 mark): Analyses a reusable standard directly limiting harmful packaging when consumer response to price is weak.",
            "AO3 Alternative (1 mark): Analyses information improving consumer decisions where the external cost is poorly understood.",
            "AO3 Alternative (1 mark): Analyses a clean-technology subsidy lowering the private cost of substitutes and encouraging innovation.",
            "AO3 Comparison (1 mark): Compares how tax preserves choice and reveals abatement incentives while regulation gives greater quantity certainty.",
            "AO4 (1 mark): Evaluates calibration: the £0.10 tax is below the estimated £0.12 external marginal cost and damage varies by location.",
            "AO4 (1 mark): Evaluates inelastic PED: quantity may fall little while consumers bear a large price increase.",
            "AO4 (1 mark): Evaluates equity and whether targeted compensation could protect low-income consumers without removing the incentive.",
            "AO4 (1 mark): Evaluates administrative, monitoring and avoidance costs for the tax and reusable standard.",
            "AO4 (1 mark): Evaluates dynamic effects: a predictable tax can induce packaging innovation, but subsidy may accelerate it more directly.",
            "AO4 (1 mark): Evaluates unintended effects such as substitution into another material with its own external costs.",
            "AO4 (1 mark): Compares effectiveness against regulation using the regulator's information and enforcement capacity.",
            "AO4 (1 mark): Selects a proportionate policy mix, rather than assuming any single instrument removes the market failure completely.",
            "AO4 (1 mark): Reaches a supported judgement on whether taxation is most effective, naming the decisive elasticity, tax accuracy and time horizon.",
        ]
    if topic_id == "1.2.4":
        return [
            "AO1 (1 mark): Defines equilibrium price as the price at which quantity demanded equals quantity supplied.",
            "AO1 (1 mark): Explains consumer surplus as willingness to pay above market price and producer surplus as price above minimum willingness to supply.",
            "AO1 (1 mark): Explains how a leftward supply shift raises equilibrium price and lowers equilibrium quantity, other things equal.",
            "AO1 (1 mark): Distinguishes short-run from long-run demand and supply responsiveness.",
            "AO2 (1 mark): Applies the source's 12% fall in domestic tomato supply after poor weather.",
            "AO2 (1 mark): Uses the price increase from £2.40 to £3.00 per kilogram and the reported fall in purchases.",
            "AO2 (1 mark): Applies evidence that energy and greenhouse costs rose for producers.",
            "AO2 (1 mark): Applies evidence on low-income households, imports or growers able to invest in protected production.",
            "AO3 Consumers (1 mark): Analyses the higher price contracting quantity demanded and reducing consumer surplus.",
            "AO3 Consumers (1 mark): Develops the real-income effect, which is larger where tomatoes take a greater budget share.",
            "AO3 Consumers (1 mark): Analyses substitution towards alternatives, depending on availability and cross elasticity of demand.",
            "AO3 Consumers (1 mark): Analyses potential quality, nutrition or distributional consequences of reduced consumption.",
            "AO3 Producers (1 mark): Analyses that the higher market price can increase revenue per unit and producer surplus for firms still able to supply.",
            "AO3 Producers (1 mark): Develops that cost increases and lost crop volume may nevertheless reduce profit for badly affected growers.",
            "AO3 Producers (1 mark): Analyses the price signal encouraging imports, greenhouse investment or future entry and supply.",
            "AO3 Market (1 mark): Develops the long-run supply response towards a lower price and higher quantity than the short-run outcome.",
            "AO4 indicative route: evaluate how PED, PES and the availability of substitutes change the size and duration of consumer- and producer-surplus effects.",
            "AO4 indicative route: compare producer cost/exposure differences; a developed qualitative comparison between weather-damaged and protected growers is sufficient and need not repeat the £3.00 price.",
            "AO4 indicative route: evaluate imports, investment and biological production lags as market-adjustment mechanisms over time.",
            "AO4 indicative route: evaluate distribution and significance using household budget shares and the source evidence.",
            "AO4 Level 3 (7–9): sustained, source-based evaluation; weighs at least two relevant conditions; reaches a supported overall judgement that addresses both consumer and producer surplus. Separate mini-conclusions are not required.",
            "AO4 Level 2 (4–6): some developed evaluation and a conclusion, but comparison, context or coverage of one surplus measure is uneven.",
            "AO4 Level 1 (1–3): limited evaluative comment or an unsupported judgement; analysis repeated without qualification remains AO3.",
            "AO4 Level 0 (0): no evaluative content. Apply best fit holistically; the indicative routes are examples, not a checklist.",
        ]
    return []


def _paper_two_section_c_guidance(topic_id: str) -> list[str]:
    if topic_id == "4.1":
        return [
            "AO1 (1 mark): Defines protectionism as policies that restrict imports, including tariffs, quotas and non-tariff barriers.",
            "AO1 (1 mark): Explains comparative advantage and gains from specialisation and trade.",
            "AO1 (1 mark): Explains tariff effects on domestic price, demand, supply and imports.",
            "AO1 (1 mark): Identifies trade creation/diversion, retaliation and government failure.",
            "AO2 (1 mark): Uses the source's £900 world e-bike price and proposed 20% tariff.",
            "AO2 (1 mark): Uses domestic output of 50,000 and imports of 150,000 bicycles.",
            "AO2 (1 mark): Applies the 1,200 jobs at risk and domestic spare capacity.",
            "AO2 (1 mark): Applies the evidence on imported components and possible retaliation against UK exports.",
            "AO3 (1 mark): Analyses the tariff raising import price and expanding domestic output and employment.",
            "AO3 (1 mark): Develops reduced import competition to higher producer surplus and tariff revenue.",
            "AO3 (1 mark): Analyses higher prices and lower choice reducing consumer surplus.",
            "AO3 (1 mark): Develops imported-component costs to weaker competitiveness for UK assemblers.",
            "AO3 (1 mark): Analyses retaliation reducing UK exports, AD, output and employment.",
            "AO3 (1 mark): Develops resource misallocation when protected firms lack comparative advantage.",
            "AO3 (1 mark): Analyses a temporary infant-industry route through investment and learning economies.",
            "AO3 (1 mark): Develops macro effects on inflation, current account, exchange rate or long-run productivity.",
            "AO4 strand 1 — up to 2 marks: elasticities and incidence; develop how responsiveness determines price, import and welfare effects.",
            "AO4 strand 2 — up to 2 marks: retaliation and component dependence; develop the net employment/current-account effect.",
            "AO4 strand 3 — up to 2 marks: time and dynamic efficiency; compare temporary adjustment support with permanent protection.",
            "AO4 strand 4 — up to 2 marks: distribution and policy alternatives; compare targeted training/innovation support with the tariff.",
            "AO4 judgement — 1 mark: reaches an economy-wide conclusion that weighs consumers, producers and government and identifies the decisive elasticity, retaliation risk and time horizon.",
        ]
    if topic_id == "4.2":
        return [
            "AO1 (1 mark): Distinguishes income from wealth inequality and absolute from relative poverty.",
            "AO1 (1 mark): Explains the Gini coefficient and Lorenz curve as measures of income distribution.",
            "AO1 (1 mark): Explains progressive taxation, transfers, minimum wages and supply-side policies.",
            "AO1 (1 mark): Identifies equity-efficiency trade-offs, incentives and government failure.",
            "AO2 (1 mark): Uses the source Gini coefficient of 0.39.",
            "AO2 (1 mark): Uses the bottom quintile's 8% income share and high food-bank demand.",
            "AO2 (1 mark): Applies the proposed higher top marginal tax rate and targeted transfers.",
            "AO2 (1 mark): Applies childcare, training and wealth-tax alternatives or administrative evidence.",
            "AO3 (1 mark): Analyses progressive tax and transfers increasing lower-income disposable income and reducing relative poverty.",
            "AO3 (1 mark): Develops redistribution to consumption, living standards and the multiplier.",
            "AO3 (1 mark): Analyses higher marginal rates affecting labour supply, enterprise, avoidance and migration.",
            "AO3 (1 mark): Develops targeted childcare/training to participation, skills, earnings and pre-tax inequality.",
            "AO3 (1 mark): Analyses a minimum wage raising earnings but potentially changing employment where labour demand is elastic.",
            "AO3 (1 mark): Analyses wealth taxation addressing asset inequality but creating valuation and avoidance problems.",
            "AO3 (1 mark): Develops macro effects through AD, productivity, fiscal cost and LRAS.",
            "AO3 (1 mark): Compares short-run redistribution with longer-run equality of opportunity.",
            "AO4 strand 1 — up to 2 marks: incentives and elasticities; develop the scale of labour-supply, employment or avoidance responses.",
            "AO4 strand 2 — up to 2 marks: targeting and administration; develop take-up, errors, stigma, valuation or fiscal cost.",
            "AO4 strand 3 — up to 2 marks: time horizon; compare immediate disposable-income effects with slower human-capital effects.",
            "AO4 strand 4 — up to 2 marks: policy mix and macro context; develop effects on growth, inflation, productivity and public finances.",
            "AO4 judgement — 1 mark: selects a justified policy mix and states whether success means a lower Gini coefficient, less poverty or greater opportunity, with a decisive condition and time horizon.",
        ]
    return []


def _question_guidance(
    paper_id: str,
    marks: int,
    command: str,
    topic: SyllabusTopic,
    case_title: str = "",
    source_reference: str = "",
) -> tuple[list[str], list[str]]:
    if paper_id == "paper_1" and marks == 25:
        points = _paper_one_section_c_guidance(topic.id)
        if points:
            return points, points
    if paper_id == "paper_2" and marks == 25:
        points = _paper_two_section_c_guidance(topic.id)
        if points:
            return points, points
    if paper_id == "paper_2" and topic.id == "2.6":
        points = _paper_two_policy_guidance(marks)
        if points:
            return points, points
    if paper_id == "paper_1" and topic.id == "3.2" and command == "explain" and marks == 5:
        points = [
            "AO1 (1 mark): Identifies a valid alternative objective, such as satisficing, employee welfare, service quality, sales revenue or long-term survival.",
            "AO2 (1 mark): Applies the reason to Extract A, for example John Lewis is employee-owned and emphasises worker interests, service quality or long-term reputation.",
            "AO3 (1 mark): Explains that employee-owners may value pay, job security or working conditions as well as the financial return from profit.",
            "AO3 (1 mark): Develops the chain: retaining staff or service quality can strengthen customer loyalty and the firm's long-term reputation, even when it reduces short-run profit.",
            "AO3 (1 mark): Concludes that managers may therefore accept a satisfactory level of profit that still funds investment while balancing employee and customer objectives. Accept another coherent, source-applied reason.",
        ]
        return points, points
    if paper_id == "paper_1" and topic.id == "3.2" and command == "examine" and marks == 8:
        points = [
            "Conflict 1 — AO1 (1 mark): Explains that retaining profit for investment can conflict with an objective to improve employee pay or working conditions.",
            "Conflict 1 — AO2 (1 mark): Applies the supplied evidence: Amazon reinvested profit in logistics, cloud computing and new services while rapid expansion increased pressure on workers.",
            "Conflict 1 — AO3 (1 mark): Analyses that higher wages or safer staffing raise costs and reduce retained profit available to finance expansion in the short run.",
            "Conflict 1 — AO3 (1 mark): Examines the qualification that improved conditions may reduce staff turnover and raise productivity, supporting future profit rather than creating a permanent conflict.",
            "Conflict 2 — AO1 (1 mark): Explains that maximising short-run profit can conflict with sales-growth or market-share objectives when expansion requires lower margins or additional expenditure.",
            "Conflict 2 — AO2 (1 mark): Applies the supplied evidence: investment in logistics and new services was intended to strengthen market share, brand loyalty and future economies of scale.",
            "Conflict 2 — AO3 (1 mark): Analyses that lower prices or higher capital spending can sacrifice current profit while attracting customers and increasing output.",
            "Conflict 2 — AO3 (1 mark): Examines the qualification that economies of scale and loyalty may later reduce average cost and increase profit, so the extent and duration of the conflict depend on successful demand growth.",
        ]
        return points, points
    if paper_id == "paper_1" and topic.id == "3.2" and command == "assess" and marks == 10:
        points = [
            "AO1 (1 mark): Explains that regulation changes firms' constraints and incentives through enforceable standards, monitoring, penalties or controls on prices and returns.",
            "AO1 (1 mark): Distinguishes profit maximisation from non-profit objectives such as service quality, environmental performance and stakeholder welfare.",
            "AO2 (1 mark): Applies the evidence that UK water companies were criticised over dividends, executive pay and environmental performance.",
            "AO2 (1 mark): Applies the evidence that regulators and consumers want stronger service and pollution targets, while investors argue profit finances infrastructure.",
            "AO3 (1 mark): Analyses that binding pollution standards and credible fines raise the expected cost of non-compliance, encouraging managers to prioritise environmental performance rather than distributions to owners.",
            "AO3 (1 mark): Analyses that service-quality targets can redirect investment and management effort towards reliability, changing the operational objective even if long-run profit remains important.",
            "AO3 (1 mark): Analyses the counter-route: if penalties are weak or monitoring is poor, paying a fine may cost less than compliance, so profit maximisation and dividend targets may remain dominant.",
            "AO4 (1 mark): Assesses that stricter objectives may reduce short-run distributable profit but infrastructure investment can improve efficiency, service and long-run returns.",
            "AO4 (1 mark): Assesses that the effect depends on regulatory design, enforcement certainty, allowed prices and whether shareholders tolerate lower short-run returns.",
            "AO4 (1 mark): Reaches a supported judgement: effective, binding and monitored regulation is likely to change proximate objectives, but need not replace profit as the firm's ultimate long-run objective.",
            "Level 3 (8–10): accurate knowledge, sustained use of Extract C, developed analysis and a supported contextual judgement.",
            "Level 2 (4–7): generally accurate knowledge with some contextual analysis, but development or judgement is uneven.",
            "Level 1 (1–3): isolated relevant points with limited development or use of Extract C.",
            "Level 0 (0): no rewardable material.",
            "Accept an equivalent valid analytical route when it is applied to Extract C and reaches a supported outcome.",
            "Do not award the same developed point twice; a response that does not use Extract C cannot reach Level 3.",
        ]
        return points, points
    if paper_id == "paper_1" and topic.id == "3.2" and command == "discuss" and marks == 12:
        points = [
            "AO1 (1 mark): Explains profit maximisation as producing where marginal revenue equals marginal cost, subject to regulatory constraints.",
            "AO1 (1 mark): Explains stakeholder objectives such as service quality, environmental performance and consumer welfare.",
            "AO2 (1 mark): Uses Extract C evidence about criticism of water-company dividends, executive pay and environmental performance.",
            "AO2 (1 mark): Uses Extract C evidence that profit is needed to finance infrastructure and improve long-run performance.",
            "AO3 Route A (1 mark): Analyses that prioritising profit can retain funds for maintenance and investment when external finance is costly.",
            "AO3 Route A (1 mark): Develops the chain to improved network reliability, productivity and potentially lower long-run unit costs.",
            "AO3 Route B (1 mark): Analyses that prioritising service and pollution targets redirects resources towards maintenance, treatment and compliance.",
            "AO3 Route B (1 mark): Develops the chain to fewer leaks or pollution incidents, higher consumer welfare and lower third-party costs.",
            "AO4 (1 mark): Evaluates that dividends or executive pay may reduce the credibility of claims that maximum profit is needed for investment.",
            "AO4 (1 mark): Evaluates the risk that very low allowed returns deter private investment and worsen service quality over time.",
            "AO4 (1 mark): Compares time horizons: stakeholder spending may reduce current profit but protect reputation and future revenue.",
            "AO4 (1 mark): Reaches a supported judgement that the appropriate priority depends on binding standards, infrastructure needs and whether profits are reinvested rather than distributed.",
        ]
        return points, points
    if paper_id == "paper_1" and topic.id == "3.2" and command == "discuss" and marks == 15:
        points = [
            "AO1 (1 mark): Defines satisficing as pursuing an acceptable profit while meeting other objectives rather than maximising profit.",
            "AO1 (1 mark): Explains separation of ownership and control as a reason managers may pursue growth, status or lower-risk objectives.",
            "AO1 (1 mark): Identifies stakeholder objectives including employee welfare, customer service, sustainability, sales growth and survival.",
            "AO2 (1 mark): Applies Extract D evidence that managers may satisfice where ownership and control are separated.",
            "AO2 (1 mark): Applies the extract's distinction between short-run costs and possible long-run gains from loyalty, retention or reputation.",
            "AO2 (1 mark): Applies uncertainty over demand, finance or stakeholder response when judging the scale of effects.",
            "AO3 (1 mark): Analyses how higher employee pay or better conditions raise cost and reduce short-run profit but may reduce turnover and raise productivity.",
            "AO3 (1 mark): Analyses how service quality or sustainability spending can differentiate the firm, increase loyalty and strengthen long-run revenue.",
            "AO3 (1 mark): Analyses how sales-growth objectives may require lower prices and higher capacity spending, increasing output but compressing margins.",
            "AO3 (1 mark): Develops stakeholder effects for consumers, workers, owners and rival firms rather than treating the firm as a single interest.",
            "AO4 (1 mark): Evaluates whether non-profit objectives complement rather than conflict with long-run profit through productivity and reputation.",
            "AO4 (1 mark): Evaluates finance: weak profit may constrain investment, resilience and survival, particularly for a highly geared firm.",
            "AO4 (1 mark): Evaluates market structure and competition, which determine whether higher stakeholder costs can be passed into prices.",
            "AO4 (1 mark): Evaluates the time horizon and how owners monitor managers, including the risk of managerial self-interest.",
            "AO4 (1 mark): Reaches a supported overall judgement on the net effects and identifies the decisive objective, stakeholder and time period from Extract D.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "1.2.3" and marks == 5:
        points = [
            "AO1 (1 mark): Defines price elasticity of supply as the responsiveness of quantity supplied to a change in price.",
            "AO2 (1 mark): Uses the 15% price change and 6% output change shown in Figure 1.",
            "AO2 (1 mark): Uses Extract A evidence about capacity, contracts or delayed access to inputs.",
            "AO3 (1 mark): Explains that the chosen constraint prevents production capacity or inputs expanding quickly after the 15% price rise.",
            "AO3 (1 mark): Infers from the smaller proportional output response (6% compared with the 15% price rise), or calculates PES = 6% / 15% = 0.4, that supply is price inelastic in the short run. Do not require the calculation when the qualitative comparison is clear.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "1.3" and marks == 5:
        points = [
            "AO1 (1 mark): Defines a negative production externality as an external cost imposed on third parties, so marginal social cost exceeds marginal private cost.",
            "AO2 (1 mark): Uses Figure 3: market output is 117 million doses, compared with the estimated socially efficient output of 100 million doses where MSB = MSC.",
            "AO2 (1 mark): Uses Extract D evidence that untreated chemical waste creates an estimated £6 external marginal water-treatment and health cost per dose that producers do not pay.",
            "AO3 (1 mark): Explains that excluding the £6 third-party cost makes MPC lower than MSC, so the private market price understates the full social cost and encourages excess output.",
            "AO3 (1 mark): Concludes explicitly that the 17 million doses between the 100 million social optimum and 117 million market output are overproduced, creating deadweight welfare loss because their marginal social cost exceeds their marginal social benefit.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "3.1" and marks == 8:
        points = [
            "Factor 1 — AO1 (1 mark): Identifies a technical economy of scale and explains that it can lower long-run average cost (LRAC) as output increases.",
            "Factor 1 — AO2 (1 mark): Uses Figure 2 evidence that capital spending increased by 5% in 2025.",
            "Factor 1 — AO3 (1 mark): Explains that the new capital raises productivity and spreads fixed costs over more units, reducing cost per unit and LRAC.",
            "Factor 1 — AO3 (1 mark): Examines the limit: if demand is insufficient to use the added capacity, fixed cost per unit may not fall, so the LRAC reduction is conditional.",
            "Factor 2 — AO1 (1 mark): Identifies a purchasing economy of scale and links bulk buying to a reduction in LRAC.",
            "Factor 2 — AO2 (1 mark): Uses Extract A evidence that long-term supply contracts reduced unit input costs by 4%.",
            "Factor 2 — AO3 (1 mark): Explains that the contract discount reduces variable cost per unit as output grows, lowering LRAC.",
            "Factor 2 — AO3 (1 mark): Examines the limit: rapid expansion may create coordination diseconomies that offset the contract saving, so LRAC may not fall overall.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "1.3" and marks == 12:
        points = [
            "AO1 (1 mark): Defines a negative externality as an external cost imposed on a third party, so marginal social cost exceeds marginal private cost.",
            "AO1 (1 mark): Explains that allocative efficiency occurs where marginal social benefit equals marginal social cost and total economic welfare is maximised.",
            "AO2 (1 mark): Uses Extract B evidence that energy prices changed by 29% and represented a larger share of expenditure for some income groups.",
            "AO2 (1 mark): Uses Extract B evidence about pollution costs, wider benefits from resilient shared networks, or compliance costs deterring entry.",
            "AO3 Route A (1 mark): Analyses how an unpriced pollution cost gives MSC > MPC, causing private energy output to exceed the socially efficient quantity.",
            "AO3 Route A (1 mark): Develops that overproduction chain to deadweight welfare loss; a correctly labelled external-cost diagram may support the analysis.",
            "AO3 Route B (1 mark): Analyses resilient-network investment as a positive spillover where MSB > MPB because firms cannot capture every wider benefit; it need not be classified as a pure public good.",
            "AO3 Route B (1 mark): Develops that chain to private investment below the socially efficient quantity and a deadweight loss from forgone net social benefits.",
            "AO4 (1 mark): Examines whether the welfare loss is large by considering the size and valuation of the external cost or benefit.",
            "AO4 (1 mark): Examines how demand and supply elasticities determine the change in quantity, incidence and resulting welfare effect.",
            "AO4 (1 mark): Considers a counterargument, such as contracts, reputation, property rights or profitable innovation allowing firms to internalise some effects.",
            "AO4 (1 mark): Reaches a supported judgement on the size of the overall welfare loss using Extract B. The 29% price change and its distributional effect may supplement, but must not replace, allocative-efficiency analysis.",
            "Level 3 (9–12): accurate welfare theory, sustained use of Extract B, developed causal analysis, balanced qualification and a supported contextual judgement.",
            "Level 2 (5–8): generally accurate theory with some context and at least one developed chain, but qualification or judgement is partial.",
            "Level 1 (1–4): isolated knowledge or assertions with limited use of Extract B and little causal development.",
            "Level 0 (0): no rewardable material.",
            "Accept an equivalent valid welfare-analysis route when it uses Extract B and reaches a supported conclusion.",
            "Do not award the same developed point twice; a response without relevant Extract B application cannot reach Level 3.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "3.5" and marks == 8:
        points = [
            "Factor 1 — AO1 (1 mark): Identifies occupational immobility caused by the qualifications and specialist training required for healthcare roles.",
            "Factor 1 — AO2 (1 mark): Uses Extract E evidence that vacancies rose by 28% and the median vacancy lasted 14 weeks.",
            "Factor 1 — AO3 (1 mark): Explains that a slow supply response leaves posts unfilled, constraining treatment capacity and raising recruitment or agency costs.",
            "Factor 1 — AO3 (1 mark): Examines the limit: funded training places or recognition of overseas qualifications can make labour supply more elastic over time.",
            "Factor 2 — AO1 (1 mark): Identifies non-wage working conditions as a determinant of labour supply and retention.",
            "Factor 2 — AO2 (1 mark): Uses Extract E evidence that overtime increased and annual staff turnover reached 12% despite a 9% wage rise.",
            "Factor 2 — AO3 (1 mark): Explains that workload and unsocial hours can reduce retention, shifting effective labour supply left and increasing wage pressure and provider costs.",
            "Factor 2 — AO3 (1 mark): Examines the limit: improved staffing, flexible schedules or productivity-enhancing technology may improve conditions and output without continuing wage inflation.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "1.4" and marks == 12:
        points = [
            "AO1 (1 mark): Explains that an indirect tax raises private marginal cost, while a subsidy lowers it; either can change producer and consumer incentives.",
            "AO1 (1 mark): Defines government failure as intervention producing a net welfare loss through information problems, unintended incentives or excessive administrative cost.",
            "AO2 (1 mark): Uses Extract E evidence that pharmaceutical prices changed by 28% and the product takes a larger expenditure share for some households.",
            "AO2 (1 mark): Applies the evidence about third-party pollution costs, wider network benefits, compliance costs or contested subsidy evidence.",
            "AO3 Route A (1 mark): Analyses how a tax calibrated to marginal external cost can raise price and reduce output towards the socially efficient level.",
            "AO3 Route A (1 mark): Develops that incentive chain to lower pollution damage and tax revenue that could fund treatment or monitoring.",
            "AO3 Route B (1 mark): Analyses how a targeted subsidy for research or resilient shared infrastructure can raise activity with positive external benefits.",
            "AO3 Route B (1 mark): Develops that chain to greater access, innovation or network resilience where private returns understate social benefits.",
            "AO4 (1 mark): Evaluates incidence and effectiveness using demand and supply elasticities; inelastic demand may leave patients paying much of a tax.",
            "AO4 (1 mark): Evaluates distribution: higher medicine prices may disproportionately reduce access for lower-income or chronically ill households.",
            "AO4 (1 mark): Evaluates information and compliance costs, including the risk that a poorly calibrated tax, subsidy or rule deters entry and innovation.",
            "AO4 (1 mark): Reaches a supported judgement comparing instruments and identifying the market failure, targeting accuracy and time horizon that determine whether incentives improve welfare.",
        ]
        return points, points
    if paper_id == "paper_3" and topic.id == "2.3" and marks == 25:
        points = [
            "AO1 Micro (1 mark): Defines productive capacity as the maximum sustainable output attainable with available capital, labour and technology.",
            "AO1 Micro (1 mark): Explains how capital investment, specialisation or economies of scale may lower a firm's long-run average cost.",
            "AO1 Macro (1 mark): Defines LRAS as the economy's productive potential at each price level and distinguishes it from short-run aggregate supply.",
            "AO1 Macro (1 mark): Identifies investment as a component of aggregate demand and a source of capital deepening that can affect LRAS.",
            "AO2 Micro (1 mark): Uses Extract C evidence that energy-sector output changed by 5%.",
            "AO2 Micro (1 mark): Uses the 11% planned-investment figure and links it to new energy capital or infrastructure.",
            "AO2 Macro (1 mark): Applies Extract C evidence about employment, aggregate demand or productive capacity in the UK economy.",
            "AO2 Macro (1 mark): Applies one stated condition: spare capacity, business confidence, import dependence or crowding out.",
            "AO3 Micro (1 mark): Analyses how new capital can raise labour or capital productivity in energy and utilities.",
            "AO3 Micro (1 mark): Develops that chain to lower unit cost/LRAC, greater sector output and potentially lower energy prices.",
            "AO3 Micro (1 mark): Analyses how additional generation or network capacity can improve reliability and reduce capacity constraints.",
            "AO3 Micro (1 mark): Develops a stakeholder effect for consumers or competing firms, such as higher consumer surplus or lower input costs.",
            "AO3 Macro (1 mark): Analyses how the 11% investment raises AD initially and may increase real GDP and employment through the multiplier.",
            "AO3 Macro (1 mark): Develops how capital deepening and infrastructure shift LRAS right, increasing potential output.",
            "AO3 Macro (1 mark): Explains that cheaper or more reliable energy can lower production costs across industries and shift SRAS right.",
            "AO3 Macro (1 mark): Develops the macro chain to stronger non-inflationary growth or a lower price level than otherwise.",
            "AO4 Micro (1 mark): Evaluates whether demand is strong enough to utilise the new sector capacity; unused capacity can prevent LRAC falling.",
            "AO4 Micro (1 mark): Evaluates financing costs, construction delays or coordination diseconomies that may raise costs before benefits arrive.",
            "AO4 Micro (1 mark): Evaluates market structure: a firm with market power may retain cost savings instead of passing them on through lower prices.",
            "AO4 Micro (1 mark): Weighs short-run disruption against longer-run productivity, reliability and consumer benefits.",
            "AO4 Macro (1 mark): Evaluates spare capacity: the AD effect may raise output when spare capacity is high but create demand-pull inflation near full capacity.",
            "AO4 Macro (1 mark): Evaluates import dependence and multiplier leakages; imported equipment can weaken the domestic GDP effect and current account initially.",
            "AO4 Macro (1 mark): Evaluates whether higher borrowing or public support crowds out private investment, depending on interest rates and confidence.",
            "AO4 Macro (1 mark): Evaluates time lags and uncertainty over whether the planned 11% investment is completed and raises productivity.",
            "AO4 Judgement (1 mark): Reaches a supported conclusion covering both energy-sector outcomes and UK macroeconomic outcomes, identifying the decisive condition and time horizon.",
            "Level 4 (20–25): precise theory, sustained Extract C application, developed micro and macro analysis, evaluation across both scopes and an integrated judgement.",
            "Level 3 (13–19): developed analysis of both scopes with relevant context, but evaluation or synthesis is uneven.",
            "Level 2 (7–12): some accurate contextual analysis, but one scope is underdeveloped or evaluation is largely asserted.",
            "Level 1 (1–6): isolated knowledge or generic statements with little use of Extract C.",
            "Level 0 (0): no rewardable material. A response cannot reach Level 4 unless it develops both the microeconomic and macroeconomic effects.",
        ]
        points = _adapt_paper_three_case_guidance(
            points, case_title, source_reference, topic.id
        )
        if "healthcare" in case_title.casefold():
            points = [
                *points[:16],
                "AO4 Evaluation strand 1 — up to 2 marks: capacity utilisation and demand. Award 1 mark for identifying spare capacity or uncertain demand; award 2 only when the response develops how low utilisation prevents LRAC/productivity benefits or how strong demand enables them.",
                "AO4 Evaluation strand 2 — up to 2 marks: finance and crowding out. Award 1 mark for identifying borrowing cost, public support or crowding out; award 2 only when the response develops the effect on private investment, AD or the net capacity increase.",
                "AO4 Evaluation strand 3 — up to 2 marks: imported equipment and time lags. Award 1 mark for identifying dependence on imported equipment/medicines or implementation delay; award 2 only when the response develops the consequence for domestic multiplier gains, the current account or the timing of LRAS gains.",
                "AO4 Evaluation strand 4 — up to 2 marks: pass-through and stakeholders. Award 1 mark for identifying market power or unequal stakeholder effects; award 2 only when the response develops whether productivity savings reach patients, taxpayers, workers or rival providers.",
                "AO4 Judgement — 1 mark: gives a supported conclusion on both the microeconomic effects and the macroeconomic effects, then states their overall balance or explains why they cannot be directly aggregated. It must select one evidenced decisive condition, weigh it against an alternative and state a time horizon; no particular condition is prescribed.",
                *points[25:],
            ]
        return points, points
    if paper_id == "paper_3" and topic.id == "4.5" and marks == 25:
        points = [
            "AO1 Micro (1 mark): Defines state intervention as government action to alter market prices, output, quality, ownership or resource allocation.",
            "AO1 Micro (1 mark): Explains how an indirect tax, subsidy, regulation or public provision can address an externality, information failure or market power.",
            "AO1 Macro (1 mark): Defines discretionary fiscal policy as deliberate changes in government spending or taxation that affect aggregate demand.",
            "AO1 Macro (1 mark): Explains opportunity cost and government failure as constraints on state allocation of scarce public funds.",
            "AO2 Micro (1 mark): Uses Extract C's 14% international-price movement and applies it to energy prices, producer costs or consumer affordability.",
            "AO2 Micro (1 mark): Applies the stated use of taxation, regulation or trade policy in the energy and utilities market.",
            "AO2 Macro (1 mark): Applies Extract C evidence that public investment may improve resilience, productivity or regional employment.",
            "AO2 Macro (1 mark): Uses the extract's evidence about imports and exports or the time needed for energy supply to respond.",
            "AO3 Micro (1 mark): Analyses how targeted subsidy or public infrastructure investment can lower producer costs and increase energy supply.",
            "AO3 Micro (1 mark): Develops the supply chain to lower prices, higher consumer surplus or improved network reliability.",
            "AO3 Micro (1 mark): Analyses how regulation or an indirect tax can internalise pollution costs or improve service standards.",
            "AO3 Micro (1 mark): Develops the intervention chain towards the socially efficient output/quality, while identifying the affected stakeholder.",
            "AO3 Macro (1 mark): Analyses how public expenditure raises AD directly and may increase real GDP and employment through the multiplier.",
            "AO3 Macro (1 mark): Analyses how resilient energy infrastructure raises productivity and shifts LRAS right over time.",
            "AO3 Macro (1 mark): Develops the LRAS chain to greater non-inflationary growth and lower economy-wide production costs.",
            "AO3 Macro (1 mark): Analyses a trade/current-account route, such as reduced imported-energy dependence improving net exports and resilience.",
            "AO4 Micro (1 mark): Evaluates policy targeting and elasticities: tax or subsidy effects depend on producer and consumer responsiveness.",
            "AO4 Micro (1 mark): Evaluates regulatory capture, compliance costs or barriers to entry that could weaken competition and raise prices.",
            "AO4 Micro (1 mark): Evaluates information limits: government may misestimate external costs, benefits or the appropriate subsidy/tax rate.",
            "AO4 Micro (1 mark): Compares intervention instruments and identifies which is most proportionate for the stated market failure.",
            "AO4 Macro (1 mark): Evaluates the opportunity cost of public expenditure and the tax or borrowing needed to finance it.",
            "AO4 Macro (1 mark): Evaluates crowding out, interest-rate conditions and business confidence when judging the net investment effect.",
            "AO4 Macro (1 mark): Evaluates import leakages, implementation lags and whether domestic spare capacity is sufficient for a large multiplier.",
            "AO4 Macro (1 mark): Weighs short-run AD/inflation effects against longer-run LRAS, productivity and resilience benefits.",
            "AO4 Judgement (1 mark): Reaches a supported conclusion covering both market-level and UK macroeconomic effects, naming the preferred policy mix, decisive condition and time horizon.",
            "Level 4 (20–25): precise theory, sustained Extract C application, developed micro and macro analysis, evaluation across both scopes and an integrated judgement.",
            "Level 3 (13–19): developed analysis of both scopes with relevant context, but evaluation or synthesis is uneven.",
            "Level 2 (7–12): some accurate contextual analysis, but one scope is underdeveloped or evaluation is largely asserted.",
            "Level 1 (1–6): isolated knowledge or generic policy statements with little use of Extract C.",
            "Level 0 (0): no rewardable material. A response cannot reach Level 4 unless it develops both microeconomic and macroeconomic effects.",
        ]
        points = _adapt_paper_three_case_guidance(
            points, case_title, source_reference, topic.id
        )
        if "healthcare" in case_title.casefold():
            points = [
                *points[:16],
                "AO4 Evaluation strand 1 — up to 2 marks: targeting and elasticities. Award 1 mark for identifying responsiveness or policy targeting; award 2 only when the response develops how this changes price, output, access or external-cost correction.",
                "AO4 Evaluation strand 2 — up to 2 marks: information and regulatory design. Award 1 mark for identifying information failure, compliance cost or regulatory capture; award 2 only when the response develops the consequence for competition, innovation or welfare.",
                "AO4 Evaluation strand 3 — up to 2 marks: finance and opportunity cost. Award 1 mark for identifying taxation, borrowing, public-spending opportunity cost or crowding out; award 2 only when the response develops the net effect on private investment, AD or public services.",
                "AO4 Evaluation strand 4 — up to 2 marks: macro timing and leakages. Award 1 mark for identifying implementation lag, spare capacity or import leakage; award 2 only when the response develops the implication for inflation, the multiplier, LRAS or the current account.",
                "AO4 Judgement — 1 mark: selects and justifies a healthcare policy mix, integrates micro and macro effects, and identifies an evidenced decisive condition and time horizon. No named instrument or condition is compulsory.",
                *points[25:],
            ]
        return points, points
    return (
        _mark_scheme(command, marks, topic.title),
        _indicative_content(topic.id, topic.title, topic.points),
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
    case_title: str = "",
) -> str:
    topic = _topic_phrase(topic_title)
    if parts:
        if parts[0].command_word == "draw":
            if stimulus_kind == "cost_revenue_graph":
                return "The axes below are for an imperfectly competitive firm with downward-sloping average and marginal revenue curves."
            return _section_a_draw_stem(topic_title)
        return _section_a_stem(topic_title, stimulus_kind)
    if section_name in {"A", "B"} and paper_id == "paper_3":
        return _paper_3_question_prompt(marks, topic, source_reference, case_title)
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
    if stimulus_kind == "state_policy_context":
        return "Read the information below about an increase in government spending on preventive healthcare."
    if stimulus_kind == "development_data_table":
        return "The table below shows selected economic development indicators for two countries."
    if stimulus_kind == "current_account_line_chart":
        return "The chart below shows the current account of the balance of payments as a percentage of GDP."
    if stimulus_kind == "inequality_line_chart":
        return "Figure 1 below shows the Gini coefficient for an economy over five years."
    if stimulus_kind == "trade_cycle":
        return "Figure 1 below shows a stylised economic cycle with recession, trough, recovery and boom phases."
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


_PAPER_3_SHORT_FOCI = {
    "demand": "demand may change",
    "supply": "supply may be relatively price inelastic in the short run",
    "price determination": "prices may become volatile",
    "market failure": "private market outcomes may cause a significant loss of economic welfare",
    "government intervention": "government intervention may change incentives",
    "business growth": "business growth may reduce average costs",
    "business objectives": "firms may pursue objectives other than profit maximisation",
    "revenues, costs and profits": "higher costs may affect profits",
    "market structures": "barriers to entry may weaken competition",
    "labour market": "labour shortages may affect wages and output",
    "government intervention in markets": "competition policy may affect firms and consumers",
    "measures of economic performance": "sectoral changes may affect economic performance",
    "aggregate demand": "changes in the sector may affect aggregate demand",
    "aggregate supply": "investment may affect productive capacity",
    "national income": "changes in spending may create a multiplier effect",
    "economic growth": "investment may affect long-run economic growth",
    "macroeconomic objectives and policies": "policy makers may face conflicting objectives",
    "international economics": "trade and exchange rates may affect the sector",
    "poverty and inequality": "price changes may affect income inequality",
    "emerging and developing economies": "the sector may influence economic development",
    "financial sector": "access to credit may affect investment",
    "role of the state in the macroeconomy": "state intervention may affect economic performance",
}

_PAPER_3_EXTENDED_FOCI = {
    "demand": "a sustained increase in demand",
    "supply": "an increase in market supply",
    "market failure": "policies intended to correct market failure",
    "government intervention": "greater government intervention",
    "business growth": "rapid business growth",
    "revenues, costs and profits": "a sustained increase in production costs",
    "market structures": "an increase in market concentration",
    "labour market": "persistent labour shortages",
    "government intervention in markets": "stronger competition policy",
    "measures of economic performance": "changes in inflation and employment",
    "aggregate demand": "a sustained increase in aggregate demand",
    "aggregate supply": "an increase in productive capacity",
    "economic growth": "faster economic growth",
    "macroeconomic objectives and policies": "tighter macroeconomic policy",
    "international economics": "increased international specialisation and trade",
    "poverty and inequality": "policies intended to reduce income inequality",
    "emerging and developing economies": "greater foreign direct investment",
    "financial sector": "greater access to credit",
    "role of the state in the macroeconomy": "greater state intervention",
}


def _paper_3_question_prompt(
    marks: int,
    topic: str,
    source_reference: str,
    case_title: str,
) -> str:
    context = case_title.lower() if case_title else "the case-study context"
    short_focus = _PAPER_3_SHORT_FOCI.get(topic, f"{topic} may affect economic outcomes")
    if marks == 5 and topic == "market failure":
        return (
            f"With reference to {source_reference}, explain why an unpriced negative "
            f"production externality may cause overproduction and a loss of economic welfare in {context}."
        )
    if marks == 5:
        return f"With reference to {source_reference}, explain one reason why {short_focus} in {context}."
    if marks == 8:
        return f"With reference to {source_reference}, examine two factors that may explain why {short_focus} in {context}."
    if marks == 12:
        return f"With reference to {source_reference}, discuss whether {short_focus} in {context}."
    if marks == 25 and topic == "aggregate supply":
        capacity_focus = (
            "increased energy-sector productive capacity"
            if "energy" in context
            else f"increased productive capacity in {context}"
        )
        return (
            f"With reference to {source_reference}, evaluate the likely microeconomic and "
            f"macroeconomic effects of {capacity_focus}: consider "
            f"firms and consumers in {context}, and the productive potential, output and price "
            "level of the UK economy."
        )
    if marks == 25 and topic in {
        "role of the state in the macroeconomy",
        "the role of the state in the macroeconomy",
    }:
        return (
            f"With reference to {source_reference}, evaluate the likely microeconomic and "
            f"macroeconomic effects of greater state intervention in {context} through public "
            "investment, taxation, regulation or trade policy."
        )
    extended_focus = _PAPER_3_EXTENDED_FOCI.get(topic, topic)
    return (
        f"Evaluate the microeconomic and macroeconomic effects of {extended_focus} "
        f"on {context}."
    )


def _source_reference(
    paper_id: str,
    section_name: str,
    index: int,
    stimulus_kind: str = "",
) -> str:
    if section_name == "A" and paper_id in {"paper_1", "paper_2"}:
        if stimulus_kind == "context_extract" or stimulus_kind.endswith("_context"):
            return ""
        if "table" in stimulus_kind:
            return "Table 1"
        return "Figure 1"
    if section_name == "B" and paper_id in {"paper_1", "paper_2"}:
        return ["Extract A", "", "", "Extract C", "Extract D"][index % 5]
    if paper_id == "paper_3":
        references = {
            "A": [
                "Figure 1 and Extract A",
                "Figure 2 and Extract A",
                "Extract B",
                "Extract C",
                "Extract C",
            ],
            "B": [
                "Figure 3 and Extract D",
                "Extract E",
                "Extract E",
                "Extract E",
                "Extract F",
            ],
        }
        return references[section_name][index % 5]
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
    *,
    paper_id: str = "",
    case_title: str = "",
    source_variant: int = 0,
    source_reference: str = "",
) -> str:
    focus = ", ".join(points[:3]) if points else _topic_phrase(topic_title)
    if paper_id == "paper_3":
        return _paper_3_source_text(
            case_title,
            topic_title,
            points,
            index,
            source_variant,
            source_reference,
        )
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


def _paper_3_source_text(
    case_title: str,
    topic_title: str,
    points: list[str],
    index: int,
    variant: int,
    source_reference: str = "",
) -> str:
    context = case_title.lower() if case_title else "the case-study market"
    first = points[0].rstrip(".") if points else topic_title.lower()
    second = points[1].rstrip(".") if len(points) > 1 else first
    price_change = 8 + (variant + index * 7) % 29
    output_change = 2 + (variant // 7 + index * 5) % 16
    firm_count = 24 + (variant // 11 + index * 13) % 67
    investment = 3 + (variant // 17 + index * 3) % 18
    year = 2022 + (variant + index) % 4
    figure_match = re.search(r"Figure\s+\d+", source_reference)
    extract_match = re.search(r"Extract\s+[A-Z]", source_reference)
    figure_ref = figure_match.group(0) if figure_match else "The figure"
    extract_ref = extract_match.group(0) if extract_match else (source_reference or "The extract")
    investment_intro = (
        f"{figure_ref} shows that firms in {context} increased capital spending by {investment}% in {year}. "
        f"{extract_ref} reports that long-term supply contracts reduced unit input costs by 4%. "
        if figure_match
        else f"{extract_ref} reports that firms in {context} increased capital spending by {investment}% in {year}, "
        "while long-term supply contracts reduced unit input costs by 4%. "
    )
    if _normal_topic_key(topic_title) == "labour market" and index == 1:
        return (
            f"{extract_ref} reports that unfilled clinical and pharmaceutical vacancies in {context} "
            "rose by 28%, with a median vacancy duration of 14 weeks. Employers increased average pay "
            "by 9%, but overtime also rose and annual staff turnover reached 12%. Training for specialist "
            "roles can take several years, and professional registration limits how quickly suitably "
            "qualified workers can enter. Providers are considering funded training places, recognition "
            "of overseas qualifications, flexible schedules and technology that complements scarce staff."
        )
    if _normal_topic_key(topic_title) == "market failure" and index == 0:
        return (
            f"{figure_ref} compares pharmaceutical output in {context}. The private market produced "
            "117 million doses. Researchers estimated that the socially efficient output, where marginal "
            f"social benefit equals marginal social cost, was 100 million doses. {extract_ref} reports that "
            "some producers discharged untreated chemical waste. Water-treatment providers and nearby "
            "households bore an estimated external marginal clean-up and health cost of £6 per dose. "
            "Producers did not pay this cost or include it in the market price, so they based output "
            "decisions on marginal private cost rather than the higher marginal social cost."
        )
    templates = (
        (
            f"{figure_ref} shows that prices in {context} changed by {price_change}% in {year}, while "
            f"output changed by {output_change}%. {extract_ref} reports that analysts linked the adjustment to {first}. There "
            f"were {firm_count} active suppliers, but their ability to alter output differed because "
            "capacity, contracts and access to inputs could not be changed immediately. Consumer "
            "groups said substitution became easier over time, while producers argued that higher "
            "expected prices were needed before new capacity would be commercially viable."
        ),
        (
            investment_intro
            +
            f"Larger businesses said {first} affected their average costs, while smaller firms reported "
            "more limited access to finance and skilled labour. Managers warned that rapid expansion "
            f"could create diseconomies and coordination problems. Evidence concerning {second} suggested "
            "that the benefits of scale depended on demand remaining strong enough to use the additional capacity."
        ),
        (
            f"Policy makers reviewing {context} focused on {first}. Households faced different effects "
            f"after prices changed by {price_change}%, because the product represented a larger share "
            "of expenditure for some income groups. Business representatives supported predictable "
            "rules but said compliance costs could deter entry. Campaigners reported air-pollution costs "
            "borne by third parties and wider benefits from investment in resilient shared networks that "
            f"private firms could not fully capture. Evidence on {second} remained contested. The final welfare effect depended on the size "
            "of any market failure, the responsiveness of consumers and firms, and uncertainty when "
            "valuing effects on third parties."
        ),
        (
            f"Changes in {context} affected the wider economy in {year}. Output in the sector changed "
            f"by {output_change}% and planned investment by {investment}%, influencing employment, "
            "aggregate demand and productive capacity. Economists linked the evidence to capital "
            "deepening, productivity and the economy's long-run productive potential. "
            "Higher imported-input and wage costs could shift short-run aggregate supply left and raise inflation, while new capital and infrastructure "
            "could increase long-run aggregate supply. The scale of the effect depended on spare "
            "capacity, business confidence, import dependence and whether policy crowded private "
            "investment in or out."
        ),
        (
            f"The government examined the long-run role of the state in {context} after international prices moved "
            f"by {price_change}% in {year}. Officials considered {first}, alongside taxation, public "
            "spending, regulation and trade policy. Supporters of intervention argued that investment "
            "could improve resilience, productivity and regional employment. Critics emphasised the "
            f"opportunity cost and the possibility of government failure. Evidence on {second} showed "
            "that the distribution of gains and losses, effects on imports and exports, and the time "
            "needed for supply to respond were central to the final judgement."
        ),
    )
    return templates[index % len(templates)]


def _data_response_extract(topic_title: str, points: list[str], index: int) -> str:
    return data_response_extract(topic_title, points, index)


def _section_c_extract(topic_id: str, topic_title: str, points: list[str], index: int) -> str:
    if topic_id == "1.4":
        return (
            "A study estimated a £0.12 external clean-up cost per disposable cup. Policy makers proposed "
            "a £0.10 tax; PED was −0.6. Alternatives included a reusable-cup standard, information and a "
            "clean-technology subsidy. Takeaway purchases formed a larger budget share for some low-income "
            "consumers, while environmental damage varied by location."
        )
    if topic_id == "1.2.4":
        return (
            "Poor weather reduced domestic tomato supply by 12%. The price rose from £2.40 to £3.00 per "
            "kilogram and purchases fell. Growers faced higher energy costs; protected producers maintained "
            "more output and retailers increased imports. The rise affected low-income households most, "
            "while growers said higher prices could finance more resilient production."
        )
    if topic_id == "4.1":
        return (
            "Imported electric bicycles sell for a world price of £900. A proposed 20% tariff aims to "
            "protect 1,200 UK jobs. Domestic firms currently produce 50,000 bicycles and imports supply "
            "150,000; UK factories have some spare capacity but rely on imported batteries and motors. "
            "Trading partners have warned that they may retaliate against UK exports."
        )
    if topic_id == "4.2":
        return (
            "The economy's Gini coefficient is 0.39 and the lowest-income fifth of households receives "
            "8% of disposable income. Food banks report high demand. Proposals include a higher top "
            "marginal income-tax rate, targeted transfers, subsidised childcare and training, a higher "
            "minimum wage and wealth tax. Officials warn about take-up, valuation, avoidance and fiscal cost."
        )
    return section_c_extract(topic_title, points, index)


def _section_a_context(
    topic_id: str,
    topic_title: str,
    focus: str,
    points: list[str],
    stimulus_kind: str = "",
) -> str:
    stimulus_contexts = {
        "ped_data_table": "The table compares how two age groups buying the same premium coffee product respond to a price change.",
        "pes_data_table": "The table gives PES coefficients showing how quantity supplied responds to price changes in two regional markets. Urban producers have limited spare capacity and contracts delay their access to inputs; rural producers report more flexible capacity and input access.",
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
        "state_policy_context": "The government plans to increase annual spending on preventive healthcare by £12 billion, financed through higher progressive income taxation. It expects earlier treatment to reduce working days lost through illness and improve labour productivity. Funding the programme means that another public investment cannot proceed, and the outcome depends on whether patients can access the additional services.",
        "trade_cycle": "Figure 1 shows real output falling through recession to a trough before rising during recovery towards a boom. Firms report spare capacity at the trough and stronger orders during recovery. The diagram does not imply that every type of unemployment disappears when output rises.",
        "development_data_table": "The data can be used to compare living standards and economic development in two emerging economies.",
        "current_account_line_chart": "The balance changed as domestic income affected import spending, overseas demand affected export revenue, and firms' non-price competitiveness altered over time.",
        "inequality_line_chart": "The Gini coefficient fell from 0.42 in Year 1 to 0.33 in Year 5. Over the same period, the government increased targeted transfers to low-income households, although the chart alone does not show whether every household's real income rose.",
        "cost_revenue_graph": "A fictional imperfectly competitive firm faces a downward-sloping AR curve. It is comparing the output at which MC equals MR with the higher output at which MR equals zero. A fall in market demand would shift both its AR and MR curves downwards.",
        "context_extract": "A consumer has £30 available. The first event ticket costs £18 and gives an estimated marginal benefit of £24. A second ticket also costs £18 but gives a marginal benefit of only £10. Money not spent can be used for another good.",
        "gdp_growth_bar_chart": "Quarterly real GDP growth varied as consumption, investment and government spending changed.",
        "terms_of_trade_index_chart": "The index compares average export prices with average import prices, using a base year of 100.",
        "labour_inactivity_context": "A higher share of working-age people were neither in work nor actively seeking employment.",
        "multiplier_context": "A survey estimates the marginal propensity to consume after households receive extra income.",
        "tariff_context": "Imported solar panels have a world price of £100 each. The UK imposes a £20 tariff per imported panel. Before the tariff, UK firms supplied 40,000 panels while imports met the remainder of demand. Domestic producers have some spare capacity, but overseas exporters may absorb part of the tariff in their margins.",
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


def _mark_breakdown(
    marks: int,
    parts: list[QuestionPart],
    stimulus_kind: str = "",
) -> str:
    if stimulus_kind == "current_account_line_chart":
        return "AO1 1, AO2 2, AO3 2"
    if stimulus_kind == "inequality_line_chart":
        return "MCQ 1, AO1 1, AO2 1, AO3 2"
    if stimulus_kind == "trade_cycle":
        return "MCQ 1, AO1 1, AO2 1, AO3 2"
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
        return [
            "Award 1 mark for the correct answer.",
            f"Correct answer directly addresses the syllabus point on {topic}.",
        ]
    if marks <= 5:
        return [
            "",
            f"AO1 (Knowledge/Understanding) — up to {max(1, marks // 3)} mark(s):",
            f"Correctly identifies or defines {topic}.",
            f"Accurately states the economic relationship or theory that underpins {topic}.",
            "",
            f"AO2 (Application) — up to {max(1, marks // 3)} mark(s):",
            "Applies the concept to the specific data, figure or context provided in the question.",
            "Uses relevant numerical values or quotes from the source material.",
            "",
            f"AO3 (Analysis) — up to {max(2, marks - 2 * (marks // 3))} mark(s):",
            "Develops a logical chain of reasoning showing cause and effect.",
            f"Connects the analysis back to the syllabus framework for {topic}.",
        ]
    cmd = command_word.lower()
    has_evaluation = marks >= 10
    bullets = [
        "",
        f"AO1 (Knowledge/Understanding) — syllabus alignment for {topic}:",
        f"Accurately recalls and defines key terminology from the {topic} section of the specification.",
        f"Demonstrates knowledge of economic models, theories or relationships relevant to {topic}.",
        "Makes precise use of syllabus concepts such as marginal analysis, elasticity, equilibrium or efficiency.",
        "",
        f"AO2 (Application) — use of context and data for {topic}:",
        "Selects and applies relevant data, figures or extract content from the question material.",
        f"Shows how the theoretical concepts from {topic} operate in the real-world context described.",
        "Where numerical data is provided, correctly calculates or interprets values to support the argument.",
        "",
        f"AO3 (Analysis) — economic reasoning for {topic}:",
        "Constructs a coherent chain of reasoning linking causes to effects using economic theory.",
        "Explains the mechanism through which changes in one variable affect another (e.g. price mechanism, multiplier effect, market adjustment processes).",
        "Uses appropriate economic models or diagrams to support the analytical argument.",
        "Develops the analysis to show second-round or dynamic effects where relevant.",
    ]
    if has_evaluation:
        if cmd in {"evaluate", "assess"}:
            bullets.extend([
                "",
                f"AO4 (Evaluation) — supported judgement for {topic}:",
                "Weighs competing arguments or stakeholder perspectives to reach a balanced conclusion.",
                "Assesses the strength of the evidence: considers which factors are most significant and why.",
                "Identifies limitations, assumptions or real-world complications (e.g. ceteris paribus, time lags, data reliability).",
                "Makes a final, well-supported judgement that directly answers the question's command word.",
                "Where appropriate, considers alternative policy options or theoretical viewpoints.",
            ])
        elif cmd == "discuss":
            bullets.extend([
                "",
                f"AO4 (Discussion) — balanced consideration for {topic}:",
                "Presents arguments on multiple sides of the issue, drawing on relevant economic theory.",
                "Evaluates the relative importance of different factors, effects or stakeholder outcomes.",
                "Synthesises the discussion into a coherent overall assessment with clear reasoning.",
                "Considers real-world constraints, empirical evidence or counter-arguments that qualify the analysis.",
            ])
        elif cmd == "examine":
            bullets.extend([
                "",
                f"AO4 (Examination) — detailed investigation for {topic}:",
                "Breaks down the issue into its component parts for systematic investigation.",
                "Investigates causes, effects and relationships in depth, using specific evidence.",
                "Draws a supported conclusion based on the weight of evidence examined.",
                "Identifies any ambiguities, exceptions or further questions raised by the analysis.",
            ])
        else:
            bullets.extend([
                "",
                f"AO4 (Evaluation) — supported judgement for {topic}:",
                "Provides a clear judgement or conclusion supported by the preceding analysis.",
                "Considers counter-arguments, limitations or alternative viewpoints.",
            ])
    bullets.insert(0, "Indicative content should be rewarded where it is relevant and developed, even if not explicitly listed. Credit must be given for accurate and relevant economic understanding demonstrated by the candidate.")
    if marks >= 8 and cmd in {
        "analyse",
        "analyze",
        "assess",
        "discuss",
        "evaluate",
        "examine",
        "justify",
    }:
        top_floor = max(2, math.ceil(marks * 0.75))
        middle_floor = max(2, math.ceil(marks * 0.4))
        bullets.extend(
            [
                "",
                "Levels-based marking: apply best fit across the complete response.",
                f"Level 3 ({top_floor}–{marks}): precise knowledge, sustained contextual analysis and a conclusion proportionate to the command word.",
                f"Level 2 ({middle_floor}–{top_floor - 1}): generally accurate knowledge with some developed analysis; judgement or application is uneven.",
                f"Level 1 (1–{middle_floor - 1}): isolated relevant points with limited development or context.",
                "Level 0 (0): no creditworthy material.",
                "Accept an equivalent valid analytical route when it uses the supplied context and reaches a supported outcome.",
                "Do not award the same developed point twice; cap a response that does not use the required context below the top level.",
            ]
        )
    return bullets


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
