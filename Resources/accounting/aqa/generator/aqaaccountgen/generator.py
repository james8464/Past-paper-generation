from __future__ import annotations

import random
import secrets

from aqaaccountgen.case_data import (
    CostingCase,
    IncomeStatementCase,
    NonCurrentAssetCase,
    PartnershipCase,
    SalesLedgerCase,
    ShareholderCase,
)
from aqaaccountgen.syllabus import Syllabus, Topic
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


def _gbp(value: int) -> str:
    """Format whole-pound values in the style used by AQA accounting papers."""

    sign = "−" if value < 0 else ""
    return f"{sign}£{abs(value):,}"


def _gbp_decimal(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}£{abs(value):,.2f}"


MCQ_TOPIC_IDS = [
    "accounting-3",
    "accounting-8",
    "accounting-5",
    "accounting-8",
    "accounting-16",
    "accounting-6",
    "accounting-6",
    "accounting-3",
    "accounting-13",
    "accounting-18",
]

RULE_TOPIC_IDS = {
    ("paper_1", "explain_trade"): "accounting-3",
    ("paper_1", "statement_extract"): "accounting-6",
    ("paper_1", "ledger_calculation"): "accounting-4",
    ("paper_1", "accounting_concept"): "accounting-3",
    ("paper_1", "company_statement"): "accounting-7",
    ("paper_1", "company_adjustment"): "accounting-17",
    ("paper_1", "partnership_1"): "accounting-15",
    ("paper_1", "partnership_2"): "accounting-15",
    ("paper_1", "partnership_3"): "accounting-15",
    ("paper_1", "decision_1"): "accounting-14",
    ("paper_1", "decision_2"): "accounting-17",
    ("paper_2", "frc"): "accounting-1",
    ("paper_2", "contribution"): "accounting-10",
    ("paper_2", "limitation"): "accounting-10",
    ("paper_2", "budget"): "accounting-9",
    ("paper_2", "variance_1"): "accounting-11",
    ("paper_2", "variance_2"): "accounting-11",
    ("paper_2", "variance_3"): "accounting-11",
    ("paper_2", "variance_4"): "accounting-11",
    ("paper_2", "costing_1"): "accounting-12",
    ("paper_2", "costing_2"): "accounting-12",
    ("paper_2", "costing_3"): "accounting-10",
    ("paper_2", "costing_4"): "accounting-12",
    ("paper_2", "decision_1"): "accounting-13",
    ("paper_2", "decision_2"): "accounting-17",
}


def build_paper(
    rule: PaperRule, syllabus: Syllabus, seed: int | None = None
) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    topics_by_id = {topic.id: topic for topic in topics}
    rng.shuffle(topics)
    cursor = 0
    sections: list[GeneratedSection] = []
    for section_rule in rule.sections:
        business = rng.choice(BUSINESSES)
        case_id = rng.randint(1000, 9999)
        values = _values(rng)
        questions: list[GeneratedQuestion] = []
        for index, question_rule in enumerate(section_rule.questions):
            if question_rule.kind == "multiple_choice" and index < len(MCQ_TOPIC_IDS):
                topic_id = MCQ_TOPIC_IDS[index]
            else:
                topic_id = RULE_TOPIC_IDS.get((rule.id, question_rule.id))
            topic = topics_by_id.get(topic_id, topics[cursor % len(topics)])
            cursor += 1
            number = _number(rule.id, section_rule.id, index)
            if question_rule.kind == "multiple_choice":
                question = _mcq(question_rule, number, index, topic, business, rng)
            else:
                question = _written(
                    rule.id, question_rule, number, topic, business, case_id, values, rng
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
    paper_id: str,
    rule: QuestionRule,
    number: str,
    topic: Topic,
    business: str,
    case_id: int,
    values: list[float],
    rng: random.Random,
) -> GeneratedQuestion:
    point = rng.choice(topic.points)
    authoring_context: dict[str, object] = {}
    if rule.id == "explain_trade":
        prompt = (
            f"Explain two reasons why {business} may offer a customer a trade discount."
        )
        scheme = [
            "A trade discount reduces the list price when the customer meets the stated purchasing condition;",
            "One valid reason is to encourage the customer to place a larger order;",
            "A second valid reason is to encourage repeat purchases and strengthen customer retention;",
            f"The lower effective unit price can persuade the customer to increase the order size, so {business} may earn more sales revenue overall;",
            f"The saving gives the customer an incentive to buy from {business} again, therefore future revenue may become more predictable;",
            f"A larger discounted order moves more units, therefore {business} may hold less inventory through increased inventory turnover;",
        ]
    elif rule.id == "statement_extract":
        case = NonCurrentAssetCase.from_chart_values(business, values)
        prompt = (
            f"Prepare an extract from the statement of financial position for {business}, "
            "showing the non-current assets section. Show all workings."
        )
        scheme = case.mark_scheme_points()
        authoring_context = case.authoring_context()
    elif rule.id == "ledger_calculation":
        case = SalesLedgerCase.from_chart_values(business, values)
        prompt = (
            f"Prepare the sales ledger control account for {business}. Balance the "
            "account and bring the balance down at the start of the next period."
        )
        scheme = case.ledger_mark_scheme_points()
        authoring_context = case.ledger_authoring_context()
    elif rule.id == "accounting_concept":
        case = SalesLedgerCase.from_chart_values(business, values)
        prompt = (
            f"Prepare the sales account for {business}. Show clearly the amount "
            "transferred to the income statement."
        )
        scheme = case.sales_account_mark_scheme_points()
        authoring_context = case.sales_account_authoring_context()
    elif rule.id == "company_statement":
        case = IncomeStatementCase.from_chart_values(business, values)
        prompt = (
            f"Prepare the income statement for {business} for the year ended. "
            "Show all workings."
        )
        scheme = case.mark_scheme_points()
        authoring_context = case.authoring_context()
    elif rule.id == "company_adjustment":
        prompt = (
            f"Assess the usefulness of the income statement to the employees of {business}."
        )
        scheme = [
            "Employees can assess profitability and the ability to sustain wages or employment;",
            "Trends may help employees judge job security and negotiate remuneration;",
            "The statement is historical and may not show future cash availability;",
            "Accounting estimates and policies limit comparability;",
            "A supported conclusion considers other financial and non-financial information.",
        ]
    elif rule.id == "partnership_1":
        case = PartnershipCase.from_chart_values(values)
        prompt = (
            "Using the information provided, prepare Alex and Morgan's capital accounts "
            "following Riley's retirement. Balance the accounts and bring down the "
            "remaining balances."
        )
        scheme = case.retirement_mark_scheme_points()
        authoring_context = case.retirement_authoring_context()
    elif rule.id == "partnership_2":
        case = PartnershipCase.from_chart_values(values)
        prompt = (
            "Using the information provided, prepare the partnership profit and loss "
            "appropriation account for both periods of the year."
        )
        scheme = case.appropriation_mark_scheme_points()
        authoring_context = case.appropriation_authoring_context()
    elif rule.id == "partnership_3":
        prompt = (
            "Assess the view that the formal partnership agreement was unnecessary."
        )
        scheme = [
            "An agreement clarifies capital, drawings, salaries, interest and profit-sharing;",
            "It provides a process for admission, retirement and dispute resolution;",
            "Preparation has legal or professional cost and cannot anticipate every event;",
            "Default partnership law may apply where no agreement exists;",
            "A supported conclusion weighs certainty and flexibility against cost.",
        ]
    elif rule.id == "decision_1":
        prompt = (
            f"Advise the owner of {business} which approach should be used to improve "
            "the accounting records. Use the information in the case and reach a "
            "justified conclusion."
        )
        scheme = [
            "Compare the annual and initial financial costs of each approach;",
            "Analyse the likely effect on accuracy, timeliness and credit control;",
            "Consider the owner's time, staff expertise and quality of management information;",
            "Evaluate security, reliability and implementation risks;",
            "Reach a justified recommendation supported by the case evidence.",
            *_levels(topic, point, case_id),
        ]
    elif rule.id == "decision_2":
        prompt = (
            f"Advise the investor whether the shares in {business} should be retained "
            "or sold. Use the financial and non-financial evidence and reach a "
            "justified conclusion."
        )
        if paper_id == "paper_1":
            case = ShareholderCase.from_chart_values(business, values)
            scheme = [*case.mark_scheme_points(), *_levels(topic, point, case_id)]
            authoring_context = case.authoring_context()
        else:
            scheme = [
                "Analyse movements in profit, equity, dividends and the market price;",
                "Use relevant investor ratios and explain what they indicate;",
                "Assess gearing, interest-rate exposure and future cost pressure;",
                "Consider dividend policy and relevant non-financial evidence;",
                "Reach a balanced judgement that recognises the investor's objectives.",
                *_levels(topic, point, case_id),
            ]
    elif rule.id == "frc":
        prompt = (
            f"Explain one benefit to investors of {business} preparing its financial "
            "statements in accordance with accounting standards."
        )
        scheme = [
            "Accounting standards require consistent recognition, measurement and presentation of transactions;",
            f"This makes {business}'s financial statements more reliable and comparable with other entities;",
            "Investors can therefore assess performance and risk more confidently before deciding whether to invest.",
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.id == "contribution":
        case = CostingCase.from_chart_values(values)
        prompt = (
            f"{business} expects to sell {case.units_sold:,} units at "
            f"£{case.selling_price_per_unit} each. Variable cost is "
            f"£{case.variable_cost_per_unit} per unit and fixed cost is "
            f"£{case.fixed_cost:,}. Calculate total contribution and profit. "
            "Show all workings."
        )
        scheme = [
            (
                "Method: contribution per unit = selling price per unit − "
                "variable cost per unit."
            ),
            (
                f"Contribution per unit: £{case.selling_price_per_unit} − "
                f"£{case.variable_cost_per_unit} = "
                f"£{case.contribution_per_unit}."
            ),
            "Method: total contribution = contribution per unit × units sold.",
            (
                f"Total contribution: £{case.contribution_per_unit} × "
                f"{case.units_sold:,} = £{case.contribution:,}."
            ),
            "Method: profit = total contribution − fixed cost.",
            (
                f"Profit: £{case.contribution:,} − £{case.fixed_cost:,} "
                f"= £{case.profit:,}."
            ),
        ]
        authoring_context = case.authoring_context()
    elif rule.id == "limitation":
        prompt = (
            f"Explain one limitation of using contribution alone when deciding whether "
            f"{business} should accept a special order."
        )
        scheme = [
            "Contribution includes variable costs but does not by itself identify every relevant fixed or opportunity cost;",
            f"The special order may use capacity that {business} could employ for a more profitable sale, or create an avoidable fixed cost;",
            "A positive contribution therefore does not necessarily mean that accepting the order will produce the best overall profit.",
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.id == "variance_3":
        prompt = (
            "State two possible causes of an adverse direct materials price variance."
        )
        scheme = [
            "The supplier increased the price paid per unit of material;",
            "The business ordered a smaller quantity and lost a bulk-purchase discount.",
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.id == "variance_4":
        prompt = (
            f"Explain two reasons why {business} should investigate an adverse direct "
            "materials price variance before taking action."
        )
        scheme = [
            "An adverse price variance means the actual price paid exceeded the standard price;",
            "A market-wide supplier price increase may be outside the purchasing manager's control;",
            f"{business} should therefore avoid blaming staff until it distinguishes an external price change from poor purchasing;",
            "A smaller order or failure to negotiate may have caused the business to lose a bulk discount;",
            "That cause is controllable and could recur if purchasing procedures are not corrected;",
            f"{business} should therefore identify the cause before choosing a proportionate corrective action.",
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.id == "costing_2":
        prompt = (
            f"State one suitable cost driver for {business}'s purchase-order "
            "processing cost pool."
        )
        scheme = ["Number of purchase orders processed."]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.id == "costing_4":
        prompt = (
            f"Assess whether {business} should replace traditional absorption costing "
            "with activity-based costing when setting product prices."
        )
        scheme = [
            "Activity-based costing assigns overheads to activities and then to products using cost drivers;",
            "It can produce more accurate product costs where products consume support activities in different proportions;",
            f"{business} may therefore set better-informed prices and stop cross-subsidising complex products;",
            "Identifying activities, measuring cost-driver volumes and maintaining the system creates additional cost;",
            "The resulting allocations still depend on judgement and may add little where overheads are low or products are similar;",
            f"{business} should therefore adopt activity-based costing only if the decision benefit from more accurate costs exceeds the implementation cost.",
        ]
        authoring_context = {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        }
    elif rule.kind == "calculation":
        prompt, scheme, authoring_context = _management_calculation(
            rule.id,
            business,
            values,
        )
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
        authoring_context=authoring_context,
    )


def _management_calculation(
    rule_id: str,
    business: str,
    values: list[float],
) -> tuple[str, list[str], dict[str, object]]:
    """Build a complete, internally solved data contract for each numeric task."""

    seeds = [max(2, round(value)) for value in values]
    if rule_id == "budget":
        sales = seeds[4] * 1_000
        variable_cost = seeds[2] * 1_000
        fixed_cost = seeds[1] * 1_000
        opening_cash = seeds[0] * 500
        capital_payment = seeds[3] * 400
        contribution = sales - variable_cost
        profit = sales - variable_cost - fixed_cost
        net_cash_flow = profit - capital_payment
        closing_cash = opening_cash + net_cash_flow
        source = {
            "sales_receipts": sales,
            "variable_cost_payments": variable_cost,
            "fixed_cost_payments": fixed_cost,
            "opening_cash": opening_cash,
            "capital_payment": capital_payment,
        }
        answers = {
            "contribution": contribution,
            "budgeted_profit": profit,
            "net_cash_flow": net_cash_flow,
            "closing_cash": closing_cash,
        }
        prompt = (
            f"Calculate the budgeted profit and closing cash balance for {business}. "
            f"Sales receipts are {_gbp(sales)}, variable-cost payments "
            f"{_gbp(variable_cost)}, fixed-cost payments {_gbp(fixed_cost)}, opening "
            f"cash {_gbp(opening_cash)} and a capital payment of "
            f"{_gbp(capital_payment)}. Show all workings."
        )
        scheme = [
            "Method: contribution = sales receipts − variable-cost payments.",
            f"Contribution: {_gbp(sales)} − {_gbp(variable_cost)} = "
            f"{_gbp(contribution)}.",
            "Method: budgeted profit = contribution − fixed-cost payments.",
            f"Budgeted profit: {_gbp(contribution)} − {_gbp(fixed_cost)} = "
            f"{_gbp(profit)}.",
            "Method: net cash flow = budgeted profit − capital payment.",
            f"Net cash flow: {_gbp(profit)} − {_gbp(capital_payment)} = "
            f"{_gbp(net_cash_flow)}.",
            "Method: closing cash = opening cash + net cash flow.",
            f"Closing cash: {_gbp(opening_cash)} + ({_gbp(net_cash_flow)}) = "
            f"{_gbp(closing_cash)}.",
        ]
    elif rule_id == "variance_1":
        standard_price = seeds[0] + 4
        actual_price = max(1, standard_price - 2)
        actual_quantity = seeds[4] * 100
        variance = (standard_price - actual_price) * actual_quantity
        source = {
            "standard_price_per_kg": standard_price,
            "actual_price_per_kg": actual_price,
            "actual_quantity_kg": actual_quantity,
        }
        answers = {"direct_material_price_variance": variance, "direction": "favourable"}
        prompt = (
            f"Calculate the direct-material price variance for {business}. The standard "
            f"price is {_gbp(standard_price)} per kg, the actual price is "
            f"{_gbp(actual_price)} per kg and {actual_quantity:,} kg were purchased and "
            "used. Show all workings and state whether the variance is favourable or adverse."
        )
        scheme = [
            "Method: price difference = standard price − actual price;",
            f"Price difference: {_gbp(standard_price)} − {_gbp(actual_price)} = "
            f"{_gbp(standard_price - actual_price)} per kg.",
            "Method: direct-material price variance = price difference × actual quantity;",
            f"Direct-material price variance: {_gbp(standard_price - actual_price)} × "
            f"{actual_quantity:,} = {_gbp(variance)} favourable.",
        ]
    elif rule_id == "variance_2":
        standard_rate = seeds[0] + 8
        actual_rate = standard_rate + 2
        standard_hours = seeds[3] * 100
        actual_hours = standard_hours + 100
        budgeted_overhead = seeds[4] * 1_000
        actual_overhead = budgeted_overhead + 2_000
        rate_variance = (standard_rate - actual_rate) * actual_hours
        efficiency_variance = (standard_hours - actual_hours) * standard_rate
        overhead_variance = budgeted_overhead - actual_overhead
        source = {
            "standard_hourly_rate": standard_rate,
            "actual_hourly_rate": actual_rate,
            "standard_hours": standard_hours,
            "actual_hours": actual_hours,
            "budgeted_fixed_overhead": budgeted_overhead,
            "actual_fixed_overhead": actual_overhead,
        }
        answers = {
            "labour_rate_variance": abs(rate_variance),
            "labour_efficiency_variance": abs(efficiency_variance),
            "fixed_overhead_expenditure_variance": abs(overhead_variance),
            "direction": "adverse",
        }
        prompt = (
            f"Calculate the direct-labour rate and efficiency variances and the fixed-overhead "
            f"expenditure variance for {business}. Standard labour is {standard_hours:,} "
            f"hours at {_gbp(standard_rate)} per hour; actual labour is "
            f"{actual_hours:,} hours at {_gbp(actual_rate)} per hour. Budgeted fixed "
            f"overhead is {_gbp(budgeted_overhead)} and actual fixed overhead is "
            f"{_gbp(actual_overhead)}. Show all workings and label each variance."
        )
        scheme = [
            "Method: labour rate variance = (standard hourly rate − actual hourly rate) × actual hours;",
            f"Labour rate variance: ({_gbp(standard_rate)} − {_gbp(actual_rate)}) × "
            f"{actual_hours:,} = {_gbp(abs(rate_variance))} adverse.",
            "Method: labour efficiency variance = (standard hours − actual hours) × standard hourly rate;",
            f"Labour efficiency variance: ({standard_hours:,} − {actual_hours:,}) × "
            f"{_gbp(standard_rate)} = {_gbp(abs(efficiency_variance))} adverse.",
            "Method: fixed-overhead expenditure variance = budgeted fixed overhead − actual fixed overhead;",
            f"Fixed-overhead expenditure variance: {_gbp(budgeted_overhead)} − "
            f"{_gbp(actual_overhead)} = {_gbp(abs(overhead_variance))} adverse.",
            "The labour rate variance is adverse because the actual hourly rate exceeds the standard hourly rate;",
            "The efficiency and overhead variances are adverse because actual hours and actual overhead exceed their comparison figures.",
        ]
    elif rule_id == "costing_1":
        setup_cost_pool = seeds[4] * 6_000
        purchase_order_cost_pool = seeds[2] * 4_000
        total_setups = seeds[0] * 10
        total_purchase_orders = seeds[1] * 20
        product_setups = max(5, seeds[3] // 4)
        product_purchase_orders = max(8, seeds[0] // 2)
        product_units = seeds[4] * 10
        setup_rate = setup_cost_pool / total_setups
        purchase_order_rate = purchase_order_cost_pool / total_purchase_orders
        setup_overhead = setup_rate * product_setups
        purchase_order_overhead = purchase_order_rate * product_purchase_orders
        total_overhead = setup_overhead + purchase_order_overhead
        overhead_per_unit = total_overhead / product_units
        source = {
            "setup_cost_pool": setup_cost_pool,
            "purchase_order_cost_pool": purchase_order_cost_pool,
            "total_setups": total_setups,
            "total_purchase_orders": total_purchase_orders,
            "product_setups": product_setups,
            "product_purchase_orders": product_purchase_orders,
            "product_units": product_units,
        }
        answers = {
            "setup_rate": setup_rate,
            "purchase_order_rate": purchase_order_rate,
            "setup_overhead": setup_overhead,
            "purchase_order_overhead": purchase_order_overhead,
            "total_overhead": total_overhead,
            "overhead_per_unit": overhead_per_unit,
        }
        prompt = (
            f"Calculate the activity-based overhead cost per unit for a product made by {business}. "
            f"Set-up costs are {_gbp(setup_cost_pool)} for {total_setups:,} set-ups and "
            f"purchase-order costs are {_gbp(purchase_order_cost_pool)} for "
            f"{total_purchase_orders:,} orders. The product uses {product_setups:,} set-ups "
            f"and {product_purchase_orders:,} orders for {product_units:,} units. Show all workings."
        )
        scheme = [
            "Method: set-up driver rate = set-up cost pool ÷ total set-ups;",
            f"Set-up driver rate: {_gbp(setup_cost_pool)} ÷ {total_setups:,} = "
            f"{_gbp_decimal(setup_rate)};",
            "Method: purchase-order driver rate = purchase-order cost pool ÷ total orders;",
            f"Purchase-order driver rate: {_gbp(purchase_order_cost_pool)} ÷ "
            f"{total_purchase_orders:,} = {_gbp_decimal(purchase_order_rate)};",
            f"Set-up overhead assigned: {_gbp_decimal(setup_rate)} × "
            f"{product_setups:,} = {_gbp_decimal(setup_overhead)};",
            f"Purchase-order overhead assigned: {_gbp_decimal(purchase_order_rate)} × "
            f"{product_purchase_orders:,} = {_gbp_decimal(purchase_order_overhead)};",
            f"Total activity-based overhead: {_gbp_decimal(setup_overhead)} + "
            f"{_gbp_decimal(purchase_order_overhead)} = {_gbp_decimal(total_overhead)};",
            f"Overhead cost per unit: {_gbp_decimal(total_overhead)} ÷ "
            f"{product_units:,} = {_gbp_decimal(overhead_per_unit)}.",
        ]
    elif rule_id == "costing_3":
        contribution_a = seeds[4] + 8
        hours_a = max(2, seeds[0] // 3)
        contribution_b = seeds[3] + 6
        hours_b = max(2, seeds[1] // 3)
        return_a = contribution_a / hours_a
        return_b = contribution_b / hours_b
        ranked_first = (
            "Product A"
            if return_a > return_b
            else "Product B"
            if return_b > return_a
            else "Equal priority"
        )
        source = {
            "product_a_contribution": contribution_a,
            "product_a_scarce_hours": hours_a,
            "product_b_contribution": contribution_b,
            "product_b_scarce_hours": hours_b,
        }
        answers = {
            "product_a_contribution_per_scarce_hour": return_a,
            "product_b_contribution_per_scarce_hour": return_b,
            "ranked_first": ranked_first,
        }
        prompt = (
            f"Calculate the contribution per scarce labour hour for both products made by "
            f"{business}. Product A earns {_gbp(contribution_a)} contribution and uses {hours_a} "
            f"scarce hours per unit; Product B earns {_gbp(contribution_b)} contribution and uses "
            f"{hours_b} scarce hours per unit. Show all workings and rank the products."
        )
        scheme = [
            "Method for Product A: contribution per unit ÷ scarce hours per unit;",
            f"Product A: {_gbp(contribution_a)} ÷ {hours_a} = "
            f"{_gbp_decimal(return_a)} per scarce hour.",
            "Method for Product B: contribution per unit ÷ scarce hours per unit;",
            f"Product B: {_gbp(contribution_b)} ÷ {hours_b} = "
            f"{_gbp_decimal(return_b)} per scarce hour.",
            f"Ranking: {ranked_first} should be produced first because it has the higher contribution per scarce hour.",
        ]
    else:
        raise ValueError(f"unsupported accounting calculation rule: {rule_id}")

    prompt_values = [value for value in source.values()]
    return prompt, scheme, {
        "preserve_prompt": True,
        "preserve_mark_scheme": True,
        "source_data": source,
        "verified_answers": answers,
        "prompt_values": prompt_values,
        "task_scope": CALCULATION_TASKS[rule_id],
    }


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
