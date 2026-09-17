"""Bounded candidate-answerable paths; printed alternatives remain reviewable.

Topology is data, never parsed from candidate-facing instructions. Item IDs are
the export's leaf paths, so parent summaries cannot silently duplicate marks.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from itertools import combinations, product
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PATH_POLICY_ID = "candidate-paths-v1"
MAX_PATHS = 256
# Intended generated policies already established by E/F/H1, not inferred
# annual board totals or a tolerance learned from student performance.
GENERATED_OBJECTIVE_POLICIES = {
    ("aqa/economics", "1"): (15, 22, 25, 18),
    ("aqa/economics", "2"): (15, 22, 25, 18),
    ("aqa/economics", "3"): (22, 24, 19, 15),
    ("ocr/economics", "1"): (18, 20, 20, 22),
    ("ocr/economics", "2"): (18, 20, 20, 22),
    ("ocr/economics", "3"): (24, 22, 18, 16),
    ("aqa/business", "1"): (27, 29, 24, 20),
    ("aqa/business", "2"): (24, 27, 28, 21),
    ("aqa/business", "3"): (19, 19, 31, 31),
    ("pearson-edexcel/economics-a-2015", "1"): (25, 26, 24, 25),
    ("pearson-edexcel/economics-a-2015", "2"): (24, 26, 25, 25),
    ("pearson-edexcel/economics-a-2015", "3"): (20, 20, 30, 30),
}


def identity(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


class PathOption(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    item_ids: list[str] = Field(min_length=1)


class PathSection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    answer_options: int = Field(gt=0)
    candidate_marks: int = Field(gt=0)
    options: list[PathOption] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_selection(self) -> PathSection:
        if self.answer_options > len(self.options):
            raise ValueError("selection count exceeds printed options")
        if len({option.id for option in self.options}) != len(self.options):
            raise ValueError("duplicate option identity")
        return self


class CandidateTopology(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1] = 1
    policy_id: str = Field(min_length=1)
    total_marks: int = Field(gt=0)
    duration_minutes: int = Field(gt=0)
    sections: list[PathSection] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_membership(self) -> CandidateTopology:
        if len({section.id for section in self.sections}) != len(self.sections):
            raise ValueError("duplicate section identity")
        members = [
            key
            for section in self.sections
            for option in section.options
            for key in option.item_ids
        ]
        if len(set(members)) != len(members):
            raise ValueError("duplicate item membership")
        if (
            sum(section.candidate_marks for section in self.sections)
            != self.total_marks
        ):
            raise ValueError("section marks differ from candidate total")
        if (
            math.prod(
                math.comb(len(s.options), s.answer_options) for s in self.sections
            )
            > MAX_PATHS
        ):
            raise ValueError("candidate path bound exceeded")
        return self

    @property
    def fingerprint(self) -> str:
        return identity(self.model_dump(mode="json"))


class CandidatePath(BaseModel):
    id: str
    item_ids: list[str]
    total_marks: int
    sections: dict[str, list[str]]
    selected_options: dict[str, list[str]]


def enumerate_candidate_paths(
    topology: CandidateTopology | dict[str, Any], items: list[dict[str, Any]]
) -> list[CandidatePath]:
    topology = CandidateTopology.model_validate(topology)
    by_id = {item["id"]: item for item in items}
    if len(by_id) != len(items):
        raise ValueError("duplicate printed item identity")
    members = {
        key
        for section in topology.sections
        for option in section.options
        for key in option.item_ids
    }
    if members != set(by_id):
        raise ValueError("topology does not cover every printed leaf exactly once")
    if any(type(item.get("marks")) is not int or item["marks"] <= 0 for item in items):
        raise ValueError("invalid leaf marks")
    paths = []
    for selected in product(
        *(combinations(s.options, s.answer_options) for s in topology.sections)
    ):
        sections = {}
        choices = {}
        for section, options in zip(topology.sections, selected, strict=True):
            keys = [key for option in options for key in option.item_ids]
            if sum(by_id[key]["marks"] for key in keys) != section.candidate_marks:
                raise ValueError(f"section {section.id} path has wrong leaf marks")
            sections[section.id] = keys
            choices[section.id] = [option.id for option in options]
        paths.append(
            CandidatePath(
                id="|".join(
                    f"{key}:{'+'.join(value)}" for key, value in choices.items()
                ),
                item_ids=[key for keys in sections.values() for key in keys],
                total_marks=topology.total_marks,
                sections=sections,
                selected_options=choices,
            )
        )
    return paths


def topology_from_blueprint(
    blueprint: dict[str, Any], items: list[dict[str, Any]], family_id: str
) -> CandidateTopology:
    def members(prefix: str) -> list[str]:
        return [
            item["id"]
            for item in items
            if item["id"].split("@", 1)[-1].startswith(prefix)
        ]

    by_id = {item["id"]: item for item in items}
    sections = []
    if isinstance(blueprint.get("sections"), list):
        for index, section in enumerate(blueprint["sections"]):
            count = section.get("answer_options")
            if type(count) is not int:
                raise ValueError(
                    "unknown section selection count; regenerate stale topology"
                )
            for option in section["options"]:
                expected = {
                    "policy_id": PATH_POLICY_ID,
                    "section_id": section["id"],
                    "answer_options": count,
                    "candidate_marks": section["candidate_marks"],
                    "option_ids": [o["id"] for o in section["options"]],
                    "bundle_id": option["id"],
                    "question_ids": [q["number"] for q in option["questions"]],
                }
                if option.get("selection_context") != expected:
                    raise ValueError("saved option selection context is stale")
            options = [
                PathOption(
                    id=option["id"], item_ids=members(f"sections.{index}.options.{j}.")
                )
                for j, option in enumerate(section["options"])
            ]
            sections.append(
                PathSection(
                    id=section["id"],
                    answer_options=count,
                    candidate_marks=section["candidate_marks"],
                    options=options,
                )
            )
    elif family_id == "pearson-edexcel/economics-a-2015":
        rules = blueprint.get("candidate_path_rules")
        if not rules:
            raise ValueError(
                "unknown Edexcel selection rules; regenerate stale topology"
            )
        for rule in rules:
            questions = [
                (i, q)
                for i, q in enumerate(blueprint["questions"])
                if q["section"] == rule["id"]
            ]
            mandatory = []
            groups: dict[str, list[PathOption]] = {}
            for i, question in questions:
                expected_context = {
                    "section_id": rule["id"],
                    "groups": rule["choice_groups"],
                    "question_ids": [q["number"] for _, q in questions],
                }
                if question.get("choice_selection_context") != expected_context:
                    raise ValueError("Edexcel saved selection context is stale")
                keys = members(f"questions.{i}.")
                # Standalone question's own path has no trailing dot.
                keys += [
                    item["id"]
                    for item in items
                    if item["id"].split("@", 1)[-1] == f"questions.{i}"
                ]
                if (
                    question.get("parts")
                    and sum(by_id[key]["marks"] for key in keys) != question["marks"]
                ):
                    raise ValueError("Edexcel parent marks differ from marked leaves")
                option = PathOption(id=question["number"], item_ids=keys)
                if question.get("choice_group"):
                    groups.setdefault(question["choice_group"], []).append(option)
                else:
                    mandatory.append(option)
            if set(groups) != set(rule["choice_groups"]):
                raise ValueError("Edexcel choice membership differs from section rules")
            if mandatory:
                sections.append(
                    PathSection(
                        id=rule["id"] + ":mandatory",
                        answer_options=len(mandatory),
                        candidate_marks=sum(
                            by_id[key]["marks"] for o in mandatory for key in o.item_ids
                        ),
                        options=mandatory,
                    )
                )
            for group, options in groups.items():
                expected = rule["choice_groups"][group]
                if [o.id for o in options] != expected["option_ids"]:
                    raise ValueError(
                        "Edexcel choice bundle identities differ from rules"
                    )
                sections.append(
                    PathSection(
                        id=rule["id"] + ":" + group,
                        answer_options=expected["answer_options"],
                        candidate_marks=expected["candidate_marks"],
                        options=options,
                    )
                )
    elif family_id == "aqa/computer-science" and isinstance(
        blueprint.get("questions"), list
    ):
        sections = [
            PathSection(
                id="mandatory",
                answer_options=1,
                candidate_marks=blueprint["total_marks"],
                options=[PathOption(id="all", item_ids=list(by_id))],
            )
        ]
    else:
        raise ValueError("unknown candidate topology; no all-items fallback")
    result = CandidateTopology(
        policy_id=PATH_POLICY_ID,
        total_marks=blueprint["total_marks"],
        duration_minutes=blueprint["duration_minutes"],
        sections=sections,
    )
    enumerate_candidate_paths(result, items)
    return result


def path_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    objectives: Counter[str] = Counter()
    for item in items:
        objectives.update(item.get("assessment_objectives") or {})
    time_known = all(
        isinstance(i.get("expected_minutes"), (int, float))
        and not isinstance(i.get("expected_minutes"), bool)
        and math.isfinite(i["expected_minutes"])
        and i["expected_minutes"] > 0
        for i in items
    )
    ao_known = all(
        isinstance(i.get("assessment_objectives"), dict)
        and all(type(v) is int and v >= 0 for v in i["assessment_objectives"].values())
        and sum(i["assessment_objectives"].values()) == i["marks"]
        for i in items
    )
    return {
        "marks": sum(i["marks"] for i in items),
        "allocated_minutes": round(sum(i["expected_minutes"] for i in items), 3)
        if time_known
        else None,
        "assessment_objectives": dict(objectives) if ao_known else None,
        "timing_basis": "design-allocation-not-observed",
        "reasoning_steps_source": "unknown",
        "learner_demand_source": "unknown",
    }


def audit_candidate_paths(
    items: list[dict[str, Any]],
    topology: CandidateTopology | dict[str, Any],
    profile: Any,
) -> dict[str, Any]:
    from Backend.Core.reference_demand import (
        _distribution_distance,
        audit_form_demand,
        build_item_demand_target,
    )

    topology = CandidateTopology.model_validate(topology)
    paths = enumerate_candidate_paths(topology, items)
    from Backend.Core.reference_evidence import validate_profile_evidence

    evidence_error = None
    try:
        qualified_source = validate_profile_evidence(profile)
    except ValueError:
        qualified_source = False
        evidence_error = "reference_evidence_invalid"
    by_id = {i["id"]: i for i in items}
    results = []
    for path in paths:
        selected = [by_id[key] for key in path.item_ids]
        audit = audit_form_demand(selected, profile)
        metrics = path_metrics(selected)
        failed = list(audit["failed_checks"])
        # A source comparison must pass as one correlated vector, not choose a
        # different reference for each coordinate. Equal-path averaging below
        # is descriptive only and is never used as a rescue gate.
        comparisons = []
        if qualified_source:
            for form in profile.reference_forms:
                if form.get("status") != "eligible":
                    continue
                for reference in form.get("paths", []):
                    expected = reference["observed"]
                    distances = {
                        name: round(
                            _distribution_distance(
                                audit["observed"][name], expected[name]
                            ),
                            6,
                        )
                        for name in form.get(
                            "comparable_metrics", profile.metric_tolerances
                        )
                    }
                    comparisons.append(
                        {
                            "source_id": form["id"],
                            "path_id": reference["id"],
                            "distances": distances,
                            "passed": all(
                                value <= profile.metric_tolerances[name]
                                for name, value in distances.items()
                            ),
                        }
                    )
            failed = (
                []
                if any(c["passed"] for c in comparisons)
                else ["correlated_reference_path_fit"]
            )
        else:
            failed.append(evidence_error or "reference_paths_insufficient")
        if metrics["allocated_minutes"] is None:
            failed.append("allocated_timing_unknown")
        elif abs(metrics["allocated_minutes"] - topology.duration_minutes) > 0.02 * len(
            selected
        ):
            failed.append("allocated_timing_budget")
        if metrics["assessment_objectives"] is None:
            failed.append("objective_allocation_unknown")
        objective_design = GENERATED_OBJECTIVE_POLICIES.get(
            (profile.family_id, profile.paper_id)
        )
        if (
            objective_design
            and topology.total_marks == sum(objective_design)
            and metrics["assessment_objectives"] is not None
        ):
            expected_ao = {
                f"AO{n}": marks for n, marks in enumerate(objective_design, 1)
            }
            metrics["objective_design_target"] = expected_ao
            metrics["objective_design_basis"] = (
                "Existing E/F/H1 generated task/credit policy, not annual board target"
            )
            if metrics["assessment_objectives"] != expected_ao:
                failed.append("objective_design_envelope")
        sections = {
            name: path_metrics([by_id[key] for key in keys])
            for name, keys in path.sections.items()
        }
        for name, section_metrics in sections.items():
            expected_minutes = (
                topology.duration_minutes
                * section_metrics["marks"]
                / topology.total_marks
            )
            section_metrics["allocated_minutes_target"] = round(expected_minutes, 3)
            if section_metrics["allocated_minutes"] is not None and abs(
                section_metrics["allocated_minutes"] - expected_minutes
            ) > 0.02 * len(path.sections[name]):
                failed.append(f"section_timing_budget:{name}")
        # Pick one complete vector by its worst tolerance-normalised deviation.
        # This selection is diagnostic; the gate above still requires all
        # coordinates of the same source path to pass together.
        closest = (
            min(
                comparisons,
                key=lambda comparison: max(
                    value / profile.metric_tolerances[name]
                    for name, value in comparison["distances"].items()
                ),
            )
            if comparisons
            else None
        )
        results.append(
            {
                **path.model_dump(mode="json"),
                **metrics,
                "section_metrics": sections,
                "observed": audit["observed"],
                "distances": closest["distances"]
                if closest
                else audit["gated_distances"],
                "comparison_path": {
                    key: closest[key] for key in ("source_id", "path_id")
                }
                if closest
                else None,
                "reference_comparisons": comparisons,
                "intended_demand_constraints": {
                    "basis": "Generated component task/credit design; content-bound H2 review required for every printed item, not source learner measurement.",
                    "source_comparison": "not-comparable: source learner demand, reasoning steps and observed time unknown",
                    "item_targets": {
                        item["id"]: build_item_demand_target(item, profile).model_dump(
                            mode="json"
                        )
                        for item in selected
                    },
                    "allocated_distribution": audit["observed"][
                        "mark_weighted_demand_distribution"
                    ],
                },
                "failed_checks": failed,
                "passed": not failed,
            }
        )
    worst = {
        name: max(row["distances"].get(name, 0) for row in results)
        for name in {name for row in results for name in row["distances"]}
    }
    return {
        "schema_version": 1,
        "policy_id": PATH_POLICY_ID,
        "evidence_validation_passed": evidence_error is None,
        "passed": all(row["passed"] for row in results),
        "path_count": len(paths),
        "evidence_state": "checked" if qualified_source else "insufficient",
        "topology": topology.model_dump(mode="json"),
        "topology_fingerprint": topology.fingerprint,
        "comparison_identity": identity(
            {
                "items": items,
                "topology": topology.model_dump(mode="json"),
                "profile": profile.comparison_fingerprint,
            }
        ),
        "comparison_basis": "Each legal generated path against a complete same-component source path; equal path/year means are descriptive, not candidate choice frequencies.",
        "printed_items": len(items),
        "printed_marks": sum(i["marks"] for i in items),
        "candidate_mark_range": [
            min(p.total_marks for p in paths),
            max(p.total_marks for p in paths),
        ],
        "allocated_minute_range": [
            min(row["allocated_minutes"] for row in results),
            max(row["allocated_minutes"] for row in results),
        ]
        if all(row["allocated_minutes"] is not None for row in results)
        else None,
        "paths": results,
        "failed_paths": [
            {"id": row["id"], "failed_checks": row["failed_checks"]}
            for row in results
            if not row["passed"]
        ],
        "worst_deviations": worst,
        "empirical_equivalence_claimed": False,
        "external_qualification": False,
    }
