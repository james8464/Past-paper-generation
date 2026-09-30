from __future__ import annotations

import random
import secrets

from aqabizgen.financials import FinancialPosition, format_number
from aqabizgen.syllabus import Syllabus, Topic
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

BUSINESSES = [
    "Aster Cycles",
    "Beacon Foods",
    "Cobalt Learning",
    "Driftwood Furniture",
    "Elm Health",
    "Fjord Outdoor",
    "Grove Mobility",
    "Harbour Analytics",
]
MARKETS = [
    "urban delivery",
    "home energy",
    "specialist training",
    "plant-based food",
    "accessible tourism",
    "repairable electronics",
]
MCQ_TOPIC_IDS = {
    1: "business-1",
    2: "business-2",
    3: "business-3",
    4: "business-4",
    5: "business-5",
    6: "business-4",
    7: "business-5",
    8: "business-8",
    9: "business-9",
    10: "business-4",
    11: "business-6",
    12: "business-10",
    13: "business-7",
    14: "business-2",
    15: "business-10",
}
FACTS = {
    "business-1": ("Which objective is most directly concerned with owners' return?", "Profit", ["Market mapping", "Capacity utilisation", "Labour turnover"]),
    "business-2": ("Which leadership style gives employees the greatest role in decisions?", "Democratic", ["Autocratic", "Paternalistic only", "Scientific"]),
    "business-3": ("Which measure compares a firm's sales with total market sales?", "Market share", ["Labour productivity", "Gearing", "Payback"]),
    "business-4": ("Which method aims to minimise inventory held?", "Just in Time", ["Market penetration", "Retrenchment", "Job rotation"]),
    "business-5": ("Which item is a cash inflow?", "Receipts from customers", ["Depreciation", "Closing inventory", "Trade credit offered"]),
    "business-6": ("Which measure records employees leaving during a period?", "Labour turnover", ["Capacity utilisation", "Gross margin", "Market growth"]),
    "business-7": ("Which framework examines political and technological change?", "PEST analysis", ["Boston Matrix", "Payback", "Decision tree"]),
    "business-8": ("Which Ansoff option combines new products with new markets?", "Diversification", ["Market penetration", "Market development", "Product development"]),
    "business-9": ("Which method joins two businesses into one ownership structure?", "Merger", ["Organic growth", "Delegation", "Benchmarking"]),
    "business-10": ("Which concept describes a strategy becoming misaligned gradually?", "Strategic drift", ["Economies of scale", "Market mapping", "Job enrichment"]),
}
ALTERNATE_FACTS = {
    14: (
        "Which leadership style gives a manager sole authority over decisions?",
        "Autocratic",
        ["Democratic", "Laissez-faire", "Paternalistic only"],
    ),
}


def build_paper(
    rule: PaperRule, syllabus: Syllabus, seed: int | None = None
) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    rng.shuffle(topics)
    topic_cursor = 0
    sections: list[GeneratedSection] = []
    for section_rule in rule.sections:
        options: list[GeneratedOption] = []
        for option_index in range(section_rule.option_count):
            question_rules = resolve_question_rules(section_rule, option_index + 1)
            business = rng.choice(BUSINESSES)
            market = rng.choice(MARKETS)
            case_id = rng.randint(1000, 9999)
            values = _values(rng)
            questions: list[GeneratedQuestion] = []
            for question_index, question_rule in enumerate(question_rules):
                topic = topics[topic_cursor % len(topics)]
                topic_cursor += 1
                if question_rule.kind == "multiple_choice":
                    required_topic = MCQ_TOPIC_IDS.get(option_index + 1)
                    if required_topic:
                        topic = next(item for item in topics if item.id == required_topic)
                    question = _mcq(
                        option_index + 1, topic, rng, question_rule
                    )
                else:
                    question = _written_question(
                        question_rule,
                        _number(rule.id, section_rule.id, option_index, question_index),
                        topic,
                        business,
                        case_id,
                        values,
                        rng,
                    )
                questions.append(question)
            stimulus_count = _stimulus_count(rule.id, section_rule.id)
            has_shared_chart = not (rule.id == "paper_1" and section_rule.id == "A")
            chart_title = f"Performance index for {business}" if has_shared_chart else ""
            chart_labels = ["2021", "2022", "2023", "2024", "2025"] if has_shared_chart else []
            chart_values = values if has_shared_chart else []
            options.append(
                GeneratedOption(
                    id=f"{section_rule.id}{option_index + 1}",
                    title=(
                        business
                        if stimulus_count
                        else f"Question {_number(rule.id, section_rule.id, option_index, 0)}"
                    ),
                    stimulus=[
                        _extract(
                            topics[(topic_cursor + index) % len(topics)],
                            business,
                            market,
                            case_id,
                            rng,
                            index + 1,
                        )
                        for index in range(stimulus_count)
                    ],
                    chart_title=chart_title,
                    chart_labels=chart_labels,
                    chart_values=chart_values,
                    questions=questions,
                )
            )
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                answer_options=section_rule.answer_options,
                candidate_marks=section_rule.candidate_marks,
                title=section_rule.title,
                instructions=_instructions(rule.id, section_rule.id),
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
    paper = enrich_paper(paper, syllabus.topics, subject="business")
    validate_generated_paper(paper, rule, syllabus.topic_ids)
    return paper


def _values(rng: random.Random) -> list[float]:
    values = [float(rng.randint(72, 126))]
    for _ in range(4):
        values.append(round(values[-1] * (1 + rng.randint(-8, 14) / 100), 1))
    return values


def _number(
    paper_id: str, section_id: str, option_index: int, question_index: int
) -> str:
    if paper_id == "paper_1":
        if section_id == "B":
            return str(16 + question_index)
        if section_id == "C":
            return str(21 + option_index)
        if section_id == "D":
            return str(23 + option_index)
    if paper_id == "paper_2":
        return f"0{section_id}.{question_index + 1}"
    return f"0{question_index + 1}"


def _stimulus_count(paper_id: str, section_id: str) -> int:
    if paper_id == "paper_3":
        return 6
    if paper_id == "paper_2":
        return 3
    if paper_id == "paper_1" and section_id == "B":
        return 2
    return 0


def _mcq(
    number: int,
    topic: Topic,
    rng: random.Random,
    rule: QuestionRule,
) -> GeneratedQuestion:
    business = rng.choice(BUSINESSES)
    authoring_context: dict[str, object] = {}
    if number == 6:
        correct = "A rise in selling price and a fall in variable cost per unit"
        choices = [
            correct,
            "A fall in selling price and a rise in variable cost per unit",
            "A rise in fixed costs and a fall in output",
            "A fall in capacity and a rise in fixed costs",
        ]
        prompt = (
            "Figure 1 shows a change in the break-even point of a product from M to N. "
            "Which combination of changes is most likely to explain the movement?"
        )
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "break_even_change",
                "inputs": {
                    "fixed_cost_before": "60",
                    "price_before": "5",
                    "variable_cost_before": "3",
                    "fixed_cost_after": "60",
                    "price_after": "6",
                    "variable_cost_after": "2",
                },
                "unit": "effect",
                "decimal_places": 0,
            },
        }
    elif number == 7:
        correct = "£3m"
        choices = [correct, "£7m", "£10m", "£14m"]
        prompt = (
            f"The financial data shown apply to {business}. What was its profit for "
            "the year after taxation?"
        )
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "after_tax_profit",
                "inputs": {
                    "revenue": "20",
                    "cost_of_sales": "6",
                    "operating_expenses": "4",
                    "taxation": "7",
                },
                "unit": "GBPm",
                "decimal_places": 0,
            },
        }
    elif number == 10:
        correct = "Factory B"
        choices = [correct, "Factory A", "Factory C", "Factory D"]
        prompt = (
            f"{business} compares four factories. Which factory has the highest labour "
            "productivity?"
        )
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "highest_productivity",
                "inputs": {},
                "rows": [
                    {"label": "Factory A", "output": "900", "employees": "60"},
                    {"label": "Factory B", "output": "840", "employees": "40"},
                    {"label": "Factory C", "output": "800", "employees": "50"},
                    {"label": "Factory D", "output": "750", "employees": "50"},
                ],
                "unit": "classification",
                "decimal_places": 0,
            },
        }
    elif number == 12:
        correct = "Strategic drift"
        choices = [correct, "Strategic fit", "Market penetration", "Retrenchment"]
        prompt = (
            "Use the evidence table to compare change in the external environment "
            "with change in the business's strategy. Which concept best describes "
            "the relationship shown?"
        )
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "strategic_drift",
                "inputs": {"external_change": "high", "strategic_change": "low"},
                "unit": "classification",
                "decimal_places": 0,
            },
        }
    elif number == 13:
        correct = "Statement 1 is true, Statement 2 is false"
        choices = [
            correct,
            "Statement 1 is false, Statement 2 is true",
            "Both statements are true",
            "Both statements are false",
        ]
        prompt = (
            f"The performance table for {business} is shown below. Statement 1: labour "
            "turnover is worse than target. Statement 2: capacity utilisation exceeded "
            "target. Which option is correct?"
        )
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "performance_statements",
                "inputs": {},
                "rows": [
                    {"label": "Capacity utilisation", "target": "90", "actual": "88", "better_when": "higher"},
                    {"label": "Labour turnover", "target": "12", "actual": "17", "better_when": "lower"},
                    {"label": "Market share", "target": "13", "actual": "15", "better_when": "higher"},
                    {"label": "ROCE", "target": "16", "actual": "12", "better_when": "higher"},
                ],
                "unit": "classification",
                "decimal_places": 0,
            },
        }
    elif number == 5:
        revenue = rng.randint(14, 48)
        cost = rng.randint(4, revenue - 3)
        correct = f"£{revenue - cost}m"
        choices = [
            correct,
            f"£{revenue + cost}m",
            f"£{cost}m",
            f"£{max(1, revenue - cost - 2)}m",
        ]
        choices = list(dict.fromkeys(choices))
        while len(choices) < 4:
            choices.append(f"£{revenue + len(choices)}m")
        prompt = (
            f"{business} has revenue of £{revenue}m and cost of sales of "
            f"£{cost}m. What is its gross profit?"
        )
        authoring_context = {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "gross_profit",
                "inputs": {"revenue": str(revenue), "cost_of_sales": str(cost)},
                "unit": "GBPm",
                "decimal_places": 0,
            }
        }
    else:
        stem, correct, distractors = ALTERNATE_FACTS.get(number, FACTS[topic.id])
        choices = [correct, *distractors]
        prompt = stem
    rng.shuffle(choices)
    answer = choices.index(correct)
    return GeneratedQuestion(
        rule_id="mcq",
        number=f"{number:02d}",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        topic_id=topic.id,
        prompt=prompt,
        choices=choices,
        correct_choice=answer,
        mark_scheme=[f"Option {'ABCD'[answer]}: {correct}."],
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "low",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )


def _written_question(
    rule: QuestionRule,
    number: str,
    topic: Topic,
    business: str,
    case_id: int,
    values: list[float],
    rng: random.Random,
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    context = f"the extracts about {business}"
    change = (values[-1] - values[0]) / values[0] * 100
    structured_scheme: list[MarkSchemePoint] = []
    authoring_context: dict[str, object] = {}
    financials = FinancialPosition.from_chart_values(values)
    if rule.id == "current_ratio":
        ratio = format_number(financials.current_ratio)
        prompt = (
            f"Calculate the current ratio for {business} for 2024. "
            "Show your working."
        )
        scheme = [
            "Current ratio = current assets ÷ current liabilities.",
            (
                f"Current assets = {financials.inventories} + "
                f"{financials.receivables} + {financials.cash} = "
                f"£{financials.current_assets}m."
            ),
            (
                f"Substitution: {financials.current_assets} ÷ "
                f"{financials.payables}."
            ),
            f"Answer: {ratio}:1 (accept {ratio} without :1).",
        ]
        structured_scheme = [
            MarkSchemePoint(
                text=scheme[0],
                marks=1,
                assessment_objective="AO1",
            ),
            *[
                MarkSchemePoint(
                    text=text,
                    marks=1,
                    assessment_objective="AO2",
                )
                for text in scheme[1:]
            ],
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "source_data": {
                "inventories": financials.inventories,
                "receivables": financials.receivables,
                "cash": financials.cash,
                "current_liabilities": financials.payables,
            },
            "verified_answers": {"current_ratio": financials.current_ratio},
        }
    elif rule.id == "roce_calculation":
        operating_profit = format_number(
            financials.operating_profit_at_twelve_percent
        )
        prompt = (
            f"{business} achieved a Return on Capital Employed (ROCE) of 12%. "
            "Using the extract from its statement of financial position, calculate "
            "its operating profit. Show your working."
        )
        scheme = [
            "ROCE = operating profit ÷ capital employed × 100.",
            (
                f"Capital employed = {financials.total_equity} + "
                f"{financials.non_current_liabilities} = "
                f"£{financials.capital_employed}m."
            ),
            f"Substitution and rearrangement: 12 × {financials.capital_employed} ÷ 100.",
            f"Operating profit = £{operating_profit}m.",
        ]
        structured_scheme = [
            MarkSchemePoint(
                text=scheme[0],
                marks=1,
                assessment_objective="AO1",
            ),
            *[
                MarkSchemePoint(
                    text=text,
                    marks=1,
                    assessment_objective="AO2",
                )
                for text in scheme[1:]
            ],
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "source_data": {
                "total_equity": financials.total_equity,
                "non_current_liabilities": financials.non_current_liabilities,
                "capital_employed": financials.capital_employed,
                "roce_percent": 12,
            },
            "verified_answers": {
                "operating_profit": financials.operating_profit_at_twelve_percent
            },
        }
    elif rule.id == "analysis_1" and rule.marks == 9:
        prompt = (
            f"Analyse how the restructuring shown in the table might affect {business}'s "
            "speed of response to customer enquiries."
        )
        scheme = [
            "Use the wider span of control and fewer hierarchy levels;",
            "Analyse faster communication and delegated decision-making;",
            "Consider workload, control and possible communication problems;",
            "Develop a contextual chain to speed of customer response.",
        ]
    elif rule.id == "analysis_2" and rule.marks == 9:
        prompt = (
            "Analyse how a government changing its fiscal policy might affect a "
            "business which provides healthcare products."
        )
        scheme = [
            "Identify a relevant change in taxation or government expenditure;",
            "Apply the change to demand, costs, investment or cash flow;",
            "Develop a linked effect on objectives or performance;",
            "Credit a relevant counter-effect or dependency.",
        ]
    elif rule.id == "analysis_3" and rule.marks == 9:
        prompt = (
            "Analyse how adopting an innovation strategy might affect the human "
            "resources function of a business."
        )
        scheme = [
            "Explain relevant recruitment, training or workforce-planning needs;",
            "Analyse the effect on skills, motivation, resistance or labour cost;",
            "Link the HR response to successful implementation;",
            "Credit a developed counter-effect or dependency.",
        ]
    elif rule.kind == "calculation":
        from Backend.Core.numeric_integrity import percentage_change_context
        authoring_context.update(percentage_change_context(values[0], values[-1]))
        if "." in number:
            prompt = (
                f"Using the business sales data for {business}, calculate the "
                "percentage change from 2021 to 2025. Give your answer to one "
                "decimal place."
            )
        else:
            prompt = (
                f"Using the performance data for {business}, calculate the percentage "
                "change in the index. Give your answer to one decimal place."
            )
        scheme = [
            f"Method: ({values[-1]} − {values[0]}) ÷ {values[0]} × 100.",
            f"Answer: {change:.1f}%.",
            "Award method credit for a correct substitution.",
        ]
    elif rule.kind == "analysis":
        prompt = (
            f"{rule.command_word} how {point} may affect {business}. Use the information "
            f"in {context} and develop linked business reasoning."
        )
        scheme = [
            f"Accurate knowledge of {topic.title}.",
            f"Application to the figures and circumstances of {business}.",
            f"Developed cause-and-effect reasoning involving {point}.",
            "Credit a relevant calculation, model or counter-effect.",
        ]
    elif rule.kind == "essay":
        market = rng.choice(MARKETS)
        comparator = rng.choice(
            [candidate for candidate in topic.points if candidate != point]
        )
        objective = rng.choice(
            [
                "operating profit",
                "market share",
                "long-term cash flow",
                "customer retention",
            ]
        )
        horizon = rng.randint(3, 6)
        investment_budget = rng.randint(2, 15)
        visible_growth = f"{change:.1f}%"
        prompt = (
            f"A business operating in {market} recorded revenue growth of "
            f"{visible_growth} last year and has an investment budget of "
            f"£{investment_budget}m. Evaluate whether prioritising {point} rather than "
            f"{comparator} is likely to be the better way to improve {objective} over the next "
            f"{horizon} years."
        )
        content = [
            f"Accurate explanation of {point} and how it could affect {objective}.",
            (
                f"A developed route for {point}: identify an intermediate effect on "
                f"revenue, cost, capability or risk in {market}, then link it to "
                f"{objective}."
            ),
            (
                f"Use the visible evidence of {visible_growth} revenue growth, the "
                f"£{investment_budget}m budget and the {horizon}-year horizon to assess "
                "scale, affordability and timing."
            ),
            (
                f"A developed counter-route for {comparator}: explain an intermediate "
                f"effect and why it could have a stronger impact on {objective}."
            ),
            (
                f"Interaction and contingency: the effect of {point} may depend on "
                f"{comparator}, competitor responses and implementation constraints in "
                f"{market}."
            ),
            (
                f"Comparative judgement: decide between {point} and {comparator} using "
                f"relative magnitude, timing, likelihood and the stated objective of "
                f"improving {objective}."
            ),
        ]
        scheme = _levels(rule.marks, topic, point, case_id, content=content)
        authoring_context = {
            "task_context": {
                "driver": point,
                "comparator": comparator,
                "market": market,
                "objective": objective,
                "revenue_growth": visible_growth,
                "investment_budget": f"£{investment_budget}m",
                "horizon": f"{horizon} years",
            },
            "required_prompt_terms": [
                point,
                comparator,
                market,
                objective,
                visible_growth,
                f"£{investment_budget}m",
                f"{horizon} years",
            ],
            "required_mark_scheme_terms": [
                point,
                comparator,
                market,
                objective,
                visible_growth,
                f"£{investment_budget}m",
                f"{horizon}-year",
            ],
            "observable_mark_points": content,
        }
    else:
        prompt = (
            f"Evaluate whether action on {point} is the best strategic response for "
            f"{business}. Use the evidence in {context} and make a supported judgement."
        )
        scheme = _levels(rule.marks, topic, point, case_id)
    if rule.id in {"current_ratio", "roce_calculation"}:
        from Backend.Core.numeric_integrity import MONEY, NUMBER, NumericOutput
        source = authoring_context["source_data"]
        is_ratio = rule.id == "current_ratio"
        expressions = (
            {"current_assets": "inventories + receivables + cash", "current_ratio": "current_assets / current_liabilities"}
            if is_ratio else {"capital_employed": "total_equity + non_current_liabilities", "operating_profit": "capital_employed * roce_percent / 100"}
        )
        source = {key: value for key, value in source.items() if key != "capital_employed"}
        outputs = (
            [NumericOutput(role="current_assets", unit="GBPm", decimal_places=0, scheme_pattern=rf"^Current assets =[^\n=]*=\s*{MONEY}m"), NumericOutput(role="current_ratio", unit="1", decimal_places=2, scheme_pattern=rf"^Answer: (?P<value>{NUMBER}):1")]
            if is_ratio else [NumericOutput(role="capital_employed", unit="GBPm", decimal_places=0, scheme_pattern=rf"^Capital employed =[^\n=]*=\s*{MONEY}m"), NumericOutput(role="operating_profit", unit="GBPm", decimal_places=2, scheme_pattern=rf"^Operating profit =\s*{MONEY}m")]
        )
        authoring_context.update({"calculation_variables": source, "calculation_input_units": {key: "%" if key == "roce_percent" else "GBPm" for key in source}, "calculation_expressions": expressions, "calculation_outputs": [output.model_dump() for output in outputs]})
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
        structured_mark_scheme=structured_scheme,
        authoring_context=authoring_context,
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        task_operation=rule.task_operation,
        source_dependency=rule.source_dependency,
    )


def _levels(
    marks: int,
    topic: Topic,
    point: str,
    case_id: int,
    *,
    content: list[str] | None = None,
) -> list[str]:
    bands = {
        16: [
            "Level 4 (13–16): excellent knowledge, sustained contextual analysis, balanced evaluation and a supported judgement.",
            "Level 3 (9–12): good knowledge and developed analysis with relevant evaluation, though balance or context may be uneven.",
            "Level 2 (5–8): some accurate knowledge and linked reasoning; evaluation is limited.",
            "Level 1 (1–4): isolated relevant points or assertions.",
        ],
        20: [
            "Level 5 (17–20): excellent contextual analysis, sustained evaluation and a fully supported strategic judgement.",
            "Level 4 (13–16): good developed analysis and balanced evaluation with a supported judgement.",
            "Level 3 (9–12): sound analysis and some evaluation, with uneven context or balance.",
            "Level 2 (5–8): limited analytical chains and weak evaluation.",
            "Level 1 (1–4): isolated points or unsupported assertions.",
        ],
        24: [
            "Level 5 (20–24): excellent synoptic analysis, sustained balanced evaluation and a fully justified strategic judgement.",
            "Level 4 (15–19): good synoptic analysis and relevant evaluation with a supported judgement.",
            "Level 3 (10–14): sound analysis and some evaluation, but uneven breadth or context.",
            "Level 2 (5–9): limited analytical chains and generic evaluation.",
            "Level 1 (1–4): isolated points or unsupported assertions.",
        ],
        25: [
            "Level 5 (21–25): excellent knowledge, sustained analysis, balanced evaluation and a fully supported judgement.",
            "Level 4 (16–20): good developed analysis and relevant evaluation with a supported judgement.",
            "Level 3 (11–15): sound analysis and some evaluation, with uneven context or balance.",
            "Level 2 (6–10): limited analytical chains and weak evaluation.",
            "Level 1 (1–5): isolated points or unsupported assertions.",
        ],
    }
    indicative_content = content or [
        f"Indicative content: {topic.title}; {point}; application to the business.",
        "Consider objectives, stakeholder effects, quantitative evidence, risk, time and alternatives.",
    ]
    return [
        *indicative_content,
        *bands[marks],
        "Level 0 (0): no creditworthy material.",
    ]


def _extract(
    topic: Topic,
    business: str,
    market: str,
    case_id: int,
    rng: random.Random,
    index: int,
) -> str:
    employee_count = rng.randint(80, 2400)
    share = rng.randint(9, 58)
    growth = rng.randint(-8, 19)
    point = topic.points[(index - 1) % len(topic.points)]
    unit_cost = rng.randint(18, 95)
    price = unit_cost + rng.randint(8, 70)
    capacity = rng.randint(62, 94)
    engagement = rng.randint(48, 86)
    investment = rng.randint(2, 18)
    time_horizon = rng.randint(2, 6)
    role = (index - 1) % 6
    if role == 0:
        return (
            f"Extract {index}. {business} competes in the {market} market. It employs "
            f"{employee_count} people, holds an estimated {share}% market share and recorded "
            f"revenue growth of {growth}% last year. Its average selling price is £{price}, "
            f"compared with a unit cost of £{unit_cost}. Demand is strongest among customers "
            f"who value reliability and transparent pricing, but two new entrants are offering "
            f"lower prices. Managers are reviewing {point}. The forecast assumes that current "
            "customer preferences continue, although the market-research sample was small and "
            "competitor responses are uncertain."
        )
    if role == 1:
        return (
            f"Extract {index}. Operations at {business} are running at {capacity}% capacity. "
            f"Employee engagement is {engagement}%, while absence and labour turnover have "
            "increased in the busiest site. A proposed process redesign would require £"
            f"{investment}m of investment and six weeks of training. The operations director "
            f"argues that {point} would improve consistency and reduce waste. Employee "
            "representatives support better training but are concerned about workload, job "
            "security and the reliability of the implementation timetable. Suppliers have "
            "also warned that energy and transport costs may remain volatile."
        )
    if role == 2:
        return (
            f"Extract {index}. The board of {business} must choose between organic expansion "
            f"and a partnership with a larger rival. The partnership could provide access to "
            f"{rng.randint(4, 14)} new regional markets within {time_horizon} years, but it "
            "would reduce management control and require shared investment decisions. Organic "
            "growth would be slower and funded from retained profit. Directors are assessing "
            f"{point}, the effect on the brand and whether expected economies of scale would "
            "actually be achieved. Forecast cash flows are sensitive to demand growth and the "
            "partner's future pricing policy."
        )
    if role == 3:
        return (
            f"Extract {index}. Conditions in the {market} market are changing. A new "
            f"regulation could add {rng.randint(2, 9)}% to operating costs, while a rival has "
            f"introduced a digital service priced {rng.randint(5, 18)}% below {business}'s "
            "offer. Consumer interest in repairability and lower environmental impact is also "
            f"growing. Managers are considering {point}. Acting quickly could protect market "
            "share, but the available evidence comes from one quarter and may not represent "
            "long-term demand. Delaying the decision would preserve cash but could allow the "
            "rival to establish customer loyalty."
        )
    if role == 4:
        return (
            f"Extract {index}. Stakeholders disagree about the next stage of {business}'s "
            f"strategy. Investors want a return within {time_horizon} years; employees favour "
            "training and predictable hours; local residents want lower traffic and emissions. "
            f"A customer survey reports satisfaction of {rng.randint(63, 91)}%, although only "
            f"{rng.randint(4, 12)}% of customers replied. The managing director believes "
            f"{point} should guide the decision. The finance director instead prioritises "
            "liquidity and warns that benefits which are difficult to measure should not be "
            "ignored or treated as certain."
        )
    return (
        f"Extract {index}. A scenario analysis for {business} gives three possible outcomes. "
        f"Under the central forecast, sales rise by {rng.randint(5, 14)}%; under the downside "
        f"case, they fall by {rng.randint(3, 11)}%; and under the upside case, capacity becomes "
        f"a constraint within {time_horizon} years. The board is reviewing {point}. Directors "
        "must decide how much weight to give the forecasts, the reversibility of the investment "
        "and the opportunity cost of waiting. None of the scenarios includes an unexpected "
        "competitor acquisition or a major supply interruption, so the estimates should be "
        "used as decision evidence rather than treated as predictions."
    )


def _instructions(paper_id: str, section_id: str) -> str:
    if paper_id == "paper_1" and section_id == "A":
        return "Answer all 15 questions. Select one answer for each question."
    if paper_id == "paper_1" and section_id in {"C", "D"}:
        return "Answer one question from this section."
    if paper_id == "paper_1" and section_id == "B":
        return "Answer all questions in this section."
    return "Answer all questions in this section using the case evidence."
