from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WrittenTaskProfile:
    focus_terms: tuple[str, ...]
    source_evidence: str
    data_mechanism: str
    diagram_contract: dict[str, str]
    analysis_prompt: str
    analysis_points: tuple[str, ...]
    evaluation_view: str
    evaluation_points: tuple[str, ...]
    recommendation: str


def _diagram(
    *,
    visual_kind: str,
    curve: str,
    direction: str,
    cause: str,
    effect: str,
    y_axis: str,
    x_axis: str,
    demand_label: str = "",
    supply_label: str = "",
) -> dict[str, str]:
    return {
        "visual_kind": visual_kind,
        "curve": curve,
        "direction": direction,
        "cause": cause,
        "effect": effect,
        "y_axis": y_axis,
        "x_axis": x_axis,
        "demand_label": demand_label,
        "supply_label": supply_label,
    }


PROFILES: dict[str, WrittenTaskProfile] = {
    "4.1.1": WrittenTaskProfile(
        ("opportunity cost", "productivity", "production possibility frontier"),
        "Investment has raised labour productivity and made some resources more adaptable between uses.",
        "greater resource mobility reduces the opportunity cost of reallocating production",
        _diagram(
            visual_kind="ppf_shift",
            curve="PPF",
            direction="outward",
            cause="an increase in labour productivity",
            effect="an outward shift of the production possibility frontier",
            y_axis="Capital goods",
            x_axis="Consumer goods",
        ),
        "Explain why allocating more resources to capital goods creates an opportunity cost in terms of current consumer goods.",
        (
            "Define opportunity cost as the next best alternative forgone.",
            "Use a production possibility frontier to show the movement from consumer goods towards capital goods.",
            "Explain how investment can expand future productive capacity while requiring current consumption to be sacrificed.",
        ),
        "Evaluate the view that improving labour mobility is the best way to reduce the economic cost of scarce resources.",
        (
            "Analyse how occupational or geographical mobility can reduce structural unemployment and unused capacity.",
            "Compare mobility policies with investment, innovation and measures that address market failure.",
            "Judge effectiveness by timescale, fiscal cost and the source of the resource misallocation.",
        ),
        "targeted retraining and relocation support",
    ),
    "4.1.2": WrittenTaskProfile(
        ("bounded rationality", "consumer information", "demand"),
        "A verified comparison tool has reduced search costs, while many buyers still use a familiar brand as a rule of thumb.",
        "lower search costs reduce information failure and can change consumer demand",
        _diagram(
            visual_kind="market_shift",
            curve="D",
            direction="right",
            cause="an improvement in consumer information",
            effect="a rightward shift of demand, raising equilibrium price and quantity",
            y_axis="Price",
            x_axis="Quantity",
        ),
        "Explain how bounded rationality and the use of rules of thumb can cause consumers to choose a product that does not maximise their utility.",
        (
            "Define bounded rationality and distinguish it from fully informed utility maximisation.",
            "Explain how information and search costs encourage a simplifying rule or default choice.",
            "Develop the consequence for consumer welfare and the allocation of resources.",
        ),
        "Evaluate the view that better consumer information is more effective than regulation at improving economic decision making.",
        (
            "Analyse how clearer information can reduce search costs and asymmetric information.",
            "Compare information remedies with defaults, regulation and direct restrictions.",
            "Judge by behavioural bias, enforcement costs and whether consumers act on the information.",
        ),
        "a verified comparison service with simplified disclosures",
    ),
    "4.1.3": WrittenTaskProfile(
        ("demand and supply", "price elasticity", "equilibrium"),
        "Consumer incomes have risen and survey evidence indicates stronger demand, while productive capacity is unchanged in the short run.",
        "stronger demand changes equilibrium price and quantity, with the size depending on supply elasticity",
        _diagram(
            visual_kind="market_shift",
            curve="D",
            direction="right",
            cause="an increase in consumer demand",
            effect="a rise in equilibrium price and equilibrium quantity",
            y_axis="Price",
            x_axis="Quantity",
        ),
        "Explain how price elasticity of demand affects the change in a firm's total revenue following an increase in price.",
        (
            "Define price elasticity of demand and total revenue.",
            "For inelastic demand, explain why the proportionate fall in quantity is smaller than the price rise.",
            "Contrast the revenue effect when demand is elastic and identify the ceteris paribus assumption.",
        ),
        "Evaluate the view that increasing competition is the best way to improve consumer welfare in a market.",
        (
            "Analyse effects on price, output, choice and productive or dynamic efficiency.",
            "Consider scale economies, innovation, contestability and the conduct of firms rather than firm numbers alone.",
            "Reach a conditional judgement using market structure and entry barriers.",
        ),
        "measures that reduce barriers to entry",
    ),
    "4.1.4": WrittenTaskProfile(
        ("productivity", "average cost", "profit"),
        "A new production process raises output per worker and lowers unit costs after an initial installation expense.",
        "higher productivity lowers average cost and can raise profit at a given price",
        _diagram(
            visual_kind="market_shift",
            curve="S",
            direction="right",
            cause="an increase in labour productivity",
            effect="a rightward shift of supply, lowering equilibrium price and raising quantity",
            y_axis="Price",
            x_axis="Quantity",
        ),
        "Explain how increasing labour productivity can affect a firm's average costs and profit.",
        (
            "Define labour productivity, average cost and profit.",
            "Explain how more output per worker can reduce labour cost per unit and average variable cost.",
            "Link the cost change to the profit margin while recognising the initial fixed investment cost.",
        ),
        "Evaluate the view that investment in new technology will always increase a firm's profit.",
        (
            "Analyse productivity, unit-cost and revenue effects of the investment.",
            "Consider finance cost, implementation risk, demand, competitor response and obsolescence.",
            "Judge by the size and timing of discounted benefits relative to costs.",
        ),
        "a time-limited investment allowance for productivity-enhancing technology",
    ),
    "4.1.5": WrittenTaskProfile(
        ("barriers to entry", "contestability", "market power"),
        "Entry costs have fallen after a common distribution platform opened to new firms, and several entrants plan to expand capacity.",
        "lower barriers to entry increase contestability and constrain incumbent pricing",
        _diagram(
            visual_kind="market_shift",
            curve="S",
            direction="right",
            cause="entry by new firms",
            effect="a rightward shift of market supply, lowering equilibrium price and raising quantity",
            y_axis="Price",
            x_axis="Quantity",
        ),
        "Explain how low sunk costs can make a concentrated market contestable and influence the behaviour of incumbent firms.",
        (
            "Define sunk cost and contestability.",
            "Explain how low entry and exit costs make hit-and-run entry more credible.",
            "Link the threat of entry to price, cost efficiency and abnormal profit.",
        ),
        "Evaluate the view that removing barriers to entry is sufficient to protect consumers from monopoly power.",
        (
            "Analyse how entry pressure affects price, output, efficiency and innovation.",
            "Consider network effects, scale economies, strategic conduct and information advantages.",
            "Compare entry policy with regulation or competition enforcement and reach a conditional judgement.",
        ),
        "open-access rules that reduce entry and switching costs",
    ),
    "4.1.6": WrittenTaskProfile(
        ("demand for labour", "marginal revenue product", "wage"),
        "Demand for the final service has risen and each trained worker can now produce more output per hour.",
        "higher marginal revenue product raises firms' demand for labour",
        _diagram(
            visual_kind="labour_market_shift",
            curve="D",
            direction="right",
            cause="an increase in labour productivity",
            effect="a rightward shift of labour demand, raising employment and the wage rate",
            y_axis="Wage rate",
            x_axis="Employment",
            demand_label="DL",
            supply_label="SL",
        ),
        "Explain how the marginal revenue product of labour helps to determine a firm's demand for labour.",
        (
            "Define marginal revenue product as marginal physical product multiplied by marginal revenue.",
            "Explain why a profit-maximising firm compares marginal revenue product with the marginal cost of labour.",
            "Analyse how product demand, productivity or product price shifts labour demand.",
        ),
        "Evaluate the view that a statutory minimum wage will improve outcomes for all workers in a labour market.",
        (
            "Analyse income and employment effects under competitive and monopsonistic conditions.",
            "Consider the wage level, labour-demand elasticity, compliance and non-wage responses.",
            "Reach a judgement distinguishing affected workers, unemployed workers and firms.",
        ),
        "a carefully monitored statutory minimum wage",
    ),
    "4.1.7": WrittenTaskProfile(
        ("income inequality", "redistribution", "Lorenz curve"),
        "A progressive tax and income-tested transfer have raised the disposable-income share received by the lowest-income households.",
        "progressive taxation and transfers can narrow disposable-income inequality",
        _diagram(
            visual_kind="lorenz_shift",
            curve="Lorenz",
            direction="towards_equality",
            cause="a progressive tax and transfer reform",
            effect="a Lorenz curve closer to the line of equality and a lower Gini coefficient",
            y_axis="Cumulative share of income",
            x_axis="Cumulative share of households",
        ),
        "Explain how a progressive tax and transfer system can reduce disposable-income inequality.",
        (
            "Define progressive taxation and disposable-income inequality.",
            "Explain how the tax burden and transfer receipts change income shares across households.",
            "Use a Lorenz curve or Gini coefficient to show the resulting distributional change.",
        ),
        "Evaluate the view that more progressive taxation is the best policy for reducing income inequality.",
        (
            "Analyse the direct effect on post-tax income and government revenue.",
            "Compare taxation with transfers, education, labour-market policy and wealth measures.",
            "Judge by behavioural responses, avoidance, work incentives, targeting and the chosen measure of inequality.",
        ),
        "a more progressive tax-and-transfer package",
    ),
    "4.1.8": WrittenTaskProfile(
        ("negative externality", "social cost", "market failure"),
        "Production creates an estimated external cost that is not included in firms' private costs or the market price.",
        "an unpriced external cost causes market output to exceed the socially efficient quantity",
        _diagram(
            visual_kind="externality",
            curve="MSC",
            direction="above_mpc",
            cause="an increase in the external cost of production",
            effect="a larger gap between marginal social and private cost and a lower socially efficient output",
            y_axis="Costs and benefits",
            x_axis="Output",
            demand_label="MSB",
            supply_label="MPC",
        ),
        "Explain why a negative externality in production can cause a market to allocate too many resources to a product.",
        (
            "Define external cost, marginal private cost and marginal social cost.",
            "Show why the market equilibrium ignores third-party costs and produces beyond the social optimum.",
            "Explain the resulting welfare loss using a correctly labelled externality diagram.",
        ),
        "Evaluate the view that an indirect tax is the best way to correct a negative externality in production.",
        (
            "Analyse how a tax can internalise the external cost and change price and output.",
            "Compare taxation with regulation, permits, information and technology support.",
            "Judge by measurement, elasticity, enforcement, distribution and government-failure risks.",
        ),
        "an indirect tax calibrated to the estimated external cost",
    ),
    "4.2.1": WrittenTaskProfile(
        ("real GDP per head", "living standards", "national income data"),
        "Real GDP has risen faster than population, but unpaid activity and the distribution of income are not recorded in the headline figure.",
        "real GDP per head can indicate material living standards but omits distribution and non-market activity",
        _diagram(
            visual_kind="aggregate_shift",
            curve="AD",
            direction="right",
            cause="an increase in real aggregate demand",
            effect="a rise in real output and the price level in the short run",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain the main limitations of using real GDP per head to compare living standards over time.",
        (
            "Explain why real GDP per head adjusts national output for inflation and population.",
            "Analyse omissions such as income distribution, unpaid activity, leisure, quality and environmental damage.",
            "Explain why measurement methods and purchasing power affect comparisons.",
        ),
        "Evaluate the view that growth in real GDP per head is the best indicator of improved economic performance.",
        (
            "Analyse what the measure captures about average material output or income.",
            "Compare it with employment, inflation, distribution, sustainability and broader wellbeing evidence.",
            "Reach a judgement about the purpose, period and reliability of the data.",
        ),
        "publishing a broader dashboard alongside real GDP per head",
    ),
    "4.2.2": WrittenTaskProfile(
        ("aggregate demand", "multiplier", "real output"),
        "Autonomous investment has increased, and firms report spare capacity and a stable short-run aggregate supply schedule.",
        "the multiplier makes the final increase in aggregate demand larger than the initial injection",
        _diagram(
            visual_kind="aggregate_shift",
            curve="AD",
            direction="right",
            cause="an increase in autonomous investment",
            effect="a rightward shift of aggregate demand, raising real output and the price level",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain how an increase in autonomous investment can create a multiplied increase in national income.",
        (
            "Identify investment as an injection into the circular flow.",
            "Explain successive rounds of income and consumption using the marginal propensity to consume.",
            "Analyse why leakages and spare capacity determine the multiplier's size and output effect.",
        ),
        "Evaluate the view that increasing government investment is the most effective way to raise real output.",
        (
            "Analyse direct demand, multiplier and possible productive-capacity effects.",
            "Consider spare capacity, crowding out, implementation lags, import leakages and project quality.",
            "Compare fiscal investment with monetary or supply-side alternatives and judge by economic conditions.",
        ),
        "a temporary programme of high-return public investment",
    ),
    "4.2.3": WrittenTaskProfile(
        ("economic cycle", "unemployment", "aggregate demand"),
        "Business confidence and household consumption have fallen, while firms report spare capacity and rising cyclical unemployment.",
        "weaker aggregate demand reduces real output and raises cyclical unemployment",
        _diagram(
            visual_kind="aggregate_shift",
            curve="AD",
            direction="left",
            cause="a fall in business and consumer confidence",
            effect="a leftward shift of aggregate demand, reducing real output and the price level",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain how a fall in aggregate demand can create a negative output gap and cyclical unemployment.",
        (
            "Define a negative output gap and cyclical unemployment.",
            "Trace lower spending through firms' output decisions to derived demand for labour.",
            "Use an AD-AS diagram to distinguish the output and price-level effects.",
        ),
        "Evaluate the view that maintaining low inflation should take priority over reducing unemployment.",
        (
            "Analyse costs of inflation and unemployment and possible short-run trade-offs.",
            "Consider the output gap, expectations, supply shocks and distributional effects.",
            "Reach a conditional judgement about the economy's position and policy credibility.",
        ),
        "a temporary demand-support package targeted at high-unemployment regions",
    ),
    "4.2.4": WrittenTaskProfile(
        ("interest rate", "credit", "aggregate demand"),
        "The central bank has raised its policy interest rate and a high share of household spending and business investment is credit-financed.",
        "higher interest rates weaken credit-financed consumption and investment",
        _diagram(
            visual_kind="aggregate_shift",
            curve="AD",
            direction="left",
            cause="an increase in the policy interest rate",
            effect="a leftward shift of aggregate demand, reducing real output and the price level",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain how an increase in the policy interest rate can reduce demand-pull inflation.",
        (
            "Explain how market borrowing and saving rates respond to the policy rate.",
            "Trace effects through consumption, investment, asset prices or the exchange rate to aggregate demand.",
            "Link weaker aggregate demand to the output gap and inflationary pressure.",
        ),
        "Evaluate the view that higher interest rates are the best response to above-target inflation.",
        (
            "Analyse the monetary transmission mechanism and its time lags.",
            "Distinguish demand-pull from cost-push inflation and consider indebted groups and investment.",
            "Compare monetary tightening with fiscal or supply-side measures and reach a conditional judgement.",
        ),
        "a measured increase in the policy interest rate",
    ),
    "4.2.5": WrittenTaskProfile(
        ("supply-side policy", "productive capacity", "long-run aggregate supply"),
        "Government-funded training and transport investment are expected to raise labour productivity and reduce production bottlenecks.",
        "effective supply-side investment can raise productivity and productive capacity",
        _diagram(
            visual_kind="aggregate_shift",
            curve="LRAS",
            direction="right",
            cause="an effective supply-side investment programme",
            effect="a rightward shift of long-run aggregate supply, raising capacity and reducing price pressure",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain how interventionist supply-side policies can increase an economy's productive capacity.",
        (
            "Identify policies that improve human capital, infrastructure or technology.",
            "Trace their effect through productivity, costs, labour-market participation or investment.",
            "Use LRAS or a production possibility frontier to show higher potential output.",
        ),
        "Evaluate the view that interventionist supply-side policy is more effective than free-market reform at improving economic performance.",
        (
            "Analyse productivity, capacity, employment and inflation effects of both approaches.",
            "Consider fiscal cost, government failure, incentives, distribution and implementation lags.",
            "Reach a judgement based on the identified market failure and institutional capacity.",
        ),
        "targeted training and infrastructure investment",
    ),
    "4.2.6": WrittenTaskProfile(
        ("exchange rate", "net exports", "current account"),
        "The currency has depreciated, and export and import demand become more price responsive after existing contracts expire.",
        "a depreciation can raise net exports when demand elasticities and supply capacity permit quantities to adjust",
        _diagram(
            visual_kind="aggregate_shift",
            curve="AD",
            direction="right",
            cause="a depreciation that increases net exports",
            effect="a rightward shift of aggregate demand, raising real output and the price level",
            y_axis="Price level",
            x_axis="Real output",
        ),
        "Explain the conditions under which a currency depreciation can improve the current-account balance.",
        (
            "Explain how depreciation changes export prices in foreign currency and import prices in domestic currency.",
            "Use the price elasticities of export and import demand to analyse expenditure switching.",
            "Distinguish short-run contract effects from longer-run quantity adjustment and supply capacity.",
        ),
        "Evaluate the view that currency depreciation is the best way to reduce a persistent current-account deficit.",
        (
            "Analyse relative-price, quantity, inflation and output effects.",
            "Consider elasticities, import dependence, retaliation, confidence and the causes of the deficit.",
            "Compare depreciation with productivity, demand-management or trade policies and reach a conditional judgement.",
        ),
        "a package that improves export productivity rather than targeting the exchange rate alone",
    ),
}


def profile_for(topic_id: str) -> WrittenTaskProfile:
    try:
        return PROFILES[topic_id]
    except KeyError as error:
        raise ValueError(f"no AQA Economics written-task profile for {topic_id}") from error
