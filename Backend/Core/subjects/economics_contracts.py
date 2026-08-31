"""Candidate data and bounded Edexcel calculations, never draft answer keys."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from Backend.Core.numeric_integrity import NUMBER, NumericOutput, numeric_result

ECONOMICS_CONTRACT_VERSION = "edexcel-instance-v1"


class SourceCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str = ""
    number: Decimal | None = None
    unit: Literal["1", "GBP", "%", "index", "units"] = "1"

    @model_validator(mode="after")
    def coherent(self):
        if self.number is not None and (self.text or not self.number.is_finite()):
            raise ValueError(
                "source cell must contain finite numeric data or text, not both"
            )
        return self

    def printed(self) -> str:
        if self.number is None:
            return self.text
        value = format(self.number, "f")
        return (
            f"£{value}"
            if self.unit == "GBP"
            else value + ("%" if self.unit == "%" else "")
        )


class EconomicsSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["edexcel-instance-v1"] = ECONOMICS_CONTRACT_VERSION
    source_id: str
    kind: str
    context: str = ""
    provenance: Literal["illustrative-generated"] = "illustrative-generated"
    rows: list[list[SourceCell]] = Field(default_factory=list)
    values: list[Decimal] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    y_label: str = ""
    x_label: str = ""
    unit: Literal["1", "%", "index"] = "1"
    givens: dict[str, SourceCell] = Field(default_factory=dict)

    @model_validator(mode="after")
    def coherent(self):
        if len(self.values) != len(self.labels) or any(
            not x.is_finite() for x in self.values
        ):
            raise ValueError("source series needs finite values and matching labels")
        if self.rows and len({len(row) for row in self.rows}) != 1:
            raise ValueError("source table must be rectangular")
        return self

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(self.model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest()

    def cell(self, row: int, column: int, unit: str) -> Decimal:
        cell = self.rows[row][column]
        if cell.number is None or cell.unit != unit:
            raise ValueError("numeric source cell has wrong value type or unit")
        return cell.number


SUPPORTED_CALCULATIONS = {
    ("household_savings_line_chart", 2),
    ("current_account_line_chart", 2),
    ("terms_of_trade_index_chart", 2),
    ("exchange_rate_index_chart", 2),
    ("inequality_line_chart", 2),
    ("inequality_line_chart", 4),
    ("pes_data_table", 4),
    ("data_table", 2),
    ("data_table", 4),
    ("elasticity_data_table", 4),
    ("concentration_ratio_table", 4),
    ("opportunity_cost_ppc_table", 4),
    ("shutdown_cost_table", 4),
    ("wage_rate_table", 4),
    ("inflation_index_table", 2),
    ("inflation_index_table", 4),
    ("development_data_table", 2),
    ("income_tax_schedule_table", 2),
    ("public_spending_pie_table", 2),
    ("gdp_growth_bar_chart", 2),
}

# Deliberately latent: no candidate-visible denominator, scale, time series or
# before/after geometry. Listing a template does not make it answerable.
UNSUPPORTED_CALCULATIONS = {
    ("ped_data_table", 4): "missing price change and selected age group",
    ("market_share_bar_chart", 4): "missing market sales value and currency scale",
    ("balance_payments_table", 2): "missing currency and scale",
    ("balance_payments_table", 4): "missing currency and scale",
    ("cost_revenue_graph", 4): "missing before/after price, output and average cost",
    ("development_data_table", 4): "missing GDP currency, price basis and year",
    (
        "labour_inactivity_context",
        2,
    ): "missing working-age population and inactivity rate",
    (
        "multiplier_context",
        4,
    ): "missing injection, currency scale and multiplier assumptions",
    (
        "unemployment_rate_bar_chart",
        2,
    ): "cross-economy observations are not a time change",
    ("macro_chart", 2): "AD/AS geometry is not a percentage observation series",
    ("line_graph", 2): "declared percentage-point task has an index source",
}


def calculation_prompt(source: EconomicsSource, marks: int) -> str:
    """Code-owned requested operation, not a draft/model-provided instruction."""
    kind = source.kind
    if (kind, marks) not in SUPPORTED_CALCULATIONS:
        raise ValueError(f"unsupported Edexcel calculation: {kind}/{marks}")
    tasks = {
        "household_savings_line_chart": "Calculate the range of the saving rate, in percentage points, over the quarters shown.",
        "current_account_line_chart": "Calculate the increase in the size of the current-account deficit, in percentage points of GDP, from the first to the final year.",
        "terms_of_trade_index_chart": "Calculate the percentage increase in the terms-of-trade index from the first to the final year.",
        "exchange_rate_index_chart": "Calculate the percentage increase in the exchange-rate index from the first to the final year.",
        "inequality_line_chart": "Calculate the fall in the Gini coefficient from the first to the final year."
        if marks == 2
        else "Calculate the percentage fall in the Gini coefficient from the first to the final year.",
        "pes_data_table": "Calculate the percentage increase in price in the rural market using the stated increase in quantity supplied and the rural PES coefficient.",
        "data_table": "Calculate the difference between the quantity-demanded and average-price indices in 2023, in index points."
        if marks == 2
        else "Calculate the percentage increase in the quantity-demanded index from 2021 to 2023.",
        "elasticity_data_table": "Calculate the percentage change in quantity demanded for cinema visits following the stated price change, using the cinema PED coefficient.",
        "concentration_ratio_table": "Calculate the three-firm concentration ratio as a percentage.",
        "opportunity_cost_ppc_table": "Calculate the opportunity cost, in units of consumer goods, of increasing capital-goods output from 20 to 40 units.",
        "shutdown_cost_table": "Calculate the firm's total profit at the output shown. Give a negative value if it makes a loss.",
        "wage_rate_table": "Calculate the percentage increase in the average hourly wage from 2021 to 2024.",
        "inflation_index_table": "Calculate the increase in the CPI from 2021 to 2023, in index points."
        if marks == 2
        else "Calculate the percentage increase in the CPI from 2021 to 2023.",
        "development_data_table": "Calculate the difference between the two economies' HDI values, subtracting the lower value from the higher value.",
        "income_tax_schedule_table": "Calculate the additional tax due on the stated additional taxable income, assuming all of it falls within the higher band of the illustrative schedule.",
        "public_spending_pie_table": "Calculate the difference between the health and education spending shares, in percentage points.",
        "gdp_growth_bar_chart": "Calculate the change in the real GDP growth rate from the first to the final quarter, in percentage points. Give a negative value for a fall.",
    }
    dp = (
        0
        if kind == "opportunity_cost_ppc_table"
        else 3
        if kind == "development_data_table"
        else 2
        if kind in {"shutdown_cost_table", "income_tax_schedule_table"}
        or (kind == "inequality_line_chart" and marks == 2)
        else 1
    )
    return (
        tasks[kind]
        + f" Give your final answer to {dp} decimal {'place' if dp == 1 else 'places'}. Show your working."
    )


def _validate_calculation_source(source: EconomicsSource) -> None:
    # These are semantic input selectors, not answer constants. A numeric cell
    # in the same position under a different heading is a different quantity.
    role_cells = {
        "pes_data_table": {(0, 1): "PES coefficient", (2, 0): "Rural"},
        "elasticity_data_table": {(0, 1): "PED", (2, 0): "Cinema"},
        "data_table": {
            (0, 1): "Quantity demanded index",
            (0, 2): "Average price index",
            (1, 0): "2021",
            (3, 0): "2023",
        },
        "concentration_ratio_table": {(0, 1): "Market share"},
        "opportunity_cost_ppc_table": {
            (0, 0): "Consumer goods",
            (1, 0): "Capital goods",
            (1, 2): "20",
            (1, 3): "40",
        },
        "shutdown_cost_table": {(0, 0): "Output", (0, 1): "Price", (0, 3): "AC"},
        "wage_rate_table": {
            (0, 1): "Average hourly wage",
            (1, 0): "2021",
            (2, 0): "2024",
        },
        "inflation_index_table": {(0, 1): "CPI index", (1, 0): "2021", (3, 0): "2023"},
        "development_data_table": {(0, 1): "HDI"},
        "income_tax_schedule_table": {(0, 2): "Marginal rate", (2, 0): "Higher"},
        "public_spending_pie_table": {
            (0, 1): "Share",
            (1, 0): "Health",
            (2, 0): "Education",
        },
    }
    try:
        if any(
            source.rows[row][column].printed() != label
            for (row, column), label in role_cells.get(source.kind, {}).items()
        ):
            raise ValueError(
                "numeric source role does not match the requested quantity"
            )
    except IndexError as exc:
        raise ValueError("numeric source role is missing") from exc
    series_units = {
        "household_savings_line_chart": "%",
        "current_account_line_chart": "%",
        "terms_of_trade_index_chart": "index",
        "exchange_rate_index_chart": "index",
        "inequality_line_chart": "1",
        "gdp_growth_bar_chart": "%",
    }
    if source.kind in series_units:
        if (
            len(source.values) < 2
            or source.unit != series_units[source.kind]
            or len(set(source.labels)) != len(source.labels)
        ):
            raise ValueError(
                "Edexcel series has missing observations, labels or wrong units"
            )
        if source.kind == "current_account_line_chart" and any(
            v >= 0 for v in (source.values[0], source.values[-1])
        ):
            raise ValueError("deficit-size task requires initial and final deficits")
        if source.kind == "inequality_line_chart" and any(
            not 0 <= v <= 1 for v in source.values
        ):
            raise ValueError("Gini coefficients must use the zero-to-one scale")
        if source.kind in {
            "terms_of_trade_index_chart",
            "exchange_rate_index_chart",
        } and any(v <= 0 for v in source.values):
            raise ValueError("price indices must be positive")
    for name in {
        "pes_data_table": ["quantity_supply_change"],
        "elasticity_data_table": ["price_change"],
    }.get(source.kind, []):
        given = source.givens.get(name)
        if given is None or given.number is None or given.unit != "%":
            raise ValueError("missing candidate percentage input")
    if source.kind == "income_tax_schedule_table":
        given = source.givens.get("Additional taxable income")
        if (
            given is None
            or given.number is None
            or given.unit != "GBP"
            or given.number <= 0
        ):
            raise ValueError("missing candidate additional-income input")


def calculation_label(source: EconomicsSource, marks: int) -> str:
    return {
        "household_savings_line_chart": "Saving rate range",
        "current_account_line_chart": "Increase in deficit size",
        "terms_of_trade_index_chart": "Terms-of-trade percentage increase",
        "exchange_rate_index_chart": "Exchange-rate percentage increase",
        "inequality_line_chart": "Gini coefficient fall"
        if marks == 2
        else "Gini percentage fall",
        "pes_data_table": "Percentage price increase",
        "data_table": "Index difference"
        if marks == 2
        else "Quantity-index percentage increase",
        "elasticity_data_table": "Quantity-demanded percentage change",
        "concentration_ratio_table": "Three-firm concentration ratio",
        "opportunity_cost_ppc_table": "Consumer goods forgone",
        "shutdown_cost_table": "Total profit",
        "wage_rate_table": "Hourly-wage percentage increase",
        "inflation_index_table": "CPI index increase"
        if marks == 2
        else "CPI percentage increase",
        "development_data_table": "HDI difference",
        "income_tax_schedule_table": "Additional tax",
        "public_spending_pie_table": "Spending-share difference",
        "gdp_growth_bar_chart": "GDP-growth rate change",
    }[source.kind]


def _three_largest_shares(source: EconomicsSource) -> list[Decimal]:
    if len(source.rows) < 4 or any(len(row) not in {2, 3} for row in source.rows):
        raise ValueError("Concentration ratio requires at least three identified firms")
    firms = [row[0].text.strip().casefold() for row in source.rows[1:]]
    if not all(firms) or len(set(firms)) != len(firms):
        raise ValueError("Concentration shares require distinct firm identities")
    shares = [source.cell(row, 1, "%") for row in range(1, len(source.rows))]
    if any(not share.is_finite() or not 0 <= share <= 100 for share in shares):
        raise ValueError(
            "Market shares must be finite percentages between zero and 100"
        )
    if not 0 < sum(shares) <= 100:
        raise ValueError(
            "Listed market shares must have a positive total no greater than 100%"
        )
    return sorted(shares, reverse=True)[:3]


def calculation_working(source: EconomicsSource, marks: int) -> str:
    """Show substituted inputs without inventing unchecked intermediate outputs."""
    c, v, kind = source.cell, source.values, source.kind
    if kind == "household_savings_line_chart":
        return f"{max(v)} − {min(v)}"
    if kind == "current_account_line_chart":
        return f"|{v[-1]}| − |{v[0]}|"
    if kind in {"terms_of_trade_index_chart", "exchange_rate_index_chart"}:
        return f"({v[-1]} − {v[0]}) ÷ {v[0]} × 100"
    if kind == "inequality_line_chart":
        return (
            f"{v[0]} − {v[-1]}" if marks == 2 else f"({v[0]} − {v[-1]}) ÷ {v[0]} × 100"
        )
    if kind == "pes_data_table":
        return f"{source.givens['quantity_supply_change'].number} ÷ {c(2, 1, '1')}"
    if kind == "elasticity_data_table":
        return f"{c(2, 1, '1')} × ({source.givens['price_change'].number})"
    if kind == "data_table":
        return (
            f"{c(3, 1, 'index')} − {c(3, 2, 'index')}"
            if marks == 2
            else f"({c(3, 1, 'index')} − {c(1, 1, 'index')}) ÷ {c(1, 1, 'index')} × 100"
        )
    if kind == "concentration_ratio_table":
        return " + ".join(str(share) for share in _three_largest_shares(source))
    if kind == "opportunity_cost_ppc_table":
        return f"{c(0, 2, 'units')} − {c(0, 3, 'units')}"
    if kind == "shutdown_cost_table":
        return f"(£{c(1, 1, 'GBP')} − £{c(1, 3, 'GBP')}) × {c(1, 0, 'units')}"
    if kind == "wage_rate_table":
        return f"(£{c(2, 1, 'GBP')} − £{c(1, 1, 'GBP')}) ÷ £{c(1, 1, 'GBP')} × 100"
    if kind == "inflation_index_table":
        return (
            f"{c(3, 1, 'index')} − {c(1, 1, 'index')}"
            if marks == 2
            else f"({c(3, 1, 'index')} − {c(1, 1, 'index')}) ÷ {c(1, 1, 'index')} × 100"
        )
    if kind == "development_data_table":
        high, low = sorted((c(1, 1, "1"), c(2, 1, "1")), reverse=True)
        return f"{high} − {low}"
    if kind == "income_tax_schedule_table":
        return f"£{source.givens['Additional taxable income'].number} × {c(2, 2, '%')} ÷ 100"
    if kind == "public_spending_pie_table":
        return f"{c(1, 1, '%')} − {c(2, 1, '%')}"
    return f"{v[-1]} − {v[0]}"


def calculation(source: EconomicsSource, marks: int) -> dict:
    kind = source.kind
    if (kind, marks) not in SUPPORTED_CALCULATIONS:
        raise ValueError(f"unsupported Edexcel calculation: {kind}/{marks}")
    _validate_calculation_source(source)
    c, v = source.cell, source.values
    role, unit, dp = "result", "%", 1
    if kind == "household_savings_line_chart":
        role, unit, value = "saving_rate_range", "percentage points", max(v) - min(v)
        method = "Subtract the minimum saving rate from the maximum saving rate."
    elif kind == "current_account_line_chart":
        role, unit, value = (
            "deficit_size_increase",
            "percentage points",
            abs(v[-1]) - abs(v[0]),
        )
        method = (
            "Subtract the initial absolute deficit from the final absolute deficit."
        )
    elif kind in {"terms_of_trade_index_chart", "exchange_rate_index_chart"}:
        value = (v[-1] - v[0]) / v[0] * 100
        method = "Subtract the first index from the final index, divide by the first index and multiply by 100."
    elif kind == "inequality_line_chart":
        value = v[0] - v[-1]
        if marks == 2:
            unit, dp = "1", 2
        else:
            value = value / v[0] * 100
        method = "Find the initial minus final Gini coefficient." + (
            " Divide by the initial coefficient and multiply by 100."
            if marks == 4
            else ""
        )
    elif kind == "pes_data_table":
        value = source.givens["quantity_supply_change"].number / c(2, 1, "1")
        method = (
            "Divide the stated percentage quantity-supply increase by the rural PES."
        )
    elif kind == "data_table":
        value = c(3, 1, "index") - c(
            3 if marks == 2 else 1, 2 if marks == 2 else 1, "index"
        )
        if marks == 2:
            unit = "index points"
        else:
            value = value / c(1, 1, "index") * 100
        method = (
            "Use the specified quantity-demanded and price columns in 2023."
            if marks == 2
            else "Find the quantity-index increase, divide by its 2021 baseline and multiply by 100."
        )
    elif kind == "elasticity_data_table":
        value = c(2, 1, "1") * source.givens["price_change"].number
        method = "Multiply cinema PED by the stated signed percentage price change."
    elif kind == "concentration_ratio_table":
        value = sum(_three_largest_shares(source))
        method = "Add the market shares of the three largest firms."
    elif kind == "opportunity_cost_ppc_table":
        value, unit, dp = c(0, 2, "units") - c(0, 3, "units"), "consumer units", 0
        method = "Find the consumer goods forgone between the specified capital-output columns."
    elif kind == "shutdown_cost_table":
        value, unit, dp = (c(1, 1, "GBP") - c(1, 3, "GBP")) * c(1, 0, "units"), "GBP", 2
        method = "Subtract average total cost from price and multiply by output; a negative profit is a loss."
    elif kind == "wage_rate_table":
        value = (c(2, 1, "GBP") - c(1, 1, "GBP")) / c(1, 1, "GBP") * 100
        method = (
            "Divide the hourly-wage increase by the initial wage and multiply by 100."
        )
    elif kind == "inflation_index_table":
        value = c(3, 1, "index") - c(1, 1, "index")
        if marks == 2:
            unit = "index points"
        else:
            value = value / c(1, 1, "index") * 100
        method = "Use CPI index levels, not the separate annual inflation-rate column."
    elif kind == "development_data_table":
        value, unit, dp = abs(c(1, 1, "1") - c(2, 1, "1")), "1", 3
        method = "Subtract the lower HDI from the higher HDI."
    elif kind == "income_tax_schedule_table":
        value = source.givens["Additional taxable income"].number * c(2, 2, "%") / 100
        unit, dp = "GBP", 2
        method = "Apply the higher-band marginal rate to the additional taxable income; do not tax the whole income again."
    elif kind == "public_spending_pie_table":
        value, unit = c(1, 1, "%") - c(2, 1, "%"), "percentage points"
        method = "Subtract education's spending share from health's share."
    else:
        value, unit = v[-1] - v[0], "percentage points"
        method = (
            "Subtract the first quarter's growth rate from the final quarter's rate."
        )
    output = NumericOutput(
        role=role,
        unit=unit,
        decimal_places=dp,
        scheme_pattern=rf"^{re.escape(calculation_label(source, marks))}:\s*(?P<value>[−+\-]?£?{NUMBER})",
    )
    return numeric_result({role: value}, [output], [method])


def solve_economics_contract(item: dict) -> dict | None:
    contract = (item.get("authoring_context") or {}).get("economics_input_contract")
    if contract is None:
        return None
    source = EconomicsSource.model_validate(contract["source"])
    if contract.get("source_fingerprint") != source.fingerprint():
        raise ValueError("Edexcel numeric source fingerprint mismatch")
    if (
        item.get("prompt") != contract.get("requested_prompt")
        or item.get("marks") != contract.get("marks")
        or item.get("prompt") != calculation_prompt(source, int(item["marks"]))
    ):
        raise ValueError("Edexcel numeric request changed")
    stimulus = item.get("stimulus", {})
    if (
        stimulus.get("values") != [float(v) for v in source.values]
        or stimulus.get("point_labels") != source.labels
        or stimulus.get("rows")
        != [[cell.printed() for cell in row] for row in source.rows]
        or stimulus.get("source_text") != source.context
        or stimulus.get("unit") != source.unit
        or stimulus.get("givens")
        != {name: cell.printed() for name, cell in source.givens.items()}
    ):
        raise ValueError("Edexcel candidate source differs from the numeric contract")
    if item.get("command_word", "").casefold() != "calculate":
        raise ValueError("Edexcel numeric contract has a different requested operation")
    return calculation(source, int(item["marks"]))
