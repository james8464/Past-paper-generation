"""Prior numeric acceptance must not masquerade as exact-floating evidence."""

import argparse
import json
from dataclasses import replace

import pytest
from ocrcsgen.cli import ADAPTER

from Backend.Core import model_review
from Backend.Core.ai_assessment import ASSESSMENT_REVIEW_VERSION
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    CheckpointMismatch,
    identity_for_blueprint,
)
from Backend.Core.family_adapter import run_family_adapter
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.numeric_integrity import NUMERIC_INTEGRITY_VERSION
from tests.test_cs_floating_exactness import ROOT


def item():
    return {
        "id": "owned-floating",
        "marks": 1,
        "kind": "calculation",
        "prompt": "Encode the supplied positive number in the declared format.",
        "mark_scheme": ["Floating representation: 01101011."],
        "authoring_context": {
            "cs_input_contract": {
                "kind": "floating-encode",
                "value": "6.5",
                "mantissa_bits": 5,
                "exponent_bits": 3,
            }
        },
    }


def test_prior_v2_canonical_solution_cannot_replay_exact_floating_acceptance():
    source = item()
    current = IndependentSolver().solve(source, [])
    assert reconcile_solution(current, source).passed
    old = current.model_copy(update={"integrity_version": "closed-numeric-v2"})
    assert not reconcile_solution(old, source).passed
    assert NUMERIC_INTEGRITY_VERSION == "closed-numeric-v4-variance-signs"


def test_prior_v2_saved_review_is_refused_for_the_same_candidate():
    source = item()
    evidence = model_review.DifficultyReviewResult(
        approved=True,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        solution_integrity_version="closed-numeric-v2",
        public_task_operation_evidence=model_review._public_task_operation_evidence(
            source
        ),
        candidate_content_identity=model_review.candidate_content_identity(source),
    ).model_dump(mode="json")
    with pytest.raises(ValueError, match="incompatible solution integrity"):
        model_review.validate_saved_difficulty_evidence(
            evidence, {}, item_id="owned-floating", candidate=source
        )


def test_real_ocr_adapter_refuses_v2_checkpoint_without_rewriting_it(tmp_path):
    syllabus_path = ROOT / "Resources/computer-science/ocr/generator/data/syllabus.json"
    syllabus = ADAPTER.load_syllabus(syllabus_path)
    paper = ADAPTER.build(ADAPTER.load_rule("1"), syllabus, 26092845)
    identity = identity_for_blueprint(
        paper,
        provider="ollama",
        model="fixture",
        prompt_version=f"{ADAPTER.prompt_version}:closed-numeric-v2:{ASSESSMENT_REVIEW_VERSION}",
    )
    path = tmp_path / "old-checkpoint.json"
    old = AssessmentCheckpointStore(path, identity)
    old.save_payload("retained", {"owned": True})
    original = path.read_bytes()

    class NeverCalled:
        provider = "ollama"
        model = "fixture"

    def must_not_resume(*args):
        pytest.fail("prior integrity evidence reached resumed authoring")

    with pytest.raises(CheckpointMismatch, match="prompt_version"):
        run_family_adapter(
            replace(ADAPTER, improve=must_not_resume),
            paper="1",
            syllabus_path=syllabus_path,
            output_dir=tmp_path / "output",
            seed=26092845,
            model="fixture",
            ollama_url="http://127.0.0.1:11434",
            dry_run=False,
            client=NeverCalled(),
            checkpoint_path=path,
        )
    assert path.read_bytes() == original
    assert old.load_payload("retained") == {"owned": True}


def test_new_package_manifest_records_the_shared_numeric_integrity_version(
    tmp_path, monkeypatch
):
    from Backend.Core import generation

    monkeypatch.setattr(generation, "_repository_commit", lambda: "a" * 40)
    monkeypatch.setattr(generation, "_generator_version", lambda _: "fixture")
    monkeypatch.setattr(generation, "_sha256", lambda _: "b" * 64)
    assessment = tmp_path / "assessment.json"
    assessment.write_text("{}")
    path = generation._write_package_manifest(
        args=argparse.Namespace(
            subject="computer_science_ocr",
            paper="1",
            seed=26092845,
            dry_run=True,
            provider="ollama",
            model="fixture",
        ),
        capability=generation.generator_capability("computer_science_ocr"),
        staging_dir=tmp_path,
        paths={"assessment_package": assessment},
        pdf_validation={},
        assessment_validation={},
        novelty_validation={},
    )
    assert json.loads(path.read_text())["inputs"]["prompt_version"] == (
        f"Backend.Core.ai_assessment:v15-{NUMERIC_INTEGRITY_VERSION}:{ASSESSMENT_REVIEW_VERSION}"
    )
