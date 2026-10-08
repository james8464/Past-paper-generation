"""V17 graph/tree facts are fixed by the app, not a model's answer."""

from copy import deepcopy
from itertools import pairwise

import pytest

from Backend.Core.france.graph_tree_depth_contract import (
    GraphTreeDepthContract,
    build_graph_tree_depth_contract,
)


def test_seeded_depth_contract_has_hand_checked_graph_steps():
    data = build_graph_tree_depth_contract(270100).to_dict()

    assert data["version"] == 3
    assert data["task_ids"] == [f"1{letter}" for letter in "abcdefghij"]
    assert data["expected"]["1a"] == {
        "neighbours": ["B", "C"],
        "degree": 2,
        "incident_weight": 21,
    }
    assert data["expected"]["1b"] == {
        "path": ["A", "C", "E", "F"],
        "weight": 32,
    }
    assert data["expected"]["1c"]["steps"] == [
        {
            "settled": "A",
            "tentative": {"A": 0, "B": 7, "C": 14, "D": None, "E": None, "F": None},
            "predecessors": {"B": "A", "C": "A"},
        },
        {
            "settled": "B",
            "tentative": {"A": 0, "B": 7, "C": 11, "D": 17, "E": None, "F": None},
            "predecessors": {"B": "A", "C": "B", "D": "B"},
        },
    ]
    assert data["expected"]["1d"] == {
        "path": ["A", "B", "C", "D", "E", "F"],
        "weight": 23,
    }


def test_seeded_depth_contract_has_hand_checked_bfs_and_tree_steps():
    data = build_graph_tree_depth_contract(270100).to_dict()
    expected = data["expected"]

    assert expected["1e"]["states"] == [
        {"dequeued": "A", "queue": ["B", "C"], "visited": ["A", "B", "C"]},
        {"dequeued": "B", "queue": ["C", "D"], "visited": ["A", "B", "C", "D"]},
    ]
    assert expected["1f"] == {
        "error": "NameError",
        "misspelled": "visin",
        "correct_name": "voisin",
    }
    assert expected["1g"] == {
        "order": ["A", "B", "C", "D", "E", "F"],
        "reason": "enqueue_once",
    }
    assert expected["1h"] == {
        "search_path": [18, 13],
        "insert_key": 10,
        "parent": 13,
        "side": "gauche",
    }
    assert expected["1i"] == {"inorder": [10, 13, 18, 29, 35, 86]}
    assert expected["1j"] == {
        "wrong_comparison": ">",
        "correct_comparison": "<",
        "search_path": [18, 13, 10],
        "found": True,
    }
    assert "visin" in data["debug_case"]["faulty_code"]
    assert "if cle > noeud.valeur" in data["search_code"]


def test_depth_contract_is_seeded_and_rejects_tampered_facts():
    contract = build_graph_tree_depth_contract(270100)
    assert contract.digest == build_graph_tree_depth_contract(270100).digest
    assert contract.digest != build_graph_tree_depth_contract(270101).digest
    assert (
        GraphTreeDepthContract.from_dict(contract.to_dict()).digest == contract.digest
    )

    for mutation in (
        lambda data: data["graph"]["edges"][0].__setitem__(2, 99),
        lambda data: data["expected"]["1b"].__setitem__("weight", 999),
        lambda data: data.__setitem__("seed", 270101),
        lambda data: data.__setitem__("search_code", "return True"),
        lambda data: data["task_ids"].pop(),
    ):
        data = deepcopy(contract.to_dict())
        mutation(data)
        with pytest.raises(ValueError):
            GraphTreeDepthContract.from_dict(data)


@pytest.mark.parametrize("seed", [0, 1, 27, 270100, 270101, 999999])
def test_depth_contract_trace_and_shortest_path_agree_for_seed_range(seed):
    data = build_graph_tree_depth_contract(seed).to_dict()
    expected = data["expected"]
    graph = data["graph"]
    edge_weights = {
        frozenset((start, end)): weight for start, end, weight in graph["edges"]
    }
    path = expected["1d"]["path"]
    assert path[0] == "A" and path[-1] == "F"
    assert (
        sum(edge_weights[frozenset((start, end))] for start, end in pairwise(path))
        == expected["1d"]["weight"]
    )
    assert expected["1c"]["steps"][0]["settled"] == "A"
    assert expected["1c"]["steps"][1]["settled"] in ("B", "C")
