"""Behavioral checks for the isolated V22 before/after route case."""

from __future__ import annotations

from copy import deepcopy

import pytest

from Backend.Core.france.graph_resilience_contract import (
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_route_trace_contract import (
    GraphRouteTraceContract,
    build_graph_route_trace_contract,
)


def _independent_shortest(edges: list[list]) -> tuple[list[str], int]:
    adjacent = {node: [] for node in "ABCDEF"}
    for left, right, cost in edges:
        adjacent[left].append((right, cost))
        adjacent[right].append((left, cost))
    routes = []

    def visit(node: str, path: tuple[str, ...], cost: int) -> None:
        if node == "F":
            routes.append((cost, path))
            return
        for neighbour, weight in adjacent[node]:
            if neighbour not in path:
                visit(neighbour, (*path, neighbour), cost + weight)

    visit("A", ("A",), 0)
    cost, path = min(routes)
    return list(path), cost


def test_v22_first_route_edge_closure_changes_the_first_trace_row() -> None:
    facts = build_graph_route_trace_contract(270100).to_dict()

    assert facts["version"] == 5
    assert facts["task_ids"] == [f"1{letter}" for letter in "abcdefghij"]
    assert facts["closed_edge"] == ["A", "B"]
    assert facts["expected"]["1d"] == {
        "path": ["A", "B", "C", "D", "E", "F"],
        "weight": 23,
    }
    assert facts["expected"]["1g"]["route_after"] == ["A", "C", "D", "E", "F"]
    assert facts["expected"]["1g"]["cost_after"] == 26
    assert facts["expected"]["1c"]["steps"][0]["tentative"]["B"] == 7
    assert facts["expected"]["1g"]["steps"][0]["tentative"]["B"] is None
    assert facts["expected"]["1g"]["steps"][1]["settled"] == "C"
    assert facts["expected"]["1g"]["steps"][1]["predecessors"] == {
        "B": "C",
        "C": "A",
        "D": "C",
        "E": "C",
    }


@pytest.mark.parametrize("seed", range(270100, 270150))
def test_v22_routes_match_independent_path_enumeration(seed: int) -> None:
    facts = build_graph_route_trace_contract(seed).to_dict()
    before = facts["graph"]["edges"]
    original_path, original_cost = _independent_shortest(before)
    closed = frozenset(facts["closed_edge"])
    after = [edge for edge in before if frozenset(edge[:2]) != closed]
    replacement_path, replacement_cost = _independent_shortest(after)

    assert facts["closed_edge"] == original_path[:2]
    assert facts["expected"]["1d"] == {
        "path": original_path,
        "weight": original_cost,
    }
    assert facts["expected"]["1g"]["route_after"] == replacement_path
    assert facts["expected"]["1g"]["cost_after"] == replacement_cost
    assert replacement_cost >= original_cost
    assert replacement_path != original_path
    assert (
        facts["expected"]["1g"]["steps"][0]
        != facts["expected"]["1c"]["steps"][0]
    )
    assert build_graph_resilience_contract(seed).to_dict()["version"] == 4


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["graph"]["edges"][0].__setitem__(2, 99),
        lambda data: data["closed_edge"].__setitem__(1, "F"),
        lambda data: data["expected"]["1g"]["steps"][0]["tentative"].__setitem__(
            "B", 7
        ),
        lambda data: data["expected"]["1g"].__setitem__("cost_after", 1),
        lambda data: data.__setitem__("seed", 270101),
    ],
)
def test_v22_rejects_mutated_application_facts(mutate) -> None:
    canonical = build_graph_route_trace_contract(270100).to_dict()
    altered = deepcopy(canonical)
    mutate(altered)

    with pytest.raises(ValueError):
        GraphRouteTraceContract.from_dict(altered)
