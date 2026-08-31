"""Closed numeric output contracts, distinct from examiner credit metadata."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

NUMERIC_INTEGRITY_VERSION = "closed-numeric-v2"
NUMBER = r"[−+\-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
MONEY = rf"(?P<value>[−+\-]?£{NUMBER})"


class NumericOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str = Field(min_length=1)
    unit: Literal[
        "GBP",
        "GBPm",
        "GBP/unit",
        "GBP/kg",
        "GBP/setup",
        "GBP/order",
        "GBP/scarce hour",
        "%",
        "1",
        "bytes",
        "percentage points",
        "index points",
        "consumer units",
    ]
    decimal_places: int = Field(ge=0, le=12)
    scheme_pattern: str = Field(min_length=1)
    scheme_ending: str = r"(?:\(own figure\)[ \t]*)?[.,;]?"
    sign: Literal["signed", "variance"] = "signed"


class CheckedNumericOutput(NumericOutput):
    value: str


class CheckedTextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str
    value: str
    scheme_pattern: str
    whole_statement: bool = False


def rounded(value: Decimal, places: int) -> Decimal:
    if not value.is_finite():
        raise ValueError("numeric output must be finite")
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def display(value: Decimal, output: NumericOutput) -> str:
    value = rounded(value, output.decimal_places)
    suffix = ""
    if output.sign == "variance":
        suffix = " adverse" if value < 0 else " favourable" if value > 0 else " nil"
        value = abs(value)
    number = f"{abs(value):,.{output.decimal_places}f}"
    sign = "−" if value < 0 else ""
    if output.unit.startswith("GBP"):
        unit = output.unit.removeprefix("GBP")
        return f"{sign}£{number}{unit}{suffix}"
    return f"{sign}{number}{'' if output.unit in {'%', '1'} else ' '}{'' if output.unit == '1' else output.unit}{suffix}"


def numeric_result(
    values: dict[str, Decimal | int | float],
    outputs: list[NumericOutput],
    steps: list[str],
) -> dict[str, Any]:
    if set(values) != {output.role for output in outputs}:
        raise ValueError("numeric output contract must cover every computed role")
    checks = [
        CheckedNumericOutput(**output.model_dump(), value=str(values[output.role]))
        for output in outputs
    ]
    answers = {check.role: display(Decimal(check.value), check) for check in checks}
    return {
        "answer": answers,
        "mark_points": answers,
        "steps": steps,
        "numeric_results": {role: float(value) for role, value in values.items()},
        "numeric_checks": [check.model_dump() for check in checks],
        "evidence_ids": [],
    }


def _published_unit_boundary(check: CheckedNumericOutput, suffix: str) -> bool:
    """Accept only the contract's unit and the current templates' result endings.

    A regex-selected numeric prefix is not a complete quantity: ``27.90e6`` and
    ``£27.90 million`` must not inherit approval for ``£27.90/unit``. Unknown
    quantity notation fails closed, including uncontracted currency words.
    """
    suffix = suffix.lstrip(" \t")
    if check.unit == "GBPm":
        unit_pattern = r"m\b"
    elif check.unit == "%":
        unit_pattern = "%"
    elif check.unit in {"bytes", "percentage points", "index points", "consumer units"}:
        unit_pattern = re.escape(check.unit) + r"\b"
    elif check.unit == "1":
        unit_pattern = r":1\b"
    elif check.unit.startswith("GBP/"):
        unit_pattern = rf"(?:per[ \t]+|/){re.escape(check.unit[4:])}\b"
    else:
        unit_pattern = ""
    if unit_pattern:
        unit = re.match(unit_pattern, suffix, re.IGNORECASE)
        if unit:
            suffix = suffix[unit.end() :].lstrip(" \t")
        elif check.unit in {"GBPm", "%", "bytes", "percentage points", "index points", "consumer units"}:
            return False
        # GBP rates can get their denominator from the explicitly selected
        # row heading. An explicit contradictory denominator is never ignored.
    if check.unit == "1" and suffix.startswith("(accept "):
        alternative = re.match(rf"\(accept ({NUMBER}) without :1\)", suffix)
        if not alternative or Decimal(alternative.group(1)) != rounded(
            Decimal(check.value), check.decimal_places
        ):
            return False
        suffix = suffix[alternative.end() :].lstrip(" \t")
    if check.sign == "variance":
        direction = re.match(r"(?:favourable|adverse|nil)\b", suffix, re.IGNORECASE)
        if not direction:
            return False
        suffix = suffix[direction.end() :].lstrip(" \t")
    return re.fullmatch(check.scheme_ending, suffix.strip(), re.IGNORECASE) is not None


def check_published_outputs(
    checks: list[CheckedNumericOutput], text: str | list[str]
) -> list[str]:
    """Bind each asserted result to its role in the published working, never a number bag.

    Patterns are code-owned field selectors, not expected answer strings. Some
    printed intermediate units are supplied by their row/column heading; final
    canonical answers always include the full unit.
    """
    statements = [text] if isinstance(text, str) else text
    errors = []
    for check in checks:
        matches = [
            (statement, match)
            for statement in statements
            for match in re.finditer(
                check.scheme_pattern, statement, re.IGNORECASE | re.MULTILINE
            )
        ]
        if not matches:
            errors.append(f"published scheme is missing numeric role {check.role}")
            continue
        expected = rounded(Decimal(check.value), check.decimal_places)
        for statement, match in matches:
            suffix = statement[match.end("value") :]
            if not _published_unit_boundary(check, suffix):
                errors.append(
                    f"published scheme has unsupported unit or scale at {check.role}"
                )
            token = (
                match.group("value").replace("£", "").replace(",", "").replace("−", "-")
            )
            actual = Decimal(token)
            if check.sign == "variance":
                direction = match.groupdict().get("direction", "").casefold()
                if actual < 0 or direction not in {"adverse", "favourable", "nil"}:
                    errors.append(
                        f"published scheme has invalid variance direction at {check.role}"
                    )
                    continue
                actual *= -1 if direction == "adverse" else 1
                if direction == "nil" and actual != 0:
                    errors.append(
                        f"published scheme has invalid nil variance at {check.role}"
                    )
            if actual != expected:
                errors.append(
                    f"published scheme disagrees at numeric role {check.role}"
                )
    return errors


def check_numeric_alternatives(
    checks: list[CheckedNumericOutput | CheckedTextOutput], alternatives: list[str]
) -> list[str]:
    """Unconditional alternatives need a unique role and a complete quantity.

    A single selected point can supply the role. Multi-output/general alternatives
    must name it explicitly. Conditional own-figure credit belongs in its separate
    follow-through field, never in this unconditional acceptance list.
    """
    errors = []
    for alternative in alternatives:
        quantity = re.sub(
            r"^(?:Accept|Allow)\s+", "", alternative.strip(), flags=re.IGNORECASE
        )
        selected = checks
        if ":" in quantity and not re.fullmatch(rf"{NUMBER}:1[.]?", quantity):
            role, quantity = quantity.split(":", 1)
            selected = [check for check in checks if check.role == role.strip()]
            quantity = quantity.strip()
        if len(selected) != 1 or not _equivalent_quantity(selected[0], quantity):
            errors.append(
                "unsupported or incorrect numeric alternative: " + alternative
            )
    return errors


def _equivalent_quantity(check: CheckedNumericOutput | CheckedTextOutput, quantity: str) -> bool:
    """Small explicit grammar: GBP/pence, declared denominator, percent, ratio."""
    if isinstance(check, CheckedTextOutput):
        # Encoded results preserve their complete width/order; only case and
        # terminal punctuation vary. Never accept a prefix or an extra claim.
        return quantity.removesuffix(".").strip().casefold() == check.value.casefold()
    expected = rounded(Decimal(check.value), check.decimal_places)
    if check.unit.startswith("GBP"):
        numerator = rf"(?:(?P<major>[−+\-]?£{NUMBER})(?P<million>m)?|(?P<minor>{NUMBER})\s*(?:p|pence))"
        denominator = (
            rf"\s*(?:per\s+|/){re.escape(check.unit[4:])}"
            if check.unit.startswith("GBP/")
            else ""
        )
        direction = (
            r"\s+(?P<direction>favourable|adverse|nil)"
            if check.sign == "variance"
            else ""
        )
        match = re.fullmatch(
            numerator + denominator + direction + r"[.]?", quantity, re.IGNORECASE
        )
        if not match:
            return False
        major = match.group("major")
        token = major.replace("£", "") if major else match.group("minor")
        actual = Decimal(token.replace(",", "").replace("−", "-"))
        actual *= (
            Decimal(1_000_000)
            if match.group("million")
            else Decimal(1)
            if major
            else Decimal("0.01")
        )
        if check.unit == "GBPm":
            expected *= 1_000_000
        if check.sign == "variance":
            if actual < 0:
                return False
            sign = match.group("direction").casefold()
            actual *= -1 if sign == "adverse" else 1
            if sign == "nil" and actual != 0:
                return False
    else:
        unit = r"(?:%|\s+percent)" if check.unit == "%" else r"(?::1)?" if check.unit == "1" else r"\s+" + re.escape(check.unit)
        match = re.fullmatch(rf"(?P<value>{NUMBER}){unit}[.]?", quantity, re.IGNORECASE)
        if not match:
            return False
        actual = Decimal(match.group("value").replace(",", "").replace("−", "-"))
    return actual == expected


def percentage_change_context(start: float, end: float) -> dict[str, Any]:
    """Candidate chart endpoints and the requested one-decimal percentage output."""
    return {
        "preserve_prompt": True,
        "calculation_expression": "(end - start) / start * 100",
        "calculation_variables": {"start": start, "end": end},
        "calculation_input_units": {"start": "index", "end": "index"},
        "calculation_output": NumericOutput(
            role="percentage_change",
            unit="%",
            decimal_places=1,
            scheme_pattern=rf"^(?:Correct )?Answer:\s*(?P<value>{NUMBER})%",
        ).model_dump(),
    }
