"""One bounded database selection is checkpointed and exactly replayable."""

import json
from copy import deepcopy

import pytest

from Backend.Core.france.database_contract import build_database_contract
from Backend.Core.france.pipeline import _tasks_for_seed


def _selection():
    return {
        "scene_id": "atelier",
        "question_forms": {f"2{letter}": f"2{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"2{letter}": f"2{letter}-r1" for letter in "abcdef"},
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
        self.calls = []

    def generate_json(self, prompt):
        self.calls.append(prompt)
        return self.responses.pop(0)


def test_database_selection_transport_policy_and_replay(tmp_path):
    from Backend.Core.france.database_authoring import (
        author_database_selection,
        database_selection_prompt,
        replay_database_selection,
    )
    from Backend.Core.france.database_prose import database_selection_schema
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed(270100)[1]
    contract = build_database_contract(270100)
    prompt = database_selection_prompt(task, contract, [])
    schema, budget = response_policy(prompt)
    assert schema == database_selection_schema(contract)
    assert budget <= 2048
    draft = tmp_path / "db-selection.json"
    client = SelectionClient([_selection()])
    raw, evidence = author_database_selection(
        client, task, contract, [], draft, run_identity=_identity()
    )
    assert len(client.calls) == 1
    assert draft.exists()
    assert raw["id"] == "2"
    assert raw["questions"][2]["answer"].count("JOIN") == 1
    assert (
        replay_database_selection(
            task, contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    assert json.loads(draft.read_text())["accepted"]["response"] == _selection()


def test_database_failed_raw_selection_is_retained_but_not_published(tmp_path):
    from Backend.Core.france.database_authoring import author_database_selection

    task = _tasks_for_seed(270100)[1]
    contract = build_database_contract(270100)
    invalid = _selection()
    invalid["question_forms"]["2a"] = "free model prose"
    draft = tmp_path / "db-selection.json"
    raw, evidence = author_database_selection(
        SelectionClient([invalid, _selection()]),
        task,
        contract,
        [],
        draft,
        run_identity=_identity(),
    )
    assert raw["id"] == "2"
    assert evidence["failed_attempts"][0]["response"] == invalid
    assert evidence["failed_attempts"][0]["response_sha256"]
    assert "free model prose" not in json.dumps(raw)


def test_database_resume_refuses_changed_identity_and_tampered_response(tmp_path):
    from Backend.Core.france.database_authoring import (
        author_database_selection,
        replay_database_selection,
    )

    task = _tasks_for_seed(270100)[1]
    contract = build_database_contract(270100)
    draft = tmp_path / "db-selection.json"
    _, evidence = author_database_selection(
        SelectionClient([_selection()]),
        task,
        contract,
        [],
        draft,
        run_identity=_identity(),
    )
    changed = {**_identity(), "model_digest": "c" * 64}
    with pytest.raises(ValueError, match=r"identity|identit"):
        author_database_selection(
            SelectionClient([]), task, contract, [], draft, run_identity=changed
        )
    tampered = deepcopy(evidence)
    tampered["accepted"]["response"]["scene_id"] = "service"
    with pytest.raises(ValueError, match=r"hash|empreinte|response"):
        replay_database_selection(
            task, contract, [], tampered, run_identity=_identity()
        )


def test_database_resume_refuses_changed_contract_or_catalogue(tmp_path, monkeypatch):
    from Backend.Core.france import database_authoring

    task = _tasks_for_seed(270100)[1]
    contract = build_database_contract(270100)
    draft = tmp_path / "db-selection.json"
    database_authoring.author_database_selection(
        SelectionClient([_selection()]),
        task,
        contract,
        [],
        draft,
        run_identity=_identity(),
    )
    with pytest.raises(ValueError, match=r"identity|identit"):
        database_authoring.author_database_selection(
            SelectionClient([]),
            task,
            build_database_contract(270101),
            [],
            draft,
            run_identity=_identity(),
        )
    monkeypatch.setattr(
        database_authoring, "database_catalogue_digest", lambda: "changed"
    )
    with pytest.raises(ValueError, match=r"identity|identit"):
        database_authoring.author_database_selection(
            SelectionClient([]),
            task,
            contract,
            [],
            draft,
            run_identity=_identity(),
        )
