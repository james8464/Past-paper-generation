"""Versioned network selections preserve failures and replay only exact identities."""

from copy import deepcopy

import pytest

from Backend.Core.france.network_depth_contract import build_network_depth_contract
from Backend.Core.france.pipeline import _tasks_for_seed_v15


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

    def generate_json(self, _prompt):
        return self.responses.pop(0)


def test_v15_selection_prompt_is_finite_and_replayable(tmp_path):
    from Backend.Core.france.network_depth_authoring import (
        author_network_depth_selection,
        network_depth_selection_prompt,
        replay_network_depth_selection,
    )
    from Backend.Core.france.network_depth_prose import network_depth_selection_schema
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v15(270100)[2]
    contract = build_network_depth_contract(270100)
    schema, budget = response_policy(network_depth_selection_prompt(task, contract, []))
    assert schema == network_depth_selection_schema(contract)
    assert budget <= 2048
    path = tmp_path / "v15-selection.json"
    raw, evidence = author_network_depth_selection(
        SelectionClient([_selection()]),
        task,
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert raw["id"] == "3"
    assert (
        replay_network_depth_selection(
            task, contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    assert path.exists()


def test_v15_selection_rejects_free_text_and_preserves_failed_attempt(tmp_path):
    from Backend.Core.france.network_depth_authoring import (
        author_network_depth_selection,
        replay_network_depth_selection,
    )

    task = _tasks_for_seed_v15(270100)[2]
    contract = build_network_depth_contract(270100)
    bad = _selection()
    bad["question_forms"]["3a"] = "coût inventé"
    path = tmp_path / "v15-selection.json"
    raw, evidence = author_network_depth_selection(
        SelectionClient([bad, _selection()]),
        task,
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert raw["id"] == "3"
    assert evidence["failed_attempts"][0]["response"] == bad
    assert evidence["failed_attempts"][0]["attempt"] == 1
    with pytest.raises(ValueError, match="identity"):
        author_network_depth_selection(
            SelectionClient([]),
            task,
            contract,
            [],
            path,
            run_identity={**_identity(), "model_digest": "c" * 64},
        )
    forged = deepcopy(evidence)
    forged["accepted"]["response"]["scene_id"] = "terrain"
    with pytest.raises(ValueError):
        replay_network_depth_selection(
            task, contract, [], forged, run_identity=_identity()
        )


def test_v15_replay_rejects_forged_contract_and_failure_history(tmp_path):
    from Backend.Core.france.network_depth_authoring import (
        author_network_depth_selection,
        replay_network_depth_selection,
    )

    task = _tasks_for_seed_v15(270100)[2]
    contract = build_network_depth_contract(270100)
    bad = _selection()
    bad["scene_id"] = "unknown"
    _, evidence = author_network_depth_selection(
        SelectionClient([bad, _selection()]),
        task,
        contract,
        [],
        tmp_path / "v15-selection.json",
        run_identity=_identity(),
    )
    forged = deepcopy(evidence)
    forged["failed_attempts"][0]["attempt"] = 2
    with pytest.raises(ValueError):
        replay_network_depth_selection(
            task, contract, [], forged, run_identity=_identity()
        )
    forged = deepcopy(evidence)
    forged["contract_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        replay_network_depth_selection(
            task, contract, [], forged, run_identity=_identity()
        )
