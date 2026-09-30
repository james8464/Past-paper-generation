from __future__ import annotations

import random
import re
import secrets
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from aqaecongen.configs import PAPER3_VISUAL_QUESTION_NUMBERS
from aqaecongen.level_policy import level_guidance
from aqaecongen.syllabus import Syllabus, Topic
from aqaecongen.written_tasks import WrittenTaskProfile, profile_for
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    MarkSchemePoint,
    PaperRule,
    QuestionRule,
    resolve_question_rules,
    validate_generated_paper,
)
from Backend.Core.mark_scheme_enrichment import enrich_paper
from Backend.Core.numeric_integrity import percentage_change_context
from Backend.Core.subjects.selected_response import (
    selected_response_contract,
    solve_selected_response,
)


class _AppliedSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OpportunityCostSource(_AppliedSource):
    operation: Literal["opportunity_cost_change"] = "opportunity_cost_change"
    primary_before: Decimal
    secondary_before: Decimal
    primary_after: Decimal
    secondary_after: Decimal


class ElasticRevenueSource(_AppliedSource):
    operation: Literal["elastic_revenue_change"] = "elastic_revenue_change"
    price_before: Decimal
    quantity_before: Decimal
    price_after: Decimal
    quantity_after: Decimal


class IncomeDistributionSource(_AppliedSource):
    operation: Literal["income_distribution_change"] = "income_distribution_change"
    poorest_share_before: Decimal
    richest_share_before: Decimal
    poorest_share_after: Decimal
    richest_share_after: Decimal


class InterestRateSource(_AppliedSource):
    operation: Literal["interest_rate_demand_change"] = "interest_rate_demand_change"
    interest_rate_before: Decimal
    interest_rate_after: Decimal
    credit_share_percent: Decimal


class TradeElasticitySource(_AppliedSource):
    operation: Literal["trade_elasticity_effect"] = "trade_elasticity_effect"
    exchange_rate_direction: Literal["depreciation"] = "depreciation"
    export_elasticity: Decimal
    import_elasticity: Decimal


AppliedMCQSource = (
    OpportunityCostSource
    | ElasticRevenueSource
    | IncomeDistributionSource
    | InterestRateSource
    | TradeElasticitySource
)


class AppliedMCQProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt: str
    choices: list[str]
    correct_choice: int
    authoring_context: dict[str, object]


APPLIED_SOURCE_BY_NUMBER: dict[int, AppliedMCQSource] = {
    1: OpportunityCostSource(
        primary_before=20,
        secondary_before=80,
        primary_after=30,
        secondary_after=68,
    ),
    3: ElasticRevenueSource(
        price_before=10,
        quantity_before=100,
        price_after=12,
        quantity_after=88,
    ),
    7: IncomeDistributionSource(
        poorest_share_before=20,
        richest_share_before=45,
        poorest_share_after=25,
        richest_share_after=38,
    ),
    11: InterestRateSource(
        interest_rate_before=4,
        interest_rate_after=6,
        credit_share_percent=60,
    ),
    17: TradeElasticitySource(export_elasticity=Decimal("0.9"), import_elasticity=Decimal("0.6")),
}

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
WRITTEN_CONTEXTS_BY_TOPIC = {
    "4.1.1": ECONOMIES,
    "4.1.2": [
        "retail financial services",
        "mobile payment platforms",
        "private dental care",
        "household energy contracts",
    ],
    "4.1.3": INDUSTRIES,
    "4.1.4": INDUSTRIES,
    "4.1.5": INDUSTRIES,
    "4.1.6": INDUSTRIES,
    "4.1.7": ECONOMIES,
    "4.1.8": INDUSTRIES,
    **{f"4.2.{index}": ECONOMIES for index in range(1, 7)},
}
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
VISUAL_CONTEXTS = {
    2: "stronger consumer confidence raises spending in a product market",
    4: "a close substitute reduces demand for an industry's output",
    9: "a productivity improvement lowers firms' unit costs in a product market",
    10: "a rise in imported-material costs raises firms' unit costs in a product market",
    13: "higher household and business expenditure expands economy-wide spending",
    14: "tighter credit conditions reduce household and business expenditure",
    19: "lower energy costs reduce economy-wide production costs in the short run",
    20: "a supply disruption raises economy-wide production costs in the short run",
    24: "investment in skills and infrastructure raises the economy's productive capacity",
    25: "storm damage reduces the economy's productive capacity",
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
                answer_options=section_rule.answer_options,
                candidate_marks=section_rule.candidate_marks,
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
    context_name = rng.choice(WRITTEN_CONTEXTS_BY_TOPIC[topic.id])
    task_profile = profile_for(topic.id)
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
            task_profile=task_profile,
        )
        if is_data
        else [
            (
                f"A fictional case in {context_name} provides the following evidence: "
                f"{task_profile.source_evidence} The analytical and policy implications "
                "depend on the assumptions identified in the questions."
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
                task_profile=task_profile,
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
    task_profile: WrittenTaskProfile,
) -> GeneratedQuestion:
    point = task_profile.focus_terms[0]
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
            "Assess the extent to which the data in the source insert support the "
            f"claim that {task_profile.data_mechanism} in {context_name}."
        )
        scheme = [
            f"Define the relevant concept: {task_profile.focus_terms[0]}.",
            "Compare at least two relevant indicators from the source insert, quoting values and directions accurately.",
            "Analyse why the indicators measure different dimensions and may give conflicting signals.",
            f"Reach a supported judgement about whether {task_profile.data_mechanism}.",
        ]
    elif rule.marks <= 10:
        if rule.kind == "diagram_analysis":
            diagram = task_profile.diagram_contract
            prompt = (
                "With the help of a correctly labelled diagram and using "
                f"{context}, explain how {diagram['cause']} is likely to affect "
                f"{task_profile.focus_terms[0]} in {context_name}."
            )
            scheme = [
                f"Define and apply {point} to the evidence about {context_name}.",
                f"Show {diagram['effect']}.",
                "Award the top level only when axes, curves, both equilibria and the direction of change are accurate and used in the explanation.",
                "Develop a causal chain from the stated change through the diagram to the final economic effect.",
            ]
        else:
            prompt = (
                f"Using {context}, explain how {task_profile.data_mechanism} in {context_name}."
            )
            scheme = [
                f"Define {point} accurately.",
                f"Use a precise item of evidence about {context_name} rather than merely naming the context.",
                f"Develop the economic mechanism: {task_profile.data_mechanism}.",
            ]
    elif rule.marks <= 15:
        prompt = task_profile.analysis_prompt
        scheme = [
            *task_profile.analysis_points,
            "Credit a relevant diagram or numerical example only when it advances the analytical chain.",
        ]
    elif rule.command_word == "Recommend":
        prompt = (
            f"After considering Extract D and the evidence in Extracts A, B and C, would you "
            f"recommend {task_profile.recommendation} for {context_name}? "
            "Justify your recommendation."
        )
        scheme = [
            *task_profile.evaluation_points,
            f"A justified recommendation on {task_profile.recommendation} that follows from the preceding analysis.",
        ]
    else:
        proposition = task_profile.evaluation_view.split(" ", 1)[1]
        prompt = (
            f"{rule.command_word} {proposition} Use {context} and your economic knowledge."
        )
        scheme = [
            *task_profile.evaluation_points,
            "A supported final judgement that answers the precise proposition in the question.",
        ]
    if rule.marks in {9, 10, 15, 25}:
        scheme.extend(level_guidance(rule.marks))
    if paper_id == "paper_3":
        scheme.extend(
            _paper_three_indicative_content(
                topic,
                context_name,
                identifier,
                values,
                point,
                include_evaluation=rule.marks >= 20,
            )
        )
    matched_focus_terms = [
        term for term in task_profile.focus_terms if term.casefold() in prompt.casefold()
    ]
    if not matched_focus_terms and rule.kind == "diagram_analysis":
        matched_focus_terms = [task_profile.diagram_contract["cause"]]
    if not matched_focus_terms and rule.kind in {"data_response", "data_interpretation"}:
        matched_focus_terms = [task_profile.data_mechanism]
    if not matched_focus_terms:
        stopwords = {
            "considering",
            "economic",
            "economy",
            "explain",
            "evaluate",
            "discuss",
            "recommend",
            "relevant",
        }
        matched_focus_terms = [
            word
            for word in re.findall(r"[A-Za-z][A-Za-z-]{6,}", prompt)
            if word.casefold() not in stopwords
        ][:1]
    authoring_context = {
        **(
            percentage_change_context(values[0], values[-1])
            if rule.kind == "calculation"
            else {}
        ),
        **(
            {"level_policy_id": f"aqa-economics-{rule.marks}-mark"}
            if rule.marks in {9, 10, 15, 25}
            else {}
        ),
    }
    if rule.marks >= 4:
        authoring_context.update(
            {
                "item_specific_mark_scheme": True,
                "task_focus_terms": matched_focus_terms,
                "required_prompt_terms": matched_focus_terms,
                "observable_mark_points": list(scheme),
            }
        )
    if rule.kind == "diagram_analysis":
        authoring_context.update(
            {
                "written_diagram_contract": dict(task_profile.diagram_contract),
                "required_prompt_terms": [
                    task_profile.diagram_contract["cause"],
                    "diagram",
                ],
            }
        )
    structured_mark_scheme = (
        _item_specific_scheme(scheme, rule)
        if rule.marks >= 4
        else []
    )
    if structured_mark_scheme:
        authoring_context["observable_mark_points"] = [
            point.text for point in structured_mark_scheme if point.marks > 0
        ]
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
        structured_mark_scheme=structured_mark_scheme,
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )


def _item_specific_scheme(
    scheme: list[str],
    rule: QuestionRule,
) -> list[MarkSchemePoint]:
    guidance_prefixes = (
        "award ",
        "credit ",
        "do not ",
        "level ",
        "levels-based",
        "marker check",
    )
    content_indices = [
        index
        for index, text in enumerate(scheme)
        if not text.casefold().startswith(guidance_prefixes)
    ]
    objectives = list(rule.assessment_objectives.items())
    if len(content_indices) < len(objectives):
        raise ValueError(
            f"{rule.id} has fewer item-specific marking routes than objectives"
        )
    allocation = {
        content_indices[index]: (objective, marks)
        for index, (objective, marks) in enumerate(objectives)
    }
    points: list[MarkSchemePoint] = []
    for index, text in enumerate(scheme):
        lowered = text.casefold()
        if lowered.startswith(("level ", "levels-based")):
            credit_type = "level"
        elif lowered.startswith(guidance_prefixes):
            credit_type = "guidance"
        else:
            credit_type = "point"
        objective, marks = allocation.get(index, (None, 0))
        points.append(
            MarkSchemePoint(
                text=text,
                marks=marks,
                credit_type=credit_type,
                assessment_objective=objective,
            )
        )
    return points


def _paper_three_indicative_content(
    topic: Topic,
    context_name: str,
    identifier: int,
    values: list[float],
    focus: str,
    *,
    include_evaluation: bool,
) -> list[str]:
    start, end = values[0], values[-1]
    change = ((end - start) / start) * 100
    peak = max(values)
    trough = min(values)
    first, second, *remaining = topic.points
    third = remaining[0] if remaining else first
    analysis = [
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
        "Distinguish a movement along a curve from a shift of the curve and require "
        "correct axis labels, curve labels and the direction of any change.",
        "Where an aggregate-demand and aggregate-supply diagram is used, distinguish "
        "the short-run effect on real output and the price level from long-run capacity.",
        "Where a market diagram is used, distinguish private and social costs or "
        "benefits and identify the relevant equilibrium quantity.",
    ]
    if not include_evaluation:
        return analysis
    return [
        *analysis,
        f"Consider how {third} could weaken, reinforce or delay the predicted effect in "
        f"{context_name}.",
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
    context = VISUAL_CONTEXTS[number]
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
        f"Figure {number} shows {context} in {scope}. Using the diagram, which "
        "combination describes the movement from the initial to the new equilibrium?"
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
    try:
        source = APPLIED_SOURCE_BY_NUMBER[number]
    except KeyError as error:
        raise ValueError(f"missing applied candidate source for question {number}") from error
    projection = project_applied_mcq(source)
    return (
        projection.prompt,
        projection.choices[projection.correct_choice],
        list(projection.choices),
        dict(projection.authoring_context),
    )


def project_applied_mcq(source: AppliedMCQSource) -> AppliedMCQProjection:
    """Project one typed source into candidate text, options and checked key."""
    values = source.model_dump(mode="json", exclude={"operation"})
    contract = selected_response_contract(source.operation, inputs=values)

    if isinstance(source, OpportunityCostSource):
        gain = source.primary_after - source.primary_before
        loss = source.secondary_before - source.secondary_after
        prompt = (
            f"Production of product X rises from {_source_number(source.primary_before)} "
            f"to {_source_number(source.primary_after)} units while production of product "
            f"Y falls from {_source_number(source.secondary_before)} to "
            f"{_source_number(source.secondary_after)} units. What is the opportunity "
            f"cost of the extra {_source_number(gain)} units of product X?"
        )
        candidates = [loss, gain, source.secondary_after, source.primary_after]
        choices = [f"{_source_number(value)} units of product Y" for value in candidates]
    elif isinstance(source, ElasticRevenueSource):
        prompt = (
            f"A product's price changes from £{_source_number(source.price_before)} "
            f"to £{_source_number(source.price_after)} and quantity demanded changes "
            f"from {_source_number(source.quantity_before)} to "
            f"{_source_number(source.quantity_after)} units. What happens to total "
            "expenditure?"
        )
        choices = [
            "Total expenditure rises",
            "Total expenditure falls",
            "Total expenditure is unchanged",
            "The effect cannot be calculated",
        ]
    elif isinstance(source, IncomeDistributionSource):
        prompt = (
            "The poorest group's income share changes from "
            f"{_source_number(source.poorest_share_before)}% to "
            f"{_source_number(source.poorest_share_after)}%, while the richest group's "
            f"share changes from {_source_number(source.richest_share_before)}% to "
            f"{_source_number(source.richest_share_after)}%. What does this evidence "
            "suggest?"
        )
        choices = [
            "Income inequality falls",
            "Income inequality rises",
            "Income inequality is unchanged",
            "Nominal GDP must fall",
        ]
    elif isinstance(source, InterestRateSource):
        prompt = (
            f"The policy interest rate changes from "
            f"{_source_number(source.interest_rate_before)}% to "
            f"{_source_number(source.interest_rate_after)}%; "
            f"{_source_number(source.credit_share_percent)}% of the reported household "
            "and business spending is credit-financed. What is the most likely effect?"
        )
        choices = [
            "Credit-financed consumption and investment weaken",
            "Credit-financed consumption and investment strengthen",
            "Credit-financed consumption and investment are unchanged",
            "All saving must cease",
        ]
    elif isinstance(source, TradeElasticitySource):
        prompt = (
            f"After a currency {source.exchange_rate_direction}, the estimated "
            f"export-demand elasticity is {_source_number(source.export_elasticity)} "
            "and the import-demand elasticity is "
            f"{_source_number(source.import_elasticity)}. Which outcome is more likely?"
        )
        choices = [
            "The trade balance is more likely to improve",
            "The trade balance is more likely to worsen",
            "The trade balance is unlikely to change from the elasticity condition alone",
            "Domestic output must become zero",
        ]
    else:  # pragma: no cover - the union is closed above
        raise TypeError("unsupported applied candidate source")

    if len(set(choices)) != 4:
        raise ValueError("applied source projection produced duplicate choices")
    item = {
        "id": f"applied-{source.operation}",
        "marks": 1,
        "kind": "multiple_choice",
        "prompt": prompt,
        "choices": choices,
        "authoring_context": {"selected_response_contract": contract},
    }
    if isinstance(source, OpportunityCostSource):
        # The model can reword the task, but these names also identify the
        # immutable choices. Renaming only the stem makes them ambiguous.
        item["authoring_context"]["required_prompt_terms"] = ["product X", "product Y"]
    solution = solve_selected_response(item)
    if solution is None or solution["answer"] not in choices:
        raise ValueError("applied source projection could not derive one checked key")
    return AppliedMCQProjection(
        prompt=prompt,
        choices=choices,
        correct_choice=choices.index(solution["answer"]),
        authoring_context=item["authoring_context"],
    )


def _source_number(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _stimulus(
    topic: Topic,
    context_name: str,
    identifier: int,
    values: list[float],
    rng: random.Random,
    *,
    expanded: bool,
    task_profile: WrittenTaskProfile,
) -> list[str]:
    sample_size = rng.randrange(900, 4200, 50)
    support = rng.randint(38, 76)
    expected_cost = rng.randint(2, 9)
    adjustment_years = rng.randint(2, 7)
    depth_count = 6 if expanded else 2
    depth = [
        _evidence_depth(
            rng,
            context_name,
            focus,
            sentence_count=depth_count,
        )
        for focus in (
            task_profile.focus_terms[0],
            task_profile.data_mechanism,
            task_profile.recommendation,
            "the reliability of the evidence",
        )
    ]
    return [
        (
            f"Extract A: Evidence for case {identifier}. The activity index for {context_name} "
            f"changed from {values[0]:.1f} in 2024 to {values[-1]:.1f} in 2028. It reached "
            f"{max(values):.1f} at its highest point and {min(values):.1f} at its lowest. "
            f"The case concerns {topic.title.lower()}. {task_profile.source_evidence} "
            "The index records relative activity rather than welfare and does not show how "
            "the change is distributed between groups. "
            + depth[0]
        ),
        (
            f"Extract B: Economic mechanism. Economists investigating {context_name} propose "
            f"the following chain: {task_profile.data_mechanism}. This claim must be supported "
            "by the direction and scale of the data, not by correlation alone. Its strength "
            "depends on the responses of the relevant households, firms, workers or government, "
            "and on whether the adjustment occurs in the short run or the long run. "
            + depth[1]
        ),
        (
            f"Extract C: Policy proposal. Policymakers are considering {task_profile.recommendation}. "
            f"A survey of {sample_size:,} affected people and organisations found that {support}% "
            f"supported the proposal, although respondents expected implementation costs to rise "
            f"by {expected_cost}%. One forecast assumed adjustment over {adjustment_years} years; "
            "another assumed an immediate response and estimated a larger effect. The proposal "
            "uses finance and administrative capacity that cannot be used for other priorities. "
            + depth[2]
        ),
        (
            f"Extract D: Reasons for caution. The evidence for {context_name} is incomplete. "
            "The headline index is a base-year measure, not an absolute level, and may conceal "
            "differences between nominal and real changes or between totals and per-person values. "
            "The sample may omit informal activity and under-represent some affected groups. "
            "Other economic changes occurred at the same time, so the observed association does "
            "not by itself establish causation. A judgement should compare realistic alternatives, "
            "opportunity costs, time periods and distributional effects. "
            + depth[3]
        ),
    ]


def _evidence_depth(
    rng: random.Random,
    context_name: str,
    focus: str,
    *,
    sentence_count: int,
) -> str:
    sample_size = rng.randrange(850, 4200, 50)
    household_share = rng.randint(24, 68)
    lag = rng.randint(2, 8)
    region = rng.choice(["northern region", "coastal region", "capital region", "rural region"])
    sentences = [
        (
            f"A survey of {sample_size:,} households found that {household_share}% had noticed "
            f"a change connected with {focus}, although reported experiences varied considerably."
        ),
        f"Evidence from the {region} differed from the national average, which may limit generalisation.",
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
            "Some relevant benefits or costs are not recorded in market transactions and are "
            "therefore omitted from the headline data."
        ),
        (
            "The estimates are sensitive to the chosen base year, the treatment of inflation "
            "and whether outcomes are measured in total or on a per-person basis."
        ),
        (
            f"A small pilot linked to {focus} produced an early change, but its participants "
            "were not randomly selected and may not be representative."
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
