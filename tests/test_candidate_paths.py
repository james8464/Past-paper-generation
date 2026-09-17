import importlib
from copy import deepcopy

import pytest


def paths_module():
    return importlib.import_module("Backend.Core.candidate_paths")


def topology():
    return {
        "schema_version": 1,
        "policy_id": "test-choice-v1",
        "total_marks": 80,
        "duration_minutes": 120,
        "sections": [
            {
                "id": "context",
                "answer_options": 1,
                "candidate_marks": 40,
                "options": [
                    {"id": "c1", "item_ids": ["a"]},
                    {"id": "c2", "item_ids": ["b"]},
                ],
            },
            {
                "id": "essay",
                "answer_options": 1,
                "candidate_marks": 40,
                "options": [
                    {"id": "e1", "item_ids": ["c", "d"]},
                    {"id": "e2", "item_ids": ["e", "f"]},
                    {"id": "e3", "item_ids": ["g", "h"]},
                ],
            },
        ],
    }


def items():
    return [
        {"id": key, "marks": marks}
        for key, marks in zip("abcdefgh", [40, 40, 15, 25, 15, 25, 15, 25], strict=True)
    ]


def test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs():
    paths = paths_module().enumerate_candidate_paths(topology(), items())
    assert len(paths) == 6
    assert {path.total_marks for path in paths} == {80}
    assert {tuple(path.item_ids) for path in paths} == {
        ("a", "c", "d"),
        ("a", "e", "f"),
        ("a", "g", "h"),
        ("b", "c", "d"),
        ("b", "e", "f"),
        ("b", "g", "h"),
    }


@pytest.mark.parametrize(
    "mutation", ["count", "duplicate", "missing", "section", "marks", "unknown"]
)
def test_malformed_topology_is_not_all_items(mutation):
    raw = topology()
    if mutation == "count":
        raw["sections"][0]["answer_options"] = 3
    elif mutation == "duplicate":
        raw["sections"][1]["options"][0]["item_ids"][0] = "a"
    elif mutation == "missing":
        raw["sections"][1]["options"].pop()
    elif mutation == "section":
        raw["sections"][1]["id"] = "context"
    elif mutation == "marks":
        raw["sections"][1]["candidate_marks"] = 50
    else:
        raw.pop("sections")
    with pytest.raises(ValueError):
        paths_module().enumerate_candidate_paths(raw, items())


def test_topology_identity_changes_on_membership_or_selection():
    module = paths_module()
    original = module.CandidateTopology.model_validate(topology())
    altered = deepcopy(topology())
    altered["sections"][1]["options"][0]["item_ids"].reverse()
    assert (
        original.fingerprint
        != module.CandidateTopology.model_validate(altered).fingerprint
    )


def test_unknown_shared_selection_count_is_rejected_not_parsed_from_instructions():
    raw = {
        "total_marks": 40,
        "duration_minutes": 60,
        "sections": [
            {
                "id": "A",
                "instructions": "Answer one option",
                "options": [{"id": "a", "questions": [{"prompt": "x", "marks": 40}]}],
            }
        ],
    }
    with pytest.raises(ValueError, match="selection"):
        paths_module().topology_from_blueprint(
            raw,
            [{"id": "a@sections.0.options.0.questions.0", "marks": 40}],
            "aqa/economics",
        )


@pytest.mark.parametrize(
    "package,family,paper_id,count,marks,printed",
    [
        ("aqaecongen", "aqa/economics", "paper_1", 6, 80, 200),
        ("aqaecongen", "aqa/economics", "paper_2", 6, 80, 200),
        ("ocregen", "ocr/economics", "paper_1", 4, 80, 130),
        ("ocregen", "ocr/economics", "paper_2", 4, 80, 130),
        ("aqabizgen", "aqa/business", "paper_1", 4, 100, 150),
    ],
)
def test_real_shared_rules_survive_generation(
    package, family, paper_id, count, marks, printed
):
    from pathlib import Path

    from Backend.Core.assessment_package import _extract_items

    generator = importlib.import_module(f"{package}.generator")
    syllabus = importlib.import_module(f"{package}.syllabus").load_syllabus(
        Path(generator.__file__).parent.parent / "data/syllabus.json"
    )
    rule = importlib.import_module(f"{package}.configs").RULES[paper_id]
    paper = generator.build_paper(rule, syllabus, seed=26090831)
    raw = paper.model_dump(mode="json")
    exported = _extract_items(raw, subject=family, paper_number=paper_id[-1])
    topology = paths_module().topology_from_blueprint(raw, exported, family)
    paths = paths_module().enumerate_candidate_paths(topology, exported)
    assert len(paths) == count
    assert {path.total_marks for path in paths} == {marks}
    assert sum(item["marks"] for item in exported) == printed
    from Backend.Core.reference_demand import audit_form_demand, profile_for

    review = audit_form_demand(
        exported, profile_for(family, paper_id[-1]), require_item_evidence=True
    )
    assert review["items_checked"] == len(exported) > len(paths[0].item_ids)
    assert review["item_review_evidence"]["reviewed_items"] == 0
    assert "item_review_coverage" in review["failed_checks"]


@pytest.mark.parametrize(
    "paper_id,count,printed",
    [("paper_1", 2, 125), ("paper_2", 2, 125), ("paper_3", 4, 150)],
)
def test_edexcel_leaf_only_marks_and_choice_groups(paper_id, count, printed):
    from pathlib import Path

    import pastpapergen.generator as generator
    from pastpapergen.paper_configs import load_builtin_paper_config
    from pastpapergen.syllabus import load_syllabus

    from Backend.Core.assessment_package import _extract_items

    syllabus = load_syllabus(
        Path(generator.__file__).parent.parent / "data/syllabus_seed.json"
    )
    paper = generator.build_paper_blueprint(
        load_builtin_paper_config(paper_id), syllabus, seed=26090831
    )
    raw = paper.model_dump(mode="json")
    exported = _extract_items(raw, subject="economics", paper_number=paper_id[-1])
    topology = paths_module().topology_from_blueprint(
        raw, exported, "pearson-edexcel/economics-a-2015"
    )
    paths = paths_module().enumerate_candidate_paths(topology, exported)
    assert len(paths) == count
    assert {path.total_marks for path in paths} == {100}
    assert sum(item["marks"] for item in exported) == printed


def test_good_printed_average_cannot_rescue_a_failed_correlated_path():
    from Backend.Core.reference_demand import ReferenceDemandProfile, audit_form_demand
    from tests.test_reference_demand import profile_payload

    module = paths_module()
    raw = {
        "policy_id": "test",
        "total_marks": 4,
        "duration_minutes": 6,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 4,
                "options": [
                    {"id": "x", "item_ids": ["x"]},
                    {"id": "y", "item_ids": ["y"]},
                ],
            }
        ],
    }
    data = [
        {
            "id": key,
            "marks": 4,
            "command_word": command,
            "expected_minutes": 6,
            "assessment_objectives": {"AO1": 4},
            "intended_demand": band,
        }
        for key, command, band in [
            ("x", "Explain", "standard"),
            ("y", "Evaluate", "high"),
        ]
    ]
    payload = profile_payload()
    payload.update(
        mark_band_distribution={"short": 1},
        command_word_distribution={"explain": 0.5, "evaluate": 0.5},
        demand_distribution={"standard": 0.5, "high": 0.5},
        mark_weighted_demand_distribution={"standard": 0.5, "high": 0.5},
        response_mode_distribution={
            "structured-reasoning": 0.5,
            "extended-evaluation": 0.5,
        },
        cognitive_operation_distribution={"explain": 0.5, "judge": 0.5},
    )
    profile = ReferenceDemandProfile.model_validate(payload)
    assert audit_form_demand(data, profile)["passed"] is True
    result = module.audit_candidate_paths(data, raw, profile)
    assert result["passed"] is False
    assert result["path_count"] == 2
    assert len(result["failed_paths"]) == 2
    assert result["printed_marks"] == 8
    assert result["candidate_mark_range"] == [4, 4]


def test_unknown_allocated_time_and_objectives_are_not_passed_defaults():
    from Backend.Core.reference_demand import ReferenceDemandProfile
    from tests.test_reference_demand import profile_payload

    data = items()
    report = paths_module().audit_candidate_paths(
        data, topology(), ReferenceDemandProfile.model_validate(profile_payload())
    )
    assert report["passed"] is False
    assert all(
        "allocated_timing_unknown" in row["failed_checks"] for row in report["paths"]
    )
    assert all(
        "objective_allocation_unknown" in row["failed_checks"]
        for row in report["paths"]
    )


def test_selection_topology_is_part_of_item_review_identity():
    from Backend.Core.candidate_identity import (
        candidate_content_identity,
        shared_difficulty_candidate_projection,
    )
    from Backend.Core.exam_blueprints import (
        GeneratedOption,
        GeneratedQuestion,
        GeneratedSection,
    )

    q = GeneratedQuestion(
        rule_id="x",
        number="1",
        marks=4,
        kind="short",
        command_word="Explain",
        topic_id="x",
        prompt="Explain",
        mark_scheme=["Credit"],
    )
    s = GeneratedSection(
        id="A",
        title="A",
        instructions="",
        answer_options=1,
        candidate_marks=4,
        options=[GeneratedOption(id="a", title="a", questions=[q])],
    )
    before = candidate_content_identity(
        shared_difficulty_candidate_projection(question=q, option=s.options[0])
    )
    changed = GeneratedSection(
        id="B",
        title="A",
        instructions="",
        answer_options=1,
        candidate_marks=4,
        options=[GeneratedOption(id="a", title="a", questions=[q])],
    )
    after = candidate_content_identity(
        shared_difficulty_candidate_projection(question=q, option=changed.options[0])
    )
    assert before != after


def test_explicit_selected_operation_is_not_relabelled_retrieval_in_audit():
    from Backend.Core.reference_demand import audit_form_demand, profile_for

    report = audit_form_demand(
        [
            {
                "id": "x",
                "marks": 1,
                "command_word": "Select",
                "kind": "mcq",
                "task_operation": "transform",
                "source_dependency": "stem",
            }
        ],
        profile_for("aqa/economics", "3"),
    )
    assert report["observed"]["cognitive_operation_distribution"] == {"transform": 1.0}


def test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds():
    from Backend.Core.reference_demand import (
        ReferenceDemandDocument,
        profile_for,
    )
    from tools.source_candidate_paths import form_from_items

    profile = profile_for("aqa/economics", "3").model_copy(deep=True)
    allocations = [
        {"AO1": 10},
        {"AO1": 5, "AO2": 5},
        {"AO2": 10},
        {"AO2": 7, "AO3": 3},
        {"AO3": 10},
        {"AO3": 6, "AO4": 4},
        {"AO4": 10},
        {"AO1": 7, "AO2": 2, "AO4": 1},
    ]
    # P3 target 22/24/19/15, with each ten-mark leaf reconciled.
    data = [
        {
            "id": str(n),
            "marks": 10,
            "expected_minutes": 15,
            "command_word": "Explain",
            "task_operation": "explain",
            "assessment_objectives": ao,
            "intended_demand": "standard",
        }
        for n, ao in enumerate(allocations)
    ]
    profile.reference_forms = []
    for year, count, marks, mode in [
        (2024, 20, 4, "structured-reasoning"),
        (2025, 8, 10, "recall"),
    ]:
        rows = [
            {
                "id": str(n),
                "marks": marks,
                "command_word": "explain",
                "cognitive_operation": "explain",
                "response_mode": mode,
                "demand_band": "unknown",
                "demand_basis": "unknown-no-learner-measurement",
                "historical_engineering_demand_proxy": "standard",
                "assessment_objectives": None,
                "objective_basis": "unknown",
                "learner_demand": None,
                "reasoning_steps": None,
                "observed_minutes": None,
            }
            for n in range(count)
        ]
        profile.reference_forms.append(
            form_from_items(
                rows,
                family="aqa/economics",
                paper="3",
                year=year,
                source_id=str(year),
                source_sha256="a" * 64,
            )
        )
    topology = {
        "policy_id": "test",
        "total_marks": 80,
        "duration_minutes": 120,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 80,
                "options": [{"id": "a", "item_ids": [i["id"] for i in data]}],
            }
        ],
    }
    evidence_document = ReferenceDemandDocument.model_validate(
        {
            "schema_version": 3,
            "purpose": "Synthetic source vectors exercise correlated path bounds.",
            "derived_aggregate_only": True,
            "retains_source_text": False,
            "profiles": [profile.model_dump(mode="json")],
        }
    )
    report = paths_module().audit_candidate_paths(
        data,
        topology,
        evidence_document.profiles[0],
        evidence_context=evidence_document,
    )
    assert report["passed"] is False
    assert report["evidence_validation_passed"] is False
    assert report["evidence_state"] == "insufficient"


def test_profile_policy_source_and_topology_changes_invalidate_target_identity():
    from Backend.Core.reference_demand import build_item_demand_target, profile_for

    profile = profile_for("aqa/economics", "1").model_copy(deep=True)
    item = {"id": "x", "marks": 4, "command_word": "Explain"}
    first = build_item_demand_target(item, profile).reference_profile_fingerprint
    profile.reference_forms[0]["source_sha256"] = "f" * 64
    assert (
        build_item_demand_target(item, profile).reference_profile_fingerprint != first
    )
    profile = profile_for("aqa/economics", "1").model_copy(deep=True)
    profile.reference_forms[0]["topology"]["policy_id"] = "changed"
    assert (
        build_item_demand_target(item, profile).reference_profile_fingerprint != first
    )


def test_bank_manifest_keeps_insufficiency_separate_from_printed_review():
    from pathlib import Path

    from cspapergen.generator import build_topic_question_bank
    from cspapergen.syllabus import load_syllabus

    from Backend.Core.assessment_package import _extract_items, _reference_demand_audit

    syllabus = load_syllabus(
        Path("Resources/computer-science/aqa/generator/data/syllabus_seed.json")
    )
    raw = build_topic_question_bank(syllabus, topic_id="4.2", seed=26090831).model_dump(
        mode="json"
    )
    data = _extract_items(raw, subject="computer_science", paper_number="bank-4.2")
    report = _reference_demand_audit(
        subject="computer_science",
        paper_number="bank-4.2",
        items=data,
        preview=False,
        blueprint=raw,
    )
    assert report["evidence_state"] == "insufficient"
    assert report["passed"] is False
    assert report["path_evidence"]["passed"] is False
    assert report["build_eligible"] is False
    assert "item_review_coverage" in report["failed_checks"]
    assert report["items_checked"] == len(data)
    assert report["topic_evidence"]["strata"]["core"] == {"parts": 19, "marks": 42}


def test_one_choice_cannot_hide_an_objective_budget_failure():
    from Backend.Core.reference_demand import profile_for

    data = [
        {
            "id": key,
            "marks": 80,
            "command_word": "Evaluate",
            "expected_minutes": 120,
            "assessment_objectives": ao,
            "intended_demand": "high",
        }
        for key, ao in [
            ("a", {"AO1": 15, "AO2": 22, "AO3": 25, "AO4": 18}),
            ("b", {"AO1": 40, "AO2": 10, "AO3": 15, "AO4": 15}),
        ]
    ]
    top = {
        "policy_id": "test",
        "total_marks": 80,
        "duration_minutes": 120,
        "sections": [
            {
                "id": "A",
                "answer_options": 1,
                "candidate_marks": 80,
                "options": [
                    {"id": "a", "item_ids": ["a"]},
                    {"id": "b", "item_ids": ["b"]},
                ],
            }
        ],
    }
    result = paths_module().audit_candidate_paths(
        data, top, profile_for("aqa/economics", "1")
    )
    assert "objective_design_envelope" not in result["paths"][0]["failed_checks"]
    assert "objective_design_envelope" in result["paths"][1]["failed_checks"]
