"""Deterministic selected responses derived only from candidate-visible inputs."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SELECTED_RESPONSE_VERSION = "selected-response-v1"
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")

SelectedOperation = Literal[
    "index_percentage_increase",
    "index_percentage_decrease",
    "index_percentage_change",
    "economic_shift",
    "opportunity_cost_change",
    "elastic_revenue_change",
    "income_distribution_change",
    "interest_rate_demand_change",
    "trade_elasticity_effect",
    "gross_profit",
    "after_tax_profit",
    "highest_productivity",
    "performance_statements",
    "break_even_change",
    "strategic_drift",
]
SelectedUnit = Literal[
    "index", "percent", "effect", "GBPm", "quantity", "classification"
]

_OPERATION_FORMAT_POLICY: dict[str, tuple[str, int]] = {
    "index_percentage_increase": ("index", 1),
    "index_percentage_decrease": ("index", 1),
    "index_percentage_change": ("percent", 1),
    "economic_shift": ("effect", 0),
    "opportunity_cost_change": ("quantity", 0),
    "elastic_revenue_change": ("effect", 0),
    "income_distribution_change": ("effect", 0),
    "interest_rate_demand_change": ("effect", 0),
    "trade_elasticity_effect": ("effect", 0),
    "gross_profit": ("GBPm", 0),
    "after_tax_profit": ("GBPm", 0),
    "highest_productivity": ("classification", 0),
    "performance_statements": ("classification", 0),
    "break_even_change": ("effect", 0),
    "strategic_drift": ("classification", 0),
}


class SelectedResponseRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1)
    target: Decimal | None = None
    actual: Decimal | None = None
    output: Decimal | None = None
    employees: Decimal | None = None
    better_when: Literal["higher", "lower"] | None = None


class SelectedResponseContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["selected-response-v1"] = SELECTED_RESPONSE_VERSION
    operation: SelectedOperation
    inputs: dict[str, Decimal | str] = Field(default_factory=dict)
    rows: list[SelectedResponseRow] = Field(default_factory=list)
    unit: SelectedUnit
    decimal_places: int = Field(ge=0, le=4)


def selected_response_contract(
    operation: SelectedOperation,
    *,
    inputs: dict[str, Decimal | str] | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a contract from the one operation-owned output format policy."""
    unit, decimal_places = _OPERATION_FORMAT_POLICY[operation]
    return SelectedResponseContract(
        operation=operation,
        inputs=inputs or {},
        rows=rows or [],
        unit=unit,
        decimal_places=decimal_places,
    ).model_dump(mode="json")


def solve_selected_response(item: dict[str, Any]) -> dict[str, Any] | None:
    """Return a one-choice solution for a supported public-input contract."""
    context = item.get("authoring_context")
    raw_contract = (
        context.get("selected_response_contract")
        if isinstance(context, dict)
        else None
    )
    if raw_contract is None:
        return None
    if item.get("kind") != "multiple_choice" or item.get("marks") != 1:
        raise ValueError("selected-response contract requires a one-mark choice item")
    contract = SelectedResponseContract.model_validate(raw_contract)
    if (contract.unit, contract.decimal_places) != _OPERATION_FORMAT_POLICY[
        contract.operation
    ]:
        raise ValueError(
            f"{contract.operation} violates selected response format policy"
        )
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != 4 or any(
        not isinstance(choice, str) or not choice.strip() for choice in choices
    ):
        raise ValueError("selected-response contract requires four choices")
    normalized_choices = [" ".join(choice.casefold().split()) for choice in choices]
    if len(set(normalized_choices)) != 4:
        raise ValueError("selected-response contract requires four distinct choices")
    if contract.rows:
        normalized_labels = [
            " ".join(row.label.casefold().split()) for row in contract.rows
        ]
        if len(set(normalized_labels)) != len(normalized_labels):
            raise ValueError("selected response requires distinct row labels")

    numeric_results: dict[str, float] = {}
    if contract.operation == "index_percentage_increase":
        _require_contract_shape(contract, {"base", "rate_percent"})
        base = _decimal(contract.inputs["base"])
        rate = _decimal(contract.inputs["rate_percent"])
        if base <= 0 or rate <= 0:
            raise ValueError("index selected response inputs must be finite and positive")
        quantum = Decimal(1).scaleb(-contract.decimal_places)
        expected = (base * (Decimal(1) + rate / Decimal(100))).quantize(
            quantum,
            rounding=ROUND_HALF_UP,
        )
        expected_text = _numeric_choice(
            choices, expected, contract.decimal_places
        )
        steps = ["Multiply the candidate-visible base index by one plus the percentage rate."]
        numeric_results = {"selected_value": float(expected)}
    elif contract.operation == "index_percentage_decrease":
        _require_contract_shape(contract, {"base", "rate_percent"})
        base = _decimal(contract.inputs["base"])
        rate = _decimal(contract.inputs["rate_percent"])
        if base <= 0 or rate <= 0 or rate >= 100:
            raise ValueError("index selected response inputs must be finite and positive")
        quantum = Decimal(1).scaleb(-contract.decimal_places)
        expected = (base * (Decimal(1) - rate / Decimal(100))).quantize(
            quantum,
            rounding=ROUND_HALF_UP,
        )
        expected_text = _numeric_choice(choices, expected, contract.decimal_places)
        steps = ["Multiply the candidate-visible base index by one minus the percentage rate."]
        numeric_results = {"selected_value": float(expected)}
    elif contract.operation == "index_percentage_change":
        _require_contract_shape(contract, {"initial", "final"})
        initial = _decimal(contract.inputs["initial"])
        final = _decimal(contract.inputs["final"])
        if initial <= 0 or final < 0:
            raise ValueError("index selected response inputs must be finite and positive")
        quantum = Decimal(1).scaleb(-contract.decimal_places)
        expected = ((final - initial) / initial * Decimal(100)).quantize(
            quantum,
            rounding=ROUND_HALF_UP,
        )
        expected_text = _percent_choice(choices, expected, contract.decimal_places)
        steps = ["Divide the change in the candidate-visible index by its initial value."]
        numeric_results = {"selected_value": float(expected)}
    elif contract.operation == "economic_shift":
        _require_contract_shape(
            contract,
            {"curve", "direction", "scope", "x_axis", "y_axis"},
        )
        values = {key: str(value) for key, value in contract.inputs.items()}
        expected_axes = (
            ("Real output", "Price level")
            if values["scope"] == "aggregate"
            else ("Quantity", "Price")
            if values["scope"] == "market"
            else None
        )
        if expected_axes is None or (
            values["x_axis"], values["y_axis"]
        ) != expected_axes:
            raise ValueError("economic shift has invalid public axes")
        try:
            curve, direction, scope = values["curve"], values["direction"], values["scope"]
            expected_text = {
                ("D", "right", "market"): "Equilibrium price rises and equilibrium quantity rises",
                ("D", "left", "market"): "Equilibrium price falls and equilibrium quantity falls",
                ("S", "right", "market"): "Equilibrium price falls and equilibrium quantity rises",
                ("S", "left", "market"): "Equilibrium price rises and equilibrium quantity falls",
                ("AD", "right", "aggregate"): "The price level rises and real output rises",
                ("AD", "left", "aggregate"): "The price level falls and real output falls",
                ("SRAS", "right", "aggregate"): "The price level falls and real output rises",
                ("SRAS", "left", "aggregate"): "The price level rises and real output falls",
                ("LRAS", "right", "aggregate"): "The price level falls and real output rises",
                ("LRAS", "left", "aggregate"): "The price level rises and real output falls",
            }[(curve, direction, scope)]
        except KeyError as error:
            raise ValueError("economic shift has invalid public inputs") from error
        steps = ["Infer the new equilibrium from the candidate-visible curve shift."]
    elif contract.operation == "opportunity_cost_change":
        prompt = item.get("prompt")
        if not isinstance(prompt, str) or not all(
            re.search(rf"\bproduct\s+{label}\b", prompt, re.IGNORECASE)
            for label in ("x", "y")
        ):
            raise ValueError(
                "opportunity-cost product labels must match product X and product Y "
                "in the public stem and source-owned choices"
            )
        _require_contract_shape(
            contract,
            {"primary_before", "secondary_before", "primary_after", "secondary_after"},
        )
        values = {key: _decimal(value) for key, value in contract.inputs.items()}
        primary_gain = values["primary_after"] - values["primary_before"]
        secondary_loss = values["secondary_before"] - values["secondary_after"]
        if any(value < 0 for value in values.values()) or primary_gain <= 0 or secondary_loss <= 0:
            raise ValueError("opportunity-cost source has invalid public values")
        expected_text = _quantity_choice(
            choices, secondary_loss, contract.decimal_places
        )
        steps = ["Read the candidate-visible fall in product Y as the opportunity cost."]
        numeric_results = {"opportunity_cost": float(secondary_loss)}
    elif contract.operation == "elastic_revenue_change":
        _require_contract_shape(
            contract,
            {"price_before", "quantity_before", "price_after", "quantity_after"},
        )
        values = {key: _decimal(value) for key, value in contract.inputs.items()}
        if any(value <= 0 for value in values.values()):
            raise ValueError("revenue source has invalid public values")
        before = values["price_before"] * values["quantity_before"]
        after = values["price_after"] * values["quantity_after"]
        expected_text = (
            "Total expenditure rises"
            if after > before
            else "Total expenditure falls"
            if after < before
            else "Total expenditure is unchanged"
        )
        steps = ["Compare price multiplied by quantity before and after the change."]
        numeric_results = {"expenditure_before": float(before), "expenditure_after": float(after)}
    elif contract.operation == "income_distribution_change":
        _require_contract_shape(
            contract,
            {
                "poorest_share_before", "richest_share_before",
                "poorest_share_after", "richest_share_after",
            },
        )
        values = {key: _decimal(value) for key, value in contract.inputs.items()}
        if any(value < 0 or value > 100 for value in values.values()) or (
            values["poorest_share_before"] > values["richest_share_before"]
            or values["poorest_share_after"] > values["richest_share_after"]
        ):
            raise ValueError("income-distribution source has invalid public shares")
        before = values["richest_share_before"] - values["poorest_share_before"]
        after = values["richest_share_after"] - values["poorest_share_after"]
        expected_text = (
            "Income inequality falls"
            if after < before
            else "Income inequality rises"
            if after > before
            else "Income inequality is unchanged"
        )
        steps = ["Compare the candidate-visible gap between the richest and poorest shares."]
    elif contract.operation == "interest_rate_demand_change":
        _require_contract_shape(
            contract,
            {"interest_rate_before", "interest_rate_after", "credit_share_percent"},
        )
        before = _decimal(contract.inputs["interest_rate_before"])
        after = _decimal(contract.inputs["interest_rate_after"])
        share = _decimal(contract.inputs["credit_share_percent"])
        if before < 0 or after < 0 or share <= 0 or share > 100:
            raise ValueError("interest-rate source has an invalid public credit share")
        expected_text = (
            "Credit-financed consumption and investment weaken"
            if after > before
            else "Credit-financed consumption and investment strengthen"
            if after < before
            else "Credit-financed consumption and investment are unchanged"
        )
        steps = ["Relate the candidate-visible interest-rate movement to borrowing costs."]
    elif contract.operation == "trade_elasticity_effect":
        _require_contract_shape(
            contract,
            {"exchange_rate_direction", "export_elasticity", "import_elasticity"},
        )
        direction = str(contract.inputs["exchange_rate_direction"]).casefold()
        if direction != "depreciation":
            raise ValueError("trade-elasticity source requires a depreciation")
        export_elasticity = _decimal(contract.inputs["export_elasticity"])
        import_elasticity = _decimal(contract.inputs["import_elasticity"])
        if export_elasticity < 0 or import_elasticity < 0:
            raise ValueError("trade-elasticity source has invalid public elasticities")
        total = export_elasticity + import_elasticity
        expected_text = (
            "The trade balance is more likely to improve"
            if total > 1
            else "The trade balance is more likely to worsen"
            if total < 1
            else "The trade balance is unlikely to change from the elasticity condition alone"
        )
        steps = ["Add the candidate-visible export and import elasticities and compare with one."]
    elif contract.operation in {"gross_profit", "after_tax_profit"}:
        names = (
            {"revenue", "cost_of_sales"}
            if contract.operation == "gross_profit"
            else {"revenue", "cost_of_sales", "operating_expenses", "taxation"}
        )
        _require_contract_shape(contract, names)
        numbers = {key: _decimal(value) for key, value in contract.inputs.items()}
        expected = numbers["revenue"] - numbers["cost_of_sales"]
        if contract.operation == "after_tax_profit":
            expected -= numbers["operating_expenses"] + numbers["taxation"]
        if any(number < 0 for number in numbers.values()) or expected < 0:
            raise ValueError("profit source has an invalid public numeric domain")
        expected_text = _money_choice(choices, expected, contract.decimal_places)
        numeric_results = {"selected_value": float(expected)}
        steps = ["Subtract the candidate-visible costs from revenue in the requested order."]
    elif contract.operation == "highest_productivity":
        _require_contract_shape(contract, set(), rows=True)
        if len(contract.rows) < 2 or any(
            row.output is None
            or row.employees is None
            or not row.output.is_finite()
            or not row.employees.is_finite()
            or row.output < 0
            or row.employees <= 0
            or row.target is not None
            or row.actual is not None
            or row.better_when is not None
            for row in contract.rows
        ):
            raise ValueError("productivity selected response has invalid public rows")
        ratios = {row.label: row.output / row.employees for row in contract.rows}
        highest = max(ratios.values())
        winners = [label for label, value in ratios.items() if value == highest]
        if len(winners) != 1:
            raise ValueError("productivity selected response must have one highest row")
        expected_text = winners[0]
        numeric_results = {label: float(value) for label, value in ratios.items()}
        steps = ["Divide each candidate-visible output by its employee count and compare."]
    elif contract.operation == "performance_statements":
        _require_contract_shape(contract, set(), rows=True)
        if any(
            row.target is None
            or row.actual is None
            or not row.target.is_finite()
            or not row.actual.is_finite()
            or row.target < 0
            or row.actual < 0
            or row.better_when is None
            or row.output is not None
            or row.employees is not None
            for row in contract.rows
        ):
            raise ValueError("performance selected response has invalid public rows")
        by_label = {row.label.casefold(): row for row in contract.rows}
        try:
            turnover = by_label["labour turnover"]
            capacity = by_label["capacity utilisation"]
        except KeyError as error:
            raise ValueError("performance selected response is missing required rows") from error
        first = _worse_than_target(turnover)
        second = _better_than_target(capacity)
        expected_text = {
            (True, True): "Both statements are true",
            (True, False): "Statement 1 is true, Statement 2 is false",
            (False, True): "Statement 1 is false, Statement 2 is true",
            (False, False): "Both statements are false",
        }[(first, second)]
        steps = ["Compare each actual value with its target using the declared desirable direction."]
    elif contract.operation == "break_even_change":
        names = {
            "fixed_cost_before", "price_before", "variable_cost_before",
            "fixed_cost_after", "price_after", "variable_cost_after",
        }
        _require_contract_shape(contract, names)
        values = {key: _decimal(value) for key, value in contract.inputs.items()}
        if (
            values["fixed_cost_before"] <= 0
            or values["fixed_cost_after"] <= 0
            or values["price_before"] <= 0
            or values["price_after"] <= 0
            or values["variable_cost_before"] < 0
            or values["variable_cost_after"] < 0
        ):
            raise ValueError("break-even source has invalid public values")
        before_contribution = values["price_before"] - values["variable_cost_before"]
        after_contribution = values["price_after"] - values["variable_cost_after"]
        if before_contribution <= 0 or after_contribution <= 0:
            raise ValueError("break-even source requires positive contribution")
        before = values["fixed_cost_before"] / before_contribution
        after = values["fixed_cost_after"] / after_contribution
        if not (
            values["price_after"] > values["price_before"]
            and values["variable_cost_after"] < values["variable_cost_before"]
            and values["fixed_cost_after"] == values["fixed_cost_before"]
            and after < before
        ):
            raise ValueError("break-even inputs contradict the declared movement")
        expected_text = "A rise in selling price and a fall in variable cost per unit"
        numeric_results = {"before_output": float(before), "after_output": float(after)}
        steps = ["Compute fixed cost divided by contribution before and after the changes."]
    elif contract.operation == "strategic_drift":
        _require_contract_shape(contract, {"external_change", "strategic_change"})
        values = {key: str(value).casefold() for key, value in contract.inputs.items()}
        if values == {"external_change": "high", "strategic_change": "low"}:
            expected_text = "Strategic drift"
        elif values["external_change"] == values["strategic_change"]:
            expected_text = "Strategic fit"
        else:
            raise ValueError("unsupported strategic-change classification")
        steps = ["Identify the concept where strategy changes more slowly than the environment."]
    else:
        raise ValueError("unsupported selected-response operation")

    matches = [index for index, choice in enumerate(choices) if choice.strip().casefold() == expected_text.casefold()]
    if len(matches) != 1:
        raise ValueError("selected response must have exactly one semantic option")
    answer = choices[matches[0]].strip()
    return {
        "steps": steps,
        "answer": answer,
        "mark_points": [answer],
        "evidence_ids": [],
        "alternatives": [],
        "partial_credit_boundaries": [],
        "follow_through_rules": [],
        "numeric_results": numeric_results,
    }


def _plain_decimal(value: str) -> Decimal | None:
    text = value.strip()
    if not _NUMBER.fullmatch(text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _require_contract_shape(
    contract: SelectedResponseContract,
    input_names: set[str],
    *,
    rows: bool = False,
) -> None:
    if set(contract.inputs) != input_names or bool(contract.rows) is not rows:
        raise ValueError(f"{contract.operation} has invalid public inputs")


def _display_decimal(value: str, places: int) -> Decimal | None:
    text = value.strip()
    pattern = (
        re.compile(r"^[+-]?\d+$")
        if places == 0
        else re.compile(rf"^[+-]?\d+\.\d{{{places}}}$")
    )
    if not pattern.fullmatch(text):
        return None
    return _plain_decimal(text)


def _numeric_choice(choices: list[str], expected: Decimal, places: int) -> str:
    parsed = [_display_decimal(choice, places) for choice in choices]
    if (
        any(value is None for value in parsed)
        or len(set(parsed)) != 4
        or sum(value == expected for value in parsed) != 1
    ):
        raise ValueError(
            "selected response requires exact precision and exactly one semantic option"
        )
    return choices[parsed.index(expected)].strip()


def _percent_choice(choices: list[str], expected: Decimal, places: int) -> str:
    parsed: list[Decimal | None] = []
    for choice in choices:
        text = choice.strip()
        parsed.append(
            _display_decimal(text[:-1], places) if text.endswith("%") else None
        )
    if (
        any(value is None for value in parsed)
        or len(set(parsed)) != 4
        or sum(value == expected for value in parsed) != 1
    ):
        raise ValueError(
            "percentage-change selected response requires percent units and exact precision"
        )
    return choices[parsed.index(expected)].strip()


def _quantity_choice(choices: list[str], expected: Decimal, places: int) -> str:
    suffix = " units of product Y"
    parsed = [
        _display_decimal(choice.strip()[: -len(suffix)], places)
        if choice.strip().endswith(suffix)
        else None
        for choice in choices
    ]
    if (
        any(value is None for value in parsed)
        or len(set(parsed)) != 4
        or sum(value == expected for value in parsed) != 1
    ):
        raise ValueError(
            "quantity selected response requires quantity units and exact precision"
        )
    return choices[parsed.index(expected)].strip()


def _decimal(value: Decimal | str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("selected response has an invalid numeric input") from error
    if not result.is_finite():
        raise ValueError("selected response has a non-finite numeric input")
    return result


def _money_choice(choices: list[str], expected: Decimal, places: int) -> str:
    quantum = Decimal(1).scaleb(-places)
    expected = expected.quantize(quantum, rounding=ROUND_HALF_UP)
    parsed = []
    for choice in choices:
        text = choice.strip()
        parsed.append(
            _display_decimal(text[1:-1], places)
            if text.startswith("£") and text.endswith("m")
            else None
        )
    if (
        any(value is None for value in parsed)
        or len(set(parsed)) != 4
        or sum(value == expected for value in parsed) != 1
    ):
        raise ValueError(
            "money selected response requires exact precision and exactly one semantic option"
        )
    return choices[parsed.index(expected)].strip()


def _better_than_target(row: SelectedResponseRow) -> bool:
    if row.actual is None or row.target is None or row.better_when is None:
        raise ValueError("performance row is incomplete")
    return row.actual > row.target if row.better_when == "higher" else row.actual < row.target


def _worse_than_target(row: SelectedResponseRow) -> bool:
    return not _better_than_target(row) and row.actual != row.target
