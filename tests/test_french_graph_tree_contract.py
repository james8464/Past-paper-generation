"""Contract facts must be reproducible and independently checkable."""

from copy import deepcopy

import pytest

from Backend.Core.france.graph_tree_contract import (
    GraphTreeContract,
    build_graph_tree_contract,
)


def test_seed_repeats_the_same_contract_and_changes_data_for_another_seed():
    first = build_graph_tree_contract(270100, "1")
    repeat = build_graph_tree_contract(270100, "1")
    other = build_graph_tree_contract(270101, "1")

    assert first.to_dict() == repeat.to_dict()
    assert first.digest == repeat.digest
    assert first.digest != other.digest
    assert first.to_dict()["version"] == 1
    assert first.to_dict()["task_ids"] == ["1a", "1b", "1c", "1d", "1e", "1f"]


def test_generated_materials_are_connected_and_the_tree_is_search_ordered():
    data = build_graph_tree_contract(270100, "1").to_dict()
    graph = data["graph"]
    tree = data["tree"]
    assert graph["id"] == "reseau"
    assert set(graph["nodes"]) == {"A", "B", "C", "D", "E", "F"}
    assert tree["id"] == "arbre"
    assert tree["columns"] == ["cle", "gauche", "droite"]
    assert "class Noeud:" in data["node_api"]
    assert "self.gauche" in data["node_api"]
    assert len(tree["rows"]) == 5
    assert (
        GraphTreeContract.from_dict(data).digest
        == build_graph_tree_contract(270100, "1").digest
    )


def test_hand_checked_graph_and_tree_results():
    data = build_graph_tree_contract(270100, "1").to_dict()
    graph = data["graph"]
    graph["edges"] = [
        ["A", "B", 4],
        ["B", "C", 3],
        ["C", "D", 2],
        ["D", "E", 5],
        ["E", "F", 2],
        ["A", "C", 10],
        ["B", "D", 8],
    ]
    data["tree"] = {
        "id": "arbre",
        "columns": ["cle", "gauche", "droite"],
        "root": 40,
        "rows": [
            [40, 20, 60],
            [20, 10, 30],
            [10, None, None],
            [30, None, None],
            [60, None, None],
        ],
        "insert_key": 25,
    }
    data.pop("expected")
    contract = GraphTreeContract.from_dict(data)
    expected = contract.to_dict()["expected"]

    assert expected["1a"] == {"path": ["A", "B", "C", "D", "E", "F"], "weight": 16}
    assert expected["1b"] == {"neighbours": ["B", "C"], "weight_sum": 14}
    assert expected["1c"] == {"fault": "misspelled_neighbour", "correct_name": "voisin"}
    assert expected["1d"] == {"order": ["A", "B", "C", "D", "E", "F"]}
    assert expected["1e"] == {"search_path": [40, 20, 30], "insert_key": 25}
    assert expected["1f"] == {"inorder": [10, 20, 25, 30, 40, 60]}


def test_tampered_edge_cannot_keep_the_old_canonical_answer():
    data = build_graph_tree_contract(270100, "1").to_dict()
    data["graph"]["edges"][0][2] += 1
    with pytest.raises(ValueError, match=r"canonical|expected|result"):
        GraphTreeContract.from_dict(data)


def test_duplicate_tree_key_is_rejected():
    data = build_graph_tree_contract(270100, "1").to_dict()
    data = deepcopy(data)
    data["tree"]["rows"][1][0] = data["tree"]["rows"][0][0]
    data.pop("expected")
    with pytest.raises(ValueError, match=r"duplicate|unique|BST"):
        GraphTreeContract.from_dict(data)


def test_graph_tree_verification_recomputes_canonical_results_and_rejects_tampering():
    from Backend.Core.france.verification import verify_contract

    data = build_graph_tree_contract(270100, "1").to_dict()
    for task_id in data["task_ids"]:
        check = {
            "kind": "graph_tree",
            "contract": data,
            "task_id": task_id,
            "expected": data["expected"][task_id],
        }
        assert verify_contract(check)["state"] == "passed"
    check["expected"] = {}
    assert verify_contract(check)["state"] == "failed"
    check["expected"] = data["expected"][task_id]
    check["contract"]["graph"]["edges"][0][2] += 1
    assert verify_contract(check)["state"] == "failed"
