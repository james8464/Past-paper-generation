from __future__ import annotations

import random
import secrets

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    validate_generated_paper,
)

from aqaecongen.syllabus import Syllabus, Topic


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
            topic = shuffled_topics[topic_cursor % len(shuffled_topics)]
            topic_cursor += 1
            if section_rule.id == "A" and rule.id == "paper_3":
                option = _build_mcq_option(option_index + 1, topic, rng)
            else:
                option, question_number = _build_written_option(
                    rule,
                    section_rule.questions,
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
        else []
    )
    questions: list[GeneratedQuestion] = []
    for part_index, question_rule in enumerate(question_rules):
        if rule.id == "paper_3":
            number = str(question_number + part_index)
        else:
            number = (
                str(question_number)
                if len(question_rules) == 1
                else f"{question_number}.{part_index + 1}"
            )
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
        question_number + 1,
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
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    change = ((values[-1] - values[0]) / values[0]) * 100
    context = (
        f"the evidence about {context_name} in practice case {identifier}"
        if is_data
        else "relevant economic theory"
    )
    if rule.kind == "calculation":
        prompt = (
            f"Using the index data for {context_name} in practice case {identifier}, calculate "
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
            f"To what extent do the data in the source insert suggest that outcomes in "
            f"{context_name} in practice case {identifier} have improved?"
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
            f"Evaluate the view that changes in {point} are the most effective way to improve "
            f"outcomes in {context_name}. Use {context} and your economic knowledge."
        )
        scheme = [
            f"Accurate knowledge and application of {topic.title}.",
            f"Developed analysis of how {point} affects incentives, behaviour and outcomes.",
            "Balanced evaluation using assumptions, time period, magnitude and alternative policies.",
            "A supported final judgement that answers the precise proposition.",
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
    )


def policy_name(topic: Topic, rng: random.Random) -> str:
    return rng.choice(
        [
            f"a targeted policy addressing {rng.choice(topic.points)}",
            "a package of regulation and financial incentives",
            "direct government provision alongside market-based reform",
        ]
    )


def _build_mcq_option(number: int, topic: Topic, rng: random.Random) -> GeneratedOption:
    if number % 5 == 0:
        base = rng.randint(55, 180)
        change = rng.choice([5, 8, 10, 12, 15, 20])
        correct = round(base * (1 + change / 100), 1)
        values = [
            round(base * (1 - change / 100), 1),
            round(base + change, 1),
            correct,
            round(base * (1 + (change + 5) / 100), 1),
        ]
        raw_choices = [f"{value:.1f}" for value in values]
        prompt = (
            f"In economy {rng.choice(ECONOMIES)}, an index linked to {rng.choice(topic.points)} "
            f"is {base}. It rises by {change}%. What is the new index value?"
        )
        correct_text = f"{correct:.1f}"
    else:
        stem, correct_text, distractors = MCQ_FACTS[topic.id]
        prompt = f"Practice scenario {rng.randint(1000, 9999)}. {stem}"
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
    )
    return GeneratedOption(id=f"A{number}", title=f"Question {number}", questions=[question])


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
        else [""] * 4
    )
    return [
        (
            f"Extract A: Independent practice case {identifier}. Activity in {context_name} changed "
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
            + depth[2]
        ),
        (
            f"Extract D: Reasons for caution. Evidence about {context_name} is incomplete and the "
            f"importance of {first} cannot be isolated from {second}. The index does not measure "
            "quality, unpaid activity or wider effects on wellbeing. Outcomes may also reflect global "
            "conditions rather than domestic policy. A judgement should therefore compare realistic "
            "alternatives, consider opportunity cost, distinguish short-run adjustment from long-run "
            "effects and explain who gains and who bears the cost. All figures, organisations and "
            "economies in this practice case are fictional. "
            + depth[3]
        ),
    ]


def _case_depth(rng: random.Random, context_name: str, topic: Topic, focus: str) -> str:
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
    return " ".join(rng.sample(sentences, 7))


def _section_instructions(paper_id: str, section_id: str, option_count: int) -> str:
    if paper_id == "paper_3" and section_id == "A":
        return "Answer all 30 questions. For each question, select one answer."
    if paper_id == "paper_3":
        return "Answer all questions in this case study."
    noun = "context" if section_id == "A" else "essay"
    return f"Answer one {noun}. You must not answer more than one of the {option_count} options."
