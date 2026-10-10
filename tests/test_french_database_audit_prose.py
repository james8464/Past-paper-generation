"""V21 prompts and candidate working surfaces stay tied to locked audit facts."""

from __future__ import annotations

import importlib
from decimal import Decimal

import pytest

from Backend.Core.france.database_audit_contract import build_database_audit_contract


def _module():
    try:
        return importlib.import_module("Backend.Core.france.database_audit_prose")
    except ModuleNotFoundError:
        pytest.fail("The finite V21 incident-audit catalogue is not implemented")


_PROFILES = {
    "5.5": ("0.25", "0.5", "0.5", "0.5", "0.75", "1", "0.5", "0.5", "0.75", "0.25"),
    "6": ("0.25", "0.5", "0.75", "0.5", "0.75", "1", "0.75", "0.5", "0.75", "0.25"),
    "6.5": ("0.25", "0.5", "0.75", "0.75", "0.75", "1", "0.75", "0.75", "0.75", "0.25"),
}


def _specs(total: str) -> list[dict]:
    return [
        {
            "id": f"2{letter}",
            "points": points,
            "estimated_minutes": minutes,
            "required_curriculum_code": (
                "LP-DEBUG" if letter in "ij" else "BDD-MODELE"
            ),
            "operation": (
                "debug"
                if letter in "ij"
                else "design"
                if letter in "efg"
                else "analyse"
            ),
            "difficulty": 4 if letter in "gi" else 3,
        }
        for letter, points, minutes in zip(
            "abcdefghij", _PROFILES[total], (6, 6, 7, 7, 8, 8, 7, 7, 7, 7), strict=True
        )
    ]


def _selection(module, contract):
    schema = module.database_audit_selection_schema(contract)
    assert set(schema["properties"]["scene_id"]["enum"]) == {"atelier", "service"}
    return {
        "scene_id": "atelier",
        "question_forms": {
            task_id: f"{task_id}-q1" for task_id in contract.to_dict()["task_ids"]
        },
        "rubric_forms": {
            task_id: f"{task_id}-r1" for task_id in contract.to_dict()["task_ids"]
        },
    }


@pytest.mark.parametrize("total", list(_PROFILES))
def test_exact_credit_timing_and_three_staged_working_tables(total: str) -> None:
    module = _module()
    contract = build_database_audit_contract(270100)
    candidate = module.render_database_audit_candidate(
        contract, _selection(module, contract), _specs(total)
    )
    questions = candidate["questions"]
    assert [question["id"] for question in questions] == [f"2{x}" for x in "abcdefghij"]
    assert sum(Decimal(q["points"]) for q in questions) == Decimal(total)
    assert sum(q["estimated_minutes"] for q in questions) == 70
    assert candidate["minutes"] == 70
    assert [material["id"] for material in candidate["materials"]] == [
        "agent",
        "categorie",
        "incident",
        "audit_jointure",
        "audit_etats",
        "audit_trace",
    ]
    for material in candidate["materials"][3:]:
        assert material["kind"] == "table"
        assert all(cell == "…" for row in material["rows"] for cell in row[1:])
    assert questions[2]["material_ids"] == ["audit_jointure"]
    assert questions[6]["material_ids"] == ["audit_etats"]
    assert questions[8]["material_ids"] == ["audit_trace"]


def test_prompts_answers_and_rubrics_track_locked_phases() -> None:
    module = _module()
    contract = build_database_audit_contract(270100)
    candidate = module.render_database_audit_candidate(
        contract, _selection(module, contract), _specs("6")
    )
    questions = {q["id"]: q for q in candidate["questions"]}
    assert "999" in questions["2b"]["prompt"]
    assert "existant" in questions["2b"]["prompt"]
    assert "id_agent = 1" in questions["2b"]["answer"]
    assert questions["2a"]["prompt"].startswith("Partie A")
    assert questions["2e"]["prompt"].startswith("Partie B")
    assert questions["2g"]["prompt"].startswith("Partie C")
    assert "def nombre_clos" not in candidate["context"]
    assert "def nombre_clos" in questions["2h"]["prompt"]
    assert "audit_trace" in questions["2h"]["material_ids"]
    assert "5, 4, 3" in questions["2h"]["answer"]
    assert "101" in questions["2c"]["prompt"]
    assert "108" in questions["2c"]["prompt"]
    assert "2, 3, 2, 1" in questions["2f"]["answer"]
    assert "3, 4, 5" in questions["2g"]["answer"]
    assert "5, 4, 3" in questions["2i"]["answer"]
    assert "3, 4, 5" in questions["2i"]["answer"]
    assert "109" not in str(candidate["materials"][:3])
    for question in candidate["questions"]:
        assert question["prompt"] and question["answer"]
        assert sum(Decimal(c["points"]) for c in question["marking"]) == Decimal(
            question["points"]
        )
        assert len(question["marking"]) == int(Decimal(question["points"]) * 4)
        assert all(Decimal(c["points"]) == Decimal("0.25") for c in question["marking"])
        assert all(c["criterion"] for c in question["marking"])
        assert question["verification"]["contract"] == contract.to_dict()


def test_catalogue_is_finite_and_rejects_bad_selection_or_blueprint() -> None:
    module = _module()
    contract = build_database_audit_contract(270100)
    selection = _selection(module, contract)
    assert (
        module.database_audit_catalogue_digest()
        == module.database_audit_catalogue_digest()
    )
    with pytest.raises(ValueError):
        module.validate_database_audit_selection(
            contract, {**selection, "scene_id": "unknown"}
        )
    with pytest.raises(ValueError):
        module.validate_database_audit_selection(
            contract,
            {
                **selection,
                "question_forms": {**selection["question_forms"], "2a": "free"},
            },
        )
    invalid = _specs("6")
    invalid[0]["points"] = "1"
    with pytest.raises(ValueError):
        module.render_database_audit_candidate(contract, selection, invalid)
