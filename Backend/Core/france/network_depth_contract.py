"""Version-two app-owned facts for the French written network exercise.

This module is deliberately separate from the v14 contract: saved v14 papers
must continue to replay against their original facts and digest.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from hashlib import sha256

_NODES = ("Central", "R1", "R2", "R3", "Station")
_EDGES = (
    ("Central", "R1", 2),
    ("Central", "R2", 5),
    ("R1", "R3", 3),
    ("R1", "R2", 4),
    ("R2", "R3", 2),
    ("R2", "Station", 10),
    ("R3", "Station", 4),
)
_PROCESSES = {
    "P1": {"holds": "A", "waits_for": "B"},
    "P2": {"holds": "B", "waits_for": "A"},
    "recovery": "abort_P2_release_B",
    "prevention_order": ["A", "B"],
}
_SECURITY = {
    "receiver_public_key_authenticated": True,
    "sender_signature": False,
    "session_key_encrypted_for_receiver": True,
    "observer": "passive",
}


def _route(links: list[list]) -> dict:
    """Recompute an auditable Dijkstra trace; reject ambiguous best routes."""
    neighbours: dict[str, list[tuple[str, int]]] = {node: [] for node in _NODES}
    for left, right, cost in links:
        neighbours[left].append((right, cost))
        neighbours[right].append((left, cost))

    distances: dict[str, int | None] = dict.fromkeys(_NODES)
    distances["Central"] = 0
    previous: dict[str, str] = {}
    path_counts = {node: 0 for node in _NODES}
    path_counts["Central"] = 1
    unsettled = set(_NODES)
    settled_order: list[str] = []
    trace: list[dict] = []
    while unsettled:
        reachable = [node for node in unsettled if distances[node] is not None]
        if not reachable:
            raise ValueError("Disconnected network")
        node = min(reachable, key=lambda item: (distances[item], item))
        unsettled.remove(node)
        settled_order.append(node)
        distance = distances[node]
        assert distance is not None
        for neighbour, cost in sorted(neighbours[node]):
            if neighbour not in unsettled:
                continue
            candidate = distance + cost
            current = distances[neighbour]
            if current is None or candidate < current:
                distances[neighbour] = candidate
                previous[neighbour] = node
                path_counts[neighbour] = path_counts[node]
            elif candidate == current:
                path_counts[neighbour] += path_counts[node]
        trace.append(
            {
                "settled": node,
                "distance": distance,
                "tentative": distances.copy(),
            }
        )

    if path_counts["Station"] != 1:
        raise ValueError("Ambiguous shortest route")
    path = ["Station"]
    while path[-1] != "Central":
        path.append(previous[path[-1]])
    path.reverse()
    return {
        "settled_order": settled_order,
        "trace": trace,
        "path": path,
        "cost": distances["Station"],
    }


def _facts(seed: int) -> dict:
    offset = random.Random(f"french-nsi-network-depth-v2:{seed}").choice(range(4))
    links = [[left, right, cost + offset] for left, right, cost in _EDGES]
    change = {"link": ["R1", "R3"], "new_cost": 12 + offset}
    changed = [edge.copy() for edge in links]
    changed[2][2] = change["new_cost"]
    before = _route(links)
    after = _route(changed)
    if before["path"] == after["path"]:
        raise ValueError("Link change did not change the best route")
    return {
        "version": 2,
        "seed": seed,
        "exercise_id": "3",
        "task_ids": [f"3{letter}" for letter in "abcdef"],
        "profile_offset": offset,
        "links": links,
        "change": change,
        "processes": _PROCESSES,
        "security": _SECURITY,
        "expected": {"before": before, "after": after},
    }


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class NetworkDepthContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> NetworkDepthContract:
        if not isinstance(data, dict):
            raise ValueError("Invalid network depth contract")
        seed = data.get("seed")
        if type(seed) is not int or type(data.get("version")) is not int:
            raise ValueError("Invalid network depth identity")
        if _canonical(data) != _canonical(_facts(seed)):
            raise ValueError("Network depth facts or derived results differ from application contract")
        return cls(_canonical(data))


def build_network_depth_contract(seed: int) -> NetworkDepthContract:
    if type(seed) is not int:
        raise ValueError("Unsupported network depth seed")
    return NetworkDepthContract.from_dict(_facts(seed))
