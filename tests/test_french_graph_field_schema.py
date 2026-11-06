"""Generation graph bounds align with the existing typed material admission."""

import json
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.nsi import NSIWeightedGraphMaterial, authoring_schema
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import Client, generate
from tests.test_french_reviewed_redraft import ReviewedClient

CURRENT = "fr-nsi-v36-graph-bounds-v1"
POSITIVE = "fr-nsi-v36-positive-points-v1"


def graph():
    return {
        "kind": "weighted_graph",
        "id": "graphe",
        "title": "Réseau public",
        "nodes": ["A", "B"],
        "edges": [["A", "B", 1]],
        "directed": False,
    }


def graph_schema():
    return subject.exercise_request("1", 42, []).schema["$defs"][
        "NSIWeightedGraphMaterial"
    ]


@pytest.mark.parametrize("weight", [-1, 1000001])
def test_public_schema_refuses_weights_already_refused_by_runtime(weight):
    raw = graph()
    raw["edges"][0][2] = weight
    with pytest.raises(ValidationError):
        NSIWeightedGraphMaterial.model_validate(raw)
    assert not Draft202012Validator(graph_schema()).is_valid(raw)


@pytest.mark.parametrize("weight", [-1, 1000001])
def test_shortest_path_verification_uses_the_same_bounded_edge_schema(weight):
    schema = subject.exercise_request("1", 42, []).schema
    material_edges = schema["$defs"]["NSIWeightedGraphMaterial"]["properties"]["edges"]
    verification = schema["$defs"]["NSIQuestion"]["properties"]["verification"]
    shortest = next(
        case
        for case in verification["oneOf"]
        if case["properties"]["kind"]["const"] == "shortest_path"
    )
    assert shortest["properties"]["edges"] == material_edges
    assert not Draft202012Validator(shortest["properties"]["edges"]).is_valid(
        [["A", "B", weight]]
    )


@pytest.mark.parametrize("label", ["", " ", "\t", "x" * 25])
@pytest.mark.parametrize("location", ["node", "start", "end"])
def test_public_schema_refuses_empty_or_oversized_graph_labels(label, location):
    raw = graph()
    if location == "node":
        raw["nodes"][0] = label
        raw["edges"][0][0] = label
    else:
        raw["edges"][0][0 if location == "start" else 1] = label
    with pytest.raises(ValidationError):
        NSIWeightedGraphMaterial.model_validate(raw)
    assert not Draft202012Validator(graph_schema()).is_valid(raw)


@pytest.mark.parametrize("weight", [0, 1, 1000000])
@pytest.mark.parametrize("label", ["A", "x" * 24, "salle A", " A "])
def test_valid_field_boundaries_and_existing_label_whitespace_are_preserved(
    weight, label
):
    raw = graph()
    raw.update(nodes=[label, "B"], edges=[[label, "B", weight]])
    before = deepcopy(raw)
    assert Draft202012Validator(graph_schema()).is_valid(raw)
    assert NSIWeightedGraphMaterial.model_validate(raw)
    assert raw == before


@pytest.mark.parametrize(
    "mutation", ["duplicate-node", "self-loop", "unknown-endpoint", "reverse-duplicate"]
)
def test_runtime_still_checks_cross_field_graph_relations(mutation):
    raw = graph()
    if mutation == "duplicate-node":
        raw["nodes"][1] = "A"
    elif mutation == "self-loop":
        raw["edges"][0][1] = "A"
    elif mutation == "unknown-endpoint":
        raw["edges"][0][1] = "C"
    else:
        raw["edges"].append(["B", "A", 1])
    # These relational constraints remain runtime checks, not schema promises.
    assert Draft202012Validator(graph_schema()).is_valid(raw)
    with pytest.raises(ValidationError):
        NSIWeightedGraphMaterial.model_validate(raw)


def test_old_positive_schema_and_request_round_hashes_are_unchanged():
    assert (
        subject._digest(
            authoring_schema(machine_field_constraints=True, positive_points=True)
        )
        == "2a88f8d0e74e24ddacafe17edf5fa431bc0b373a83dd76770e040f872cc6219d"
    )
    request = subject.exercise_request("1", 42, [], authoring_schema_policy=POSITIVE)
    assert (
        sha256(request.prompt.encode()).hexdigest()
        == "28ea72769e531913bf33c579a545b9ac3a0d6e5c9a9c17e5e9ba08ff9f1c7531"
    )
    assert (
        subject._digest(request.schema)
        == "185553220e3cf0437a56d1ad136bb68350d77653cba9ed9270045ebd3f15c77d"
    )
    _, identity = subject._round_request(
        SimpleNamespace(provider="ollama"),
        {"primary_topic": "algorithmique", "references": []},
        42,
        "1",
        1,
        set(),
        False,
        None,
        authoring_schema_policy=POSITIVE,
    )
    assert identity == {
        "prompt_sha256": "b143b0155add34d0ba92c533ce617dbe4ffbd8b71fd3ab4a102e3880dca64151",
        "schema_sha256": "185553220e3cf0437a56d1ad136bb68350d77653cba9ed9270045ebd3f15c77d",
        "generation_seed": 43,
        "attempt": 1,
        "operation": "french_nsi_authoring",
        "temperature": 0.6,
        "output_budget": 8192,
        "review_seed": 143,
    }


def test_current_schema_compiles_with_installed_portable_grammar():
    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    grammar = llguidance.grammar_from(
        "json",
        json.dumps(_mlx_decoder_schema(subject.exercise_request("1", 42, []).schema)),
    )
    assert not llguidance.LLMatcher.validate_grammar(grammar)


@pytest.mark.parametrize("refused", [False, True])
def test_retained_explicit_positive_policy_replays_without_relabelling(
    monkeypatch, tmp_path, refused
):
    original_round = subject._round_request
    original_identity = subject._recovery_identity

    def positive_round(*args, **kwargs):
        return original_round(*args, **{**kwargs, "authoring_schema_policy": POSITIVE})

    def positive_identity(*args, **kwargs):
        return original_identity(
            *args, **{**kwargs, "authoring_schema_policy": POSITIVE}
        )

    with monkeypatch.context() as context:
        context.setattr(subject, "_round_request", positive_round)
        context.setattr(subject, "_recovery_identity", positive_identity)
        if refused:
            with pytest.raises(GenerationEvidenceError) as caught:
                generate(tmp_path, ReviewedClient(refuse_rounds=(1, 2)))
            retained = caught.value.details
        else:
            retained = generate(tmp_path, Client())
    key = "recovery_identity" if refused else "identity"
    validate = subject.validate_rejected_rounds if refused else subject.validate_package
    assert retained[key]["authoring_schema_policy"] == POSITIVE
    before = json.dumps(retained, sort_keys=True, ensure_ascii=False)
    validate(retained)
    assert json.dumps(retained, sort_keys=True, ensure_ascii=False) == before
    changed = deepcopy(retained)
    changed[key]["authoring_schema_policy"] = CURRENT
    with pytest.raises(ValueError):
        validate(changed)


def test_new_generation_records_current_graph_policy(tmp_path):
    package = generate(tmp_path, Client())
    assert package["identity"]["authoring_schema_policy"] == CURRENT
    for policy in (POSITIVE, None, True, "unknown"):
        changed = deepcopy(package)
        changed["identity"]["authoring_schema_policy"] = policy
        with pytest.raises(ValueError):
            subject.validate_package(changed)


def test_removing_current_policy_does_not_relabel_current_rounds_as_legacy(tmp_path):
    package = generate(tmp_path, Client())
    package["identity"].pop("authoring_schema_policy")
    with pytest.raises(ValueError, match="nouvelle rédaction"):
        subject.validate_package(package)
