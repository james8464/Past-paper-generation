from __future__ import annotations


LINE_CHART_SERIES: dict[str, tuple[str, str, tuple[float, ...]]] = {
    "household_savings_line_chart": (
        "%",
        "Quarter",
        (8.8, 9.6, 7.3, 4.8, 5.1, 22.8, 13.4, 16.9, 10.1),
    ),
    "investment_line_chart": (
        "% GDP",
        "Quarter",
        (22.7, 23.3, 21.6, 24.2, 23.1, 21.6, 20.8, 22.4, 22.7, 22.8, 22.5),
    ),
    "current_account_line_chart": (
        "% GDP",
        "Year",
        (-3.8, -4.6, -4.9, -4.8, -5.2, -3.8, -4.2, -3.5, -3.7, -4.3),
    ),
    "inequality_line_chart": (
        "Gini coefficient",
        "Year",
        (0.42, 0.40, 0.38, 0.35, 0.33),
    ),
    "terms_of_trade_index_chart": (
        "Index",
        "Year",
        (82, 79, 80, 81, 83, 92, 92, 88, 85, 86, 91),
    ),
    "exchange_rate_index_chart": (
        "Index",
        "Year",
        (100, 96, 91, 94, 101, 106, 109),
    ),
}

TABLE_ROWS: dict[str, list[list[str]]] = {
    "ped_data_table": [["Age group", "PED"], ["16-18", "-0.7"], ["Adult", "-0.4"]],
    "pes_data_table": [["Region", "PES coefficient"], ["Urban", "0.5"], ["Rural", "1.8"]],
    "development_data_table": [
        ["Country", "HDI", "GNI per head", "GDP per capita"],
        ["Morocco", "0.683", "7 303", "3 795"],
        ["Pakistan", "0.544", "4 624", "1 473"],
    ],
    "balance_payments_table": [["Year", "Exports", "Imports"], ["2021", "612", "645"], ["2022", "701", "748"], ["2023", "742", "789"]],
    "inflation_index_table": [["Year", "CPI index", "Inflation"], ["2021", "100.0", "2.5%"], ["2022", "109.1", "9.1%"], ["2023", "116.0", "6.3%"]],
    "concentration_ratio_table": [["Firm", "Market share", "Rank"], ["A", "26.6%", "1"], ["B", "19.5%", "2"], ["C", "12.7%", "3"]],
    "elasticity_data_table": [["Good", "PED", "YED"], ["Bus travel", "-0.6", "+0.2"], ["Cinema", "-1.4", "+1.8"], ["Fuel", "-0.2", "+0.1"]],
    "marginal_utility_table": [["Units consumed", "Total utility", "Marginal utility"], ["1", "42", "42"], ["2", "72", "30"], ["3", "90", "18"], ["4", "98", "8"]],
    "opportunity_cost_ppc_table": [["Consumer goods", "100", "85", "60", "20"], ["Capital goods", "0", "20", "40", "60"]],
    "shutdown_cost_table": [["Output", "Price", "AVC", "AC"], ["500", "£18", "£14", "£22"]],
    "wage_rate_table": [["Year", "Average hourly wage", "Vacancies"], ["2021", "£12.00", "18 400"], ["2024", "£14.00", "26 700"]],
    "contestability_barrier_table": [["Barrier", "Indicator"], ["Sunk costs", "High"], ["Switching costs", "Medium"], ["Legal barriers", "Low"]],
    "income_tax_schedule_table": [["Band", "Taxable income", "Marginal rate"], ["Basic", "£12 571-£50 270", "20%"], ["Higher", "£50 271-£125 140", "40%"], ["Additional", "over £125 140", "45%"]],
    "public_spending_pie_table": [["Area", "Share"], ["Health", "21%"], ["Education", "10%"], ["Debt interest", "8%"], ["Defence", "5%"]],
    "data_table": [["Year", "Quantity demanded index", "Average price index"], ["2021", "74.2", "68.5"], ["2022", "81.6", "71.4"], ["2023", "88.0", "75.2"]],
}


def line_chart_data(kind: str) -> tuple[str, str, list[float]]:
    y_label, x_label, values = LINE_CHART_SERIES.get(
        kind,
        ("Index", "Year", (74.2, 81.6, 78.5, 88.0)),
    )
    return y_label, x_label, list(values)


def line_chart_values(kind: str) -> list[float]:
    series = LINE_CHART_SERIES.get(kind)
    return list(series[2]) if series else []


def table_rows(kind: str) -> list[list[str]]:
    rows = TABLE_ROWS.get(kind, TABLE_ROWS["data_table"])
    return [list(row) for row in rows]


def review_table_rows(kind: str) -> list[list[str]]:
    rows = TABLE_ROWS.get(kind)
    return [list(row) for row in rows] if rows else []
