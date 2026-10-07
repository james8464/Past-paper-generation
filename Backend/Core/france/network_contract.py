"""Application-owned facts for the French NSI written network exercise.

The model cannot supply, change or infer these routing, process or security facts.
The four printed link costs alone determine every routing answer.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from hashlib import sha256

_TASK_IDS = [f"3{letter}" for letter in "abcdef"]
_PROFILES = (
    (4, 5, 6, 6, 10),
    (3, 6, 6, 7, 12),
    (5, 4, 6, 5, 9),
    (4, 6, 7, 6, 12),
)
_EDGES = (
    ("Central", "R1"),
    ("R1", "Station"),
    ("Central", "R2"),
    ("R2", "Station"),
)
_PROCESSES = [["B", "A", "B"], ["C", "B", "A"]]
_SECURITY = {
    "pre_shared_secret": False,
    "receiver_public_key_authenticated": True,
    "observer": "passive",
}


def _facts(seed: int) -> tuple[list[list], dict]:
    values = random.Random(f"french-nsi-network-v1:{seed}").choice(_PROFILES)
    links = [
        [left, right, cost]
        for (left, right), cost in zip(_EDGES, values[:4], strict=True)
    ]
    return links, {"link": ["R1", "Station"], "new_cost": values[4]}


def _paths(links: list[list]) -> dict:
    """Enumerate simple paths rather than trusting a stored shortest-path answer."""
    adjacent: dict[str, list[tuple[str, int]]] = {}
    for left, right, cost in links:
        adjacent.setdefault(left, []).append((right, cost))
        adjacent.setdefault(right, []).append((left, cost))
    pending = [("Central", ["Central"], 0)]
    routes = []
    while pending:
        node, path, cost = pending.pop()
        if node == "Station":
            routes.append((cost, path))
            continue
        for neighbour, weight in adjacent[node]:
            if neighbour not in path:
                pending.append((neighbour, [*path, neighbour], cost + weight))
    if len(routes) != 2:
        raise ValueError("Network must have exactly two simple routes")
    routes.sort(key=lambda route: route[0])
    if routes[0][0] == routes[1][0]:
        raise ValueError("Ambiguous shortest route")
    return {
        "path": routes[0][1],
        "cost": routes[0][0],
        "other_cost": routes[1][0],
    }


def _expected(links: list[list], change: dict) -> dict:
    before = _paths(links)
    changed = [row.copy() for row in links]
    changed[1][2] = change["new_cost"]
    after = _paths(changed)
    if before["path"] == after["path"]:
        raise ValueError("Link change does not change preferred route")
    return {"before": before, "after": after}


@dataclass(frozen=True)
class NetworkContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> NetworkContract:
        if not isinstance(data, dict) or set(data) != {
            "version", "seed", "exercise_id", "task_ids", "links", "change",
            "processes", "security", "expected",
        }:
            raise ValueError("Invalid network contract fields")
        seed = data["seed"]
        if (
            type(data["version"]) is not int
            or data["version"] != 1
            or type(seed) is not int
            or data["exercise_id"] != "3"
            or data["task_ids"] != _TASK_IDS
            or data["processes"] != _PROCESSES
            or data["security"] != _SECURITY
        ):
            raise ValueError("Invalid network contract identity or premises")
        links, change = _facts(seed)
        if data["links"] != links or data["change"] != change:
            raise ValueError("Network facts differ from seeded application contract")
        if data["expected"] != _expected(links, change):
            raise ValueError("Network route result mismatch")
        return cls(
            json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )


def build_network_contract(seed: int, exercise_id: str = "3") -> NetworkContract:
    if type(seed) is not int or exercise_id != "3":
        raise ValueError("Unsupported network seed or exercise")
    links, change = _facts(seed)
    return NetworkContract.from_dict(
        {
            "version": 1,
            "seed": seed,
            "exercise_id": exercise_id,
            "task_ids": _TASK_IDS,
            "links": links,
            "change": change,
            "processes": _PROCESSES,
            "security": _SECURITY,
            "expected": _expected(links, change),
        }
    )
