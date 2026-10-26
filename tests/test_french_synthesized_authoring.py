"""Experimental authoring replay binds the entire exercise, not just answers."""

from copy import deepcopy

import pytest

from Backend.Core.france.synthesized_authoring import author, replay


@pytest.mark.parametrize("family", ["recursive", "postfix"])
@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_full_question_verification_not_metadata_alone(family, total):
    from Backend.Core.france.synthesized_authoring import verify_question

    raw, _ = author(family, 713, references=[], total=total)
    for question in raw["questions"]:
        result = verify_question(question, family, 713, total=total)
        assert result["state"] == "passed"
        assert result["scope"] == "canonical_question_replay"
        for field in (
            "id",
            "prompt",
            "answer",
            "marking",
            "points",
            "material_ids",
            "verification",
            "curriculum_codes",
            "estimated_minutes",
        ):
            changed = deepcopy(question)
            changed[field] = "tampered"
            assert (
                verify_question(changed, family, 713, total=total)["state"] == "failed"
            )


@pytest.mark.parametrize("question", [None, [], {}, {"id": "missing"}])
def test_malformed_question_never_passes(question):
    from Backend.Core.france.synthesized_authoring import verify_question

    assert not verify_question(question, "postfix", 713)["passed"]


def test_metadata_alone_cannot_qualify_new_questions():
    from Backend.Core.france.verification import verify_contract

    for family in ("recursive", "postfix"):
        raw, _ = author(family, 713, references=[])
        for question in raw["questions"]:
            assert verify_contract(question["verification"])["state"] == "unresolved"


def test_question_verification_rejects_wrong_identity_and_extra_fields():
    from Backend.Core.france.synthesized_authoring import verify_question

    raw, _ = author("postfix", 713, references=[])
    question = raw["questions"][0]
    for family, seed, total in (
        ("recursive", 713, "6"),
        ("postfix", 714, "6"),
        ("postfix", True, "6"),
        ("postfix", 713, "5.5"),
        ("unknown", 713, "6"),
    ):
        assert not verify_question(question, family, seed, total=total)["passed"]
    assert not verify_question({**question, "approved": True}, "postfix", 713)["passed"]


@pytest.mark.parametrize("family", ["recursive", "postfix"])
@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_blueprint_and_replay_bind_allocated_marks(family, total):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _check_exercise_plan
    from Backend.Core.france.synthesized_authoring import blueprint

    task = blueprint(family, 713, total=total)
    raw, evidence = author(family, 713, references=[], total=total, task=task)
    _check_exercise_plan(NSIExercise.model_validate(raw), task, "1")
    assert replay(family, 713, [], raw, evidence, total=total, task=task) == raw
    changed = deepcopy(task)
    changed["question_blueprint"][0]["points"] = "9"
    with pytest.raises(ValueError):
        author(family, 713, references=[], total=total, task=changed)
    wrong = "5.5" if total == "6" else "6"
    with pytest.raises(ValueError):
        replay(family, 713, [], raw, evidence, total=wrong)


@pytest.mark.parametrize("family", ["recursive", "postfix"])
def test_replay_preserves_complete_candidate_and_provenance(family):
    raw, evidence = author(family, 713, references=[{"id": "fr-reference"}])
    assert evidence["origin"] == "application_owned"
    assert evidence["model_used"] is False
    assert replay(family, 713, [{"id": "fr-reference"}], raw, evidence) == raw
    for field in ("prompt", "answer", "marking", "verification", "points"):
        changed = deepcopy(raw)
        changed["questions"][0][field] = "forged"
        with pytest.raises(ValueError):
            replay(family, 713, [{"id": "fr-reference"}], changed, evidence)


@pytest.mark.parametrize("family", ["recursive", "postfix"])
def test_rehashed_tampering_is_not_replay(family):
    from Backend.Core.france.database_depth_authoring import _hash

    raw, evidence = author(family, 713, references=[])
    raw["questions"][0]["answer"] = "Untrusted answer"
    evidence["candidate_sha256"] = _hash(raw)
    with pytest.raises(ValueError):
        replay(family, 713, [], raw, evidence)


def test_extra_evidence_fields_and_relabelled_origin_are_rejected():
    raw, evidence = author("postfix", 713, references=[])
    for changed in (
        {**evidence, "origin": "model_authored"},
        {**evidence, "approved": True},
        {**evidence, "model_used": True},
    ):
        with pytest.raises(ValueError):
            replay("postfix", 713, [], raw, changed)


def test_replay_does_not_mutate_caller_data():
    references = [{"id": "fr", "metadata": {"split": "reference"}}]
    raw, evidence = author("recursive", 713, references=references)
    before = deepcopy((references, raw, evidence))
    restored = replay("recursive", 713, references, raw, evidence)
    assert (references, raw, evidence) == before
    restored["questions"][0]["answer"] = "changed outside replay"
    assert raw == before[1]


def test_seed_family_reference_and_source_are_bound(monkeypatch):
    import Backend.Core.france.synthesized_authoring as module

    raw, evidence = author("postfix", 713, references=[])
    for family, seed, references in [
        ("recursive", 713, []),
        ("postfix", 714, []),
        ("postfix", 713, [{"id": "other"}]),
    ]:
        with pytest.raises(ValueError):
            replay(family, seed, references, raw, evidence)
    monkeypatch.setattr(module, "catalogue_digest", lambda: "changed-source")
    with pytest.raises(ValueError):
        replay("postfix", 713, [], raw, evidence)


@pytest.mark.parametrize(
    "family,seed,references",
    [
        ("unknown", 713, []),
        ("postfix", True, []),
        ("postfix", 713, None),
        ("postfix", 713, ["invalid"]),
    ],
)
def test_invalid_authoring_inputs_fail_closed(family, seed, references):
    with pytest.raises(ValueError):
        author(family, seed, references=references)


@pytest.mark.parametrize("family", ["recursive", "postfix"])
def test_synthesized_e1_preserves_actual_pipeline_allocations(family):
    from decimal import Decimal

    from Backend.Core.france.database_case_prose import render_case as database
    from Backend.Core.france.nsi import LANGUAGE_RUBRIC_2027, NSIExercise
    from Backend.Core.france.pipeline import _tasks_for_seed_v32
    from Backend.Core.france.system_case_prose import render_case as system

    for seed in range(270100, 270130):
        tasks = _tasks_for_seed_v32(seed)
        first, _ = author(
            family, seed, references=[], total=tasks[0]["technical_points"]
        )
        exercises = [NSIExercise.model_validate(first)] + [
            NSIExercise.model_validate(renderer(seed, total=task["technical_points"]))
            for renderer, task in zip((database, system), tasks[1:], strict=True)
        ]
        assert [e.id for e in exercises] == ["1", "2", "3"]
        assert sum(e.credit for e in exercises) == Decimal("18")
        assert sum(e.minutes for e in exercises) == 210
        assert LANGUAGE_RUBRIC_2027["points"] == "2"
