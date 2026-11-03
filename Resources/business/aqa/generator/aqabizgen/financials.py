from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite

from Backend.Core.numeric_integrity import rounded


# Shared Paper 1 financial-statement figures.
@dataclass(frozen=True)
class FinancialPosition:
    inventories: int
    receivables: int
    cash: int
    payables: int
    non_current_assets: int
    non_current_liabilities: int
    total_equity: int

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, int) and not isfinite(value)
            for value in (
                self.inventories,
                self.receivables,
                self.cash,
                self.payables,
                self.non_current_assets,
                self.non_current_liabilities,
                self.total_equity,
            )
        ):
            raise ValueError("financial-position amounts must be finite")
        if any(
            value < 0
            for value in (
                self.inventories,
                self.receivables,
                self.cash,
                self.payables,
                self.non_current_assets,
                self.non_current_liabilities,
            )
        ):
            raise ValueError("asset and liability amounts must be non-negative")
        if self.total_assets != self.total_liabilities_and_equity:
            raise ValueError("statement of financial position must balance")

    @classmethod
    def from_chart_values(cls, chart_values: list[float]) -> FinancialPosition:
        if len(chart_values) < 5:
            raise ValueError("financial-position data requires five chart values")
        if any(not isfinite(value) for value in chart_values):
            raise ValueError("financial-position source values must be finite")
        if any(value < 0 for value in chart_values):
            raise ValueError("financial-position source values must be non-negative")
        values = [round(value) for value in chart_values]
        inventories = values[0]
        receivables = int(values[1] * 0.42)
        cash = int(values[2] * 0.35)
        payables = int(values[3] * 0.66)
        non_current_assets = int(values[4] * 3.35)
        non_current_liabilities = int(values[2] * 2.3)
        total_equity = (
            inventories
            + receivables
            + cash
            + non_current_assets
            - payables
            - non_current_liabilities
        )
        return cls(
            inventories=inventories,
            receivables=receivables,
            cash=cash,
            payables=payables,
            non_current_assets=non_current_assets,
            non_current_liabilities=non_current_liabilities,
            total_equity=total_equity,
        )

    @property
    def current_assets(self) -> int:
        return self.inventories + self.receivables + self.cash

    @property
    def total_assets(self) -> int:
        return self.current_assets + self.non_current_assets

    @property
    def total_liabilities_and_equity(self) -> int:
        return self.payables + self.non_current_liabilities + self.total_equity

    @property
    def net_current_assets(self) -> int:
        return self.current_assets - self.payables

    @property
    def current_ratio(self) -> float:
        if self.payables == 0:
            raise ValueError("current ratio requires positive current liabilities")
        return self.current_assets / self.payables

    @property
    def capital_employed(self) -> int:
        return self.total_equity + self.non_current_liabilities

    @property
    def operating_profit_at_twelve_percent(self) -> float:
        return self.capital_employed * 0.12


# Format an exam answer without meaningless trailing zeroes.
def format_number(value: float) -> str:
    result = rounded(Decimal(str(value)), 2)
    return f"{result:.2f}".rstrip("0").rstrip(".") if result else "0"
