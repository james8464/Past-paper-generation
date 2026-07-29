from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinancialPosition:
    """The single source of truth for Paper 1 financial-statement figures."""

    inventories: int
    receivables: int
    cash: int
    payables: int
    non_current_assets: int
    non_current_liabilities: int
    total_equity: int

    @classmethod
    def from_chart_values(cls, chart_values: list[float]) -> FinancialPosition:
        if len(chart_values) < 5:
            raise ValueError("financial-position data requires five chart values")
        values = [int(round(value)) for value in chart_values]
        return cls(
            inventories=values[0],
            receivables=int(values[1] * 0.42),
            cash=int(values[2] * 0.35),
            payables=int(values[3] * 0.66),
            non_current_assets=int(values[4] * 3.35),
            non_current_liabilities=int(values[2] * 2.3),
            total_equity=int(values[1] * 1.9),
        )

    @property
    def current_assets(self) -> int:
        return self.inventories + self.receivables + self.cash

    @property
    def net_current_assets(self) -> int:
        return self.current_assets - self.payables

    @property
    def current_ratio(self) -> float:
        return self.current_assets / self.payables

    @property
    def capital_employed(self) -> int:
        return self.total_equity + self.non_current_liabilities

    @property
    def operating_profit_at_twelve_percent(self) -> float:
        return self.capital_employed * 0.12


def format_number(value: float) -> str:
    """Format an exam answer without meaningless trailing zeroes."""

    return f"{value:.2f}".rstrip("0").rstrip(".")
