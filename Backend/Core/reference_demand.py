from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from Backend.Core.paths import REPO_ROOT

PROFILES_PATH = REPO_ROOT / "Resources" / "reference-demand-profiles.json"

DemandBand = Literal["low", "standard", "high"]


class ReferenceDemandProfile(BaseModel):
    family_id: str = Field(min_length=3)
    paper_id: str = Field(min_length=1)
    assessment_kind: Literal["full-paper", "question-bank"] = "full-paper"
    comparison_basis: str = Field(min_length=12)
    source_document_count: int = Field(gt=0)
    source_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    mark_band_distribution: dict[str, float]
    command_word_distribution: dict[str, float]
    demand_distribution: dict[str, float]
    distribution_tolerance: float = Field(default=0.55, gt=0, le=2)

    @field_validator(
        "mark_band_distribution",
        "command_word_distribution",
        "demand_distribution",
    )
    @classmethod
    def validate_distribution(cls, value: dict[str, float]) -> dict[str, float]:
        if not value or any(not key.strip() or amount < 0 for key, amount in value.items()):
            raise ValueError("reference distributions must contain non-negative values")
        total = sum(value.values())
        if abs(total - 1.0) > 0.002:
            raise ValueError("reference distributions must total 1")
        return {key.casefold(): round(float(amount), 6) for key, amount in value.items()}


class ReferenceDemandDocument(BaseModel):
    schema_version: Literal[1]
    purpose: str = Field(min_length=20)
    derived_aggregate_only: Literal[True]
    retains_source_text: Literal[False]
    profiles: list[ReferenceDemandProfile] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profiles(self) -> ReferenceDemandDocument:
        keys = [(profile.family_id, profile.paper_id) for profile in self.profiles]
        if len(keys) != len(set(keys)):
            raise ValueError("reference demand profiles must be unique")
        return self


class ItemDemandTarget(BaseModel):
    demand_band: DemandBand
    minimum_reasoning_steps: int = Field(ge=1, le=8)
    response_mode: str
    requires_context: bool
    requires_analysis_chain: bool
    requires_judgement: bool
    requires_multiple_concepts: bool
    requires_data_transformation: bool
    expected_minutes: float | None = Field(default=None, gt=0)
    reference_comparison_basis: str
    reference_profile_fingerprint: str


@lru_cache(maxsize=1)
def load_reference_demand_document(
    path: Path = PROFILES_PATH,
) -> ReferenceDemandDocument:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError("reference demand profiles are missing") from error
    return ReferenceDemandDocument.model_validate(payload)


def profile_for(
    family_id: str,
    paper_id: str,
    *,
    document: ReferenceDemandDocument | None = None,
) -> ReferenceDemandProfile:
    source = document or load_reference_demand_document()
    for profile in source.profiles:
        if (profile.family_id, profile.paper_id) == (family_id, str(paper_id)):
            return profile
    raise ValueError(
        f"no reference demand profile for {family_id} paper {paper_id}"
    )


def build_item_demand_target(
    item: Any,
    profile: ReferenceDemandProfile,
) -> ItemDemandTarget:
    raw = _serialise_item(item)
    marks = _positive_int(raw.get("marks"), name="marks")
    command = str(raw.get("command_word") or _leading_command(raw.get("prompt"))).casefold()
    kind = str(raw.get("kind") or raw.get("style_id") or "").casefold()
    objectives = _objective_marks(raw.get("assessment_objectives"))
    demand = str(raw.get("intended_demand") or "").casefold()
    if demand not in {"low", "standard", "high"}:
        demand = _infer_demand(marks=marks, command=command, kind=kind)

    minimum_steps = {"low": 1, "standard": 2, "high": 3}[demand]
    calculation = kind in {"calculation", "quantitative"} or command in {
        "calculate",
        "complete",
        "construct",
        "derive",
        "prepare",
    }
    if calculation and marks >= 4:
        minimum_steps = max(minimum_steps, 3)
    if demand == "high" and marks >= 12:
        minimum_steps = 4

    requires_judgement = objectives.get("AO4", 0) > 0 or command in {
        "assess",
        "discuss",
        "evaluate",
        "justify",
        "recommend",
    }
    requires_analysis = objectives.get("AO3", 0) > 0 or command in {
        "analyse",
        "analyze",
        "assess",
        "discuss",
        "evaluate",
        "examine",
        "explain",
    }
    requires_context = objectives.get("AO2", 0) > 0 or bool(
        raw.get("context")
        or raw.get("evidence_ids")
        or raw.get("source_references")
        or raw.get("source_reference")
    )
    response_mode = _response_mode(
        marks=marks,
        command=command,
        kind=kind,
        calculation=calculation,
    )
    expected_minutes = raw.get("expected_minutes")
    return ItemDemandTarget(
        demand_band=demand,
        minimum_reasoning_steps=minimum_steps,
        response_mode=response_mode,
        requires_context=requires_context,
        requires_analysis_chain=requires_analysis,
        requires_judgement=requires_judgement,
        requires_multiple_concepts=(demand == "high" or marks >= 8),
        requires_data_transformation=calculation or kind in {"data", "graph"},
        expected_minutes=(float(expected_minutes) if expected_minutes else None),
        reference_comparison_basis=profile.comparison_basis,
        reference_profile_fingerprint=profile.source_fingerprint,
    )


def audit_form_demand(
    items: list[dict[str, Any]],
    profile: ReferenceDemandProfile,
) -> dict[str, Any]:
    if not items:
        raise ValueError("reference demand audit requires assessment items")
    targets = [build_item_demand_target(item, profile) for item in items]
    observed = {
        "mark_band_distribution": _distribution(
            _mark_band(_positive_int(item.get("marks"), name="marks"))
            for item in items
        ),
        "command_word_distribution": _distribution(
            str(item.get("command_word") or _leading_command(item.get("prompt"))).casefold()
            or "unspecified"
            for item in items
        ),
        "demand_distribution": _distribution(
            target.demand_band for target in targets
        ),
    }
    expected = {
        "mark_band_distribution": profile.mark_band_distribution,
        "command_word_distribution": profile.command_word_distribution,
        "demand_distribution": profile.demand_distribution,
    }
    observed["command_family_distribution"] = _collapse_command_distribution(
        observed["command_word_distribution"]
    )
    expected["command_family_distribution"] = _collapse_command_distribution(
        expected["command_word_distribution"]
    )
    distances = {
        name: round(_distribution_distance(observed[name], distribution), 6)
        for name, distribution in expected.items()
    }
    gated_distributions = (
        "mark_band_distribution",
        "command_family_distribution",
        "demand_distribution",
    )
    failed = [
        name for name in gated_distributions
        for distance in [distances[name]]
        if distance > profile.distribution_tolerance
    ]
    return {
        "schema_version": 1,
        "passed": not failed,
        "profile_fingerprint": profile.source_fingerprint,
        "comparison_basis": profile.comparison_basis,
        "source_document_count": profile.source_document_count,
        "items_checked": len(items),
        "tolerance": profile.distribution_tolerance,
        "observed": observed,
        "expected": expected,
        "distances": distances,
        "gated_distances": {
            name: distances[name] for name in gated_distributions
        },
        "failed_checks": failed,
        "empirical_equivalence_claimed": False,
    }


def _serialise_item(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        raw = value.model_dump(mode="json")
    elif isinstance(value, dict):
        raw = value
    else:
        raise TypeError("demand targets require a model or mapping")
    if not isinstance(raw, dict):
        raise TypeError("demand target input must serialise to an object")
    return raw


def _positive_int(value: Any, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"demand item {name} must be a positive integer")
    return value


def _objective_marks(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key).upper(): int(amount)
        for key, amount in value.items()
        if isinstance(amount, int) and amount > 0
    }


def _leading_command(value: Any) -> str:
    words = str(value or "").strip().split()
    return words[0].strip(".,:;!?()[]{}").casefold() if words else ""


def _infer_demand(*, marks: int, command: str, kind: str) -> DemandBand:
    if marks >= 10 or command in {"assess", "discuss", "evaluate"}:
        return "high"
    if marks <= 3 or command in {"define", "give", "identify", "select", "state"}:
        return "low"
    if kind == "multiple_choice":
        return "low"
    return "standard"


def _response_mode(
    *, marks: int, command: str, kind: str, calculation: bool
) -> str:
    if kind == "multiple_choice":
        return "selected-response"
    if calculation:
        return "multi-stage-calculation" if marks >= 4 else "calculation"
    if command in {"state", "identify", "give", "name", "define", "select"}:
        return "recall"
    if command in {"assess", "discuss", "evaluate", "recommend"} or marks >= 12:
        return "extended-evaluation"
    if command in {"analyse", "analyze", "examine", "explain"}:
        return "structured-reasoning"
    return "constructed-response"


def _mark_band(marks: int) -> str:
    if marks <= 4:
        return "short"
    if marks <= 9:
        return "medium"
    return "extended"


def _collapse_command_distribution(
    distribution: dict[str, float],
) -> dict[str, float]:
    collapsed: Counter[str] = Counter()
    for command, share in distribution.items():
        collapsed[_command_family(command)] += share
    return {key: round(value, 6) for key, value in sorted(collapsed.items())}


def _command_family(command: str) -> str:
    value = command.casefold().strip()
    if value in {"mcq", "select"}:
        return "selected-response"
    if value in {"define", "give", "identify", "name", "state"}:
        return "short-response"
    if value in {
        "calculate",
        "complete",
        "construct",
        "convert",
        "design",
        "develop",
        "draw",
        "prepare",
        "trace",
        "write",
    }:
        return "procedural"
    if value in {
        "analyse",
        "analyze",
        "compare",
        "describe",
        "examine",
        "explain",
        "outline",
        "suggest",
    }:
        return "reasoned-response"
    if value in {
        "advise",
        "assess",
        "discuss",
        "evaluate",
        "justify",
        "recommend",
    }:
        return "evaluation"
    return "other"


def _distribution(values: Any) -> dict[str, float]:
    counts = Counter(values)
    total = sum(counts.values())
    return {
        key: round(count / total, 6)
        for key, count in sorted(counts.items())
    }


def _distribution_distance(
    observed: dict[str, float], expected: dict[str, float]
) -> float:
    return sum(
        abs(observed.get(key, 0.0) - expected.get(key, 0.0))
        for key in set(observed) | set(expected)
    )
