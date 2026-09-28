import importlib
from pathlib import Path

import pytest


def module():
    return importlib.import_module("Backend.Core.topic_reference_evidence")


def bank_items(topic, seed=111):
    from cspapergen.generator import build_topic_question_bank
    from cspapergen.syllabus import load_syllabus

    from Backend.Core.assessment_package import _extract_items

    syllabus = load_syllabus(Path("Resources/computer-science/aqa/generator/data/syllabus_seed.json"))
    paper = build_topic_question_bank(syllabus, topic_id=topic, seed=seed)
    return _extract_items(paper.model_dump(mode="json"), subject="computer_science", paper_number=f"bank-{topic}")


@pytest.mark.parametrize("topic", ["4.2", "4.10", "4.12"])
def test_source_backed_bank_qualifies_only_its_generated_items(topic):
    items = bank_items(topic)
    report = module().audit_topic_bank(items, topic, module().reviewed_topic_records(topic))
    assert report["passed"], report["coverage"]
    assert report["qualification_scope"] == "generated-items"
    assert report["whole_topic_qualified"] is False
    assert report["empirical_equivalence_claimed"] is False
    assert report["coverage"]["matched_items"] == len(items)
    assert sum(item["marks"] for item in items) == 30


def test_forged_or_sparse_source_inventory_cannot_qualify_bank():
    from copy import deepcopy
    records = module().reviewed_topic_records("4.10")
    items = bank_items("4.10")
    tampered = deepcopy(records)
    tampered[0]["question_sha256"] = "0" * 64
    for invalid in (tampered, records[:1], [{}], []):
        report = module().audit_topic_bank(items, "4.10", invalid)
        assert report["passed"] is False
        assert report["evidence_validation_passed"] is False


def test_same_operation_in_different_structure_does_not_support_a_task():
    items = bank_items("4.2")
    item = items[0]
    item.update(prompt="Describe the insertion process for a hash table.")
    # A serialised queue contract must not turn unrelated hash content into queue evidence.
    report = module().audit_topic_bank(items, "4.2", module().reviewed_topic_records("4.2"))
    assert report["passed"] is False
    assert item["id"] in report["coverage"]["unmatched_item_ids"]


@pytest.mark.parametrize("topic,index,mutation", [
    ("4.12", 0, "blank"), ("4.12", 0, "stem-only"),
    ("4.12", 0, "missing-values"), ("4.12", 0, "unrelated-trace"),
    ("4.12", 3, "stem-only"), ("4.12", 9, "stem-only"),
    ("4.2", 2, "code-construction"), ("4.2", 5, "stem-only"),
    ("4.10", 0, "stem-only"), ("4.10", 8, "empty"),
    ("4.10", 8, "incomplete-scenario"),
])
def test_reviewed_support_requires_substantive_task_linked_context(topic, index, mutation):
    items = bank_items(topic)
    item = items[index]
    if mutation == "blank":
        item["context"] = [" "]
    elif mutation == "empty":
        item["context"] = []
    elif mutation == "stem-only":
        item["context"] = item["context"][:1]
    elif mutation == "missing-values":
        item["context"][-1] = "\n".join(item["context"][-1].splitlines()[1:])
    elif mutation == "unrelated-trace":
        item["prompt"] = "Complete a trace table for the electron energy values."
    elif mutation == "code-construction":
        item["prompt"] = "Write code to insert a new key into a hash table using linear probing."
    else:
        item["context"] = ["A workshop provider records clients and their registrations."]
    report = module().audit_topic_bank(items, topic, module().reviewed_topic_records(topic))
    assert not report["passed"]
    assert item["id"] in report["coverage"]["unmatched_item_ids"]


def test_relational_design_declares_its_scenario_dependency():
    item = bank_items("4.10")[8]
    assert item["reference_source_dependency"] == "task-context"
    assert item["reference_task_contract"]["source_dependency"] == "task-context"


def test_preview_seed_database_bank_preserves_required_sql_error_analysis():
    from cspapergen.generator import build_topic_question_bank
    from cspapergen.syllabus import load_syllabus
    from cspapergen.validation import validate_blueprint

    syllabus = load_syllabus(Path("Resources/computer-science/aqa/generator/data/syllabus_seed.json"))
    bank = build_topic_question_bank(syllabus, topic_id="4.10", seed=26092851)
    validate_blueprint(bank, syllabus)
    # Deletion construction alone must not substitute for the error-analysis task.
    bank.questions[0].parts[3].prompt = "Write a DELETE statement for BOOKING."
    with pytest.raises(ValueError, match=r"missing required SQL work.*ERROR"):
        validate_blueprint(bank, syllabus)


@pytest.mark.parametrize("mutation", ["context", "mode", "tariff", "focus"])
def test_bank_support_rejects_changed_work_not_just_matching_topic_words(mutation):
    items = bank_items("4.12")
    item = items[0]
    if mutation == "context":
        item["context"] = []
    elif mutation == "mode":
        item["prompt"] = "Explain the purpose of the trace table."
    elif mutation == "tariff":
        item["marks"] = 12
    else:
        item["prompt"] = "Complete a trace table for this relational database query."
    report = module().audit_topic_bank(items, "4.12", module().reviewed_topic_records("4.12"))
    assert not report["passed"]
    assert item["id"] in report["coverage"]["unmatched_item_ids"]


@pytest.mark.parametrize(
    "topic,count,marks,ao",
    [
        ("4.2", 21, 48, {"AO1": 38, "AO2": 10, "AO3": 0}),
        ("4.10", 18, 47, {"AO1": 9, "AO2": 24, "AO3": 14}),
        ("4.12", 16, 28, {"AO1": 6, "AO2": 22, "AO3": 0}),
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
    data = [next(i for i in bank_items("4.2") if "stack capacity" in i["prompt"])]
    report = module().audit_topic_bank(
        data, "4.2", module().reviewed_topic_records("4.2")
    )
    assert report["evidence_state"] == "insufficient"
    assert report["passed"] is False
    assert report["coverage"]["matched_items"] == 1
    assert len(report["cluster_sensitivity"]["leave_one_year_out"]) == 6
    assert report["whole_topic_qualified"] is False
    sensitivity = report["cluster_sensitivity"]
    assert sensitivity["admitted_mixed_ids"] == ["75171-2024-06.3"]
    assert "complete-code:code" not in sensitivity["pooled_parts"]


def test_real_bank_explanation_drawing_and_sequence_are_not_false_table_matches():
    structures = bank_items("4.2")
    database = bank_items("4.10")
    explanation = module().task_features(structures[1])
    assert explanation == {"topic_id": "4.2", "operation": "explain", "mode": "prose"}
    drawing = module().task_features(next(i for i in database if i["prompt"].startswith("Draw")))
    assert drawing == {"topic_id": "4.10", "operation": "represent", "mode": "diagram"}
    sequence = module().task_features(next(i for i in structures if "in-order traversal" in i["prompt"]))
    assert sequence["mode"] == "sequence"
    for task in (explanation, drawing, sequence):
        assert all(r["mode"] != "table" for r in module().matching_records(module().reviewed_topic_records(task["topic_id"]), task))


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
