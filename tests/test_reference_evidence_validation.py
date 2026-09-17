import copy
import json
from pathlib import Path

import pytest

from Backend.Core.candidate_paths import audit_candidate_paths
from Backend.Core.reference_demand import (
    ReferenceDemandDocument,
    ReferenceDemandProfile,
    audit_form_demand,
    profile_for,
)
from tests.test_reference_demand import profile_payload


def document(raw):
    return {
        "schema_version": 3,
        "purpose": "Malformed H3 evidence must remain rejected",
        "derived_aggregate_only": True,
        "retains_source_text": False,
        "profiles": [raw],
    }


def test_schema_three_rejects_both_review_reproductions():
    raw = profile_payload()
    with pytest.raises(ValueError):
        ReferenceDemandDocument.model_validate(document(raw))
    raw.update(
        evidence_policy_id="unknown-policy",
        reference_forms=[
            {
                "id": "x",
                "status": "eligible",
                "comparable_metrics": ["mark_band_distribution"],
                "paths": [
                    {"id": "x", "observed": {"mark_band_distribution": {"short": 1}}}
                ],
            }
        ],
    )
    with pytest.raises(ValueError):
        ReferenceDemandDocument.model_validate(document(raw))


@pytest.mark.parametrize(
    "mutation",
    [
        "policy",
        "hash",
        "metrics",
        "topology",
        "paths",
        "item",
        "distribution",
        "unknown_steps",
    ],
)
def test_h3_nested_evidence_rejects_stale_partial_or_unknown_data(mutation):
    raw = json.loads(Path("Resources/reference-demand-profiles.json").read_text())
    raw["profiles"] = [
        next(
            p
            for p in raw["profiles"]
            if p["family_id"] == "aqa/economics" and p["paper_id"] == "1"
        )
    ]
    form = raw["profiles"][0]["reference_forms"][0]
    if mutation == "policy":
        raw["profiles"][0]["evidence_policy_id"] = "unknown-policy"
    elif mutation == "hash":
        form.pop("source_sha256")
    elif mutation == "metrics":
        form["comparable_metrics"] = ["mark_band_distribution"]
    elif mutation == "topology":
        form["topology"]["sections"][0]["answer_options"] = 2
    elif mutation == "paths":
        form["paths"].pop()
    elif mutation == "item":
        form["items"][0]["marks"] += 1
    elif mutation == "distribution":
        form["paths"][0]["observed"]["response_mode_distribution"] = {"recall": 1.0}
    else:
        form["items"][0]["reasoning_steps"] = 1
    with pytest.raises(ValueError):
        ReferenceDemandDocument.model_validate(raw)


def test_explicit_legacy_still_loads_but_never_qualifies_unknown_paths():
    raw = profile_payload()
    item = {
        "id": "x",
        "marks": 80,
        "expected_minutes": 120,
        "command_word": "Explain",
        "assessment_objectives": {"AO1": 15, "AO2": 22, "AO3": 25, "AO4": 18},
        "intended_demand": "standard",
    }
    observed = audit_form_demand([item], ReferenceDemandProfile.model_validate(raw))[
        "observed"
    ]
    for name in set(raw) & set(observed):
        raw[name] = observed[name]
    payload = document(raw)
    payload["schema_version"] = 2
    profile = ReferenceDemandDocument.model_validate(payload).profiles[0]
    topology = {
        "policy_id": "candidate-paths-v1",
        "total_marks": 80,
        "duration_minutes": 120,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 80,
                "options": [{"id": "a", "item_ids": ["x"]}],
            }
        ],
    }
    result = audit_candidate_paths([item], topology, profile)
    assert result["passed"] is False
    assert result["evidence_state"] == "insufficient"
    assert result["failed_paths"]


def test_checked_in_h3_profiles_are_valid():
    schema = json.loads(
        Path("Resources/reference-demand-profile.schema.json").read_text()
    )
    assert "evidence_policy_id" in schema["properties"]["profiles"]["items"]["required"]
    assert {
        "SourceForm",
        "SourcePath",
        "SourceItem",
        "TopicRecord",
        "CandidateTopology",
    } <= schema["$defs"].keys()
    ReferenceDemandDocument.model_validate_json(
        Path("Resources/reference-demand-profiles.json").read_text()
    )


def test_mutated_unknown_policy_cannot_bypass_direct_audit():
    profile = ReferenceDemandProfile.model_validate(profile_payload())
    profile.evidence_policy_id = "unknown-policy"
    profile.reference_forms = [
        {
            "id": "x",
            "status": "eligible",
            "comparable_metrics": ["mark_band_distribution"],
            "paths": [
                {"id": "x", "observed": {"mark_band_distribution": {"short": 1.0}}}
            ],
        }
    ]
    item = {
        "id": "x",
        "marks": 1,
        "expected_minutes": 1,
        "assessment_objectives": {"AO1": 1},
        "command_word": "State",
    }
    topology = {
        "policy_id": "test",
        "total_marks": 1,
        "duration_minutes": 1,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 1,
                "options": [{"id": "a", "item_ids": ["x"]}],
            }
        ],
    }
    result = audit_candidate_paths([item], topology, profile)
    assert result["evidence_validation_passed"] is False
    assert result["passed"] is False and result["evidence_state"] == "insufficient"
    assert result["failed_paths"]


def test_direct_profile_cannot_qualify_after_private_version_marker_mutation():
    """Only membership in a validated schema-3 document may qualify H3 evidence."""
    profile = profile_for("aqa/economics", "3").model_copy(deep=True)
    profile._document_schema_version = 3
    item = {
        "id": "x",
        "marks": 1,
        "expected_minutes": 1,
        "assessment_objectives": {"AO1": 1},
        "command_word": "State",
    }
    topology = {
        "policy_id": "test",
        "total_marks": 1,
        "duration_minutes": 1,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 1,
                "options": [{"id": "a", "item_ids": ["x"]}],
            }
        ],
    }

    result = audit_candidate_paths([item], topology, profile)

    assert result["evidence_validation_passed"] is False
    assert result["evidence_state"] == "insufficient"


def test_model_copied_document_cannot_promote_a_valid_profile_to_schema_three():
    """`model_copy(update=...)` does not re-run schema-three evidence validation."""
    checked_in = json.loads(Path("Resources/reference-demand-profiles.json").read_text())
    source = ReferenceDemandDocument.model_validate(
        {
            **checked_in,
            "profiles": [
                next(
                    profile
                    for profile in checked_in["profiles"]
                    if profile["family_id"] == "aqa/economics"
                    and profile["paper_id"] == "3"
                )
            ],
        }
    )
    legacy = ReferenceDemandDocument.model_validate(
        {
            "schema_version": 2,
            "purpose": "Legacy aggregate data cannot qualify source evidence.",
            "derived_aggregate_only": True,
            "retains_source_text": False,
            "profiles": [profile_payload()],
        }
    )
    forged = legacy.model_copy(
        update={
            "schema_version": 3,
            "profiles": [source.profiles[0].model_copy(deep=True)],
        }
    )
    item = {
        "id": "x",
        "marks": 1,
        "expected_minutes": 1,
        "assessment_objectives": {"AO1": 1},
        "command_word": "State",
    }
    topology = {
        "policy_id": "test",
        "total_marks": 1,
        "duration_minutes": 1,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 1,
                "options": [{"id": "a", "item_ids": ["x"]}],
            }
        ],
    }

    result = audit_candidate_paths(
        [item], topology, forged.profiles[0], evidence_document=forged
    )

    assert result["evidence_validation_passed"] is False
    assert result["evidence_state"] == "insufficient"


def test_public_evidence_api_cannot_attest_a_forged_document():
    """Only ReferenceDemandDocument validation may create an H3 attestation."""
    import Backend.Core.reference_evidence as evidence

    assert not hasattr(evidence, "attest_validated_document")


def test_profile_list_mutation_invalidates_a_schema_three_document_attestation():
    """Qualification cannot survive a post-validation profile-list mutation."""
    checked_in = json.loads(Path("Resources/reference-demand-profiles.json").read_text())
    document = ReferenceDemandDocument.model_validate(
        {
            **checked_in,
            "profiles": [
                next(
                    profile
                    for profile in checked_in["profiles"]
                    if profile["family_id"] == "aqa/economics"
                    and profile["paper_id"] == "3"
                )
            ],
        }
    )
    document.profiles.append(document.profiles[0].model_copy(deep=True))
    item = {
        "id": "x",
        "marks": 1,
        "expected_minutes": 1,
        "assessment_objectives": {"AO1": 1},
        "command_word": "State",
    }
    topology = {
        "policy_id": "test",
        "total_marks": 1,
        "duration_minutes": 1,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 1,
                "options": [{"id": "a", "item_ids": ["x"]}],
            }
        ],
    }

    result = audit_candidate_paths(
        [item], topology, document.profiles[0], evidence_document=document
    )

    assert result["evidence_validation_passed"] is False
    assert result["evidence_state"] == "insufficient"


def test_schema_two_document_rejects_copied_h3_source_evidence():
    raw = json.loads(Path("Resources/reference-demand-profiles.json").read_text())
    profile_raw = next(
        profile
        for profile in raw["profiles"]
        if profile["family_id"] == "aqa/economics" and profile["paper_id"] == "3"
    )
    with pytest.raises(ValueError):
        ReferenceDemandDocument.model_validate(
            {
                "schema_version": 2,
                "purpose": raw["purpose"],
                "derived_aggregate_only": True,
                "retains_source_text": False,
                "profiles": [copy.deepcopy(profile_raw)],
            }
        )


def test_outer_reference_document_rejects_unknown_fields():
    payload = document(profile_payload())
    payload["unexpected"] = True
    with pytest.raises(ValueError):
        ReferenceDemandDocument.model_validate(payload)
