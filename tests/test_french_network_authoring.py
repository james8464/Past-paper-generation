"""A bounded Exercise 3 selection is checkpointed and exactly replayable."""

from copy import deepcopy

import pytest

from Backend.Core.france.network_contract import build_network_contract
from Backend.Core.france.pipeline import _tasks_for_seed


def _selection():
    return {
        "scene_id": "campus",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


class SelectionClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate_json(self, prompt):
        return self.responses.pop(0)


def test_network_selection_transport_and_replay(tmp_path):
    from Backend.Core.france.network_authoring import (
        author_network_selection,
        network_selection_prompt,
        replay_network_selection,
    )
    from Backend.Core.france.network_prose import network_selection_schema
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed(270100)[2]
    contract = build_network_contract(270100)
    schema, budget = response_policy(network_selection_prompt(task, contract, []))
    assert schema == network_selection_schema(contract)
    assert budget <= 2048
    path = tmp_path / "network-selection.json"
    raw, evidence = author_network_selection(
        SelectionClient([_selection()]), task, contract, [], path,
        run_identity=_identity(),
    )
    assert raw["id"] == "3"
    assert replay_network_selection(
        task, contract, [], evidence, run_identity=_identity()
    ) == raw


def test_network_rejects_free_text_preserves_failure_and_identity(tmp_path):
    from Backend.Core.france.network_authoring import (
        author_network_selection,
        replay_network_selection,
    )

    task = _tasks_for_seed(270100)[2]
    contract = build_network_contract(270100)
    invalid = _selection()
    invalid["question_forms"]["3a"] = "arbitrary prose"
    path = tmp_path / "network-selection.json"
    raw, evidence = author_network_selection(
        SelectionClient([invalid, _selection()]), task, contract, [], path,
        run_identity=_identity(),
    )
    assert raw["id"] == "3"
    assert evidence["failed_attempts"][0]["response"] == invalid
    with pytest.raises(ValueError, match="identity"):
        author_network_selection(
            SelectionClient([]), task, contract, [], path,
            run_identity={**_identity(), "model_digest": "c" * 64},
        )
    tampered = deepcopy(evidence)
    tampered["accepted"]["response"]["scene_id"] = "terrain"
    with pytest.raises(ValueError, match="hash"):
        replay_network_selection(
            task, contract, [], tampered, run_identity=_identity()
        )


def test_network_replay_rejects_forged_attempt_history(tmp_path):
    from Backend.Core.france.network_authoring import (
        author_network_selection,
        replay_network_selection,
    )

    task = _tasks_for_seed(270100)[2]
    contract = build_network_contract(270100)
    invalid = _selection()
    invalid["scene_id"] = "unlisted"
    path = tmp_path / "network-selection.json"
    _, evidence = author_network_selection(
        SelectionClient([invalid, _selection()]), task, contract, [], path,
        run_identity=_identity(),
    )
    for tamper in ("third_failure", "attempt_number", "valid_failed_response"):
        forged = deepcopy(evidence)
        if tamper == "third_failure":
            forged["failed_attempts"].extend(
                [deepcopy(forged["failed_attempts"][0]) for _ in range(2)]
            )
            forged["failed_attempts"][1]["attempt"] = 2
            forged["failed_attempts"][2]["attempt"] = 3
        elif tamper == "attempt_number":
            forged["failed_attempts"][0]["attempt"] = 2
        else:
            forged["failed_attempts"][0]["response"] = _selection()
            from Backend.Core.france.network_authoring import _hash
            forged["failed_attempts"][0]["response_sha256"] = _hash(_selection())
        with pytest.raises(ValueError):
            replay_network_selection(
                task, contract, [], forged, run_identity=_identity()
            )
        forged["accepted"] = None
        path.write_text(__import__("json").dumps(forged), encoding="utf-8")
        with pytest.raises(ValueError):
            author_network_selection(
                SelectionClient([_selection()]), task, contract, [], path,
                run_identity=_identity(),
            )
