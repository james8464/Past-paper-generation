"""Positive generation credits are versioned without rewriting retained schemas."""

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from random import Random
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.nsi import Credit, authoring_schema
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import Client, generate
from tests.test_french_reviewed_redraft import ReviewedClient

CURRENT = "fr-nsi-v36-graph-bounds-v1"
LEGACY = "fr-nsi-v36-machine-fields-v1"
LEGACY_SCHEMA_SHA = "8b9ee51b2eac59289ce83e43af9232df351512751a76ccbeef1b7edb589f9766"


def point_field(schema, location):
    return schema["$defs"][location]["properties"]["points"]


@pytest.mark.parametrize("location", ["Credit", "NSIQuestion"])
@pytest.mark.parametrize(
    "value", ["0", "00", "000000", "0.0", "000.0000", "000000.0000"]
)
def test_current_public_request_refuses_zero_points(location, value):
    field = point_field(subject.exercise_request("1", 42, []).schema, location)
    assert not Draft202012Validator(field).is_valid(value)


@pytest.mark.parametrize("value", ["0", "00", "000.0000"])
def test_legacy_machine_schema_zero_admission_does_not_relax_runtime(value):
    field = point_field(authoring_schema(machine_field_constraints=True), "Credit")
    assert Draft202012Validator(field).is_valid(value)
    with pytest.raises(ValidationError, match="strictement positif"):
        Credit.model_validate({"points": value, "criterion": "Résultat justifié."})


@pytest.mark.parametrize("location", ["Credit", "NSIQuestion"])
@pytest.mark.parametrize(
    "value",
    ["1", "0.0001", "000001", "000001.0000", "000000.0001", "000.0100", "999999.9999"],
)
def test_current_generation_keeps_all_positive_machine_forms(location, value):
    field = point_field(subject.exercise_request("1", 42, []).schema, location)
    assert Draft202012Validator(field).is_valid(value)


@pytest.mark.parametrize(
    "value", ["+1", "-1", "0,5", "1e2", "١", "1\n", "1234567", "0.12345", ".5", "1."]
)
def test_positive_schema_retains_existing_ascii_machine_bounds(value):
    field = point_field(
        authoring_schema(machine_field_constraints=True, positive_points=True), "Credit"
    )
    # '$' is deliberately not relied on to enforce runtime fullmatch semantics.
    if value == "1\n":
        with pytest.raises(ValidationError):
            Credit.model_validate({"points": value, "criterion": "Résultat justifié."})
    else:
        assert not Draft202012Validator(field).is_valid(value)


@pytest.mark.parametrize(
    "machine,expected",
    [
        (False, "d9e975acd5bfb8d022577b443c89dd55caf4295b706e74f70e383c74e2e634e8"),
        (True, "81cf0fbe471f86582f784dd072b2c16e006d010b7c9985403607ba03bc927c98"),
    ],
)
def test_existing_authoring_schema_defaults_are_byte_equivalent(machine, expected):
    assert (
        subject._digest(authoring_schema(machine_field_constraints=machine)) == expected
    )


def test_positive_schema_matches_exact_old_grammar_minus_zero():
    validator = Draft202012Validator(
        point_field(subject.exercise_request("1", 42, []).schema, "Credit")
    )
    random = Random(27011110)
    values = ["0" * width for width in range(1, 7)]
    for _ in range(400):
        whole = "".join(str(random.randrange(10)) for _ in range(random.randint(1, 6)))
        count = random.randrange(5)
        fraction = (
            "." + "".join(str(random.randrange(10)) for _ in range(count))
            if count
            else ""
        )
        values.append(whole + fraction)
    for value in values:
        assert validator.is_valid(value) is (Decimal(value) > 0), value


def test_positive_schema_compiles_in_installed_portable_json_grammar():
    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    schema = subject.exercise_request("1", 42, []).schema
    grammar = llguidance.grammar_from("json", json.dumps(_mlx_decoder_schema(schema)))
    assert not llguidance.LLMatcher.validate_grammar(grammar)


def test_explicit_legacy_request_and_round_keep_exact_existing_hashes():
    request = subject.exercise_request("1", 42, [], authoring_schema_policy=LEGACY)
    assert (
        sha256(request.prompt.encode()).hexdigest()
        == "423f449232625fc89e728149d65302f90c80274243b0738e498730aca4561ac5"
    )
    assert subject._digest(request.schema) == LEGACY_SCHEMA_SHA
    _, identity = subject._round_request(
        SimpleNamespace(provider="ollama"),
        {"primary_topic": "algorithmique", "references": []},
        42,
        "1",
        1,
        set(),
        False,
        None,
        authoring_schema_policy=LEGACY,
    )
    assert identity == {
        "attempt": 1,
        "generation_seed": 43,
        "operation": "french_nsi_authoring",
        "output_budget": 8192,
        "prompt_sha256": "a5d2cb2ac6a319e07fe770f8a1b7fd761af426dff86aa91a69ca02b0b62bceb3",
        "review_seed": 143,
        "schema_sha256": LEGACY_SCHEMA_SHA,
        "temperature": 0.6,
    }


@pytest.mark.parametrize("policy", [None, True, False, "unknown", 1])
def test_unknown_explicit_request_policies_refuse(policy):
    with pytest.raises(ValueError, match="schéma"):
        subject.exercise_request("1", 42, [], authoring_schema_policy=policy)


@pytest.fixture(scope="module")
def package(tmp_path_factory):
    return generate(tmp_path_factory.mktemp("positive-points-owned"), Client())


def test_new_generation_records_policy_and_replays_without_mutation(package):
    assert package["identity"]["authoring_schema_policy"] == CURRENT
    before = json.dumps(package, ensure_ascii=False, sort_keys=True)
    assert subject.validate_package(package)
    assert json.dumps(package, ensure_ascii=False, sort_keys=True) == before


@pytest.mark.parametrize("policy", [None, True, False, "unknown", LEGACY])
def test_explicit_invalid_package_policy_cannot_replay(package, policy):
    changed = deepcopy(package)
    changed["identity"]["authoring_schema_policy"] = policy
    with pytest.raises(ValueError, match="schéma"):
        subject.validate_package(changed)


def test_removing_current_policy_cannot_launder_current_round_hashes(package):
    changed = deepcopy(package)
    changed["identity"].pop("authoring_schema_policy")
    with pytest.raises(ValueError, match="nouvelle rédaction"):
        subject.validate_package(changed)


def test_retained_absent_policy_reconstructs_legacy_rounds_without_relabelling(
    monkeypatch, tmp_path
):
    original_round = subject._round_request
    original_identity = subject._recovery_identity

    def legacy_round(*args, **kwargs):
        return original_round(*args, **{**kwargs, "authoring_schema_policy": LEGACY})

    def legacy_identity(*args, **kwargs):
        return original_identity(*args, **{**kwargs, "authoring_schema_policy": LEGACY})

    # Recreate the earlier generation selectors using owned, deterministic clients.
    # Golden schema/prompt hashes above independently pin the retained request.
    with monkeypatch.context() as context:
        context.setattr(subject, "_round_request", legacy_round)
        context.setattr(subject, "_recovery_identity", legacy_identity)
        retained = generate(tmp_path, Client())
    assert "authoring_schema_policy" not in retained["identity"]
    before = json.dumps(retained, ensure_ascii=False, sort_keys=True)
    assert subject.validate_package(retained)
    assert json.dumps(retained, ensure_ascii=False, sort_keys=True) == before
    changed = deepcopy(retained)
    changed["identity"]["authoring_schema_policy"] = CURRENT
    with pytest.raises(ValueError, match="nouvelle rédaction"):
        subject.validate_package(changed)


def test_rejected_round_recovery_carries_and_checks_the_schema_policy(tmp_path):
    client = ReviewedClient(refuse_rounds=(1, 2))
    with pytest.raises(GenerationEvidenceError) as caught:
        generate(tmp_path, client)
    details = caught.value.details
    assert details["recovery_identity"]["authoring_schema_policy"] == CURRENT
    before = json.dumps(details, sort_keys=True, ensure_ascii=False)
    subject.validate_rejected_rounds(details)
    assert json.dumps(details, sort_keys=True, ensure_ascii=False) == before
    for value in (None, True, "unknown", LEGACY):
        changed = deepcopy(details)
        changed["recovery_identity"]["authoring_schema_policy"] = value
        with pytest.raises(ValueError, match="schéma"):
            subject.validate_rejected_rounds(changed)
    changed = deepcopy(details)
    changed["recovery_identity"].pop("authoring_schema_policy")
    with pytest.raises(ValueError, match="nouvelle rédaction"):
        subject.validate_rejected_rounds(changed)


def test_retained_rejected_recovery_keeps_absent_policy(monkeypatch, tmp_path):
    original_round = subject._round_request
    original_identity = subject._recovery_identity

    def legacy_round(*args, **kwargs):
        return original_round(*args, **{**kwargs, "authoring_schema_policy": LEGACY})

    def legacy_identity(*args, **kwargs):
        return original_identity(*args, **{**kwargs, "authoring_schema_policy": LEGACY})

    with monkeypatch.context() as context:
        context.setattr(subject, "_round_request", legacy_round)
        context.setattr(subject, "_recovery_identity", legacy_identity)
        with pytest.raises(GenerationEvidenceError) as caught:
            generate(tmp_path, ReviewedClient(refuse_rounds=(1, 2)))
    retained = caught.value.details
    assert "authoring_schema_policy" not in retained["recovery_identity"]
    before = json.dumps(retained, ensure_ascii=False, sort_keys=True)
    subject.validate_rejected_rounds(retained)
    assert json.dumps(retained, ensure_ascii=False, sort_keys=True) == before
