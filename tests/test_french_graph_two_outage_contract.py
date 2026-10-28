# V25 route facts are immutable and independently checkable.

from __future__ import annotations

from copy import deepcopy
from importlib import import_module
from unittest.mock import patch

import pytest


def _module():
    return import_module("Backend.Core.france.graph_two_outage_contract")


def _build(seed: int):
    return _module().build_graph_two_outage_contract(seed)


def _enumerated_minimum(edges: list[list]) -> tuple[list[str], int]:
    adjacent = {node: [] for node in "ABCDEF"}
    for left, right, weight in edges:
        adjacent[left].append((right, weight))
        adjacent[right].append((left, weight))
    routes: list[tuple[int, tuple[str, ...]]] = []

    def visit(node: str, path: tuple[str, ...], cost: int) -> None:
        if node == "F":
            routes.append((cost, path))
            return
        for neighbour, weight in adjacent[node]:
            if neighbour not in path:
                visit(neighbour, (*path, neighbour), cost + weight)

    visit("A", ("A",), 0)
    minimum, path = min(routes)
    return list(path), minimum


def test_v25_seed_270100_has_two_distinct_closures_and_verified_survivor() -> None:
    facts = _build(270100).to_dict()

    assert facts["version"] == 6
    assert facts["closed_edge"] == ["A", "B"]
    assert facts["closed_edge_second"] == ["E", "F"]
    assert facts["expected"]["1f"]["route_after"] == ["A", "C", "D", "E", "F"]
    assert facts["expected"]["1f"]["cost_after"] == 26
    assert facts["expected"]["1g"] == {
        "route_before": ["A", "C", "D", "E", "F"],
        "cost_before": 26,
        "route_after": ["A", "C", "D", "F"],
        "cost_after": 30,
        "comparison": "supérieur",
    }


@pytest.mark.parametrize("seed", range(270100, 270150))
def test_v25_two_outage_oracle_and_surviving_route(seed: int) -> None:
    facts = _build(seed).to_dict()
    first = frozenset(facts["closed_edge"])
    second = frozenset(facts["closed_edge_second"])
    assert first != second
    assert "A" not in second
    assert facts["closed_edge_second"] == facts["expected"]["1f"]["route_after"][-2:]
    surviving = [
        edge
        for edge in facts["graph"]["edges"]
        if frozenset(edge[:2]) not in {first, second}
    ]
    path, cost = _enumerated_minimum(surviving)
    assert facts["expected"]["1g"]["route_after"] == path
    assert facts["expected"]["1g"]["cost_after"] == cost
    assert cost >= facts["expected"]["1f"]["cost_after"]


def test_v25_equal_cost_second_outage_is_not_mislabelled_as_increase() -> None:
    facts = _build(270102).to_dict()

    assert facts["expected"]["1f"]["cost_after"] == 32
    assert facts["expected"]["1g"]["cost_after"] == 32
    assert facts["expected"]["1g"]["comparison"] == "égal"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["closed_edge_second"].__setitem__(0, "A"),
        lambda data: data["expected"]["1g"].__setitem__("cost_after", 1),
        lambda data: data["expected"]["1g"].__setitem__("comparison", "égal"),
        lambda data: data.__setitem__("seed", 270101),
    ],
)
def test_v25_rejects_mutated_second_outage_facts(mutate) -> None:
    altered = deepcopy(_build(270100).to_dict())
    mutate(altered)

    with pytest.raises(ValueError):
        _module().GraphTwoOutageContract.from_dict(altered)


def test_v25_rejects_dijkstra_disagreement_with_independent_oracle() -> None:
    module = _module()
    real = module._dijkstra_steps

    def wrong_route(adjacency):
        steps, route = real(adjacency)
        return steps, {**route, "weight": route["weight"] + 1}

    with (
        patch.object(module, "_dijkstra_steps", side_effect=wrong_route),
        pytest.raises(ValueError, match="independent"),
    ):
        _build(270100)
