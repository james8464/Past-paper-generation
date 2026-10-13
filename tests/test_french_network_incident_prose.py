"""The new case must print linked premises and award each requested step."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.pipeline import _tasks_for_seed_v22


def _selection():
    return {
        "scene_id": "station",
        "question_forms": {f"3{x}": f"3{x}-q1" for x in "abcdefghijkl"},
        "rubric_forms": {f"3{x}": f"3{x}-r1" for x in "abcdefghijkl"},
    }


@pytest.mark.parametrize(
    "seed,total,deadline", [(270100, "5.5", 19), (270101, "6", 19), (270102, "6.5", 10)]
)
def test_v23_candidate_has_staged_evidence_causal_answers_exact_credit(
    seed, total, deadline
):
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )
    from Backend.Core.france.network_incident_prose import (
        render_network_incident_candidate,
    )
    from Backend.Core.france.nsi import NSIExercise

    task = _tasks_for_seed_v22(seed)[2]
    exercise = NSIExercise.model_validate(
        render_network_incident_candidate(
            build_network_incident_contract(seed),
            _selection(),
            task["question_blueprint"],
        )
    )
    assert exercise.credit == Decimal(total)
    assert exercise.minutes == 70
    assert [q.id for q in exercise.questions] == [f"3{x}" for x in "abcdefghijkl"]
    assert sum((Decimal(q.points) for q in exercise.questions), Decimal()) == Decimal(
        total
    )
    assert sum(q.estimated_minutes for q in exercise.questions) == 70
    material_ids = {m.id for m in exercise.materials}
    assert {
        "links",
        "route_working",
        "packet_card",
        "process_initial",
        "message_cards",
        "threat_working",
    } == material_ids
    assert all(set(q.material_ids) <= material_ids for q in exercise.questions)
    assert all(
        sum(Decimal(m.points) for m in q.marking) == Decimal(q.points)
        for q in exercise.questions
    )
    assert str(deadline) in exercise.context
    assert str(deadline + 1) in exercise.questions[3].answer
    assert "retard" in exercise.questions[3].answer.lower()
    assert "paquet" in exercise.questions[7].answer.lower()
    assert "non authentifi" in exercise.questions[10].answer.lower()
    criteria_3k = " ".join(credit.criterion for credit in exercise.questions[10].marking)
    assert "Central authentifié" in criteria_3k
    assert "Station authentifiée" not in criteria_3k


def test_v23_route_calculation_and_low_credit_rubrics_cover_all_requested_steps():
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )
    from Backend.Core.france.network_incident_prose import (
        render_network_incident_candidate,
    )

    task = _tasks_for_seed_v22(270100)[2]
    exercise = render_network_incident_candidate(
        build_network_incident_contract(270100),
        _selection(),
        task["question_blueprint"],
    )
    questions = {item["id"]: item for item in exercise["questions"]}
    assert "5 + 6 + 7 = 18" in questions["3c"]["answer"]
    assert "retard" in " ".join(
        item["criterion"] for item in questions["3d"]["marking"]
    )
    assert "terminal" in " ".join(
        item["criterion"] for item in questions["3l"]["marking"]
    )


def test_v23_recovery_action_is_printed_as_premise_not_awarded_as_work():
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )
    from Backend.Core.france.network_incident_prose import (
        render_network_incident_candidate,
    )

    exercise = render_network_incident_candidate(
        build_network_incident_contract(270100),
        _selection(),
        _tasks_for_seed_v22(270100)[2]["question_blueprint"],
    )
    process = next(m for m in exercise["materials"] if m["id"] == "process_initial")
    printed = exercise["context"] + str(process["rows"])
    assert "P2 est arrêté" in printed and "libère B" in printed
    rubric = " ".join(item["criterion"] for item in exercise["questions"][6]["marking"])
    assert "l'arrêt de P2" not in rubric
    assert "traitement de M-27" in rubric


def test_v23_finite_selection_and_blueprint_tampering_fail_closed():
    from Backend.Core.france.network_incident_contract import (
        build_network_incident_contract,
    )
    from Backend.Core.france.network_incident_prose import (
        network_incident_selection_schema,
        render_network_incident_candidate,
        validate_network_incident_selection,
    )

    contract = build_network_incident_contract(270100)
    assert network_incident_selection_schema(contract)["additionalProperties"] is False
    for bad in (
        {**_selection(), "free_text": "une réponse"},
        {**_selection(), "scene_id": "unknown"},
        {
            **_selection(),
            "question_forms": {**_selection()["question_forms"], "3d": "free text"},
        },
    ):
        with pytest.raises(ValueError):
            validate_network_incident_selection(contract, bad)
    task_specs = deepcopy(_tasks_for_seed_v22(270100)[2]["question_blueprint"])
    task_specs[3]["points"] = "1"
    with pytest.raises(ValueError):
        render_network_incident_candidate(contract, _selection(), task_specs)
