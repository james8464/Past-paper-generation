# strict E3 provenance/checkpoint binding and independently rebuilt contracts

import json
from copy import deepcopy

import pytest

from Backend.Core.france.system_case_authoring import author_case, replay_case
from Backend.Core.france.system_case_prose import case_task, render_case
from Backend.Core.france.verification import verify_contract


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_e3_checkpoint_rejects_incompatible_evidence_without_overwriting(
    tmp_path, seed
):
    identity = dict(
        prompt_version="fr-nsi-written-2027-v32",
        seed=seed,
        provider="fixture",
        model_digest="fixture",
        implementation_sha256="fixture",
    )
    task = case_task(seed)
    assert task["archetype_id"] == "network-operation-and-security"
    path = tmp_path / "system.json"
    raw, evidence = author_case(task, [], path, run_identity=identity)
    assert raw == render_case(seed)
    assert author_case(task, [], path, run_identity=identity) == (raw, evidence)
    changed = dict(identity, model_digest="different")
    with pytest.raises(ValueError):
        replay_case(task, [], evidence, run_identity=changed)
    path.write_text(json.dumps(dict(evidence, model_used=0)), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        author_case(task, [], path, run_identity=identity)
    assert path.read_bytes() == before


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_e3_contract_rebuilds_and_rejects_tampered_truth(seed):
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
        changed = deepcopy(contract)
        changed[key] = value
        assert verify_contract(changed)["state"] != "passed"
