from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from Backend.Core.subject_plugins import SubjectValidation


@dataclass(frozen=True)
class Formula:
    source: str
    elements: dict[str, int]

    @classmethod
    def parse(cls, value: str) -> Formula:
        compact = value.strip().replace(" ", "")
        if not compact:
            raise ValueError("chemical formula is empty")
        tokens = re.findall(r"[A-Z][a-z]?|\d+|[()]", compact)
        if "".join(tokens) != compact:
            raise ValueError(f"unsupported chemical formula: {value}")
        elements, index = _parse_group(tokens, 0, expects_closing=False)
        if index != len(tokens):
            raise ValueError(f"unmatched closing bracket in {value}")
        return cls(compact, dict(elements))


def equation_is_balanced(value: str) -> bool:
    arrow = "->" if "->" in value else "→" if "→" in value else None
    if arrow is None:
        raise ValueError("chemical equation requires an arrow")
    left, right = value.split(arrow, 1)
    return _equation_side(left) == _equation_side(right)


class ChemistryPlugin:
    id = "chemistry"

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
            diagnostics.append("a canonical chemistry answer is required")
        elif item.get("answer_kind") == "chemical-equation":
            try:
                if not equation_is_balanced(answer):
                    diagnostics.append("canonical chemical equation must be balanced")
            except ValueError as error:
                diagnostics.append(str(error))
        if item.get("item_kind") == "required-practical" and not item.get(
            "required_practical_id"
        ):
            diagnostics.append("required-practical items need a practical ID")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        return item["answer"]

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict) or specification.get("kind") not in {
            "apparatus",
            "energy-profile",
            "mechanism",
            "molecule",
            "spectrum",
        }:
            raise ValueError("unsupported chemistry visual kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict) or not scheme.get("mark_points"):
            return SubjectValidation(False, ("mark scheme requires mark points",))
        return SubjectValidation(True)

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "topic": str(payload.get("topic", "unknown")),
            "answer_kind": str(payload.get("answer_kind", "text")),
        }


def _parse_group(
    tokens: list[str],
    index: int,
    *,
    expects_closing: bool,
) -> tuple[Counter[str], int]:
    result: Counter[str] = Counter()
    while index < len(tokens):
        token = tokens[index]
        if token == ")":
            return result, index + 1
        if token == "(":
            inner, index = _parse_group(tokens, index + 1, expects_closing=True)
            if index > len(tokens):
                raise ValueError("unmatched opening bracket")
            multiplier, index = _multiplier(tokens, index)
            for element, count in inner.items():
                result[element] += count * multiplier
            continue
        if token.isdigit():
            raise ValueError("unexpected coefficient inside formula")
        multiplier, index = _multiplier(tokens, index + 1)
        result[token] += multiplier
    if expects_closing:
        raise ValueError("unmatched opening bracket")
    return result, index


def _multiplier(tokens: list[str], index: int) -> tuple[int, int]:
    if index < len(tokens) and tokens[index].isdigit():
        return int(tokens[index]), index + 1
    return 1, index


def _equation_side(value: str) -> Counter[str]:
    result: Counter[str] = Counter()
    for raw in value.split("+"):
        species = raw.strip()
        match = re.fullmatch(r"(?:(\d+)\s*)?(.+)", species)
        if match is None:
            raise ValueError(f"invalid equation species: {species}")
        coefficient = int(match.group(1) or 1)
        formula = Formula.parse(match.group(2))
        for element, count in formula.elements.items():
            result[element] += coefficient * count
    return result
