# V25 candidate wording binds each closure to answerable graph work.

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from importlib import import_module

import pytest

from Backend.Core.france.graph_two_outage_contract import (
    build_graph_two_outage_contract,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v17

_IDS = [f"1{letter}" for letter in "abcdefghij"]
_MINUTES = (3, 3, 10, 8, 8, 10, 11, 6, 5, 6)
_BASE = ("0.25", "0.25", "1", "0.5", "0.5", "1", "0.5", "0.5", "0.5", "0.5")


def _prose():
    return import_module("Backend.Core.france.graph_two_outage_prose")


def _specs(total: str) -> list[dict]:
    specs = deepcopy(_tasks_for_seed_v17(270100)[0]["question_blueprint"])
    for index, item in enumerate(specs):
        item["points"] = _BASE[index]
        item["estimated_minutes"] = _MINUTES[index]
    specs[5].update(operation="analyse", difficulty=4)
    specs[6].update(operation="justify", difficulty=4)
    if total in ("6", "6.5"):
        specs[4]["points"] = "1"
    if total == "6.5":
        specs[9]["points"] = "1"
    return specs


def _selection() -> dict:
    return {
        "scene_id": "service",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in _IDS},
        "rubric_forms": {task_id: f"{task_id}-r1" for task_id in _IDS},
    }


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_v25_stages_two_outages_with_exact_credit_and_no_answer_leak(
    total: str,
) -> None:
    candidate = _prose().render_graph_two_outage_candidate(
        build_graph_two_outage_contract(270100), _selection(), _specs(total)
    )
    NSIExercise.model_validate(candidate)
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert [question["id"] for question in candidate["questions"]] == _IDS
    assert [
        question["estimated_minutes"] for question in candidate["questions"]
    ] == list(_MINUTES)
    assert sum(
        Decimal(question["points"]) for question in candidate["questions"]
    ) == Decimal(total)
    assert all(
        sum(Decimal(mark["points"]) for mark in question["marking"])
        == Decimal(question["points"])
        for question in candidate["questions"]
    )
    materials = {material["id"]: material for material in candidate["materials"]}
    questions = {question["id"]: question for question in candidate["questions"]}
    assert "trace_fermeture" in questions["1f"]["material_ids"]
    assert "trace_fermeture" not in questions["1g"]["material_ids"]
    assert "route_double_fermeture" in questions["1g"]["material_ids"]
    assert "E–F" in materials["route_double_fermeture"]["title"]
    assert all(
        "_____" in cell for cell in materials["route_double_fermeture"]["rows"][0]
    )
    assert "A–B" in questions["1f"]["prompt"]
    assert "E–F" in questions["1g"]["prompt"]
    assert "file après" not in questions["1f"]["prompt"].lower()
    assert "A → C → D → E → F" in questions["1f"]["answer"]
    assert "A → C → D → F" not in questions["1g"]["prompt"]
    assert "A → C → D → F" in questions["1g"]["answer"]
    assert "14 + 2 + 14 = 30" in questions["1g"]["answer"]
    assert questions["1g"]["points"] == "0.5"
    assert questions["1f"]["operation"] == "analyse"
    assert questions["1f"]["difficulty"] == 4
    assert questions["1g"]["difficulty"] == 4
    assert len(questions["1g"]["marking"]) == 2
    assert all(mark["points"] == "0.25" for mark in questions["1g"]["marking"])
    assert all(
        question["verification"]["kind"] == "graph_two_outage_contract"
        for question in questions.values()
    )


def test_v25_equal_cost_answer_says_equal() -> None:
    candidate = _prose().render_graph_two_outage_candidate(
        build_graph_two_outage_contract(270102), _selection(), _specs("6")
    )
    question = next(item for item in candidate["questions"] if item["id"] == "1g")
    assert "égal" in question["answer"]
    assert "supérieur" not in question["answer"]


def test_v25_finite_selection_and_wrong_profile_fail_closed() -> None:
    prose = _prose()
    contract = build_graph_two_outage_contract(270100)
    assert len(prose.graph_two_outage_catalogue_digest()) == 64
    assert prose.graph_two_outage_selection_schema(contract)["properties"]["scene_id"][
        "enum"
    ]
    assert (
        prose.validate_graph_two_outage_selection(contract, _selection())
        == _selection()
    )
    bad_selection = _selection()
    bad_selection["question_forms"]["1g"] = "unregistered"
    with pytest.raises(ValueError):
        prose.validate_graph_two_outage_selection(contract, bad_selection)
    bad_specs = _specs("6")
    bad_specs[6]["points"] = "0.75"
    with pytest.raises(ValueError):
        prose.render_graph_two_outage_candidate(contract, _selection(), bad_specs)
