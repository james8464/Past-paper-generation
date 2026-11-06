"""Synthetic reader invariants, not real learner or specialist approval evidence."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from Backend.Core import psychometrics as subject


def policy_path(tmp_path, status):
    payload = json.loads(
        Path("Resources/empirical-calibration-policy.json").read_text()
    )
    payload.update(
        status=status,
        approved_by_identity_class="assessment-specialist"
        if status == "approved"
        else None,
        approval_evidence="SYNTHETIC-TEST-NOT-REAL-POLICY-APPROVAL"
        if status == "approved"
        else None,
    )
    path = tmp_path / "SYNTHETIC-policy.json"
    path.write_text(json.dumps(payload))
    return path


def report(policy, declared):
    checks = {
        name: True
        for name in (
            "candidate_sample",
            "item_coverage",
            "facility_range",
            "internal_consistency",
            "marker_standardisation",
            "group_fairness_screen",
            "independent_manual_review",
        )
    }
    checks["policy_approved"] = declared
    payload = {
        "schema_version": 1,
        "fixture_classification": "SYNTHETIC INVARIANT TEST: NOT LEARNER OR REVIEW EVIDENCE",
        "family": "owned-synthetic/family",
        "paper": "owned",
        "form_id": "synthetic-form",
        "sample": {"candidates": 0},
        "policy": policy.summary(),
        "thresholds": dict(policy.thresholds),
        "checks": checks,
        "difficulty_independently_verified": all(
            value is True for value in checks.values()
        ),
    }
    payload["evidence_fingerprint"] = subject.evidence_fingerprint(payload)
    return payload


def read(tmp_path, payload, policy):
    path = tmp_path / "SYNTHETIC-calibration.json"
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    try:
        return subject.validate_calibration(
            path,
            family=payload["family"],
            paper=payload["paper"],
            form_id=payload["form_id"],
            policy_path=policy,
        )
    finally:
        assert path.read_bytes() == before


def test_draft_policy_cannot_be_promoted_by_recomputed_saved_checks(tmp_path):
    path = policy_path(tmp_path, "draft")
    policy = subject.load_calibration_policy(path)
    assert policy.approved is False
    payload = report(policy, True)
    assert payload["difficulty_independently_verified"] is True
    with pytest.raises(ValueError, match="policy approval"):
        read(tmp_path, payload, path)


@pytest.mark.parametrize(
    "status,expected", [("draft", False), ("approved", True), ("retired", False)]
)
def test_consistent_saved_policy_check_remains_readable(tmp_path, status, expected):
    path = policy_path(tmp_path, status)
    policy = subject.load_calibration_policy(path)
    payload = report(policy, expected)
    before = deepcopy(payload)
    summary = read(tmp_path, payload, path)
    assert summary["difficulty_independently_verified"] is expected
    assert summary["checks"]["policy_approved"] is expected
    assert payload == before


@pytest.mark.parametrize("declared", [0, 1, None, "false", "true", [], {}])
@pytest.mark.parametrize("status", ["draft", "approved"])
def test_policy_check_requires_exact_boolean_identity(tmp_path, status, declared):
    path = policy_path(tmp_path, status)
    policy = subject.load_calibration_policy(path)
    with pytest.raises(ValueError, match="policy approval"):
        read(tmp_path, report(policy, declared), path)


def test_approved_policy_cannot_keep_a_contradictory_false_check(tmp_path):
    path = policy_path(tmp_path, "approved")
    policy = subject.load_calibration_policy(path)
    with pytest.raises(ValueError, match="policy approval"):
        read(tmp_path, report(policy, False), path)


def test_stale_fingerprint_still_refuses_before_policy_check(tmp_path):
    path = policy_path(tmp_path, "draft")
    payload = report(subject.load_calibration_policy(path), False)
    payload["checks"]["policy_approved"] = True
    with pytest.raises(ValueError, match="fingerprint"):
        read(tmp_path, payload, path)


@pytest.mark.parametrize("field", ["policy", "thresholds"])
def test_recomputed_fingerprint_cannot_replace_current_policy(tmp_path, field):
    path = policy_path(tmp_path, "draft")
    payload = report(subject.load_calibration_policy(path), False)
    if field == "policy":
        payload["policy"]["policy_id"] = "synthetic-other-policy"
    else:
        payload["thresholds"]["minimum_candidates"] += 1
    payload["evidence_fingerprint"] = subject.evidence_fingerprint(
        {key: value for key, value in payload.items() if key != "evidence_fingerprint"}
    )
    with pytest.raises(ValueError, match="policy"):
        read(tmp_path, payload, path)
