# The V26 candidate surface must demand the new causal timing work.

from copy import deepcopy

import pytest

from Backend.Core.france.network_incident_timeline_contract import (
    build_network_incident_timeline_contract,
)
from Backend.Core.france.network_incident_timeline_prose import (
    render_network_incident_timeline_candidate,
    validate_network_incident_timeline_exercise,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v25


def _selection():
    ids = [f"3{letter}" for letter in "abcdefghijkl"]
    return {
        "scene_id": "station",
        "question_forms": {q: f"{q}-q1" for q in ids},
        "rubric_forms": {q: f"{q}-r1" for q in ids},
    }


def _specs(seed=270100):
    specs = deepcopy(_tasks_for_seed_v25(seed)[2]["question_blueprint"])
    specs[6].update(points="0.75", estimated_minutes=8, difficulty=4)
    specs[9].update(points="0.25", estimated_minutes=3)
    return specs


def test_v26_candidate_requires_computed_recovery_and_report_times():
    contract = build_network_incident_timeline_contract(270100)
    raw = render_network_incident_timeline_candidate(contract, _selection(), _specs())
    assert raw["target_points"] == _tasks_for_seed_v25(270100)[2]["technical_points"]
    assert len(raw["questions"]) == 12
    assert len(raw["materials"]) == 6
    timeline = next(item for item in raw["materials"] if item["id"] == "packet_card")
    assert "à compléter" in str(timeline["rows"])
    assert "22" not in str(timeline["rows"])
    assert "26" not in str(timeline["rows"])
    assert "28" not in str(timeline["rows"])
    question = {item["id"]: item for item in raw["questions"]}
    assert question["3g"]["points"] == "0.75"
    assert question["3j"]["points"] == "0.25"
    assert "packet_card" in question["3g"]["material_ids"]
    assert "packet_card" in question["3l"]["material_ids"]
    assert "t=22" in question["3g"]["answer"]
    assert "t=26" in question["3g"]["answer"]
    assert "t=28" in question["3g"]["answer"]
    assert "t=29" in question["3l"]["answer"]
    assert all(
        item["verification"]["kind"] == "network_incident_timeline_contract"
        for item in raw["questions"]
    )
    validate_network_incident_timeline_exercise(
        contract, NSIExercise.model_validate(raw), _specs()
    )


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
@pytest.mark.parametrize("form", [1, 2])
def test_v26_all_credit_profiles_and_wording_forms_validate(seed, form):
    contract = build_network_incident_timeline_contract(seed)
    selection = _selection()
    selection["scene_id"] = "observatoire" if form == 2 else "station"
    selection["question_forms"] = {
        q: f"{q}-q{form}" for q in selection["question_forms"]
    }
    selection["rubric_forms"] = {q: f"{q}-r{form}" for q in selection["rubric_forms"]}
    raw = render_network_incident_timeline_candidate(contract, selection, _specs(seed))
    assert sum(float(item["points"]) for item in raw["questions"]) == float(
        raw["target_points"]
    )
    assert all(
        sum(float(mark["points"]) for mark in item["marking"]) == float(item["points"])
        for item in raw["questions"]
    )
    validate_network_incident_timeline_exercise(
        contract, NSIExercise.model_validate(raw), _specs(seed)
    )


@pytest.mark.parametrize("field", ["context", "table", "answer", "credit"])
def test_v26_rejects_tampered_candidate_timeline(field):
    contract = build_network_incident_timeline_contract(270100)
    raw = render_network_incident_timeline_candidate(contract, _selection(), _specs())
    if field == "context":
        raw["context"] = raw["context"].replace("9 minutes", "8 minutes")
    elif field == "table":
        next(item for item in raw["materials"] if item["id"] == "packet_card")["rows"][
            3
        ][1] = "3"
    elif field == "answer":
        raw["questions"][6]["answer"] = "t=23"
    else:
        raw["questions"][6]["points"] = "0.5"
    with pytest.raises(ValueError):
        validate_network_incident_timeline_exercise(
            contract, NSIExercise.model_validate(raw), _specs()
        )
