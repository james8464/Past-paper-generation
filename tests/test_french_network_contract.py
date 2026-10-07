"""The third exercise must be answerable from application-owned facts."""

from copy import deepcopy

import pytest

from Backend.Core.france.network_contract import NetworkContract, build_network_contract


@pytest.mark.parametrize("seed", [270100, 270101, 270102, 1, 999999])
def test_seeded_paths_change_without_ties(seed):
    contract = build_network_contract(seed)
    data = contract.to_dict()
    edges = data["links"]
    assert len(edges) == 4
    assert {tuple(edge[:2]) for edge in edges} == {
        ("Central", "R1"),
        ("R1", "Station"),
        ("Central", "R2"),
        ("R2", "Station"),
    }
    expected = data["expected"]
    assert expected["before"]["path"] != expected["after"]["path"]
    assert expected["before"]["cost"] != expected["before"]["other_cost"]
    assert expected["after"]["cost"] != expected["after"]["other_cost"]
    assert all(type(edge[2]) is int and edge[2] > 0 for edge in edges)
    assert NetworkContract.from_dict(data).digest == contract.digest


def test_tampered_route_or_unprinted_link_rejected():
    data = build_network_contract(270100).to_dict()
    forged = deepcopy(data)
    forged["expected"]["before"]["cost"] += 1
    with pytest.raises(ValueError):
        NetworkContract.from_dict(forged)
    forged = deepcopy(data)
    forged["links"].pop()
    with pytest.raises(ValueError):
        NetworkContract.from_dict(forged)


def test_process_deadlock_and_crypto_premises_are_fixed():
    data = build_network_contract(270100).to_dict()
    assert data["processes"] == [
        ["B", "A", "B"],
        ["C", "B", "A"],
    ]
    assert data["security"] == {
        "pre_shared_secret": False,
        "receiver_public_key_authenticated": True,
        "observer": "passive",
    }
    forged = deepcopy(data)
    forged["processes"][1][2] = "B"
    with pytest.raises(ValueError):
        NetworkContract.from_dict(forged)
    forged = deepcopy(data)
    forged["security"]["receiver_public_key_authenticated"] = False
    with pytest.raises(ValueError):
        NetworkContract.from_dict(forged)


def test_boolean_version_is_not_an_integer_version():
    forged = build_network_contract(270100).to_dict()
    forged["version"] = True
    with pytest.raises(ValueError):
        NetworkContract.from_dict(forged)


def test_network_verifier_recomputes_all_results_and_rejects_tampering():
    from Backend.Core.france.verification import verify_contract

    data = build_network_contract(270100).to_dict()
    check = {
        "kind": "network_contract",
        "contract": data,
        "task_id": "3b",
        "expected": data["expected"],
    }
    assert verify_contract(check)["state"] == "passed"
    forged = deepcopy(check)
    forged["expected"]["after"]["cost"] += 1
    assert verify_contract(forged)["state"] == "failed"
    forged = deepcopy(check)
    forged["contract"]["links"][1][2] += 1
    assert verify_contract(forged)["state"] == "failed"
