from __future__ import annotations

import random
import secrets
from decimal import ROUND_HALF_UP, Decimal

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
ANALYTICAL_FACTS = {
    "micro-1": ("A region moves skilled workers from clinics to housebuilding. Which chain best explains the opportunity cost?", "Clinic output falls because the same scarce workers cannot produce both services", ["Both outputs rise because scarcity has ended", "Only money wages are an opportunity cost", "The forgone clinic output is irrelevant once houses are built"]),
    "micro-2": ("A firm raises price by 6% and quantity demanded falls by 2%. Which conclusion is supported?", "Demand is price inelastic, so total spending rises", ["Demand is price elastic, so total spending rises", "Supply must have shifted left by 4%", "Total spending falls because quantity demanded falls"]),
    "micro-3": ("A firm's marginal cost is below its average cost. Which effect follows while that remains true?", "The next units pull average cost down", ["Average cost must rise", "Fixed cost rises with each unit", "Revenue must equal zero"]),
    "micro-4": ("New firms can enter without large unrecoverable expenditure. Which chain best explains the effect?", "Low sunk costs make entry and exit more credible, increasing contestability", ["Low sunk costs create a legal monopoly", "Entry becomes impossible because fixed costs are low", "Contestability falls because customers have more choice"]),
    "micro-5": ("One employer buys most local specialist labour. Which chain is most likely?", "Employer buying power can hold wages and employment below competitive levels", ["Workers necessarily receive higher wages", "Labour demand becomes perfectly elastic", "Employer bargaining power disappears"]),
    "micro-6": ("A producer ignores pollution damage. Which rule identifies the efficient output?", "Choose output where social marginal benefit equals social marginal cost", ["Choose maximum output because private cost is lower", "Choose output where pollution is unpriced", "Choose zero private marginal cost"]),
    "macro-1": ("Firms increase planned investment while other AD components are unchanged. Which chain follows first?", "Aggregate demand rises, increasing real output in the short run when spare capacity exists", ["Aggregate demand falls because investment is an injection", "Long-run aggregate supply must fall immediately", "Imports fall to zero"]),
    "macro-2": ("Nominal GDP rises while prices and population also rise. Which measure best tests whether average material living standards improved?", "Real GDP per head", ["Nominal GDP alone", "The price index alone", "The money supply alone"]),
    "macro-3": ("Government funds vocational training for workers lacking relevant skills. Which chain is most plausible?", "Skills and productivity can rise, shifting productive capacity right over time", ["Aggregate supply must fall immediately", "Training is a contractionary monetary policy", "Productive capacity is unchanged by skills"]),
    "macro-4": ("A currency depreciates and export and import demand are price elastic. Which chain is most plausible after adjustment?", "Trade volumes respond sufficiently for net trade to improve", ["Quantities remain fixed by definition", "Import prices fall in domestic currency", "Depreciation guarantees an immediate improvement regardless of elasticities"]),
    "macro-5": ("A central bank raises interest rates. Which transmission chain is most plausible?", "Borrowing costs rise, weakening credit-financed consumption and investment", ["Borrowing becomes cheaper and spending rises", "The money multiplier becomes infinite", "Every asset price must rise"]),
}
ALTERNATE_FACTS = {
    "micro-1": ("Which statement distinguishes a free good from an economic good?", "A free good has no opportunity cost at the point of use", ["A free good must have a money price", "An economic good is unlimited", "Scarcity is irrelevant to economic goods"]),
    "micro-2": ("What causes a movement along a demand curve?", "A change in the product's own price", ["A change in consumer income", "A change in the price of a substitute", "A change in tastes"]),
    "micro-3": ("Which expression defines profit?", "Total revenue minus total cost", ["Total cost minus fixed cost", "Average revenue plus marginal cost", "Fixed cost minus variable cost"]),
    "micro-4": ("Which feature is a barrier to entry?", "A legally protected patent", ["Low sunk costs", "Easy access to distribution", "Perfect information for entrants"]),
}
_OCR_TOPIC_IDS = [
    "micro-1", "micro-2", "micro-3", "micro-4", "micro-5", "micro-6",
    "macro-1", "macro-2", "macro-3", "macro-4", "macro-5",
]
_OCR_RETRIEVAL_TOPICS = {
    number: _OCR_TOPIC_IDS[index % len(_OCR_TOPIC_IDS)]
    for index, number in enumerate((2, 4, 6, 8, 11, 12, 14, 16, 18, 21, 22, 24, 26, 27, 29))
}
_OCR_ALTERNATE_NUMBERS = {24, 26, 27, 29}
_OCR_ANALYTICAL_TOPICS = {
    number: _OCR_TOPIC_IDS[index]
    for index, number in enumerate((1, 3, 7, 9, 13, 17, 19, 23, 28))
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
            question_rules = resolve_question_rules(section_rule, option_index + 1)
            topic = topics[topic_cursor % len(topics)]
            topic_cursor += 1
            if rule.id == "paper_3" and section_rule.id == "A":
                number = option_index + 1
                topic_id = _OCR_RETRIEVAL_TOPICS.get(number) or _OCR_ANALYTICAL_TOPICS.get(number)
                if topic_id:
                    topic = next(item for item in topics if item.id == topic_id)
                option = _mcq(option_index + 1, topic, rng, question_rules[0])
            else:
                option = _written_option(rule, section_rule.id, option_index, topic, question_rules, rng)
            options.append(option)
        instructions = _instructions(rule.id, section_rule.id)
        sections.append(GeneratedSection(id=section_rule.id, title=section_rule.title, instructions=instructions, options=options, answer_options=section_rule.answer_options, candidate_marks=section_rule.candidate_marks))
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
    figure_contexts: list[dict[str, object]] = []
    if paper_rule.id == "paper_3":
        title = f"Synoptic theme: {context.title()}"
        figure_contexts = [
            _theme_figure(context, rng, index)
            for index in range(1, 4)
        ]
        stimulus = [
            _extract(
                topic,
                context,
                case_id,
                rng,
                index,
                figure=figure_contexts[index - 1],
            )
            for index in range(1, 4)
        ]
        for figure_context, extract_text in zip(
            figure_contexts,
            stimulus,
            strict=True,
        ):
            figure_context["extract_text"] = extract_text
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
        _question(
            rule,
            number,
            topic,
            context,
            case_id,
            values,
            rng,
            figure_contexts=figure_contexts,
        )
        for rule, number in zip(rules, numbers, strict=True)
    ]
    chart_values = (
        list(figure_contexts[0]["series"][0]["values"])
        if figure_contexts
        else values if stimulus else []
    )
    return GeneratedOption(
        id=f"{section_id}{option_index + 1}",
        title=title,
        stimulus=stimulus,
        chart_title=(
            str(figure_contexts[0]["title"])
            if figure_contexts
            else f"Index for {context} (base = 100)"
        ),
        chart_labels=(
            list(figure_contexts[0]["labels"])
            if figure_contexts
            else [str(2021 + index) for index in range(5)]
        ),
        chart_values=chart_values,
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
    *,
    figure_contexts: list[dict[str, object]] | None = None,
) -> GeneratedQuestion:
    extract_number = _extract_number(rule.id)
    if extract_number is None:
        point = rng.choice(topic.points)
        bound_concepts: list[str] = []
    else:
        primary_concept = topic.points[(extract_number - 1) % len(topic.points)]
        secondary_concept = topic.points[extract_number % len(topic.points)]
        bound_concepts = [primary_concept, secondary_concept]
        point = (
            primary_concept
            if rule.kind in {"extended_response", "short_answer"}
            else secondary_concept
        )
    figure = (
        figure_contexts[extract_number - 1]
        if figure_contexts and extract_number is not None
        else None
    )
    question_values = (
        [float(value) for value in figure["series"][0]["values"]]
        if figure is not None
        else values
    )
    comparison_series = (
        figure["series"][1]
        if figure is not None and len(figure["series"]) > 1
        else None
    )
    evidence = (
        f"Extract {extract_number}"
        if extract_number is not None
        else f"the extracts about {context}"
    )
    change = (question_values[-1] - question_values[0]) / question_values[0] * 100
    authoring_context: dict[str, object] = {}
    source_references: list[str] = []
    if figure is not None:
        authoring_context = {
            "task_scope": (
                f"Use only Extract {extract_number} and its bound Figure "
                f"{extract_number}.1 when answering this item."
            ),
            "figure": {
                key: value
                for key, value in figure.items()
                if key != "extract_text"
            },
            "extract_text": figure.get("extract_text", ""),
            "bound_concepts": bound_concepts,
            "required_prompt_terms": [context, point],
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
        source_references = [f"Extract {extract_number}"]
    if rule.kind == "calculation":
        from Backend.Core.numeric_integrity import percentage_change_context
        authoring_context.update(percentage_change_context(question_values[0], question_values[-1]))
        authoring_context.update(
            {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            }
        )
        if extract_number is not None:
            prompt = (
                f"Using Figure {extract_number}.1 and the information in {evidence}, "
                "calculate the percentage change in the primary index. Give your "
                "answer to one decimal place."
            )
            source_references.append(f"Figure {extract_number}.1")
        else:
            prompt = (
                f"Using the data in {evidence}, calculate the percentage change in "
                "the index. Give your answer to one decimal place."
            )
        mark_label = "mark" if rule.marks == 1 else "marks"
        scheme = [
            f"Valid method using {question_values[0]} and {question_values[-1]}.",
            (
                f"Calculation: (({question_values[-1]} - {question_values[0]}) / "
                f"{question_values[0]}) "
                f"x 100 = {change:.1f}%."
            ),
            f"Correct answer: {change:.1f}%.",
            f"Maximum {rule.marks} {mark_label}.",
        ]
    elif rule.kind == "short_answer" and rule.command_word == "Identify":
        prompt = (
            f"Using Figure {extract_number}.1 and {evidence}, identify two features "
            f"relevant to {point}."
            if extract_number is not None
            else f"Using {evidence}, identify two features relevant to {point}."
        )
        if extract_number is not None:
            source_references.append(f"Figure {extract_number}.1")
        if comparison_series is None:
            scheme = [
                "One mark for each of two distinct features supported by the extract."
            ]
        else:
            scheme = [
                "Primary activity index: credit an accurate feature using "
                f"{question_values[0]} and {question_values[-1]}.",
                f"{comparison_series['label']}: credit an accurate feature using "
                f"{comparison_series['values'][0]} and "
                f"{comparison_series['values'][-1]}.",
            ]
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
            source_references.append(f"Figure {figure_number}")
        else:
            verb = "compare" if rule.command_word == "Compare" else "explain"
            prompt = f"Using the data in {evidence}, {verb} the observed changes and relate them to {point}."
        if rule.id == "relationship_3":
            scheme = [
                f"Accurate knowledge of the expected relationship involving {point}.",
                f"A coherent economic mechanism explaining the relationship involving {point}.",
                "Application to the observed change from "
                f"{question_values[0]} to {question_values[-1]}, with a clear statement "
                "of whether the evidence matches the expected relationship.",
            ]
        elif rule.id == "relationship_4":
            scheme = [
                f"Accurate knowledge of the relevant relationship involving {point}.",
                f"A coherent economic mechanism explaining the relationship involving {point}.",
                "Application to the primary index change from "
                f"{question_values[0]} to {question_values[-1]}.",
                "A developed link between the numerical trend and relevant evidence from "
                "the extracts.",
            ]
        else:
            direction = (
                "an increase"
                if question_values[-1] >= question_values[0]
                else "a decrease"
            )
            scheme = [
                "Accurate comparison: the primary index changes from "
                f"{question_values[0]} to {question_values[-1]}.",
                f"This is {direction} of "
                f"{abs(question_values[-1] - question_values[0]):.1f} index points.",
                f"Developed economic reasoning involving {point}.",
                "Recognition of the limits of the comparison.",
            ]
        if comparison_series is not None and rule.id not in {
            "relationship_3",
            "relationship_4",
        }:
            scheme.insert(
                2,
                f"The {comparison_series['label'].lower()} changes from "
                f"{comparison_series['values'][0]} to "
                f"{comparison_series['values'][-1]}.",
            )
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
        source_references=source_references,
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )


def _extract_number(rule_id: str) -> int | None:
    if not rule_id.startswith("extract_"):
        return None
    part = rule_id.split("_", 2)[1]
    return int(part) if part.isdigit() else None


def _theme_figure(
    context: str,
    rng: random.Random,
    index: int,
) -> dict[str, object]:
    labels = [str(year) for year in range(2019, 2024)]

    def series_values() -> list[float]:
        start = float(rng.randint(84, 118))
        end = round(start * (1 + rng.randint(-10, 16) / 100), 1)
        values = [start]
        for step in range(1, 4):
            trend = start + (end - start) * step / 4
            values.append(round(trend + rng.uniform(-2.4, 2.4), 1))
        values.append(end)
        return values

    series = [
        {
            "label": "Primary activity index",
            "values": series_values(),
        }
    ]
    if index in {2, 3}:
        comparison_label = (
            "Price pressure index" if index == 2 else "Well-being index"
        )
        series.append({"label": comparison_label, "values": series_values()})
    return {
        "number": f"{index}.1",
        "title": f"Indices for {context.title()} (2019 = 100)",
        "labels": labels,
        "series": series,
        "units": "index points",
    }


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


def _mcq(
    number: int,
    topic: Topic,
    rng: random.Random,
    rule: QuestionRule,
) -> GeneratedOption:
    authoring_context: dict[str, object] = {}
    if number % 5 == 0:
        base = rng.randint(60, 180)
        rate = rng.choice([5, 8, 10, 12, 15])
        quantum = Decimal("0.1")
        base_value = Decimal(base)
        rate_value = Decimal(rate) / Decimal(100)
        correct = str(
            (base_value * (Decimal(1) + rate_value)).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
        )
        distractor_values = [
            Decimal(base + rate),
            base_value * (Decimal(1) - rate_value),
            base_value * (Decimal(1) + Decimal(rate + 5) / Decimal(100)),
            base_value / (Decimal(1) + rate_value),
        ]
        distractors: list[str] = []
        for value in distractor_values:
            rendered = str(value.quantize(quantum, rounding=ROUND_HALF_UP))
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
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "index_percentage_increase",
                "inputs": {"base": str(base), "rate_percent": str(rate)},
                "unit": "index",
                "decimal_places": 1,
            },
        }
    else:
        if rule.task_operation == "analyse":
            stem, correct, distractors = ANALYTICAL_FACTS[topic.id]
        else:
            source = (
                ALTERNATE_FACTS
                if number in _OCR_ALTERNATE_NUMBERS
                else FACTS
            )
            stem, correct, distractors = source[topic.id]
        choices = [correct, *distractors]
        prompt = stem
    rng.shuffle(choices)
    answer = choices.index(correct)
    question = GeneratedQuestion(
        rule_id="mcq", number=str(number), marks=1, kind="multiple_choice",
        command_word="Select", topic_id=topic.id, prompt=prompt, choices=choices,
        correct_choice=answer, mark_scheme=[f"Option {'ABCD'[answer]}: {correct}."],
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "low",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )
    return GeneratedOption(id=f"A{number}", title=f"Question {number}", questions=[question])


def _extract(
    topic: Topic,
    context: str,
    case_id: int,
    rng: random.Random,
    index: int,
    *,
    figure: dict[str, object] | None = None,
) -> str:
    focus = topic.points[(index - 1) % len(topic.points)]
    share = rng.randint(18, 76)
    years = rng.randint(2, 7)
    if figure is None:
        start_index = float(rng.randint(82, 126))
        end_index = round(start_index * (1 + rng.randint(-9, 17) / 100), 1)
        comparison_sentence = ""
    else:
        primary_values = figure["series"][0]["values"]
        start_index = float(primary_values[0])
        end_index = float(primary_values[-1])
        comparison_sentence = ""
        if len(figure["series"]) > 1:
            comparison = figure["series"][1]
            comparison_sentence = (
                f" The {comparison['label'].lower()} changed from "
                f"{comparison['values'][0]} to {comparison['values'][-1]}."
            )
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
        f"An index of {measure} changed from {start_index:g} to {end_index:g}."
        f"{comparison_sentence} The four largest "
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
