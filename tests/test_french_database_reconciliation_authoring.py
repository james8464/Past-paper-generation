"""V24 selection is finite, hash-bound, and version-isolated."""

from __future__ import annotations

from copy import deepcopy

import pytest

from Backend.Core.france.database_reconciliation_contract import (
    build_database_reconciliation_contract,
)
from Backend.Core.france.database_reconciliation_prose import (
    database_reconciliation_selection_schema,
)


def _selection():
    return {
        "scene_id": "atelier",
        "question_forms": {f"2{x}": f"2{x}-q1" for x in "abcdefghijkl"},
        "rubric_forms": {f"2{x}": f"2{x}-r1" for x in "abcdefghijkl"},
    }


class _Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate_json(self, _prompt):
        return next(self.responses)


def test_v24_selection_policy_and_replay_bind_all_inputs(tmp_path):
    from Backend.Core.france import database_reconciliation_authoring as authoring
    from Backend.Core.france.pipeline import _tasks_for_seed_v24
    from Backend.Core.france.provider import response_policy

    task = _tasks_for_seed_v24(270100)[1]
    contract = build_database_reconciliation_contract(270100)
    refs = [{"source_id": "official-nsi-programme", "snippet": "programme"}]
    run = {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }
    prompt = authoring.database_reconciliation_selection_prompt(task, contract, refs)
    assert prompt.startswith("Sélectionne l'exercice 2 v24")
    assert response_policy(prompt)[0] == database_reconciliation_selection_schema(
        contract
    )
    with pytest.raises(ValueError):
        response_policy(prompt.replace(contract.digest, "0" * 64))

    invalid = _selection()
    invalid["question_forms"]["2a"] = "free"
    candidate, evidence = authoring.author_database_reconciliation_selection(
        _Client([invalid, _selection()]),
        task,
        contract,
        refs,
        tmp_path / "v24.json",
        run_identity=run,
    )
    assert len(evidence["failed_attempts"]) == 1
    assert candidate == authoring.replay_database_reconciliation_selection(
        task, contract, refs, evidence, run_identity=run
    )
    for field in ("contract_sha256", "prose_catalogue_sha256"):
        altered = deepcopy(evidence)
        altered[field] = "0" * 64
        with pytest.raises(ValueError):
            authoring.replay_database_reconciliation_selection(
                task, contract, refs, altered, run_identity=run
            )
    with pytest.raises(ValueError):
        authoring.replay_database_reconciliation_selection(
            task,
            contract,
            refs,
            evidence,
            run_identity={**run, "model_digest": "c" * 64},
        )


def test_v24_blueprint_preserves_other_exercises_and_exact_credit():
    from decimal import Decimal

    from Backend.Core.france.pipeline import _tasks_for_seed_v23, _tasks_for_seed_v24

    for seed in (0, 1, 270100, 270101):
        old = _tasks_for_seed_v23(seed)
        new = _tasks_for_seed_v24(seed)
        assert new[0] == old[0] and new[2] == old[2]
        assert [q["id"] for q in new[1]["question_blueprint"]] == [
            f"2{x}" for x in "abcdefghijkl"
        ]
        assert sum(Decimal(t["technical_points"]) for t in new) == 18
        assert sum(q["estimated_minutes"] for q in new[1]["question_blueprint"]) == 70
        assert sum(
            Decimal(q["points"]) for q in new[1]["question_blueprint"]
        ) == Decimal(new[1]["technical_points"])
