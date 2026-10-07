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


def test_service_scene_has_no_atelier_specific_table_title():
    contract, plans, selection = _setup()
    selection["scene_id"] = "service"
    exercise = NSIExercise.model_validate(
        render_database_candidate(contract, selection, plans)
    )
    assert all(
        "atelier" not in material.title.lower() for material in exercise.materials
    )


def test_database_marking_is_specific_and_does_not_embed_code_fences():
    contract, plans, selection = _setup()
    exercise = NSIExercise.model_validate(
        render_database_candidate(contract, selection, plans)
    )
    criteria = [
        credit.criterion
        for question in exercise.questions
        for credit in question.marking
    ]
    assert all("```" not in criterion for criterion in criteria)
    assert "incident.id_cat = categorie.id_cat" in " ".join(criteria)
    assert "101" in " ".join(criteria)
    assert "ouvert" in " ".join(criteria)
    assert "clos" in " ".join(criteria)
    assert all(not criterion.startswith("Attribuer pour") for criterion in criteria)


def test_database_inline_prose_is_print_ready_without_markdown_backticks():
    contract, plans, selection = _setup()
    exercise = NSIExercise.model_validate(
        render_database_candidate(contract, selection, plans)
    )
    context_without_code = exercise.context.replace(
        "```sql\n" + contract.to_dict()["faulty_sql"] + "\n```", ""
    ).replace("```python\n" + contract.to_dict()["faulty_python"] + "\n```", "")
    assert "`" not in context_without_code
    assert "Chaque argument" not in context_without_code
    assert all("`" not in question.prompt for question in exercise.questions)
    assert "`" not in exercise.questions[4].answer.replace("```python", "").replace(
        "```", ""
    )
    assert "`" not in exercise.questions[5].answer.replace("```python", "").replace(
        "```", ""
    )
    assert "```python\nassert nombre_clos([" in exercise.questions[4].answer
    assert (
        "```python\nif incident['statut'] == 'clos':\n```"
        in exercise.questions[5].answer
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


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
def test_database_renderer_respects_each_seeded_credit_profile(seed):
    contract = build_database_contract(seed)
    task = _tasks_for_seed(seed)[1]
    selection = _setup()[2]
    exercise = NSIExercise.model_validate(
        render_database_candidate(contract, selection, task["question_blueprint"])
    )
    assert exercise.credit == Decimal(task["technical_points"])
    assert [question.points for question in exercise.questions] == [
        plan["points"] for plan in task["question_blueprint"]
    ]
