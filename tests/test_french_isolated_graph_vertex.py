"""Shortest paths use every declared vertex, including isolated ones."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from Backend.Core.france.llm_pipeline import validate_authored_exercise
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import raw_exercise


def graph_exercise(start="C", end="C", expected=0):
    raw = raw_exercise()
    raw["materials"] = [
        {
            "kind": "weighted_graph",
            "id": "graphe",
            "title": "Graphe témoin",
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 1]],
            "directed": False,
        }
    ]
    for question in raw["questions"]:
        question["material_ids"] = ["graphe"]
    raw["questions"][0].update(
        prompt=f"Déterminer la distance minimale du sommet {start} au sommet {end}.",
        answer=str(expected),
        verification={
            "kind": "shortest_path",
            "material_id": "graphe",
            "edges": [["A", "B", 1]],
            "directed": False,
            "start": start,
            "end": end,
            "expected": expected,
        },
    )
    return raw


@pytest.mark.parametrize("directed", [False, True])
def test_public_admission_accepts_declared_isolated_vertex_zero_path(directed):
    raw = graph_exercise()
    raw["materials"][0]["directed"] = directed
    raw["questions"][0]["verification"]["directed"] = directed
    assert (
        validate_authored_exercise(raw, "1").questions[0].verification["expected"] == 0
    )


@pytest.mark.parametrize(
    "start,end,expected",
    [("X", "X", 0), ("C", "A", 0), ("A", "C", 0), ("C", "C", 1)],
)
def test_unlisted_unreachable_and_wrong_distances_remain_refused(start, end, expected):
    with pytest.raises(ValueError):
        validate_authored_exercise(graph_exercise(start, end, expected), "1")


def test_existing_edge_path_and_contract_identity_remain_unchanged():
    raw = graph_exercise("A", "B", 1)
    original = deepcopy(raw)
    admitted = validate_authored_exercise(raw, "1")
    assert raw == original
    assert (
        admitted.questions[0].verification == original["questions"][0]["verification"]
    )


def test_historical_unbound_contract_does_not_invent_isolated_vertices():
    contract = graph_exercise()["questions"][0]["verification"]
    assert not verify_contract(contract)["passed"]
    contract.update(start="A", end="B", expected=1)
    assert verify_contract(contract)["passed"]


@pytest.mark.parametrize(
    "field,value", [("edges", [["A", "C", 1]]), ("directed", True)]
)
def test_source_graph_divergence_still_refused(field, value):
    raw = graph_exercise()
    raw["questions"][0]["verification"][field] = value
    with pytest.raises(ValueError):
        validate_authored_exercise(raw, "1")


@pytest.mark.parametrize("nodes", [[], ["A", "A"], "ABC", ["A", 2], ["A", []]])
def test_invalid_trusted_node_context_is_refused(nodes):
    contract = graph_exercise("A", "B", 1)["questions"][0]["verification"]
    assert not verify_contract(contract, graph_nodes=nodes)["passed"]


def test_trusted_context_cannot_gain_vertices_from_foreign_edges():
    contract = graph_exercise("A", "B", 1)["questions"][0]["verification"]
    assert not verify_contract(contract, graph_nodes=["A", "C"])["passed"]


def test_authored_nodes_cannot_replace_the_printed_graph():
    raw = graph_exercise("X", "X", 0)
    raw["questions"][0]["verification"]["nodes"] = ["A", "B", "C", "X"]
    with pytest.raises(SchemaValidationError):
        validate_authored_exercise(raw, "1")
