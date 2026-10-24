"""V26 finite selection with a separately bound timed candidate.

The model selects only inherited scene/wording IDs. It never supplies timing
facts or answers; the V26 layer derives those from its immutable contract.
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from Backend.Core.france.network_incident_authoring import (
    author_network_incident_selection,
    replay_network_incident_selection,
)
from Backend.Core.france.network_incident_contract import (
    build_network_incident_contract,
)
from Backend.Core.france.network_incident_timeline_contract import (
    NetworkIncidentTimelineContract,
)
from Backend.Core.france.network_incident_timeline_prose import (
    _legacy_specs,
    render_network_incident_timeline_candidate,
)


def _digest(value: dict) -> str:
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _legacy_task(task: dict) -> dict:
    legacy = deepcopy(task)
    legacy["question_blueprint"] = _legacy_specs(task["question_blueprint"])
    return legacy


def _wrap(
    task: dict,
    contract: NetworkIncidentTimelineContract,
    base_evidence: dict,
    *,
    revision: int = 1,
) -> tuple[dict, dict]:
    response = base_evidence["accepted"]["response"]
    raw = render_network_incident_timeline_candidate(
        contract,
        response,
        task["question_blueprint"],
        revision=revision,
    )
    return raw, {
        "version": "v27" if revision == 2 else "v26",
        "contract_sha256": contract.digest,
        "candidate_sha256": _digest(raw),
        "base_selection": base_evidence,
    }


def author_network_incident_timeline_selection(
    client,
    task: dict,
    contract: NetworkIncidentTimelineContract,
    references: list[dict],
    path: Path,
    *,
    run_identity: dict,
) -> tuple[dict, dict]:
    base_contract = build_network_incident_contract(contract.to_dict()["seed"])
    _, base_evidence = author_network_incident_selection(
        client,
        _legacy_task(task),
        base_contract,
        references,
        path,
        run_identity=run_identity,
    )
    return _wrap(
        task,
        contract,
        base_evidence,
        revision=2
        if run_identity.get("prompt_version")
        in {
            "fr-nsi-written-2027-v27",
            "fr-nsi-written-2027-v28",
            "fr-nsi-written-2027-v29",
        }
        else 1,
    )


def replay_network_incident_timeline_selection(
    task: dict,
    contract: NetworkIncidentTimelineContract,
    references: list[dict],
    evidence: dict,
    *,
    run_identity: dict,
) -> dict:
    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {"version", "contract_sha256", "candidate_sha256", "base_selection"}
        or evidence["version"]
        != (
            "v27"
            if run_identity.get("prompt_version")
            in {
                "fr-nsi-written-2027-v27",
                "fr-nsi-written-2027-v28",
                "fr-nsi-written-2027-v29",
            }
            else "v26"
        )
        or evidence["contract_sha256"] != contract.digest
    ):
        raise ValueError("Network incident timeline selection identity mismatch")
    base_contract = build_network_incident_contract(contract.to_dict()["seed"])
    replay_network_incident_selection(
        _legacy_task(task),
        base_contract,
        references,
        evidence["base_selection"],
        run_identity=run_identity,
    )
    raw, canonical = _wrap(
        task,
        contract,
        evidence["base_selection"],
        revision=2
        if run_identity.get("prompt_version")
        in {
            "fr-nsi-written-2027-v27",
            "fr-nsi-written-2027-v28",
            "fr-nsi-written-2027-v29",
        }
        else 1,
    )
    if canonical != evidence:
        raise ValueError("Network incident timeline candidate hash mismatch")
    return raw
