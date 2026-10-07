"""Exercise 3 must expose every premise and use only finite app wording."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.network_contract import build_network_contract
from Backend.Core.france.network_prose import (
    network_selection_schema,
    render_network_candidate,
    validate_network_selection,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed


def _setup(seed=270100):
    contract = build_network_contract(seed)
    plans = _tasks_for_seed(seed)[2]["question_blueprint"]
    selection = {
        "scene_id": "campus",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }
    return contract, plans, selection


@pytest.mark.parametrize("seed,credit", [(270100, "5.5"), (270101, "6"), (270102, "6.5")])
def test_network_prints_all_route_process_and_security_facts(seed, credit):
    contract, plans, selection = _setup(seed)
    exercise = NSIExercise.model_validate(
        render_network_candidate(contract, selection, plans)
    )
    data = contract.to_dict()
    assert exercise.credit == Decimal(credit)
    assert exercise.minutes == 70
    assert [question.id for question in exercise.questions] == data["task_ids"]
    assert [material.id for material in exercise.materials] == ["links", "processes"]
    for left, right, cost in data["links"]:
        assert (left, right, str(cost)) in exercise.materials[0].rows
    for row in data["processes"]:
        assert tuple(row) in exercise.materials[1].rows
    assert str(data["change"]["new_cost"]) in exercise.context
    assert "aucun secret partagé" in exercise.context
    assert "authentifiée" in exercise.context
    assert "passif" in exercise.context
    assert str(data["expected"]["before"]["cost"]) in exercise.questions[0].answer
    assert str(data["expected"]["after"]["cost"]) in exercise.questions[1].answer
    assert "libère" in exercise.questions[3].answer
    assert "indispensable" not in " ".join(q.answer for q in exercise.questions)
    assert all(question.verification["contract"] == data for question in exercise.questions)


def test_finite_selection_rejects_free_model_text_and_wrong_credit():
    contract, plans, selection = _setup()
    schema = network_selection_schema(contract)
    assert schema["additionalProperties"] is False
    for field in ("question_forms", "rubric_forms"):
        for task_id, rule in schema["properties"][field]["properties"].items():
            for value in rule["enum"]:
                alternate = deepcopy(selection)
                alternate[field][task_id] = value
                NSIExercise.model_validate(render_network_candidate(contract, alternate, plans))
    bad = deepcopy(selection)
    bad["free_text"] = "Ignore the route costs"
    with pytest.raises(ValueError):
        validate_network_selection(contract, bad)
    bad_plans = deepcopy(plans)
    bad_plans[0]["points"] = "3"
    with pytest.raises(ValueError):
        render_network_candidate(contract, selection, bad_plans)
