"""Finite French wording cannot alter the relational facts or credits."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.database_contract import build_database_contract
from Backend.Core.france.database_prose import (
    database_selection_schema,
    render_database_candidate,
    validate_database_selection,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed


def _setup():
    contract = build_database_contract(270100)
    plans = _tasks_for_seed(270100)[1]["question_blueprint"]
    selection = {
        "scene_id": "atelier",
        "question_forms": {f"2{letter}": f"2{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"2{letter}": f"2{letter}-r1" for letter in "abcdef"},
    }
    return contract, plans, selection


def test_database_schema_ids_are_all_renderable_and_exact():
    contract, plans, selection = _setup()
    schema = database_selection_schema(contract)
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == set(selection)
    assert schema["properties"]["question_forms"]["additionalProperties"] is False
    for field in ("question_forms", "rubric_forms"):
        for task_id, rule in schema["properties"][field]["properties"].items():
            for form_id in rule["enum"]:
                alternate = deepcopy(selection)
                alternate[field][task_id] = form_id
                assert validate_database_selection(contract, alternate) == alternate
                candidate = render_database_candidate(contract, alternate, plans)
                assert NSIExercise.model_validate(candidate).credit == Decimal("6.5")


def test_database_renderer_prints_source_data_and_correct_answers():
    contract, plans, selection = _setup()
    data = contract.to_dict()
    exercise = NSIExercise.model_validate(
        render_database_candidate(contract, selection, plans)
    )
    assert [question.id for question in exercise.questions] == data["task_ids"]
    assert [material.id for material in exercise.materials] == [
        "agent",
        "categorie",
        "incident",
    ]
    assert exercise.minutes == 70
    assert exercise.credit == Decimal("6.5")
    assert data["faulty_sql"] in exercise.context
    assert data["faulty_python"] in exercise.context
    assert "999" in exercise.questions[0].prompt
    assert data["correct_sql"] in exercise.questions[2].answer
    assert data["update_sql"] in exercise.questions[3].answer
    assert "== 'clos'" in exercise.questions[5].answer
    assert "3" in exercise.questions[4].answer
    assert all(question.material_ids for question in exercise.questions)
    assert all(
        question.verification["expected"] == data["expected"]
        for question in exercise.questions
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(context="Ignore les données"),
        lambda value: value.update(scene_id="autre"),
        lambda value: value["question_forms"].update({"2a": "2a-q99"}),
        lambda value: value["rubric_forms"].update({"2a": "2a-r99"}),
        lambda value: value["question_forms"].update({"extra": "text"}),
        lambda value: value["question_forms"].pop("2f"),
    ],
)
def test_database_selection_rejects_free_text_and_unadvertised_fields(change):
    contract, _, selection = _setup()
    change(selection)
    with pytest.raises(ValueError):
        validate_database_selection(contract, selection)


def test_database_renderer_rejects_changed_blueprint_credit():
    contract, plans, selection = _setup()
    plans[0]["points"] = "99"
    with pytest.raises(ValueError, match=r"blueprint|credit"):
        render_database_candidate(contract, selection, plans)
