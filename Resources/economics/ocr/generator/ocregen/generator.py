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
from Backend.Core.mark_scheme_enrichment import enrich_paper

from ocregen.syllabus import Syllabus, Topic

CONTEXTS = [
    "regional ferry services",
    "low-carbon construction",
    "digital banking",
    "urban rental housing",
    "medical diagnostics",
    "food-delivery platforms",
    "renewable electricity",
    "technical training",
]
CONTEXTS_BY_TOPIC = {
    "micro-1": ["technical training", "low-carbon construction"],
    "micro-2": ["regional ferry services", "food-delivery platforms"],
    "micro-3": ["medical diagnostics", "low-carbon construction"],
    "micro-4": ["digital banking", "food-delivery platforms"],
    "micro-5": ["technical training", "medical diagnostics"],
    "micro-6": ["renewable electricity", "urban rental housing"],
    "macro-1": ["low-carbon construction", "renewable electricity"],
    "macro-2": ["urban rental housing", "technical training"],
    "macro-3": ["renewable electricity", "low-carbon construction"],
    "macro-4": ["regional ferry services", "renewable electricity"],
    "macro-5": ["digital banking", "urban rental housing"],
}
ECONOMIES = ["Arden", "Bellmare", "Corvia", "Delsin", "Eland", "Faron", "Galen", "Helios"]
STAKEHOLDERS = [
    "households on low incomes",
    "new market entrants",
    "established producers",
    "workers with specialist skills",
    "local authorities",
    "small exporters",
]
POLICY_OPTIONS = [
    "a targeted subsidy with a fixed three-year budget",
    "a gradually rising levy accompanied by information provision",
    "competition rules supported by stronger disclosure requirements",
    "public investment financed through a mix of taxation and borrowing",
    "a time-limited regulatory standard followed by an independent review",
]
EVIDENCE_LIMITS = [
    "the sample excluded informal activity",
    "the series covered only a short period",
    "the average concealed substantial regional variation",
    "the survey measured intentions rather than completed decisions",
    "a simultaneous change in input costs made causation uncertain",
]
FACTS = {
    "micro-1": ("Which statement best describes opportunity cost?", "The next best alternative forgone", ["All money spent", "The total benefit received", "Any fixed production cost"]),
    "micro-2": ("Demand is price inelastic. What follows from a price rise?", "Total spending rises", ["Quantity demanded rises", "Supply must fall", "Total spending must fall"]),
    "micro-3": ("Where is average cost at its minimum?", "Where marginal cost equals average cost", ["Where fixed cost is zero", "Where revenue is zero", "Where price always equals zero"]),
    "micro-4": ("What makes a market more contestable?", "Low sunk costs", ["A protected monopoly", "Permanent legal entry barriers", "One seller with an exclusive patent"]),
    "micro-5": ("What may result from labour-market monopsony?", "Wages below the competitive level", ["Perfectly elastic labour demand", "No employer bargaining power", "Every worker receiving the same wage"]),
    "micro-6": ("Where is output socially efficient with an external cost?", "Where social marginal cost equals social marginal benefit", ["Where private cost is zero", "At maximum output", "Where third-party costs are ignored"]),
    "macro-1": ("What would directly increase aggregate demand?", "Higher planned investment", ["Lower productivity", "A fall in export demand", "A rise in imports with no other change"]),
    "macro-2": ("Which measure adjusts output for population and inflation?", "Real GDP per head", ["Nominal GDP", "The consumer price index", "The money supply"]),
    "macro-3": ("Which is an interventionist supply-side policy?", "Government-funded skills training", ["A rise in the policy interest rate", "A general increase in indirect tax", "A reduction in transfer payments only"]),
    "macro-4": ("When is depreciation more likely to improve net trade?", "When trade elasticities are sufficiently high", ["When all quantities are fixed", "When imports have no price", "When domestic output is zero"]),
    "macro-5": ("What is a likely short-run effect of higher interest rates?", "Weaker credit-financed spending", ["Cheaper borrowing", "An infinite money multiplier", "A guaranteed rise in asset prices"]),
}


def build_paper(rule: PaperRule, syllabus: Syllabus, seed: int | None = None) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    rng.shuffle(topics)
    sections: list[GeneratedSection] = []
    topic_cursor = 0
    for section_rule in rule.sections:
        options: list[GeneratedOption] = []
        for option_index in range(section_rule.option_count):
            topic = topics[topic_cursor % len(topics)]
            topic_cursor += 1
            if rule.id == "paper_3" and section_rule.id == "A":
                option = _mcq(option_index + 1, topic, rng)
            else:
                option = _written_option(rule, section_rule.id, option_index, topic, section_rule.questions, rng)
            options.append(option)
        instructions = _instructions(rule.id, section_rule.id)
        sections.append(GeneratedSection(id=section_rule.id, title=section_rule.title, instructions=instructions, options=options))
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


def _written_option(
    paper_rule: PaperRule,
    section_id: str,
    option_index: int,
    topic: Topic,
    rules: list[QuestionRule],
    rng: random.Random,
) -> GeneratedOption:
    case_id = rng.randint(1000, 9999)
    context = rng.choice(CONTEXTS_BY_TOPIC.get(topic.id, CONTEXTS))
    values = [float(rng.randint(70, 135))]
    for _ in range(4):
        values.append(round(values[-1] * (1 + rng.randint(-8, 13) / 100), 1))
    if paper_rule.id == "paper_3":
        title = f"Synoptic theme: {context.title()}"
        stimulus = [_extract(topic, context, case_id, rng, index) for index in range(1, 4)]
        numbers = [str(31 + index) for index in range(len(rules))]
    elif section_id == "A":
        title = f"Question 1: {context.title()}"
        stimulus = [_extract(topic, context, case_id, rng, index) for index in range(1, 4)]
        if paper_rule.id == "paper_1":
            numbers = ["1(a)", "1(b)", "1(c)(i)", "1(c)(ii)", "1(d)", "1(e)"]
        else:
            numbers = [f"1({chr(97 + index)})" for index in range(len(rules))]
    else:
        base = 2 if section_id == "B" else 4
        number = base + option_index
        title = f"Question {number}"
        stimulus = []
        numbers = [str(number)]
    questions = [
        _question(rule, number, topic, context, case_id, values, rng)
        for rule, number in zip(rules, numbers, strict=True)
    ]
    return GeneratedOption(
        id=f"{section_id}{option_index + 1}",
        title=title,
        stimulus=stimulus,
        chart_title=f"Index for {context} (base = 100)",
        chart_labels=[str(2021 + index) for index in range(5)],
        chart_values=values if stimulus else [],
        questions=questions,
    )


def _question(
    rule: QuestionRule,
    number: str,
    topic: Topic,
    context: str,
    case_id: int,
    values: list[float],
    rng: random.Random,
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    evidence = f"the extracts about {context}"
    change = (values[-1] - values[0]) / values[0] * 100
    if rule.kind == "calculation":
        prompt = f"Using the data in {evidence}, calculate the percentage change in the index. Give your answer to one decimal place."
        mark_label = "mark" if rule.marks == 1 else "marks"
        scheme = [
            f"Valid method using {values[0]} and {values[-1]}.",
            f"Correct answer: {change:.1f}%.",
            f"Maximum {rule.marks} {mark_label}.",
        ]
    elif rule.kind == "short_answer" and rule.command_word == "Identify":
        prompt = f"Using {evidence}, identify two features relevant to {point}."
        scheme = ["One mark for each valid feature supported by the stimulus."]
    elif rule.kind == "short_answer":
        prompt = f"Explain what is meant by '{point}'."
        scheme = [f"Accurate explanation of {point}.", "Accept an equivalent economic definition."]
    elif rule.kind == "diagram_analysis":
        prompt = f"Explain, using an appropriate diagram, how a change in {point} could affect {context}."
        scheme = ["Correct axes, curves and initial equilibrium.", "Relevant shift and new equilibrium.", "Coherent explanation linked to the context."]
    elif rule.kind == "data_response":
        if rule.id == "relationship_3":
            prompt = (
                f"Explain whether the relationship shown in Figure 1 of {evidence} is the "
                f"expected one, with reference to {point}."
            )
        elif rule.id == "relationship_4":
            prompt = (
                f"Using Figure 1 in {evidence}, explain the relationship between the index "
                f"and the evidence in the extracts, and relate it to {point}."
            )
        elif rule.id.startswith("extract_"):
            extract_number = rule.id.split("_")[1]
            figure_number = f"{extract_number}.1"
            verb = "compare" if rule.command_word == "Compare" else "explain"
            prompt = (
                f"Using Figure {figure_number}, {verb} the changes shown and relate them to "
                f"{point}."
            )
        else:
            verb = "compare" if rule.command_word == "Compare" else "explain"
            prompt = f"Using the data in {evidence}, {verb} the observed changes and relate them to {point}."
        scheme = ["Accurate use of at least two data points.", f"Developed economic reasoning involving {point}.", "Recognition of the limits of the comparison."]
    elif rule.kind == "essay":
        prompt = f"Evaluate, using an appropriate diagram where relevant, the impact of {point} on {topic.title.lower()}."
        scheme = _evaluation_scheme(topic, point, rule.marks)
    else:
        if rule.id.startswith("extract_"):
            extract_number = rule.id.split("_")[1]
            prompt = (
                f"Evaluate, using the information in Extract {extract_number}, whether {point} "
                f"is the main influence on outcomes in {context}."
            )
        elif rule.id == "evaluation_8":
            prompt = (
                f"Evaluate, using evidence from {evidence}, the effectiveness of a policy "
                f"designed to change {point}."
            )
        else:
            prompt = (
                f"Evaluate, using evidence from {evidence}, the extent to which {point} is the "
                "main influence on outcomes."
            )
        scheme = _evaluation_scheme(topic, point, rule.marks)
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


def _evaluation_scheme(topic: Topic, point: str, marks: int) -> list[str]:
    level_bands = {
        25: [
            "Level 5 (21–25): precise knowledge, consistently developed contextual analysis, sustained evaluation and a fully supported judgement.",
            "Level 4 (16–20): good knowledge, developed analysis, relevant evaluation and a supported judgement, with minor imbalance or omission.",
            "Level 3 (11–15): sound knowledge and some developed analysis; evaluation is present but partial or not consistently contextual.",
            "Level 2 (6–10): limited knowledge with short chains of reasoning; evaluation is asserted or weakly supported.",
            "Level 1 (1–5): isolated relevant points with little economic reasoning and no supported judgement.",
        ],
        15: [
            "Level 4 (13–15): accurate contextual knowledge, developed analysis, balanced evaluation and a supported judgement.",
            "Level 3 (10–12): good knowledge and linked analysis; evaluation is relevant but may be uneven.",
            "Level 2 (7–9): some accurate knowledge and analysis; evaluation is limited or generic.",
            "Level 1 (1–6): fragmentary knowledge, undeveloped reasoning or unsupported assertions.",
        ],
        12: [
            "Level 4 (10–12): accurate contextual knowledge, developed analysis, balanced evaluation and a supported judgement.",
            "Level 3 (7–9): good knowledge and linked analysis; evaluation is relevant but may be uneven.",
            "Level 2 (4–6): some accurate knowledge and analysis; evaluation is limited or generic.",
            "Level 1 (1–3): fragmentary knowledge, undeveloped reasoning or unsupported assertions.",
        ],
        8: [
            "Level 4 (7–8): accurate application, developed analysis, relevant evaluation and a concise supported judgement.",
            "Level 3 (5–6): good application with linked analysis and some evaluation.",
            "Level 2 (3–4): some relevant knowledge and a short analytical chain; evaluation is limited.",
            "Level 1 (1–2): isolated relevant points or unsupported assertions.",
        ],
    }
    return [
        f"Accurate knowledge and application of {topic.title}.",
        f"Developed analysis of {point} through incentives, behaviour and outcomes.",
        "Evaluation of assumptions, magnitude, time period, distribution and alternatives.",
        "A supported judgement that answers the precise question.",
        *level_bands[marks],
        "Level 0 (0): no creditworthy material.",
    ]


def _mcq(number: int, topic: Topic, rng: random.Random) -> GeneratedOption:
    if number % 5 == 0:
        base = rng.randint(60, 180)
        rate = rng.choice([5, 8, 10, 12, 15])
        correct = f"{base * (1 + rate / 100):.1f}"
        distractor_values = [
            base + rate,
            base * (1 - rate / 100),
            base * (1 + (rate + 5) / 100),
            base / (1 + rate / 100),
        ]
        distractors: list[str] = []
        for value in distractor_values:
            rendered = f"{value:.1f}"
            if rendered != correct and rendered not in distractors:
                distractors.append(rendered)
        while len(distractors) < 3:
            rendered = f"{base + rate + len(distractors) + 1:.1f}"
            if rendered != correct and rendered not in distractors:
                distractors.append(rendered)
        choices = [correct, *distractors[:3]]
        prompt = (
            f"Analysts in {rng.choice(ECONOMIES)} use an index to monitor {rng.choice(topic.points)}. "
            f"The index is {base} and then rises by {rate}% while all other measurement conventions "
            "remain unchanged. What is its new value?"
        )
    else:
        stem, correct, distractors = FACTS[topic.id]
        choices = [correct, *distractors]
        context = rng.choice(CONTEXTS if topic.component == 1 else ECONOMIES)
        prompt = (
            f"The following scenario concerns {context}, where decision-makers "
            f"are assessing {rng.choice(topic.points)} after new evidence changed expected costs and "
            f"benefits by an estimated {number + 2}%. {stem}"
        )
    rng.shuffle(choices)
    answer = choices.index(correct)
    question = GeneratedQuestion(
        rule_id="mcq", number=str(number), marks=1, kind="multiple_choice",
        command_word="Select", topic_id=topic.id, prompt=prompt, choices=choices,
        correct_choice=answer, mark_scheme=[f"Option {'ABCD'[answer]}: {correct}."],
    )
    return GeneratedOption(id=f"A{number}", title=f"Question {number}", questions=[question])


def _extract(topic: Topic, context: str, case_id: int, rng: random.Random, index: int) -> str:
    focus = topic.points[(index - 1) % len(topic.points)]
    share = rng.randint(18, 76)
    years = rng.randint(2, 7)
    start_index = rng.randint(82, 126)
    end_index = round(start_index * (1 + rng.randint(-9, 17) / 100), 1)
    stakeholder = rng.choice(STAKEHOLDERS)
    second_stakeholder = rng.choice([item for item in STAKEHOLDERS if item != stakeholder])
    policy = rng.choice(POLICY_OPTIONS)
    limitation = rng.choice(EVIDENCE_LIMITS)
    response = rng.choice(
        [
            "changed purchases sooner than firms changed production",
            "became more price-sensitive as substitutes entered the market",
            "revised investment plans only after borrowing conditions changed",
            "responded differently according to income, information and access to credit",
        ]
    )
    measure = {
        "micro-1": "output per unit of scarce land and skilled labour",
        "micro-2": "the average price and number of transactions",
        "micro-3": "average cost, revenue and operating profit",
        "micro-4": "market share and the rate of new entry",
        "micro-5": "vacancy rates, employment and median hourly pay",
        "micro-6": "emissions, consumption and third-party costs",
        "macro-1": "real output, investment and spare capacity",
        "macro-2": "real income per head, inflation and employment",
        "macro-3": "government borrowing and productive capacity",
        "macro-4": "export volumes, import expenditure and the exchange rate",
        "macro-5": "lending, arrears and the cost of credit",
    }.get(topic.id, "the main activity index")
    return (
        f"Extract {index}: {context.title()}. The available evidence concerns {focus}. "
        f"An index of {measure} changed from {start_index} to {end_index}. The four largest "
        f"participants accounted for {share}% of recorded activity. Over the same period, households "
        f"and firms {response}. The effect was strongest for {stakeholder}; {second_stakeholder} "
        "experienced a different balance of costs and benefits. "
        f"<br/><br/>Researchers linked the movement to {topic.points[index % len(topic.points)]}. "
        "They reported changes in price, output, quality and investment rather than assuming that "
        "every participant responded in the same way. Expectations were important: a movement "
        f"expected to last more than {years} years produced a larger response than a temporary one. "
        f"However, {limitation}. The figures therefore show an association, not proof of causation. "
        f"<br/><br/>Policy-makers considered {policy}. Supporters predicted stronger incentives and "
        "more efficient resource allocation. Critics expected administrative costs, avoidance and "
        "unequal regional effects. The outcome would depend on elasticities, opportunity cost, the "
        "time period and the response of affected groups."
    )


def _instructions(paper_id: str, section_id: str) -> str:
    if paper_id == "paper_3" and section_id == "A":
        return "Answer all 30 questions. Select one answer for each question."
    if paper_id == "paper_3":
        return "Answer all questions. Use the three extracts and figures where instructed."
    if section_id == "A":
        return "Answer all parts of Question 1."
    return "Answer one question from this section. Write the chosen question number clearly."
