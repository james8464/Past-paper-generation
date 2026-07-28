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

from aqaaccountgen.syllabus import Syllabus, Topic


BUSINESSES = [
    "Alder Manufacturing",
    "Bracken Retail",
    "Copper Lane Foods",
    "Dales Engineering",
    "Evergreen Services",
    "Foundry Components",
    "Glenmore Trading",
    "Harbour Textiles",
]

MCQ_FACTS = [
    ("Which book of prime entry records credit purchases of inventory?", "Purchases journal", ["Sales journal", "Cash book", "General journal"]),
    ("Which formula calculates gross profit margin?", "Gross profit ÷ revenue × 100", ["Profit for the year ÷ capital × 100", "Current assets ÷ current liabilities", "Revenue ÷ gross profit × 100"]),
    ("Which concept records income when it is earned?", "Accruals", ["Prudence", "Materiality", "Business entity"]),
    ("Which ratio measures short-term liquidity?", "Current ratio", ["Gearing", "Return on capital employed", "Asset turnover"]),
    ("Which source of finance normally increases gearing?", "A long-term loan", ["A rights issue", "Retained earnings", "Ordinary share capital"]),
    ("Where is carriage inwards normally included?", "Cost of sales", ["Finance costs", "Distribution costs", "Other income"]),
    ("Which item is a current asset?", "Trade receivables", ["Share capital", "Bank loan repayable in ten years", "Trade payables"]),
    ("What is the double entry for a credit sale?", "Debit receivables, credit sales", ["Debit sales, credit receivables", "Debit bank, credit sales", "Debit purchases, credit payables"]),
    ("Which method discounts future cash flows?", "Net present value", ["Payback", "Contribution per unit", "Inventory turnover"]),
    ("Which principle requires professional honesty?", "Integrity", ["Consistency", "Realisation", "Duality"]),
]

CALCULATION_TASKS = {
    "statement_extract": "Prepare the requested extract from the statement of financial position",
    "ledger_calculation": "Calculate the closing balance on the relevant ledger account",
    "company_statement": "Prepare the required section of the limited-company financial statements",
    "partnership_1": "Calculate the partners' residual profit shares",
    "partnership_2": "Prepare the partners' current accounts",
    "contribution": "Calculate contribution and profit",
    "budget": "Calculate the budgeted profit and closing cash position",
    "variance_1": "Calculate the direct-material price variance",
    "variance_2": "Calculate the direct-labour and overhead variances",
    "costing_1": "Calculate the overhead cost per unit using activity-based costing",
    "costing_3": "Calculate the contribution per unit of limiting factor",
}

DECISIONS = [
    "accept a long-term supply contract",
    "invest in automated production equipment",
    "replace absorption costing with activity-based costing",
    "raise finance through a new loan",
    "change its credit-control policy",
    "launch a product with uncertain forecast demand",
]


def build_paper(
    rule: PaperRule, syllabus: Syllabus, seed: int | None = None
) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    rng.shuffle(topics)
    cursor = 0
    sections: list[GeneratedSection] = []
    for section_rule in rule.sections:
        business = rng.choice(BUSINESSES)
        case_id = rng.randint(1000, 9999)
        values = _values(rng)
        questions: list[GeneratedQuestion] = []
        for index, question_rule in enumerate(section_rule.questions):
            topic = topics[cursor % len(topics)]
            cursor += 1
            number = _number(rule.id, section_rule.id, index)
            if question_rule.kind == "multiple_choice":
                question = _mcq(question_rule, number, index, topic, business, rng)
            else:
                question = _written(
                    question_rule, number, topic, business, case_id, values, rng
                )
            questions.append(question)
        option = GeneratedOption(
            id=f"{section_rule.id}1",
            title=business,
            stimulus=[
                _extract(section_rule.id, business, case_id, rng, 1),
                _extract(section_rule.id, business, case_id, rng, 2),
            ],
            chart_title=f"Five-year accounting index for {business}",
            chart_labels=["2021", "2022", "2023", "2024", "2025"],
            chart_values=values,
            questions=questions,
        )
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                title=section_rule.title,
                instructions="Answer all questions in this section.",
                options=[option],
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
    paper = enrich_paper(paper, syllabus.topics, subject="accounting")
    validate_generated_paper(paper, rule, syllabus.topic_ids)
    return paper


def _number(paper_id: str, section_id: str, index: int) -> str:
    if section_id == "A":
        if index < 10:
            return f"{index + 1:02d}"
        if paper_id == "paper_1":
            return ["11", "12", "13.1", "13.2"][index - 10]
        return ["11", "12.1", "12.2", "13"][index - 10]
    if section_id == "B":
        if paper_id == "paper_1":
            return ["14.1", "14.2", "15.1", "15.2", "15.3"][index]
        return [
            "14.1", "14.2", "14.3", "14.4",
            "15.1", "15.2", "15.3", "15.4",
        ][index]
    return str(16 + index)


def _values(rng: random.Random) -> list[float]:
    values = [float(rng.randint(70, 120))]
    for _ in range(4):
        values.append(round(values[-1] * (1 + rng.randint(-10, 15) / 100), 1))
    return values


def _mcq(
    rule: QuestionRule,
    number: str,
    index: int,
    topic: Topic,
    business: str,
    rng: random.Random,
) -> GeneratedQuestion:
    stem, correct, distractors = MCQ_FACTS[index]
    if index in {6, 8}:
        revenue = rng.randrange(80, 220, 5)
        cost = rng.randrange(35, revenue - 10, 5)
        correct = f"£{revenue - cost}000"
        distractors = [
            f"£{revenue + cost}000",
            f"£{cost}000",
            f"£{revenue}000",
        ]
        stem = (
            f"{business} has revenue of £{revenue}000 and cost of sales of "
            f"£{cost}000. What is gross profit?"
        )
    choices = [correct, *distractors]
    rng.shuffle(choices)
    answer = choices.index(correct)
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=stem,
        choices=choices,
        correct_choice=answer,
        mark_scheme=[f"Option {'ABCD'[answer]}: {correct}."],
    )


def _written(
    rule: QuestionRule,
    number: str,
    topic: Topic,
    business: str,
    case_id: int,
    values: list[float],
    rng: random.Random,
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    if rule.kind == "calculation":
        task = CALCULATION_TASKS.get(rule.id, "Calculate the required accounting figure")
        prompt = (
            f"{task} for {business} using the case evidence and accounting-information "
            f"table. Show all workings and "
            f"apply {point} where relevant."
        )
        contribution = values[4] - values[2]
        scheme = [
            f"Contribution indicator: £{values[4]:.1f}000 − £{values[2]:.1f}000 = £{contribution:.1f}000.",
            f"Profit indicator: £{contribution:.1f}000 − £{values[1]:.1f}000 = £{contribution - values[1]:.1f}000.",
            "Award method marks for valid ledger, statement or costing workings.",
            f"Credit a correctly labelled answer applied to {business}.",
        ]
    elif rule.kind == "analysis":
        prompt = (
            f"{rule.command_word} how {point} should be treated or interpreted by "
            f"{business}. Use the evidence in the extracts."
        )
        scheme = [
            f"Accurate knowledge of {topic.title}.",
            f"Application to {business} and the supplied figures.",
            f"Developed accounting reasoning about {point}.",
            "Credit relevant limitations or alternative treatments.",
        ]
    else:
        decision = rng.choice(DECISIONS)
        prompt = (
            f"{rule.command_word} the directors of {business} whether it should {decision}. "
            f"Use quantitative and qualitative evidence from the extracts, including "
            f"{point}, and reach a justified conclusion."
        )
        scheme = _levels(topic, point, case_id)
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


def _levels(topic: Topic, point: str, case_id: int) -> list[str]:
    return [
        f"Indicative content: {topic.title}; {point}; application to the business.",
        "Use accurate calculations, accounting principles and relevant non-financial evidence.",
        "Level 5 (21–25): fully integrated analysis, balanced evaluation and a justified recommendation.",
        "Level 4 (16–20): developed analysis and relevant evaluation with a supported recommendation.",
        "Level 3 (11–15): sound accounting analysis and some evaluation.",
        "Level 2 (6–10): partial calculations or limited analytical links.",
        "Level 1 (1–5): isolated relevant points.",
        "Level 0 (0): no creditworthy material.",
    ]


def _extract(
    section: str,
    business: str,
    case_id: int,
    rng: random.Random,
    index: int,
) -> str:
    revenue = rng.randrange(320, 1800, 10)
    profit = rng.randrange(20, max(30, revenue // 4), 5)
    current_assets = rng.randrange(90, 520, 10)
    current_liabilities = rng.randrange(60, 430, 10)
    if index == 1:
        return (
            f"Extract 1. {business} reported revenue of £{revenue}000 and profit "
            f"for the year of £{profit}000. Current assets were £{current_assets}000 and "
            f"current liabilities were £{current_liabilities}000. Management expects sales "
            f"volume to change by {rng.randint(-8, 18)}% next year. The figures are provisional "
            "and include estimates for inventory and doubtful debts."
        )
    return (
        f"Extract 2. The directors are considering investment of "
        f"£{rng.randrange(100, 700, 25)}000, financed over {rng.randint(3, 8)} years. Staff "
        f"turnover is {rng.randint(5, 24)}% and a customer survey response rate was "
        f"{rng.randint(8, 36)}%. The accountant has warned that forecasts depend on demand, "
        f"cost inflation and the chosen treatment of overheads. Section {section} decisions "
        "should therefore use both financial and non-financial evidence."
    )
