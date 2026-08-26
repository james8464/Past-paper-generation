from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarkSchemeQuality:
    points: int
    covered_objectives: tuple[str, ...]
    has_working: bool
    has_alternatives: bool
    has_credit_limits: bool
    has_levels: bool
    has_evidence_binding: bool


def validate_mark_scheme_item(item: dict[str, Any]) -> MarkSchemeQuality:
    item_id = str(item.get("id", "unknown"))
    marks = int(item.get("marks", 0))
    kind = str(item.get("kind", "")).casefold()
    command = str(item.get("command_word", "")).casefold()
    scheme = [
        str(point).strip()
        for point in item.get("mark_scheme", [])
        if str(point).strip()
    ]
    structured = [
        point
        for point in item.get("structured_mark_scheme", [])
        if isinstance(point, dict)
    ]
    depth_text = [*scheme]
    depth_text.extend(
        str(point.get("text", "")).strip()
        for point in structured
        if str(point.get("text", "")).strip()
    )
    substantive = {
        normalised
        for point in depth_text
        if (normalised := _normalise(point))
        and normalised not in {"indicative content", "answer", "guidance"}
        and "allocation within the levels grid" not in normalised
    }
    minimum_points = max(1, min(6, math.ceil(marks / 3)))
    if len(substantive) < minimum_points:
        raise ValueError(
            f"mark scheme for item {item_id} is too shallow: "
            f"{len(substantive)} substantive point(s), expected at least {minimum_points}"
        )

    combined = "\n".join(scheme).casefold()
    covered_objectives = {
        match.upper()
        for match in re.findall(r"\bAO[1-4]\b", combined, flags=re.IGNORECASE)
    }
    covered_objectives.update(
        str(point.get("assessment_objective", "")).upper()
        for point in structured
        if point.get("assessment_objective")
    )
    declared_objectives = {
        str(objective).upper()
        for objective, allocated in dict(
            item.get("assessment_objectives") or {}
        ).items()
        if int(allocated) > 0
    }
    if marks >= 5 or structured or covered_objectives:
        for objective in sorted(declared_objectives - covered_objectives):
            raise ValueError(
                f"mark scheme for item {item_id} does not cover {objective}"
            )

    has_working = _contains_any(
        combined,
        ("working", "method", "formula", "calculation", " = ", "step"),
    ) or any(point.get("depends_on") for point in structured)
    has_alternatives = _contains_any(
        combined,
        ("accept", "alternative", "equivalent", "valid route", "allow "),
    ) or any(point.get("alternatives") or point.get("allow") for point in structured)
    has_credit_limits = _contains_any(
        combined,
        (
            "do not",
            "reject",
            "ignore",
            "maximum",
            "no credit",
            "not award",
            "only award",
            "limit credit",
        ),
    ) or any(point.get("do_not_accept") or point.get("ignore") for point in structured)
    has_levels = _contains_any(
        combined,
        ("levels-based", "level 1", "level 2", "best fit"),
    ) or any(point.get("credit_type") == "level" for point in structured)
    evidence_ids = [
        str(identifier).strip()
        for identifier in item.get("evidence_ids", [])
        if str(identifier).strip()
    ]
    has_evidence_binding = (
        kind == "multiple_choice"
        or not evidence_ids
        or any(identifier.casefold() in combined for identifier in evidence_ids)
        or _contains_any(
            combined,
            ("evidence", "source", "extract", "figure", "data", "table", "context"),
        )
    )
    if evidence_ids and not has_evidence_binding:
        raise ValueError(
            f"mark scheme for item {item_id} does not bind its required evidence: "
            + ", ".join(evidence_ids)
        )

    contract = item.get("assessment_contract")
    if isinstance(contract, dict):
        missing_contract_guidance = [
            f"{field}: {requirement}"
            for field in (
                "valid_alternatives",
                "partial_credit_boundaries",
                "follow_through_rules",
            )
            for requirement in contract.get(field, [])
            if isinstance(requirement, str)
            and _normalise(requirement) not in _normalise(combined)
        ]
        if missing_contract_guidance:
            raise ValueError(
                f"mark scheme for item {item_id} omits contract guidance: "
                + "; ".join(missing_contract_guidance)
            )

    calculation = kind == "calculation" or command in {
        "calculate",
        "complete",
        "prepare",
    }
    extended = marks >= 8 and (
        kind in {"extended_response", "essay", "analysis", "evaluation"}
        or command
        in {
            "analyse",
            "analyze",
            "assess",
            "advise",
            "discuss",
            "evaluate",
            "justify",
        }
    )
    if calculation and marks >= 3 and not has_working:
        raise ValueError(
            f"mark scheme for item {item_id} has no working or method guidance"
        )
    if extended and not has_levels:
        raise ValueError(f"mark scheme for item {item_id} has no levels descriptors")
    if extended and not has_alternatives:
        raise ValueError(
            f"mark scheme for item {item_id} has no alternative-answer guidance"
        )
    if extended and not has_credit_limits:
        raise ValueError(
            f"mark scheme for item {item_id} has no explicit credit limits"
        )

    return MarkSchemeQuality(
        points=len(substantive),
        covered_objectives=tuple(sorted(covered_objectives)),
        has_working=has_working,
        has_alternatives=has_alternatives,
        has_credit_limits=has_credit_limits,
        has_levels=has_levels,
        has_evidence_binding=has_evidence_binding,
    )


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)
