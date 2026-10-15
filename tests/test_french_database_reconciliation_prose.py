"""V24 prompts and working tables must express the locked incident chain."""

from __future__ import annotations

import importlib
from decimal import Decimal

import pytest

from Backend.Core.france.database_reconciliation_contract import (
    build_database_reconciliation_contract,
)

_QUARTERS = {
    "5.5": (1, 2, 2, 2, 2, 3, 2, 2, 2, 2, 1, 1),
    "6": (1, 2, 3, 2, 2, 4, 2, 2, 2, 2, 1, 1),
    "6.5": (1, 2, 3, 2, 2, 4, 3, 2, 2, 3, 1, 1),
}
_MINUTES = (4, 5, 8, 6, 7, 8, 6, 6, 6, 6, 4, 4)
_IDS = tuple(f"2{letter}" for letter in "abcdefghijkl")


def _module():
    try:
        return importlib.import_module(
            "Backend.Core.france.database_reconciliation_prose"
        )
    except ModuleNotFoundError:
        pytest.fail("The V24 finite reconciliation catalogue is not implemented")


def _specs(total: str) -> list[dict]:
    return [
        {
            "id": task_id,
            "points": str(Decimal(quarters) / 4),
            "estimated_minutes": minutes,
            "required_curriculum_code": "LP-DEBUG" if task_id >= "2g" else "BDD-MODELE",
            "operation": (
                "debug"
                if task_id >= "2g"
                else "design"
                if task_id in {"2e", "2f"}
                else "analyse"
            ),
            "difficulty": 4 if task_id in {"2c", "2f", "2j", "2k"} else 3,
        }
        for task_id, quarters, minutes in zip(
            _IDS, _QUARTERS[total], _MINUTES, strict=True
        )
    ]


def _selection(module, contract) -> dict:
    schema = module.database_reconciliation_selection_schema(contract)
    assert set(schema["properties"]["scene_id"]["enum"]) == {"atelier", "service"}
    return {
        "scene_id": "atelier",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in _IDS},
        "rubric_forms": {task_id: f"{task_id}-r1" for task_id in _IDS},
    }


@pytest.mark.parametrize("total", list(_QUARTERS))
def test_exact_credit_time_and_working_surfaces(total: str) -> None:
    module = _module()
    contract = build_database_reconciliation_contract(270100)
    candidate = module.render_database_reconciliation_candidate(
        contract, _selection(module, contract), _specs(total)
    )
    questions = candidate["questions"]
    assert [question["id"] for question in questions] == list(_IDS)
    assert [Decimal(q["points"]) for q in questions] == [
        Decimal(value) / 4 for value in _QUARTERS[total]
    ]
    assert sum(Decimal(q["points"]) for q in questions) == Decimal(total)
    assert sum(q["estimated_minutes"] for q in questions) == candidate["minutes"] == 70
    assert [material["id"] for material in candidate["materials"]] == [
        "agent",
        "categorie",
        "incident",
        "recon_jointure",
        "recon_effectifs",
        "recon_etats",
    ]
    for material in candidate["materials"][3:]:
        assert material["kind"] == "table"
    assert all(
        cell == "…"
        for material in (candidate["materials"][3], candidate["materials"][5])
        for row in material["rows"]
        for cell in row[1:]
    )
    assert len(candidate["materials"][3]["rows"]) == 8
    assert candidate["materials"][4]["rows"][-1] == ["5", "—", "…"]
    assert questions[2]["material_ids"] == ["recon_jointure"]
    assert questions[5]["material_ids"] == ["recon_effectifs"]
    assert questions[9]["material_ids"] == ["recon_etats"]


def test_prompts_answers_and_criteria_cover_the_dependent_trace() -> None:
    module = _module()
    contract = build_database_reconciliation_contract(270100)
    candidate = module.render_database_reconciliation_candidate(
        contract, _selection(module, contract), _specs("6")
    )
    questions = {question["id"]: question for question in candidate["questions"]}
    assert "109" in questions["2b"]["prompt"]
    assert "101" in questions["2c"]["prompt"]
    assert "108" in questions["2c"]["prompt"]
    assert "101, 102, 103, 104, 105, 106" in questions["2d"]["answer"]
    assert "2, 2, 2, 2" in questions["2f"]["answer"]
    assert "def nombre_clos_categorie" in questions["2g"]["prompt"]
    assert "2" in questions["2g"]["answer"]
    assert "id_cat" in questions["2h"]["answer"]
    assert "101" in questions["2i"]["answer"]
    assert "104" in questions["2i"]["answer"]
    assert all(
        "modifie une ligne" in mark["criterion"] for mark in questions["2i"]["marking"]
    )
    assert "0, 1, 2" in questions["2j"]["answer"]
    assert "2, 2, 2" in questions["2j"]["answer"]
    assert "S2" in questions["2k"]["prompt"]
    assert "0" in questions["2l"]["answer"]
    for question in questions.values():
        assert question["prompt"] and question["answer"]
        assert len(question["marking"]) == int(Decimal(question["points"]) * 4)
        assert sum(Decimal(mark["points"]) for mark in question["marking"]) == Decimal(
            question["points"]
        )
        assert all(mark["criterion"] for mark in question["marking"])
        assert question["verification"]["contract"] == contract.to_dict()


def test_finite_selection_rejects_free_text_and_wrong_profile() -> None:
    module = _module()
    contract = build_database_reconciliation_contract(270100)
    selection = _selection(module, contract)
    assert module.database_reconciliation_catalogue_digest()
    with pytest.raises(ValueError):
        module.validate_database_reconciliation_selection(
            contract, {**selection, "scene_id": "other"}
        )
    with pytest.raises(ValueError):
        module.validate_database_reconciliation_selection(
            contract, {**selection, "scene_id": ["atelier"]}
        )
    with pytest.raises(ValueError):
        module.validate_database_reconciliation_selection(
            contract,
            {
                **selection,
                "question_forms": {**selection["question_forms"], "2a": "free text"},
            },
        )
    invalid = _specs("6")
    invalid[0]["points"] = "1"
    with pytest.raises(ValueError):
        module.render_database_reconciliation_candidate(contract, selection, invalid)
