from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
)
from Backend.Core.generator_registry import REGISTRY_PATH


def module():
    return importlib.import_module("Backend.Core.reference_demand")


def tool_module():
    return importlib.import_module("tools.reference_demand_profiles")


def profile_payload() -> dict[str, object]:
    return {
        "family_id": "aqa/economics",
        "paper_id": "1",
        "assessment_kind": "full-paper",
        "comparison_basis": "Aggregate features from current official question papers.",
        "source_document_count": 4,
        "source_fingerprint": "a" * 64,
        "mark_band_distribution": {
            "short": 0.5,
            "medium": 0.25,
            "extended": 0.25,
        },
        "command_word_distribution": {
            "explain": 0.5,
            "analyse": 0.25,
            "evaluate": 0.25,
        },
        "demand_distribution": {
            "low": 0.25,
            "standard": 0.5,
            "high": 0.25,
        },
        "mark_weighted_demand_distribution": {
            "low": 0.1,
            "standard": 0.4,
            "high": 0.5,
        },
        "response_mode_distribution": {
            "recall": 0.25,
            "structured-reasoning": 0.5,
            "extended-evaluation": 0.25,
        },
        "cognitive_operation_distribution": {
            "retrieve": 0.25,
            "explain": 0.5,
            "judge": 0.25,
        },
        "extraction_coverage": 0.95,
        "metric_tolerances": {
            "mark_band_distribution": 0.5,
            "command_family_distribution": 0.5,
            "mark_weighted_demand_distribution": 0.5,
            "response_mode_distribution": 0.7,
            "cognitive_operation_distribution": 0.7,
        },
    }


def test_profile_rejects_missing_aggregate_evidence() -> None:
    reference_demand = module()
    payload = profile_payload()
    payload["source_document_count"] = 0

    with pytest.raises(ValueError):
        reference_demand.ReferenceDemandProfile.model_validate(payload)


def test_item_target_turns_high_demand_into_observable_requirements() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    target = reference_demand.build_item_demand_target(
        {
            "id": "q8",
            "marks": 15,
            "kind": "essay",
            "command_word": "Evaluate",
            "intended_demand": "high",
            "assessment_objectives": {"AO1": 3, "AO2": 3, "AO3": 4, "AO4": 5},
            "context": ["A case study supplies financial and operational evidence."],
        },
        profile,
    )

    assert target.demand_band == "high"
    assert target.minimum_reasoning_steps == 4
    assert target.maximum_reasoning_steps == 7
    assert "judge" in target.required_cognitive_operations
    assert "integrate" in target.required_cognitive_operations
    assert target.requires_shortcut_resistance is True
    assert target.maximum_scaffolding == "minimal"
    assert target.requires_context is True
    assert target.requires_analysis_chain is True
    assert target.requires_judgement is True
    assert target.requires_multiple_concepts is True
    assert target.reference_profile_fingerprint == "a" * 64


def test_item_target_distinguishes_multistage_calculation_from_recall() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    calculation = reference_demand.build_item_demand_target(
        {
            "id": "q2",
            "marks": 6,
            "kind": "calculation",
            "command_word": "Calculate",
            "assessment_objectives": {"AO2": 6},
            "context": ["A table supplies values."],
        },
        profile,
    )
    recall = reference_demand.build_item_demand_target(
        {
            "id": "q1",
            "marks": 2,
            "kind": "short_answer",
            "command_word": "State",
            "assessment_objectives": {"AO1": 2},
            "context": [],
        },
        profile,
    )

    assert calculation.response_mode == "multi-stage-calculation"
    assert calculation.minimum_reasoning_steps == 3
    assert calculation.maximum_reasoning_steps >= calculation.minimum_reasoning_steps
    assert "transform" in calculation.required_cognitive_operations
    assert calculation.requires_data_transformation is True
    assert recall.response_mode == "recall"
    assert recall.minimum_reasoning_steps == 1
    assert recall.maximum_reasoning_steps == 2
    assert recall.required_cognitive_operations == ["retrieve"]


@pytest.mark.parametrize(
    ("marks", "expected_maximum"),
    [(2, 3), (5, 5), (7, 7), (8, 8), (14, 12)],
)
def test_calculation_reasoning_ceiling_scales_with_tariff(
    marks: int,
    expected_maximum: int,
) -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    target = reference_demand.build_item_demand_target(
        {
            "id": f"q-{marks}",
            "marks": marks,
            "kind": "calculation",
            "command_word": "Prepare",
            "assessment_objectives": {"AO2": marks},
            "intended_demand": (
                "low" if marks <= 3 else "high" if marks >= 12 else "standard"
            ),
            "context": ["A complete accounting case supplies the required figures."],
        },
        profile,
    )

    assert target.maximum_reasoning_steps == expected_maximum


def test_reference_extraction_pairs_local_command_and_mark_without_retaining_prose() -> (
    None
):
    tool = tool_module()
    text = """
    01 Explain two consequences for the business.
    [4 marks]
    02 Evaluate whether the investment should proceed.
    [12 marks]
    """

    items = tool.extract_reference_items(text, board="aqa")

    assert items == [
        {
            "marks": 4,
            "command_word": "explain",
            "demand_band": "standard",
            "response_mode": "structured-reasoning",
            "cognitive_operation": "explain",
        },
        {
            "marks": 12,
            "command_word": "evaluate",
            "demand_band": "high",
            "response_mode": "extended-evaluation",
            "cognitive_operation": "judge",
        },
    ]
    assert "business" not in json.dumps(items)
    assert "investment" not in json.dumps(items)


def test_form_audit_weights_demand_by_marks_and_reports_review_coverage() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())
    items = [
        {
            "id": "q1",
            "marks": 1,
            "kind": "multiple_choice",
            "command_word": "Select",
            "intended_demand": "low",
            "difficulty_evidence": {
                "approved": True,
                "reasoning_range_fit": True,
                "context_fit": True,
                "shortcut_resistant": True,
            },
        },
        {
            "id": "q2",
            "marks": 9,
            "kind": "essay",
            "command_word": "Evaluate",
            "intended_demand": "high",
            "difficulty_evidence": {
                "approved": True,
                "reasoning_range_fit": True,
                "context_fit": True,
                "shortcut_resistant": True,
            },
        },
    ]

    report = reference_demand.audit_form_demand(items, profile)

    assert report["schema_version"] == 2
    assert report["observed"]["mark_weighted_demand_distribution"] == {
        "high": 0.9,
        "low": 0.1,
    }
    assert report["item_review_evidence"]["coverage"] == 1.0
    assert report["extraction_coverage"] == 0.95


def test_form_audit_rejects_distribution_drift() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())
    items = [
        {
            "id": f"q{index}",
            "marks": 1,
            "kind": "multiple_choice",
            "command_word": "Select",
            "assessment_objectives": {"AO1": 1},
            "context": [],
        }
        for index in range(12)
    ]

    report = reference_demand.audit_form_demand(items, profile)

    assert report["passed"] is False
    assert report["profile_fingerprint"] == "a" * 64
    assert "command_family_distribution" in report["failed_checks"]
    assert "command_word_distribution" in report["distances"]
    assert "command_word_distribution" not in report["gated_distances"]


def test_committed_profiles_cover_every_advertised_assessment_without_source_text() -> (
    None
):
    reference_demand = module()
    document = reference_demand.load_reference_demand_document()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    expected = {
        (family["id"], str(paper["id"]))
        for family in registry["families"]
        if family["advertised"]
        for paper in family["papers"]
    }
    actual = {(profile.family_id, profile.paper_id) for profile in document.profiles}

    assert expected <= actual
    assert document.derived_aggregate_only is True
    assert document.retains_source_text is False
    rendered = Path(reference_demand.PROFILES_PATH).read_text(encoding="utf-8")
    assert "Reference Corpus" not in rendered
    assert "question-papers" not in rendered


def test_committed_profiles_include_unadvertised_aqa_mathematics_evidence() -> None:
    reference_demand = module()
    document = reference_demand.load_reference_demand_document()
    profiles = {
        profile.paper_id: profile
        for profile in document.profiles
        if profile.family_id == "aqa/mathematics"
    }

    assert set(profiles) == {"1", "2", "3"}
    assert all(profile.source_document_count >= 3 for profile in profiles.values())
    assert all(profile.extraction_coverage >= 0.6 for profile in profiles.values())
    assert all(
        "unspecified" not in profile.command_word_distribution
        for profile in profiles.values()
    )


def test_reference_extraction_keeps_demand_features_but_discards_question_prose() -> (
    None
):
    tool = tool_module()
    text = """
    01 Explain two consequences for the business.
    [4 marks]
    02 Evaluate whether the investment should proceed.
    [12 marks]
    """

    features = tool.extract_reference_features(text, board="aqa")

    assert features == {
        "marks": [4, 12],
        "command_words": ["explain", "evaluate"],
    }
    assert "business" not in json.dumps(features)
    assert "investment" not in json.dumps(features)


def test_reference_extraction_recognises_board_style_command_phrases() -> None:
    tool = tool_module()
    text = """
    01 Which one of the following is correct?
    [1 mark]
    02 Which of the following combinations is correct?
    [1 mark]
    03 To what extent is the proposed strategy appropriate?
    [20 marks]
    """

    features = tool.extract_reference_features(text, board="aqa")

    assert features == {
        "marks": [1, 1, 20],
        "command_words": ["select", "select", "evaluate"],
    }


def test_reference_extraction_recognises_mathematical_command_words() -> None:
    tool = tool_module()
    text = """
    01 Show that the result has the stated form.
    [3 marks]
    02 Find the exact value of the constant.
    [4 marks]
    03 Solve the equation for the stated interval.
    [5 marks]
    04 Determine the range of values.
    [6 marks]
    05 Prove that the assertion is true.
    [7 marks]
    """

    features = tool.extract_reference_features(text, board="aqa")

    assert features == {
        "marks": [3, 4, 5, 6, 7],
        "command_words": ["show", "find", "solve", "determine", "prove"],
    }


def test_mathematical_commands_require_transformative_reasoning() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    target = reference_demand.build_item_demand_target(
        {
            "id": "q6",
            "marks": 7,
            "kind": "mathematical_argument",
            "command_word": "Prove",
            "intended_demand": "high",
            "assessment_objectives": {"AO2": 3, "AO3": 4},
        },
        profile,
    )

    assert target.response_mode == "mathematical-argument"
    assert "transform" in target.required_cognitive_operations
    assert "analyse" in target.required_cognitive_operations
    assert target.requires_shortcut_resistance is True


def test_evaluative_commands_do_not_require_redundant_explain_operation() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    target = reference_demand.build_item_demand_target(
        {
            "id": "q14.2",
            "marks": 6,
            "kind": "analysis",
            "command_word": "Assess",
            "intended_demand": "high",
            "assessment_objectives": {"AO2": 2, "AO3": 2, "AO4": 2},
            "context": ["A complete financial scenario."],
        },
        profile,
    )

    assert target.required_cognitive_operations == [
        "analyse",
        "contextualise",
        "integrate",
        "judge",
    ]


def test_reference_extraction_models_the_published_ocr_paper_three_mcq_block() -> None:
    tool = tool_module()
    text = "1 What is scarcity?\n[1]\n31 Explain one effect.\n[4]"

    features = tool.extract_reference_features(
        text,
        board="ocr",
        family_id="ocr/economics",
        paper_id="3",
    )

    assert features["command_words"] == ["select"] * 30 + ["explain"]


def test_profile_tool_runs_standalone_outside_the_repository(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "tools" / "reference_demand_profiles.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
    )

    assert result.returncode == 0, result.stderr
    assert "aggregate reference-demand profiles" in result.stdout


def test_assessment_package_records_the_exact_reference_demand_audit(
    tmp_path: Path,
) -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=4,
        kind="data_response",
        command_word="Explain",
        topic_id="markets",
        prompt="Explain one effect of the change shown in the extract.",
        mark_scheme=["One developed effect using the extract."],
        assessment_objectives={"AO1": 1, "AO2": 1, "AO3": 2},
        source_references=["Extract A"],
        authoring_context={
            "difficulty_evidence": {
                "schema_version": 2,
                "approved": True,
                "reasoning_range_fit": True,
                "context_fit": True,
                "shortcut_resistant": True,
            }
        },
    )
    paper = GeneratedPaper(
        paper_id="paper_1",
        paper_code="7136/1",
        title="Paper 1",
        duration_minutes=120,
        total_marks=4,
        seed=1,
        sections=[
            GeneratedSection(
                id="A",
                title="Section A",
                instructions="Answer the question.",
                options=[
                    GeneratedOption(
                        id="A1",
                        title="Extract A",
                        stimulus=["A market changed after a policy intervention."],
                        questions=[question],
                    )
                ],
            )
        ],
    )
    path = tmp_path / "assessment.json"

    write_assessment_package(
        paper,
        path,
        subject="economics_aqa",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )

    document = json.loads(path.read_text(encoding="utf-8"))
    audit = document["reference_demand"]
    assert audit["items_checked"] == 1
    assert (
        audit["profile_fingerprint"]
        == module().profile_for("aqa/economics", "1").source_fingerprint
    )
    assert audit["empirical_equivalence_claimed"] is False
    assert document["items"][0]["difficulty_evidence"]["approved"] is True
    assert audit["item_review_evidence"]["coverage"] == 1.0


def test_live_form_audit_fails_closed_without_item_review_evidence() -> None:
    reference_demand = module()
    profile = reference_demand.ReferenceDemandProfile.model_validate(profile_payload())

    report = reference_demand.audit_form_demand(
        [
            {
                "id": "q1",
                "marks": 4,
                "command_word": "Explain",
                "kind": "data_response",
                "context": ["An extract"],
            }
        ],
        profile,
        require_item_evidence=True,
    )

    assert report["passed"] is False
    assert "item_review_coverage" in report["failed_checks"]
