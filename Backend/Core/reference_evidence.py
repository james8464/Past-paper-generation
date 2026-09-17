"""Strict H3 source evidence boundaries; aggregate-v2 is not path qualification."""

from __future__ import annotations

import math
from collections import Counter
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from Backend.Core.candidate_paths import (
    CandidateTopology,
    enumerate_candidate_paths,
)

EXTRACTION_POLICY = "edition-leaf-path-features-v2"
TOPIC_POLICY = "aqa-topic-operation-records-v2"
UNQUALIFIED_POLICY = "unqualified-reference-v1"
COMPARABLE_METRICS = (
    "mark_band_distribution",
    "command_family_distribution",
    "response_mode_distribution",
    "cognitive_operation_distribution",
)
Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Text = Annotated[str, Field(min_length=1)]
Marks = Annotated[int, Field(gt=0, strict=True)]
Objectives = dict[
    Literal["AO1", "AO2", "AO3", "AO4"], Annotated[int, Field(ge=0, strict=True)]
]


class StrictEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class UnknownLearnerFeatures(StrictEvidence):
    learner_demand: None
    observed_minutes: None
    reasoning_steps: None


class Observations(StrictEvidence):
    mark_band_distribution: dict[str, float]
    command_word_distribution: dict[str, float]
    command_family_distribution: dict[str, float]
    response_mode_distribution: dict[str, float]
    cognitive_operation_distribution: dict[str, float]
    demand_distribution: dict[str, float]
    mark_weighted_demand_distribution: dict[str, float]

    @model_validator(mode="after")
    def distributions(self):
        for values in self.model_dump().values():
            if (
                not values
                or any(
                    not key or not math.isfinite(value) or value < 0
                    for key, value in values.items()
                )
                or abs(sum(values.values()) - 1) > 0.002
            ):
                raise ValueError(
                    "source distributions must be finite, nonnegative and total one"
                )
        if self.demand_distribution != {
            "unknown": 1.0
        } or self.mark_weighted_demand_distribution != {"unknown": 1.0}:
            raise ValueError("source learner demand must remain unknown")
        return self


class SourceItem(UnknownLearnerFeatures):
    id: Text
    marks: Marks
    assessment_objectives: Objectives | None
    objective_basis: Literal["unknown", "published-item-allocation"]
    cognitive_operation: Literal[
        "retrieve",
        "describe",
        "explain",
        "contextualise",
        "transform",
        "analyse",
        "judge",
        "design",
        "program",
        "trace",
    ]
    command_word: Text
    response_mode: Literal[
        "programming",
        "algorithm-trace",
        "computational-design",
        "calculation",
        "mathematical-argument",
        "selected-response",
        "structured-reasoning",
        "constructed-response",
        "extended-evaluation",
        "recall",
        "multi-stage-calculation",
        "computational-analysis",
    ]
    demand_band: Literal["unknown"]
    demand_basis: Literal["unknown-no-learner-measurement"]
    historical_engineering_demand_proxy: Literal["low", "standard", "high"]
    demand_eligible: bool = True
    operation_basis: str | None = None
    source_subpart: str | None = None
    source_page: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def objective_credit(self):
        if (self.assessment_objectives is None) != (self.objective_basis == "unknown"):
            raise ValueError("source objective evidence basis is inconsistent")
        if (
            self.assessment_objectives is not None
            and sum(self.assessment_objectives.values()) != self.marks
        ):
            raise ValueError("source objective marks do not reconcile")
        return self


class SourcePath(UnknownLearnerFeatures):
    id: Text
    item_ids: list[Text] = Field(min_length=1)
    marks: Marks
    assessment_objectives: Objectives | None
    observed: Observations
    section_features: dict[str, Observations]


class SourceIdentity(StrictEvidence):
    id: Text
    year: int = Field(ge=2000, le=2100)
    source_sha256: Hash
    scheme_file: str | None = None
    scheme_sha256: Hash | None = None

    @model_validator(mode="after")
    def scheme_identity(self):
        if self.scheme_file and not self.scheme_sha256:
            raise ValueError("paired scheme filename needs its content hash")
        return self


class QualitativeExaminerEvidence(StrictEvidence):
    source_sha256: Hash
    pages: list[Marks] = Field(min_length=1)
    challenging_mcq_ids: list[Marks] = Field(min_length=1)
    basis: Literal["qualitative-cohort-commentary"]
    facility: None


class SourceForm(SourceIdentity):
    status: Literal["eligible"]
    extraction_policy: Literal[EXTRACTION_POLICY]
    feature_basis: Text
    objective_basis: Literal["unknown", "reconciled-published-aggregate"]
    weighting_basis: Literal["equal-path-within-year-equal-year-descriptive"]
    comparable_metrics: list[str]
    non_comparable_features: dict[
        Literal["learner_demand", "reasoning_steps", "observed_minutes"],
        Literal["unknown"],
    ]
    topology: CandidateTopology
    topology_fingerprint: Hash
    printed_marks: Marks
    items: list[SourceItem] = Field(min_length=1)
    paths: list[SourcePath] = Field(min_length=1)
    qualitative_examiner_evidence: QualitativeExaminerEvidence | None = None

    @model_validator(mode="after")
    def reconcile(self):
        if (
            self.objective_basis != "unknown"
            or any(item.assessment_objectives is not None for item in self.items)
        ) and not self.scheme_sha256:
            raise ValueError("published objective evidence needs the scheme hash")
        if self.comparable_metrics != list(COMPARABLE_METRICS):
            raise ValueError(
                "source comparison must contain all allowed observable metrics"
            )
        if set(self.non_comparable_features) != {
            "learner_demand",
            "reasoning_steps",
            "observed_minutes",
        }:
            raise ValueError("source unknown feature declarations are incomplete")
        if self.topology.fingerprint != self.topology_fingerprint:
            raise ValueError("source topology fingerprint is stale")
        items = [item.model_dump() for item in self.items]
        if sum(item["marks"] for item in items) != self.printed_marks:
            raise ValueError("source printed marks do not reconcile")
        paths = enumerate_candidate_paths(self.topology, items)
        if len(paths) != len(self.paths):
            raise ValueError("source legal path inventory is incomplete")
        by_id = {item["id"]: item for item in items}
        for actual, saved in zip(paths, self.paths, strict=True):
            if (actual.id, actual.item_ids, actual.total_marks) != (
                saved.id,
                saved.item_ids,
                saved.marks,
            ):
                raise ValueError(
                    "source path identity/leaf membership does not reconcile"
                )
            if (
                saved.assessment_objectives is not None
                and sum(saved.assessment_objectives.values()) != saved.marks
            ):
                raise ValueError("source path objective marks do not reconcile")
            if (saved.assessment_objectives is None) != (
                self.objective_basis == "unknown"
            ):
                raise ValueError("source path objective basis is inconsistent")
            if saved.observed.model_dump() != source_observations(
                [by_id[key] for key in actual.item_ids]
            ):
                raise ValueError("source path feature vector is stale")
            expected_sections = {
                name: source_observations([by_id[key] for key in keys])
                for name, keys in actual.sections.items()
            }
            if {
                name: value.model_dump()
                for name, value in saved.section_features.items()
            } != expected_sections:
                raise ValueError(
                    "source section feature vectors are incomplete or stale"
                )
        return self


class QuarantinedForm(SourceIdentity):
    status: Literal["quarantined"]
    objective_basis: Literal["unknown", "printed-conflicting"]
    paths: list[Any] = Field(max_length=0)
    reason: Text | None = None
    conflicting_evidence: dict[str, Any] | None = None
    qualitative_examiner_evidence: QualitativeExaminerEvidence | None = None

    @model_validator(mode="after")
    def quarantine_reason(self):
        if not self.reason and not self.conflicting_evidence:
            raise ValueError("quarantined source needs its reason/evidence")
        return self


class TopicRecord(UnknownLearnerFeatures):
    id: Text
    year: int = Field(ge=2000, le=2100)
    paper: Literal["1", "2"]
    item: Text
    question_cluster: Text
    topic_id: Literal["4.2", "4.10", "4.12"]
    topic_basis: Text
    stratum: Literal["core", "mixed", "context-incomplete"]
    context_complete: bool
    marks: Marks
    assessment_objectives: Objectives | None
    objective_basis: Literal["unknown", "published-item-allocation"]
    operation: Literal[
        "explain",
        "describe",
        "analyse",
        "represent",
        "retrieve",
        "trace",
        "program",
        "complete-code",
        "analyse-complexity",
        "unknown",
    ]
    mode: Literal[
        "prose",
        "table",
        "result",
        "diagram",
        "code",
        "query",
        "selected",
        "relations",
        "multi-selected",
        "unknown",
    ]
    feature_basis: Literal["reviewed-task-inference"]
    source_dependency: Literal["unknown", "task-context", "self-contained"]
    question_pages: Text
    scheme_pages: Text
    question_file: Text
    scheme_file: Text
    question_sha256: Hash
    scheme_sha256: Hash
    specification_sha256: Hash

    @model_validator(mode="after")
    def identities(self):
        if (
            self.id != f"7517{self.paper}-{self.year}-{self.item}"
            or self.question_cluster
            != f"{self.year}-{self.paper}-{self.item.split('.')[0]}"
        ):
            raise ValueError("topic source identity/cluster mismatch")
        if self.context_complete != (self.stratum != "context-incomplete"):
            raise ValueError("topic source context status mismatch")
        if (self.assessment_objectives is None) != (self.objective_basis == "unknown"):
            raise ValueError("topic objective basis mismatch")
        if (
            self.assessment_objectives is not None
            and sum(self.assessment_objectives.values()) != self.marks
        ):
            raise ValueError("topic objective marks mismatch")
        if self.context_complete and (
            self.operation == "unknown" or self.mode == "unknown"
        ):
            raise ValueError("eligible topic record has unknown task features")
        return self


Form = Annotated[SourceForm | QuarantinedForm, Field(discriminator="status")]


def source_observations(items):
    from Backend.Core.reference_demand import _collapse_command_distribution, _mark_band

    def normalised(counts):
        total = sum(counts.values())
        result = {key: round(value / total, 6) for key, value in sorted(counts.items())}
        if result:
            largest = max(result, key=result.get)
            result[largest] = round(
                result[largest] + round(1.0 - sum(result.values()), 6), 6
            )
        return result

    def _distribution(values):
        return normalised(Counter(values))

    def _weighted_distribution(values):
        counts = Counter()
        for key, weight in values:
            counts[key] += weight
        return normalised(counts)

    items = [item for item in items if item.get("demand_eligible", True)]
    result = {
        "mark_band_distribution": _distribution(
            _mark_band(item["marks"]) for item in items
        ),
        "command_word_distribution": _distribution(
            item["command_word"] for item in items
        ),
        "response_mode_distribution": _distribution(
            item["response_mode"] for item in items
        ),
        "cognitive_operation_distribution": _distribution(
            item["cognitive_operation"] for item in items
        ),
        "demand_distribution": _distribution(item["demand_band"] for item in items),
        "mark_weighted_demand_distribution": _weighted_distribution(
            (item["demand_band"], item["marks"]) for item in items
        ),
    }
    result["command_family_distribution"] = _collapse_command_distribution(
        result["command_word_distribution"]
    )
    return result


def validate_profile_evidence(profile, *, evidence_context=None):
    from Backend.Core.reference_demand import _is_verified_reference_profile

    if not _is_verified_reference_profile(evidence_context, profile):
        raise ValueError("canonical reference evidence context is required")
    return validate_profile_payload(profile)


def validate_profile_payload(profile):
    if profile.evidence_policy_id == EXTRACTION_POLICY:
        if (
            profile.assessment_kind != "full-paper"
            or not profile.reference_forms
            or profile.topic_records
        ):
            raise ValueError("full-paper H3 source evidence is missing or mixed")
        forms = TypeAdapter(list[Form]).validate_python(profile.reference_forms)
        if len({form.id for form in forms}) != len(forms) or len(
            {form.year for form in forms}
        ) != len(forms):
            raise ValueError("source edition identity is duplicated")
        for form in forms:
            if (
                isinstance(form, SourceForm)
                and form.topology.policy_id
                != f"{EXTRACTION_POLICY}:{profile.family_id}:{profile.paper_id}:{form.year}"
            ):
                raise ValueError("source component/edition topology policy mismatch")
        return any(isinstance(form, SourceForm) for form in forms)
    if profile.evidence_policy_id == TOPIC_POLICY:
        if (
            profile.assessment_kind != "question-bank"
            or profile.reference_forms
            or not profile.evidence_gaps
        ):
            raise ValueError("topic H3 evidence is missing or mixed")
        records = TypeAdapter(list[TopicRecord]).validate_python(profile.topic_records)
        topic = profile.paper_id.removeprefix("bank-")
        if (
            not records
            or len({r.id for r in records}) != len(records)
            or any(r.topic_id != topic for r in records)
        ):
            raise ValueError("topic source identity is incomplete or mismatched")
        from Backend.Core.topic_reference_evidence import reviewed_topic_records

        if profile.topic_records != reviewed_topic_records(topic):
            raise ValueError("topic record inventory differs from reviewed policy")
        return False
    if (
        profile.evidence_policy_id == UNQUALIFIED_POLICY
        and profile.assessment_kind == "full-paper"
        and not profile.reference_forms
        and not profile.topic_records
        and profile.evidence_gaps
    ):
        return False
    raise ValueError("missing or unsupported H3 evidence policy")
