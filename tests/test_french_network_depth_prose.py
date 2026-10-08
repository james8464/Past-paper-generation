"""The v15 network case prints every needed fact and awards exact, separable credit."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.network_depth_contract import build_network_depth_contract
from Backend.Core.france.network_depth_prose import (
    network_depth_selection_schema,
    render_network_depth_candidate,
    validate_network_depth_selection,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v15
from Backend.Core.france.verification import verify_contract


def _selection():
    return {
        "scene_id": "campus",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }


@pytest.mark.parametrize(
    "seed,credit", [(270100, "5.5"), (270101, "6"), (270102, "6.5")]
)
def test_v15_finite_case_prints_all_premises_and_exact_credit(seed, credit):
    contract = build_network_depth_contract(seed)
    task = _tasks_for_seed_v15(seed)[2]
    exercise = NSIExercise.model_validate(
        render_network_depth_candidate(
            contract, _selection(), task["question_blueprint"]
        )
    )
    facts = contract.to_dict()
    assert exercise.credit == Decimal(credit)
    assert exercise.minutes == 70
    assert [question.id for question in exercise.questions] == facts["task_ids"]
    assert [material.id for material in exercise.materials] == ["links", "processes"]
    for left, right, cost in facts["links"]:
        assert (left, right, str(cost)) in exercise.materials[0].rows
    assert str(facts["change"]["new_cost"]) in exercise.context
    assert ("P1", "A", "B") in exercise.materials[1].rows
    assert ("P2", "B", "A") in exercise.materials[1].rows
    assert "A avant B" in exercise.context
    assert "authentifiée" in exercise.context
    assert "signature" in exercise.context
    assert all(
        verify_contract(question.verification)["state"] == "passed"
        for question in exercise.questions
    )
    assert [question.points for question in exercise.questions] == [
        plan["points"] for plan in task["question_blueprint"]
    ]
    assert sum(
        (Decimal(question.points) for question in exercise.questions), Decimal()
    ) == Decimal(credit)


def test_routing_answers_and_marks_separate_trace_path_and_cost():
    seed = next(
        seed
        for seed in range(100)
        if build_network_depth_contract(seed).to_dict()["profile_offset"] == 0
    )
    task = _tasks_for_seed_v15(seed)[2]
    exercise = NSIExercise.model_validate(
        render_network_depth_candidate(
            build_network_depth_contract(seed), _selection(), task["question_blueprint"]
        )
    )
    initial, changed = exercise.questions[:2]
    assert "Central" in initial.prompt and "R1" in initial.answer
    assert "Dijkstra" in changed.prompt
    assert "R2" in changed.answer and "R3" in changed.answer
    assert "11" in changed.answer
    assert "R3=14" in changed.answer
    assert "R3=7" in changed.answer
    assert "Station=15" in changed.answer
    assert "Station=11" in changed.answer
    assert [credit.points for credit in changed.marking] == ["0.25"] * 6
    assert sum("trace" in credit.criterion for credit in changed.marking) >= 3
    assert all(credit.criterion.strip() for credit in changed.marking)
    assert "P2" in exercise.questions[3].answer
    assert "A avant B" in exercise.questions[3].answer
    assert "n'authentifie pas" in exercise.questions[5].answer


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
def test_network_rubric_splits_independent_steps_without_losing_credit(seed):
    task = _tasks_for_seed_v15(seed)[2]
    exercise = NSIExercise.model_validate(
        render_network_depth_candidate(
            build_network_depth_contract(seed), _selection(), task["question_blueprint"]
        )
    )
    for question in exercise.questions:
        assert all(credit.points == "0.25" for credit in question.marking)
        assert all(" ; " not in credit.criterion for credit in question.marking)
        assert sum(
            (Decimal(credit.points) for credit in question.marking), Decimal()
        ) == Decimal(question.points)


def test_network_limit_question_requests_each_awarded_limit():
    contract = build_network_depth_contract(270101)
    task = _tasks_for_seed_v15(270101)[2]
    for form in ("3f-q1", "3f-q2"):
        selection = _selection()
        selection["question_forms"]["3f"] = form
        exercise = NSIExercise.model_validate(
            render_network_depth_candidate(
                contract, selection, task["question_blueprint"]
            )
        )
        prompt = exercise.questions[-1].prompt.lower()
        assert "station" in prompt
        assert "terminal compromis" in prompt


def test_selection_and_credit_tampering_are_rejected():
    contract = build_network_depth_contract(270100)
    task = _tasks_for_seed_v15(270100)[2]
    schema = network_depth_selection_schema(contract)
    assert schema["additionalProperties"] is False
    for field in ("question_forms", "rubric_forms"):
        for question_id, rule in schema["properties"][field]["properties"].items():
            for value in rule["enum"]:
                selection = _selection()
                selection[field][question_id] = value
                NSIExercise.model_validate(
                    render_network_depth_candidate(
                        contract, selection, task["question_blueprint"]
                    )
                )
    for bad in (
        {**_selection(), "free_text": "changer le coût"},
        {**_selection(), "scene_id": "unknown"},
        {
            **_selection(),
            "question_forms": {**_selection()["question_forms"], "3a": "texte libre"},
        },
    ):
        with pytest.raises(ValueError):
            validate_network_depth_selection(contract, bad)
    plans = deepcopy(task["question_blueprint"])
    plans[1]["points"] = "2"
    with pytest.raises(ValueError):
        render_network_depth_candidate(contract, _selection(), plans)
