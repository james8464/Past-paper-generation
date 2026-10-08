"""Immutable application-owned facts for the V18 NSI written network case.

The six-question V15-V17 contract remains untouched so saved packages replay.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from Backend.Core.france.network_depth_contract import build_network_depth_contract

_NODES = ("Central", "R1", "R2", "R3", "Station")
_PROCESS_SCHEDULE = (
    {"step": "t0", "P1": "détient A", "P2": "détient B"},
    {"step": "t1", "P1": "attend B", "P2": "attend A"},
    {"step": "t2", "P1": "obtient B", "P2": "arrêté, libère B"},
    {"step": "t3", "P1": "termine, libère A et B", "P2": "redémarre, prend A puis B"},
)
_SECURITY_MESSAGES = (
    {"step": 1, "sender": "Station", "content": "clé publique authentifiée"},
    {"step": 2, "sender": "Capteur", "content": "clé de session chiffrée pour Station"},
    {
        "step": 3,
        "sender": "Capteur",
        "content": "mesures chiffrées avec la clé de session",
    },
)


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _predecessors(links: list[list], route: dict) -> dict[str, str | None]:
    distances = route["trace"][-1]["tentative"]
    result: dict[str, str | None] = {"Central": None}
    for node in _NODES[1:]:
        candidates = [
            left if right == node else right
            for left, right, weight in links
            if node in (left, right)
            and distances[left if right == node else right] + weight == distances[node]
        ]
        if len(candidates) != 1:
            raise ValueError("Network reasoning predecessor is ambiguous")
        result[node] = candidates[0]
    return result


def _route_with_working(links: list[list], route: dict) -> dict:
    return {
        **route,
        "predecessors": _predecessors(links, route),
        "unique": True,
    }


def _facts(seed: int) -> dict:
    old = build_network_depth_contract(seed).to_dict()
    links = old["links"]
    changed = [edge.copy() for edge in links]
    changed[2][2] = old["change"]["new_cost"]
    processes = old["processes"]
    holds = {
        process: record["holds"]
        for process, record in processes.items()
        if process in {"P1", "P2"}
    }
    wait_for = [
        [process, owner]
        for process in ("P1", "P2")
        for owner, resource in holds.items()
        if resource == processes[process]["waits_for"]
    ]
    security = old["security"]
    return {
        "version": 3,
        "seed": seed,
        "exercise_id": "3",
        "task_ids": [f"3{letter}" for letter in "abcdefghijkl"],
        "profile_offset": old["profile_offset"],
        "links": links,
        "change": old["change"],
        "processes": processes,
        "process_schedule": list(_PROCESS_SCHEDULE),
        "security": security,
        "security_messages": list(_SECURITY_MESSAGES),
        "expected": {
            "before": _route_with_working(links, old["expected"]["before"]),
            "after": _route_with_working(changed, old["expected"]["after"]),
            "wait_for": wait_for,
            "recovery_order": ["P2", "P1", "P2"],
            "threats": {
                "passive_reads_message": False,
                "station_authenticated": security["receiver_public_key_authenticated"],
                "sender_authenticated": security["sender_signature"],
                "metadata_visible": True,
                "compromised_endpoint_protected": False,
            },
        },
    }


@dataclass(frozen=True)
class NetworkReasoningContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> NetworkReasoningContract:
        if not isinstance(data, dict):
            raise ValueError("Invalid network reasoning contract")
        seed = data.get("seed")
        if type(seed) is not int or type(data.get("version")) is not int:
            raise ValueError("Invalid network reasoning identity")
        if _canonical(data) != _canonical(_facts(seed)):
            raise ValueError("Network reasoning facts differ from application contract")
        return cls(_canonical(data))


def build_network_reasoning_contract(seed: int) -> NetworkReasoningContract:
    if type(seed) is not int:
        raise ValueError("Unsupported network reasoning seed")
    return NetworkReasoningContract.from_dict(_facts(seed))
