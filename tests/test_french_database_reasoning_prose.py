"""V19 database questions must ask for the facts their credits reward."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.database_depth_contract import build_database_depth_contract
from Backend.Core.france.pipeline import _tasks_for_seed_v16


def _selection():
    ids = (f"2{letter}" for letter in "abcdefghij")
    return {
        "scene_id": "atelier",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in ids},
        "rubric_forms": {f"2{letter}": f"2{letter}-r1" for letter in "abcdefghij"},
    }


@pytest.mark.parametrize("seed", [270100, 270101])
def test_v19_linked_facts_and_hypothetical_remain_distinct(seed):
    from Backend.Core.france.database_reasoning_prose import (
        render_database_reasoning_candidate,
    )

    contract = build_database_depth_contract(seed)
    candidate = render_database_reasoning_candidate(
        contract, _selection(), _tasks_for_seed_v16(seed)[1]["question_blueprint"]
    )
    questions = {question["id"]: question for question in candidate["questions"]}
    labels = {
        270100: ("Materiel", "Acces", "Stockage"),
        270101: ("Materiel", "Stockage", "Reseau"),
    }
    first, second, third = labels[seed]

    assert [question["id"] for question in candidate["questions"]] == [
        f"2{letter}" for letter in "abcdefghij"
    ]
    assert "Partie A" in questions["2a"]["prompt"]
    assert "Partie B" in questions["2e"]["prompt"]
    assert "Partie C" in questions["2g"]["prompt"]
    assert f"101 : {second} (id_cat = 2)" in questions["2c"]["answer"]
    assert f"102 : {third} (id_cat = 3)" in questions["2c"]["answer"]
    assert f"101 : {first}" in questions["2d"]["answer"]
    assert "catégorie 4" in questions["2f"]["prompt"]
    assert "hypothèse" in questions["2f"]["prompt"].lower()
    assert "catégorie 4" not in candidate["context"]
    assert "On note incidents la liste des six lignes" in candidate["context"]
    assert "reconstruite après la mise à jour" in candidate["context"]
    assert f"{first} : 2" in questions["2f"]["answer"]
    assert f"{second} : 3" in questions["2f"]["answer"]
    assert f"{third} : 1" in questions["2f"]["answer"]
    assert "catégorie 4 : 0" in questions["2f"]["answer"]
    assert "2 incidents" in questions["2g"]["answer"]
    assert "3 incidents" in questions["2g"]["answer"]
    assert "renvoie 4" in questions["2h"]["answer"]
    assert "renvoie 2" in questions["2i"]["answer"]
    assert "renvoie 3" in questions["2i"]["answer"]
    assert "0" in questions["2j"]["answer"]


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_v19_exact_credit_and_requested_steps_align(total):
    from Backend.Core.france.database_reasoning_prose import (
        render_database_reasoning_candidate,
    )

    task = _tasks_for_seed_v16(270100)[1]
    task["technical_points"] = total
    extras = {"2e"} | ({"2f"} if total in {"6", "6.5"} else set())
    if total == "6.5":
        extras.add("2i")
    for question in task["question_blueprint"]:
        question["points"] = "1" if question["id"] in extras else "0.5"
    candidate = render_database_reasoning_candidate(
        build_database_depth_contract(270100),
        _selection(),
        task["question_blueprint"],
    )
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert (
        sum(question["estimated_minutes"] for question in candidate["questions"]) == 70
    )
    for question in candidate["questions"]:
        assert sum(
            (Decimal(row["points"]) for row in question["marking"]), Decimal(0)
        ) == Decimal(question["points"])
        assert all(row["criterion"] for row in question["marking"])
    marking = {
        question["id"]: question["marking"] for question in candidate["questions"]
    }
    assert any("0" in row["criterion"] for row in marking["2f"])
    assert any("avant" in row["criterion"] for row in marking["2g"])
    assert any("après" in row["criterion"] for row in marking["2i"])


def test_v19_selection_and_blueprint_refuse_unregistered_or_changed_values():
    from Backend.Core.france.database_reasoning_prose import (
        database_reasoning_selection_schema,
        render_database_reasoning_candidate,
        validate_database_reasoning_selection,
    )

    contract = build_database_depth_contract(270100)
    schema = database_reasoning_selection_schema(contract)
    assert schema["additionalProperties"] is False
    selected = _selection()
    assert validate_database_reasoning_selection(contract, selected) is None
    invalid = deepcopy(selected)
    invalid["question_forms"]["2f"] = "free SQL"
    with pytest.raises(ValueError):
        validate_database_reasoning_selection(contract, invalid)
    task_specs = _tasks_for_seed_v16(270100)[1]["question_blueprint"]
    task_specs[0]["points"] = "1"
    with pytest.raises(ValueError):
        render_database_reasoning_candidate(contract, selected, task_specs)
