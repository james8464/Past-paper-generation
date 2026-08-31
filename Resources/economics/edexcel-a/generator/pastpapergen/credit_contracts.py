"""Task-specific credit projections; examples never add to a tariff twice."""

from __future__ import annotations

import re

# Each scenario states a direction rather than asking about unspecified 'changes'.
# The pair supplies an economic mechanism and its consequence, not revision notes.
TOPIC_CHAINS = {
    "1.1": (
        "Consumers compare extra benefit with extra cost.",
        "A further purchase is worthwhile only while marginal benefit is at least marginal cost.",
    ),
    "1.2.1": (
        "Consumers compare extra benefit with extra cost.",
        "A further purchase is worthwhile only while marginal benefit is at least marginal cost.",
    ),
    "1.2.2": (
        "Consumer incomes increase for a normal good.",
        "Demand shifts right; at the original price excess demand encourages a higher equilibrium price and quantity.",
    ),
    "1.2.3": (
        "The cost of a productive input increases.",
        "Higher marginal costs reduce supply; the equilibrium price rises and equilibrium quantity falls, other things equal.",
    ),
    "1.2.4": (
        "Demand increases while the supply curve remains unchanged.",
        "Excess demand at the original price bids price up, inducing an extension of supply to a higher equilibrium quantity.",
    ),
    "1.3": (
        "Production imposes a cost on people outside the market transaction.",
        "Private production decisions omit external costs, so market output can exceed the socially efficient output.",
    ),
    "1.4": (
        "An indirect tax is imposed on a product with external costs.",
        "The tax increases private marginal cost, reducing quantity demanded and produced and potentially reducing external damage.",
    ),
    "2.1": (
        "Aggregate demand falls while productive capacity is unchanged.",
        "Firms reduce output and derived demand for labour, increasing cyclical unemployment and reducing household incomes.",
    ),
    "2.2": (
        "Investment spending increases while there is spare productive capacity.",
        "Investment is an injection into aggregate demand; additional income induces further consumption, increasing real output.",
    ),
    "2.3": (
        "Investment in technology raises labour productivity.",
        "Lower unit costs and greater productive capacity shift aggregate supply right, allowing more output with less price pressure.",
    ),
    "2.4": (
        "Government spending increases without an immediate increase in taxation.",
        "The injection raises recipients' incomes; induced consumption generates further income, limited by saving, taxation and imports.",
    ),
    "2.5": (
        "Skills investment increases workers' productivity.",
        "Potential output rises; when additional capacity is used, real incomes and consumption possibilities can increase.",
    ),
    "2.6": (
        "Interest rates are increased to reduce demand-pull inflation.",
        "Higher borrowing costs reduce consumption and investment, lowering price pressure but risking weaker output and higher unemployment.",
    ),
    "3.1": (
        "A firm expands its scale of production.",
        "Spreading fixed costs or specialising production can lower average costs and improve price competitiveness, subject to diseconomies.",
    ),
    "3.2": (
        "Managers prioritise sales growth over maximum short-run profit.",
        "A lower price and higher output can increase sales, but output beyond the profit maximum reduces profit at the margin.",
    ),
    "3.3": (
        "A firm's average total cost rises while its selling price is unchanged.",
        "Profit per unit falls; at unchanged output, total profit falls and losses may occur.",
    ),
    "3.4": (
        "An industry has high barriers to entry.",
        "The threat of entry is weaker, allowing incumbents greater discretion over prices; actual power also depends on rivalry and substitutes.",
    ),
    "3.5": (
        "Firms increase demand for labour while labour supply is unchanged.",
        "Competition for workers raises the equilibrium wage and employment; the size of the response depends on labour-supply elasticity.",
    ),
    "3.6": (
        "A subsidy lowers producers' marginal costs.",
        "Supply expands, reducing the consumer price and increasing quantity, while creating an opportunity cost for public funds.",
    ),
    "4.1": (
        "The domestic currency appreciates.",
        "Exports become more expensive to overseas buyers and imports cheaper domestically; export volume and net trade may fall, depending on elasticities.",
    ),
    "4.2": (
        "Transfers raise the disposable incomes of lower-income households.",
        "Income inequality can fall and access to necessities can improve; the effect on poverty also depends on absolute income levels.",
    ),
    "4.3": (
        "Improved transport infrastructure reduces firms' distribution costs.",
        "Market access and investment can increase, supporting employment and development; benefits depend on maintenance and access for poorer groups.",
    ),
    "4.4": (
        "A bank expands lending to businesses.",
        "Finance enables investment, but excessive risk-taking can raise default losses and threaten financial stability.",
    ),
    "4.5": (
        "Government raises spending on education.",
        "Human capital and productivity can improve, raising productive capacity, but spending displaces another use of public funds.",
    ),
}

STYLE_CHAINS = {
    "marginal_utility_table": (
        "Additional units yield diminishing marginal utility.",
        "A rational buyer stops when the marginal benefit of another unit is below its marginal cost; total utility alone is not the purchase criterion.",
    ),
    "opportunity_cost_ppc_table": (
        "Capital and consumer goods compete for scarce resources.",
        "Producing more capital goods requires forgoing consumer goods; that forgone alternative is the opportunity cost.",
    ),
    "market_share_bar_chart": (
        "A few large firms account for substantial market shares.",
        "Concentration is consistent with oligopoly and interdependence; firms consider rivals' responses to price changes, but concentration alone does not prove collusion.",
    ),
    "concentration_ratio_table": (
        "A few large firms account for substantial market shares.",
        "Market concentration may weaken competitive pressure and support higher prices, depending on entry barriers and rival behaviour.",
    ),
    "business_objective_context": (
        "Managers may be rewarded for revenue or market-share growth.",
        "This incentive can make them choose greater sales even when the additional output reduces short-run profit.",
    ),
    "financial_market_context": (
        "Market participants may manipulate prices or information for private gain.",
        "Distorted price signals misallocate finance and can reduce trust; merely describing legitimate credit provision does not explain market rigging.",
    ),
    "imperfect_information_context": (
        "Buyers lack relevant information about a product's costs or benefits.",
        "Their perceived marginal benefit can differ from its actual benefit, causing over- or under-consumption and a welfare loss.",
    ),
    "xed_context": (
        "A price change for one product affects demand for another.",
        "Positive cross elasticity indicates substitutes, while negative cross elasticity indicates complements; apply the stated relationship rather than confuse it with own-price elasticity.",
    ),
    "minimum_wage_context": (
        "A binding minimum wage raises hourly labour costs.",
        "Firms may reduce labour demand or substitute capital, although productivity, retention and market power can alter the employment effect.",
    ),
    "investment_line_chart": (
        "Investment is a component of aggregate demand.",
        "A fall in investment reduces the initial injection and induced consumption, lowering equilibrium real output when other components do not offset it.",
    ),
    "current_account_line_chart": (
        "Higher domestic spending can increase demand for imports.",
        "Imports rising relative to exports reduce net trade and can widen the current-account deficit; accept weaker foreign demand reducing exports as an alternative.",
    ),
    "exchange_rate_index_chart": (
        "An appreciation raises the foreign-currency price of domestic exports.",
        "Overseas quantity demanded may fall, reducing export sales; the revenue effect depends on demand elasticity.",
    ),
    "household_savings_line_chart": (
        "Uncertainty can raise precautionary saving.",
        "Households defer consumption to build a financial buffer, increasing saving as a proportion of disposable income; a recovery in confidence can reverse this.",
    ),
    "terms_of_trade_index_chart": (
        "A rising terms-of-trade index means export prices rise relative to import prices.",
        "Higher export prices can raise receipts when demand is inelastic, but lower export volumes can offset this; the current-account effect is therefore conditional.",
    ),
    "labour_inactivity_context": (
        "More working-age people leave the labour force.",
        "Effective labour supply and productive potential can fall, worsening recruitment constraints; inactivity is not the same as unemployment.",
    ),
    "wage_rate_table": (
        "Higher real wages raise the reward from employment.",
        "Participation or hours supplied may increase through substitution towards work, although income effects or non-wage barriers may limit the response.",
    ),
}


def drawing_contract(question, part):
    if not any("Correctly identifies or defines" in p for p in part.mark_scheme):
        return part.prompt, part.mark_scheme
    kind = question.stimulus_kind
    if kind == "context_extract":
        kind = {
            "1.2.2": "demand_increase",
            "1.2.4": "demand_increase",
            "1.2.3": "supply_decrease",
            "1.3": "negative_externality",
            "1.4": "indirect_tax",
            "3.1": "economies_of_scale",
            "3.3": "fixed_cost_increase",
            "3.4": "monopoly_diagram",
            "3.5": "labour_market_diagram",
            "3.6": "subsidy",
        }[question.topic_id]
    records = {
        "demand_increase": (
            "Draw a demand and supply diagram showing an increase in demand with supply unchanged.",
            [
                "Price and quantity axes; downward demand and upward supply.",
                "Correct original equilibrium.",
                "Demand shifts right with supply unchanged.",
                "New equilibrium has higher price and quantity, correctly identified.",
            ],
        ),
        "supply_decrease": (
            "Draw a demand and supply diagram showing higher input costs with demand unchanged.",
            [
                "Price and quantity axes; downward demand and upward supply.",
                "Correct original equilibrium.",
                "Supply shifts left/up following higher costs.",
                "New equilibrium has higher price and lower quantity, correctly identified.",
            ],
        ),
        "negative_externality": (
            "Draw a negative production externality diagram showing market output, socially efficient output and welfare loss.",
            [
                "Marginal costs/benefits and output axes; MSB = MPB.",
                "MSC above MPC for positive output.",
                "Market output where MPB = MPC exceeds efficient output where MSB = MSC.",
                "Welfare-loss area between MSC and MSB over the excess-output range.",
            ],
        ),
        "indirect_tax": (
            "Draw a demand and supply diagram showing the effect of a per-unit indirect tax.",
            [
                "Price and quantity axes, demand and initial supply.",
                "Correct initial equilibrium.",
                "Post-tax supply shifted vertically upwards by the tax.",
                "Higher consumer price, lower quantity and producer price net of tax shown consistently.",
            ],
        ),
        "subsidy": (
            "Draw a demand and supply diagram showing the effect of a per-unit producer subsidy.",
            [
                "Price and quantity axes, demand and initial supply.",
                "Correct initial equilibrium.",
                "Post-subsidy supply shifted down by the subsidy.",
                "Lower consumer price and higher equilibrium quantity; producer receipt including subsidy shown consistently.",
            ],
        ),
        "economies_of_scale": (
            "Draw a long-run average cost diagram showing expansion over a range with economies of scale.",
            [
                "Average cost and output axes.",
                "LRAC curve with a downward-sloping economies-of-scale range.",
                "Initial and higher output both located in that range.",
                "Lower average cost at the higher output, identified with projections or labels.",
            ],
        ),
        "fixed_cost_increase": (
            "Draw a cost and revenue diagram for a price-taking firm showing how higher fixed costs reduce profit at unchanged price and output.",
            [
                "Costs/revenues and output axes, horizontal AR = MR.",
                "MC crossing MR at the selected output and an initial AC below price at that output.",
                "Higher AC following the fixed-cost increase; MC unchanged.",
                "Smaller profit area at the same price and output, correctly identified.",
            ],
        ),
        "monopoly_diagram": (
            "Draw a cost and revenue diagram showing a profit-maximising monopoly earning supernormal profit.",
            [
                "Costs/revenues and output axes; downward AR with MR below AR.",
                "Appropriate MC and AC curves.",
                "Profit-maximising output at MC = MR with price read from AR.",
                "Price above AC at that output and the supernormal-profit area identified.",
            ],
        ),
        "perfect_competition_diagram": (
            part.prompt,
            [
                "Costs/revenues and output axes with horizontal AR = MR.",
                "Appropriate MC and U-shaped AC.",
                "Profit-maximising output where MC = MR.",
                "Price equals AC at its minimum, demonstrating normal profit.",
            ],
        ),
        "monopsony_diagram": (
            part.prompt,
            [
                "Wage/cost of labour and employment axes; upward ACL/labour supply.",
                "MCL above ACL and downward MRP/labour demand.",
                "Employment where MCL = MRP.",
                "Wage read from ACL at that employment, below the competitive wage.",
            ],
        ),
        "labour_market_diagram": (
            "Draw a labour market diagram showing an increase in demand for labour with labour supply unchanged.",
            [
                "Wage and employment axes; labour demand and labour supply.",
                "Correct initial equilibrium.",
                "Labour demand shifts right with labour supply unchanged.",
                "Higher equilibrium wage and employment correctly identified.",
            ],
        ),
        "business_objective_context": (
            part.prompt,
            [
                "Costs/revenues and output axes with downward AR and lower MR.",
                "Appropriate MC and AC curves.",
                "Profit-maximising output at MC = MR with its price on AR.",
                "Distinct revenue-maximising output at MR = 0 and its price on AR.",
            ],
        ),
        "minimum_wage_context": (
            part.prompt,
            [
                "Wage and employment axes; labour demand and labour supply.",
                "Correct original equilibrium.",
                "Binding minimum wage above the equilibrium wage.",
                "Lower labour demanded and excess labour supply at that minimum wage.",
            ],
        ),
    }
    if kind not in records:
        raise ValueError(f"unsupported Edexcel drawing credit: {kind}")
    prompt, points = records[kind]
    return prompt, [
        f"{'AO1' if i < 2 else 'AO2'} (1 mark): {point}"
        for i, point in enumerate(points)
    ]


def clean_points(points: list[str]) -> list[str]:
    result = []
    for point in points:
        text = re.sub(
            r"^(?:(?:Factor|Conflict)\s+\d+\s*[—–-]\s*)?AO[1-4][^:]*:\s*",
            "",
            point.strip(),
        )
        if not text or point.strip().endswith(":"):
            continue
        if text not in result:
            result.append(text)
    return result


def short_credit(question, part, source) -> list[str]:
    existing = part.mark_scheme
    generic = any("Correctly identifies or defines" in p for p in existing)
    if part.command_word == "draw":
        if not generic:
            return existing
        if question.stimulus_kind == "business_objective_context":
            return [
                "AO1 (1 mark): Correct downward-sloping AR and lower MR curves on costs/revenues and output axes.",
                "AO1 (1 mark): Appropriate MC and AC curves.",
                "AO2 (1 mark): Profit-maximising output at MC = MR and its price on AR.",
                "AO2 (1 mark): Distinct revenue-maximising output at MR = 0 and its price on AR.",
            ]
        if question.stimulus_kind == "minimum_wage_context":
            return [
                "AO1 (1 mark): Wage and employment axes with upward labour supply and downward labour demand.",
                "AO1 (1 mark): Correct original labour-market equilibrium.",
                "AO2 (1 mark): Minimum wage shown above the equilibrium wage.",
                "AO2 (1 mark): Lower quantity of labour demanded and excess labour supply at the minimum wage.",
            ]
        return [
            "AO1 (1 mark): Correctly label both axes for the economic model required by the stated task.",
            "AO1 (1 mark): Draw and label the relevant original curves and equilibrium.",
            f"AO2 (1 mark): Represent the specified change: {TOPIC_CHAINS[question.topic_id][0]}",
            f"AO2 (1 mark): Show the corresponding new outcome: {TOPIC_CHAINS[question.topic_id][1]}",
        ]
    if not generic and part.marks == 2:
        points = clean_points(existing)
        if source.kind == "terms_of_trade_index_chart":
            points = [
                f"Recognise that the increase from {source.values[0]} to {source.values[-1]} means average export prices rose relative to average import prices.",
                "Export receipts may rise if overseas demand is sufficiently price inelastic, but lower export volumes may offset this; link the mechanism to the current account.",
            ]
        return [f"AO1 (1 mark): {points[0]}", f"AO3 (1 mark): {points[1]}"]
    if not generic and part.marks == 4:
        points = clean_points(existing)
        # Existing source-specific theory/application/mechanism remains useful,
        # but the analysis chain is one budget, not two separately additive marks.
        return [
            f"AO1 (2 marks): {points[0]} Identify the relevant factor and explain its economic meaning.",
            f"AO2 (1 mark): {points[1]}",
            f"AO3 (1 mark): {' '.join(points[2:])}",
            "Accept an equivalent relevant factor with its own source application and developed link, within the same tariff.",
        ]
    cause, mechanism = STYLE_CHAINS.get(source.kind, TOPIC_CHAINS[question.topic_id])
    if part.marks == 2:
        return [f"AO1 (1 mark): {cause}", f"AO3 (1 mark): {mechanism}"]
    evidence = source.context
    if source.rows:
        evidence = "; ".join(
            " | ".join(cell.printed() for cell in row) for row in source.rows[:3]
        )
    elif source.values:
        evidence = f"{source.labels[0]}: {source.values[0]} {source.y_label}; {source.labels[-1]}: {source.values[-1]} {source.y_label}"
    return [
        f"AO1 (2 marks): {cause} Identify the relevant economic concept and explain its meaning.",
        f"AO2 (1 mark): Apply a relevant detail from this source: {evidence}",
        f"AO3 (1 mark): {mechanism}",
        "Accept another valid source-linked mechanism answering this task; unrelated facts or a repeated point earn no extra credit.",
    ]


def _instance_synoptic_points(question, points):
    text = question.source_text
    patterns = {
        "investment": r"planned investment by (\d+)%",
        "output": r"Output in the sector changed by (\d+)%",
        "price": r"international prices moved by (\d+)%",
    }
    values = {
        role: match.group(1)
        for role, pattern in patterns.items()
        if (match := re.search(pattern, text))
    }
    result = []
    for point in points:
        for role, value in values.items():
            if role in point.casefold() and "%" in point:
                point = re.sub(r"\d+%", value + "%", point)
                break
        if "energy" not in question.source_title.casefold():
            point = point.replace(
                "energy and utilities", question.source_title.lower()
            ).replace("energy", "sector")
        result.append(point)
    return result


KNOWLEDGE_FACTS = {
    "1.2.2": (
        "Real income is purchasing power after allowing for the price level.",
        "Income elasticity of demand is the percentage change in quantity demanded divided by the percentage change in income.",
    ),
    "1.2.3": (
        "Price elasticity of supply measures the responsiveness of quantity supplied to a change in price.",
        "Price-inelastic supply means PES is less than one: the proportional quantity-supplied response is smaller than the proportional price change.",
    ),
    "1.2.4": (
        "Market equilibrium occurs where quantity demanded equals quantity supplied.",
        "Consumer surplus is willingness to pay above the actual price; producer surplus is receipts above the minimum supply price.",
    ),
    "1.3": (
        "A negative production externality is an uncompensated cost imposed on third parties by production.",
        "Marginal social cost includes marginal private cost plus marginal external cost.",
    ),
    "1.4": (
        "An indirect tax is charged on production or expenditure rather than directly on income.",
        "A specific tax charges a fixed amount per unit; an ad valorem tax charges a proportion of value.",
    ),
    "3.1": (
        "Economies of scale arise when expansion lowers long-run average cost.",
        "The long run permits all factors of production to vary; short-run spare-capacity use alone is not an economy of scale.",
    ),
    "3.2": (
        "Profit is total revenue minus total cost, so profit maximisation is distinct from maximising sales receipts.",
        "Satisficing means achieving an acceptable level of profit while pursuing another objective.",
    ),
    "3.3": (
        "Profit is total revenue minus total cost.",
        "Fixed costs do not change with output in the short run, whereas variable costs do.",
    ),
    "3.4": (
        "Contestability depends on the threat of entry and exit, not simply the current number of firms.",
        "Sunk entry costs cannot be recovered on exit and therefore create a risk for potential entrants.",
    ),
    "3.5": (
        "Demand for labour is derived from demand for the output it produces.",
        "Labour-supply elasticity measures the proportional employment-supply response to a proportional wage change.",
    ),
    "3.6": (
        "A maximum price is a legal ceiling on the price charged.",
        "The ceiling is binding only when it is below the market-clearing price.",
    ),
    "2.1": (
        "Aggregate demand is planned spending on domestically produced goods and services.",
        "Cyclical unemployment results from deficient aggregate demand, unlike unemployment caused by a skills mismatch.",
    ),
    "2.2": (
        "Investment is spending on capital goods and forms part of aggregate demand.",
        "An injection enters the income flow, whereas saving, taxation and imports are leakages.",
    ),
    "2.3": (
        "Long-run aggregate supply is the economy's sustainable productive potential.",
        "Productivity is output per unit of input, not simply an increase in total output.",
    ),
    "2.4": (
        "The multiplier is the final change in national income divided by the initial injection.",
        "Saving, taxation and imports withdraw spending from the domestic income flow.",
    ),
    "2.5": (
        "Actual economic growth is an increase in real output.",
        "Potential growth is an increase in productive capacity and need not be fully realised immediately.",
    ),
    "2.6": (
        "Bank Rate is the central bank's policy interest rate.",
        "Demand-pull inflation is rising prices caused by aggregate demand pressing against available productive capacity.",
    ),
    "4.1": (
        "An appreciation increases the value of a currency in terms of other currencies.",
        "Exports are sales abroad and imports are purchases from abroad; net exports are exports minus imports.",
    ),
    "4.2": (
        "Income inequality concerns how unevenly income is distributed.",
        "Relative poverty concerns income below a relative threshold, whereas absolute poverty concerns inability to meet basic needs.",
    ),
    "4.3": (
        "Foreign direct investment involves a lasting ownership interest and control in an overseas business.",
        "Economic development includes health, education and living standards, not just output per head.",
    ),
    "4.4": (
        "Banks channel finance from savers and other funding sources to borrowers.",
        "Asymmetric information means one party knows more about a transaction's relevant risks than the other.",
    ),
    "4.5": (
        "Public investment creates assets and is part of government spending in aggregate demand.",
        "Opportunity cost is the value of the next-best alternative use of committed resources.",
    ),
}


def _knowledge_pair(topic_id):
    return KNOWLEDGE_FACTS[topic_id]


def extended_credit(
    question, budget: dict[str, int], source=None
) -> tuple[list[str], dict]:
    points = clean_points(question.mark_scheme)
    if source and question.number.startswith(("1(", "2(")):
        if question.topic_id == "3.5" and "tourism" in question.source_title.casefold():
            points = [
                p.replace(
                    "healthcare roles",
                    "experienced chef and hospitality-supervisor roles",
                )
                .replace("treatment capacity", "service capacity")
                .replace("overseas qualifications", "overseas experience")
                for p in points
            ]
        if question.topic_id == "1.2.3" and question.marks == 5:
            price = source.givens["Price change"].number
            quantity = source.givens["Quantity supplied change"].number
            points = [
                "Price elasticity of supply measures the responsiveness of quantity supplied to price.",
                f"Use the price increase of {price}% and quantity-supplied increase of {quantity}% in the figure.",
                "Use the extract's limited capacity, fixed contracts or delayed access to inputs.",
                "The selected constraint prevents output expanding quickly after the price rise, so the smaller proportional supply response indicates price-inelastic supply; a qualitative comparison is sufficient.",
            ]
        elif question.topic_id == "3.1" and question.marks == 8:
            investment = source.givens["Capital spending change"].number
            points = [
                re.sub(r"5% in 2025", f"{investment}% in the stated period", p)
                for p in points
            ]
        # The old case examples used a different seed's percentages. Replace
        # only named input roles, never every matching number in a string.
        elif question.topic_id == "1.3" and question.marks == 12:
            match = re.search(r"prices changed by (\d+)%", source.context)
            if match:
                points = [
                    p.replace("29%", match.group(1) + "%")
                    .replace("energy prices", "sector prices")
                    .replace("energy output", "sector output")
                    for p in points
                ]
        elif question.topic_id in {"2.3", "4.5"} and question.marks == 25:
            points = _instance_synoptic_points(question, points)
    generic = any(
        "Correctly identifies or defines" in p or "syllabus alignment" in p
        for p in question.mark_scheme
    )
    banned = (
        "syllabus alignment",
        "Accurately recalls",
        "Demonstrates knowledge",
        "Makes precise use",
        "Constructs a coherent chain",
        "Selects and applies relevant",
        "Shows how the theoretical",
        "Develops the analysis",
        "Uses appropriate economic",
        "Weighs competing",
        "Assesses the strength",
        "Makes a final, well-supported",
        "Where appropriate",
        "Where numerical",
        "Identifies limitations",
        "Level ",
        "Levels-based",
        "cannot reach Level",
        "Correctly identifies",
        "Accurately states",
        "Applies the concept",
        "Uses relevant numerical",
        "Develops a logical",
        "Connects the analysis",
    )
    points = [p for p in points if not any(b in p for b in banned)]
    # Existing explicitly source-authored extended routes supply contextual chains.
    # No broad revision notes are used as indicative credit.
    if generic or len(points) < 3:
        cause, mechanism = TOPIC_CHAINS[question.topic_id]
        points = [
            cause,
            mechanism,
            f"Apply the stated source evidence to this task: {question.prompt}",
            "Test the mechanism against the assumptions, affected groups and time period in the source.",
        ]
    if question.marks < 8:
        if question.topic_id == "2.6" and "higher Bank Rate" in question.prompt:
            points = [
                points[0],
                points[1],
                "Apply the extract's mortgage or business-loan exposure to the affected households or firms.",
                "Higher debt-servicing costs reduce interest-sensitive consumption or investment; weaker aggregate demand reduces demand-pull inflation. One developed transmission route is sufficient.",
            ]
        knowledge_name, knowledge_meaning = _knowledge_pair(question.topic_id)
        if question.topic_id == "4.1" and "trade barriers" in question.prompt:
            knowledge_name = "A trade barrier restricts cross-border exchange, unlike a domestic transaction cost."
            knowledge_meaning = "A tariff is a tax on imports; reducing it lowers the tax-inclusive import price, other things equal."
        scheme = [
            f"AO1 (1 mark): {knowledge_name}",
            f"AO1 (1 mark): {knowledge_meaning}",
            f"AO2 (1 mark): From {question.source_reference or 'the supplied source'}: {points[1]}",
            f"AO2 (1 mark): From {question.source_reference or 'the supplied source'}: {points[2]}",
            f"AO3 (1 mark): {' '.join(points[3:])}",
        ]
        return scheme, {"scheme_mode": "points", "credit": scheme}
    evaluation = budget["AO4"]
    kaa = question.marks - evaluation
    if question.marks == 8:
        if len(points) == 8:
            knowledge, application, analysis, limits = (
                [points[i] for i in indexes]
                for indexes in ([0, 4], [1, 5], [2, 6], [3, 7])
            )
        elif len(points) == 7:
            knowledge = list(_knowledge_pair(question.topic_id))
            application, analysis, limits = points[1:3], points[3:5], points[5:7]
        else:
            raise ValueError(
                "Eight-mark task needs two complete source-linked credit routes"
            )
        scheme = [
            "Point-based credit: up to 6 KAA marks plus up to 2 evaluation marks; no level bands.",
            *[
                f"{ao} (1 mark): {point}"
                for ao, group in (
                    ("AO1", knowledge),
                    ("AO2", application),
                    ("AO3", analysis),
                )
                for point in group
            ],
            "AO4 (up to 2 marks): Award 2 for one developed relevant qualification, or 1 each for two distinct relevant qualifications. An overall conclusion is not required.",
            *[
                f"Evaluation example (within the same 2-mark budget): {point}"
                for point in limits
            ],
            "Accept equivalent source-linked factors and reasoning within these budgets; no credit twice for the same point.",
        ]
        return scheme, {
            "scheme_mode": "points",
            "credit": scheme,
            "kaa_marks": 6,
            "evaluation_marks": 2,
        }
    bands = {
        10: [(1, 2), (3, 4), (5, 6)],
        12: [(1, 2), (3, 5), (6, 8)],
        15: [(1, 3), (4, 6), (7, 9)],
        25: [(1, 4), (5, 8), (9, 12), (13, 16)],
    }[question.marks]
    evaluation_bands = {
        2: [[1, 2]],
        4: [[1, 2], [3, 4]],
        6: [[1, 2], [3, 4], [5, 6]],
        9: [[1, 3], [4, 6], [7, 9]],
    }[evaluation]
    caps = []
    if question.source_reference:
        caps.append(
            "Highest KAA band requires relevant application of the designated source, not an unrelated example."
        )
    if re.search(r"\b(two|policies|methods|strategies)\b", question.prompt, re.I):
        caps.append(
            "Highest KAA band requires the breadth requested in the question; one route alone cannot satisfy a plural task."
        )
    if "diagram" in question.prompt.casefold():
        caps.append(
            "Highest KAA band requires a correct relevant diagram integrated into the explanation."
        )
    if question.marks == 25 and question.section in {"A", "B"}:
        caps.append(
            "For this synoptic task, the strongest answer integrates relevant microeconomic and macroeconomic effects."
        )
    kaa_descriptors = [
        "Limited relevant knowledge with isolated assertions; context is absent or incidental and causal links are missing or unreliable.",
        "Relevant knowledge is applied to the task with some causal development, but explanation or contextual support is uneven and important links remain incomplete.",
        "Accurate knowledge supports connected economic reasoning, with relevant source evidence used to explain the requested effects and sufficient breadth to address the task.",
    ]
    if len(bands) == 4:
        kaa_descriptors[-1] = (
            "Mostly accurate, contextual reasoning develops several relevant effects; some links or integration remain uneven, although the argument addresses the task coherently."
        )
        kaa_descriptors.append(
            "Precise economic reasoning is sustained throughout a coherent argument; contextual evidence supports complete causal chains and the full scope of the task is integrated."
        )
    evaluation_descriptors = [
        "A relevant qualification or alternative is identified, but its explanation is brief and its importance for this particular task is not established.",
        "Relevant qualifications are developed in context, explaining how assumptions or competing effects alter the outcome and supporting an answer to the question.",
    ]
    if len(evaluation_bands) == 3:
        evaluation_descriptors[-1] = (
            "Relevant qualifications are explained with some contextual support; competing effects are considered but their relative importance or the final judgement is uneven."
        )
        evaluation_descriptors.append(
            "Sustained contextual evaluation weighs competing effects and their importance; a reasoned judgement follows from explicit conditions, evidence and the question's focus."
        )
    points = [
        re.sub(
            r"Award 1 mark for identifying (.*?); award 2 only when the response develops",
            r"Consider \1; stronger assessment develops",
            p,
            flags=re.I,
        )
        for p in points
    ]
    scheme = [
        "Levels-based credit: use best fit separately for KAA and evaluation; the indicative examples are not a point-counting grid.",
        f"Knowledge (AO1), Application (AO2) and Analysis (AO3): 0 for no relevant credit; up to {kaa} KAA marks.",
        *[
            f"KAA {lo}-{hi} marks: {descriptor}"
            for (lo, hi), descriptor in zip(bands, kaa_descriptors, strict=True)
        ],
        f"Evaluation (AO4): 0 for no relevant assessment; up to {evaluation} marks, separately from KAA.",
        *[
            f"Evaluation {lo}-{hi} marks: {descriptor}"
            for (lo, hi), descriptor in zip(
                evaluation_bands, evaluation_descriptors, strict=True
            )
        ],
        "Indicative content: the routes below are alternatives/examples, not additive marks. Do not award the same point in two budgets.",
        "Accept an equivalent valid economic argument or evaluation when it answers this task and uses the designated evidence; the examples below are not an exhaustive checklist.",
        *caps,
        *points,
    ]
    return scheme, {
        "scheme_mode": "levels",
        "credit": points,
        "kaa_marks": kaa,
        "kaa_bands": [list(band) for band in bands],
        "evaluation_marks": evaluation,
        "evaluation_bands": evaluation_bands,
        "highest_band_conditions": caps,
        "kaa_descriptors": kaa_descriptors,
        "evaluation_descriptors": evaluation_descriptors,
    }
