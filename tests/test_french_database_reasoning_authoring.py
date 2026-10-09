"""V19 selection must bind finite wording and retain failed attempts."""

from copy import deepcopy

import pytest

from Backend.Core.france.database_depth_contract import build_database_depth_contract
from Backend.Core.france.database_reasoning_prose import (
    database_reasoning_selection_schema,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v18


def _selection():
    return {
        "scene_id": "atelier",
        "question_forms": {f"2{x}": f"2{x}-q1" for x in "abcdefghij"},
        "rubric_forms": {f"2{x}": f"2{x}-r1" for x in "abcdefghij"},
    }


class _Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate_json(self, _prompt):
        return next(self.responses)


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


def test_v19_prompt_schema_and_replay_bind_all_evidence(tmp_path):
    from Backend.Core.france import database_reasoning_authoring as authoring
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v18(270100)[1]
    contract = build_database_depth_contract(270100)
    prompt = authoring.database_reasoning_selection_prompt(task, contract, [])
    assert prompt.startswith("Sélectionne l'exercice 2 v19")
    assert response_policy(prompt)[0] == database_reasoning_selection_schema(contract)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))
    bad = _selection()
    bad["question_forms"]["2a"] = "unknown"
    path = tmp_path / "v19.json"
    candidate, evidence = authoring.author_database_reasoning_selection(
        _Client([bad, _selection()]),
        task,
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert len(evidence["failed_attempts"]) == 1
    assert candidate == authoring.replay_database_reasoning_selection(
        task, contract, [], evidence, run_identity=_identity()
    )
    for change in (
        lambda e: e["accepted"]["response"]["question_forms"].update({"2j": "wrong"}),
        lambda e: e["failed_attempts"][0].update({"response_sha256": "0" * 64}),
        lambda e: e.update({"prose_catalogue_sha256": "0" * 64}),
    ):
        tampered = deepcopy(evidence)
        change(tampered)
        with pytest.raises(ValueError):
            authoring.replay_database_reasoning_selection(
                task, contract, [], tampered, run_identity=_identity()
            )


def test_v19_blueprint_changes_only_database_source():
    from Backend.Core.france.pipeline import _tasks_for_seed_v19

    old = _tasks_for_seed_v18(270100)
    new = _tasks_for_seed_v19(270100)
    assert new == old and new is not old
    assert len(new) == 3
    assert sum(float(task["technical_points"]) for task in new) == 18
    assert new[1]["minutes"] == 70
