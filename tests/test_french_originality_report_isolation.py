"""Originality evidence must not expose mutable screening policy."""

import json

import pytest

from Backend.Core.france import originality


@pytest.fixture
def policy(monkeypatch):
    # Isolate the genuine red mutation from other tests in this interpreter.
    baseline = dict(originality.THRESHOLDS)
    monkeypatch.setattr(originality, "THRESHOLDS", dict(baseline))
    return baseline


def candidate():
    return (
        "Un observatoire étudie les déplacements de tortues marines. "
        "Construire le graphe des stations et justifier un itinéraire minimal."
    )


def test_reports_have_independent_policy_snapshots(policy):
    first = originality.screen_originality(candidate(), [])
    second = originality.screen_originality(candidate(), [])
    assert first["thresholds"] is not originality.THRESHOLDS
    assert first["thresholds"] is not second["thresholds"]
    first["thresholds"]["contiguous_characters"] = 1_000_000
    assert second["thresholds"] == policy
    assert policy == originality.THRESHOLDS


def test_mutating_a_report_cannot_disable_later_copy_refusal(policy):
    report = originality.screen_originality(candidate(), [])
    for name in report["thresholds"]:
        report["thresholds"][name] = 1_000_000
    with pytest.raises(originality.SimilarityRejected, match="originalité"):
        originality.screen_originality(candidate(), [candidate()])
    assert policy == originality.THRESHOLDS


def test_serialized_report_keeps_existing_policy_and_counts(policy):
    report = originality.screen_originality(candidate(), [])
    saved = json.loads(json.dumps(report))
    assert saved["state"] == "passed_calibrated_screen"
    assert saved["calibration_set"] == "fr-nsi-labelled-v1"
    assert saved["thresholds"] == policy
    assert saved["maximum_scores"] == {name: 0 for name in policy}
    assert saved["comparison_counts"] == {"references": 0, "previous_generations": 0}
    assert saved["copyright_guarantee"] is False
    assert saved["teacher_review_required"] is True
