from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal


def _nearest_hundred(value: float) -> int:
    return int(round(value / 100.0) * 100)


def _gbp(value: int) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}£{abs(value):,}"


def _round_pounds(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class AccountingSystemCase:
    """Candidate-visible source for the bookkeeping-system decision."""

    business: str
    annual_bookkeeper_salary: int
    annual_software_cost: int
    initial_training_cost: int
    annual_accountant_fee: int
    estimated_lost_profit: int

    @classmethod
    def from_chart_values(
        cls, business: str, values: list[float]
    ) -> AccountingSystemCase:
        if len(values) != 5:
            raise ValueError("accounting-system case requires five chart values")
        scaled = [round(value * 1_000) for value in values]
        return cls(
            business=business,
            annual_bookkeeper_salary=int(scaled[0] * 0.32),
            annual_software_cost=int(scaled[1] * 0.24),
            initial_training_cost=int(scaled[2] * 0.09),
            annual_accountant_fee=int(scaled[3] * 0.08),
            estimated_lost_profit=int(scaled[4] * 0.14),
        )

    @classmethod
    def from_candidate_source(
        cls, source: dict[str, object]
    ) -> AccountingSystemCase:
        costs = dict(source["costs"])
        return cls(
            business=str(source["business"]),
            annual_bookkeeper_salary=int(costs["annual_bookkeeper_salary"]),
            annual_software_cost=int(costs["annual_software_cost"]),
            initial_training_cost=int(costs["initial_training_cost"]),
            annual_accountant_fee=int(costs["annual_accountant_fee"]),
            estimated_lost_profit=int(costs["estimated_lost_profit"]),
        )

    def candidate_source(self) -> dict[str, object]:
        return {
            "business": self.business,
            "source_type": "accounting_system_decision_case",
            "units": "GBP per year unless described as initial",
            "costs": {
                "annual_bookkeeper_salary": self.annual_bookkeeper_salary,
                "annual_software_cost": self.annual_software_cost,
                "initial_training_cost": self.initial_training_cost,
                "annual_accountant_fee": self.annual_accountant_fee,
                "estimated_lost_profit": self.estimated_lost_profit,
            },
            "current_system": [
                "The owner spends two days each week recording transactions, preparing customer statements and following up late payments.",
                "The latest trial balance contained errors and the year-end accounts were delayed.",
                "Inventory records do not agree with the physical count and monthly bank reconciliations are several weeks in arrears.",
                "The owner cannot determine the profit earned on individual contracts.",
            ],
            "bookkeeper_option": [
                "A qualified bookkeeper would use double-entry records and prepare draft financial statements.",
                "The owner expects improved credit control, monthly management information and more time to develop the business.",
            ],
            "software_option": [
                "Cloud software would automate bank reconciliation and invoicing.",
                "The external accountant would introduce the system and provide quarterly management information.",
                "The owner is concerned about data security, subscription increases and unreliable internet access.",
            ],
            "implementation_evidence": [
                "Two family members work in the business but neither has formal accounting training.",
                "One family member opposes changing familiar procedures.",
            ],
        }

    def authoring_context(self) -> dict[str, object]:
        source = self.candidate_source()
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Advise the owner which accounting-record system to adopt using all "
                "published costs, control weaknesses, benefits and implementation risks."
            ),
            "required_prompt_terms": ["accounting records", "owner"],
            "candidate_source": source,
            "source_data": source,
        }

    def mark_scheme_points(self) -> list[str]:
        return [
            (
                f"AO2: Compare the annual bookkeeper salary of {_gbp(self.annual_bookkeeper_salary)} "
                f"with annual software cost of {_gbp(self.annual_software_cost)}, initial "
                f"training of {_gbp(self.initial_training_cost)} and the current accountant "
                f"fee of {_gbp(self.annual_accountant_fee)}."
            ),
            (
                f"AO2: Apply the estimated lost profit of {_gbp(self.estimated_lost_profit)} "
                "and the stated record, reconciliation and credit-control weaknesses."
            ),
            "AO3: Develop how a bookkeeper could improve double entry, credit control and timely management information, while creating a recurring employment cost and dependence on one employee.",
            "AO3: Develop how cloud automation could improve invoicing and bank reconciliation at lower annual cost, while training, cyber security, subscription and internet risks may reduce the benefit.",
            "AO3: Compare both options with continuing the current system, including the owner's time and the cost of recurring errors and delayed decisions.",
            "AO3: Reach a justified, conditional recommendation linked to cost, control quality, staff capability and implementation risk; do not recommend solely on the lowest stated cost.",
        ]


@dataclass(frozen=True)
class CostingCase:
    units_sold: int
    selling_price_per_unit: int
    variable_cost_per_unit: int
    fixed_cost: int

    @classmethod
    def from_chart_values(cls, values: list[float]) -> CostingCase:
        if len(values) != 5:
            raise ValueError("costing case requires five chart values")
        variable_cost_per_unit = max(4, round(values[2] / 15))
        return cls(
            units_sold=int(values[4] * 1_000),
            selling_price_per_unit=(
                variable_cost_per_unit + max(4, round(values[0] / 20))
            ),
            variable_cost_per_unit=variable_cost_per_unit,
            fixed_cost=int(values[1] * 2_000),
        )

    @property
    def contribution_per_unit(self) -> int:
        return self.selling_price_per_unit - self.variable_cost_per_unit

    @property
    def contribution(self) -> int:
        return self.units_sold * self.contribution_per_unit

    @property
    def profit(self) -> int:
        return self.contribution - self.fixed_cost

    def authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "required_prompt_terms": [
                "units",
                "selling price",
                "variable cost",
                "fixed cost",
            ],
            "source_data": {
                "units_sold": self.units_sold,
                "selling_price_per_unit": self.selling_price_per_unit,
                "variable_cost_per_unit": self.variable_cost_per_unit,
                "fixed_cost": self.fixed_cost,
            },
            "verified_answers": {
                "contribution_per_unit": self.contribution_per_unit,
                "contribution": self.contribution,
                "profit": self.profit,
            },
        }


@dataclass(frozen=True)
class ShareholderCase:
    """Candidate-visible source contract for the Paper 1 shareholder decision."""

    business: str
    nominal_share_value_pence: int
    opening_ordinary_shares: int
    bonus_shares_issued: int
    opening_share_premium_thousands: int
    opening_retained_earnings_thousands: int
    revaluation_reserve_increase_thousands: int
    profit_for_year_thousands: int
    dividends_paid_thousands: int
    share_price_start_pence: int
    share_price_end_pence: int
    long_term_borrowings_thousands: int
    comparator_name: str
    comparator_share_price_pence: int
    comparator_earnings_per_share_pence: float
    comparator_dividend_per_share_pence: float
    comparator_long_term_borrowings_thousands: int
    comparator_total_equity_thousands: int

    @classmethod
    def from_chart_values(
        cls,
        business: str,
        values: list[float],
    ) -> ShareholderCase:
        if len(values) != 5:
            raise ValueError("shareholder case requires five chart values")
        nominal_value = 50
        opening_shares = (round(values[4]) * 50_000 // 5) * 5
        bonus_shares = opening_shares // 5
        bonus_capital = bonus_shares * nominal_value // 100_000
        profit = round(values[3]) * 12
        closing_shares = opening_shares + bonus_shares
        dividends = closing_shares * 4 // 100_000
        share_price_end = round(values[4] * 1.15)
        comparator_price = max(80, round(share_price_end * 0.95))
        return cls(
            business=business,
            nominal_share_value_pence=nominal_value,
            opening_ordinary_shares=opening_shares,
            bonus_shares_issued=bonus_shares,
            opening_share_premium_thousands=bonus_capital + round(values[1] * 9),
            opening_retained_earnings_thousands=round(values[3] * 35),
            revaluation_reserve_increase_thousands=round(values[0] * 6),
            profit_for_year_thousands=profit,
            dividends_paid_thousands=dividends,
            share_price_start_pence=round(values[0] * 1.25),
            share_price_end_pence=share_price_end,
            long_term_borrowings_thousands=round(values[2] * 35),
            comparator_name="Northbridge plc",
            comparator_share_price_pence=comparator_price,
            comparator_earnings_per_share_pence=round(comparator_price / 6.5, 1),
            comparator_dividend_per_share_pence=5.0,
            comparator_long_term_borrowings_thousands=round(values[2] * 23),
            comparator_total_equity_thousands=round(values[3] * 78),
        )

    @classmethod
    def from_candidate_source(cls, source: dict[str, object]) -> ShareholderCase:
        """Rehydrate the renderer's case only from the published source data."""

        equity = dict(source["statement_of_changes_in_equity"])
        market = dict(source["market_data"])
        comparator = dict(source["comparator"])
        return cls(
            business=str(source["business"]),
            nominal_share_value_pence=int(source["nominal_share_value_pence"]),
            opening_ordinary_shares=int(source["opening_ordinary_shares"]),
            bonus_shares_issued=int(source["bonus_shares_issued"]),
            opening_share_premium_thousands=int(equity["opening_share_premium"]),
            opening_retained_earnings_thousands=int(equity["opening_retained_earnings"]),
            revaluation_reserve_increase_thousands=int(equity["revaluation_increase"]),
            profit_for_year_thousands=int(equity["profit_for_year"]),
            dividends_paid_thousands=int(equity["dividends_paid"]),
            share_price_start_pence=int(market["share_price_start"]),
            share_price_end_pence=int(market["share_price_end"]),
            long_term_borrowings_thousands=int(source["long_term_borrowings"]),
            comparator_name=str(comparator["name"]),
            comparator_share_price_pence=int(comparator["share_price"]),
            comparator_earnings_per_share_pence=float(comparator["earnings_per_share"]),
            comparator_dividend_per_share_pence=float(comparator["dividend_per_share"]),
            comparator_long_term_borrowings_thousands=int(comparator["long_term_borrowings"]),
            comparator_total_equity_thousands=int(comparator["total_equity"]),
        )

    @property
    def closing_ordinary_shares(self) -> int:
        return self.opening_ordinary_shares + self.bonus_shares_issued

    @property
    def ordinary_share_capital_opening_thousands(self) -> int:
        return self.opening_ordinary_shares * self.nominal_share_value_pence // 100_000

    @property
    def bonus_issue_capital_thousands(self) -> int:
        return self.bonus_shares_issued * self.nominal_share_value_pence // 100_000

    @property
    def ordinary_share_capital_closing_thousands(self) -> int:
        return self.ordinary_share_capital_opening_thousands + self.bonus_issue_capital_thousands

    @property
    def share_premium_closing_thousands(self) -> int:
        return self.opening_share_premium_thousands - self.bonus_issue_capital_thousands

    @property
    def retained_earnings_closing_thousands(self) -> int:
        return (
            self.opening_retained_earnings_thousands
            + self.profit_for_year_thousands
            - self.dividends_paid_thousands
        )

    @property
    def total_equity_closing_thousands(self) -> int:
        return (
            self.ordinary_share_capital_closing_thousands
            + self.share_premium_closing_thousands
            + self.revaluation_reserve_increase_thousands
            + self.retained_earnings_closing_thousands
        )

    @property
    def earnings_per_share_pence(self) -> float:
        return round(
            self.profit_for_year_thousands * 100_000 / self.closing_ordinary_shares,
            1,
        )

    @property
    def dividend_per_share_pence(self) -> float:
        return round(
            self.dividends_paid_thousands * 100_000 / self.closing_ordinary_shares,
            1,
        )

    @property
    def price_earnings_ratio(self) -> float:
        return round(self.share_price_end_pence / self.earnings_per_share_pence, 1)

    @property
    def dividend_yield_percent(self) -> float:
        return round(
            self.dividend_per_share_pence / self.share_price_end_pence * 100,
            1,
        )

    @property
    def gearing_percent(self) -> float:
        return round(
            self.long_term_borrowings_thousands
            / (self.long_term_borrowings_thousands + self.total_equity_closing_thousands)
            * 100,
            1,
        )

    @property
    def comparator_price_earnings_ratio(self) -> float:
        return round(
            self.comparator_share_price_pence / self.comparator_earnings_per_share_pence,
            1,
        )

    @property
    def comparator_dividend_yield_percent(self) -> float:
        return round(
            self.comparator_dividend_per_share_pence
            / self.comparator_share_price_pence
            * 100,
            1,
        )

    @property
    def comparator_gearing_percent(self) -> float:
        return round(
            self.comparator_long_term_borrowings_thousands
            / (
                self.comparator_long_term_borrowings_thousands
                + self.comparator_total_equity_thousands
            )
            * 100,
            1,
        )

    def candidate_source(self) -> dict[str, object]:
        """Return only facts and units printed on the candidate source page."""

        return {
            "business": self.business,
            "source_type": "shareholder_investor_case",
            "units": {
                "ordinary_shares": "number of shares",
                "nominal_share_value": "pence per ordinary share",
                "market_data": "pence per ordinary share",
                "equity_statement": "£000",
                "borrowings": "£000",
            },
            "nominal_share_value_pence": self.nominal_share_value_pence,
            "opening_ordinary_shares": self.opening_ordinary_shares,
            "bonus_shares_issued": self.bonus_shares_issued,
            "market_data": {
                "share_price_start": self.share_price_start_pence,
                "share_price_end": self.share_price_end_pence,
                "earnings_per_share": self.earnings_per_share_pence,
                "dividend_per_share": self.dividend_per_share_pence,
            },
            "statement_of_changes_in_equity": {
                "opening_ordinary_share_capital": self.ordinary_share_capital_opening_thousands,
                "opening_share_premium": self.opening_share_premium_thousands,
                "opening_retained_earnings": self.opening_retained_earnings_thousands,
                "revaluation_increase": self.revaluation_reserve_increase_thousands,
                "bonus_issue_capital_transfer": self.bonus_issue_capital_thousands,
                "profit_for_year": self.profit_for_year_thousands,
                "dividends_paid": self.dividends_paid_thousands,
                "closing_ordinary_share_capital": self.ordinary_share_capital_closing_thousands,
                "closing_share_premium": self.share_premium_closing_thousands,
                "closing_retained_earnings": self.retained_earnings_closing_thousands,
            },
            "long_term_borrowings": self.long_term_borrowings_thousands,
            "comparator": {
                "name": self.comparator_name,
                "share_price": self.comparator_share_price_pence,
                "earnings_per_share": self.comparator_earnings_per_share_pence,
                "dividend_per_share": self.comparator_dividend_per_share_pence,
                "long_term_borrowings": self.comparator_long_term_borrowings_thousands,
                "total_equity": self.comparator_total_equity_thousands,
            },
            "qualitative_evidence": [
                "New production equipment increases capacity but demand for the expansion is uncertain.",
                "The equipment is expected to reduce energy use, but higher interest rates could increase finance costs.",
                "Directors plan to retain more profit to support the expansion.",
            ],
        }

    def authoring_context(self) -> dict[str, object]:
        return {
            "preserve_mark_scheme": True,
            "task_scope": (
                "Advise an investor whether to retain or sell shares using the complete "
                "published shareholder source, comparator data and uncertainty."
            ),
            "required_prompt_terms": ["shares", "investor"],
            "candidate_source": self.candidate_source(),
            "source_data": self.candidate_source(),
        }

    def mark_scheme_points(self) -> list[str]:
        return [
            (
                f"AO2: Apply the share-price movement from {self.share_price_start_pence}p to "
                f"{self.share_price_end_pence}p and what it may indicate about investor confidence."
            ),
            (
                f"AO2: Calculate and interpret the price earnings ratio: {self.share_price_end_pence}p ÷ "
                f"{self.earnings_per_share_pence:.1f}p = {self.price_earnings_ratio:.1f} times."
            ),
            (
                f"AO2: Calculate and interpret dividend yield: {self.dividend_per_share_pence:.1f}p ÷ "
                f"{self.share_price_end_pence}p × 100 = {self.dividend_yield_percent:.1f}%."
            ),
            (
                f"AO2: Calculate gearing from published long-term borrowings and closing equity: "
                f"£{self.long_term_borrowings_thousands * 1_000:,} ÷ "
                f"(£{self.long_term_borrowings_thousands * 1_000:,} + "
                f"£{self.total_equity_closing_thousands * 1_000:,}) "
                f"× 100 = {self.gearing_percent:.1f}%."
            ),
            (
                f"AO3: Compare with {self.comparator_name}: price earnings ratio "
                f"{self.comparator_price_earnings_ratio:.1f} times, dividend yield "
                f"{self.comparator_dividend_yield_percent:.1f}% and gearing "
                f"{self.comparator_gearing_percent:.1f}%; explain the trade-off for the investor."
            ),
            "AO3: Develop whether retaining profit can finance growth and reduce future share issues, while reducing current shareholder income.",
            "AO3: Develop the risk that uncertain demand or higher interest rates could prevent the new capacity improving returns, despite lower energy use.",
            "AO3: Reach a balanced, conditional judgement linked to the investor's income, growth and risk priorities; do not treat one ratio as decisive.",
        ]


@dataclass(frozen=True)
class IncomeStatementCase:
    """Complete, internally consistent source for the Paper 1 company statement."""

    business: str
    administration_expenses: int
    cost_of_sales: int
    marketing_expenses: int
    revenue: int
    warehouse_expenses: int
    damaged_inventory_cost: int
    damaged_inventory_sale_proceeds: int
    damaged_inventory_repair_cost: int
    roof_repair: int
    insurance_claim: int
    trade_receivable: int
    supplier_invoice: int
    new_debenture: int
    earlier_debenture: int

    @classmethod
    def from_chart_values(
        cls,
        business: str,
        values: list[float],
    ) -> IncomeStatementCase:
        if len(values) != 5:
            raise ValueError("income-statement case requires five chart values")
        damaged_cost = int(values[0] * 760)
        roof_repair = int(values[1] * 84)
        return cls(
            business=business,
            administration_expenses=int(values[0] * 4_000),
            cost_of_sales=int(values[4] * 34_000),
            marketing_expenses=int(values[1] * 8_000),
            revenue=int(values[4] * 72_000),
            warehouse_expenses=int(values[2] * 9_000),
            damaged_inventory_cost=damaged_cost,
            damaged_inventory_sale_proceeds=int(damaged_cost * 0.72),
            damaged_inventory_repair_cost=int(damaged_cost * 0.14),
            roof_repair=roof_repair,
            insurance_claim=int(roof_repair * 0.88),
            trade_receivable=int(values[4] * 1_980),
            supplier_invoice=int(values[2] * 31),
            new_debenture=int(values[4] * 21_000),
            earlier_debenture=int(values[3] * 13_000),
        )

    @property
    def inventory_write_down(self) -> int:
        net_realisable_value = (
            self.damaged_inventory_sale_proceeds
            - self.damaged_inventory_repair_cost
        )
        return max(0, self.damaged_inventory_cost - net_realisable_value)

    @property
    def irrecoverable_debt(self) -> int:
        return _round_pounds(Decimal(self.trade_receivable) * 90 / 100)

    @property
    def adjusted_cost_of_sales(self) -> int:
        return self.cost_of_sales + self.inventory_write_down

    @property
    def adjusted_administration_expenses(self) -> int:
        return self.administration_expenses + self.irrecoverable_debt

    @property
    def adjusted_marketing_expenses(self) -> int:
        return self.marketing_expenses + self.supplier_invoice

    @property
    def new_debenture_interest(self) -> int:
        return _round_pounds(Decimal(self.new_debenture) * 6 / 100 * 4 / 12)

    @property
    def earlier_debenture_interest(self) -> int:
        return _round_pounds(Decimal(self.earlier_debenture) * 8 / 100 * 10 / 12)

    @property
    def finance_cost(self) -> int:
        return self.new_debenture_interest + self.earlier_debenture_interest

    @property
    def profit_before_tax(self) -> int:
        return (
            self.revenue
            - self.adjusted_cost_of_sales
            - self.adjusted_administration_expenses
            - self.adjusted_marketing_expenses
            - self.warehouse_expenses
            + self.insurance_claim
            - self.finance_cost
        )

    @property
    def current_tax_charge(self) -> int:
        return max(0, _round_pounds(Decimal(self.profit_before_tax) * 19 / 100))

    @property
    def profit_for_year(self) -> int:
        return self.profit_before_tax - self.current_tax_charge

    def mark_scheme_points(self) -> list[str]:
        """Return one exact, independently checkable award point per mark."""
        gross_profit = self.revenue - self.adjusted_cost_of_sales
        new_interest = self.new_debenture_interest
        earlier_interest = self.earlier_debenture_interest
        return [
            f"Revenue: {_gbp(self.revenue)}.",
            (
                "Damaged inventory write-down: "
                f"{_gbp(self.damaged_inventory_cost)} − "
                f"({_gbp(self.damaged_inventory_sale_proceeds)} − "
                f"{_gbp(self.damaged_inventory_repair_cost)}) = "
                f"{_gbp(self.inventory_write_down)}."
            ),
            (
                f"Adjusted cost of sales: {_gbp(self.cost_of_sales)} + "
                f"{_gbp(self.inventory_write_down)} = "
                f"{_gbp(self.adjusted_cost_of_sales)}."
            ),
            (
                f"Gross profit: {_gbp(self.revenue)} − "
                f"{_gbp(self.adjusted_cost_of_sales)} = {_gbp(gross_profit)}."
            ),
            (
                f"Irrecoverable debt: 90% × {_gbp(self.trade_receivable)} = "
                f"{_gbp(self.irrecoverable_debt)}."
            ),
            (
                f"Administration expenses: {_gbp(self.administration_expenses)} + "
                f"{_gbp(self.irrecoverable_debt)} = "
                f"{_gbp(self.adjusted_administration_expenses)}."
            ),
            f"Accrue the supplier invoice of {_gbp(self.supplier_invoice)}.",
            (
                f"Marketing expenses: {_gbp(self.marketing_expenses)} + "
                f"{_gbp(self.supplier_invoice)} = "
                f"{_gbp(self.adjusted_marketing_expenses)}."
            ),
            f"Warehouse expenses: {_gbp(self.warehouse_expenses)}.",
            (
                f"Other income — insurance claim: {_gbp(self.insurance_claim)}. "
                f"The roof repair of {_gbp(self.roof_repair)} is already included "
                "in warehouse expenses."
            ),
            (
                f"Debenture interest: {_gbp(self.new_debenture)} × 6% × 4/12 "
                f"= {_gbp(new_interest)} and {_gbp(self.earlier_debenture)} × "
                f"8% × 10/12 = {_gbp(earlier_interest)}."
            ),
            f"Total finance cost: {_gbp(self.finance_cost)}.",
            f"Profit before tax: {_gbp(self.profit_before_tax)}.",
            (
                f"Supplied taxation charge: {_gbp(self.current_tax_charge)}; "
                "final profit for the year: "
                f"{_gbp(self.profit_for_year)}."
            ),
        ]

    def authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare only the income statement for the year ended from the "
                "supplied trial-balance amounts and adjustments."
            ),
            "required_prompt_terms": ["income statement"],
            "source_data": {
                "administration_expenses": self.administration_expenses,
                "cost_of_sales": self.cost_of_sales,
                "marketing_expenses": self.marketing_expenses,
                "revenue": self.revenue,
                "warehouse_expenses": self.warehouse_expenses,
            },
            "adjustment_source_data": {
                "damaged_inventory_cost": self.damaged_inventory_cost,
                "damaged_inventory_sale_proceeds": (
                    self.damaged_inventory_sale_proceeds
                ),
                "damaged_inventory_repair_cost": self.damaged_inventory_repair_cost,
                "roof_repair": self.roof_repair,
                "insurance_claim": self.insurance_claim,
                "trade_receivable": self.trade_receivable,
                "supplier_invoice": self.supplier_invoice,
                "new_debenture": self.new_debenture,
                "earlier_debenture": self.earlier_debenture,
                "current_tax_charge": self.current_tax_charge,
            },
            "adjustment_policy": {
                "irrecoverable_debt_percent": 90,
                "new_debenture_rate_percent": 6,
                "new_debenture_months": 4,
                "earlier_debenture_rate_percent": 8,
                "earlier_debenture_months": 10,
                "round_each_adjustment_to_nearest_pound": True,
            },
            "adjustments": {
                "inventory_write_down": self.inventory_write_down,
                "irrecoverable_debt": self.irrecoverable_debt,
                "supplier_invoice_accrual": self.supplier_invoice,
                "insurance_claim_other_income": self.insurance_claim,
                "finance_cost": self.finance_cost,
                "current_tax_charge": self.current_tax_charge,
            },
            "verified_answers": {
                "revenue": self.revenue,
                "adjusted_cost_of_sales": self.adjusted_cost_of_sales,
                "adjusted_administration_expenses": (
                    self.adjusted_administration_expenses
                ),
                "adjusted_marketing_expenses": self.adjusted_marketing_expenses,
                "profit_before_tax": self.profit_before_tax,
                "profit_for_year": self.profit_for_year,
            },
            "observable_mark_points": self.mark_scheme_points(),
        }


@dataclass(frozen=True)
class PartnershipCase:
    """Complete retirement and appropriation data for Paper 1 Question 15."""

    opening_capital: dict[str, int]
    goodwill: int
    target_capital: dict[str, int]
    profit_for_year: int
    period_months: tuple[int, int] = (8, 4)
    partner_salary_per_year: int = 12_000
    capital_interest_rate_percent: int = 6
    first_period_drawings_interest: dict[str, int] | None = None
    second_period_drawings_interest: dict[str, int] | None = None

    @classmethod
    def from_chart_values(cls, values: list[float]) -> PartnershipCase:
        if len(values) != 5:
            raise ValueError("partnership case requires five chart values")
        opening = {
            "Alex": _nearest_hundred(values[0] * 210),
            "Morgan": _nearest_hundred(values[1] * 210),
            "Riley": _nearest_hundred(values[2] * 210),
        }
        # Divisibility by both profit-sharing ratios keeps the goodwill
        # accounts exact in whole pounds.
        goodwill = round(values[4]) * 300
        goodwill_credit = {
            "Alex": goodwill * 3 // 6,
            "Morgan": goodwill * 2 // 6,
            "Riley": goodwill // 6,
        }
        goodwill_write_off = {
            "Alex": goodwill * 3 // 5,
            "Morgan": goodwill * 2 // 5,
        }
        adjusted = {
            partner: opening[partner]
            + goodwill_credit[partner]
            - goodwill_write_off[partner]
            for partner in ("Alex", "Morgan")
        }
        target = {
            partner: _nearest_hundred(amount * 0.8)
            for partner, amount in adjusted.items()
        }
        case = cls(
            opening_capital=opening,
            goodwill=goodwill,
            target_capital=target,
            profit_for_year=int(round(values[4] * 1_000 / 1_200) * 1_200),
            first_period_drawings_interest={"Alex": 140, "Morgan": 130, "Riley": 150},
            second_period_drawings_interest={"Alex": 10, "Morgan": 14},
        )
        # Keep both residual-profit allocations exact rather than silently
        # losing a pound by truncating each partner's share.
        for offset in sorted(range(-45, 46, 3), key=abs):
            candidate = replace(case, profit_for_year=case.profit_for_year + offset)
            periods = candidate.appropriation_by_period()
            if (
                periods["first_period"]["residual_profit"] % 6 == 0
                and periods["second_period"]["residual_profit"] % 5 == 0
            ):
                return candidate
        raise ValueError("could not construct exact partnership profit shares")

    @property
    def old_profit_sharing_ratio(self) -> dict[str, int]:
        return {"Alex": 3, "Morgan": 2, "Riley": 1}

    @property
    def new_profit_sharing_ratio(self) -> dict[str, int]:
        return {"Alex": 3, "Morgan": 2}

    @property
    def goodwill_credit(self) -> dict[str, int]:
        return {
            partner: self.goodwill * share // 6
            for partner, share in self.old_profit_sharing_ratio.items()
        }

    @property
    def goodwill_write_off(self) -> dict[str, int]:
        return {
            partner: self.goodwill * share // 5
            for partner, share in self.new_profit_sharing_ratio.items()
        }

    @property
    def cash_withdrawn(self) -> dict[str, int]:
        return {
            partner: self.opening_capital[partner]
            + self.goodwill_credit[partner]
            - self.goodwill_write_off[partner]
            - self.target_capital[partner]
            for partner in self.new_profit_sharing_ratio
        }

    @property
    def period_profit(self) -> list[int]:
        return [
            self.profit_for_year * months // 12
            for months in self.period_months
        ]

    def _capital_interest(self, period_index: int) -> dict[str, int]:
        months = self.period_months[period_index]
        capitals = self.opening_capital if period_index == 0 else self.target_capital
        partners = (
            self.old_profit_sharing_ratio
            if period_index == 0
            else self.new_profit_sharing_ratio
        )
        return {
            partner: capitals[partner]
            * self.capital_interest_rate_percent
            // 100
            * months
            // 12
            for partner in partners
        }

    def appropriation_by_period(self) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        drawings = (
            self.first_period_drawings_interest or {},
            self.second_period_drawings_interest or {},
        )
        ratios = (self.old_profit_sharing_ratio, self.new_profit_sharing_ratio)
        for index, name in enumerate(("first_period", "second_period")):
            capital_interest = self._capital_interest(index)
            salary = self.partner_salary_per_year * self.period_months[index] // 12
            residual = (
                self.period_profit[index]
                + sum(drawings[index].values())
                - salary
                - sum(capital_interest.values())
            )
            ratio_total = sum(ratios[index].values())
            shares = {
                partner: residual * share // ratio_total
                for partner, share in ratios[index].items()
            }
            result[name] = {
                "profit": self.period_profit[index],
                "interest_on_drawings": drawings[index],
                "partner_salary": {"Morgan": salary},
                "interest_on_capital": capital_interest,
                "residual_profit": residual,
                "residual_profit_shares": shares,
            }
        return result

    def retirement_mark_scheme_points(self) -> list[str]:
        return [
            (
                "Opening capital balances: "
                f"Alex {_gbp(self.opening_capital['Alex'])}; "
                f"Morgan {_gbp(self.opening_capital['Morgan'])}."
            ),
            (
                f"Credit total goodwill of {_gbp(self.goodwill)} in the old "
                f"3:2:1 ratio: "
                f"Alex {_gbp(self.goodwill_credit['Alex'])}; "
                f"Morgan {_gbp(self.goodwill_credit['Morgan'])}."
            ),
            (
                "Write goodwill off in the new ratio: "
                f"Alex {_gbp(self.goodwill_write_off['Alex'])}; "
                f"Morgan {_gbp(self.goodwill_write_off['Morgan'])}."
            ),
            f"Record Alex's cash withdrawal of {_gbp(self.cash_withdrawn['Alex'])}.",
            f"Record Morgan's cash withdrawal of {_gbp(self.cash_withdrawn['Morgan'])}.",
            (
                "Closing capital balances: "
                f"Alex {_gbp(self.target_capital['Alex'])}; "
                f"Morgan {_gbp(self.target_capital['Morgan'])}."
            ),
        ]

    def appropriation_mark_scheme_points(self) -> list[str]:
        periods = self.appropriation_by_period()
        first = periods["first_period"]
        second = periods["second_period"]
        return [
            (
                f"Apportion annual profit of {_gbp(self.profit_for_year)} for "
                f"{self.period_months[0]} and {self.period_months[1]} months: "
                f"first period {_gbp(first['profit'])}; second period "
                f"{_gbp(second['profit'])}."
            ),
            (
                "Interest on drawings: first period "
                + ", ".join(
                    f"{partner} {_gbp(amount)}"
                    for partner, amount in first["interest_on_drawings"].items()
                )
                + f", total {_gbp(sum(first['interest_on_drawings'].values()))}; "
                + "second period "
                + ", ".join(
                    f"{partner} {_gbp(amount)}"
                    for partner, amount in second["interest_on_drawings"].items()
                )
                + f", total {_gbp(sum(second['interest_on_drawings'].values()))}."
            ),
            (
                f"First-period interest on capital at "
                f"{self.capital_interest_rate_percent}% for "
                f"{self.period_months[0]} months: "
                + "; ".join(
                    f"{partner} {_gbp(self.opening_capital[partner])} gives "
                    f"{_gbp(amount)}"
                    for partner, amount in first["interest_on_capital"].items()
                )
                + "."
            ),
            (
                f"Second-period interest on capital at "
                f"{self.capital_interest_rate_percent}% for "
                f"{self.period_months[1]} months: "
                + "; ".join(
                    f"{partner} {_gbp(self.target_capital[partner])} gives "
                    f"{_gbp(amount)}"
                    for partner, amount in second["interest_on_capital"].items()
                )
                + "."
            ),
            (
                f"Morgan's annual salary {_gbp(self.partner_salary_per_year)}: "
                f"first period {_gbp(first['partner_salary']['Morgan'])}; "
                f"second period {_gbp(second['partner_salary']['Morgan'])}."
            ),
            (
                "Residual profit: first period "
                f"{_gbp(first['residual_profit'])}; second period "
                f"{_gbp(second['residual_profit'])}."
            ),
            (
                "Alex's residual-profit share using 3:2:1 then 3:2: first period "
                f"{_gbp(first['residual_profit_shares']['Alex'])}; second period "
                f"{_gbp(second['residual_profit_shares']['Alex'])}."
            ),
            (
                "Morgan's residual-profit share using 3:2:1 then 3:2: first period "
                f"{_gbp(first['residual_profit_shares']['Morgan'])}; second period "
                f"{_gbp(second['residual_profit_shares']['Morgan'])}; Riley's "
                f"first-period share {_gbp(first['residual_profit_shares']['Riley'])}."
            ),
        ]

    def retirement_authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare Alex and Morgan's capital accounts after Riley retires, "
                "writing goodwill in and back out before the stated cash withdrawals."
            ),
            "required_prompt_terms": ["capital accounts"],
            "forbidden_prompt_terms": [
                "retiring partner's account",
                "retiring partner’s account",
                "written off against Riley",
                "written back out of Riley",
            ],
            "required_mark_scheme_terms": [
                "Alex",
                "Morgan",
                "goodwill",
                "withdraw",
                "closing",
            ],
            "forbidden_mark_scheme_terms": [
                "Riley's goodwill write-off",
                "retiring partner's goodwill write-off",
                "remove Riley's share",
            ],
            "source_data": {
                "opening_capital": self.opening_capital,
                "goodwill": self.goodwill,
                "old_profit_sharing_ratio": self.old_profit_sharing_ratio,
                "new_profit_sharing_ratio": self.new_profit_sharing_ratio,
                "target_capital": self.target_capital,
            },
            "verified_answers": {
                "goodwill_credit": self.goodwill_credit,
                "goodwill_write_off": self.goodwill_write_off,
                "cash_withdrawn": self.cash_withdrawn,
                "closing_capital": self.target_capital,
            },
            "observable_mark_points": self.retirement_mark_scheme_points(),
        }

    def appropriation_authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare the partnership profit and loss appropriation account "
                "for the two stated periods using only the supplied agreement data."
            ),
            "required_prompt_terms": ["appropriation account"],
            "required_mark_scheme_terms": [
                "first period",
                "second period",
                "interest on capital",
                "interest on drawings",
                "salary",
                "residual profit",
                "profit-sharing ratio",
            ],
            "source_data": {
                "period_months": list(self.period_months),
                "profit_for_year": self.profit_for_year,
                "profit_sharing_ratios": {
                    "first_period": self.old_profit_sharing_ratio,
                    "second_period": self.new_profit_sharing_ratio,
                },
                "capital_balances": {
                    "first_period": self.opening_capital,
                    "second_period": self.target_capital,
                },
                "partner_salary_per_year": {
                    "Morgan": self.partner_salary_per_year
                },
                "capital_interest_rate_percent": self.capital_interest_rate_percent,
                "interest_on_drawings": {
                    "first_period": self.first_period_drawings_interest,
                    "second_period": self.second_period_drawings_interest,
                },
            },
            "verified_answers": {
                "period_profit": self.period_profit,
                "appropriation_by_period": self.appropriation_by_period(),
            },
            "observable_mark_points": self.appropriation_mark_scheme_points(),
        }


@dataclass(frozen=True)
class NonCurrentAssetCase:
    business: str
    plant_cost_opening: int
    plant_accumulated_depreciation_opening: int
    plant_purchase: int
    motor_cost_opening: int
    motor_accumulated_depreciation_opening: int
    motor_disposal_cost: int
    motor_disposal_accumulated_depreciation: int
    plant_rate_percent: int = 10
    motor_rate_percent: int = 20

    @classmethod
    def from_chart_values(
        cls,
        business: str,
        values: list[float],
    ) -> NonCurrentAssetCase:
        if len(values) != 5:
            raise ValueError("non-current asset case requires five chart values")
        plant_cost = _nearest_hundred(values[4] * 1_000)
        motor_cost = _nearest_hundred(values[3] * 1_300)
        return cls(
            business=business,
            plant_cost_opening=plant_cost,
            plant_accumulated_depreciation_opening=_nearest_hundred(
                plant_cost * 0.30
            ),
            plant_purchase=_nearest_hundred(values[2] * 200),
            motor_cost_opening=motor_cost,
            motor_accumulated_depreciation_opening=_nearest_hundred(
                motor_cost * 0.35
            ),
            motor_disposal_cost=_nearest_hundred(values[1] * 180),
            motor_disposal_accumulated_depreciation=_nearest_hundred(
                values[1] * 180 * 0.60
            ),
        )

    @property
    def plant_cost_closing(self) -> int:
        return self.plant_cost_opening + self.plant_purchase

    @property
    def plant_depreciation_charge(self) -> int:
        return self.plant_cost_closing * self.plant_rate_percent // 100

    @property
    def plant_accumulated_depreciation_closing(self) -> int:
        return (
            self.plant_accumulated_depreciation_opening
            + self.plant_depreciation_charge
        )

    @property
    def plant_carrying_amount(self) -> int:
        return self.plant_cost_closing - self.plant_accumulated_depreciation_closing

    @property
    def motor_cost_closing(self) -> int:
        return self.motor_cost_opening - self.motor_disposal_cost

    @property
    def motor_accumulated_depreciation_before_charge(self) -> int:
        return (
            self.motor_accumulated_depreciation_opening
            - self.motor_disposal_accumulated_depreciation
        )

    @property
    def motor_depreciation_charge(self) -> int:
        carrying_amount = (
            self.motor_cost_closing
            - self.motor_accumulated_depreciation_before_charge
        )
        return carrying_amount * self.motor_rate_percent // 100

    @property
    def motor_accumulated_depreciation_closing(self) -> int:
        return (
            self.motor_accumulated_depreciation_before_charge
            + self.motor_depreciation_charge
        )

    @property
    def motor_carrying_amount(self) -> int:
        return self.motor_cost_closing - self.motor_accumulated_depreciation_closing

    @property
    def total_carrying_amount(self) -> int:
        return self.plant_carrying_amount + self.motor_carrying_amount

    def mark_scheme_points(self) -> list[str]:
        return [
            (
                f"Plant cost: {_gbp(self.plant_cost_opening)} + "
                f"{_gbp(self.plant_purchase)} = {_gbp(self.plant_cost_closing)}."
            ),
            (
                f"Plant depreciation: {_gbp(self.plant_cost_closing)} × "
                f"{self.plant_rate_percent}% = {_gbp(self.plant_depreciation_charge)}; "
                f"accumulated depreciation {_gbp(self.plant_accumulated_depreciation_opening)} "
                f"+ {_gbp(self.plant_depreciation_charge)} = "
                f"{_gbp(self.plant_accumulated_depreciation_closing)}."
            ),
            f"Plant and machinery carrying amount: {_gbp(self.plant_carrying_amount)}.",
            (
                f"Motor cost: {_gbp(self.motor_cost_opening)} − "
                f"{_gbp(self.motor_disposal_cost)} = {_gbp(self.motor_cost_closing)}; "
                f"accumulated depreciation {_gbp(self.motor_accumulated_depreciation_opening)} "
                f"− {_gbp(self.motor_disposal_accumulated_depreciation)} = "
                f"{_gbp(self.motor_accumulated_depreciation_before_charge)}."
            ),
            (
                f"Motor depreciation: ({_gbp(self.motor_cost_closing)} − "
                f"{_gbp(self.motor_accumulated_depreciation_before_charge)}) × "
                f"{self.motor_rate_percent}% = {_gbp(self.motor_depreciation_charge)}."
            ),
            (
                "Motor vehicles closing accumulated depreciation "
                f"{_gbp(self.motor_accumulated_depreciation_closing)} and carrying "
                f"amount {_gbp(self.motor_carrying_amount)}."
            ),
            f"Total non-current assets: {_gbp(self.total_carrying_amount)} (own figure).",
        ]

    def authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare only the non-current assets section of the statement of "
                "financial position and show supporting depreciation workings."
            ),
            "opening_balances": {
                "plant_and_machinery": {
                    "cost": self.plant_cost_opening,
                    "accumulated_depreciation": (
                        self.plant_accumulated_depreciation_opening
                    ),
                },
                "motor_vehicles": {
                    "cost": self.motor_cost_opening,
                    "accumulated_depreciation": (
                        self.motor_accumulated_depreciation_opening
                    ),
                },
            },
            "transactions_at_start_of_year": {
                "plant_purchase_cost": self.plant_purchase,
                "motor_disposal_cost": self.motor_disposal_cost,
                "motor_disposal_accumulated_depreciation": (
                    self.motor_disposal_accumulated_depreciation
                ),
            },
            "depreciation_policy": {
                "plant_straight_line_percent_on_cost": self.plant_rate_percent,
                "motor_reducing_balance_percent": self.motor_rate_percent,
                "full_year_on_purchases": True,
                "depreciation_on_disposals": False,
            },
            "verified_answers": {
                "plant_cost": self.plant_cost_closing,
                "plant_accumulated_depreciation": (
                    self.plant_accumulated_depreciation_closing
                ),
                "plant_carrying_amount": self.plant_carrying_amount,
                "motor_cost": self.motor_cost_closing,
                "motor_accumulated_depreciation": (
                    self.motor_accumulated_depreciation_closing
                ),
                "motor_carrying_amount": self.motor_carrying_amount,
                "total_carrying_amount": self.total_carrying_amount,
            },
            "observable_mark_points": self.mark_scheme_points(),
        }


@dataclass(frozen=True)
class SalesLedgerCase:
    """Single source of truth for the Paper 1 sales-ledger case.

    The question paper, AI authoring contract and mark scheme all consume this
    object so every amount remains present, sufficient and arithmetically
    consistent.
    """

    business: str
    opening_receivables: int
    credit_sales: int
    sales_returns: int
    cash_received: int
    discount_allowed: int

    @classmethod
    def from_chart_values(
        cls,
        business: str,
        values: list[float],
    ) -> SalesLedgerCase:
        if len(values) != 5:
            raise ValueError("sales-ledger case requires five chart values")
        credit_sales = _nearest_hundred(values[4] * 1_900)
        return cls(
            business=business,
            opening_receivables=_nearest_hundred(values[2] * 550),
            credit_sales=credit_sales,
            sales_returns=max(100, _nearest_hundred(values[0] * 6)),
            cash_received=_nearest_hundred(credit_sales * 0.86),
            discount_allowed=max(100, _nearest_hundred(credit_sales * 0.006)),
        )

    @property
    def closing_receivables(self) -> int:
        return (
            self.opening_receivables
            + self.credit_sales
            - self.sales_returns
            - self.cash_received
            - self.discount_allowed
        )

    @property
    def net_sales(self) -> int:
        return self.credit_sales - self.sales_returns

    def ledger_mark_scheme_points(self) -> list[str]:
        total = self.opening_receivables + self.credit_sales
        return [
            f"Debit opening trade receivables of {_gbp(self.opening_receivables)}.",
            f"Debit credit sales of {_gbp(self.credit_sales)}.",
            f"Credit bank with cash received of {_gbp(self.cash_received)}.",
            (
                f"Credit sales returns of {_gbp(self.sales_returns)} and discount "
                f"allowed of {_gbp(self.discount_allowed)}."
            ),
            (
                f"Balance the account at {_gbp(total)}; carry down and bring down "
                f"closing trade receivables of {_gbp(self.closing_receivables)}."
            ),
        ]

    def sales_account_mark_scheme_points(self) -> list[str]:
        return [
            f"Credit gross credit sales of {_gbp(self.credit_sales)}.",
            (
                f"Debit sales returns of {_gbp(self.sales_returns)} and transfer "
                f"net sales of {_gbp(self.net_sales)} to the income statement."
            ),
        ]

    def ledger_authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare and balance only the sales ledger control account from "
                "the supplied books-of-prime-entry data."
            ),
            "source_data": {
                "opening_trade_receivables": self.opening_receivables,
                "credit_sales": self.credit_sales,
                "sales_returns": self.sales_returns,
                "cash_received_from_credit_customers": self.cash_received,
                "discount_allowed": self.discount_allowed,
            },
            "required_entries": {
                "debit": ["opening trade receivables", "credit sales"],
                "credit": [
                    "cash received",
                    "sales returns",
                    "discount allowed",
                    "closing balance",
                ],
            },
            "verified_answers": {
                "closing_trade_receivables": self.closing_receivables,
                "next_period_opening_balance": self.closing_receivables,
            },
            "observable_mark_points": self.ledger_mark_scheme_points(),
        }

    def sales_account_authoring_context(self) -> dict[str, object]:
        return {
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
            "task_scope": (
                "Prepare only the sales account from the supplied sales and sales "
                "returns journals."
            ),
            "source_data": {
                "gross_credit_sales": self.credit_sales,
                "sales_returns": self.sales_returns,
            },
            "required_entries": {
                "debit": ["sales returns", "income statement transfer"],
                "credit": ["gross credit sales"],
            },
            "verified_answers": {
                "net_sales_transferred_to_income_statement": self.net_sales,
            },
            "observable_mark_points": self.sales_account_mark_scheme_points(),
        }
