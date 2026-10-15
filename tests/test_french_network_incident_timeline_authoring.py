"""V26 bounded wording selection and timed candidate hashes replay exactly."""

from copy import deepcopy

import pytest

from Backend.Core.france.network_incident_timeline_authoring import (
    author_network_incident_timeline_selection,
    replay_network_incident_timeline_selection,
)
from Backend.Core.france.network_incident_timeline_contract import (
    build_network_incident_timeline_contract,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v25


class Client:
    def generate_json(self, _prompt):
        return {
            "scene_id": "station",
            "question_forms": {f"3{x}": f"3{x}-q1" for x in "abcdefghijkl"},
            "rubric_forms": {f"3{x}": f"3{x}-r1" for x in "abcdefghijkl"},
        }


def test_v26_selection_replays_timed_candidate_and_rejects_forged_hash(tmp_path):
    task = deepcopy(_tasks_for_seed_v25(270100)[2])
    task["question_blueprint"][6].update(
        points="0.75", estimated_minutes=8, difficulty=4
    )
    task["question_blueprint"][9].update(points="0.25", estimated_minutes=3)
    contract = build_network_incident_timeline_contract(270100)
    identity = {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }
    raw, evidence = author_network_incident_timeline_selection(
        Client(), task, contract, [], tmp_path / "selection.json", run_identity=identity
    )
    assert (
        raw["questions"][6]["verification"]["kind"]
        == "network_incident_timeline_contract"
    )
    assert (
        replay_network_incident_timeline_selection(
            task, contract, [], evidence, run_identity=identity
        )
        == raw
    )
    forged = deepcopy(evidence)
    forged["candidate_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        replay_network_incident_timeline_selection(
            task, contract, [], forged, run_identity=identity
        )
    with pytest.raises(ValueError, match="identity"):
        replay_network_incident_timeline_selection(
            task,
            contract,
            [],
            evidence,
            run_identity={**identity, "model_digest": "c" * 64},
        )
