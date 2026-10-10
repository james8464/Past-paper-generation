"""V22 wording must expose the intended work but not the derived answers."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.graph_route_trace_contract import (
    build_graph_route_trace_contract,
)
from Backend.Core.france.graph_route_trace_prose import (
    graph_route_trace_catalogue_digest,
    graph_route_trace_selection_schema,
    render_graph_route_trace_candidate,
    validate_graph_route_trace_selection,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v17

_IDS = [f"1{letter}" for letter in "abcdefghij"]
_BASE = ("0.25", "0.25", "1", "0.5", "0.5", "0.5", "1", "0.5", "0.5", "0.5")


def _specs(total: str) -> list[dict]:
    specs = deepcopy(_tasks_for_seed_v17(270100)[0]["question_blueprint"])
    for index, item in enumerate(specs):
        item["points"] = _BASE[index]
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
def test_v22_candidate_has_staged_before_after_work_and_exact_credit(total: str) -> None:
    candidate = render_graph_route_trace_candidate(
        build_graph_route_trace_contract(270100), _selection(), _specs(total)
    )
    NSIExercise.model_validate(candidate)
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert [question["id"] for question in candidate["questions"]] == _IDS
    assert sum(question["estimated_minutes"] for question in candidate["questions"]) == 70
    assert all(
        sum(Decimal(mark["points"]) for mark in question["marking"])
        == Decimal(question["points"])
        for question in candidate["questions"]
    )
    materials = {material["id"]: material for material in candidate["materials"]}
    assert {"reseau", "arbre", "trace_initial", "trace_fermeture"} <= set(materials)
    for phase in ("trace_initial", "trace_fermeture"):
        table = materials[phase]
        assert table["kind"] == "table"
        assert table["columns"] == ["Fixation / donnée", *"ABCDEF"]
        assert len(table["rows"]) == 4
        assert all(len(row) == 7 for row in table["rows"])
        assert [row[0] for row in table["rows"]] == [
            "1re distance (fixé : ___)", "1re préd.",
            "2e distance (fixé : ___)", "2e préd.",
        ]
        assert all(row[1:] == ["_____" for _ in "ABCDEF"] for row in table["rows"])
        assert all("A=0" not in " ".join(row) for row in table["rows"])
    assert "A–B" in materials["trace_fermeture"]["title"]
    questions = {question["id"]: question for question in candidate["questions"]}
    assert "trace_initial" in questions["1c"]["material_ids"]
    assert "trace_fermeture" in questions["1g"]["material_ids"]
    assert "trace_fermeture" not in questions["1c"]["material_ids"]
    assert "arbre" in questions["1h"]["material_ids"]
    assert "Nommez l'exception" in questions["1e"]["prompt"]
    assert "NameError" not in questions["1e"]["prompt"]
    assert "NameError" in questions["1e"]["answer"]
    assert "```python" in questions["1e"]["prompt"]
    assert "après correction" in questions["1f"]["prompt"].lower()
    assert "deux" in questions["1g"]["prompt"]
    assert "comparez" in questions["1g"]["prompt"].lower()
    assert "A → C → D → E → F" not in questions["1g"]["prompt"]
    assert "A → C → D → E → F" in questions["1g"]["answer"]
    assert "14 + 2 + 8 + 2 = 26" in questions["1g"]["answer"]
    assert len(questions["1g"]["marking"]) == 4
    assert all(mark["points"] == "0.25" for mark in questions["1g"]["marking"])
    assert all(
        question["verification"]["kind"] == "graph_route_trace_contract"
        for question in questions.values()
    )


def test_v22_selection_rejects_free_form_and_catalogue_is_bound() -> None:
    contract = build_graph_route_trace_contract(270100)
    schema = graph_route_trace_selection_schema(contract)
    assert schema["properties"]["scene_id"]["enum"]
    assert len(graph_route_trace_catalogue_digest()) == 64
    assert validate_graph_route_trace_selection(contract, _selection()) == _selection()
    invalid = _selection()
    invalid["question_forms"]["1g"] = "free text"
    with pytest.raises(ValueError):
        validate_graph_route_trace_selection(contract, invalid)
    invalid = _selection()
    invalid["claimed_distance"] = 1
    with pytest.raises(ValueError):
        validate_graph_route_trace_selection(contract, invalid)


@pytest.mark.parametrize("size,leading", [(12, 15), (16, 20)])
def test_v22_working_table_allocates_per_node_writing_height(
    size: int, leading: int
) -> None:
    from reportlab.lib.styles import ParagraphStyle

    from Backend.Core.france.nsi import NSITableMaterial
    from Backend.Core.france.rendering import structured_material

    candidate = render_graph_route_trace_candidate(
        build_graph_route_trace_contract(270100), _selection(), _specs("6")
    )
    material = NSITableMaterial.model_validate(
        next(item for item in candidate["materials"] if item["id"] == "trace_initial")
    )
    flowable = structured_material(
        material,
        body=ParagraphStyle("test", fontSize=size, leading=leading),
        bold_font="Helvetica-Bold",
        regular_font="Helvetica",
        available_width=460,
    )
    table = next(item for item in flowable._content if hasattr(item, "_rowHeights"))
    assert len(table._rowHeights) == 5
    assert table._rowHeights[1:] == [leading * 2 + 8] * 4
    assert len(table._colWidths) == 7


def test_v22_rejects_wrong_profile_or_unrequested_rubric() -> None:
    contract = build_graph_route_trace_contract(270100)
    specs = _specs("6")
    specs[6]["points"] = "0.75"
    with pytest.raises(ValueError):
        render_graph_route_trace_candidate(contract, _selection(), specs)
