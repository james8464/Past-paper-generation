"""Immutable V25 two-outage graph facts; V22-V24 facts stay unchanged."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from Backend.Core.france.graph_route_trace_contract import _facts as _route_trace_facts
from Backend.Core.france.graph_route_trace_contract import _independent_shortest
from Backend.Core.france.graph_tree_depth_contract import _adjacency, _dijkstra_steps


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _facts(seed: int) -> dict:
    if type(seed) is not int:
        raise ValueError("Unsupported graph two-outage seed")
    data = _route_trace_facts(seed)
    first_outage = data["expected"]["1g"]
    second_edge = first_outage["route_after"][-2:]
    first_edge_key = frozenset(data["closed_edge"])
    second_edge_key = frozenset(second_edge)
    if first_edge_key == second_edge_key or "A" in second_edge_key:
        raise ValueError("Invalid second route outage")
    surviving = [
        edge
        for edge in data["graph"]["edges"]
        if frozenset(edge[:2]) not in {first_edge_key, second_edge_key}
    ]
    if len(surviving) != len(data["graph"]["edges"]) - 2:
        raise ValueError("Second route edge is not unique")
    _steps, second_route = _dijkstra_steps(_adjacency({"edges": surviving}))
    if second_route != _independent_shortest(surviving):
        raise ValueError("Two-outage route disagrees with independent shortest path")
    if second_route["weight"] < first_outage["cost_after"]:
        raise ValueError("Second closure cannot improve the minimum route")
    data["version"] = 6
    data["closed_edge_second"] = second_edge
    data["expected"]["1f"] = first_outage
    data["expected"]["1g"] = {
        "route_before": first_outage["route_after"],
        "cost_before": first_outage["cost_after"],
        "route_after": second_route["path"],
        "cost_after": second_route["weight"],
        "comparison": (
            "égal"
            if second_route["weight"] == first_outage["cost_after"]
            else "supérieur"
        ),
    }
    return data


@dataclass(frozen=True)
class GraphTwoOutageContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> GraphTwoOutageContract:
        if not isinstance(data, dict) or type(data.get("seed")) is not int:
            raise ValueError("Invalid graph two-outage contract")
        canonical = _facts(data["seed"])
        if _canonical(data) != _canonical(canonical):
            raise ValueError("Graph two-outage facts differ from application contract")
        return cls(_canonical(canonical))


def build_graph_two_outage_contract(seed: int) -> GraphTwoOutageContract:
    return GraphTwoOutageContract.from_dict(_facts(seed))
