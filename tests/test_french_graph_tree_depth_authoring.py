"""V17 graph/tree wording and credit are finite, locked, and replayable."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.graph_tree_depth_contract import (
    build_graph_tree_depth_contract,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed

_IDS = tuple(f"1{letter}" for letter in "abcdefghij")
_MINUTES = (6, 6, 8, 7, 8, 7, 7, 7, 7, 7)
_CODES = (
    "SD-GRAPHE",
    "SD-GRAPHE",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-ARBRES",
    "ALG-ARBRES",
    "ALG-ARBRES",
)
_OPERATIONS = (
    "apply",
    "analyse",
    "analyse",
    "justify",
    "apply",
    "debug",
    "justify",
    "apply",
    "analyse",
    "debug",
)


def _task(total="6"):
    source = _tasks_for_seed(270100)[0]
    extras = {"1c"} | ({"1e"} if total in {"6", "6.5"} else set())
    if total == "6.5":
        extras.add("1j")
    template = source["question_blueprint"][0]
    source["technical_points"] = total
    source["question_blueprint"] = [
        {
            **template,
            "id": task_id,
            "points": "1" if task_id in extras else "0.5",
            "estimated_minutes": minute,
            "part_id": "AAAABBBCCC"[index],
            "required_curriculum_code": code,
            "operation": operation,
            "difficulty": 4 if task_id in {"1c", "1j"} else 2,
        }
        for index, (task_id, minute, code, operation) in enumerate(
            zip(_IDS, _MINUTES, _CODES, _OPERATIONS, strict=True)
        )
    ]
    return source


def _selection():
    return {
        "scene_id": "service",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in _IDS},
        "rubric_forms": {task_id: f"{task_id}-r1" for task_id in _IDS},
    }


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


class SelectionClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate_json(self, prompt):
        return self.responses.pop(0)


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_depth_candidate_has_ten_native_french_questions_and_exact_credit(total):
    from Backend.Core.france.graph_tree_depth_prose import (
        render_graph_tree_depth_candidate,
    )

    contract = build_graph_tree_depth_contract(270100)
    candidate = render_graph_tree_depth_candidate(
        contract, _selection(), _task(total)["question_blueprint"]
    )
    NSIExercise.model_validate(candidate)
    assert candidate["id"] == "1"
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert [item["id"] for item in candidate["questions"]] == list(_IDS)
    assert sum(item["estimated_minutes"] for item in candidate["questions"]) == 70
    assert sum(Decimal(item["points"]) for item in candidate["questions"]) == Decimal(
        total
    )
    assert all(
        sum(Decimal(mark["points"]) for mark in item["marking"])
        == Decimal(item["points"])
        and all(mark["points"] == "0.25" for mark in item["marking"])
        for item in candidate["questions"]
    )
    assert "A–C–E–F" in candidate["questions"][1]["prompt"]
    assert "32" in candidate["questions"][1]["answer"]
    assert "11" in candidate["questions"][2]["answer"]
    assert "NameError" in candidate["questions"][5]["answer"]
    assert "18 → 13 → 10" in candidate["questions"][9]["answer"]
    assert "if cle > noeud.valeur" in candidate["context"]
    assert "if cle < noeud.valeur" not in candidate["context"]
    assert all(
        item["verification"]["kind"] == "graph_tree_depth_contract"
        for item in candidate["questions"]
    )


def test_depth_schema_and_transport_reject_free_form_claims():
    from Backend.Core.france.graph_tree_depth_authoring import (
        graph_tree_depth_selection_prompt,
    )
    from Backend.Core.france.graph_tree_depth_prose import (
        graph_tree_depth_selection_schema,
        validate_graph_tree_depth_selection,
    )
    from Backend.Core.france.provider import response_policy

    contract = build_graph_tree_depth_contract(270100)
    prompt = graph_tree_depth_selection_prompt(_task(), contract, [])
    assert response_policy(prompt) == (
        graph_tree_depth_selection_schema(contract),
        2048,
    )
    invalid = _selection()
    invalid["question_forms"]["1j"] = "print('answer')"
    with pytest.raises(ValueError):
        validate_graph_tree_depth_selection(contract, invalid)
    invalid = _selection()
    invalid["claimed_result"] = {"1d": "invented"}
    with pytest.raises(ValueError):
        validate_graph_tree_depth_selection(contract, invalid)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))


def test_depth_selection_retains_failure_and_hash_binds_replay(tmp_path, monkeypatch):
    from Backend.Core.france import graph_tree_depth_authoring as authoring

    contract = build_graph_tree_depth_contract(270100)
    bad = _selection()
    bad["rubric_forms"]["1a"] = "free prose"
    path = tmp_path / "selection.json"
    raw, evidence = authoring.author_graph_tree_depth_selection(
        SelectionClient([bad, _selection()]),
        _task(),
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert evidence["failed_attempts"][0]["response"] == bad
    assert evidence["failed_attempts"][0]["response_sha256"]
    assert (
        authoring.replay_graph_tree_depth_selection(
            _task(), contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    tampered = deepcopy(evidence)
    tampered["accepted"]["response"]["scene_id"] = "collecte"
    with pytest.raises(ValueError):
        authoring.replay_graph_tree_depth_selection(
            _task(), contract, [], tampered, run_identity=_identity()
        )
    monkeypatch.setattr(
        authoring, "graph_tree_depth_catalogue_digest", lambda: "changed"
    )
    with pytest.raises(ValueError):
        authoring.replay_graph_tree_depth_selection(
            _task(), contract, [], evidence, run_identity=_identity()
        )


def test_depth_blueprint_or_question_order_cannot_change(tmp_path):
    from Backend.Core.france.graph_tree_depth_authoring import (
        author_graph_tree_depth_selection,
    )
    from Backend.Core.france.graph_tree_depth_prose import (
        render_graph_tree_depth_candidate,
    )

    contract = build_graph_tree_depth_contract(270100)
    task = _task()
    path = tmp_path / "selection.json"
    author_graph_tree_depth_selection(
        SelectionClient([_selection()]),
        task,
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    changed = _task("6.5")
    with pytest.raises(ValueError):
        author_graph_tree_depth_selection(
            SelectionClient([]),
            changed,
            contract,
            [],
            path,
            run_identity=_identity(),
        )
    reordered = deepcopy(task["question_blueprint"])
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(ValueError):
        render_graph_tree_depth_candidate(contract, _selection(), reordered)
