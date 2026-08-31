"""Closed numeric output contracts, distinct from examiner credit metadata."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

NUMERIC_INTEGRITY_VERSION = "closed-numeric-v1"
NUMBER = r"[−+\-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
MONEY = rf"(?P<value>[−+\-]?£{NUMBER})"


class NumericOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    decimal_places: int = Field(ge=0, le=12)
    scheme_pattern: str = Field(min_length=1)
    sign: Literal["signed", "variance"] = "signed"


class CheckedNumericOutput(NumericOutput):
    value: str


class CheckedTextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str
    value: str
    scheme_pattern: str


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
        elif check.unit in {"GBPm", "%"}:
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
    return bool(
        re.match(
            r"(?:$|[\r\n]|[.,;](?!\d)|\)|\(own figure\)|(?:and|to)\b)",
            suffix,
            re.IGNORECASE,
        )
    )


def check_published_outputs(checks: list[CheckedNumericOutput], text: str) -> list[str]:
    """Bind each asserted result to its role in the published working, never a number bag.

    Patterns are code-owned field selectors, not expected answer strings. Some
    printed intermediate units are supplied by their row/column heading; final
    canonical answers always include the full unit.
    """
    errors = []
    for check in checks:
        matches = list(
            re.finditer(check.scheme_pattern, text, re.IGNORECASE | re.MULTILINE)
        )
        if not matches:
            errors.append(f"published scheme is missing numeric role {check.role}")
            continue
        expected = rounded(Decimal(check.value), check.decimal_places)
        for match in matches:
            if not _published_unit_boundary(check, text[match.end("value") :]):
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
