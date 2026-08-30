from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any


def solve_accounting_calculation(item: dict[str, Any]) -> dict[str, Any] | None:
    """Recompute known closed accounting contracts from candidate-visible data.

    No renderer, draft mark scheme, or verified-answer field is consulted. The
    normal model content and difficulty reviews still run after this arithmetic
    pass. Unrecognised contracts remain on the general independent-solver path.
    """
    context = item.get("authoring_context")
    if not isinstance(context, dict) or not (
        context.get("preserve_prompt") is True
        and context.get("preserve_mark_scheme") is True
    ):
        return None
    solvers = {
        "statement_extract": (_assets, {"opening_balances", "depreciation_policy"}),
        "ledger_calculation": (_ledger, {"source_data", "required_entries"}),
        "accounting_concept": (_sales, {"source_data", "required_entries"}),
        "company_statement": (
            _income,
            {"source_data", "adjustment_source_data", "adjustment_policy"},
        ),
        "partnership_1": (_retirement, {"source_data", "task_scope"}),
        "partnership_2": (_appropriation, {"source_data", "task_scope"}),
    }
    entry = solvers.get(str(item.get("rule_id", "")))
    if entry is None or not entry[1].issubset(context):
        return None
    return entry[0](context)


def _number(values: dict[str, Any], key: str) -> Decimal:
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"accounting source field {key} must be numeric")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError(f"accounting source field {key} must be finite")
    return result


def _exact(value: Decimal) -> int:
    if value != value.to_integral_value():
        raise ValueError("accounting calculation needs an explicit rounding policy")
    return int(value)


def _pounds(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _result(values: dict[str, int], steps: list[str]) -> dict[str, Any]:
    return {
        "answer": "\n".join(
            f"{label.replace('_', ' ')}: {'−' if amount < 0 else ''}£{abs(amount):,}"
            for label, amount in values.items()
        ),
        "steps": steps,
        "numeric_results": values,
        "evidence_ids": [],
    }


def _assets(context: dict[str, Any]) -> dict[str, Any]:
    opening = context["opening_balances"]
    transactions = context["transactions_at_start_of_year"]
    policy = context["depreciation_policy"]
    plant = opening["plant_and_machinery"]
    motor = opening["motor_vehicles"]
    plant_cost = _number(plant, "cost") + _number(transactions, "plant_purchase_cost")
    plant_charge = plant_cost * _number(policy, "plant_straight_line_percent_on_cost") / 100
    plant_depreciation = _number(plant, "accumulated_depreciation") + plant_charge
    motor_cost = _number(motor, "cost") - _number(transactions, "motor_disposal_cost")
    motor_before = _number(motor, "accumulated_depreciation") - _number(
        transactions, "motor_disposal_accumulated_depreciation"
    )
    motor_charge = (motor_cost - motor_before) * _number(
        policy, "motor_reducing_balance_percent"
    ) / 100
    motor_depreciation = motor_before + motor_charge
    plant_carrying = plant_cost - plant_depreciation
    motor_carrying = motor_cost - motor_depreciation
    return _result(
        {
            "plant_cost": _exact(plant_cost),
            "plant_depreciation_charge": _exact(plant_charge),
            "plant_accumulated_depreciation": _exact(plant_depreciation),
            "plant_carrying_amount": _exact(plant_carrying),
            "motor_cost": _exact(motor_cost),
            "motor_depreciation_charge": _exact(motor_charge),
            "motor_accumulated_depreciation": _exact(motor_depreciation),
            "motor_carrying_amount": _exact(motor_carrying),
            "total_carrying_amount": _exact(plant_carrying + motor_carrying),
        },
        [
            "Add the plant purchase to opening cost.",
            "Apply straight-line depreciation to closing plant cost.",
            "Deduct accumulated depreciation to obtain plant carrying amount.",
            "Remove the disposed motor vehicle's cost and accumulated depreciation.",
            "Apply reducing-balance depreciation to the remaining motor carrying amount.",
            "Deduct closing accumulated depreciation to obtain motor carrying amount.",
            "Add the two carrying amounts for total non-current assets.",
        ],
    )


def _ledger(context: dict[str, Any]) -> dict[str, Any]:
    data = context["source_data"]
    total = _number(data, "opening_trade_receivables") + _number(data, "credit_sales")
    closing = total - sum(
        _number(data, key)
        for key in (
            "sales_returns",
            "cash_received_from_credit_customers",
            "discount_allowed",
        )
    )
    return _result(
        {"account_total": _exact(total), "closing_trade_receivables": _exact(closing)},
        [
            "Debit the opening balance and credit sales.",
            "Credit receipts, returns, and discounts.",
            "Balance the account and bring the closing receivable down as a debit.",
        ],
    )


def _sales(context: dict[str, Any]) -> dict[str, Any]:
    data = context["source_data"]
    net = _number(data, "gross_credit_sales") - _number(data, "sales_returns")
    return _result(
        {"net_sales_transferred_to_income_statement": _exact(net)},
        [
            "Credit gross sales.",
            "Debit sales returns.",
            "Transfer the net credit balance to the income statement.",
        ],
    )


def _income(context: dict[str, Any]) -> dict[str, Any]:
    data = context["source_data"]
    adjustments = context["adjustment_source_data"]
    policy = context["adjustment_policy"]
    if policy.get("round_each_adjustment_to_nearest_pound") is not True:
        raise ValueError("income statement requires an explicit whole-pound policy")
    nrv = _number(adjustments, "damaged_inventory_sale_proceeds") - _number(
        adjustments, "damaged_inventory_repair_cost"
    )
    write_down = max(Decimal(0), _number(adjustments, "damaged_inventory_cost") - nrv)
    debt = _pounds(
        _number(adjustments, "trade_receivable")
        * _number(policy, "irrecoverable_debt_percent") / 100
    )
    finance = sum(
        _pounds(
            _number(adjustments, f"{period}_debenture")
            * _number(policy, f"{period}_debenture_rate_percent") / 100
            * _number(policy, f"{period}_debenture_months") / 12
        )
        for period in ("new", "earlier")
    )
    revenue = _exact(_number(data, "revenue"))
    cost_of_sales = _exact(_number(data, "cost_of_sales") + write_down)
    administration = _exact(_number(data, "administration_expenses") + debt)
    marketing = _exact(
        _number(data, "marketing_expenses") + _number(adjustments, "supplier_invoice")
    )
    warehouse = _exact(_number(data, "warehouse_expenses"))
    insurance = _exact(_number(adjustments, "insurance_claim"))
    tax = _exact(_number(adjustments, "current_tax_charge"))
    profit_before_tax = (
        revenue - cost_of_sales - administration - marketing - warehouse
        + insurance - finance
    )
    return _result(
        {
            "revenue": revenue,
            "adjusted_cost_of_sales": cost_of_sales,
            "gross_profit": revenue - cost_of_sales,
            "adjusted_administration_expenses": administration,
            "adjusted_marketing_expenses": marketing,
            "warehouse_expenses": warehouse,
            "insurance_claim": insurance,
            "finance_cost": finance,
            "profit_before_tax": profit_before_tax,
            "taxation": tax,
            "profit_for_year": profit_before_tax - tax,
        },
        [
            "Net realisable value is sale proceeds less repair cost; write inventory down to that value.",
            "Add the inventory write-down to cost of sales and calculate gross profit.",
            "Add the irrecoverable proportion of the receivable to administration expenses.",
            "Accrue the unrecorded supplier invoice in marketing expenses.",
            "Keep the roof repair in warehouse expenses and recognise the supplied insurance claim separately.",
            "Time-apportion both debenture interest charges, rounding each adjustment as instructed.",
            "Deduct all adjusted expenses and add other income to obtain profit before tax.",
            "Deduct the supplied taxation charge to obtain profit for the year.",
        ],
    )


def _retirement(context: dict[str, Any]) -> dict[str, Any]:
    data = context["source_data"]
    old_ratio = data["old_profit_sharing_ratio"]
    new_ratio = data["new_profit_sharing_ratio"]
    goodwill = _number(data, "goodwill")
    values: dict[str, int] = {}
    for partner in new_ratio:
        credit = goodwill * _number(old_ratio, partner) / sum(old_ratio.values())
        write_off = goodwill * _number(new_ratio, partner) / sum(new_ratio.values())
        target = _number(data["target_capital"], partner)
        withdrawal = _number(data["opening_capital"], partner) + credit - write_off - target
        values[f"{partner}_goodwill_credit"] = _exact(credit)
        values[f"{partner}_goodwill_write_off"] = _exact(write_off)
        values[f"{partner}_cash_withdrawn"] = _exact(withdrawal)
        values[f"{partner}_closing_capital"] = _exact(target)
    return _result(
        values,
        [
            "Enter the continuing partners' opening capitals.",
            "Credit goodwill in the old profit-sharing ratio.",
            "Write goodwill off only against the continuing partners in the new ratio.",
            "Calculate each cash withdrawal to reach the stated target capital.",
            "Balance and bring down both continuing capital accounts.",
        ],
    )


def _appropriation(context: dict[str, Any]) -> dict[str, Any]:
    data = context["source_data"]
    values: dict[str, int] = {}
    for index, period in enumerate(("first_period", "second_period")):
        months = Decimal(data["period_months"][index])
        profit = _number(data, "profit_for_year") * months / 12
        drawings = sum(
            _number(data["interest_on_drawings"][period], partner)
            for partner in data["interest_on_drawings"][period]
        )
        capitals = data["capital_balances"][period]
        interest = {
            partner: _number(capitals, partner)
            * _number(data, "capital_interest_rate_percent") / 100 * months / 12
            for partner in capitals
        }
        salary = _number(data["partner_salary_per_year"], "Morgan") * months / 12
        residual = profit + drawings - salary - sum(interest.values())
        ratio = data["profit_sharing_ratios"][period]
        values[f"{period}_profit"] = _exact(profit)
        values[f"{period}_drawings_interest"] = _exact(drawings)
        values[f"{period}_salary"] = _exact(salary)
        values[f"{period}_residual_profit"] = _exact(residual)
        for partner, amount in interest.items():
            values[f"{period}_{partner}_capital_interest"] = _exact(amount)
        for partner in ratio:
            values[f"{period}_{partner}_profit_share"] = _exact(
                residual * _number(ratio, partner) / sum(ratio.values())
            )
    return _result(
        values,
        [
            "Apportion the annual profit between the two periods.",
            "Add each period's interest on drawings.",
            "Calculate interest on opening capitals for the first period.",
            "Calculate interest on revised capitals for the second period.",
            "Time-apportion Morgan's salary.",
            "Calculate the residual profit in each period.",
            "Allocate the first residual profit in the old ratio.",
            "Allocate the second residual profit in the new ratio.",
        ],
    )
