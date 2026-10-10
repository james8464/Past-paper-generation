"""V21 selection is finite, source-bound, and isolated from old packages."""

from __future__ import annotations

import importlib
from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.database_audit_contract import build_database_audit_contract
from Backend.Core.france.database_audit_prose import database_audit_selection_schema


def _authoring():
    try:
        return importlib.import_module("Backend.Core.france.database_audit_authoring")
    except ModuleNotFoundError:
        pytest.fail("V21 database-audit authoring is not implemented")


def _selection():
    return {
        "scene_id": "atelier",
        "question_forms": {f"2{x}": f"2{x}-q1" for x in "abcdefghij"},
        "rubric_forms": {f"2{x}": f"2{x}-r1" for x in "abcdefghij"},
    }


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


class _Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate_json(self, _prompt):
        return next(self.responses)


def test_v21_blueprint_keeps_three_exercises_and_exact_credit() -> None:
    from Backend.Core.france.pipeline import _tasks_for_seed_v20, _tasks_for_seed_v21

    for seed in (0, 1, 270100, 270101):
        old = _tasks_for_seed_v20(seed)
        new = _tasks_for_seed_v21(seed)
        assert [task["question_blueprint"][0]["id"][0] for task in new] == [
            "1",
            "2",
            "3",
        ]
        assert new[0] == old[0] and new[2] == old[2]
        assert new is not old
        assert sum(Decimal(task["technical_points"]) for task in new) == Decimal(18)
        assert new[1]["minutes"] == 70
        assert [q["id"] for q in new[1]["question_blueprint"]] == [
            f"2{x}" for x in "abcdefghij"
        ]
        assert sum(
            Decimal(q["points"]) for q in new[1]["question_blueprint"]
        ) == Decimal(new[1]["technical_points"])
        assert sum(q["estimated_minutes"] for q in new[1]["question_blueprint"]) == 70
        assert [q["part_id"] for q in new[1]["question_blueprint"]] == list(
            "AAAABBCCCC"
        )


def test_v21_policy_and_replay_bind_source_prompt_reference_and_run(tmp_path) -> None:
    authoring = _authoring()
    from Backend.Core.france.pipeline import _tasks_for_seed_v21
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v21(270100)[1]
    contract = build_database_audit_contract(270100)
    refs = [{"source_id": "official-nsi-programme", "snippet": "programme"}]
    prompt = authoring.database_audit_selection_prompt(task, contract, refs)
    assert prompt.startswith("Sélectionne l'exercice 2 v21")
    assert response_policy(prompt)[0] == database_audit_selection_schema(contract)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))

    invalid = _selection()
    invalid["question_forms"]["2a"] = "free"
    path = tmp_path / "audit-v21.json"
    candidate, evidence = authoring.author_database_audit_selection(
        _Client([invalid, _selection()]),
        task,
        contract,
        refs,
        path,
        run_identity=_identity(),
    )
    assert len(evidence["failed_attempts"]) == 1
    assert candidate == authoring.replay_database_audit_selection(
        task, contract, refs, evidence, run_identity=_identity()
    )
    changes = (
        lambda e: e["accepted"]["response"]["question_forms"].update({"2j": "free"}),
        lambda e: e["accepted"].update({"prompt_sha256": "0" * 64}),
        lambda e: e.update({"contract_sha256": "0" * 64}),
        lambda e: e.update({"prose_catalogue_sha256": "0" * 64}),
        lambda e: e["failed_attempts"][0].update({"response_sha256": "0" * 64}),
    )
    for change in changes:
        tampered = deepcopy(evidence)
        change(tampered)
        with pytest.raises(ValueError):
            authoring.replay_database_audit_selection(
                task, contract, refs, tampered, run_identity=_identity()
            )
    with pytest.raises(ValueError):
        authoring.replay_database_audit_selection(
            task,
            contract,
            [{**refs[0], "snippet": "changed"}],
            evidence,
            run_identity=_identity(),
        )
    with pytest.raises(ValueError):
        authoring.replay_database_audit_selection(
            task,
            contract,
            refs,
            evidence,
            run_identity={**_identity(), "implementation_sha256": "c" * 64},
        )
    with pytest.raises(ValueError):
        authoring.replay_database_audit_selection(
            {**task, "minutes": 69},
            contract,
            refs,
            evidence,
            run_identity=_identity(),
        )
