# Immutable V26 timing facts layered over the replayable V23 incident
#
# the second deadline concerns the encrypted report, not arrival of M-27. A
# late packet can still produce an on-time report after a successful recovery

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from Backend.Core.france.network_incident_contract import (
    build_network_incident_contract,
)


def _canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _facts(seed: int) -> dict:
    facts = build_network_incident_contract(seed).to_dict()
    arrival = facts["expected"]["packet"]["after_arrival"]
    release = arrival + 2
    processed = release + 4
    delivered = processed + 2
    due = arrival + 9
    facts["version"] = 5
    facts["timeline"] = {
        "stop_and_release_minutes": 2,
        "processing_minutes": 4,
        "secure_report_minutes": 2,
        "report_deadline": due,
    }
    facts["expected"]["timeline"] = {
        "packet_arrival": arrival,
        "resource_released": release,
        "packet_processed": processed,
        "report_delivered": delivered,
        "report_margin": due - delivered,
        "report_on_time": delivered <= due,
    }
    return facts


@dataclass(frozen=True)
class NetworkIncidentTimelineContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> NetworkIncidentTimelineContract:
        if not isinstance(data, dict):
            raise ValueError("Invalid network incident timeline contract")
        seed = data.get("seed")
        if type(seed) is not int or type(data.get("version")) is not int:
            raise ValueError("Invalid network incident timeline identity")
        if _canonical(data) != _canonical(_facts(seed)):
            raise ValueError(
                "Network incident timeline facts differ from application contract"
            )
        return cls(_canonical(data))


def build_network_incident_timeline_contract(
    seed: int,
) -> NetworkIncidentTimelineContract:
    if type(seed) is not int:
        raise ValueError("Unsupported network incident timeline seed")
    return NetworkIncidentTimelineContract.from_dict(_facts(seed))
