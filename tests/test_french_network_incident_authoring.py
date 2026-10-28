# V23 finite model selection is hash-bound and replayable.

from copy import deepcopy

import pytest

from Backend.Core.france.network_incident_contract import (
    build_network_incident_contract,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v22


def _selection():
    return {
        "scene_id": "station",
        "question_forms": {f"3{x}": f"3{x}-q1" for x in "abcdefghijkl"},
        "rubric_forms": {f"3{x}": f"3{x}-r1" for x in "abcdefghijkl"},
    }


class Client:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate_json(self, _prompt):
        return self.responses.pop(0)


def test_v23_selection_accepts_only_registered_ids_and_replays_exact_hashes(tmp_path):
    from Backend.Core.france.network_incident_authoring import (
        author_network_incident_selection,
        network_incident_selection_prompt,
        replay_network_incident_selection,
    )
    from Backend.Core.france.network_incident_prose import (
        network_incident_selection_schema,
    )
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v22(270100)[2]
    contract = build_network_incident_contract(270100)
    schema, budget = response_policy(
        network_incident_selection_prompt(task, contract, [])
    )
    assert schema == network_incident_selection_schema(contract)
    assert budget <= 2048
    identity = {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }
    bad = deepcopy(_selection())
    bad["question_forms"]["3d"] = "free-text"
    path = tmp_path / "v23-selection.json"
    raw, evidence = author_network_incident_selection(
        Client([bad, _selection()]), task, contract, [], path, run_identity=identity
    )
    assert raw["id"] == "3"
    assert evidence["failed_attempts"][0]["response"] == bad
    assert (
        replay_network_incident_selection(
            task, contract, [], evidence, run_identity=identity
        )
        == raw
    )
    forged = deepcopy(evidence)
    forged["accepted"]["response"]["scene_id"] = "invented"
    with pytest.raises(ValueError):
        replay_network_incident_selection(
            task, contract, [], forged, run_identity=identity
        )
    forged = deepcopy(evidence)
    forged["contract_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        replay_network_incident_selection(
            task, contract, [], forged, run_identity=identity
        )
    with pytest.raises(ValueError):
        author_network_incident_selection(
            Client([]),
            task,
            contract,
            [],
            path,
            run_identity={**identity, "model_digest": "c" * 64},
        )
