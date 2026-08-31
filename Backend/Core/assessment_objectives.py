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
    computational: bool = False

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
        """Reject unsupported labels in new or persisted qualified contracts."""
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

    def task_operation(self, raw: dict[str, Any], command: str, kind: str) -> str:
        """CS tasks are not classified from their tariff or AO3 label alone."""
        explicit = raw.get("task_operation") or (raw.get("authoring_context") or {}).get("task_operation")
        if explicit:
            return str(explicit)
        prompt = " ".join(str(raw.get("prompt", "")).casefold().split())
        objectives = raw.get("assessment_objectives") or {}
        # Reference tasks may request artefacts without an imperative verb.
        if "program source code" in prompt:
            return "program"
        if "screen capture" in prompt and "test" in prompt:
            return "judge"
        if command == "trace" or kind == "trace" or "trace table" in prompt or (
            command in {"show", "give", "state", "complete"}
            and re.search(r"\b(contents|output|values|pointers?)\b.*\b(after|execut|following)", prompt)
        ):
            return "trace"
        if command in {"design", "develop"}:
            return "design" if command == "design" else "program"
        if command == "draw" and re.search(r"\b(circuit|logic|algorithm)\b", prompt):
            return "design" if not objectives or objectives.get("AO3") else "analyse"
        if kind == "table" or (command == "complete" and "table" in prompt
                                and not re.search(r"\b(truth|binary|denary|hexadecimal)\b", prompt)):
            return "analyse"
        if kind == "programming" or (
            command in {"write", "complete"} and re.search(
                r"\b(program|code|function|subroutine|algorithm|pseudocode|query|statement|add_record|adjusted_value|print_report)\b", prompt
            )
        ):
            return "program"
        contextual = bool(objectives.get("AO2")) or (not objectives and bool(re.search(
            r"\b(this|these|shown|given|supplied|following|above|below|figure|fig|table|line)\b", prompt)))
        if command in {"calculate", "convert", "simplify", "complete", "determine"}:
            if command == "complete" and re.search(r"\b(fsm|transition|classification|hierarchy)\b", prompt):
                return "analyse"
            return "transform"
        if command in {"discuss", "evaluate", "assess", "justify", "recommend"}:
            return "judge"
        if command in {"state", "identify", "select", "name", "give", "define"}:
            return "analyse" if contextual else "retrieve"
        if command in {"describe", "outline"}:
            return "analyse" if contextual else "describe"
        return "analyse" if contextual else "explain"

    def response_mode(self, operation: str, command: str, marks: int) -> str:
        return {
            "design": "computational-design", "program": "programming",
            "trace": "algorithm-trace", "analyse": "computational-analysis",
            "transform": "multi-stage-calculation" if marks >= 4 else "calculation",
            "retrieve": "selected-response" if command == "select" else "recall",
            "judge": "extended-evaluation",
            "describe": "constructed-response",
            "explain": "structured-reasoning" if command == "explain" else "constructed-response",
        }.get(operation, "constructed-response")


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
COMPUTER_SCIENCE_OBJECTIVES = ObjectivePolicy(
    version="computer-science-aqa7517-ocrh446-objectives-v1",
    meanings={
        "AO1": "knowledge and understanding of computing principles, concepts, algorithms and representation",
        "AO2": "application of computing principles to supplied data and analysis of problems in computational terms",
        "AO3": "design, programming and evaluation of systems that solve problems; reasoned judgements only where the task asks for evaluation",
    },
    analysis_objectives=(),
    judgement_objectives=(),
    explicit_allocations=True,
    computational=True,
)


def objective_policy_for(*identifiers: str) -> ObjectivePolicy:
    """Resolve family IDs, subject names or qualification codes."""
    identity = " ".join(identifiers).casefold()
    # Explicit board identities precede subject aliases. Cambridge 9618 is an
    # unqualified configured preview; its placeholder policy is Task 9 debt,
    # not evidence that the AQA/OCR policy or its old AO4 allocation is valid.
    if "cambridge" in identity or "9618" in identity:
        return GENERAL_OBJECTIVES
    if "accounting" in identity or "7127" in identity:
        return ACCOUNTING_OBJECTIVES
    if any(token in identity for token in ("computer science", "computer-science", "computer_science", "7517", "h446")):
        return COMPUTER_SCIENCE_OBJECTIVES
    return GENERAL_OBJECTIVES
