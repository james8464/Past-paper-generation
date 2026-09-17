import importlib
from pathlib import Path

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
                "reference_task_contract": {
                    "policy_id": "aqa-cs-topic-evidence-v1",
                    "topic_id": "4.2",
                    "style_id": "data_structures_tree",
                    "operation": "trace",
                    "response_mode": "table",
                    "source_dependency": "self-contained",
                },
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


def test_real_bank_explanation_drawing_and_stack_are_not_false_table_matches():
    from cspapergen.generator import build_topic_question_bank
    from cspapergen.syllabus import load_syllabus

    from Backend.Core.assessment_package import _extract_items

    syllabus = load_syllabus(
        Path("Resources/computer-science/aqa/generator/data/syllabus_seed.json")
    )
    paper = build_topic_question_bank(syllabus, topic_id="4.2", seed=111)
    items = _extract_items(
        paper.model_dump(mode="json"),
        subject="computer_science",
        paper_number="bank-4.2",
    )
    by_id = {item["id"]: item for item in items}
    explanation = module().task_features(by_id["3@questions.3.parts.2"])
    assert explanation == {"topic_id": "4.2", "operation": "analyse", "mode": "prose"}
    drawing = module().task_features(by_id["1@questions.2.parts.0"])
    assert drawing == {"topic_id": "4.2", "operation": "represent", "mode": "diagram"}
    stack = module().task_features(by_id["1@questions.0.parts.0"])
    assert stack["mode"] == "sequence"
    assert not module().matching_records(
        module().reviewed_topic_records("4.2"), drawing
    )
    assert not module().matching_records(module().reviewed_topic_records("4.2"), stack)


@pytest.mark.parametrize(
    "item",
    [
        {
            "topic_id": "4.12",
            "task_operation": "trace",
            "kind": "recursion",
            "prompt": "Trace this function by completing the table.",
            "context": [
                "An imperative graph traversal visits each vertex, adding neighbours to a visited set."
            ],
        },
        {
            "topic_id": "4.10",
            "task_operation": "explain",
            "kind": "sql_normalisation",
            "prompt": "Explain the format used by this service.",
            "context": ["A RESTful web service returns XML documents."],
        },
        {
            "topic_id": "4.12",
            "task_operation": "trace",
            "prompt": "Trace this function by completing the table.",
        },
    ],
)
def test_task_and_context_must_establish_topic_membership(item):
    assert not module().matching_records(
        module().reviewed_topic_records(item["topic_id"]), module().task_features(item)
    )


def test_actual_same_topic_operation_and_mode_still_matches():
    item = {
        "topic_id": "4.10",
        "task_operation": "program",
        "kind": "sql_normalisation",
        "prompt": "Write one SELECT query for this relational database.",
        "context": ["A relational database stores bookings."],
        "reference_task_contract": {
            "policy_id": "aqa-cs-topic-evidence-v1",
            "topic_id": "4.10",
            "style_id": "sql_normalisation",
            "operation": "program",
            "response_mode": "query",
            "source_dependency": "task-context",
        },
    }
    assert module().matching_records(
        module().reviewed_topic_records("4.10"), module().task_features(item)
    )


@pytest.mark.parametrize(
    "item",
    [
        {
            "topic_id": "4.2",
            "task_operation": "analyse",
            "kind": "data_structures_graph",
            "prompt": "Explain why a relational database normalisation procedure should not use an adjacency matrix.",
        },
        {
            "topic_id": "4.12",
            "task_operation": "explain",
            "kind": "functional_programming",
            "prompt": "Explain how a relational database can store the result of a lambda expression.",
        },
    ],
)
def test_inherited_metadata_and_incidental_keywords_never_establish_topic_membership(item):
    task = module().task_features(item)
    assert task["topic_id"] is None
    assert not module().matching_records(module().reviewed_topic_records(item["topic_id"]), task)


def test_topic_contract_rejects_cross_topic_prompt_even_when_metadata_agrees():
    item = {
        "topic_id": "4.2",
        "task_operation": "analyse",
        "kind": "data_structures_graph",
        "prompt": "Explain why a relational database normalisation procedure should not use an adjacency matrix.",
        "reference_task_contract": {
            "policy_id": "aqa-cs-topic-evidence-v1",
            "topic_id": "4.2",
            "style_id": "data_structures_graph",
            "operation": "analyse",
            "response_mode": "prose",
            "source_dependency": "self-contained",
        },
    }
    assert module().task_features(item)["topic_id"] is None


def test_topic_contract_cannot_relabel_the_question_operation_or_response_form():
    """A serialised hint must never override the question that will be printed."""
    item = {
        "topic_id": "4.2",
        "task_operation": "analyse",
        "kind": "data_structures_tree",
        "prompt": "Explain why the binary search tree remains balanced.",
        "reference_task_contract": {
            "policy_id": "aqa-cs-topic-evidence-v1",
            "topic_id": "4.2",
            "style_id": "data_structures_tree",
            "operation": "trace",
            "response_mode": "table",
            "source_dependency": "self-contained",
        },
    }

    assert module().task_features(item) == {
        "topic_id": None,
        "operation": "unknown",
        "mode": "unknown",
    }


def test_topic_contract_rejects_unknown_serialised_fields():
    """Only the versioned contract may establish a reference comparison."""
    item = {
        "topic_id": "4.2",
        "task_operation": "explain",
        "kind": "data_structures_tree",
        "prompt": "Explain why a binary search tree remains balanced.",
        "reference_task_contract": {
            "policy_id": "aqa-cs-topic-evidence-v1",
            "topic_id": "4.2",
            "style_id": "data_structures_tree",
            "operation": "explain",
            "response_mode": "prose",
            "source_dependency": "self-contained",
            "unreviewed_override": "trace:table",
        },
    }

    assert module().task_features(item)["topic_id"] is None
