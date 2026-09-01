"""Deterministic selected responses derived only from candidate-visible inputs."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SELECTED_RESPONSE_VERSION = "selected-response-v1"
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


class SelectedResponseRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    target: Decimal | None = None
    actual: Decimal | None = None
    output: Decimal | None = None
    employees: Decimal | None = None
    better_when: Literal["higher", "lower"] | None = None


class SelectedResponseContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["selected-response-v1"] = SELECTED_RESPONSE_VERSION
    operation: Literal[
        "index_percentage_increase",
        "economic_shift",
        "gross_profit",
        "after_tax_profit",
        "highest_productivity",
        "performance_statements",
        "break_even_change",
        "strategic_drift",
    ]
    inputs: dict[str, Decimal | str] = Field(default_factory=dict)
    rows: list[SelectedResponseRow] = Field(default_factory=list)
    unit: Literal["index", "effect", "GBPm", "ratio", "classification"]
    decimal_places: int = Field(ge=0, le=4)


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
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != 4 or any(
        not isinstance(choice, str) or not choice.strip() for choice in choices
    ):
        raise ValueError("selected-response contract requires four choices")

    numeric_results: dict[str, float] = {}
    if contract.operation == "index_percentage_increase":
        if set(contract.inputs) != {"base", "rate_percent"}:
            raise ValueError("index selected response has incomplete public inputs")
        base = _decimal(contract.inputs["base"])
        rate = _decimal(contract.inputs["rate_percent"])
        if not base.is_finite() or not rate.is_finite() or base <= 0:
            raise ValueError("index selected response inputs must be finite and positive")
        quantum = Decimal(1).scaleb(-contract.decimal_places)
        expected = (base * (Decimal(1) + rate / Decimal(100))).quantize(
            quantum,
            rounding=ROUND_HALF_UP,
        )
        parsed = [_plain_decimal(choice) for choice in choices]
        if any(value is None for value in parsed):
            raise ValueError("index selected-response options must be plain index values")
        if len(set(parsed)) != 4 or sum(value == expected for value in parsed) != 1:
            raise ValueError("selected response must have exactly one semantic option")
        expected_text = choices[parsed.index(expected)].strip()
        steps = ["Multiply the candidate-visible base index by one plus the percentage rate."]
        numeric_results = {"selected_value": float(expected)}
    elif contract.operation == "economic_shift":
        values = {key: str(value) for key, value in contract.inputs.items()}
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
            }[(curve, direction, scope)]
        except KeyError as error:
            raise ValueError("economic shift has invalid public inputs") from error
        steps = ["Infer the new equilibrium from the candidate-visible curve shift."]
    elif contract.operation in {"gross_profit", "after_tax_profit"}:
        names = (
            {"revenue", "cost_of_sales"}
            if contract.operation == "gross_profit"
            else {"revenue", "cost_of_sales", "operating_expenses", "taxation"}
        )
        if set(contract.inputs) != names:
            raise ValueError("profit selected response has incomplete public inputs")
        numbers = {key: _decimal(value) for key, value in contract.inputs.items()}
        expected = numbers["revenue"] - numbers["cost_of_sales"]
        if contract.operation == "after_tax_profit":
            expected -= numbers["operating_expenses"] + numbers["taxation"]
        expected_text = _money_choice(choices, expected, contract.decimal_places)
        numeric_results = {"selected_value": float(expected)}
        steps = ["Subtract the candidate-visible costs from revenue in the requested order."]
    elif contract.operation == "highest_productivity":
        if len(contract.rows) < 2 or any(
            row.output is None or row.employees is None or row.employees <= 0
            for row in contract.rows
        ):
            raise ValueError("productivity selected response has incomplete public rows")
        ratios = {row.label: row.output / row.employees for row in contract.rows}
        highest = max(ratios.values())
        winners = [label for label, value in ratios.items() if value == highest]
        if len(winners) != 1:
            raise ValueError("productivity selected response must have one highest row")
        expected_text = winners[0]
        numeric_results = {label: float(value) for label, value in ratios.items()}
        steps = ["Divide each candidate-visible output by its employee count and compare."]
    elif contract.operation == "performance_statements":
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
        if set(contract.inputs) != names:
            raise ValueError("break-even selected response has incomplete public inputs")
        values = {key: _decimal(value) for key, value in contract.inputs.items()}
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
        values = {key: str(value).casefold() for key, value in contract.inputs.items()}
        if values != {"external_change": "high", "strategic_change": "low"}:
            raise ValueError("unsupported strategic-change classification")
        expected_text = "Strategic drift"
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
    pattern = re.compile(r"^£([+-]?(?:\d+(?:\.\d*)?|\.\d+))m$")
    parsed = []
    for choice in choices:
        match = pattern.fullmatch(choice.strip())
        parsed.append(Decimal(match.group(1)) if match else None)
    if (
        any(value is None for value in parsed)
        or len(set(parsed)) != 4
        or sum(value == expected for value in parsed) != 1
    ):
        raise ValueError("selected response must have exactly one semantic option")
    return choices[parsed.index(expected)].strip()


def _better_than_target(row: SelectedResponseRow) -> bool:
    if row.actual is None or row.target is None or row.better_when is None:
        raise ValueError("performance row is incomplete")
    return row.actual > row.target if row.better_when == "higher" else row.actual < row.target


def _worse_than_target(row: SelectedResponseRow) -> bool:
    return not _better_than_target(row) and row.actual != row.target
