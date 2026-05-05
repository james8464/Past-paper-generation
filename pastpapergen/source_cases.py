from __future__ import annotations

GENERIC_SOURCE_ATTRIBUTION = "Source: adapted from public reports and economic data"


def data_response_extract(topic_title: str, points: list[str], index: int) -> str:
    title = _normalise(topic_title)
    cases = _DATA_RESPONSE_CASES.get(title)
    if cases is None:
        cases = _macro_fallback(topic_title, points) if _is_macro_title(title) else _micro_fallback(topic_title, points)
    return cases[index % len(cases)]


def section_c_extract(topic_title: str, points: list[str], index: int) -> str:
    title = _normalise(topic_title)
    cases = _SECTION_C_CASES.get(title) or _section_c_fallback(topic_title, points)
    return cases[index % len(cases)]


def _normalise(title: str) -> str:
    return title.lower().strip()


def _is_macro_title(title: str) -> bool:
    return title.startswith(("measures", "aggregate", "national", "economic growth", "macroeconomic", "international", "poverty", "emerging", "financial", "role of"))


_DATA_RESPONSE_CASES: dict[str, list[str]] = {
    "market structures": [
        "In October 2023, the Competition and Markets Authority gave consent for Microsoft to acquire Activision Blizzard after the cloud gaming rights outside the European Economic Area were excluded from the deal. Microsoft argued the merger would improve access to games across devices, while rivals said exclusive content could reduce consumer choice.",
        "The UK digital games market includes console sales, subscriptions, mobile apps and cloud gaming. Consumers often stay with one platform because of existing game libraries, friends' networks and exclusive titles. Independent developers said platform fees and marketing costs made it harder to compete with established firms.",
        "A digital entertainment survey estimated that the four largest console game publishers accounted for more than half of UK boxed and digital sales in 2024. Some firms used online distribution to reduce marginal costs, but high fixed costs for game development increased the importance of economies of scale.",
        "Competition authorities said intervention may be needed where mergers reduce contestability or increase barriers to entry. Supporters of mergers argued that larger firms can fund innovation and spread development costs; critics argued that market power may lead to higher prices, lower quality or less choice.",
    ],
    "labour market": [
        "GOV.UK announced that hourly pay under the National Living Wage for workers aged 21 and over rose to GBP11.44 per hour in April 2024, an increase of 9.8%. Hospitality firms said the rise increased wage costs, but trade unions argued it improved living standards and incentives to work.",
        "Care homes, hotels and restaurants reported recruitment difficulties after the pandemic. Some workers moved to retail or logistics jobs with more predictable hours. Firms responded by offering flexible shifts, staff discounts and training, although smaller businesses said they had less ability to raise pay.",
        "In one coastal labour market, five large employers accounted for a high share of advertised vacancies for seasonal workers. Trade unions claimed this gave firms monopsony power, while employers said labour shortages meant workers could move between firms more easily than before.",
        "The Low Pay Commission has argued that the effects of minimum wages depend on productivity, profit margins and the price elasticity of demand for labour. Some firms may accept lower profits, while others may raise prices, reduce hours or invest in labour-saving technology.",
    ],
    "revenues, costs and profits": [
        "Ryanair and easyJet both reported in 2024 that fuel, airport and wage costs were important pressures after international travel recovered. Airlines tried to keep load factors high by filling a large share of seats, because many costs such as aircraft leases and landing slots are fixed in the short run.",
        "A UK bakery chain reported higher electricity, flour and staff costs during 2023 and 2024. Managers said price rises protected profit margins, but sales of premium products became more sensitive as household budgets were squeezed by inflation.",
        "Consumers became more price sensitive during 2023 and 2024 as real incomes were squeezed. Tesco and Sainsbury's used loyalty-card discounts to protect sales volumes.",
        "A manufacturer of electric vans said output could not expand quickly because specialist machinery and skilled labour were fixed in the short run. In the long run, investment in a larger factory could reduce average costs, but only if demand remained strong.",
    ],
    "price determination": [
        "In 2022, the UK government offered new North Sea oil and gas licences, arguing that domestic production could improve energy security. Firms said new exploration may take many years before supply increases, suggesting supply is price inelastic in the short run.",
        "Wholesale gas prices rose sharply after Russia's invasion of Ukraine. Ofgem's price cap limited the extent to which suppliers could pass higher costs to households immediately, but many firms still faced cash-flow pressures.",
        "Used car prices rose when shortages of semiconductors reduced the supply of new cars. Buyers switched into second-hand markets, increasing demand for used cars at the same time as supply was limited.",
        "When supply is slow to respond, changes in demand can cause large price movements. Analysts said markets with storage costs, capacity limits or long production lags are more likely to experience volatile prices.",
    ],
    "market failure": [
        "Nearly 750,000 consumers in Britain were reported to have unresolved problems with used-car purchases. Consumer groups argued that imperfect information allowed some sellers to charge higher prices for poor-quality cars.",
        "Local councils considering clean-air zones said road traffic created external costs including congestion, noise and air pollution. Delivery firms argued that charges increased costs and could be passed on to consumers.",
        "The Competition and Markets Authority has investigated markets where consumers find it difficult to compare prices or cancel contracts. Behavioural biases such as inertia may reduce competitive pressure on firms.",
        "Policy makers may use regulation, taxes or information campaigns to reduce market failure. The overall effect depends on the size of the external cost, enforcement costs and whether consumers and firms change behaviour.",
    ],
    "government intervention": [
        "Ofgem's energy price cap limited the maximum unit price charged to many households. Supporters said the cap protected consumers from sudden price rises, while suppliers argued it reduced incentives for new firms to enter the market.",
        "The Soft Drinks Industry Levy encouraged some producers to reformulate drinks with lower sugar content. Public health groups said this could reduce negative externalities, while some businesses said the levy increased compliance costs.",
        "London's Ultra Low Emission Zone charged some drivers of more polluting vehicles. The policy aimed to reduce air pollution, but critics argued it placed a higher burden on low-income drivers who could not easily replace older cars.",
        "Government intervention can create winners and losers. A subsidy may increase output and reduce prices, but it also has an opportunity cost because public funds could be used elsewhere.",
    ],
    "government intervention in markets": [
        "Ofgem's energy price cap limited the maximum unit price charged to many households. Supporters said the cap protected consumers from sudden price rises, while suppliers argued it reduced incentives for new firms to enter the market.",
        "The Soft Drinks Industry Levy encouraged some producers to reformulate drinks with lower sugar content. Public health groups said this could reduce negative externalities, while some businesses said the levy increased compliance costs.",
        "London's Ultra Low Emission Zone charged some drivers of more polluting vehicles. The policy aimed to reduce air pollution, but critics argued it placed a higher burden on low-income drivers who could not easily replace older cars.",
        "Government intervention can create winners and losers. A subsidy may increase output and reduce prices, but it also has an opportunity cost because public funds could be used elsewhere.",
    ],
    "measures of economic performance": [
        "The Office for National Statistics (ONS) reported that UK CPI inflation reached 11.1% in October 2022 before falling during 2023 and 2024. Households on low incomes said food and energy prices had a larger effect on living standards than the headline rate suggested.",
        "Real GDP measures the value of output adjusted for inflation, but it does not show how income is distributed or whether growth is sustainable. Some regions reported stronger services growth, while manufacturing output remained under pressure from high costs.",
        "Unemployment data can understate weakness if people leave the labour force. In 2024, long-term sickness became an important UK policy concern.",
        "Economists use a range of indicators including GDP per head, inflation, unemployment, productivity and the current account. A government may face trade-offs when one indicator improves while another worsens.",
    ],
    "aggregate demand": [
        "The Bank of England increased Bank Rate to 5.25% in August 2023 to help bring inflation back towards its 2% target. Higher mortgage payments reduced disposable income for some households and weakened consumption.",
        "Retailers reported that consumers traded down to cheaper own-brand products when food prices rose. This reduced demand for premium brands but increased sales volumes for some discount supermarkets.",
        "Government spending on health, transport and education can increase aggregate demand directly. However, higher borrowing may put pressure on future taxes or interest payments.",
        "A fall in consumer confidence may reduce spending on durable goods such as cars and furniture. The multiplier effect depends on leakages through savings, taxes and imports.",
    ],
    "aggregate supply": [
        "Firms in energy-intensive industries such as steel, glass and chemicals faced higher costs when wholesale gas prices increased. Some reduced output or delayed investment, shifting short-run aggregate supply left.",
        "Investment in ports, broadband and transport infrastructure may increase productive capacity. The effects on long-run aggregate supply depend on project delivery, skills and whether private investment is crowded in.",
        "The UK labour market experienced shortages in health care, construction and hospitality. Training and migration policies can affect the quantity and quality of labour available to firms.",
        "Productivity growth has been weak in many advanced economies since the financial crisis. If output per worker rises slowly, real wages and living standards may also grow slowly.",
    ],
    "national income": [
        "A fall in injections such as investment or exports can reduce national income through the multiplier process. The final change depends on the marginal propensity to consume and the size of leakages.",
        "During the pandemic, government support schemes helped maintain household incomes even as output fell. This affected consumption patterns and public borrowing.",
        "A rise in imports can reduce the value of the multiplier because spending leaks out of the domestic circular flow. The effect may be larger for economies that rely heavily on imported energy or components.",
        "National income statistics help governments forecast tax revenue and welfare spending. However, revisions to data mean policy may be based on incomplete information.",
    ],
    "economic growth": [
        "ONS data showed that the UK economy recovered from the pandemic shock, but growth remained uneven across sectors. Hospitality and travel recovered as restrictions ended, while some manufacturers faced supply-chain pressures.",
        "Economic growth can improve tax receipts and employment, but it may also increase negative externalities if it relies on higher resource use. The effect depends on the composition and sustainability of growth.",
        "Businesses said uncertainty over energy prices and interest rates delayed some investment projects. Lower investment may reduce capital accumulation and future productive capacity.",
        "Governments may try to raise trend growth through education, infrastructure and incentives for research and development. These policies usually take time to affect productivity.",
    ],
    "macroeconomic objectives and policies": [
        "The Bank of England increased Bank Rate to 5.25% in August 2023 as part of monetary policy aimed at reducing inflation. Higher rates affected mortgages, business loans and exchange rates.",
        "Fiscal policy can support demand during a downturn, but expansionary policy may increase borrowing. After energy prices rose, the UK government introduced support for households and firms.",
        "Supply-side policies such as training, childcare support and infrastructure investment may reduce unemployment and increase productive capacity. However, they can be expensive and slow to take effect.",
        "Policy makers face conflicts between objectives. Reducing inflation may slow growth, while faster growth can increase imports and pressure the current account.",
    ],
    "international economics": [
        "ONS Pink Book data reported that the UK's trade deficit narrowed in 2023, partly because the goods deficit narrowed. The UK continued to run a surplus in services, including financial and business services.",
        "A depreciation of sterling can make UK exports cheaper overseas and imports more expensive. The final effect on the current account depends on price elasticities of demand and supply constraints.",
        "Protectionist policies such as tariffs may protect domestic jobs in the short run. However, firms using imported components may face higher costs, and trading partners may retaliate.",
        "The UK has sought trade agreements outside the EU, but firms said rules of origin, customs paperwork and standards checks still affected costs and delivery times.",
    ],
    "poverty and inequality": [
        "The Office for National Statistics reported that disposable income inequality, measured by the Gini coefficient, was 32.9% in financial year ending 2024. Charities argued that housing costs made poverty worse for low-income renters.",
        "Food banks reported high demand when energy and food prices rose. Low-income households spent a larger share of income on essentials, making them more vulnerable to inflation.",
        "Progressive taxation and welfare payments can reduce income inequality after taxes and benefits. However, high marginal tax rates may affect incentives to work or train.",
        "Regional inequality can persist when high-skilled jobs, transport links and investment are concentrated in a few cities. Policies to reduce inequality may require both demand-side and supply-side measures.",
    ],
    "emerging and developing economies": [
        "The World Bank updated its extreme poverty line to $2.15 per person per day using 2017 purchasing power parity prices. Many low-income economies remained vulnerable to food, fuel and debt shocks.",
        "Some emerging economies benefited from foreign direct investment in manufacturing and digital services. However, profits may be repatriated and jobs may depend on global demand.",
        "Rapid growth can reduce poverty if it creates employment and raises tax revenue. It may also increase pollution, urban congestion and regional inequality.",
        "Governments in developing economies may face a savings gap, a foreign exchange gap and limited tax capacity. International aid, debt relief and remittances can affect development prospects.",
    ],
    "financial sector": [
        "The Bank of England's Financial Stability Report said major UK banks entered 2023 with strong capital and liquidity positions. Higher interest rates improved some lending margins but increased pressure on borrowers.",
        "Non-bank financial institutions such as pension funds and investment funds became more important in credit markets. Regulators warned that liquidity problems in these institutions could amplify financial shocks.",
        "Commercial banks create credit by lending to households and firms. If banks become more cautious during a downturn, reduced lending can lower investment and aggregate demand.",
        "Financial market failure can arise from asymmetric information, moral hazard and systemic risk. Regulation aims to protect consumers and reduce the probability of bank failure.",
    ],
    "role of the state in the macroeconomy": [
        "The UK government used tax, spending and regulation to respond to high energy prices and weak growth. Supporters argued that state intervention protected living standards; critics said it increased borrowing and distorted incentives.",
        "Public investment in the NHS, schools and transport can increase long-run productive potential. The opportunity cost is high because funds could be used for tax cuts or debt reduction.",
        "Automatic stabilisers such as unemployment benefits and progressive taxes can reduce fluctuations in income without new legislation. Their effect depends on the size of the public sector.",
        "A larger role for the state may help correct market failure and reduce inequality, but it can also create government failure if policies are poorly targeted or costly to administer.",
    ],
}


_SECTION_C_CASES: dict[str, list[str]] = {
    "government intervention in markets": [
        "Ofgem changed rules for the retail energy market after suppliers failed during the period of high wholesale gas prices. Evaluate the likely microeconomic effects of price controls or regulation in an energy market.",
        "London's Ultra Low Emission Zone was expanded to reduce air pollution from road transport. Evaluate the likely microeconomic effects of charging drivers of more polluting vehicles.",
    ],
    "labour market": [
        "The Low Pay Commission recommended increases in minimum wage rates after evidence on pay, employment and business costs. Evaluate the likely effects of a higher minimum wage on workers and firms.",
        "Some NHS and care providers reported staff shortages and rising agency costs. Evaluate the likely effects of occupational immobility in a labour market.",
    ],
    "market structures": [
        "The CMA approved Microsoft's revised acquisition of Activision Blizzard after changes to cloud gaming rights. Evaluate the likely effects of mergers in a digital market.",
        "TikTok's owner ByteDance has entered markets outside social media, including retail and consumer products. Evaluate the level of contestability in a market of your choice.",
    ],
    "market failure": [
        "Local authorities considered clean-air zones to reduce congestion and pollution. Evaluate whether government intervention is likely to correct market failure in transport.",
        "Consumer groups reported unresolved problems in the used-car market. Evaluate the microeconomic effects of imperfect information in a market of your choice.",
    ],
    "international economics": [
        "ONS data showed the UK continued to run a services surplus while importing many goods. Evaluate the likely effects of a persistent trade deficit in goods.",
        "Several countries used tariffs and subsidies to support domestic green industries. Evaluate the likely effects of increased protectionism on an economy.",
    ],
    "poverty and inequality": [
        "ONS data showed UK disposable income inequality changed little in FYE 2024. Evaluate the likely effects of policies designed to reduce income inequality.",
        "Food banks reported high demand after increases in energy and food prices. Evaluate the likely economic effects of poverty on households and the wider economy.",
    ],
    "emerging and developing economies": [
        "The World Bank's $2.15 extreme poverty line is used to compare living standards across low-income economies. Evaluate the likely effects of rapid economic growth on poverty.",
        "Some developing economies received increased foreign direct investment in manufacturing. Evaluate the likely benefits and drawbacks of FDI for development.",
    ],
}


def _micro_fallback(topic_title: str, points: list[str]) -> list[str]:
    title = topic_title.lower()
    first = points[0] if points else title
    second = points[1] if len(points) > 1 else first
    third = points[2] if len(points) > 2 else second
    return [
        f"A UK market report by a consumer group and the CMA described changes in {title}. It found that {first} affected prices, output and consumer choices, with some firms responding faster than others.",
        f"Businesses in this market reported different cost pressures during 2023 and 2024. Larger firms were more able to use technology and bulk purchasing, while smaller firms said {second} made adjustment harder.",
        f"Survey evidence suggested consumers became more price sensitive as real incomes were squeezed. Firms responded with discounts, loyalty schemes and changes in product quality.",
        f"Policy makers considered whether intervention was needed. Supporters argued that action could improve outcomes linked to {third}; critics argued that intervention may create unintended consequences.",
    ]


def _macro_fallback(topic_title: str, points: list[str]) -> list[str]:
    title = topic_title.lower()
    first = points[0] if points else title
    second = points[1] if len(points) > 1 else first
    third = points[2] if len(points) > 2 else second
    return [
        f"ONS and Bank of England data showed that {title} affected households and firms during 2023 and 2024. The evidence suggested {first} influenced spending, saving and investment decisions.",
        f"Businesses reported that higher borrowing costs and energy prices changed plans for investment and employment. Some exporters benefited from stronger overseas demand, while importers faced cost pressures linked to {second}.",
        f"Households on lower incomes were more exposed to changes in prices because essentials took a larger share of their budgets. This affected consumption and may have reduced the multiplier effect.",
        f"Policy makers considered whether fiscal, monetary or supply-side policies were most appropriate. The final effect depended on confidence, spare capacity and the extent to which {third} changed incentives.",
    ]


def _section_c_fallback(topic_title: str, points: list[str]) -> list[str]:
    title = topic_title.lower()
    focus = points[0] if points else title
    return [
        f"A public report in 2024 described a UK issue linked to {title}. It suggested that {focus} could affect consumers, firms and government decisions in different ways.",
        f"Economists disagreed about the likely short-run and long-run effects of changes in {title}. Some emphasised efficiency and incentives, while others focused on equity and welfare.",
    ]
