from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Any

from Backend.Core.assessment_objectives import objective_policy_for
from Backend.Core.assessment_quality import (
    assert_distinct_items,
    item_fingerprint,
)
from Backend.Core.candidate_identity import (
    difficulty_candidate_projection,
    edexcel_difficulty_candidate_projection,
    shared_difficulty_candidate_projection,
)
from Backend.Core.computer_science_audit import audit_computer_science_blueprint
from Backend.Core.computer_science_authoring import (
    aqa_cs_difficulty_candidate,
    validate_aqa_cs_reviews,
)
from Backend.Core.generator_registry import generator_capability
from Backend.Core.level_of_response import (
    LevelOfResponseEngine,
    load_level_policies,
    scale_level_policy,
)
from Backend.Core.mark_scheme_quality import validate_mark_scheme_item
from Backend.Core.paths import REPO_ROOT
from Backend.Core.reference_demand import (
    assessment_objectives_for_item,
    audit_form_demand,
    profile_for_verified_context,
    verified_reference_profile,
)
from Backend.Core.response_simulation import ResponseSimulator
from Backend.Core.subjects.sql_contracts import (
    SQLSourceContract,
    render_sql_schema,
    sql_source_intent_sha256,
)


class AssessmentPackageCompatibilityError(ValueError):
    """The package cannot be upgraded safely by this application version."""


def load_assessment_package(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise AssessmentPackageCompatibilityError(
            "Assessment package must contain a JSON object."
        )
    version = document.get("schema_version", 0)
    if version == 1:
        objective_policy_for(str(document.get("subject", ""))).validate(document)
        return document
    if version == 0:
        return _migrate_schema_zero(document)
    raise AssessmentPackageCompatibilityError(
        f"Assessment package schema version {version} is not supported; "
        "update Paper Creator and try again."
    )


def _migrate_schema_zero(document: dict[str, Any]) -> dict[str, Any]:
    required = {"subject", "paper", "preview", "items", "blueprint"}
    if required - set(document):
        raise AssessmentPackageCompatibilityError(
            "Legacy assessment package is incomplete and cannot be upgraded."
        )
    raw_items = document.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise AssessmentPackageCompatibilityError(
            "Legacy assessment package has no items to upgrade."
        )
    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict) or not str(raw.get("prompt", "")).strip():
            raise AssessmentPackageCompatibilityError(
                "Legacy assessment package contains an invalid item."
            )
        item = dict(raw)
        item["fingerprint"] = item_fingerprint(str(item["prompt"]).strip())
        items.append(item)
    subject = str(document["subject"])
    paper = str(document["paper"])
    migrated = dict(document)
    migrated.update(
        {
            "schema_version": 1,
            "subject": subject,
            "paper": paper,
            "items": items,
            "form_id": _form_id(
                subject=subject,
                paper_number=paper,
                items=items,
            ),
        }
    )
    return migrated


def write_assessment_package(
    paper: Any,
    path: Path,
    *,
    subject: str,
    paper_number: str,
    preview: bool,
    provider: str | None,
    model: str | None,
) -> Path:
    """Write the renderer-independent item record used by release validation."""

    payload = _serialise(paper)
    validate_aqa_cs_reviews(payload, required=not preview)
    objective_policy_for(subject).validate(payload)
    items = _extract_items(
        payload,
        subject=subject,
        paper_number=paper_number,
    )
    if not preview:
        assert_distinct_items(items)
    form_id = _form_id(
        subject=subject,
        paper_number=paper_number,
        items=items,
    )
    reference_demand = _reference_demand_audit(
        subject=subject,
        paper_number=paper_number,
        items=items,
        preview=preview,
        blueprint=payload,
    )
    document = {
        "schema_version": 1,
        "form_id": form_id,
        "subject": subject,
        "paper": paper_number,
        "seed": payload.get("seed"),
        "preview": preview,
        "provider": None if preview else provider,
        "model": None if preview else model,
        "items": items,
        "blueprint": payload,
    }
    if reference_demand is not None:
        document["reference_demand"] = reference_demand
    if objective_policy_for(subject).computational:
        document["assessment_policy"] = audit_computer_science_blueprint(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def validate_assessment_package(
    path: Path,
    *,
    subject: str,
    paper_number: str,
    preview: bool,
    provider: str | None,
    model: str | None,
) -> dict[str, Any]:
    document = load_assessment_package(path)
    validate_aqa_cs_reviews(document.get("blueprint", {}), required=not preview)
    objective_policy_for(subject).validate(document)
    expected = (subject, paper_number, preview)
    actual = (
        document.get("subject"),
        document.get("paper"),
        document.get("preview"),
    )
    if actual != expected:
        raise ValueError(
            f"assessment package identity {actual} does not match request {expected}"
        )
    if not preview and (
        document.get("provider") != provider or document.get("model") != model
    ):
        raise ValueError(
            "assessment package provider/model does not match the generation request"
        )
    items = document.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("assessment package has no items")
    expected_items = _extract_items(
        document["blueprint"],
        subject=subject,
        paper_number=paper_number,
    )
    if items != expected_items:
        raise ValueError("assessment package exported items differ from the blueprint")
    mark_scheme_reports = []
    if objective_policy_for(subject).computational:
        audit = audit_computer_science_blueprint(document.get("blueprint", {}))
        if document.get("assessment_policy") != audit:
            raise ValueError("CS assessment policy evidence is stale or inconsistent")
    response_simulation_reports = []
    for item in items:
        if not isinstance(item, dict):
            raise TypeError("assessment package contains an invalid item")
        prompt = str(item.get("prompt", "")).strip()
        if not prompt or item.get("fingerprint") != item_fingerprint(prompt):
            raise ValueError(
                f"assessment item {item.get('id')} has an invalid fingerprint"
            )
        if not isinstance(item.get("marks"), int) or int(item["marks"]) <= 0:
            raise ValueError(f"assessment item {item.get('id')} has invalid marks")
        scheme = item.get("mark_scheme")
        if not isinstance(scheme, list) or not any(
            str(point).strip() for point in scheme
        ):
            raise ValueError(
                f"assessment item {item.get('id')} has no usable mark scheme"
            )
        mark_scheme_reports.append(validate_mark_scheme_item(item))
        simulation = _validate_response_bands(item)
        if simulation:
            response_simulation_reports.append(simulation)
    cross_paper_quality = validate_cross_paper_quality(items)
    reference_demand = _reference_demand_audit(
        subject=subject,
        paper_number=paper_number,
        items=items,
        preview=preview,
        blueprint=document["blueprint"],
    )
    if reference_demand is not None:
        if document.get("reference_demand") != reference_demand:
            raise ValueError("assessment package reference-demand evidence is invalid")
        if not preview and not reference_demand.get(
            "build_eligible", reference_demand["passed"]
        ):
            failed = ", ".join(reference_demand["failed_checks"])
            raise ValueError(
                "assessment form is outside its reference-demand tolerance: " + failed
            )
    if not preview:
        assert_distinct_items(items)
    expected_form_id = _form_id(
        subject=subject,
        paper_number=paper_number,
        items=items,
    )
    if document.get("form_id") != expected_form_id:
        raise ValueError("assessment package form identity is invalid")
    return {
        "schema_version": document["schema_version"],
        "form_id": expected_form_id,
        "item_count": len(items),
        "fingerprints_verified": True,
        "authoring_provenance": _authoring_provenance(items),
        "mark_schemes_present": True,
        "mark_scheme_quality": {
            "items_verified": len(mark_scheme_reports),
            "items_with_working": sum(
                report.has_working for report in mark_scheme_reports
            ),
            "items_with_alternatives": sum(
                report.has_alternatives for report in mark_scheme_reports
            ),
            "items_with_credit_limits": sum(
                report.has_credit_limits for report in mark_scheme_reports
            ),
            "items_with_levels": sum(
                report.has_levels for report in mark_scheme_reports
            ),
            "evidence_bindings_verified": sum(
                report.has_evidence_binding for report in mark_scheme_reports
            ),
        },
        "cross_paper_quality": cross_paper_quality,
        "reference_demand": reference_demand,
        "path_evidence": reference_demand.get("path_evidence")
        if reference_demand
        else None,
        "response_simulation": {
            "items_verified": len(response_simulation_reports),
            "results": response_simulation_reports,
        },
    }


def _authoring_provenance(items: list[dict[str, Any]]) -> dict[str, Any]:
    values = [str(item.get("provenance", "")).strip() for item in items]
    counts = dict(sorted(Counter(values).items()))
    reviewed_fixed = sum(
        value in {"reviewed-fixed", "reviewed-deterministic-contract"}
        or value == "verified-contract-reviewed"
        or value.startswith("reviewed-seeded-fallback:")
        for value in values
    )
    ai_authored_stem = sum(
        value == "ai-authored-stem-reviewed-contract" for value in values
    )
    ai_authored = sum(
        value == "ai-authored" or value.startswith("ai:") for value in values
    )
    unreviewed = sum(
        value
        in {
            "built-in",
            "deterministic-contract",
            "generator-specific",
            "verified-contract",
        }
        for value in values
    )
    classified = reviewed_fixed + ai_authored_stem + ai_authored + unreviewed
    return {
        "schema_version": 1,
        "items": len(items),
        "counts": counts,
        "reviewed_fixed_items": reviewed_fixed,
        "ai_authored_items": ai_authored,
        "ai_authored_stem_items": ai_authored_stem,
        "unreviewed_or_builtin_items": unreviewed,
        "unknown_items": len(items) - classified,
    }


def _reference_demand_audit(
    *,
    subject: str,
    paper_number: str,
    items: list[dict[str, Any]],
    preview: bool,
    blueprint: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        capability = generator_capability(subject)
    except ValueError:
        return None
    profile = verified_reference_profile(capability.id, paper_number)
    evidence_context = profile_for_verified_context(profile)
    report = audit_form_demand(items, profile, require_item_evidence=not preview)
    if blueprint is None:
        return report
    from Backend.Core.candidate_paths import (
        audit_candidate_paths,
        topology_from_blueprint,
    )
    from Backend.Core.topic_reference_evidence import audit_topic_bank

    topology = topology_from_blueprint(blueprint, items, capability.id)
    paths = audit_candidate_paths(
        items,
        topology,
        profile,
        evidence_context=evidence_context,
    )
    # Whole printed-item review is separate from candidate selection. Never
    # remove a failed/unreviewed alternative from the review denominator.
    review_failed = [
        name for name in report["failed_checks"] if name.startswith("item_")
    ]
    report["printed_inventory_proxy"] = {
        key: report[key] for key in ("passed", "observed", "distances", "failed_checks")
    }
    report["path_evidence"] = paths
    metric_names = report["observed"].keys()
    report["observed"] = {
        name: {
            key: round(
                sum(row["observed"][name].get(key, 0) for row in paths["paths"])
                / len(paths["paths"]),
                6,
            )
            for key in sorted(
                {key for row in paths["paths"] for key in row["observed"][name]}
            )
        }
        for name in metric_names
    }
    report["observed_weighting_basis"] = (
        "equal-legal-path-descriptive-not-choice-frequency"
    )
    report["gated_distances"] = paths["worst_deviations"]
    report["profile_fit_passed"] = paths["passed"]
    report["evidence_state"] = paths["evidence_state"]
    report["failed_checks"] = review_failed + (
        ["candidate_paths"] if not paths["passed"] else []
    )
    report["passed"] = paths["passed"] and not review_failed
    report["build_eligible"] = not preview and report["passed"]
    if profile.assessment_kind == "question-bank":
        topic = audit_topic_bank(
            items, profile.paper_id.removeprefix("bank-"), profile.topic_records
        )
        report["topic_evidence"] = topic
        report["evidence_state"] = "insufficient"
        report["profile_fit_passed"] = False
        report["passed"] = False
        paths["passed"] = False
        paths["evidence_state"] = "insufficient"
        report["failed_checks"] = [
            *review_failed,
            "topic_reference_evidence_insufficient",
        ]
        # Controller ruling: insufficiency is not a calibration pass nor an
        # exemption from structural, source/content, correctness or review gates.
        structural_failures = [
            failure
            for row in paths["paths"]
            for failure in row["failed_checks"]
            if failure.startswith(("allocated_", "objective_", "section_"))
        ]
        report["build_eligible"] = (
            not preview
            and not review_failed
            and not structural_failures
            and paths["evidence_validation_passed"]
        )
        report["build_gate_basis"] = (
            "Structure/correctness/source-content identity/item review required; topic calibration remains insufficient."
        )
    return report


def _serialise(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        raw = value.model_dump(mode="json")
    elif isinstance(value, dict):
        raw = value
    else:
        raise TypeError("assessment package requires a Pydantic model or mapping")
    if not isinstance(raw, dict):
        raise TypeError("assessment package blueprint must serialise to an object")
    return raw


def _extract_items(
    blueprint: dict[str, Any],
    *,
    subject: str,
    paper_number: str,
) -> list[dict[str, Any]]:
    discovered: list[
        tuple[str, dict[str, Any], list[str], str, dict[str, Any] | None]
    ] = []

    def walk(
        value: Any,
        path: list[str],
        inherited_stems: list[str],
        inherited_kind: str = "",
        inherited_provenance: str = "generator-specific",
        inherited_sql_contract: dict[str, Any] | None = None,
        inherited_candidate_parent: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(value, dict):
            provenance = value.get("provenance", inherited_provenance)
            kind = str(
                value.get("kind")
                or value.get("style_id")
                or value.get("stimulus_kind")
                or inherited_kind
            )
            stems = inherited_stems
            stem = value.get("stem")
            if isinstance(stem, str) and stem.strip():
                stems = [*inherited_stems, stem.strip()]
            source_text = value.get("source_text")
            if isinstance(source_text, str) and source_text.strip():
                stems = [*stems, source_text.strip()]
            stimulus = value.get("stimulus")
            if isinstance(stimulus, dict):
                sql_contract = stimulus.get("sql_contract")
                if isinstance(sql_contract, dict):
                    inherited_sql_contract = sql_contract
                stimulus_code = (
                    render_sql_schema(
                        SQLSourceContract.model_validate(sql_contract, strict=True)
                    )
                    if isinstance(sql_contract, dict)
                    else stimulus.get("code", "")
                )
                source_parts = [
                    *stimulus.get("lines", []),
                    *(cell for row in stimulus.get("rows", []) for cell in row),
                    stimulus_code,
                ]
                stems = [
                    *stems,
                    *(str(part).strip() for part in source_parts if str(part).strip()),
                ]
            if isinstance(stimulus, list):
                stimulus_text = " ".join(
                    str(item).strip() for item in stimulus if str(item).strip()
                )
                if stimulus_text:
                    stems = [*stems, stimulus_text]
            prompt = value.get("prompt")
            marks = value.get("marks")
            parts = value.get("parts")
            has_marked_parts = isinstance(parts, list) and any(
                isinstance(part, dict)
                and isinstance(part.get("prompt"), str)
                and bool(part["prompt"].strip())
                and isinstance(part.get("marks"), int)
                for part in parts
            )
            if (
                isinstance(prompt, str)
                and prompt.strip()
                and isinstance(marks, int)
                and not has_marked_parts
            ):
                discovered_value = {**value, "provenance": provenance}
                intent_id = str(value.get("sql_intent_id", ""))
                if inherited_sql_contract is not None:
                    contract = SQLSourceContract.model_validate(
                        inherited_sql_contract, strict=True
                    )
                    discovered_value["_candidate_source_contract"] = (
                        contract.model_dump(mode="json")
                    )
                    if intent_id:
                        try:
                            intent = contract.intents[intent_id]
                        except KeyError as error:
                            raise ValueError(
                                "exported SQL part refers to an unknown intent"
                            ) from error
                        discovered_value.update(
                            {
                                "_answer_intent": intent.model_dump(mode="json"),
                                "_source_intent_sha256": sql_source_intent_sha256(
                                    contract, intent_id
                                ),
                            }
                        )
                discovered.append(
                    (
                        ".".join(path),
                        discovered_value,
                        stems,
                        kind,
                        inherited_candidate_parent,
                    )
                )
            child_stems = (
                [*stems, prompt.strip()]
                if has_marked_parts and isinstance(prompt, str) and prompt.strip()
                else stems
            )
            for key, child in value.items():
                child_candidate_parent = (
                    value
                    if key in {"parts", "questions"}
                    else inherited_candidate_parent
                )
                walk(
                    child,
                    [*path, str(key)],
                    child_stems,
                    kind,
                    provenance,
                    inherited_sql_contract,
                    child_candidate_parent,
                )
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(
                    child,
                    [*path, str(index)],
                    inherited_stems,
                    inherited_kind,
                    inherited_provenance,
                    inherited_sql_contract,
                    inherited_candidate_parent,
                )

    walk(blueprint, [], [])
    items: list[dict[str, Any]] = []
    for index, (path, raw, stems, kind, candidate_parent) in enumerate(
        discovered, start=1
    ):
        prompt = str(raw["prompt"]).strip()
        item_id = str(
            raw.get("number")
            or raw.get("label")
            or raw.get("rule_id")
            or f"item-{index}"
        )
        scheme = _scheme_text(raw)
        item = {
            "id": f"{item_id}@{path}",
            "subject": subject,
            "paper": paper_number,
            "topic_id": raw.get("topic_id") or (candidate_parent or {}).get("topic_id"),
            "marks": raw["marks"],
            "command_word": raw.get("command_word"),
            "intended_demand": raw.get("intended_demand"),
            "expected_minutes": raw.get("expected_minutes"),
            "task_operation": raw.get("task_operation")
            or (raw.get("authoring_context") or {}).get("task_operation"),
            "source_dependency": raw.get("source_dependency")
            or (raw.get("authoring_context") or {}).get("source_dependency"),
            "reference_source_dependency": raw.get("reference_source_dependency"),
            "kind": kind,
            "prompt": prompt,
            "context": stems,
            "mark_scheme": scheme,
            "assessment_objectives": assessment_objectives_for_item(raw),
            "scheme_mode": raw.get("scheme_mode") or "points",
            "structured_mark_scheme": _structured_scheme(raw),
            "evidence_ids": _evidence_ids(raw),
            "assessment_contract": _assessment_contract(raw),
            "reference_task_contract": raw.get("reference_task_contract"),
            "fingerprint": item_fingerprint(prompt),
            "provenance": raw.get("provenance", "generator-specific"),
            "choices": raw.get("choices") or [],
            "options": raw.get("options") or [],
            "response_slots": raw.get("response_slots") or [],
            "correct_choice": raw.get("correct_choice"),
            "chart_values": raw.get("chart_values") or [],
            "difficulty_evidence": (
                raw.get("difficulty_evidence")
                if isinstance(raw.get("difficulty_evidence"), dict)
                else (
                    raw.get("authoring_context", {}).get("difficulty_evidence", {})
                    if isinstance(raw.get("authoring_context"), dict)
                    else {}
                )
            ),
        }
        if raw.get("_candidate_source_contract"):
            item["candidate_source_contract"] = raw["_candidate_source_contract"]
        if raw.get("_answer_intent"):
            item["answer_intent"] = raw["_answer_intent"]
            item["source_intent_sha256"] = raw["_source_intent_sha256"]
        item["difficulty_candidate_projection"] = (
            _export_difficulty_candidate_projection(
                raw=raw,
                parent=candidate_parent,
                item=item,
                subject=subject,
            ).model_dump(mode="json")
        )
        items.append(item)
    if not items:
        raise ValueError("assessment blueprint contains no marked question items")
    return items


def _export_difficulty_candidate_projection(
    *,
    raw: dict[str, Any],
    parent: dict[str, Any] | None,
    item: dict[str, Any],
    subject: str,
) -> object:
    if isinstance(parent, dict) and parent.get("style_id") and parent.get("parts"):
        return aqa_cs_difficulty_candidate(parent, raw)
    edexcel_parent = (
        parent
        if isinstance(parent, dict) and "section" in parent
        else raw
        if "section" in raw
        else None
    )
    if isinstance(edexcel_parent, dict) and (
        "source_instance" in edexcel_parent or "source_reference" in edexcel_parent
    ):
        return edexcel_difficulty_candidate_projection(
            question=edexcel_parent,
            part=raw,
            review_content=item,
        )
    if isinstance(parent, dict) and isinstance(parent.get("questions"), list):
        return shared_difficulty_candidate_projection(
            question=raw,
            option=parent,
        )
    return difficulty_candidate_projection(
        route=f"export-{subject.casefold().replace(' ', '-')}",
        review_content=item,
        identity_content=raw,
    )


def _scheme_text(raw: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for key in ("mark_scheme", "indicative_content"):
        value = raw.get(key)
        if isinstance(value, list):
            result.extend(str(item).strip() for item in value if str(item).strip())
    if result:
        return list(dict.fromkeys(result))
    marking = raw.get("marking")
    if isinstance(marking, dict):
        for key in ("points", "accept", "reject", "levels"):
            value = marking.get(key)
            if isinstance(value, list):
                result.extend(str(item).strip() for item in value if str(item).strip())
        if result:
            return result
    breakdown = str(raw.get("mark_breakdown", "")).strip()
    return [breakdown] if breakdown else []


def _structured_scheme(raw: dict[str, Any]) -> list[dict[str, Any]]:
    structured = raw.get("structured_mark_scheme")
    if isinstance(structured, list):
        return [point for point in structured if isinstance(point, dict)]
    marking = raw.get("marking")
    if not isinstance(marking, dict):
        return []
    objective = str(marking.get("ao", "")).upper() or None
    accepts = [str(value) for value in marking.get("accept", [])]
    rejects = [str(value) for value in marking.get("reject", [])]
    levels = [str(value) for value in marking.get("levels", [])]
    points = [str(value) for value in marking.get("points", [])]
    result = [
        {
            "text": point,
            "marks": 0,
            "credit_type": "point",
            "assessment_objective": objective,
            "alternatives": accepts,
            "do_not_accept": rejects,
        }
        for point in points
    ]
    result.extend(
        {
            "text": level,
            "marks": 0,
            "credit_type": "level",
            "assessment_objective": objective,
        }
        for level in levels
    )
    return result


def _evidence_ids(raw: dict[str, Any]) -> list[str]:
    values: list[str] = []
    references = raw.get("source_references")
    if isinstance(references, list):
        values.extend(str(value).strip() for value in references)
    reference = str(raw.get("source_reference", "")).strip()
    if reference:
        values.append(reference)
    contract = raw.get("contract")
    if isinstance(contract, dict):
        allowed = contract.get("allowed_evidence_ids")
        if isinstance(allowed, list):
            values.extend(str(value).strip() for value in allowed)
    return list(dict.fromkeys(value for value in values if value))


def _assessment_contract(raw: dict[str, Any]) -> dict[str, Any]:
    instance_contract = raw.get("assessment_contract")
    if isinstance(instance_contract, dict) and instance_contract:
        return instance_contract
    contract = raw.get("contract")
    if isinstance(contract, dict):
        return contract
    context = raw.get("authoring_context")
    if not isinstance(context, dict):
        return {}
    fields = (
        "expected_answer_form",
        "completion_time_minutes",
        "prerequisite_knowledge",
        "misconception_targets",
        "observable_mark_points",
        "valid_alternatives",
        "partial_credit_boundaries",
        "common_errors",
        "follow_through_rules",
        "level_policy_id",
    )
    return {field: context[field] for field in fields if field in context}


@lru_cache(maxsize=1)
def _level_policies() -> dict[str, Any]:
    return load_level_policies(
        REPO_ROOT / "Resources" / "level-of-response-policies.json"
    )


def _validate_response_bands(item: dict[str, Any]) -> dict[str, Any] | None:
    if item.get("scheme_mode") != "levels":
        return None
    contract = item.get("assessment_contract")
    if not isinstance(contract, dict):
        return None
    policy_id = contract.get("level_policy_id")
    if not isinstance(policy_id, str) or not policy_id:
        return None
    try:
        policy = _level_policies()[policy_id]
    except KeyError as error:
        raise ValueError(
            f"assessment item {item.get('id')} uses unknown level policy {policy_id}"
        ) from error
    points = contract.get("observable_mark_points")
    if not isinstance(points, list) or not points:
        points = [
            str(point.get("text", "")).strip()
            for point in item.get("structured_mark_scheme", [])
            if isinstance(point, dict)
            and int(point.get("marks", 0) or 0) > 0
            and str(point.get("text", "")).strip()
        ]
    if not points:
        raise ValueError(
            f"assessment item {item.get('id')} cannot simulate level responses "
            "without observable mark points"
        )
    simulated_item = {
        "id": item.get("id"),
        "prompt": item.get("prompt"),
        "authoring_context": {
            "observable_mark_points": points,
            "misconception_targets": contract.get("misconception_targets", []),
        },
    }
    responses = ResponseSimulator().responses(simulated_item)
    scaled = scale_level_policy(policy, int(item["marks"]))
    decisions = [
        LevelOfResponseEngine().mark(response, scaled) for response in responses
    ]
    marks = [decision.mark for decision in decisions]
    if any(left >= right for left, right in pairwise(marks)):
        raise ValueError(
            f"assessment item {item.get('id')} level scheme cannot distinguish "
            f"weak, average and excellent responses: {marks}"
        )
    if any(
        len(decision.annotations) != scaled.maximum_mark
        or any(not annotation.reason for annotation in decision.annotations)
        for decision in decisions
    ):
        raise ValueError(
            f"assessment item {item.get('id')} has incomplete mark annotations"
        )
    return {
        "item_id": item.get("id"),
        "policy_id": policy_id,
        "bands": [response.band for response in responses],
        "marks": marks,
        "monotonic": True,
        "annotations_complete": True,
    }


def validate_cross_paper_quality(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate cross-item clues and return the paper's assessment balance."""

    topics: Counter[str] = Counter()
    objectives: Counter[str] = Counter()
    commands: Counter[str] = Counter()
    demand: Counter[str] = Counter()
    fingerprints: set[tuple[str, str]] = set()
    total_marks = 0
    for item in items:
        item_id = str(item.get("id", "unknown"))
        prompt = str(item.get("prompt", "")).strip()
        normalised = " ".join(prompt.casefold().split())
        context = item.get("context")
        context_key = (
            " ".join(" ".join(str(value).casefold().split()) for value in context)
            if isinstance(context, list)
            else ""
        )
        fingerprint = (normalised, context_key)
        if fingerprint in fingerprints:
            raise ValueError(f"cross-paper duplication at item {item_id}")
        fingerprints.add(fingerprint)
        if re.search(
            r"\b(?:the\s+)?correct answer\s+is\b|\banswer\s*:", prompt, re.IGNORECASE
        ):
            raise ValueError(f"assessment item {item_id} contains answer leakage")
        if re.match(
            r"^(?:it|they|this|these|those)\s+"
            r"(?:is|are|was|were|causes?|means?|shows?|suggests?)\b",
            prompt,
            re.IGNORECASE,
        ) and not (
            isinstance(context, list) and any(str(value).strip() for value in context)
        ):
            raise ValueError(
                f"assessment item {item_id} has an ambiguous opening pronoun"
            )
        if _contains_non_finite(item):
            raise ValueError(f"assessment item {item_id} contains non-finite data")
        marks = int(item.get("marks", 0) or 0)
        total_marks += marks
        topic = str(item.get("topic_id", "") or "unclassified")
        command = str(item.get("command_word", "") or "unclassified")
        band = str(item.get("intended_demand", "") or "unclassified")
        topics[topic] += marks
        commands[command] += 1
        demand[band] += 1
        for objective, allocated in dict(
            item.get("assessment_objectives") or {}
        ).items():
            objectives[str(objective)] += int(allocated)
    return {
        "items": len(items),
        "total_marks": total_marks,
        "topics_by_mark": dict(sorted(topics.items())),
        "assessment_objectives": dict(sorted(objectives.items())),
        "command_words": dict(sorted(commands.items())),
        "demand": dict(sorted(demand.items())),
        "duplicates": 0,
        "answer_leakage": 0,
        "ambiguous_opening_pronouns": 0,
        "non_finite_data": 0,
    }


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_non_finite(item) for item in value)
    return False


def _form_id(
    *,
    subject: str,
    paper_number: str,
    items: list[dict[str, Any]],
) -> str:
    identity = {
        "subject": subject,
        "paper": paper_number,
        "items": [
            {
                "id": item.get("id"),
                "marks": item.get("marks"),
                "fingerprint": item.get("fingerprint"),
                "mark_scheme": item.get("mark_scheme"),
            }
            for item in items
        ],
    }
    digest = hashlib.sha256(
        json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"{subject}-{paper_number}-{digest[:20]}"
