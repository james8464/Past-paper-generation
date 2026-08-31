from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from Backend.Core.numeric_integrity import MONEY, NUMBER, NumericOutput, numeric_result


def solve_accounting_calculation(item: dict[str, Any]) -> dict[str, Any] | None:
    """Recompute known closed accounting contracts from candidate-visible data.

    No renderer, draft mark scheme, or verified-answer field is consulted. The
    normal model content and difficulty reviews still run after this arithmetic
    pass. Unrecognised closed calculations fail on the shared solver boundary.
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
        **{
            rule: (_management, {"source_data", "numeric_input_contract"})
            for rule in MANAGEMENT_INPUT_UNITS
        },
    }
    entry = solvers.get(str(item.get("rule_id", "")))
    if entry is None or not entry[1].issubset(context):
        return None
    rule = str(item["rule_id"])
    if rule in MANAGEMENT_INPUT_UNITS:
        expected = management_input_contract(rule, context["source_data"])
        if context["numeric_input_contract"] != expected:
            raise ValueError(
                "accounting numeric candidate-input contract is stale or inconsistent"
            )
        result = _management(context, rule)
    else:
        result = entry[0](context)
    solution = numeric_result(
        result["numeric_results"], accounting_outputs(rule, context), result["steps"]
    )
    if rule == "costing_3":
        values = list(result["numeric_results"].values())
        priority = (
            "Product A"
            if values[0] > values[1]
            else "Product B"
            if values[1] > values[0]
            else "Equal priority"
        )
        solution["answer"]["ranked_first"] = priority
        solution["mark_points"]["ranked_first"] = priority
        solution["text_checks"] = [
            {
                "role": "ranked_first",
                "value": priority,
                "scheme_pattern": r"^Ranking: (Product A|Product B|Equal priority) should be produced first",
            }
        ]
    return solution


MANAGEMENT_INPUT_UNITS = {
    "contribution": {
        "units_sold": "units",
        "selling_price_per_unit": "GBP/unit",
        "variable_cost_per_unit": "GBP/unit",
        "fixed_cost": "GBP",
    },
    "budget": {
        key: "GBP"
        for key in (
            "sales_receipts",
            "variable_cost_payments",
            "fixed_cost_payments",
            "opening_cash",
            "capital_payment",
        )
    },
    "variance_1": {
        "standard_price_per_kg": "GBP/kg",
        "actual_price_per_kg": "GBP/kg",
        "actual_quantity_kg": "kg",
    },
    "variance_2": {
        "standard_hourly_rate": "GBP/hour",
        "actual_hourly_rate": "GBP/hour",
        "standard_hours": "hours",
        "actual_hours": "hours",
        "budgeted_fixed_overhead": "GBP",
        "actual_fixed_overhead": "GBP",
    },
    "costing_1": {
        "setup_cost_pool": "GBP",
        "purchase_order_cost_pool": "GBP",
        "total_setups": "setups",
        "total_purchase_orders": "orders",
        "product_setups": "setups",
        "product_purchase_orders": "orders",
        "product_units": "units",
    },
    "costing_3": {
        "product_a_contribution": "GBP/unit",
        "product_a_scarce_hours": "hours/unit",
        "product_b_contribution": "GBP/unit",
        "product_b_scarce_hours": "hours/unit",
    },
}


def management_input_contract(rule: str, source: dict[str, Any]) -> dict[str, Any]:
    units = MANAGEMENT_INPUT_UNITS[rule]
    if set(source) != set(units):
        raise ValueError("accounting numeric candidate-input contract is incomplete")
    return {
        "version": 1,
        "inputs": {
            key: {"value": float(_number(source, key)), "unit": unit}
            for key, unit in units.items()
        },
        "outputs": [
            output.model_dump(exclude={"scheme_pattern"})
            for output in accounting_outputs(rule, {})
        ],
        "rounding": "half-up at display only; retain full intermediate precision",
        "variance_sign": "positive favourable; negative adverse; zero nil",
        "text_outputs": ["ranked_first"] if rule == "costing_3" else [],
    }


def accounting_outputs(rule: str, context: dict[str, Any]) -> list[NumericOutput]:
    """Code-owned role selectors. They contain no solved numbers or draft keys."""
    patterns: dict[str, str] = {}
    units: dict[str, str] = {}
    places = 0
    variance_roles: set[str] = set()
    if rule == "contribution":
        patterns = {
            role: rf"^{label}:[^\n=]*=\s*{MONEY}"
            for role, label in (
                ("contribution_per_unit", "Contribution per unit"),
                ("contribution", "Total contribution"),
                ("profit", "Profit"),
            )
        }
        units["contribution_per_unit"] = "GBP/unit"
    elif rule == "budget":
        patterns = {
            role: rf"^{label}:[^\n=]*=\s*{MONEY}"
            for role, label in (
                ("contribution", "Contribution"),
                ("budgeted_profit", "Budgeted profit"),
                ("net_cash_flow", "Net cash flow"),
                ("closing_cash", "Closing cash"),
            )
        }
    elif rule == "variance_1":
        patterns = {
            "price_difference": rf"^Price difference:[^\n=]*=\s*{MONEY} per kg",
            "direct_material_price_variance": rf"^Direct-material price variance:[^\n=]*=\s*{MONEY}\s+(?P<direction>favourable|adverse|nil)",
        }
        units["price_difference"] = "GBP/kg"
        variance_roles = {"direct_material_price_variance"}
    elif rule == "variance_2":
        patterns = {
            role: rf"^{label}:[^\n=]*=\s*{MONEY}\s+(?P<direction>favourable|adverse|nil)"
            for role, label in (
                ("labour_rate_variance", "Labour rate variance"),
                ("labour_efficiency_variance", "Labour efficiency variance"),
                (
                    "fixed_overhead_expenditure_variance",
                    "Fixed-overhead expenditure variance",
                ),
            )
        }
        variance_roles = set(patterns)
    elif rule == "costing_1":
        places = 2
        patterns = {
            role: rf"^{label}:[^\n=]*=\s*{MONEY}"
            for role, label in (
                ("setup_rate", "Set-up driver rate"),
                ("purchase_order_rate", "Purchase-order driver rate"),
                ("setup_overhead", "Set-up overhead assigned"),
                ("purchase_order_overhead", "Purchase-order overhead assigned"),
                ("total_overhead", "Total activity-based overhead"),
                ("overhead_per_unit", "Overhead cost per unit"),
            )
        }
        units = {
            "setup_rate": "GBP/setup",
            "purchase_order_rate": "GBP/order",
            "overhead_per_unit": "GBP/unit",
        }
    elif rule == "costing_3":
        places = 2
        patterns = {
            f"product_{product}_contribution_per_scarce_hour": rf"^Product {product.upper()}:[^\n=]*=\s*{MONEY} per scarce hour"
            for product in ("a", "b")
        }
        units = dict.fromkeys(patterns, "GBP/scarce hour")
    elif rule == "statement_extract":
        patterns = {
            "plant_cost": rf"^Plant cost:[^\n=]*=\s*{MONEY}",
            "plant_depreciation_charge": rf"^Plant depreciation:[^\n=]*=\s*{MONEY};",
            "plant_accumulated_depreciation": rf"^Plant depreciation:[^\n;]*;[^\n=]*=\s*{MONEY}",
            "plant_carrying_amount": rf"^Plant and machinery carrying amount:\s*{MONEY}",
            "motor_cost": rf"^Motor cost:[^\n=]*=\s*{MONEY};",
            "motor_depreciation_charge": rf"^Motor depreciation:[^\n=]*=\s*{MONEY}",
            "motor_accumulated_depreciation": rf"^Motor vehicles closing accumulated depreciation\s*{MONEY}",
            "motor_carrying_amount": rf"^Motor vehicles closing accumulated depreciation[^\n]*carrying amount\s*{MONEY}",
            "total_carrying_amount": rf"^Total non-current assets:\s*{MONEY}",
        }
    elif rule == "ledger_calculation":
        patterns = {
            "account_total": rf"^Balance the account at\s*{MONEY}",
            "closing_trade_receivables": rf"^Balance the account[^\n]*closing trade receivables of\s*{MONEY}",
        }
    elif rule == "accounting_concept":
        patterns = {
            "net_sales_transferred_to_income_statement": rf"^Debit sales returns[^\n]*transfer net sales of\s*{MONEY}"
        }
    elif rule == "company_statement":
        patterns = {
            "inventory_write_down": rf"^Damaged inventory write-down:[^\n=]*=\s*{MONEY}",
            "irrecoverable_debt": rf"^Irrecoverable debt:[^\n=]*=\s*{MONEY}",
            "new_debenture_interest": rf"^Debenture interest:[^\n=]*=\s*{MONEY}",
            "earlier_debenture_interest": rf"^Debenture interest:[^\n]* and [^\n=]*=\s*{MONEY}",
            "revenue": rf"^Revenue:\s*{MONEY}",
            "adjusted_cost_of_sales": rf"^Adjusted cost of sales:[^\n=]*=\s*{MONEY}",
            "gross_profit": rf"^Gross profit:[^\n=]*=\s*{MONEY}",
            "adjusted_administration_expenses": rf"^Administration expenses:[^\n=]*=\s*{MONEY}",
            "adjusted_marketing_expenses": rf"^Marketing expenses:[^\n=]*=\s*{MONEY}",
            "warehouse_expenses": rf"^Warehouse expenses:\s*{MONEY}",
            "insurance_claim": rf"^Other income — insurance claim:\s*{MONEY}",
            "finance_cost": rf"^Total finance cost:\s*{MONEY}",
            "profit_before_tax": rf"^Profit before tax:\s*{MONEY}",
            "taxation": rf"^Supplied taxation charge:\s*{MONEY}",
            "profit_for_year": rf"^Supplied taxation charge:[^\n;]*; final profit for the year:\s*{MONEY}",
        }
    elif rule == "partnership_1":
        for partner in context["source_data"]["new_profit_sharing_ratio"]:
            patterns.update(
                {
                    f"{partner}_goodwill_credit": rf"^Credit total goodwill[^\n]*{partner}\s*{MONEY}",
                    f"{partner}_goodwill_write_off": rf"^Write goodwill off[^\n]*{partner}\s*{MONEY}",
                    f"{partner}_cash_withdrawn": rf"^Record {partner}'s cash withdrawal of\s*{MONEY}",
                    f"{partner}_closing_capital": rf"^Closing capital balances:[^\n]*{partner}\s*{MONEY}",
                }
            )
    elif rule == "partnership_2":
        for period, label in (("first_period", "first"), ("second_period", "second")):
            patterns.update(
                {
                    f"{period}_profit": rf"^Apportion annual profit[^\n]*{label} period\s*{MONEY}",
                    f"{period}_drawings_interest": rf"^Interest on drawings:[^\n]*{label} period[^;\n]*total\s*{MONEY}",
                    f"{period}_salary": rf"^Morgan's annual salary[^\n]*{label} period\s*{MONEY}",
                    f"{period}_residual_profit": rf"^Residual profit:[^\n]*{label} period\s*{MONEY}",
                }
            )
            for partner in context["source_data"]["capital_balances"][period]:
                patterns[f"{period}_{partner}_capital_interest"] = (
                    rf"^{label}-period interest on capital[^\n]*{partner}[^;\n]*gives\s*{MONEY}"
                )
                patterns[f"{period}_{partner}_profit_share"] = (
                    rf"Riley's first-period share\s*{MONEY}"
                    if partner == "Riley"
                    else rf"^{partner}'s residual-profit share[^\n]*{label} period\s*{MONEY}"
                )
    return [
        NumericOutput(
            role=role,
            unit=units.get(role, "GBP"),
            decimal_places=places,
            scheme_pattern=pattern,
            **(
                {"scheme_ending": ending}
                if (ending := _accounting_endings(rule).get(role))
                else {}
            ),
            sign="variance" if role in variance_roles else "signed",
        )
        for role, pattern in patterns.items()
    ]


def _accounting_endings(rule: str) -> dict[str, str]:
    """Complete code-owned row continuations; never a free suffix wildcard.

    Other computed quantities on the same row have their own output checks.
    Given quantities in working remain source inputs, not accepted alternatives.
    """
    money = rf"[−+\-]?£{NUMBER}"
    second = rf"; second period {money}\."
    if rule == "statement_extract":
        return {
            "plant_depreciation_charge": rf"; accumulated depreciation {money} \+ {money} = {money}\.",
            "motor_cost": rf"; accumulated depreciation {money} − {money} = {money}\.",
            "motor_accumulated_depreciation": rf"and carrying amount {money}\.",
        }
    if rule == "ledger_calculation":
        return {
            "account_total": rf"; carry down and bring down closing trade receivables of {money}\."
        }
    if rule == "accounting_concept":
        return {
            "net_sales_transferred_to_income_statement": r"to the income statement\."
        }
    if rule == "company_statement":
        return {
            "new_debenture_interest": rf"and {money} × {NUMBER}% × {NUMBER}/{NUMBER} = {money}\.",
            "insurance_claim": rf"\. The roof repair of {money} is already included in warehouse expenses\.",
            "taxation": rf"; final profit for the year: {money}\.",
        }
    if rule == "partnership_1":
        return {
            f"Alex_{role}": rf"; Morgan {money}\."
            for role in ("goodwill_credit", "goodwill_write_off", "closing_capital")
        }
    if rule == "partnership_2":
        riley = rf"; Riley's first-period share {money}\."
        return {
            **{
                f"first_period_{role}": second
                for role in ("profit", "salary", "residual_profit", "Alex_profit_share")
            },
            "first_period_drawings_interest": rf"; second period Alex {money}, Morgan {money}, total {money}\.",
            "first_period_Alex_capital_interest": rf"; Morgan {money} gives {money}; Riley {money} gives {money}\.",
            "first_period_Morgan_capital_interest": rf"; Riley {money} gives {money}\.",
            "second_period_Alex_capital_interest": rf"; Morgan {money} gives {money}\.",
            "first_period_Morgan_profit_share": rf"; second period {money}{riley}",
            "second_period_Morgan_profit_share": riley,
        }
    return {}


def _management(context: dict[str, Any], rule: str) -> dict[str, Any]:
    data = {
        key: _number(context["source_data"], key)
        for key in MANAGEMENT_INPUT_UNITS[rule]
    }
    if any(value < 0 for value in data.values()):
        raise ValueError("accounting source inputs must be non-negative")
    if rule == "contribution":
        unit_contribution = (
            data["selling_price_per_unit"] - data["variable_cost_per_unit"]
        )
        contribution = unit_contribution * data["units_sold"]
        values = {
            "contribution_per_unit": unit_contribution,
            "contribution": contribution,
            "profit": contribution - data["fixed_cost"],
        }
    elif rule == "budget":
        contribution = data["sales_receipts"] - data["variable_cost_payments"]
        profit = contribution - data["fixed_cost_payments"]
        flow = profit - data["capital_payment"]
        values = {
            "contribution": contribution,
            "budgeted_profit": profit,
            "net_cash_flow": flow,
            "closing_cash": data["opening_cash"] + flow,
        }
    elif rule == "variance_1":
        difference = data["standard_price_per_kg"] - data["actual_price_per_kg"]
        values = {
            "price_difference": difference,
            "direct_material_price_variance": difference * data["actual_quantity_kg"],
        }
    elif rule == "variance_2":
        values = {
            "labour_rate_variance": (
                data["standard_hourly_rate"] - data["actual_hourly_rate"]
            )
            * data["actual_hours"],
            "labour_efficiency_variance": (
                data["standard_hours"] - data["actual_hours"]
            )
            * data["standard_hourly_rate"],
            "fixed_overhead_expenditure_variance": data["budgeted_fixed_overhead"]
            - data["actual_fixed_overhead"],
        }
    elif rule == "costing_1":
        setup_rate = data["setup_cost_pool"] / data["total_setups"]
        order_rate = data["purchase_order_cost_pool"] / data["total_purchase_orders"]
        setup = setup_rate * data["product_setups"]
        order = order_rate * data["product_purchase_orders"]
        values = {
            "setup_rate": setup_rate,
            "purchase_order_rate": order_rate,
            "setup_overhead": setup,
            "purchase_order_overhead": order,
            "total_overhead": setup + order,
            "overhead_per_unit": (setup + order) / data["product_units"],
        }
    else:
        values = {
            f"product_{p}_contribution_per_scarce_hour": data[
                f"product_{p}_contribution"
            ]
            / data[f"product_{p}_scarce_hours"]
            for p in ("a", "b")
        }
    return {
        "numeric_results": values,
        "steps": [
            f"Compute {role.replace('_', ' ')} from the supplied inputs, retaining full precision."
            for role in values
        ],
    }


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
    plant_charge = (
        plant_cost * _number(policy, "plant_straight_line_percent_on_cost") / 100
    )
    plant_depreciation = _number(plant, "accumulated_depreciation") + plant_charge
    motor_cost = _number(motor, "cost") - _number(transactions, "motor_disposal_cost")
    motor_before = _number(motor, "accumulated_depreciation") - _number(
        transactions, "motor_disposal_accumulated_depreciation"
    )
    motor_charge = (
        (motor_cost - motor_before)
        * _number(policy, "motor_reducing_balance_percent")
        / 100
    )
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
        * _number(policy, "irrecoverable_debt_percent")
        / 100
    )
    interest_charges = {
        period: _pounds(
            _number(adjustments, f"{period}_debenture")
            * _number(policy, f"{period}_debenture_rate_percent")
            / 100
            * _number(policy, f"{period}_debenture_months")
            / 12
        )
        for period in ("new", "earlier")
    }
    finance = sum(interest_charges.values())
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
        revenue
        - cost_of_sales
        - administration
        - marketing
        - warehouse
        + insurance
        - finance
    )
    return _result(
        {
            "inventory_write_down": _exact(write_down),
            "irrecoverable_debt": debt,
            "new_debenture_interest": interest_charges["new"],
            "earlier_debenture_interest": interest_charges["earlier"],
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
        withdrawal = (
            _number(data["opening_capital"], partner) + credit - write_off - target
        )
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
            * _number(data, "capital_interest_rate_percent")
            / 100
            * months
            / 12
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
