# V32 integration: whole E1/E2 cases, honest provenance and strict replay

from copy import deepcopy
from decimal import Decimal

import pytest


def test_deterministic_case_rejection_keeps_one_attempt_without_model_retries(
    tmp_path, monkeypatch
):
    import json

    from Backend.Core.france import pipeline
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    calls = []

    def refused(*args, **kwargs):
        calls.append(True)
        raise ValueError("originality fixture rejection")

    monkeypatch.setattr(pipeline, "_originality", refused)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="originality fixture rejection"):
        pipeline.generate_assessment(
            index_path=index,
            client=ControlledTwoOutageFrenchClient(),
            seed=270100,
            checkpoint=checkpoint,
            contract_graph_tree=True,
            contract_authoring_version="v32",
        )
    state = json.loads(checkpoint.read_text())
    assert len(calls) == 1
    assert len(state["failed_attempts"]) == 1
    assert state["failed_attempts"][0]["attempt"] == 1
    assert state["accepted"] == {}


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_v32_package_replays_whole_case_and_rejects_mutations(
    tmp_path, seed, monkeypatch
):
    from Backend.Core.france import pipeline
    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)

    def forbidden_model_authoring(*args, **kwargs):
        pytest.fail("V32 whole cases must not invoke legacy model-selection authoring")

    monkeypatch.setattr(
        pipeline, "author_database_reconciliation_selection", forbidden_model_authoring
    )
    monkeypatch.setattr(
        pipeline, "author_graph_two_outage_selection", forbidden_model_authoring
    )
    monkeypatch.setattr(
        pipeline,
        "author_network_incident_timeline_selection",
        forbidden_model_authoring,
    )
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v32",
    )
    validate_package(package)
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v32"
    assert "database_reconciliation_contract_sha256" not in package["identity"]
    assert "graph_two_outage_contract_sha256" not in package["identity"]
    assert "network_incident_timeline_contract_sha256" not in package["identity"]
    system_evidence = package["evidence"][2]["system_case_evidence"]
    assert system_evidence["origin"] == "application_owned"
    assert system_evidence["model_used"] is False
    for key, value in (("model_used", 0), ("case_sha256", "0" * 64), ("extra", True)):
        altered = deepcopy(package)
        altered["evidence"][2]["system_case_evidence"][key] = value
        with pytest.raises(ValueError):
            validate_package(altered)
    for key in (
        "system_case_sha256",
        "system_case_version",
        "system_case_catalogue_sha256",
    ):
        altered = deepcopy(package)
        altered["identity"][key] = "invalid"
        with pytest.raises(ValueError):
            validate_package(altered)
    assert all(
        q["verification"]["kind"] == "system_case_contract"
        for q in package["exercises"][2]["questions"]
    )
    for field in ("prompt", "answer", "points"):
        altered = deepcopy(package)
        altered["exercises"][2]["questions"][3][field] = "altered"
        altered["evidence"][2]["exercise_sha256"] = digest(altered["exercises"][2])
        altered["evidence"][2]["candidate_sha256"] = digest(altered["exercises"][2])
        with pytest.raises(ValueError):
            validate_package(altered)
    assert all(
        q["verification"]["kind"] == "tree_case_contract"
        for q in package["exercises"][0]["questions"]
    )
    tree_evidence = package["evidence"][0]["tree_case_evidence"]
    assert tree_evidence["origin"] == "application_owned"
    assert tree_evidence["model_used"] is False
    assert "accepted" not in tree_evidence
    for field in (
        "tree_case_sha256",
        "tree_case_version",
        "tree_case_catalogue_sha256",
    ):
        altered = deepcopy(package)
        altered["identity"][field] = "invalid"
        with pytest.raises(ValueError):
            validate_package(altered)
    for key, value in (("model_used", 0), ("case_sha256", "0" * 64), ("extra", True)):
        altered = deepcopy(package)
        altered["evidence"][0]["tree_case_evidence"][key] = value
        with pytest.raises(ValueError):
            validate_package(altered)
    for field in ("prompt", "answer", "points"):
        altered = deepcopy(package)
        altered["exercises"][0]["questions"][6][field] = "altered"
        altered["evidence"][0]["exercise_sha256"] = digest(altered["exercises"][0])
        altered["evidence"][0]["candidate_sha256"] = digest(altered["exercises"][0])
        with pytest.raises(ValueError):
            validate_package(altered)
    exercise = package["exercises"][1]
    evidence = package["evidence"][1]["database_case_evidence"]
    assert evidence["origin"] == "application_owned"
    assert evidence["model_used"] is False
    assert "accepted" not in evidence and "failed_attempts" not in evidence
    assert "database_reconciliation_selection" not in package["evidence"][1]
    assert all(
        q["verification"]["kind"] == "database_case_contract"
        for q in exercise["questions"]
    )
    assert (
        sum(Decimal(q["points"]) for e in package["exercises"] for q in e["questions"])
        == 18
    )
    for field in ("prompt", "answer", "points"):
        altered = deepcopy(package)
        altered["exercises"][1]["questions"][7][field] = "altered"
        # Re-signing the outer data must not bypass closed-content replay
        altered["evidence"][1]["exercise_sha256"] = digest(altered["exercises"][1])
        altered["evidence"][1]["candidate_sha256"] = digest(altered["exercises"][1])
        with pytest.raises(ValueError):
            validate_package(altered)
    altered = deepcopy(package)
    altered["identity"]["database_case_catalogue_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate_package(altered)
    for key, value in (
        ("model_used", True),
        ("case_sha256", "0" * 64),
        ("extra", True),
    ):
        altered = deepcopy(package)
        altered["evidence"][1]["database_case_evidence"][key] = value
        with pytest.raises(ValueError):
            validate_package(altered)

    # a saved checkpoint resumes exactly, without another model call
    class NoCalls:
        provider = ControlledTwoOutageFrenchClient.provider
        model = ControlledTwoOutageFrenchClient.model
        model_digest = ControlledTwoOutageFrenchClient.model_digest

        def generate_json(self, *args, **kwargs):
            pytest.fail("Completed checkpoint unexpectedly called model")

    resumed = generate_assessment(
        index_path=index,
        client=NoCalls(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v32",
    )
    assert resumed == package
    # the fresh V32 path is deterministic app authoring too, not a live model run
    fresh = generate_assessment(
        index_path=index,
        client=NoCalls(),
        seed=seed,
        checkpoint=tmp_path / "fresh.json",
        contract_graph_tree=True,
        contract_authoring_version="v32",
    )
    assert fresh == package
