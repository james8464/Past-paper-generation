"""Subject meaning for AO labels, independent of item tariffs and renderers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObjectivePolicy:
    version: str
    meanings: dict[str, str]
    analysis_objectives: tuple[str, ...] = ("AO3",)
    judgement_objectives: tuple[str, ...] = ("AO4",)
    explicit_allocations: bool = False

    def operations(self, objectives: dict[str, int], command: str) -> tuple[bool, bool]:
        judgement_commands = {
            "advise",
            "assess",
            "discuss",
            "evaluate",
            "justify",
            "recommend",
        }
        analysis_commands = judgement_commands | {
            "analyse",
            "analyze",
            "examine",
            "explain",
            "prove",
            "show",
            "verify",
        }
        return (
            any(objectives.get(ao, 0) > 0 for ao in self.analysis_objectives)
            or command in analysis_commands,
            any(objectives.get(ao, 0) > 0 for ao in self.judgement_objectives)
            or command in judgement_commands,
        )

    def guidance(self) -> str:
        meanings = " ".join(
            f"{ao}: {meaning}." for ao, meaning in self.meanings.items()
        )
        return (
            "Assessment-objective policy: "
            + meanings
            + " Use only the item's declared objectives. Infer the required operation "
            "from the command and actual task; do not require a judgement for every "
            "short analytical explanation. Check that the credited work demonstrates "
            "the allocated objective, not merely that totals add up. "
        )

    def validate(self, value: Any) -> None:
        """Reject unsupported labels in new or persisted Accounting contracts."""
        if not self.explicit_allocations:
            return
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "assessment_objectives" and isinstance(child, dict):
                    invalid = set(child) - self.meanings.keys()
                    if invalid:
                        raise ValueError(
                            f"unsupported assessment objective: {sorted(invalid)}"
                        )
                self.validate(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                self.validate(child)
        elif isinstance(value, str):
            invalid = set(re.findall(r"\bAO\d+\b", value, re.IGNORECASE))
            invalid = {label.upper() for label in invalid} - self.meanings.keys()
            if invalid:
                raise ValueError(f"unsupported assessment objective: {sorted(invalid)}")

    def fingerprint(self, objectives: dict[str, int], command: str, kind: str) -> str:
        if not self.explicit_allocations:
            return ""
        payload = [self.version, self.meanings, objectives, command, kind]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


GENERAL_OBJECTIVES = ObjectivePolicy(
    version="general-objectives-v1",
    meanings={
        "AO1": "accurate subject knowledge and understanding",
        "AO2": "explicit application to the supplied source or context",
        "AO3": "a developed causal link within a complete chain of analysis",
        "AO4": "a supported comparative judgement or conclusion",
    },
)
ACCOUNTING_OBJECTIVES = ObjectivePolicy(
    version="aqa-accounting-7127-objectives-v1",
    meanings={
        "AO1": "knowledge and understanding of accounting principles, including familiar accounting techniques and calculations",
        "AO2": "application of accounting principles and techniques to the particular data or situation",
        "AO3": "analysis and evaluation of accounting data, including supported judgements and conclusions when required by the task",
    },
    judgement_objectives=(),
    explicit_allocations=True,
)


def objective_policy_for(*identifiers: str) -> ObjectivePolicy:
    """Resolve family IDs, subject names or qualification codes; CS follows separately."""
    identity = " ".join(identifiers).casefold()
    if "accounting" in identity or "7127" in identity:
        return ACCOUNTING_OBJECTIVES
    return GENERAL_OBJECTIVES
