"""Immutable V22 graph route traces; earlier French packages remain unchanged."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from Backend.Core.france.graph_tree_depth_contract import (
    _adjacency,
    _dijkstra_steps,
    build_graph_tree_depth_contract,
)


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _facts(seed: int) -> dict:
    if type(seed) is not int:
        raise ValueError("Unsupported graph route-trace seed")
    data = build_graph_tree_depth_contract(seed).to_dict()
    before = data["expected"]["1d"]
    closed_edge = before["path"][:2]
    surviving_edges = [
        edge
        for edge in data["graph"]["edges"]
        if frozenset(edge[:2]) != frozenset(closed_edge)
    ]
    if len(surviving_edges) != len(data["graph"]["edges"]) - 1:
        raise ValueError("Closed route edge is not unique")
    baseline_steps, baseline_route = _dijkstra_steps(_adjacency(data["graph"]))
    outage_steps, outage_route = _dijkstra_steps(
        _adjacency({"edges": surviving_edges})
    )
    if (
        baseline_route != before
        or baseline_steps != data["expected"]["1c"]["steps"]
        or baseline_steps[0] == outage_steps[0]
        or outage_route["path"] == before["path"]
        or outage_route["weight"] < before["weight"]
    ):
        raise ValueError("Route trace disagrees with the closed-link case")
    old_error = data["expected"]["1f"]
    old_states = data["expected"]["1e"]["states"]
    data["version"] = 5
    data["closed_edge"] = closed_edge
    data["expected"]["1e"] = old_error
    data["expected"]["1f"] = {
        "states": old_states,
        "order": data["expected"]["1g"]["order"],
    }
    data["expected"]["1g"] = {
        "steps": outage_steps,
        "route_before": before["path"],
        "cost_before": before["weight"],
        "route_after": outage_route["path"],
        "cost_after": outage_route["weight"],
        "comparison": (
            "égal" if outage_route["weight"] == before["weight"] else "supérieur"
        ),
    }
    return data


@dataclass(frozen=True)
class GraphRouteTraceContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> GraphRouteTraceContract:
        if not isinstance(data, dict) or type(data.get("seed")) is not int:
            raise ValueError("Invalid graph route-trace contract")
        canonical = _facts(data["seed"])
        if _canonical(data) != _canonical(canonical):
            raise ValueError("Graph route-trace facts differ from application contract")
        return cls(_canonical(canonical))


def build_graph_route_trace_contract(seed: int) -> GraphRouteTraceContract:
    return GraphRouteTraceContract.from_dict(_facts(seed))
