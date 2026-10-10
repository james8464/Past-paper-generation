"""V20 finite selection is hash-bound and earlier versions remain distinct."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.graph_resilience_contract import (
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_resilience_prose import (
    graph_resilience_selection_schema,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v19


def _selection():
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


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


def test_v20_prompt_policy_and_replay_bind_every_selection_fact(tmp_path):
    from Backend.Core.france import graph_resilience_authoring as authoring
    from Backend.Core.france.pipeline import _tasks_for_seed_v20
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v20(270100)[0]
    contract = build_graph_resilience_contract(270100)
    references = [{"source_id": "official-fr", "digest": "a" * 64}]
    prompt = authoring.graph_resilience_selection_prompt(task, contract, references)
    assert prompt.startswith("Sélectionne l'exercice 1 v20")
    assert response_policy(prompt)[0] == graph_resilience_selection_schema(contract)
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))

    bad = _selection()
    bad["question_forms"]["1g"] = "model-route"
    path = tmp_path / "v20.json"
    candidate, evidence = authoring.author_graph_resilience_selection(
        _Client([bad, _selection()]),
        task,
        contract,
        references,
        path,
        run_identity=_identity(),
    )
    assert len(evidence["failed_attempts"]) == 1
    assert candidate == authoring.replay_graph_resilience_selection(
        task,
        contract,
        references,
        evidence,
        run_identity=_identity(),
    )
    for change in (
        lambda e: e["accepted"]["response"]["question_forms"].update({"1j": "wrong"}),
        lambda e: e["accepted"].update({"candidate_sha256": "0" * 64}),
        lambda e: e["failed_attempts"][0].update({"response_sha256": "0" * 64}),
        lambda e: e.update({"prose_catalogue_sha256": "0" * 64}),
        lambda e: e.update({"contract_sha256": "0" * 64}),
    ):
        tampered = deepcopy(evidence)
        change(tampered)
        with pytest.raises(ValueError):
            authoring.replay_graph_resilience_selection(
                task,
                contract,
                references,
                tampered,
                run_identity=_identity(),
            )
    with pytest.raises(ValueError):
        authoring.replay_graph_resilience_selection(
            task,
            contract,
            [],
            evidence,
            run_identity=_identity(),
        )
    with pytest.raises(ValueError):
        authoring.replay_graph_resilience_selection(
            task,
            contract,
            references,
            evidence,
            run_identity={**_identity(), "model_digest": "c" * 64},
        )


@pytest.mark.parametrize("seed", [0, 1, 270100, 270101, 999999])
def test_v20_blueprint_changes_only_e1_and_keeps_exact_paper_credit(seed):
    from Backend.Core.france.pipeline import _tasks_for_seed_v20

    old = _tasks_for_seed_v19(seed)
    new = _tasks_for_seed_v20(seed)
    assert len(new) == 3
    assert new[1:] == old[1:]
    assert new[0]["minutes"] == 70
    assert sum(Decimal(task["technical_points"]) for task in new) == Decimal(18)
    assert sum(item["estimated_minutes"] for item in new[0]["question_blueprint"]) == 70
    marks = {item["id"]: item["points"] for item in new[0]["question_blueprint"]}
    assert marks["1a"] == marks["1b"] == "0.25"
    assert marks["1c"] == marks["1g"] == "1"
    assert sum(Decimal(value) for value in marks.values()) == Decimal(
        new[0]["technical_points"]
    )


def test_v20_deterministic_verifier_recomputes_locked_outage():
    from Backend.Core.france.verification import verify_contract

    data = build_graph_resilience_contract(270100).to_dict()
    evidence = {
        "kind": "graph_resilience_contract",
        "contract": data,
        "task_id": "1g",
        "expected": data["expected"]["1g"],
    }
    assert verify_contract(evidence)["state"] == "passed"
    altered = deepcopy(evidence)
    altered["expected"]["cost_after"] += 1
    assert verify_contract(altered)["state"] != "passed"
