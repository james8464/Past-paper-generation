"""The V20 outage is derived by trusted code and isolated from V3."""

from copy import deepcopy
from itertools import pairwise

import pytest

from Backend.Core.france.graph_resilience_contract import (
    GraphResilienceContract,
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_tree_depth_contract import (
    build_graph_tree_depth_contract,
)


def _path_cost(edges, path):
    weights = {frozenset((a, b)): weight for a, b, weight in edges}
    return sum(weights[frozenset(edge)] for edge in pairwise(path))


@pytest.mark.parametrize("seed", [0, 1, 27, 270100, 270101, 999999])
def test_v4_closes_middle_shortest_route_edge_and_recomputes(seed):
    old = build_graph_tree_depth_contract(seed).to_dict()
    case = build_graph_resilience_contract(seed).to_dict()
    before = old["expected"]["1d"]
    middle = list(pairwise(before["path"]))[len(before["path"]) // 2 - 1]

    assert case["version"] == 4
    assert case["graph"] == old["graph"]
    assert case["tree"] == old["tree"]
    assert case["closed_edge"] == list(middle)
    assert case["expected"]["1g"]["route_before"] == before["path"]
    assert case["expected"]["1g"]["cost_before"] == before["weight"]
    after = case["expected"]["1g"]["route_after"]
    edges_after = [
        edge
        for edge in case["graph"]["edges"]
        if frozenset(edge[:2]) != frozenset(middle)
    ]
    assert after[0] == "A" and after[-1] == "F"
    assert after != before["path"]
    assert all(frozenset(edge) != frozenset(middle) for edge in pairwise(after))
    assert _path_cost(edges_after, after) == case["expected"]["1g"]["cost_after"]
    assert case["expected"]["1e"]["states"] == old["expected"]["1e"]["states"]


def test_v4_handles_equal_and_higher_failure_costs():
    comparisons = {
        build_graph_resilience_contract(seed).to_dict()["expected"]["1g"]["comparison"]
        for seed in range(100)
    }
    assert comparisons == {"égal", "supérieur"}


def test_v4_digest_rejects_changed_facts_and_retains_v3():
    contract = build_graph_resilience_contract(270100)
    assert contract.digest == build_graph_resilience_contract(270100).digest
    assert contract.digest != build_graph_resilience_contract(270101).digest
    assert (
        GraphResilienceContract.from_dict(contract.to_dict()).digest == contract.digest
    )
    for mutation in (
        lambda data: data.__setitem__("seed", 270101),
        lambda data: data["graph"]["edges"][0].__setitem__(2, 999),
        lambda data: data["closed_edge"].reverse(),
        lambda data: data["expected"]["1g"]["route_after"].reverse(),
        lambda data: data["expected"]["1g"].__setitem__("cost_after", 999),
        lambda data: data["expected"]["1e"]["states"][0]["queue"].pop(),
        lambda data: data["tree"].__setitem__("root", 999),
        lambda data: data.__setitem__("search_code", "return True"),
    ):
        altered = deepcopy(contract.to_dict())
        mutation(altered)
        with pytest.raises(ValueError):
            GraphResilienceContract.from_dict(altered)
    assert build_graph_tree_depth_contract(270100).to_dict()["version"] == 3
