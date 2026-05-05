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
            available_topics = _topics_suitable_for_template(available_topics, part_commands, stimulus_kind)
            topic = source_context_topic or _choose_topic(rng, available_topics, excluded_ids)
            command_word = section.command_words[index]
            number = _question_number(config.id, section.name, absolute_question_number, index)
            parts = _build_parts(part_marks, part_commands, topic.title)
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
    "revenues, costs and profits": "changes in fixed costs, variable costs and profit",
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


_STIMULUS_TOPIC_IDS = {
    "cost_revenue_graph": {"3.2", "3.3", "3.4"},
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


def _build_parts(part_marks: list[int], part_commands: list[str], topic_title: str) -> list[QuestionPart]:
    if not part_marks:
        return []
    return [
        _build_part(chr(97 + part_index), marks, command, topic_title, part_index)
        for part_index, (marks, command) in enumerate(zip(part_marks, part_commands, strict=True))
    ]


def _build_part(
    label: str,
    marks: int,
    command: str,
    topic_title: str,
    part_index: int,
) -> QuestionPart:
    if command == "mcq":
        options = _mcq_options(topic_title)
        correct = "A"
        return QuestionPart(
            label=label,
            marks=marks,
            command_word=command,
            prompt=_mcq_prompt(topic_title),
            options=options,
            correct_option=correct,
            mark_breakdown="1 mark",
            mark_scheme=[
                f"The only correct answer is {correct}",
                *[
                    f"{option.label} is not correct because it does not accurately describe {topic_title.lower()}."
                    for option in options
                    if option.label != correct
                ],
            ],
        )
    return QuestionPart(
        label=label,
        marks=marks,
        command_word=command,
        prompt=_placeholder_prompt(command, marks, topic_title),
        mark_breakdown=_part_mark_breakdown(marks, command),
        mark_scheme=_mark_scheme(command, marks, topic_title),
        indicative_content=_indicative_content("", topic_title, []),
    )


def _mcq_options(topic_title: str) -> list[MultipleChoiceOption]:
    topic = _topic_phrase(topic_title)
    topic_key = topic_title.lower()
    topic_options = _TOPIC_MCQ_OPTIONS.get(topic_key)
    if topic_options:
        return [MultipleChoiceOption(label=label, text=text) for label, text in topic_options]
    sentence_topic = topic[0].upper() + topic[1:]
    return [
        MultipleChoiceOption(label="A", text=f"Changes in {topic} can alter incentives and resource allocation"),
        MultipleChoiceOption(label="B", text=f"{sentence_topic} means opportunity cost no longer exists"),
        MultipleChoiceOption(label="C", text=f"{sentence_topic} only affects consumers and never affects firms"),
        MultipleChoiceOption(label="D", text=f"{sentence_topic} always leaves market price unchanged"),
    ]


def _mcq_prompt(topic_title: str) -> str:
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
    if stimulus_kind == "cost_revenue_graph":
        return f"The diagram below shows cost and revenue curves for a firm affected by {focus}."
    if stimulus_kind in {"data_table", "elasticity_data_table", "concentration_ratio_table", "balance_payments_table", "inflation_index_table"}:
        return f"The table below shows selected economic data linked to {focus}."
    if stimulus_kind in {"market_diagram", "demand_shift_graph", "supply_shift_graph"}:
        return f"The diagram below shows demand and supply in a market affected by {focus}."
    if stimulus_kind in {"tax_subsidy_diagram", "externality_diagram", "minimum_price_diagram", "maximum_price_diagram"}:
        return f"The diagram below shows a possible intervention or market failure linked to {focus}."
    if stimulus_kind in {"consumer_surplus_diagram", "producer_surplus_diagram"}:
        return f"The diagram below shows welfare effects in a market affected by {focus}."
    if stimulus_kind in {"perfect_competition_diagram", "monopoly_diagram", "monopsony_diagram", "labour_market_diagram"}:
        return f"The diagram below shows a market structure or labour market linked to {focus}."
    if stimulus_kind in {"macro_chart", "ad_as_diagram", "keynesian_as_diagram", "trade_cycle", "phillips_curve", "lorenz_curve", "exchange_rate_diagram", "tariff_diagram", "money_market_diagram", "laffer_curve", "poverty_trap_diagram", "production_possibility_frontier"}:
        return f"The diagram below shows an economic relationship linked to {focus}."
    if stimulus_kind == "payoff_matrix":
        return f"The pay-off matrix below shows possible outcomes for firms affected by {focus}."
    if stimulus_kind in {"line_graph", "index_number_chart"}:
        return f"The line graph below shows changes in data linked to {focus}."
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
        return _section_a_context(topic_id, topic_title, focus, points)
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


def _section_a_context(topic_id: str, topic_title: str, focus: str, points: list[str]) -> str:
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
