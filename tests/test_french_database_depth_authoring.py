"""V2 database wording is finite, credit-locked, and replayable."""

import json
from copy import deepcopy

import pytest

from Backend.Core.france.database_depth_contract import build_database_depth_contract
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed


def _task(total="6"):
    source = _tasks_for_seed(270100)[1]
    minutes = (6, 6, 7, 7, 8, 8, 7, 7, 7, 7)
    extras = {"2e"} | ({"2f"} if total in {"6", "6.5"} else set())
    if total == "6.5":
        extras.add("2i")
    template = source["question_blueprint"][0]
    codes = (
        "BDD-ANOMALIES",
        "BDD-ANOMALIES",
        "BDD-SQL-SELECT",
        "BDD-SQL-SELECT",
        "BDD-SQL-SELECT",
        "BDD-SQL-SELECT",
        "BDD-SQL-MUTATION",
        "LP-DEBUG",
        "LP-DEBUG",
        "LP-DEBUG",
    )
    operations = (
        "recall",
        "apply",
        "analyse",
        "debug",
        "design",
        "analyse",
        "apply",
        "debug",
        "justify",
        "analyse",
    )
    source["technical_points"] = total
    source["question_blueprint"] = [
        {
            **template,
            "id": task_id,
            "points": "1" if task_id in extras else "0.5",
            "estimated_minutes": minute,
            "required_curriculum_code": code,
            "operation": operation,
            "difficulty": 4 if task_id in {"2f", "2h"} else 2,
        }
        for task_id, minute, code, operation in zip(
            (f"2{letter}" for letter in "abcdefghij"),
            minutes,
            codes,
            operations,
            strict=True,
        )
    ]
    return source


def _selection():
    return {
        "scene_id": "atelier",
        "question_forms": {f"2{letter}": f"2{letter}-q1" for letter in "abcdefghij"},
        "rubric_forms": {f"2{letter}": f"2{letter}-r1" for letter in "abcdefghij"},
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
    from Backend.Core.france.database_depth_prose import (
        render_database_depth_candidate,
    )

    contract = build_database_depth_contract(270100)
    candidate = render_database_depth_candidate(
        contract, _selection(), _task(total)["question_blueprint"]
    )
    NSIExercise.model_validate(candidate)
    assert candidate["target_points"] == total
    assert candidate["minutes"] == 70
    assert [q["id"] for q in candidate["questions"]] == [
        f"2{letter}" for letter in "abcdefghij"
    ]
    assert sum(q["estimated_minutes"] for q in candidate["questions"]) == 70
    assert all(
        q["prompt"] and q["answer"] and q["marking"] for q in candidate["questions"]
    )
    assert all(
        q["verification"]["kind"] == "database_depth_contract"
        for q in candidate["questions"]
    )
    assert "id_agent = 999" in candidate["questions"][1]["prompt"]
    assert "0" in candidate["questions"][9]["answer"]
    assert "Effectifs" in candidate["questions"][5]["answer"]
    assert "UPDATE" in candidate["questions"][6]["answer"]
    if total in {"6", "6.5"}:
        assert [item["points"] for item in candidate["questions"][5]["marking"]] == [
            "0.5",
            "0.5",
        ]


def test_depth_schema_and_transport_are_explicit_and_fail_closed():
    from Backend.Core.france.database_depth_authoring import (
        database_depth_selection_prompt,
    )
    from Backend.Core.france.database_depth_prose import (
        database_depth_selection_schema,
        validate_database_depth_selection,
    )
    from Backend.Core.france.provider import response_policy

    contract = build_database_depth_contract(270100)
    prompt = database_depth_selection_prompt(_task(), contract, [])
    schema, budget = response_policy(prompt)
    assert schema == database_depth_selection_schema(contract)
    assert budget <= 2048
    invalid = _selection()
    invalid["question_forms"]["2j"] = "SELECT 1"
    with pytest.raises(ValueError):
        validate_database_depth_selection(contract, invalid)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))


def test_depth_failed_selection_is_retained_and_accepted_replay_is_bound(
    tmp_path, monkeypatch
):
    from Backend.Core.france import database_depth_authoring as authoring

    contract = build_database_depth_contract(270100)
    bad = _selection()
    bad["rubric_forms"]["2a"] = "free prose"
    path = tmp_path / "v2-selection.json"
    raw, evidence = authoring.author_database_depth_selection(
        SelectionClient([bad, _selection()]),
        _task(),
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert evidence["failed_attempts"][0]["response"] == bad
    assert evidence["failed_attempts"][0]["response_sha256"]
    assert "free prose" not in json.dumps(raw)
    assert (
        authoring.replay_database_depth_selection(
            _task(), contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    tampered = deepcopy(evidence)
    tampered["accepted"]["response"]["scene_id"] = "service"
    with pytest.raises(ValueError):
        authoring.replay_database_depth_selection(
            _task(), contract, [], tampered, run_identity=_identity()
        )
    monkeypatch.setattr(authoring, "database_depth_catalogue_digest", lambda: "changed")
    with pytest.raises(ValueError):
        authoring.replay_database_depth_selection(
            _task(), contract, [], evidence, run_identity=_identity()
        )


def test_depth_resume_refuses_changed_model_contract_or_blueprint(tmp_path):
    from Backend.Core.france.database_depth_authoring import (
        author_database_depth_selection,
    )

    path = tmp_path / "v2-selection.json"
    contract = build_database_depth_contract(270100)
    raw, evidence = author_database_depth_selection(
        SelectionClient([_selection()]),
        _task(),
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert raw["id"] == "2"
    assert evidence["accepted"]
    with pytest.raises(ValueError):
        author_database_depth_selection(
            SelectionClient([]),
            _task(),
            build_database_depth_contract(270101),
            [],
            path,
            run_identity=_identity(),
        )
    with pytest.raises(ValueError):
        author_database_depth_selection(
            SelectionClient([]),
            _task("6.5"),
            contract,
            [],
            path,
            run_identity=_identity(),
        )
    changed = {**_identity(), "model_digest": "c" * 64}
    with pytest.raises(ValueError):
        author_database_depth_selection(
            SelectionClient([]), _task(), contract, [], path, run_identity=changed
        )


def test_depth_resume_rejects_tampered_failed_response(tmp_path):
    from Backend.Core.france.database_depth_authoring import (
        author_database_depth_selection,
    )

    path = tmp_path / "v2-failed.json"
    invalid = _selection()
    invalid["question_forms"]["2j"] = "free text"
    with pytest.raises(ValueError):
        author_database_depth_selection(
            SelectionClient([invalid, invalid, invalid]),
            _task(),
            build_database_depth_contract(270100),
            [],
            path,
            run_identity=_identity(),
        )
    saved = json.loads(path.read_text())
    assert len(saved["failed_attempts"]) == 3
    saved["failed_attempts"][0]["response"]["scene_id"] = "service"
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="hash"):
        author_database_depth_selection(
            SelectionClient([]),
            _task(),
            build_database_depth_contract(270100),
            [],
            path,
            run_identity=_identity(),
        )


def test_depth_rejects_credit_or_order_drift():
    from Backend.Core.france.database_depth_prose import render_database_depth_candidate

    contract = build_database_depth_contract(270100)
    plan = _task()["question_blueprint"]
    plan[0]["points"] = "1"
    with pytest.raises(ValueError):
        render_database_depth_candidate(contract, _selection(), plan)
    plan = _task()["question_blueprint"]
    plan[0], plan[1] = plan[1], plan[0]
    with pytest.raises(ValueError):
        render_database_depth_candidate(contract, _selection(), plan)
