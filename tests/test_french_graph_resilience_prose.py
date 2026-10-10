"""V20 wording and marks are finite and match the requested evidence."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.graph_resilience_contract import (
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_resilience_prose import (
    graph_resilience_catalogue_digest,
    graph_resilience_selection_schema,
    render_graph_resilience_candidate,
    validate_graph_resilience_selection,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v17

_IDS = [f"1{letter}" for letter in "abcdefghij"]
_BASE = ("0.25", "0.25", "1", "0.5", "0.5", "0.5", "1", "0.5", "0.5", "0.5")


def _specs(total):
    specs = deepcopy(_tasks_for_seed_v17(270100)[0]["question_blueprint"])
    for index, item in enumerate(specs):
        item["points"] = _BASE[index]
    if total in ("6", "6.5"):
        specs[4]["points"] = "1"
    if total == "6.5":
        specs[9]["points"] = "1"
    return specs


def _selection():
    return {
        "scene_id": "service",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in _IDS},
        "rubric_forms": {task_id: f"{task_id}-r1" for task_id in _IDS},
    }


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_v20_candidate_has_exact_profile_and_evidence_matched_criteria(total):
    contract = build_graph_resilience_contract(270100)
    candidate = render_graph_resilience_candidate(contract, _selection(), _specs(total))
    NSIExercise.model_validate(candidate)
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert [question["id"] for question in candidate["questions"]] == _IDS
    assert sum(q["estimated_minutes"] for q in candidate["questions"]) == 70
    assert all(
        sum(Decimal(mark["points"]) for mark in q["marking"]) == Decimal(q["points"])
        for q in candidate["questions"]
    )
    questions = {q["id"]: q for q in candidate["questions"]}
    assert "degré" in questions["1a"]["prompt"]
    assert "somme des poids incidents" not in questions["1a"]["prompt"]
    assert "A–C–E–F" in questions["1b"]["prompt"]
    assert "ordre complet" in questions["1e"]["prompt"]
    assert "liaison" in questions["1g"]["prompt"]
    assert all(mark["points"] == "0.25" for mark in questions["1g"]["marking"])
    assert len(questions["1g"]["marking"]) == 4
    assert "Comparez" in questions["1g"]["prompt"]
    assert "il peut être de même poids" not in questions["1g"]["prompt"]
    assert questions["1g"]["answer"].count("→") >= 1
    assert all(
        q["verification"]["kind"] == "graph_resilience_contract"
        for q in questions.values()
    )


def test_v20_catalogue_and_selection_are_finite_and_hash_bound():
    contract = build_graph_resilience_contract(270100)
    schema = graph_resilience_selection_schema(contract)
    assert schema["properties"]["scene_id"]["enum"]
    assert len(graph_resilience_catalogue_digest()) == 64
    assert validate_graph_resilience_selection(contract, _selection()) == _selection()
    invalid = _selection()
    invalid["question_forms"]["1g"] = "invented-route"
    with pytest.raises(ValueError):
        validate_graph_resilience_selection(contract, invalid)
    invalid = _selection()
    invalid["claimed_cost"] = 0
    with pytest.raises(ValueError):
        validate_graph_resilience_selection(contract, invalid)


def test_v20_catalogue_binds_reused_v3_answer_wording(monkeypatch):
    from Backend.Core.france import graph_resilience_prose as prose

    original = prose.graph_resilience_catalogue_digest()
    monkeypatch.setattr(prose, "graph_tree_depth_catalogue_digest", lambda: "changed")
    assert prose.graph_resilience_catalogue_digest() != original


def test_v20_equal_cost_answer_does_not_claim_an_increase():
    seed = next(
        seed
        for seed in range(100)
        if build_graph_resilience_contract(seed).to_dict()["expected"]["1g"][
            "comparison"
        ]
        == "égal"
    )
    contract = build_graph_resilience_contract(seed)
    candidate = render_graph_resilience_candidate(contract, _selection(), _specs("6"))
    answer = candidate["questions"][6]["answer"]
    assert "égal" in answer
    assert "supérieur" not in answer


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_v20_route_and_search_prompts_match_credited_evidence(total):
    candidate = render_graph_resilience_candidate(
        build_graph_resilience_contract(270100), _selection(), _specs(total)
    )
    questions = {question["id"]: question for question in candidate["questions"]}
    route = questions["1d"]
    assert "liaisons parcourues" in route["prompt"]
    assert "+" in route["answer"]
    assert any("liaisons" in mark["criterion"] for mark in route["marking"])

    search = questions["1j"]
    if total == "6.5":
        assert "tracez" in search["prompt"]
        assert "justifiez" in search["prompt"]
        assert any("chemin" in mark["criterion"] for mark in search["marking"])
        assert any("justification" in mark["criterion"] for mark in search["marking"])
    else:
        assert "tracez" in search["prompt"]
        assert "justifiez" not in search["prompt"]
        assert any("chemin" in mark["criterion"] for mark in search["marking"])
        assert all("justification" not in mark["criterion"] for mark in search["marking"])
