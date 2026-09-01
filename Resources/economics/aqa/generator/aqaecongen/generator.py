from __future__ import annotations

import random
import secrets
from decimal import ROUND_HALF_UP, Decimal

from aqaecongen.configs import PAPER3_VISUAL_QUESTION_NUMBERS
from aqaecongen.syllabus import Syllabus, Topic
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    resolve_question_rules,
    validate_generated_paper,
)
from Backend.Core.mark_scheme_enrichment import enrich_paper
from Backend.Core.numeric_integrity import percentage_change_context

INDUSTRIES = [
    "urban bus services",
    "heat-pump installation",
    "mobile payment platforms",
    "offshore wind maintenance",
    "specialist food retailing",
    "battery recycling",
    "regional housebuilding",
    "cloud accounting software",
    "private dental care",
    "rail freight",
]
ECONOMIES = [
    "Asteria",
    "Borealis",
    "Calidora",
    "Dameron",
    "Estara",
    "Freymark",
    "Galene",
    "Hesperia",
    "Ilyria",
    "Junora",
]
MCQ_FACTS = {
    "4.1.1": (
        "Which change represents an increase in opportunity cost?",
        "More of one product must be sacrificed to produce an extra unit of another",
        ["All resources become unemployed", "The price level falls", "Consumer surplus is unchanged"],
    ),
    "4.1.2": (
        "Which behaviour is most consistent with bounded rationality?",
        "Using a simple rule of thumb because information is costly",
        ["Maximising utility with perfect information", "Ignoring every available choice", "Producing where price equals marginal cost"],
    ),
    "4.1.3": (
        "Demand is price inelastic. Which outcome follows from a rise in price, other things equal?",
        "Total expenditure on the product rises",
        ["Quantity demanded rises", "Total expenditure must fall", "Supply shifts to the left"],
    ),
    "4.1.4": (
        "Which statement about a firm's costs is correct?",
        "Marginal cost crosses average cost at the minimum of average cost",
        ["Fixed cost rises with every unit", "Average variable cost always equals price", "Total cost can never rise"],
    ),
    "4.1.5": (
        "Which feature is most likely to make a market contestable?",
        "Low sunk costs for firms entering and leaving",
        ["A statutory monopoly", "Perfect price discrimination", "A single protected patent"],
    ),
    "4.1.6": (
        "Which outcome is associated with a monopsonistic labour market?",
        "A powerful employer can hold wages below the competitive level",
        ["Every worker receives economic rent", "Labour supply is perfectly horizontal", "Employment must be zero"],
    ),
    "4.1.7": (
        "Which change would unambiguously make a Lorenz curve show less income inequality?",
        "The curve moves closer to the line of equality",
        ["The curve moves further from the line of equality", "Nominal GDP rises", "The price level is unchanged"],
    ),
    "4.1.8": (
        "Production creates an external cost. Which quantity is normally socially efficient?",
        "The output where social marginal cost equals social marginal benefit",
        ["The output where private marginal cost is zero", "The maximum technically possible output", "The output chosen without considering third parties"],
    ),
    "4.2.1": (
        "Which measure is most useful when comparing average material living standards over time?",
        "Real GDP per head",
        ["Nominal GDP alone", "The consumer price index alone", "The money supply alone"],
    ),
    "4.2.2": (
        "The marginal propensity to consume rises. What happens to the simple multiplier?",
        "It becomes larger",
        ["It becomes zero", "It necessarily becomes negative", "It is unchanged in every case"],
    ),
    "4.2.3": (
        "Which combination is most consistent with a positive output gap?",
        "Actual output exceeds the economy's sustainable trend",
        ["Cyclical unemployment rises sharply", "Aggregate demand is always zero", "The current account must balance"],
    ),
    "4.2.4": (
        "A central bank raises its policy interest rate. Which is the most likely short-run effect?",
        "Credit-financed consumption and investment weaken",
        ["Borrowing becomes cheaper", "The money multiplier becomes infinite", "All asset prices must rise"],
    ),
    "4.2.5": (
        "Which measure is an interventionist supply-side policy?",
        "Government-funded vocational training",
        ["A rise in indirect tax to cut demand", "A reduction in the money supply", "A tariff with no domestic production"],
    ),
    "4.2.6": (
        "A country's currency depreciates. Which condition makes an improvement in its trade balance more likely?",
        "Export and import demand are sufficiently price elastic",
        ["All trade volumes are fixed forever", "Domestic inflation is necessarily zero", "Its current account is already balanced"],
    ),
}
MCQ_CONTEXTS = {
    "4.1.1": "An economy can transfer workers and machinery between two industries, but some resources are specialised.",
    "4.1.2": "A household chooses a pension product using limited information and a familiar rule of thumb.",
    "4.1.3": "A rail operator is considering a fare increase after estimating how passengers respond to price changes.",
    "4.1.4": "A manufacturer records its total, average and marginal costs as weekly output changes.",
    "4.1.5": "New firms can enter a digital market quickly, although incumbent firms retain large customer networks.",
    "4.1.6": "One large employer purchases most of the labour supplied by qualified workers in a local area.",
    "4.1.7": "A government compares household income distributions before and after a reform to direct taxation.",
    "4.1.8": "Production at a chemical plant creates pollution costs that are not included in the firm's accounts.",
    "4.2.1": "An economist compares national income and population data across several years with different price levels.",
    "4.2.2": "Households decide to spend a larger proportion of every additional pound of disposable income.",
    "4.2.3": "Real output has risen above its estimated long-run sustainable level during a period of strong demand.",
    "4.2.4": "The central bank changes its policy rate in response to persistent inflationary pressure.",
    "4.2.5": "A government wants to raise productive capacity without relying only on lower taxes or deregulation.",
    "4.2.6": "A country's exchange rate falls while exporters and importers can adjust quantities over time.",
}

APPLIED_TOPIC_BY_NUMBER = {
    1: "4.1.1",
    3: "4.1.3",
    7: "4.1.7",
    11: "4.2.4",
    17: "4.2.6",
}
VISUAL_SPECS = {
    2: ("4.1.3", "D", "right", "market"),
    4: ("4.1.3", "D", "left", "market"),
    9: ("4.1.8", "S", "right", "market"),
    10: ("4.1.8", "S", "left", "market"),
    13: ("4.2.2", "AD", "right", "aggregate"),
    14: ("4.2.4", "AD", "left", "aggregate"),
    19: ("4.2.3", "SRAS", "right", "aggregate"),
    20: ("4.2.3", "SRAS", "left", "aggregate"),
    24: ("4.2.5", "LRAS", "right", "aggregate"),
    25: ("4.2.5", "LRAS", "left", "aggregate"),
}
INDEX_TOPIC_BY_NUMBER = {5: "4.2.1", 15: "4.2.1", 30: "4.2.1"}
FACTUAL_TOPIC_BY_NUMBER = dict(
    zip(
        (6, 8, 12, 16, 18, 21, 22, 23, 26, 27, 28, 29),
        tuple(MCQ_FACTS)[:12],
        strict=True,
    )
)
PAPER3_TOPIC_BY_NUMBER = {
    **APPLIED_TOPIC_BY_NUMBER,
    **{number: spec[0] for number, spec in VISUAL_SPECS.items()},
    **INDEX_TOPIC_BY_NUMBER,
    **FACTUAL_TOPIC_BY_NUMBER,
}


def build_paper(rule: PaperRule, syllabus: Syllabus, seed: int | None = None) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    if not topics:
        raise ValueError("no syllabus topics are available for this paper")
    shuffled_topics = topics[:]
    rng.shuffle(shuffled_topics)

    sections: list[GeneratedSection] = []
    question_number = 1
    topic_cursor = 0
    for section_rule in rule.sections:
        if rule.id == "paper_3" and section_rule.id == "B":
            question_number = 31
        options: list[GeneratedOption] = []
        for option_index in range(section_rule.option_count):
            question_rules = resolve_question_rules(section_rule, option_index + 1)
            topic = shuffled_topics[topic_cursor % len(shuffled_topics)]
            topic_cursor += 1
            if section_rule.id == "A" and rule.id == "paper_3":
                topic_id = PAPER3_TOPIC_BY_NUMBER[option_index + 1]
                topic = next(candidate for candidate in topics if candidate.id == topic_id)
                option = _build_mcq_option(option_index + 1, topic, rng, question_rules[0])
            else:
                option, question_number = _build_written_option(
                    rule,
                    question_rules,
                    section_rule.id,
                    option_index + 1,
                    question_number,
                    topic,
                    rng,
                )
            options.append(option)
        instructions = _section_instructions(rule.id, section_rule.id, section_rule.option_count)
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                title=section_rule.title,
                instructions=instructions,
                options=options,
            )
        )

    paper = GeneratedPaper(
        paper_id=rule.id,
        paper_code=rule.code,
        title=rule.title,
        duration_minutes=rule.duration_minutes,
        total_marks=rule.total_marks,
        seed=run_seed,
        sections=sections,
    )
    paper = enrich_paper(paper, syllabus.topics, subject="economics")
    validate_generated_paper(paper, rule, syllabus.topic_ids)
    return paper


def _build_written_option(
    rule: PaperRule,
    question_rules: list[QuestionRule],
    section_id: str,
    option_index: int,
    question_number: int,
    topic: Topic,
    rng: random.Random,
) -> tuple[GeneratedOption, int]:
    is_data = section_id == "A" or rule.id == "paper_3"
    context_name = rng.choice(INDUSTRIES if topic.paper == 1 else ECONOMIES)
    start = rng.randint(72, 138)
    changes = [rng.randint(-9, 14) for _ in range(4)]
    values = [float(start)]
    for change in changes:
        values.append(round(max(20, values[-1] * (1 + change / 100)), 1))
    identifier = rng.randint(1000, 9999)
    title = (
        f"Context {option_index}: {context_name.title()} ({identifier})"
        if is_data
        else f"Essay {option_index}: {topic.title}"
    )
    stimulus = (
        _stimulus(
            topic,
            context_name,
            identifier,
            values,
            rng,
            expanded=rule.id == "paper_3",
        )
        if is_data
        else [
            (
                f"A fictional case in {context_name} illustrates how {rng.choice(topic.points)} "
                f"can affect firms, households and wider economic outcomes. Recent evidence "
                "suggests that the size and distribution of these effects remain contested."
            )
        ]
    )
    questions: list[GeneratedQuestion] = []
    for part_index, question_rule in enumerate(question_rules):
        number = str(question_number + part_index)
        questions.append(
            _written_question(
                question_rule,
                number,
                topic,
                context_name,
                identifier,
                values,
                rng,
                is_data=is_data,
                paper_id=rule.id,
            )
        )
    return (
        GeneratedOption(
            id=f"{section_id}{option_index}",
            title=title,
            stimulus=stimulus,
            chart_title=f"Index of activity in {context_name} (base year = 100)",
            chart_labels=[str(2024 + index) for index in range(5)] if is_data else [],
            chart_values=values if is_data else [],
            questions=questions,
        ),
        question_number + len(question_rules),
    )


def _written_question(
    rule: QuestionRule,
    number: str,
    topic: Topic,
    context_name: str,
    identifier: int,
    values: list[float],
    rng: random.Random,
    *,
    is_data: bool,
    paper_id: str,
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    change = ((values[-1] - values[0]) / values[0]) * 100
    context = (
        (
            f"the evidence in the source insert about {context_name}"
            if paper_id == "paper_3"
            else f"the extracts about {context_name}"
        )
        if is_data
        else "relevant economic theory"
    )
    if rule.kind == "calculation":
        prompt = (
            f"Using the index data for {context_name} in the "
            f"{'source insert' if paper_id == 'paper_3' else 'extracts'}, calculate "
            "the percentage change from "
            "2024 to 2028. "
            "Give your answer to one decimal place."
        )
        scheme = [
            f"Correct method: (({values[-1]} − {values[0]}) ÷ {values[0]}) × 100.",
            f"Correct answer: {change:.1f}%.",
            f"Award up to {rule.marks} marks for a valid method and correct answer.",
        ]
    elif rule.kind == "data_interpretation":
        prompt = (
            "Assess the extent to which the data in the source insert suggest "
            f"that outcomes in {context_name} have improved."
        )
        scheme = [
            "Accurate comparison of at least two relevant indicators from the source insert.",
            "Recognition that the indicators measure different dimensions and may conflict.",
            "A supported judgement about the extent of improvement and limits of the data.",
        ]
    elif rule.marks <= 10:
        if rule.kind == "diagram_analysis":
            prompt = (
                f"With the help of a correctly labelled diagram and using {context}, explain "
                f"one way in which {point} could affect {context_name}."
            )
        else:
            prompt = (
                f"Using {context}, explain one way in which {point} could affect {context_name}."
            )
        scheme = [
            f"Knowledge and application of {point}.",
            f"A logical chain connecting the change to an outcome in {context_name}.",
            (
                "A correctly labelled diagram with the relevant shift and new equilibrium."
                if rule.kind == "diagram_analysis"
                else "Accurate use of the supplied evidence."
            ),
        ]
    elif rule.marks <= 15:
        prompt = (
            f"Explain how {point} can influence outcomes associated with {topic.title.lower()}."
        )
        scheme = [
            f"Accurate knowledge of {topic.title}.",
            f"Developed analysis of at least two channels involving {point}.",
            "Relevant diagram, calculation or contextual example where appropriate.",
        ]
    elif rule.command_word == "Recommend":
        prompt = (
            f"After considering Extract D and the evidence in Extracts A, B and C, would you "
            f"recommend {policy_name(topic, rng)} to improve outcomes in {context_name}? "
            "Justify your recommendation."
        )
        scheme = [
            f"Accurate knowledge and application of {topic.title}.",
            "Developed analysis of the proposed intervention and at least one realistic alternative.",
            "Evaluation of evidence quality, opportunity cost, unintended effects and time period.",
            "A justified recommendation that follows from the preceding analysis.",
        ]
    else:
        prompt = (
            f"{rule.command_word} the view that changes in {point} are the most "
            f"effective way to improve outcomes in {context_name}. Use {context} "
            "and your economic knowledge."
        )
        scheme = [
            f"Accurate knowledge and application of {topic.title}.",
            f"Developed analysis of how {point} affects incentives, behaviour and outcomes.",
            "Balanced evaluation using assumptions, time period, magnitude and alternative policies.",
            "A supported final judgement that answers the precise proposition.",
        ]
    if paper_id == "paper_3":
        scheme.extend(
            _paper_three_indicative_content(
                topic,
                context_name,
                identifier,
                values,
                point,
            )
        )
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
        authoring_context=(
            percentage_change_context(values[0], values[-1])
            if rule.kind == "calculation" else {}
        ),
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )


def _paper_three_indicative_content(
    topic: Topic,
    context_name: str,
    identifier: int,
    values: list[float],
    focus: str,
) -> list[str]:
    start, end = values[0], values[-1]
    change = ((end - start) / start) * 100
    peak = max(values)
    trough = min(values)
    first, second, *remaining = topic.points
    third = remaining[0] if remaining else first
    return [
        f"Use the change in the activity index from {start:.1f} to {end:.1f}, "
        f"equivalent to {change:.1f}%, and state whether it supports the proposition.",
        f"Compare the peak of {peak:.1f} with the trough of {trough:.1f}; the path "
        "matters because a start-to-end comparison can conceal volatility.",
        "The index shows relative change from a base year, not the absolute level of "
        "output, income, welfare or the distribution of gains.",
        f"Evidence about {context_name} should be linked directly to {focus}; a "
        "quotation without an explained economic mechanism is not application.",
        f"Define {first} accurately and identify the economic agents whose incentives "
        f"or constraints change in case {identifier}.",
        f"Analyse one channel through which {first} changes prices, output, employment "
        "or welfare, identifying each intermediate step.",
        f"Develop a separate analytical route using {second}; reward it only where it "
        "adds a distinct mechanism rather than repeating the first chain.",
        f"Consider how {third} could weaken, reinforce or delay the predicted effect in "
        f"{context_name}.",
        "Distinguish a movement along a curve from a shift of the curve and require "
        "correct axis labels, curve labels and the direction of any change.",
        "Where an aggregate-demand and aggregate-supply diagram is used, distinguish "
        "the short-run effect on real output and the price level from long-run capacity.",
        "Where a market diagram is used, distinguish private and social costs or "
        "benefits and identify the relevant equilibrium quantity.",
        "Test the importance of price and income elasticities; the direction of an "
        "effect may be clear while its size remains uncertain.",
        "Consider adjustment lags and expectations. Households and firms may respond "
        "before implementation or only after contracts and habits change.",
        "Evaluate the size and representativeness of the sample and whether an observed "
        "correlation identifies the causal effect claimed.",
        "Consider omitted variables, changes elsewhere in the economy and the "
        "possibility of reverse causation.",
        "Separate nominal from real values and totals from per-person measures whenever "
        "inflation or population change could alter the interpretation.",
        "Assess distributional effects: an improvement in the average can coexist with "
        "losses for particular income groups, regions, workers or firms.",
        "Identify the opportunity cost of the proposed intervention, including public "
        "funds, administrative resources and displaced private activity.",
        "Compare the proposal with at least one realistic alternative rather than with "
        "an unrealistic policy of doing nothing.",
        "Consider government failure, compliance costs, information requirements and "
        "unintended changes in behaviour.",
        "Separate short-run demand effects from long-run effects on productivity, "
        "participation, investment and productive capacity.",
        "A strong judgement states the conditions under which the proposal is likely "
        "to work and the evidence that would change the recommendation.",
        f"The final conclusion must answer the precise question about {context_name} "
        "and follow from the relative weight of the analysis.",
    ]


def policy_name(topic: Topic, rng: random.Random) -> str:
    return rng.choice(
        [
            f"a targeted policy addressing {rng.choice(topic.points)}",
            "a package of regulation and financial incentives",
            "direct government provision alongside market-based reform",
        ]
    )


def _build_mcq_option(
    number: int,
    topic: Topic,
    rng: random.Random,
    rule: QuestionRule,
) -> GeneratedOption:
    authoring_context: dict[str, object] = {}
    source_references: list[str] = []
    if number in PAPER3_VISUAL_QUESTION_NUMBERS:
        prompt, correct_text, raw_choices, authoring_context = _visual_mcq(
            number,
            topic,
            rng,
        )
        source_references = [f"Figure {number}"]
    elif number in {5, 15, 30}:
        base = rng.randint(55, 180)
        change = rng.choice([5, 8, 10, 12, 15, 20])
        quantum = Decimal("0.1")
        base_value = Decimal(base)
        change_rate = Decimal(change) / Decimal(100)
        if number == 5:
            operation = "index_percentage_increase"
            correct = (base_value * (Decimal(1) + change_rate)).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
            prompt = (
                f"An economic activity index is {base} and rises by {change}%. "
                "What is its new value?"
            )
            inputs = {"base": str(base), "rate_percent": str(change)}
            unit = "index"
        elif number == 15:
            operation = "index_percentage_decrease"
            correct = (base_value * (Decimal(1) - change_rate)).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
            prompt = (
                f"An economic activity index is {base} and falls by {change}%. "
                "What is its new value?"
            )
            inputs = {"base": str(base), "rate_percent": str(change)}
            unit = "index"
        else:
            operation = "index_percentage_change"
            final = (base_value * (Decimal(1) + change_rate)).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
            correct = ((final - base_value) / base_value * Decimal(100)).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
            prompt = (
                f"An economic activity index rises from {base_value:.1f} to {final:.1f}. "
                "What is the percentage change?"
            )
            inputs = {"initial": str(base_value), "final": str(final)}
            unit = "percent"
        values = [correct]
        for raw_candidate in (
            correct + Decimal("5.0"),
            correct - Decimal("5.0"),
            correct + Decimal("10.0"),
            correct - Decimal("10.0"),
        ):
            candidate = raw_candidate.quantize(quantum, rounding=ROUND_HALF_UP)
            if candidate not in values:
                values.append(candidate)
            if len(values) == 4:
                break
        while len(values) < 4:
            candidate = correct + Decimal(len(values) * 3)
            if candidate not in values:
                values.append(candidate)
        suffix = "%" if operation == "index_percentage_change" else ""
        raw_choices = [f"{value:.1f}{suffix}" for value in values]
        correct_text = f"{correct:.1f}{suffix}"
        authoring_context = {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                "inputs": inputs,
                "unit": unit,
                "decimal_places": 1,
            }
        }
    elif number in APPLIED_TOPIC_BY_NUMBER:
        prompt, correct_text, raw_choices, authoring_context = _applied_mcq(number)
    else:
        stem, correct_text, distractors = MCQ_FACTS[topic.id]
        prompt = stem
        raw_choices = [correct_text, *distractors]
    rng.shuffle(raw_choices)
    choices = raw_choices
    correct_choice = choices.index(correct_text)
    question = GeneratedQuestion(
        rule_id="mcq",
        number=str(number),
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        topic_id=topic.id,
        prompt=prompt,
        choices=choices,
        correct_choice=correct_choice,
        mark_scheme=[f"Option {'ABCD'[correct_choice]}: {correct_text}."],
        source_references=source_references,
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "low",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )
    return GeneratedOption(id=f"A{number}", title=f"Question {number}", questions=[question])


def _visual_mcq(
    number: int,
    topic: Topic,
    rng: random.Random,
) -> tuple[str, str, list[str], dict[str, object]]:
    topic_id, curve, direction, scope_id = VISUAL_SPECS[number]
    if topic.id != topic_id:
        raise ValueError("visual topic does not match its declared task")
    is_aggregate = scope_id == "aggregate"
    if is_aggregate:
        outcomes = {
            ("AD", "right"): "The price level rises and real output rises",
            ("AD", "left"): "The price level falls and real output falls",
            ("SRAS", "right"): "The price level falls and real output rises",
            ("SRAS", "left"): "The price level rises and real output falls",
            ("LRAS", "right"): "The price level falls and real output rises",
            ("LRAS", "left"): "The price level rises and real output falls",
        }
        choices = [
            "The price level rises and real output rises",
            "The price level rises and real output falls",
            "The price level falls and real output rises",
            "The price level falls and real output falls",
        ]
        x_axis = "Real output"
        y_axis = "Price level"
        scope = (
            "aggregate demand and long-run aggregate supply"
            if curve == "LRAS"
            else "aggregate demand and short-run aggregate supply"
        )
    else:
        outcomes = {
            ("D", "right"): "Equilibrium price rises and equilibrium quantity rises",
            ("D", "left"): "Equilibrium price falls and equilibrium quantity falls",
            ("S", "right"): "Equilibrium price falls and equilibrium quantity rises",
            ("S", "left"): "Equilibrium price rises and equilibrium quantity falls",
        }
        choices = [
            "Equilibrium price rises and equilibrium quantity rises",
            "Equilibrium price rises and equilibrium quantity falls",
            "Equilibrium price falls and equilibrium quantity rises",
            "Equilibrium price falls and equilibrium quantity falls",
        ]
        x_axis = "Quantity"
        y_axis = "Price"
        scope = f"demand and supply in the market for {rng.choice(INDUSTRIES)}"

    correct_text = outcomes[(curve, direction)]
    prompt = (
        f"Use Figure {number}, which shows {scope}. Which combination describes "
        "the change from the initial equilibrium to the new equilibrium?"
    )
    return (
        prompt,
        correct_text,
        list(choices),
        {
            "visual_kind": "economic_shift_diagram",
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "economic_shift",
                "inputs": {
                    "curve": curve,
                    "direction": direction,
                    "scope": "aggregate" if is_aggregate else "market",
                    "x_axis": x_axis,
                    "y_axis": y_axis,
                },
                "unit": "effect",
                "decimal_places": 0,
            },
        },
    )


def _applied_mcq(
    number: int,
) -> tuple[str, str, list[str], dict[str, object]]:
    tasks: dict[int, tuple[str, str, list[str], str, dict[str, str], str]] = {
        1: (
            "Production of product X rises from 20 to 30 units while production of "
            "product Y falls from 80 to 68 units. What is the opportunity cost of "
            "the extra 10 units of product X?",
            "12 units of product Y",
            ["12 units of product Y", "20 units of product Y", "10 units of product Y", "68 units of product Y"],
            "opportunity_cost_change",
            {"primary_before": "20", "secondary_before": "80", "primary_after": "30", "secondary_after": "68"},
            "ratio",
        ),
        3: (
            "A product's price rises from £10 to £12 and quantity demanded falls "
            "from 100 to 88 units. What happens to total expenditure?",
            "Total expenditure rises",
            ["Total expenditure rises", "Total expenditure falls", "Total expenditure is unchanged", "The effect cannot be calculated"],
            "elastic_revenue_change",
            {"price_before": "10", "quantity_before": "100", "price_after": "12", "quantity_after": "88"},
            "GBPm",
        ),
        7: (
            "The poorest group's income share rises from 20% to 25%, while the "
            "richest group's share falls from 45% to 38%. What does this evidence suggest?",
            "Income inequality falls",
            ["Income inequality falls", "Income inequality rises", "Income inequality is unchanged", "Nominal GDP must fall"],
            "income_distribution_change",
            {"poorest_share_before": "20", "richest_share_before": "45", "poorest_share_after": "25", "richest_share_after": "38"},
            "percent",
        ),
        11: (
            "The policy interest rate rises from 4% to 6%; 60% of the reported "
            "household and business spending is credit-financed. What is the most likely effect?",
            "Credit-financed consumption and investment weaken",
            ["Credit-financed consumption and investment weaken", "Credit-financed consumption and investment strengthen", "Credit-financed consumption and investment are unchanged", "All saving must cease"],
            "interest_rate_demand_change",
            {"interest_rate_before": "4", "interest_rate_after": "6", "credit_share_percent": "60"},
            "percent",
        ),
        17: (
            "After a currency depreciation, the estimated export-demand elasticity "
            "is 0.9 and the import-demand elasticity is 0.6. Which outcome is more likely?",
            "The trade balance is more likely to improve",
            ["The trade balance is more likely to improve", "The trade balance is more likely to worsen", "The trade balance must be unchanged", "Domestic output must become zero"],
            "trade_elasticity_effect",
            {"exchange_rate_direction": "depreciation", "export_elasticity": "0.9", "import_elasticity": "0.6"},
            "effect",
        ),
    }
    prompt, answer, choices, operation, inputs, unit = tasks[number]
    return (
        prompt,
        answer,
        choices,
        {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                "inputs": inputs,
                "unit": unit,
                "decimal_places": 1,
            }
        },
    )


def _stimulus(
    topic: Topic,
    context_name: str,
    identifier: int,
    values: list[float],
    rng: random.Random,
    *,
    expanded: bool,
) -> list[str]:
    first, second = rng.sample(topic.points, 2)
    share = rng.randint(18, 72)
    policy = rng.choice(
        ["a targeted tax change", "new competition rules", "a training subsidy", "an interest-rate change"]
    )
    depth = (
        [
            _case_depth(rng, context_name, topic, focus)
            for focus in (first, second, policy, f"the reliability of evidence about {first}")
        ]
        if expanded
        else [
            _case_depth(rng, context_name, topic, first, sentence_count=2),
            _case_depth(rng, context_name, topic, second, sentence_count=2),
            "",
            "",
        ]
    )
    compact_c = ""
    compact_d = ""
    if not expanded:
        sample_size = rng.randrange(900, 4200, 50)
        support = rng.randint(38, 76)
        expected_cost = rng.randint(2, 9)
        adjustment_years = rng.randint(2, 7)
        compact_c = (
            f" A survey of {sample_size:,} households and firms found that {support}% "
            f"supported the proposal, although respondents expected compliance costs to "
            f"rise by {expected_cost}%. A pilot scheme reported higher participation and "
            "investment, but the participating area was not randomly selected. One forecast "
            f"assumed that behaviour would adjust over {adjustment_years} years; another "
            "assumed an immediate response and estimated a much larger effect. The measure "
            "would also require public spending that could otherwise support infrastructure, "
            "healthcare or education."
        )
        compact_d = (
            " The headline index is a base-year measure rather than an absolute value and "
            "does not distinguish nominal from real changes. The sample excludes informal "
            "activity and may under-represent low-income households and small firms. "
            "Correlation between the policy and the outcome does not establish causation: "
            "exchange rates, energy prices and conditions in trading partners also changed. "
            "Some benefits may arise only in the long run, while adjustment costs are "
            "concentrated in the short run. Economists therefore disagree about the size, "
            "distribution and durability of the predicted effects."
        )
    return [
        (
            f"Extract A: Activity in {context_name} changed "
            f"from an index of {values[0]:.1f} to {values[-1]:.1f}. Analysts linked the movement "
            f"to {first} and changing household and firm incentives. The path was uneven: the "
            f"index reached {max(values):.1f} at its highest point and {min(values):.1f} at its "
            "lowest. This suggests that a single annual comparison may conceal important changes "
            "in capacity, confidence and the distribution of gains. Survey respondents also "
            "reported different experiences according to income, location and access to finance. "
            + depth[0]
        ),
        (
            f"Extract B: The largest participants account for {share}% of measured activity. "
            f"Some economists argue that {second} explains the observed outcome; others emphasise "
            "adjustment lags, imperfect information and differences between short-run and long-run "
            "effects. New entrants face uncertain demand and must make decisions before complete "
            "information is available. Established participants may benefit from scale, reputation "
            "or access to distribution networks. These conditions affect prices, output, employment "
            "and the extent to which changes in efficiency are passed on to households. "
            + depth[1]
        ),
        (
            f"Extract C: Policymakers are considering {policy}. The likely effects depend on "
            "elasticities, the response of expectations, administrative costs and conditions elsewhere "
            "in the economy. Supporters expect the measure to change incentives and improve long-run "
            "productive capacity. Critics argue that resources could be diverted from more effective "
            "uses and that firms or consumers may alter their behaviour in ways that reduce the "
            "policy's impact. Distributional effects may differ from the effect on total output. "
            + compact_c
            + depth[2]
        ),
        (
            f"Extract D: Reasons for caution. Evidence about {context_name} is incomplete and the "
            f"importance of {first} cannot be isolated from {second}. The index does not measure "
            "quality, unpaid activity or wider effects on wellbeing. Outcomes may also reflect global "
            "conditions rather than domestic policy. A judgement should therefore compare realistic "
            "alternatives, consider opportunity cost, distinguish short-run adjustment from long-run "
            "effects and explain who gains and who bears the cost. "
            + compact_d
            + depth[3]
        ),
    ]


def _case_depth(
    rng: random.Random,
    context_name: str,
    topic: Topic,
    focus: str,
    *,
    sentence_count: int = 7,
) -> str:
    sample_size = rng.randrange(850, 4200, 50)
    household_share = rng.randint(24, 68)
    firm_share = rng.randint(12, 55)
    lag = rng.randint(2, 8)
    region = rng.choice(["northern region", "coastal region", "capital region", "rural region"])
    sentences = [
        (
            f"A survey of {sample_size:,} households found that {household_share}% had noticed "
            f"a change connected with {focus}, although reported experiences varied considerably."
        ),
        (
            f"Businesses in the {region} were more cautious: only {firm_share}% expected the "
            "change to persist, and several reported constraints on investment or recruitment."
        ),
        (
            f"One forecast assumed an adjustment period of {lag} years, but a second forecast "
            "used faster behavioural responses and produced a substantially different result."
        ),
        (
            f"The headline average for {context_name} combines groups with different incomes, "
            "costs and access to substitutes, so it may not describe any individual group well."
        ),
        (
            f"Economists also disagreed about whether {focus} was a cause of the outcome or a "
            "response to other changes taking place at the same time."
        ),
        (
            "Some benefits are not recorded in market transactions, while some costs fall on "
            "third parties and are therefore omitted from private financial data."
        ),
        (
            "The estimates are sensitive to the chosen base year, the treatment of inflation "
            "and whether outcomes are measured in total or on a per-person basis."
        ),
        (
            f"A small pilot scheme linked to {rng.choice(topic.points)} produced an early improvement, "
            "but the participating area was not randomly selected and may not be representative."
        ),
        (
            "Expectations may change before a policy is introduced, making it difficult to separate "
            "announcement effects from the effect of the measure once it is operating."
        ),
        (
            "International comparisons should be treated cautiously because institutions, tax "
            "systems, industrial structures and the quality of recorded data are not identical."
        ),
        (
            "A distributional breakdown suggests that a rise in the overall average can occur even "
            "when a sizeable minority experiences no improvement or becomes worse off."
        ),
        (
            "Opportunity cost remains important: labour, finance and administrative capacity used "
            "here cannot simultaneously be used for other public or private priorities."
        ),
    ]
    return " ".join(rng.sample(sentences, sentence_count))


def _section_instructions(paper_id: str, section_id: str, option_count: int) -> str:
    if paper_id == "paper_3" and section_id == "A":
        return "Answer all 30 questions. For each question, select one answer."
    if paper_id == "paper_3":
        return "Answer all questions in this context."
    noun = "context" if section_id == "A" else "essay"
    return f"Answer one {noun}. You must not answer more than one of the {option_count} options."
