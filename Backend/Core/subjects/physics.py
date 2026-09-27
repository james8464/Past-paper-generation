from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from Backend.Core.subject_contracts import SubjectValidation


def compare_physical_answers(
    candidate: str,
    expected: str,
    candidate_unit: str,
    expected_unit: str,
    *,
    significant_figures: int | None = None,
    tolerance: Decimal = Decimal("0"),
) -> bool:
    if _normalise_unit(candidate_unit) != _normalise_unit(expected_unit):
        return False
    try:
        candidate_value = Decimal(candidate)
        expected_value = Decimal(expected)
    except InvalidOperation:
        return False
    if abs(candidate_value - expected_value) > tolerance:
        return False
    return significant_figures is None or _significant_figures(candidate) == significant_figures


class PhysicsPlugin:
    id = "physics"

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        diagnostics: list[str] = []
        if not str(item.get("question", "")).strip():
            diagnostics.append("question text is required")
        marks = item.get("marks")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")
        if item.get("answer") in (None, ""):
            diagnostics.append("a canonical physics answer is required")
        if not str(item.get("unit", "")).strip():
            diagnostics.append("a canonical unit is required")
        if item.get("answer_kind") == "uncertainty" and item.get("uncertainty") in (
            None,
            "",
        ):
            diagnostics.append("uncertainty items require a canonical uncertainty")
        if item.get("item_kind") == "required-practical" and not item.get(
            "required_practical_id"
        ):
            diagnostics.append("required-practical items need a practical ID")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        return {"value": item["answer"], "unit": item["unit"]}

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict) or specification.get("kind") not in {
            "apparatus",
            "circuit",
            "field",
            "graph",
            "ray",
            "vector",
            "wave",
        }:
            raise ValueError("unsupported physics visual kind")
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
            "answer_kind": str(payload.get("answer_kind", "numeric")),
        }


def _normalise_unit(value: str) -> str:
    return value.strip().replace(" ", "").replace("−", "-").replace("²", "^2")


def _significant_figures(value: str) -> int:
    compact = value.strip().lower()
    mantissa = compact.split("e", 1)[0].lstrip("+-")
    digits = mantissa.replace(".", "").lstrip("0")
    return len(digits) if digits else 1
