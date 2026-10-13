"""V23's incident facts must be causal, deterministic and immutable."""

from copy import deepcopy

import pytest


def _contract(seed=270100):
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )

    return build_network_incident_contract(seed)


def test_v23_hand_checked_route_deadline_and_recovery():
    facts = _contract().to_dict()
    assert facts["version"] == 4
    assert facts["task_ids"] == [f"3{letter}" for letter in "abcdefghijkl"]
    assert facts["expected"]["before"]["path"] == ["Central", "R1", "R3", "Station"]
    assert facts["expected"]["before"]["cost"] == 18
    assert facts["expected"]["after"]["path"] == ["Central", "R2", "R3", "Station"]
    assert facts["expected"]["after"]["cost"] == 20
    assert facts["packet"]["deadline"] == 19
    assert facts["expected"]["packet"] == {
        "before_arrival": 18,
        "after_arrival": 20,
        "late_by": 1,
        "before_on_time": True,
        "after_on_time": False,
    }
    assert facts["expected"]["wait_for"] == [["P1", "P2"], ["P2", "P1"]]
    assert facts["expected"]["recovery_order"] == ["P2", "P1", "P2"]
    assert facts["expected"]["packet_after_recovery"] == "traité"
    assert facts["packet"]["sender"] == "Central"
    assert facts["packet"]["receiver"] == "Station"
    assert facts["security"]["messages"][1][1] == "Central"
    assert facts["expected"]["threats"]["central_authenticated"] is True
    assert facts["expected"]["threats"]["sender_authenticated"] is False


@pytest.mark.parametrize("seed", range(270100, 270116))
def test_v23_every_seed_changes_route_and_misses_derived_deadline(seed):
    first = _contract(seed)
    second = _contract(seed)
    facts = first.to_dict()
    assert first.digest == second.digest
    assert facts == second.to_dict()
    assert facts["expected"]["before"]["path"] != facts["expected"]["after"]["path"]
    assert facts["packet"]["deadline"] == facts["expected"]["before"]["cost"] + 1
    assert facts["expected"]["after"]["cost"] > facts["packet"]["deadline"]
    assert facts["expected"]["packet"]["late_by"] == 1


@pytest.mark.parametrize("mutation", ["link", "deadline", "queue", "threat", "extra"])
def test_v23_deserialization_rejects_edited_incident_fact(mutation):
    from Backend.Core.france.network_incident_contract import NetworkIncidentContract

    facts = deepcopy(_contract().to_dict())
    if mutation == "link":
        facts["links"][0][2] += 1
    elif mutation == "deadline":
        facts["packet"]["deadline"] += 1
    elif mutation == "queue":
        facts["processes"]["queue_state"] = "traité"
    elif mutation == "threat":
        facts["expected"]["threats"]["sender_authenticated"] = True
    else:
        facts["unexpected"] = 1
    with pytest.raises(ValueError):
        NetworkIncidentContract.from_dict(facts)


def test_v23_contract_rejects_bool_seed_and_prior_version():
    from Backend.Core.france.network_incident_contract import NetworkIncidentContract

    facts = _contract().to_dict()
    for seed, version in ((True, 4), (270100, 3)):
        bad = deepcopy(facts)
        bad["seed"] = seed
        bad["version"] = version
        with pytest.raises(ValueError):
            NetworkIncidentContract.from_dict(bad)
