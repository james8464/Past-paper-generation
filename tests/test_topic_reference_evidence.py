import importlib

import pytest


def module():
    return importlib.import_module("Backend.Core.topic_reference_evidence")


@pytest.mark.parametrize(
    "topic,count,marks,ao",
    [
        ("4.2", 19, 42, {"AO1": 34, "AO2": 8, "AO3": 0}),
        ("4.10", 18, 47, {"AO1": 9, "AO2": 24, "AO3": 14}),
        ("4.12", 12, 19, {"AO1": 4, "AO2": 15, "AO3": 0}),
    ],
)
def test_reviewed_core_preserves_audited_subparts_and_unknown_features(
    topic, count, marks, ao
):
    records = [
        r for r in module().reviewed_topic_records(topic) if r["stratum"] == "core"
    ]
    assert len(records) == count
    assert sum(r["marks"] for r in records) == marks
    assert {
        key: sum(r["assessment_objectives"].get(key, 0) for r in records) for key in ao
    } == ao
    assert all(
        r["reasoning_steps"] is None
        and r["observed_minutes"] is None
        and r["learner_demand"] is None
        for r in records
    )
    assert all(
        len(r["question_sha256"]) == len(r["scheme_sha256"]) == 64 for r in records
    )


def test_mixed_structure_anchors_are_task_matched_not_pooled():
    records = module().reviewed_topic_records("4.2")
    robust = [r for r in records if r["stratum"] == "mixed" and r["context_complete"]]
    assert len(robust) == 6
    assert sum(r["marks"] for r in robust) == 26
    assert module().matching_records(
        records, {"topic_id": "4.2", "operation": "trace", "mode": "table"}
    )
    assert not module().matching_records(
        records, {"topic_id": "4.2", "operation": "program", "mode": "code"}
    )
    assert not module().matching_records(
        records, {"topic_id": "4.10", "operation": "trace", "mode": "table"}
    )


def test_incomplete_context_and_keyword_only_membership_are_ineligible():
    records = module().reviewed_topic_records("4.2")
    assert all(
        r["context_complete"]
        for r in module().matching_records(
            records, {"topic_id": "4.2", "operation": "analyse", "mode": "prose"}
        )
    )
    assert (
        module().task_features(
            {
                "topic_id": "4.10",
                "task_operation": "analyse",
                "prompt": "Explain the REST resource and JSON encoding",
                "kind": "sql_normalisation",
            }
        )["topic_id"]
        is None
    )
    assert (
        module().task_features(
            {
                "topic_id": "4.12",
                "task_operation": "trace",
                "prompt": "Trace this imperative graph traversal",
                "kind": "graph_traversal",
            }
        )["topic_id"]
        is None
    )


def test_sparse_bank_is_insufficient_with_cluster_sensitivity_not_calibrated():
    data = [
        {
            "id": "a",
            "topic_id": "4.2",
            "marks": 6,
            "task_operation": "trace",
            "kind": "data_structures_tree",
            "prompt": "Trace the tree traversal in the table",
            "response_slots": ["state"],
        }
    ]
    report = module().audit_topic_bank(
        data, "4.2", module().reviewed_topic_records("4.2")
    )
    assert report["evidence_state"] == "insufficient"
    assert report["passed"] is False
    assert report["coverage"]["matched_items"] == 1
    assert len(report["cluster_sensitivity"]["leave_one_year_out"]) == 4
    assert report["whole_topic_qualified"] is False
    sensitivity = report["cluster_sensitivity"]
    assert len(sensitivity["admitted_mixed_ids"]) == 3
    assert "complete-code:code" not in sensitivity["pooled_parts"]
