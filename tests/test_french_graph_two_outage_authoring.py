# V25 selection is finite, hash-bound, and isolated from V24.

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from importlib import import_module

import pytest

from Backend.Core.france.graph_two_outage_contract import (
    build_graph_two_outage_contract,
)
from Backend.Core.france.graph_two_outage_prose import (
    graph_two_outage_selection_schema,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v24


def _authoring():
    return import_module("Backend.Core.france.graph_two_outage_authoring")


def _selection() -> dict:
    return {
        "scene_id": "service",
        "question_forms": {f"1{x}": f"1{x}-q1" for x in "abcdefghij"},
        "rubric_forms": {f"1{x}": f"1{x}-r1" for x in "abcdefghij"},
    }


class _Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate_json(self, _prompt):
        return next(self.responses)


def _identity() -> dict:
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


def test_v25_selection_policy_and_replay_bind_every_fact(tmp_path) -> None:
    from Backend.Core.france.provider import response_policy

    authoring = _authoring()
    task = import_module("Backend.Core.france.pipeline")._tasks_for_seed_v25(270100)[0]
    contract = build_graph_two_outage_contract(270100)
    references = [{"source_id": "official-fr", "digest": "a" * 64}]
    prompt = authoring.graph_two_outage_selection_prompt(task, contract, references)
    assert prompt.startswith("Sélectionne l'exercice 1 v25")
    assert response_policy(prompt)[0] == graph_two_outage_selection_schema(contract)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))

    bad = _selection()
    bad["question_forms"]["1g"] = "model-route"
    candidate, evidence = authoring.author_graph_two_outage_selection(
        _Client([bad, _selection()]),
        task,
        contract,
        references,
        tmp_path / "v25.json",
        run_identity=_identity(),
    )
    assert len(evidence["failed_attempts"]) == 1
    assert candidate == authoring.replay_graph_two_outage_selection(
        task, contract, references, evidence, run_identity=_identity()
    )
    for change in (
        lambda e: e.update({"untrusted_extra": "ignored"}),
        lambda e: e["accepted"]["response"]["question_forms"].update({"1j": "wrong"}),
        lambda e: e["accepted"].update({"candidate_sha256": "0" * 64}),
        lambda e: e["failed_attempts"][0].update({"response_sha256": "0" * 64}),
        lambda e: e.update({"prose_catalogue_sha256": "0" * 64}),
        lambda e: e.update({"contract_sha256": "0" * 64}),
    ):
        altered = deepcopy(evidence)
        change(altered)
        with pytest.raises(ValueError):
            authoring.replay_graph_two_outage_selection(
                task, contract, references, altered, run_identity=_identity()
            )
    with pytest.raises(ValueError):
        authoring.replay_graph_two_outage_selection(
            task, contract, [], evidence, run_identity=_identity()
        )


@pytest.mark.parametrize("seed", [0, 1, 270100, 270102, 999999])
def test_v25_blueprint_only_changes_e1_and_preserves_total(seed: int) -> None:
    old = _tasks_for_seed_v24(seed)
    new = import_module("Backend.Core.france.pipeline")._tasks_for_seed_v25(seed)
    assert len(new) == 3
    assert new[1:] == old[1:]
    assert [item["id"] for item in new[0]["question_blueprint"]] == [
        f"1{x}" for x in "abcdefghij"
    ]
    assert [item["estimated_minutes"] for item in new[0]["question_blueprint"]] == [
        3,
        3,
        10,
        8,
        8,
        10,
        11,
        6,
        5,
        6,
    ]
    assert new[0]["question_blueprint"][5]["points"] == "1"
    assert new[0]["question_blueprint"][6]["points"] == "0.5"
    assert sum(Decimal(task["technical_points"]) for task in new) == Decimal(18)
    assert sum(item["estimated_minutes"] for item in new[0]["question_blueprint"]) == 70


def test_v25_deterministic_verifier_recomputes_both_outages() -> None:
    from Backend.Core.france.verification import verify_contract

    facts = build_graph_two_outage_contract(270100).to_dict()
    evidence = {
        "kind": "graph_two_outage_contract",
        "contract": facts,
        "task_id": "1g",
        "expected": facts["expected"]["1g"],
    }
    assert verify_contract(evidence)["state"] == "passed"
    altered = deepcopy(evidence)
    altered["expected"]["cost_after"] = 1
    assert verify_contract(altered)["state"] != "passed"
