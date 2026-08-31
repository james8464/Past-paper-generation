"""Concrete authored scenarios for formerly topic-note-only extended tasks.

Each record is a task, two candidate facts, two causal routes and two limits.
The facts are illustrative assumptions, not unattributed national statistics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    event: str
    outcome: str
    concept: str
    facts: tuple[str, str]
    routes: tuple[str, str]
    limits: tuple[str, str]


SCENARIOS = {
    "1.2.2": Scenario(
        "a fall in real household incomes",
        "demand for own-brand food",
        "Real income measures purchasing power; income elasticity measures the responsiveness of demand to income.",
        (
            "Households have less purchasing power after essential bills rise, while own-brand food remains cheaper than premium brands.",
            "Shoppers regard the two ranges as substitutes, but some value the premium brand's quality.",
        ),
        (
            "Households switch towards the cheaper own-brand substitute to preserve food consumption; demand for the own-brand range increases at each price.",
            "Brand loyalty and perceived quality reduce substitution for some shoppers, so the demand increase differs between groups.",
        ),
        (
            "If own-brand food is an inferior good, lower income raises demand; do not assume all inexpensive food is inferior without applying the scenario.",
            "A large relative-price reduction by premium brands or an own-brand capacity constraint could limit the quantity sold.",
        ),
    ),
    "1.2.3": Scenario(
        "capacity and input constraints",
        "firms' short-run supply response",
        "Price elasticity of supply measures the proportional quantity-supplied response to a price change.",
        (
            "Factories are operating near capacity and new machinery takes a year to install.",
            "Specialist inputs are supplied under fixed short-run contracts; overtime is possible but costly.",
        ),
        (
            "Limited spare capacity prevents a large immediate output increase after prices rise, making short-run supply relatively price inelastic.",
            "Fixed input deliveries restrict production even when extra labour is available; renegotiating contracts and installing capacity makes supply more elastic over time.",
        ),
        (
            "Firms holding inventories may expand sales more readily than firms producing only to order.",
            "Supply becomes more responsive only if higher prices are expected to persist long enough to justify investment.",
        ),
    ),
    "1.2.4": Scenario(
        "a reduction in market supply",
        "consumers and producers",
        "Market equilibrium occurs where quantity demanded equals quantity supplied; consumer and producer surplus measure gains from trade.",
        (
            "Poor weather reduces the vegetable harvest, while consumer demand initially remains unchanged.",
            "Protected growers maintain more output than exposed growers, and retailers can import substitutes after a delay.",
        ),
        (
            "Supply shifts left, raising equilibrium price and reducing quantity; consumers lose surplus and purchasing power.",
            "Producers able to maintain output may gain from the higher price, while crop losses and higher unit costs can reduce other growers' profits.",
        ),
        (
            "Inelastic demand creates a larger price response and a smaller quantity response.",
            "Imports and later harvests expand supply over time, limiting the duration of the price rise.",
        ),
    ),
    "1.3": Scenario(
        "unpriced external costs of production",
        "economic welfare",
        "A negative production externality is a cost imposed on third parties that is excluded from the producer's private cost.",
        (
            "Factories emit air pollution that increases nearby households' cleaning and health costs without compensation.",
            "Cleaner equipment is available, but producers bear its installation cost while neighbours receive much of the benefit.",
        ),
        (
            "Marginal social cost exceeds marginal private cost, so the market produces beyond the socially efficient quantity and creates a welfare loss.",
            "Producers have too little private incentive to install cleaner equipment because they do not capture the avoided third-party costs.",
        ),
        (
            "The scale of welfare loss depends on the external marginal cost and responsiveness of production.",
            "A tax or standard can reduce damage, but imperfect measurement, enforcement cost and cleaner-technology availability constrain the gain.",
        ),
    ),
    "1.4": Scenario(
        "an indirect tax on a polluting product",
        "firms, consumers and third parties",
        "An indirect tax raises the private marginal cost of supplying a product; internalisation aligns private incentives with external costs.",
        (
            "Production imposes pollution costs on nearby households, and government proposes a per-unit tax.",
            "Consumers have some cleaner substitutes, but smaller producers find clean equipment expensive.",
        ),
        (
            "The tax shifts supply up, increasing price and reducing output, which can reduce pollution and the associated welfare loss.",
            "Producers face an incentive to adopt cleaner methods, while tax receipts could finance monitoring or support affected households.",
        ),
        (
            "Inelastic demand limits the output reduction and shifts more of the burden towards consumers.",
            "Poor calibration or costly enforcement can create government failure; compare a targeted standard or clean-technology subsidy.",
        ),
    ),
    "3.1": Scenario(
        "business expansion",
        "firms' average costs and consumers",
        "Economies of scale occur when increasing the scale of production lowers long-run average cost.",
        (
            "An expanding manufacturer negotiates bulk-input discounts and installs specialist production lines.",
            "Managers report slower communication across sites and uncertainty over demand for the extra capacity.",
        ),
        (
            "Purchasing discounts and greater specialisation reduce unit input and labour costs, lowering long-run average cost.",
            "Communication and coordination problems can create diseconomies, while unused capacity spreads fixed expenditure over too few sales.",
        ),
        (
            "Cost savings depend on demand and capacity utilisation, not expansion alone.",
            "Consumers benefit more when competition makes firms pass cost savings into prices rather than retain them as profit.",
        ),
    ),
    "3.2": Scenario(
        "a shift towards sales-growth objectives",
        "firms and their stakeholders",
        "Sales or revenue maximisation differs from profit maximisation, which occurs where marginal revenue equals marginal cost.",
        (
            "Managers receive bonuses linked to sales growth and propose lower prices plus new distribution capacity.",
            "Shareholders require sufficient profit to finance investment, while employees seek predictable hours and higher pay.",
        ),
        (
            "Lower prices and new capacity can expand sales and market share but reduce short-run margins and retained profit.",
            "Scale, reputation and customer loyalty may later lower costs or strengthen demand, making growth complement long-run profit.",
        ),
        (
            "The revenue effect of lower prices depends on demand elasticity and rivals' responses.",
            "Finance constraints and owner monitoring limit managers' discretion; stakeholder gains may conflict in the short run.",
        ),
    ),
    "3.3": Scenario(
        "higher production costs",
        "firms' profits and output",
        "Profit is total revenue minus total cost; fixed and variable costs respond differently to output.",
        (
            "A bakery's flour cost rises from £20 to £24 per bag while its shop lease remains £2,400 a month.",
            "Customers can switch to competing bakeries, and the business has some spare capacity.",
        ),
        (
            "Higher variable costs increase marginal and average cost, reducing profit at the original price and output.",
            "Passing costs into prices can preserve margin per unit but reduce sales; the total-profit effect depends on demand responsiveness and output.",
        ),
        (
            "In the short run a loss-making firm may continue if price covers average variable cost and contributes to fixed cost.",
            "Efficiency investment or cheaper inputs may offset the shock over time, but financing and substitution options differ between firms.",
        ),
    ),
    "3.4": Scenario(
        "high barriers to entry",
        "competition and consumers",
        "Contestability depends on the threat of entry and exit, not only the number of incumbent firms.",
        (
            "Entrants must incur unrecoverable development costs and obtain access to a distribution network.",
            "Customers face switching costs, although online distribution provides a possible alternative entry route.",
        ),
        (
            "Sunk entry costs and restricted distribution deter entry, weakening the competitive threat and allowing incumbents greater pricing discretion.",
            "Switching costs protect established customers, but cheaper online entry can reduce barriers and pressure firms to improve price or quality.",
        ),
        (
            "Existing rivalry and substitutes can constrain market power even when entry is difficult.",
            "Large firms may also fund innovation or exploit scale economies; evaluate whether these benefits reach consumers.",
        ),
    ),
    "3.5": Scenario(
        "persistent labour shortages",
        "wages, employment and firms' costs",
        "Labour demand is derived from demand for output; equilibrium wages depend on labour demand and supply.",
        (
            "Employers have unfilled skilled vacancies and offer higher pay; specialist training takes several years.",
            "Workers value flexible hours and transport access, while smaller firms have limited room to raise pay.",
        ),
        (
            "Inelastic short-run labour supply means stronger competition for skilled workers raises wages substantially but fills relatively few vacancies.",
            "Training, flexible work and improved access can expand effective labour supply, easing shortages and supporting output over time.",
        ),
        (
            "Higher labour costs can reduce profit or raise consumer prices, depending on productivity and product-demand elasticity.",
            "Training delays, staff retention and recruitment from other sectors determine whether shortages are solved or merely displaced.",
        ),
    ),
    "3.6": Scenario(
        "a binding maximum price",
        "firms and consumers",
        "A maximum price is a legal ceiling; it is binding only when set below the market-clearing price.",
        (
            "Government proposes a price ceiling below the existing equilibrium price for an essential service.",
            "Suppliers have rising maintenance costs and consumers cannot readily switch to another service.",
        ),
        (
            "The lower legal price expands quantity demanded and contracts supply, creating excess demand and possible rationing.",
            "Some successful buyers gain affordability, but lower returns may reduce maintenance, quality and investment, harming other consumers.",
        ),
        (
            "The shortage depends on demand and supply elasticity and the size of the price reduction.",
            "A targeted subsidy or public supply may improve access but requires funding and creates an opportunity cost.",
        ),
    ),
    "2.1": Scenario(
        "a fall in aggregate demand",
        "inflation, output and employment",
        "Aggregate demand is total planned spending on domestic output; cyclical unemployment arises from deficient demand.",
        (
            "Households postpone purchases; a typical firm's monthly orders fall from 120 to 100 units while capacity is 160 units.",
            "Imported input costs remain high and some vacancies require skills held by few unemployed workers.",
        ),
        (
            "Lower spending reduces output and derived demand for labour, raising cyclical unemployment and reducing demand-pull inflation pressure.",
            "High imported costs may sustain cost-push inflation, while skills mismatch means demand recovery alone will not remove all unemployment.",
        ),
        (
            "The output-price split depends on spare capacity and wage-price flexibility.",
            "Policy that restores demand can support jobs but risks inflation if supply constraints remain.",
        ),
    ),
    "2.2": Scenario(
        "an increase in investment",
        "output and employment",
        "Investment is spending on capital goods and an injection into aggregate demand; induced consumption creates a multiplier process.",
        (
            "Firms plan new domestic production facilities while the economy has spare capacity.",
            "Some machinery is imported and households save part of any additional income.",
        ),
        (
            "Construction and equipment spending raise aggregate demand, income and employment; recipients' consumption creates further rounds of demand.",
            "New capital can raise productivity and productive capacity, reducing unit costs and supporting non-inflationary output growth over time.",
        ),
        (
            "Saving and import leakages reduce the domestic multiplier.",
            "Near full capacity, extra spending mainly raises prices; expected demand and finance determine whether planned investment occurs.",
        ),
    ),
    "2.3": Scenario(
        "investment in productive capacity",
        "output, prices and living standards",
        "Long-run aggregate supply represents sustainable productive potential; productivity is output per unit of input.",
        (
            "Firms invest in technology and workers receive training, but installation temporarily disrupts production.",
            "Imported equipment is costly and demand may be insufficient to use all new capacity.",
        ),
        (
            "Technology and skills raise productivity, lowering unit costs and shifting aggregate supply right, allowing higher output with less price pressure.",
            "Investment initially raises aggregate demand and employment, while capacity gains occur later and can support real wages and consumption.",
        ),
        (
            "Unused capacity and poorly matched training reduce the realised productivity gain.",
            "Import leakages, borrowing costs and installation delays can weaken short-run gains before long-run benefits arrive.",
        ),
    ),
    "2.4": Scenario(
        "an increase in government spending",
        "national income",
        "The multiplier relates the final change in income to an initial injection; saving, taxation and imports are leakages.",
        (
            "Government commissions local construction when firms have spare capacity and unemployment is high.",
            "Households spend part of extra earnings on domestic goods but also save, pay tax and import products.",
        ),
        (
            "The injection raises construction incomes, inducing consumption and further rounds of income and employment.",
            "Domestic sourcing and a high propensity to consume strengthen the multiplier, while leakage from each round limits the final income increase.",
        ),
        (
            "At full capacity, extra spending raises prices rather than real output.",
            "Tax or borrowing finance may offset private demand; compare the injection with the opportunity cost of other public uses.",
        ),
    ),
    "2.5": Scenario(
        "faster economic growth",
        "firms, households and living standards",
        "Economic growth is an increase in real output; potential growth increases the economy's productive capacity.",
        (
            "New technology raises output per worker and firms expand employment, but gains are concentrated in skilled occupations.",
            "Transport congestion and pollution rise as production expands; public services face greater demand.",
        ),
        (
            "Higher productivity and employment can raise real wages, consumption and tax receipts, supporting material living standards.",
            "Unequal access to skilled jobs and rising external costs mean average real GDP growth need not improve every household's welfare.",
        ),
        (
            "Distribution, population growth and the composition of output affect real income per person.",
            "Training and cleaner infrastructure can make growth more inclusive and sustainable but require resources and time.",
        ),
    ),
    "2.6": Scenario(
        "higher interest rates to reduce inflation",
        "firms and consumers",
        "Monetary policy influences borrowing costs and aggregate demand; demand-pull and cost-push inflation require different analysis.",
        (
            "The central bank raises interest rates while households have variable-rate loans and firms plan debt-financed investment.",
            "Some households are net savers, while imported energy costs contribute to inflation.",
        ),
        (
            "Higher debt-servicing costs reduce consumption and investment, weakening demand and price pressure but lowering firms' sales and employment.",
            "Savers gain interest income and the currency may appreciate, lowering import prices but weakening export competitiveness.",
        ),
        (
            "Imported cost-push inflation is less directly responsive to weaker domestic demand.",
            "Long lags and indebtedness differences affect the cost of restoring stability; credible policy can help anchor expectations.",
        ),
    ),
    "4.1": Scenario(
        "a reduction in trade barriers",
        "firms, consumers and the wider economy",
        "Comparative advantage permits gains from specialisation when opportunity costs differ; trade barriers restrict these gains.",
        (
            "Trading partners lower tariffs on manufactured products and components, while domestic producers face stronger foreign competition.",
            "Exporters can reach a larger market, but workers cannot immediately move between industries.",
        ),
        (
            "Cheaper imports and components improve choice and reduce costs; greater specialisation and market size can raise efficiency and consumer welfare.",
            "Export expansion can raise output, jobs and scale economies, while less competitive industries contract and experience structural unemployment.",
        ),
        (
            "Labour mobility and adjustment support determine the duration and distribution of losses.",
            "Exchange rates, non-tariff barriers and foreign demand determine whether potential export opportunities become actual sales.",
        ),
    ),
    "4.2": Scenario(
        "redistributive taxation and transfers",
        "income inequality and living standards",
        "Income inequality concerns the distribution of income; relative poverty differs from an inability to afford basic necessities.",
        (
            "Government proposes a more progressive income tax and targeted transfers to low-income households.",
            "Some eligible households do not claim benefits, and higher earners have opportunities to change hours or taxable income.",
        ),
        (
            "Transfers raise low-income disposable income and consumption, while progressive tax reduces post-tax income dispersion.",
            "Work incentives, avoidance and incomplete take-up can reduce tax revenue or limit how much redistribution reaches poorer households.",
        ),
        (
            "The effect depends on benefit targeting and whether costs such as housing absorb the income gain.",
            "Childcare and training can raise pre-tax earnings but take time and may complement rather than replace redistribution.",
        ),
    ),
    "4.3": Scenario(
        "foreign direct investment",
        "economic development",
        "FDI involves lasting investment and control in an overseas business; development includes health, education and living standards as well as output.",
        (
            "A foreign manufacturer builds a factory, trains local workers and buys some domestic inputs.",
            "The government offers tax concessions, and the investor may repatriate profits or import specialist equipment.",
        ),
        (
            "Capital, skills and local purchasing can raise productivity, employment and incomes, with spillovers to domestic suppliers.",
            "Profit repatriation, imported inputs and tax concessions limit domestic income and fiscal gains, while environmental costs may fall on local communities.",
        ),
        (
            "Benefits depend on local skills, supply linkages and the state's ability to enforce standards.",
            "Dependence on one investor creates vulnerability to relocation; compare the opportunity cost of incentives with education or infrastructure.",
        ),
    ),
    "4.4": Scenario(
        "greater access to bank credit",
        "investment and financial stability",
        "Banks channel finance to borrowers; asymmetric information and moral hazard can cause credit-market failure.",
        (
            "Banks offer more loans to small businesses with investment plans, but cannot perfectly observe project risks.",
            "Managers are rewarded for loan growth, and borrowers face variable interest rates.",
        ),
        (
            "Credit relaxes finance constraints, enabling investment, employment and productive capacity to expand.",
            "Weak screening or incentives to take risk can increase defaults and bank losses, reducing future lending and amplifying an economic downturn.",
        ),
        (
            "The gain depends on project quality and whether credit finances productive capital rather than unsustainable speculation.",
            "Prudential regulation can limit systemic risk but may raise borrowing costs or exclude viable firms with little collateral.",
        ),
    ),
    "4.5": Scenario(
        "greater public investment",
        "firms, households and economic performance",
        "Public investment creates assets and raises aggregate demand; opportunity cost is the next-best use of the resources committed.",
        (
            "Government plans transport and training investment financed by borrowing while some domestic resources are unemployed.",
            "Projects face construction delays and some equipment must be imported; private firms may expand if transport becomes more reliable.",
        ),
        (
            "Spending raises demand and employment initially, while better infrastructure and skills can lower business costs and increase productive capacity.",
            "Reliable networks can encourage private investment, but borrowing, taxes or resource competition may displace private spending or another public service.",
        ),
        (
            "Spare capacity and import leakages determine the short-run multiplier and inflation effect.",
            "Project selection, delivery and use determine long-run returns; weak information or political incentives can create government failure.",
        ),
    ),
}


SOURCE_DETAILS = {
    "1.2.2": (
        "Supermarkets trial smaller own-brand packs in neighbourhoods where food spending absorbs more of household budgets.",
        "Some shoppers retain premium purchases for special occasions but choose cheaper staples each week.",
        "Retailers can add shelf space quickly, although suppliers need longer to change packaging and production.",
    ),
    "1.2.3": (
        "Semiconductor producers must reserve specialist components months before delivery and qualify new machinery before commercial use.",
        "Existing factories can add shifts, but trained technicians are scarce and overtime raises production costs.",
        "Customers can postpone some orders, while vehicle manufacturers need the components to complete their products.",
    ),
    "1.2.4": (
        "Retailers initially draw down stocks and renegotiate deliveries with growers outside the affected region.",
        "Protected growers have higher heating bills, whereas exposed farms suffer larger harvest losses.",
        "Imported vegetables arrive later and must meet the same quality requirements as domestic produce.",
    ),
    "1.3": (
        "Nearby residents pay to clean polluted water, while the factory's accounts record only its own treatment expenses.",
        "Monitoring stations find that exposure differs with distance and weather, making compensation difficult to target.",
        "Clean equipment requires temporary closure, and smaller producers cannot finance installation as readily.",
    ),
    "1.4": (
        "The proposed tax would apply to each unit sold, including output from small producers.",
        "Officials can observe sales more easily than the pollution caused by each production method.",
        "Cleaner producers request differentiated treatment, while retailers worry about customers switching to untaxed imports.",
    ),
    "3.1": (
        "The manufacturer plans a second site with larger machines, a central purchasing team and shared distribution.",
        "Orders are not guaranteed, and the new site will initially operate below its designed capacity.",
        "Local managers seek greater discretion after delays in obtaining decisions from the central office.",
    ),
    "3.2": (
        "Sales managers favour introductory discounts and investment in delivery coverage, while owners monitor cash flow.",
        "A larger customer base may bring repeat orders, but competitors can match the discounts.",
        "Employees request predictable shifts as the business extends operating hours to support expansion.",
    ),
    "3.3": (
        "The bakery sells bread for £2.50 a loaf and is testing customer responses before revising its price list.",
        "Its £2,400 monthly lease cannot be changed this year, although flour purchases vary with production.",
        "An efficient oven would reduce energy use but require borrowing and a temporary production shutdown.",
    ),
    "3.4": (
        "In this digital-games market, new studios need distribution access and must recover development spending before earning profit.",
        "Players value existing game libraries, while an online entrant offers a subscription that works across devices.",
        "Incumbents can respond through exclusive content, lower fees or improved service rather than price alone.",
    ),
    "3.5": (
        "Employers advertise higher hourly pay, but applicants also ask about transport, childcare and shift flexibility.",
        "In some towns a single large employer gives the labour market monopsony features; other towns have several competing providers.",
        "Training places expand slowly because experienced staff must supervise trainees as well as maintain existing services.",
    ),
    "3.6": (
        "Providers cannot reduce maintenance indefinitely without affecting reliability and the condition of their assets.",
        "Consumers with flexible schedules may obtain the scarce service more easily than those needing it at peak times.",
        "Officials consider eligibility rules and additional public supply, but both require administration and funding.",
    ),
    "2.1": (
        "The firm's £30,000 monthly wage bill adjusts slowly because hours and contracts were agreed before orders weakened.",
        "Input prices rise by 6% during the same period, so weaker demand does not remove every source of price pressure.",
        "A training programme addresses vacant technical posts, while other unemployed workers previously worked in declining sectors.",
    ),
    "2.2": (
        "Construction firms can hire unemployed workers, but specialist machinery must be ordered from abroad.",
        "Local suppliers expect more orders only if the proposed factory opens and continues to operate.",
        "Lenders require evidence of future sales before releasing the full investment loan.",
    ),
    "2.3": (
        "Installation temporarily interrupts production, and workers need training before the technology reaches its planned efficiency.",
        "Customers may place orders elsewhere during the interruption, making the eventual use of the new capacity uncertain.",
        "Reliable transport and electricity are needed alongside the new machinery to secure productivity gains.",
    ),
    "2.4": (
        "Local builders have idle equipment, although some specialised materials must be imported.",
        "Payments reach suppliers before all households receive higher earnings, so spending effects occur at different times.",
        "The government must service its borrowing and cannot fund every proposed project from the same budget.",
    ),
    "2.5": (
        "Skilled workers obtain most of the new jobs, while some routine tasks are automated.",
        "Residents near industrial sites report heavier traffic and increased pressure on local services.",
        "Tax receipts may fund education and transport, but these projects take time to change living conditions.",
    ),
    "2.6": (
        "Borrowers on variable rates face higher payments immediately; fixed-rate borrowers are affected when contracts renew.",
        "Some firms postpone investment, while savers receive more interest income.",
        "Imported costs and wage negotiations can keep inflation elevated even as domestic orders weaken.",
    ),
    "4.1": (
        "Exporters quote some contracts in domestic currency and others in the buyer's currency.",
        "Import-dependent producers gain lower input costs but may still face weaker overseas demand for finished goods.",
        "Hedging and existing contracts delay price changes, and customers need time to find alternative suppliers.",
    ),
    "4.2": (
        "The local advice centre has a six-week waiting list and closes before evening-shift workers finish.",
        "Housing costs absorb more of the benefit in areas with limited accommodation supply.",
        "Childcare availability and travel costs affect whether recipients can increase their earnings through employment.",
    ),
    "4.3": (
        "The foreign-owned factory offers training, but senior technical roles initially require staff from abroad.",
        "Local suppliers must meet quality standards before receiving long-term contracts.",
        "Residents expect jobs but are concerned about water use and whether tax concessions reduce public-service funding.",
    ),
    "4.4": (
        "New borrowers include productive businesses with little collateral and projects with uncertain future revenues.",
        "Loan officers cannot fully observe how borrowers use funds after approval.",
        "When interest rates rise, repayment difficulties can spread across borrowers exposed to the same market.",
    ),
    "4.5": (
        "The proposed transport link could shorten delivery times, but construction disrupts existing routes.",
        "Training providers need staff and premises before expanding places, and firms must release workers to attend.",
        "Project costs compete with health and maintenance budgets, while benefits depend on whether firms use the improved network.",
    ),
}


def concrete_fallback(question):
    """Replace only a task whose old credit was generated topic-note boilerplate."""
    if question.parts or not any(
        "Correctly identifies or defines" in p or "syllabus alignment" in p
        for p in question.mark_scheme
    ):
        return question
    scenario = SCENARIOS[question.topic_id]
    reference = (
        f"With reference to {question.source_reference}, "
        if question.source_reference
        else ""
    )
    if question.marks == 5:
        task = f"explain one likely effect of {scenario.event} on {scenario.outcome}."
    elif question.marks == 8:
        task = f"examine two factors influencing the effects of {scenario.event} on {scenario.outcome}."
    elif question.marks == 12:
        task = f"discuss whether {scenario.event} is likely to have mainly beneficial effects on {scenario.outcome}."
    elif question.marks == 15:
        task = f"discuss how the short-run and long-run effects of {scenario.event} on {scenario.outcome} may differ."
    else:
        scope = (
            "microeconomic and macroeconomic "
            if question.number.startswith(("1(", "2(")) and question.marks == 25
            else ""
        )
        task = f"{question.command_word} the likely {scope}effects of {scenario.event} on {scenario.outcome}."
    prompt = reference + task if reference else task[:1].upper() + task[1:]
    market = {
        "1.2.2": "Household food purchases",
        "1.2.3": "Semiconductor production",
        "1.2.4": "Vegetable production and retail",
        "1.3": "Industrial production and neighbouring households",
        "1.4": "Polluting producers and cleaner substitutes",
        "3.1": "Manufacturing expansion",
        "3.2": "Business managers, owners and employees",
        "3.3": "Local bakeries",
        "3.4": "Digital games",
        "3.5": "Skilled employment",
        "3.6": "An essential service",
        "2.1": "Household spending and manufacturing orders",
        "2.2": "Manufacturing investment",
        "2.3": "Technology and workforce training",
        "2.4": "Public construction",
        "2.5": "Manufacturing, employment and local services",
        "2.6": "Borrowers and savers",
        "4.1": "Exporters and import-dependent producers",
        "4.2": "Household incomes and transfers",
        "4.3": "Foreign-owned manufacturing",
        "4.4": "Business lending",
        "4.5": "Transport and training projects",
    }[question.topic_id]
    context = f"{market}. " + " ".join(scenario.facts)
    details = SOURCE_DETAILS[question.topic_id]
    indices = {
        5: (0, 1),
        8: (1, 2),
        10: (0, 1, 2),
        12: (0, 1, 2),
        15: (2, 0),
        25: (0, 1, 2),
    }[question.marks]
    context += " " + " ".join(details[i] for i in indices)
    if question.section == "C":
        # Essay choices have short stimulus extracts, not a full article that
        # overflows the shared question page. Both facts are printed in full.
        context = " ".join(scenario.facts)
    points = [scenario.concept, *scenario.facts, *scenario.routes]
    if question.marks >= 8:
        points.extend(scenario.limits)
    return question.model_copy(
        update={
            "prompt": prompt,
            "source_text": context,
            "mark_scheme": points,
            "indicative_content": points,
        }
    )
