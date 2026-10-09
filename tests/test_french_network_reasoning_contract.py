"""Locked app-owned facts for the deeper written Exercise 3."""

import copy

import pytest


def _build(seed=270100):
    from Backend.Core.france.network_reasoning_contract import (
        build_network_reasoning_contract,
    )

    return build_network_reasoning_contract(seed)


def test_network_reasoning_contract_has_twelve_tasks_and_hand_checked_routes():
    data = _build().to_dict()

    assert data["version"] == 3
    assert data["seed"] == 270100
    assert data["exercise_id"] == "3"
    assert data["task_ids"] == [f"3{letter}" for letter in "abcdefghijkl"]
    assert data["links"] == [
        ["Central", "R1", 5],
        ["Central", "R2", 8],
        ["R1", "R3", 6],
        ["R1", "R2", 7],
        ["R2", "R3", 5],
        ["R2", "Station", 13],
        ["R3", "Station", 7],
    ]
    initial = data["expected"]["before"]
    changed = data["expected"]["after"]
    assert (initial["path"], initial["cost"]) == (
        ["Central", "R1", "R3", "Station"],
        18,
    )
    assert (changed["path"], changed["cost"]) == (
        ["Central", "R2", "R3", "Station"],
        20,
    )
    assert initial["predecessors"]["R3"] == "R1"
    assert changed["predecessors"]["R3"] == "R2"
    assert changed["trace"][2]["tentative"]["Station"] == 21
    assert changed["trace"][3]["tentative"]["Station"] == 20


@pytest.mark.parametrize("seed", range(270100, 270116))
def test_network_reasoning_contract_is_deterministic_with_unique_changed_route(seed):
    first = _build(seed)
    second = _build(seed)
    data = first.to_dict()

    assert first.digest == second.digest
    assert data == second.to_dict()
    assert data["expected"]["before"]["path"] != data["expected"]["after"]["path"]
    assert data["expected"]["before"]["unique"] is True
    assert data["expected"]["after"]["unique"] is True
    assert len(data["expected"]["after"]["trace"]) == 5


def test_network_reasoning_process_and_security_states_are_bounded():
    data = _build().to_dict()

    assert data["working_surfaces"] == {
        "route_nodes": ["Central", "R1", "R2", "R3", "Station"],
        "process_steps": ["t0", "t1", "t2", "t3"],
        "threat_scenarios": [
            "Observateur passif",
            "Authentification",
            "Métadonnées",
            "Terminal compromis",
        ],
    }

    assert data["process_schedule"] == [
        {"step": "t0", "P1": "détient A", "P2": "détient B"},
        {"step": "t1", "P1": "attend B", "P2": "attend A"},
        {"step": "t2", "P1": "obtient B", "P2": "arrêté, libère B"},
        {
            "step": "t3",
            "P1": "termine, libère A et B",
            "P2": "redémarre, prend A puis B",
        },
    ]
    assert data["expected"]["wait_for"] == [["P1", "P2"], ["P2", "P1"]]
    assert data["expected"]["recovery_order"] == ["P2", "P1", "P2"]
    assert data["security_messages"] == [
        {"step": 1, "sender": "Station", "content": "clé publique authentifiée"},
        {
            "step": 2,
            "sender": "Capteur",
            "content": "clé de session chiffrée pour Station",
        },
        {
            "step": 3,
            "sender": "Capteur",
            "content": "mesures chiffrées avec la clé de session",
        },
    ]
    assert data["expected"]["threats"] == {
        "passive_reads_message": False,
        "station_authenticated": True,
        "sender_authenticated": False,
        "metadata_visible": True,
        "compromised_endpoint_protected": False,
    }


@pytest.mark.parametrize("mutation", ["cost", "state", "threat", "working", "extra"])
def test_network_reasoning_contract_rejects_tampering(mutation):
    from Backend.Core.france.network_reasoning_contract import NetworkReasoningContract

    original = _build()
    data = copy.deepcopy(original.to_dict())
    if mutation == "cost":
        data["links"][0][2] += 1
    elif mutation == "state":
        data["process_schedule"][1]["P1"] = "attend A"
    elif mutation == "threat":
        data["expected"]["threats"]["sender_authenticated"] = True
    elif mutation == "working":
        data["working_surfaces"]["route_nodes"].append("Other")
    else:
        data["unexpected"] = "not part of the locked case"
    with pytest.raises(ValueError):
        NetworkReasoningContract.from_dict(data)


def test_network_reasoning_contract_rejects_non_integer_identity():
    from Backend.Core.france.network_reasoning_contract import NetworkReasoningContract

    data = _build().to_dict()
    data["seed"] = True
    with pytest.raises(ValueError):
        NetworkReasoningContract.from_dict(data)
