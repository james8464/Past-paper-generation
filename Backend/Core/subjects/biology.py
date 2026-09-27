from __future__ import annotations

from typing import Any

from Backend.Core.subject_contracts import SubjectValidation


class BiologyPlugin:
    id = "biology"

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        diagnostics: list[str] = []
        if not str(item.get("question", "")).strip():
            diagnostics.append("question text is required")
        marks = item.get("marks")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")
        if not str(item.get("answer", "")).strip():
            diagnostics.append("a canonical biological answer is required")
        if item.get("item_kind") == "required-practical":
            if not str(item.get("required_practical_id", "")).strip():
                diagnostics.append("required-practical items need a practical ID")
            if item.get("data") is not None and not str(
                item.get("data_provenance", "")
            ).strip():
                diagnostics.append("practical data needs deterministic provenance")
        if item.get("item_kind") == "magnification":
            for field in ("image_size", "actual_size", "unit"):
                if item.get(field) in (None, ""):
                    diagnostics.append(f"magnification items require {field}")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        return item["answer"]

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict) or specification.get("kind") not in {
            "biological-drawing",
            "data-table",
            "graph",
            "microscope-field",
            "pedigree",
        }:
            raise ValueError("unsupported biology visual kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict) or not scheme.get("mark_points"):
            return SubjectValidation(False, ("mark scheme requires mark points",))
        if len(scheme["mark_points"]) < int(item.get("marks", 0)):
            return SubjectValidation(False, ("mark scheme has too few observable points",))
        return SubjectValidation(True)

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "topic": str(payload.get("topic", "unknown")),
            "practical": str(payload.get("required_practical_id", "none")),
        }
