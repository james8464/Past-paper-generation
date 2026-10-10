"""Immutable V20 app-owned graph-resilience facts; V3 packages stay unchanged."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.graph_tree_depth_contract import (
    _adjacency,
    _dijkstra_steps,
    build_graph_tree_depth_contract,
)


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _facts(seed: int) -> dict:
    if type(seed) is not int:
        raise ValueError("Unsupported graph resilience seed")
    data = build_graph_tree_depth_contract(seed).to_dict()
    route_before = data["expected"]["1d"]["path"]
    edges_on_route = list(pairwise(route_before))
    closed_edge = edges_on_route[len(route_before) // 2 - 1]
    surviving_edges = [
        edge
        for edge in data["graph"]["edges"]
        if frozenset(edge[:2]) != frozenset(closed_edge)
    ]
    if len(surviving_edges) != len(data["graph"]["edges"]) - 1:
        raise ValueError("Closed edge is not unique")
    _steps, shortest_after = _dijkstra_steps(_adjacency({"edges": surviving_edges}))
    if shortest_after["path"] == route_before:
        raise ValueError("Closed edge did not alter route")
    cost_before = data["expected"]["1d"]["weight"]
    cost_after = shortest_after["weight"]
    if cost_after < cost_before:
        raise ValueError("Closing a link cannot improve the minimum cost")

    data["version"] = 4
    data["closed_edge"] = list(closed_edge)
    data["expected"]["1e"]["order"] = data["expected"]["1g"]["order"]
    data["expected"]["1g"] = {
        "route_before": route_before,
        "cost_before": cost_before,
        "route_after": shortest_after["path"],
        "cost_after": cost_after,
        "comparison": "égal" if cost_after == cost_before else "supérieur",
    }
    return data


@dataclass(frozen=True)
class GraphResilienceContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @property
    def closed_edge(self) -> list[str]:
        return self.to_dict()["closed_edge"]

    @property
    def route_before(self) -> list[str]:
        return self.to_dict()["expected"]["1g"]["route_before"]

    @property
    def route_after(self) -> list[str]:
        return self.to_dict()["expected"]["1g"]["route_after"]

    @property
    def cost_before(self) -> int:
        return self.to_dict()["expected"]["1g"]["cost_before"]

    @property
    def cost_after(self) -> int:
        return self.to_dict()["expected"]["1g"]["cost_after"]

    @property
    def bfs_states(self) -> list[dict]:
        return self.to_dict()["expected"]["1e"]["states"]

    @classmethod
    def from_dict(cls, data: dict) -> GraphResilienceContract:
        if not isinstance(data, dict) or type(data.get("seed")) is not int:
            raise ValueError("Invalid graph resilience contract")
        canonical = _facts(data["seed"])
        if _canonical(data) != _canonical(canonical):
            raise ValueError("Graph resilience facts differ from application contract")
        return cls(_canonical(canonical))


def build_graph_resilience_contract(seed: int) -> GraphResilienceContract:
    return GraphResilienceContract.from_dict(_facts(seed))
