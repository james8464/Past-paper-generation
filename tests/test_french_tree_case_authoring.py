# Whole E1 checkpoint ownership and strict deterministic verification.

import json
from copy import deepcopy

import pytest

from Backend.Core.france.tree_case_authoring import author_case, replay_case
from Backend.Core.france.tree_case_prose import case_task, render_case
from Backend.Core.france.verification import verify_contract


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_checkpoint_replays_and_corruption_is_preserved_not_overwritten(tmp_path, seed):
    identity = dict(
        prompt_version="fr-nsi-written-2027-v32",
        seed=seed,
        provider="fixture",
        model_digest="fixture",
        implementation_sha256="fixture",
    )
    task = case_task(seed)
    path = tmp_path / "tree.json"
    raw, evidence = author_case(task, [], path, run_identity=identity)
    assert raw == render_case(seed)
    assert author_case(task, [], path, run_identity=identity) == (raw, evidence)
    changed = deepcopy(identity)
    changed["model_digest"] = "different"
    with pytest.raises(ValueError):
        replay_case(task, [], evidence, run_identity=changed)
    corrupt = dict(evidence, model_used=0)
    path.write_text(json.dumps(corrupt), encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ValueError):
        author_case(task, [], path, run_identity=identity)
    assert path.read_bytes() == original


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_contract_rejects_mutated_identity_shape_and_answer(seed):
    contract = render_case(seed)["questions"][0]["verification"]
    assert verify_contract(contract)["state"] == "passed"
    for key, value in (
        ("seed", True),
        ("task_id", "2a"),
        ("version", "wrong"),
        ("case_sha256", "wrong"),
        ("expected", {}),
        ("extra", 1),
    ):
        mutated = deepcopy(contract)
        mutated[key] = value
        assert verify_contract(mutated)["state"] != "passed"
