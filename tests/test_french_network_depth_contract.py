"""The deeper network case is deterministic, independently checkable, and sealed."""

from copy import deepcopy

import pytest

from Backend.Core.france.network_depth_contract import (
    NetworkDepthContract,
    build_network_depth_contract,
)

BASE_LINKS = (
    ("Central", "R1", 2),
    ("Central", "R2", 5),
    ("R1", "R3", 3),
    ("R1", "R2", 4),
    ("R2", "R3", 2),
    ("R2", "Station", 10),
    ("R3", "Station", 4),
)


def _all_routes(links):
    """Independent exhaustive oracle, not the production Dijkstra method."""
    neighbours = {}
    for left, right, weight in links:
        neighbours.setdefault(left, []).append((right, weight))
        neighbours.setdefault(right, []).append((left, weight))
    pending = [("Central", ("Central",), 0)]
    routes = []
    while pending:
        node, path, cost = pending.pop()
        if node == "Station":
            routes.append((cost, path))
            continue
        pending.extend(
            (next_node, (*path, next_node), cost + weight)
            for next_node, weight in neighbours[node]
            if next_node not in path
        )
    return sorted(routes)


def test_all_four_profiles_have_unique_changed_shortest_routes():
    profiles = {}
    for seed in range(100):
        contract = build_network_depth_contract(seed)
        data = contract.to_dict()
        offset = data["profile_offset"]
        profiles.setdefault(offset, data)
        assert data["version"] == 2
        assert data["task_ids"] == ["3a", "3b", "3c", "3d", "3e", "3f"]
        assert data["links"] == [[a, b, c + offset] for a, b, c in BASE_LINKS]
        assert data["change"] == {"link": ["R1", "R3"], "new_cost": 12 + offset}
        assert NetworkDepthContract.from_dict(data).digest == contract.digest
        before = _all_routes(data["links"])
        changed = deepcopy(data["links"])
        changed[2][2] = data["change"]["new_cost"]
        after = _all_routes(changed)
        assert before[0][0] < before[1][0]
        assert after[0][0] < after[1][0]
        assert data["expected"]["before"]["path"] == list(before[0][1])
        assert data["expected"]["before"]["cost"] == before[0][0]
        assert data["expected"]["after"]["path"] == list(after[0][1])
        assert data["expected"]["after"]["cost"] == after[0][0]
        assert before[0][1] != after[0][1]
    assert set(profiles) == {0, 1, 2, 3}


def test_dijkstra_trace_is_explicit_and_recomputed():
    data = next(
        build_network_depth_contract(seed).to_dict()
        for seed in range(100)
        if build_network_depth_contract(seed).to_dict()["profile_offset"] == 0
    )
    before = data["expected"]["before"]
    after = data["expected"]["after"]
    assert before["settled_order"] == ["Central", "R1", "R2", "R3", "Station"]
    assert after["settled_order"] == ["Central", "R1", "R2", "R3", "Station"]
    assert before["path"] == ["Central", "R1", "R3", "Station"]
    assert before["cost"] == 9
    assert after["path"] == ["Central", "R2", "R3", "Station"]
    assert after["cost"] == 11
    assert before["trace"][0] == {
        "settled": "Central",
        "distance": 0,
        "tentative": {"Central": 0, "R1": 2, "R2": 5, "R3": None, "Station": None},
    }
    assert before["trace"][-1]["tentative"]["Station"] == 9
    assert after["trace"][-1]["tentative"]["Station"] == 11


def test_forged_seeded_facts_or_derived_trace_fail_closed():
    data = build_network_depth_contract(270100).to_dict()
    mutations = (
        lambda value: value["links"].pop(),
        lambda value: value["links"][1].__setitem__(2, 99),
        lambda value: value["change"].__setitem__("new_cost", 99),
        lambda value: value["expected"]["before"].__setitem__("cost", 99),
        lambda value: value["expected"]["after"]["settled_order"].reverse(),
        lambda value: value["expected"]["before"]["trace"][0]["tentative"].__setitem__("R1", 99),
        lambda value: value.__setitem__("version", True),
        lambda value: value.__setitem__("profile_offset", True),
    )
    for mutate in mutations:
        forged = deepcopy(data)
        mutate(forged)
        with pytest.raises(ValueError):
            NetworkDepthContract.from_dict(forged)


def test_fixed_process_and_security_premises_are_sealed():
    data = build_network_depth_contract(270100).to_dict()
    assert data["processes"] == {
        "P1": {"holds": "A", "waits_for": "B"},
        "P2": {"holds": "B", "waits_for": "A"},
        "recovery": "abort_P2_release_B",
        "prevention_order": ["A", "B"],
    }
    assert data["security"] == {
        "receiver_public_key_authenticated": True,
        "sender_signature": False,
        "session_key_encrypted_for_receiver": True,
        "observer": "passive",
    }
    for section in ("processes", "security"):
        for key in data[section]:
            forged = deepcopy(data)
            forged[section][key] = None
            with pytest.raises(ValueError):
                NetworkDepthContract.from_dict(forged)
