# V26 adds an independently checkable second deadline to the incident.

from copy import deepcopy

import pytest


def _contract(seed=270100):
    from Backend.Core.france.network_incident_timeline_contract import (
        build_network_incident_timeline_contract,
    )

    return build_network_incident_timeline_contract(seed)


def test_v26_timeline_has_causal_event_times_and_distinct_deadlines():
    facts = _contract().to_dict()
    assert facts["version"] == 5
    assert facts["expected"]["packet"]["after_arrival"] == 20
    assert facts["packet"]["deadline"] == 19
    assert facts["timeline"] == {
        "stop_and_release_minutes": 2,
        "processing_minutes": 4,
        "secure_report_minutes": 2,
        "report_deadline": 29,
    }
    assert facts["expected"]["timeline"] == {
        "packet_arrival": 20,
        "resource_released": 22,
        "packet_processed": 26,
        "report_delivered": 28,
        "report_margin": 1,
        "report_on_time": True,
    }
    assert facts["expected"]["packet"]["after_on_time"] is False


@pytest.mark.parametrize("seed", range(270100, 270116))
def test_v26_timeline_is_deterministic_and_keeps_old_incident(seed):
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )

    contract = _contract(seed)
    facts = contract.to_dict()
    old = build_network_incident_contract(seed).to_dict()
    assert contract.digest == _contract(seed).digest
    for field in ("links", "change", "packet", "processes", "security"):
        assert facts[field] == old[field]
    events = facts["expected"]["timeline"]
    assert events["resource_released"] == events["packet_arrival"] + 2
    assert events["packet_processed"] == events["resource_released"] + 4
    assert events["report_delivered"] == events["packet_processed"] + 2
    assert events["report_margin"] == 1


@pytest.mark.parametrize("field", ["duration", "deadline", "event", "old_route"])
def test_v26_deserialization_rejects_edited_timeline_or_inherited_fact(field):
    from Backend.Core.france.network_incident_timeline_contract import (
        NetworkIncidentTimelineContract,
    )

    facts = deepcopy(_contract().to_dict())
    if field == "duration":
        facts["timeline"]["processing_minutes"] += 1
    elif field == "deadline":
        facts["timeline"]["report_deadline"] += 1
    elif field == "event":
        facts["expected"]["timeline"]["report_delivered"] -= 1
    else:
        facts["expected"]["after"]["cost"] += 1
    with pytest.raises(ValueError, match=r"timeline|incident"):
        NetworkIncidentTimelineContract.from_dict(facts)


def test_v26_verification_checks_derived_timeline_not_just_declared_fact():
    from Backend.Core.france.verification import verify_contract

    facts = _contract().to_dict()
    verification = {
        "kind": "network_incident_timeline_contract",
        "contract": facts,
        "task_id": "3g",
        "expected": facts["expected"],
    }
    assert verify_contract(verification)["state"] == "passed"
    changed = deepcopy(verification)
    changed["expected"]["timeline"]["report_delivered"] -= 1
    assert verify_contract(changed)["state"] != "passed"
