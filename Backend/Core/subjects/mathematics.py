from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

import sympy
from sympy.parsing.sympy_parser import parse_expr

from Backend.Core.subject_plugins import SubjectValidation

_SAFE_EXPRESSION = re.compile(r"^[A-Za-z0-9_+\-*/^()., ]+$")
_UNIT_ALIASES = {
    "ms^-2": "m/s^2",
    "ms−2": "m/s^2",
    "m s^-2": "m/s^2",
    "m s−2": "m/s^2",
    "m/s²": "m/s^2",
    "ms^-1": "m/s",
    "m s^-1": "m/s",
    "m/s¹": "m/s",
}


@dataclass(frozen=True)
class MathematicalAnswer:
    expression: str
    unit: str | None = None
    tolerance: Decimal = Decimal("0")
    significant_figures: int | None = None


@dataclass(frozen=True)
class AnswerComparison:
    equivalent: bool
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarkingRule:
    code: str
    description: str
    depends_on: tuple[str, ...] = ()
    follow_through: bool = False


@dataclass(frozen=True)
class MarkAward:
    awarded: tuple[str, ...]
    total: int

    @classmethod
    def from_observed(
        cls,
        rules: tuple[MarkingRule, ...],
        observed: set[str],
    ) -> MarkAward:
        known = {rule.code for rule in rules}
        unknown = observed - known
        if unknown:
            raise ValueError(f"unknown marking rule: {sorted(unknown)[0]}")
        for rule in rules:
            if rule.code not in observed or rule.follow_through:
                continue
            for dependency in rule.depends_on:
                if dependency not in observed:
                    raise ValueError(f"{rule.code} depends on {dependency}")
        ordered = tuple(rule.code for rule in rules if rule.code in observed)
        return cls(awarded=ordered, total=len(ordered))


def compare_mathematical_answers(
    candidate: MathematicalAnswer,
    expected: MathematicalAnswer,
) -> AnswerComparison:
    candidate_unit = _normalise_unit(candidate.unit)
    expected_unit = _normalise_unit(expected.unit)
    if candidate_unit != expected_unit:
        return AnswerComparison(
            False,
            (f"unit {candidate.unit or 'none'} does not match {expected.unit or 'none'}",),
        )

    try:
        left = _parse(candidate.expression)
        right = _parse(expected.expression)
    except (SyntaxError, TypeError, ValueError) as error:
        return AnswerComparison(False, (f"invalid mathematical expression: {error}",))

    difference = sympy.simplify(left - right)
    if difference == 0:
        return AnswerComparison(True)

    if not (left.is_number and right.is_number):
        return AnswerComparison(False, ("expressions are not symbolically equivalent",))
    implicit_float_tolerance = (
        Decimal("1e-15") if left.has(sympy.Float) or right.has(sympy.Float) else Decimal(0)
    )
    tolerance = max(candidate.tolerance, expected.tolerance, implicit_float_tolerance)
    numeric_difference = abs(Decimal(str(sympy.N(difference, 30))))
    if numeric_difference <= tolerance:
        return AnswerComparison(True)
    return AnswerComparison(
        False,
        (f"numeric difference {numeric_difference} exceeds tolerance {tolerance}",),
    )


def round_to_significant_figures(value: Decimal, figures: int) -> Decimal:
    if figures <= 0:
        raise ValueError("significant figures must be positive")
    if value == 0:
        return Decimal(0)
    with localcontext() as context:
        context.prec = max(figures, 1)
        exponent = value.copy_abs().adjusted() - figures + 1
        quantum = Decimal(1).scaleb(exponent)
        return value.quantize(quantum)


class MathematicsPlugin:
    id = "mathematics"

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        diagnostics: list[str] = []
        if not str(item.get("question", "")).strip():
            diagnostics.append("question text is required")
        marks = item.get("marks")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")
        answer = str(item.get("answer", "")).strip()
        if not answer:
            diagnostics.append("a canonical mathematical answer is required")
        else:
            try:
                _parse(answer, tuple(str(value) for value in item.get("variables", ())))
            except (SyntaxError, TypeError, ValueError) as error:
                diagnostics.append(f"invalid canonical answer: {error}")
        try:
            rules = _marking_rules(item.get("marking_rules", ()))
            if rules and len(rules) != marks:
                diagnostics.append("marking-rule count must equal item marks")
        except ValueError as error:
            diagnostics.append(str(error))
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        variables = tuple(str(value) for value in item.get("variables", ()))
        return sympy.simplify(_parse(str(item["answer"]), variables))

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict):
            raise ValueError("mathematical visual must be an object")
        if specification.get("kind") not in {
            "coordinate-grid",
            "distribution",
            "geometry",
            "plot",
            "statistical-chart",
            "vector",
        }:
            raise ValueError("unsupported mathematical visual kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict):
            return SubjectValidation(False, ("mark scheme must be an object",))
        try:
            expected = _marking_rules(item.get("marking_rules", ()))
            actual = _marking_rules(scheme.get("marking_rules", ()))
        except ValueError as error:
            return SubjectValidation(False, (str(error),))
        if actual != expected:
            return SubjectValidation(False, ("marking rules do not match the item contract",))
        return SubjectValidation(True)

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "topic": str(payload.get("topic", "unknown")),
            "answer_form": str(payload.get("answer_form", "expression")),
        }


def _parse(expression: str, variables: tuple[str, ...] = ()) -> sympy.Expr:
    normalized = expression.replace("^", "**").strip()
    if not normalized or not _SAFE_EXPRESSION.fullmatch(normalized):
        raise ValueError("expression contains unsupported characters")
    inferred_names = set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", normalized))
    inferred_names -= {"sin", "cos", "tan", "log", "exp", "sqrt", "pi", "E"}
    declared_names = set(variables) or inferred_names
    local_symbols = {name: sympy.Symbol(name, real=True) for name in declared_names}
    local_symbols.update(
        {
            "sin": sympy.sin,
            "cos": sympy.cos,
            "tan": sympy.tan,
            "log": sympy.log,
            "exp": sympy.exp,
            "sqrt": sympy.sqrt,
            "pi": sympy.pi,
            "E": sympy.E,
        }
    )
    parsed = parse_expr(
        normalized,
        local_dict=local_symbols,
        global_dict={
            "Symbol": sympy.Symbol,
            "Integer": sympy.Integer,
            "Float": sympy.Float,
            "Rational": sympy.Rational,
        },
        evaluate=True,
    )
    if not isinstance(parsed, sympy.Expr):
        raise ValueError("expression does not produce a mathematical value")
    undeclared = {str(symbol) for symbol in parsed.free_symbols} - set(variables)
    if variables and undeclared:
        raise ValueError(f"undeclared symbol: {sorted(undeclared)[0]}")
    return parsed


def _marking_rules(value: Any) -> tuple[MarkingRule, ...]:
    if value in (None, ()):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("marking rules must be a list")
    rules: list[MarkingRule] = []
    for payload in value:
        if not isinstance(payload, dict):
            raise ValueError("each marking rule must be an object")
        code = str(payload.get("code", "")).strip()
        description = str(payload.get("description", "")).strip()
        if not code or not description:
            raise ValueError("each marking rule needs a code and description")
        rules.append(
            MarkingRule(
                code=code,
                description=description,
                depends_on=tuple(str(item) for item in payload.get("depends_on", ())),
                follow_through=bool(payload.get("follow_through", False)),
            )
        )
    codes = [rule.code for rule in rules]
    if len(set(codes)) != len(codes):
        raise ValueError("marking-rule codes must be unique")
    known = set(codes)
    for rule in rules:
        missing = set(rule.depends_on) - known
        if missing:
            raise ValueError(f"{rule.code} has unknown dependency {sorted(missing)[0]}")
    return tuple(rules)


def _normalise_unit(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.strip().split())
    return _UNIT_ALIASES.get(compact, compact)
