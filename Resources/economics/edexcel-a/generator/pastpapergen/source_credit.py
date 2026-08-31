"""P3 credit built from the selected source's roles, not legacy example text.

Numeric roles are extracted once from the owned candidate prose into its typed
source. Each branch below supplies the actual reference and uses that role;
non-numeric mechanisms are tied to observations in that same source template.
"""

import re


def source_bound_points(question, source):
    pair = question.topic_id, question.marks
    if pair not in {
        ("1.2.3", 5),
        ("1.3", 5),
        ("3.1", 8),
        ("3.5", 8),
        ("1.3", 12),
        ("1.4", 12),
        ("2.3", 25),
        ("4.5", 25),
    }:
        return None
    reference = question.source_reference
    figure = re.search(r"Figure \d+", reference)
    extract = re.search(r"Extract [A-F]", reference)
    if extract is None:
        raise ValueError("Source-bound P3 credit needs its designated extract")
    extract = extract.group()
    figure = figure.group() if figure else extract
    market = (
        question.source_title.removeprefix("Fictional regional economy: ")
        .removesuffix(" and related markets")
        .lower()
    )

    def value(role, unit="%"):
        cell = source.givens.get(role)
        if cell is None or cell.number is None or cell.unit != unit:
            raise ValueError(f"Selected P3 source lacks credit input: {role}")
        return cell.number

    if pair == ("1.2.3", 5):
        price, quantity = value("Price change"), value("Quantity supplied change")
        return [
            "Price elasticity of supply measures quantity-supplied responsiveness to price.",
            f"Use {figure}'s price increase of {price}% and quantity-supplied increase of {quantity}%.",
            f"Use {extract}'s limited capacity, fixed contracts or delayed access to inputs.",
            "The chosen constraint prevents output expanding quickly after the price rise. The smaller proportional supply response indicates price-inelastic supply; a qualitative comparison is sufficient.",
        ]
    if pair == ("1.3", 5):
        actual = value("Market output (million doses)", "units")
        optimum = value("Socially efficient output (million doses)", "units")
        cost = value("External marginal cost per dose", "GBP")
        return [
            "An unpriced production externality separates private and social marginal cost.",
            f"Use {figure}: market output is {actual} million doses against the socially efficient {optimum} million doses where MSB = MSC.",
            f"Use {extract}: untreated chemical waste creates an unpaid external marginal clean-up and health cost of £{cost} per dose.",
            f"Excluding the £{cost} third-party cost makes MPC lower than MSC, so private price understates full social cost and encourages excess output.",
            f"The {actual - optimum} million doses above the {optimum} million optimum are overproduced: MSC exceeds MSB on those units, causing deadweight welfare loss.",
        ]
    if pair == ("3.1", 8):
        capital, discount = (
            value("Capital spending change"),
            value("Unit input cost reduction"),
        )
        return [
            "A technical economy of scale lowers long-run average cost as specialist capital increases productivity.",
            f"Use {figure}: capital spending increased by {capital}% in {market} in the stated period.",
            "Specialist machinery permits greater output per worker and spreads fixed expenditure over more units, reducing LRAC when the extra capacity is used.",
            "Unrenewed customer contracts make capacity utilisation uncertain: idle machinery may prevent the expected fall in cost per unit.",
            "A purchasing economy of scale arises when larger combined orders secure a lower unit input price.",
            f"Use {extract}: long-term supply contracts reduced unit input costs by {discount}%; an operator combined purchasing across three sites.",
            "The input discount lowers variable cost per unit as output expands, reducing LRAC.",
            "The additional management layer and slower approvals can create coordination diseconomies that offset the purchasing saving.",
        ]
    if pair == ("3.5", 8):
        vacancy, duration, pay, turnover = (
            value("Vacancy growth"),
            value("Median vacancy duration (weeks)", "1"),
            value("Pay growth"),
            value("Annual staff turnover"),
        )
        tourism = "chef and hospitality-supervisor" in source.context
        roles = (
            "experienced chef and hospitality-supervisor roles"
            if tourism
            else "specialist healthcare roles"
        )
        constraint = (
            "multi-year chef training, seasonal contracts and expensive resort housing"
            if tourism
            else "multi-year specialist training and professional registration"
        )
        capacity = "service capacity" if tourism else "treatment capacity"
        entry = (
            "overseas experience, apprenticeships or staff accommodation"
            if tourism
            else "overseas qualifications or funded training places"
        )
        return [
            f"Occupational immobility and inelastic short-run labour supply arise because entry to {roles} takes time.",
            f"Use {extract}: vacancies rose by {vacancy}%, the median vacancy lasted {duration} weeks, and entry is constrained by {constraint}.",
            f"A slow labour-supply response leaves posts unfilled, constraining {capacity} and increasing recruitment or overtime costs.",
            f"The proposed recognition of {entry} can expand effective labour supply over time, but implementation and retention affect the result.",
            "Non-wage working conditions affect labour supply and staff retention as well as pay.",
            f"Use {extract}: overtime increased and annual staff turnover reached {turnover}% despite a {pay}% wage rise.",
            "Workload and unsocial hours can reduce retention, shifting effective labour supply left and increasing wage pressure and employers' costs.",
            "More predictable or flexible schedules can improve retention; smaller employers' resources and the time needed to train replacements limit an immediate improvement.",
        ]
    if pair in {("1.3", 12), ("1.4", 12)}:
        price = value("Later-period price change")
        applications = [
            f"Use {extract}: prices changed by {price}% in the later period in {market}, with the product taking a larger budget share for lower-income households.",
            f"Use {extract}: neighbours pay unreimbursed cleaning and respiratory-treatment costs; backup supply also prevents outages at premises that pay no fee to the network operator.",
        ]
        if pair[0] == "1.3":
            return [
                "A negative externality is an uncompensated third-party cost, making MSC exceed MPC.",
                "Allocative efficiency occurs where MSB = MSC and total economic welfare is maximised.",
                *applications,
                "Unpriced pollution gives MSC > MPC, so private output can exceed the socially efficient quantity.",
                "Output beyond the social optimum creates deadweight welfare loss; an accurate external-cost diagram can support the reasoning.",
                "Unpaid network resilience is a positive spillover where MSB > MPB: the operator cannot capture every wider benefit, without the service necessarily being a pure public good.",
                "Private network investment can therefore be below the socially efficient level, losing net social benefits from additional investment.",
                "Only two monitoring stations provide pollution measurements; incomplete evidence makes the size and value of external damage uncertain.",
                "Demand and supply responsiveness affect the quantity adjustment and size of welfare loss; a large price change alone does not establish that loss.",
                "Contracts, reputation, property rights or profitable innovation may internalise some effects; explain whether that qualification fits the unpaid costs and benefits here.",
                f"Reach a supported welfare judgement using {extract}; its {price}% price change and distributional effect may supplement, but must not replace, allocative-efficiency analysis. Accept an equivalent source-applied welfare route.",
            ]
        return [
            "An indirect tax raises private marginal cost and a subsidy lowers it, altering production and consumption incentives.",
            "Government failure occurs when intervention produces a net welfare loss through information problems, unintended incentives or administrative cost.",
            *applications,
            "A tax calibrated to the unpaid marginal pollution cost can reduce output towards the socially efficient level.",
            "Lower output or cleaner methods can reduce third-party damage; revenue could finance monitoring or compensation.",
            "A targeted grant or subsidy for shared backup infrastructure can encourage investment with positive external benefits.",
            "Greater network resilience benefits both paying customers and neighbouring premises, where private returns understate social benefits.",
            "Compare tax and subsidy incidence: inelastic demand can leave consumers bearing much of a tax, while the source's lower-income households face a larger budget burden.",
            "The same annual inspection fee for small and large firms may impose a larger proportional burden on entrants, affecting competition and innovation.",
            "Limited monitoring data makes correct targeting difficult; compare the residents' immediate emissions-limit proposal with the industry's preferred equipment grants.",
            f"Use {extract} to judge which instrument best addresses the particular unpaid cost or benefit, considering measurement, distribution and implementation time. Accept other coherent source-applied policy comparisons.",
        ]
    if pair == ("2.3", 25):
        output, investment = (
            value("Sector output change"),
            value("Planned investment change"),
        )
        return [
            "Productive capacity is the maximum sustainable output attainable with available capital, labour and technology.",
            "Capital investment and specialisation can lower firms' long-run average cost by raising productivity.",
            "LRAS represents the economy's productive potential; SRAS also responds to current input costs.",
            "Investment enters aggregate demand and adds to the capital stock; these are distinct short-run and long-run channels.",
            f"Use {extract}: output in {market} changed by {output}%.",
            f"Use {extract}'s {investment}% planned-investment increase and orders for replacement machinery and additional production lines.",
            f"Apply {extract}'s imported equipment and eighteen-month delivery time to the timing and domestic share of investment spending.",
            f"Apply {extract}'s unused shifts, vacant maintenance posts, limited college places or requirement for signed customer contracts.",
            f"New machinery can raise output per worker in {market}, lowering unit costs when it operates effectively.",
            "Lower LRAC can increase profitable output and reduce product or service prices, depending on competition and demand.",
            "Additional production lines expand firms' capacity, but maintenance staff and trained operators must complement the equipment.",
            "Customers may gain availability or lower prices, while rivals and workers face changes in market share, skills and employment.",
            f"The {investment}% investment increase raises AD initially; payments to domestic suppliers and workers may generate a multiplier increase in GDP and employment.",
            "New capital and skills can shift LRAS right, expanding potential output beyond the initial spending effect.",
            "The source's higher component invoices and wages can raise current unit costs and shift SRAS left, even while planned capital raises future potential.",
            "Distinguish this short-run cost pressure from longer-run productivity gains and their consequences for non-inflationary growth.",
            "Unused shifts and unsigned contracts indicate uncertain utilisation: weak demand can prevent lower LRAC despite added capacity.",
            "Limited maintenance staff and college places may delay effective use of capital; explain how complementary training changes the outcome.",
            "Market power can allow firms to retain cost savings rather than pass them to customers; compare stakeholder outcomes rather than assume everyone gains.",
            "Delivery and installation may raise costs before benefits arrive; weigh disruption against later productivity and availability.",
            "With spare capacity the AD effect can raise output, whereas near full capacity more of the initial stimulus may raise prices.",
            "Imported machinery creates a leakage from domestic spending and may initially weaken net exports, limiting the domestic multiplier.",
            "Finance and the requirement for customer contracts affect whether planned investment is completed; borrowing costs can displace other private projects.",
            "Evaluate the eighteen-month delivery lag and skill constraints against the scale of investment: completion alone does not guarantee productivity gains.",
            f"Reach a supported conclusion on both microeconomic effects in {market} and UK macroeconomic effects using {extract}; weigh a decisive evidenced condition against an alternative and state the time horizon. No particular condition is prescribed.",
        ]
    price = value("International price change")
    return [
        "State intervention changes market incentives or resource allocation through spending, taxation, regulation or public provision.",
        "Taxes, subsidies and standards can address externalities or market power, but instruments have different incidence and information requirements.",
        "Discretionary fiscal policy changes government spending or taxes and therefore aggregate demand.",
        "Public expenditure has an opportunity cost; government failure can arise from poor information, targeting or implementation.",
        f"Use {extract}'s {price}% international-price movement in {market} when considering costs and affordability.",
        f"Use {extract}'s infrastructure grant financed partly by a levy on businesses outside the sector.",
        f"Apply {extract}'s three-year construction period and imported equipment to domestic spending and timing.",
        f"Apply {extract}'s delayed private projects, previous cost overrun, revised estimates or requested publication of household access.",
        "The grant can reduce the recipient's financing burden and enable infrastructure that increases capacity or lowers unit cost.",
        "Improved capacity can raise availability and consumer surplus, but gains depend on who receives access and whether savings reach customers.",
        "A levy raises costs for non-recipient businesses and may reduce their output or investment, offsetting some benefits within the supported sector.",
        "Compare a conditional grant or service standard with unconditional support; conditions may improve access or quality but create compliance costs.",
        "Public project spending raises AD directly and can support employment and further domestic spending through the multiplier.",
        "Infrastructure can increase productive potential over time, shifting LRAS right if complementary skills and demand allow effective use.",
        "Higher productivity can expand sustainable output and reduce economy-wide cost pressure; distinguish that effect from the initial construction stimulus.",
        "Imported equipment initially increases import spending, while more productive domestic firms may later compete more effectively; the net trade effect is conditional.",
        "Evaluate targeting and responsiveness: a grant has little additional effect if firms would invest anyway; conditions may change firms' behaviour.",
        "A previous cost overrun and revised estimates indicate uncertainty over value for money; assess monitoring and incentives rather than assuming accurate forecasts.",
        "Publication of household access matters because beneficiaries and levy payers differ; weigh distribution and service access explicitly.",
        "Compare proportionate policy alternatives within the requested intervention question, explaining their information and compliance costs.",
        "The levy has an opportunity cost for other businesses; public funds also displace alternative projects or services.",
        "Two firms postponed private projects pending the grant decision: explain whether support ultimately crowds investment in or delays/displaces it.",
        "Imported equipment and three-year construction weaken or delay the domestic multiplier; spare capacity affects inflation versus output gains.",
        "Weigh short-run costs and demand effects against longer-run capacity, productivity and resilience, with an explicit implementation horizon.",
        f"Reach a supported conclusion using {extract} to justify a policy mix for {market}, integrating market-level and UK macroeconomic effects and selecting an evidenced decisive condition and time horizon. No named instrument or condition is compulsory.",
    ]
