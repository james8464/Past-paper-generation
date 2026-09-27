from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Backend.Core.subject_contracts import SubjectValidation

_EVIDENCE_FIELDS = {
    "psychology": ("study",),
    "geography": ("case_study", "source_extract"),
    "sociology": ("theorist", "source_extract"),
    "history": ("interpretation", "source_extract"),
    "english-literature": ("extract", "quotation"),
}


@dataclass(frozen=True)
class EssaySubjectPlugin:
    id: str

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        diagnostics: list[str] = []
        if not str(item.get("question", "")).strip():
            diagnostics.append("question text is required")
        marks = item.get("marks")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")

        evidence_present = any(
            item.get(field) not in (None, "")
            for field in _EVIDENCE_FIELDS.get(self.id, ())
        )
        if evidence_present:
            diagnostics.extend(_validate_provenance(item.get("source_provenance")))

        if not str(item.get("answer", "")).strip():
            diagnostics.append("indicative content is required")
        if marks and marks >= 12 and not str(item.get("level_policy_id", "")).strip():
            diagnostics.append("extended responses require a level policy ID")
        if self.id == "english-literature" and not str(
            item.get("option_route", "")
        ).strip():
            diagnostics.append("English Literature items require an option route")
        if self.id == "history":
            chronology = item.get("chronology")
            if chronology is not None and (
                not isinstance(chronology, list) or chronology != sorted(chronology)
            ):
                diagnostics.append("history chronology must be in chronological order")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        return item["answer"]

    def render_visual(self, specification: Any) -> Any:
        allowed = {
            "psychology": {"data-table", "distribution", "study-design"},
            "geography": {"chart", "cross-section", "map", "transect"},
            "sociology": {"data-table", "source-panel"},
            "history": {"source-panel", "timeline"},
            "english-literature": {"extract-panel", "text-comparison"},
        }
        if not isinstance(specification, dict) or specification.get("kind") not in allowed.get(
            self.id, set()
        ):
            raise ValueError(f"unsupported {self.id} visual kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict):
            return SubjectValidation(False, ("mark scheme must be an object",))
        diagnostics: list[str] = []
        if not scheme.get("indicative_content"):
            diagnostics.append("mark scheme requires indicative content")
        if int(item.get("marks", 0)) >= 12:
            if scheme.get("level_policy_id") != item.get("level_policy_id"):
                diagnostics.append("mark scheme level policy does not match the item")
            if not scheme.get("levels"):
                diagnostics.append("extended response scheme requires level descriptors")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "command": str(payload.get("command", "unknown")),
            "level_policy": str(payload.get("level_policy_id", "none")),
        }


def _validate_provenance(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["quoted, study, case, or source evidence requires provenance"]
    required = ("source_id", "rights_basis", "verification_hash")
    missing = [field for field in required if not str(value.get(field, "")).strip()]
    if missing:
        return [f"source provenance is missing {', '.join(missing)}"]
    if value["rights_basis"] not in {"licensed", "public-domain", "user-supplied"}:
        return ["source provenance has an unsupported rights basis"]
    return []
