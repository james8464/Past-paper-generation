"""Immutable app-owned facts for the V23 written network incident.

V18 and earlier network contracts remain unchanged for package replay.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from Backend.Core.france.network_reasoning_contract import (
    build_network_reasoning_contract,
)


def _canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _independent_shortest_path(
    links: list[list], source: str, target: str
) -> tuple[list[str], int]:
    """Enumerate simple paths, independently of the Dijkstra trace used in V18."""
    adjacent: dict[str, list[tuple[str, int]]] = {}
    for left, right, cost in links:
        adjacent.setdefault(left, []).append((right, cost))
        adjacent.setdefault(right, []).append((left, cost))
    paths: list[tuple[int, list[str]]] = []

    def walk(node: str, route: list[str], cost: int) -> None:
        if node == target:
            paths.append((cost, route))
            return
        for neighbour, weight in adjacent[node]:
            if neighbour not in route:
                walk(neighbour, [*route, neighbour], cost + weight)

    walk(source, [source], 0)
    if not paths:
        raise ValueError("Network incident route is disconnected")
    paths.sort(key=lambda item: (item[0], item[1]))
    if len(paths) > 1 and paths[0][0] == paths[1][0]:
        raise ValueError("Network incident route is ambiguous")
    cost, route = paths[0]
    return route, cost


def _facts(seed: int) -> dict:
    old = build_network_reasoning_contract(seed).to_dict()
    links = old["links"]
    changed = [edge.copy() for edge in links]
    changed[2][2] = old["change"]["new_cost"]
    before_path, before_cost = _independent_shortest_path(links, "Central", "Station")
    after_path, after_cost = _independent_shortest_path(changed, "Central", "Station")
    if (before_path, before_cost) != (
        old["expected"]["before"]["path"],
        old["expected"]["before"]["cost"],
    ):
        raise ValueError("Network incident baseline oracle disagrees")
    if (after_path, after_cost) != (
        old["expected"]["after"]["path"],
        old["expected"]["after"]["cost"],
    ):
        raise ValueError("Network incident changed oracle disagrees")
    deadline = before_cost + 1
    if after_cost <= deadline:
        raise ValueError("Network incident has no delayed packet")
    return {
        "version": 4,
        "seed": seed,
        "exercise_id": "3",
        "task_ids": [f"3{letter}" for letter in "abcdefghijkl"],
        "profile_offset": old["profile_offset"],
        "links": links,
        "change": old["change"],
        "packet": {
            "id": "M-27",
            "sender": "Central",
            "receiver": "Station",
            "emission": 0,
            "deadline": deadline,
            "cost_unit": "minute",
            "payload": "mesures",
        },
        "processes": {
            "at": after_cost,
            "P1": {"holds": "A", "waits_for": "B", "role": "ingestion du paquet M-27"},
            "P2": {"holds": "B", "waits_for": "A", "role": "maintenance"},
            "queue_state": "M-27 en attente de traitement",
            "recovery": [
                "arrêter P2 et libérer B",
                "P1 prend B, traite M-27, puis libère A et B",
                "redémarrer P2, qui prend A puis B",
            ],
        },
        "security": {
            "receiver_public_key_authenticated": True,
            "sender_signature": False,
            "passive_observer": True,
            "primitives_secure": True,
            "messages": [
                ["M1", "Station", "compte rendu M-27 chiffré avec la clé de session"],
                ["M2", "Central", "clé publique authentifiée de Central"],
                ["M3", "Station", "clé de session chiffrée pour Central"],
            ],
        },
        "working_surfaces": {
            "route_nodes": ["Central", "R1", "R2", "R3", "Station"],
            "recovery_steps": [
                "arrivée",
                "après arrêt P2",
                "après fin P1",
                "après redémarrage",
            ],
            "threat_scenarios": [
                "Observateur passif",
                "Authentification",
                "Métadonnées",
                "Terminal compromis",
            ],
        },
        "expected": {
            "before": old["expected"]["before"],
            "after": old["expected"]["after"],
            "packet": {
                "before_arrival": before_cost,
                "after_arrival": after_cost,
                "late_by": after_cost - deadline,
                "before_on_time": before_cost <= deadline,
                "after_on_time": after_cost <= deadline,
            },
            "wait_for": [["P1", "P2"], ["P2", "P1"]],
            "recovery_order": ["P2", "P1", "P2"],
            "packet_after_recovery": "traité",
            "threats": {
                "passive_reads_message": False,
                "central_authenticated": True,
                "sender_authenticated": False,
                "metadata_visible": True,
                "compromised_endpoint_protected": False,
            },
        },
    }


@dataclass(frozen=True)
class NetworkIncidentContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> NetworkIncidentContract:
        if not isinstance(data, dict):
            raise ValueError("Invalid network incident contract")
        seed = data.get("seed")
        if type(seed) is not int or type(data.get("version")) is not int:
            raise ValueError("Invalid network incident identity")
        if _canonical(data) != _canonical(_facts(seed)):
            raise ValueError("Network incident facts differ from application contract")
        return cls(_canonical(data))


def build_network_incident_contract(seed: int) -> NetworkIncidentContract:
    if type(seed) is not int:
        raise ValueError("Unsupported network incident seed")
    return NetworkIncidentContract.from_dict(_facts(seed))
