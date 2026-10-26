"""V32 app-owned E2 checkpointing must not invent model-generation evidence."""

from copy import deepcopy

import pytest


def fixture(seed=270100):
    from Backend.Core.france.database_case_prose import case_task

    task = case_task(seed)
    identity = {
        "prompt_version": "fr-nsi-written-2027-v32",
        "seed": seed,
        "provider": "fixture",
        "model_digest": "pinned-model",
        "implementation_sha256": "pinned-implementation",
    }
    return task, [], identity


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_application_case_checkpoint_and_replay_are_explicit(tmp_path, seed):
    from Backend.Core.france.database_case_authoring import author_case, replay_case

    task, references, identity = fixture(seed)
    path = tmp_path / "case.json"
    raw, evidence = author_case(task, references, path, run_identity=identity)
    assert evidence["origin"] == "application_owned"
    assert evidence["model_used"] is False
    assert "accepted" not in evidence and "failed_attempts" not in evidence
    assert replay_case(task, references, evidence, run_identity=identity) == raw
    assert author_case(task, references, path, run_identity=identity) == (raw, evidence)
    raw["questions"][0]["answer"] = "corrupted returned object"
    assert author_case(task, references, path, run_identity=identity)[0] != raw


def test_replay_rejects_changed_identity_sources_task_or_evidence(tmp_path):
    from Backend.Core.france.database_case_authoring import author_case, replay_case

    task, references, identity = fixture()
    path = tmp_path / "case.json"
    _, evidence = author_case(task, references, path, run_identity=identity)
    for key in ("seed", "model_digest", "implementation_sha256", "prompt_version"):
        changed = {**identity, key: "changed"}
        with pytest.raises(ValueError):
            replay_case(task, references, evidence, run_identity=changed)
        with pytest.raises(ValueError):
            author_case(task, references, path, run_identity=changed)
    changed = deepcopy(task)
    changed["question_blueprint"][0]["points"] = "1"
    with pytest.raises(ValueError):
        replay_case(changed, references, evidence, run_identity=identity)
    with pytest.raises(ValueError):
        replay_case(task, [{"text": "different"}], evidence, run_identity=identity)
    for key, value in (
        ("model_used", 0),
        ("origin", "model"),
        ("candidate_sha256", "wrong"),
        ("extra", True),
    ):
        with pytest.raises(ValueError):
            replay_case(
                task, references, {**evidence, key: value}, run_identity=identity
            )


def test_replay_checks_current_catalogue_not_only_saved_hashes(tmp_path, monkeypatch):
    from Backend.Core.france import database_case_authoring as authoring

    task, references, identity = fixture()
    _, evidence = authoring.author_case(
        task, references, tmp_path / "case.json", run_identity=identity
    )
    monkeypatch.setattr(authoring, "catalogue_digest", lambda: "changed-source")
    with pytest.raises(ValueError):
        authoring.replay_case(task, references, evidence, run_identity=identity)


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_task_matches_real_pipeline_shape_and_allocation(seed, tmp_path):
    from Backend.Core.france.database_case_authoring import author_case
    from Backend.Core.france.database_case_prose import case_task
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _check_exercise_plan, _tasks_for_seed_v31

    legacy_task = _tasks_for_seed_v31(seed)[1]
    task = case_task(seed, legacy_task["technical_points"])
    assert set(task) == set(legacy_task)
    _, references, identity = fixture(seed)
    raw, _ = author_case(
        task, references, tmp_path / "case.json", run_identity=identity
    )
    _check_exercise_plan(NSIExercise.model_validate(raw), task, "2")


def test_three_cases_pass_pipeline_checks_with_preserved_history(tmp_path):
    from Backend.Core.france.database_case_authoring import author_case
    from Backend.Core.france.database_case_prose import case_task
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import (
        _check_exercise_plan,
        _originality,
        _tasks_for_seed_v31,
        exercise_candidate_text,
    )
    from Backend.Core.france.verification import verify_contract

    history = []
    for seed in range(270100, 270103):
        total = _tasks_for_seed_v31(seed)[1]["technical_points"]
        task = case_task(seed, total)
        _, references, identity = fixture(seed)
        raw, _ = author_case(
            task, references, tmp_path / f"case-{seed}.json", run_identity=identity
        )
        exercise = NSIExercise.model_validate(raw)
        _check_exercise_plan(exercise, task, "2")
        assert all(
            verify_contract(q.verification)["state"] == "passed"
            for q in exercise.questions
        )
        _originality(exercise, references, history)
        history.append(exercise_candidate_text(exercise))
        # A successful family must not turn off duplicate protection.
        with pytest.raises(ValueError):
            _originality(exercise, references, history)
    assert len(history) == 3


@pytest.mark.parametrize("content", ('{"origin":"model"}', "not JSON"))
def test_incompatible_checkpoint_is_never_overwritten(tmp_path, content):
    from Backend.Core.france.database_case_authoring import author_case

    task, references, identity = fixture()
    path = tmp_path / "case.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        author_case(task, references, path, run_identity=identity)
    assert path.read_text(encoding="utf-8") == content
