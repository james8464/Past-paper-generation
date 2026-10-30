"""The owner may regenerate one complete author after a typed provider refusal."""

import hashlib
import io
import json
import traceback

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import (
    GenerationEvidenceError,
    save_failure_diagnostic,
)
from Backend.Core.providers import HostedLLMClient
from tests.test_deepseek_provider import KEY, response
from tests.test_french_llm_pipeline import Client, raw_exercise
from tests.test_nsi_pipeline import make_index


def transport(monkeypatch, authors=(), *, envelope_change=None, transport_error=None):
    calls = []
    pending = iter(authors)
    fixture = Client()

    def send(_url, data, _headers, **options):
        payload = json.loads(data)
        calls.append((payload, options))
        if transport_error is not None:
            raise transport_error
        schema = payload["text"]["format"]["schema"]
        request = subject.GenerationRequest(
            payload["input"], "french_nsi_authoring", schema
        )
        value = fixture.generate_request(request)
        if "id" in schema["properties"]:
            value = next(pending, value)
        text = (
            value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        )
        envelope = response()
        envelope["output"][1]["content"][0]["text"] = text
        if envelope_change is not None:
            envelope_change(envelope)
        return io.BytesIO(json.dumps(envelope).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    return calls


def client():
    return HostedLLMClient(provider="deepseek", model="deepseek-flash", api_key=KEY)


def make_package(tmp_path, model):
    index = tmp_path / "references.sqlite"
    make_index(index)
    return subject.generate(index_path=index, client=model, seed=42)


def resign(package):
    package["identity"]["content_sha256"] = subject._digest(
        {k: v for k, v in package.items() if k != "identity"}
    )


@pytest.mark.parametrize("failure", ["json", "schema"])
def test_actual_hosted_provider_regenerates_once_before_blind_review(
    monkeypatch, tmp_path, failure
):
    invalid = '{"secret":"' + KEY + '",}' if failure == "json" else {"private": KEY}
    calls = transport(monkeypatch, [invalid, raw_exercise()])
    package = make_package(tmp_path, client())
    assert len(calls) == 10
    assert [
        "id" in payload["text"]["format"]["schema"]["properties"]
        for payload, _ in calls[:3]
    ] == [True, True, False]
    assert all(options["attempts"] == 1 for _, options in calls)
    first, second = (item[0] for item in calls[:2])
    assert first["text"] == second["text"]
    assert first["model"] == second["model"]
    assert first["max_output_tokens"] == second["max_output_tokens"]
    assert first["reasoning"] == second["reasoning"]
    assert "REGENERATION" in second["input"]
    assert KEY not in second["input"]
    record = package["authoring_attempts"][0]
    assert record["attempts"] == 2
    rejected = record["rejected"][0]
    assert rejected["kind"] == "provider_output_contract_v1"
    assert rejected["provider"] == "deepseek"
    assert rejected["failure"] == (
        "invalid_json" if failure == "json" else "schema_mismatch"
    )
    original = (
        invalid if isinstance(invalid, str) else json.dumps(invalid, ensure_ascii=False)
    )
    assert rejected["response_sha256"] == hashlib.sha256(original.encode()).hexdigest()
    assert "response" not in rejected and KEY not in json.dumps(rejected)
    assert subject.validate_package(package)


def test_direct_provider_still_makes_only_one_call(monkeypatch):
    calls = transport(monkeypatch, ['{"id":1,}'])
    with pytest.raises(GenerationEvidenceError) as caught:
        client().generate_request(subject.exercise_request("1", 42, []))
    assert type(caught.value).__name__ == "ProviderOutputContractError"
    assert len(calls) == 1


def test_second_provider_refusal_stops_without_blind_calls_and_keeps_private_hashes(
    monkeypatch, tmp_path
):
    calls = transport(monkeypatch, ['{"value":"' + KEY + '",}'] * 2)
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._author(client(), subject.exercise_request("1", 42, []), "1")
    assert len(calls) == 2
    assert all(
        "id" in payload["text"]["format"]["schema"]["properties"]
        for payload, _ in calls
    )
    assert len(caught.value.details["attempts"]) == 2
    public = str(caught.value)
    private = json.dumps(caught.value.details)
    assert KEY not in public + private
    assert KEY not in "".join(traceback.format_exception(caught.value))
    assert "raw_response" not in private
    path = save_failure_diagnostic(tmp_path, caught.value, secrets=(KEY,))
    assert path is not None and path.stat().st_size < 8192


@pytest.mark.parametrize("provider_first", [False, True])
def test_mixed_local_and_provider_errors_share_the_same_two_attempt_budget(
    monkeypatch, provider_first
):
    local = raw_exercise()
    local["questions"][0]["answer"] = "def total():\n    return 1"
    invalid = '{"id":1,}'
    calls = transport(
        monkeypatch, [invalid, local] if provider_first else [local, invalid]
    )
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._author(client(), subject.exercise_request("1", 42, []), "1")
    assert len(calls) == 2
    attempts = caught.value.details["attempts"]
    assert len(attempts) == 2
    assert (
        sum(item.get("kind") == "provider_output_contract_v1" for item in attempts) == 1
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda raw: raw.update(status="incomplete"),
        lambda raw: raw.update(model="another-model"),
        lambda raw: raw.update(usage={}),
        lambda raw: raw.update(output=[]),
        lambda raw: raw["output"][1].update(role="user"),
        lambda raw: raw["output"][1]["content"][0].update(text="x" * 1_048_577),
    ],
)
def test_envelope_identity_usage_and_oversize_failures_remain_hard_single_call(
    monkeypatch, change
):
    calls = transport(monkeypatch, envelope_change=change)
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._author(client(), subject.exercise_request("1", 42, []), "1")
    assert type(caught.value).__name__ != "ProviderOutputContractError"
    assert len(calls) == 1


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("transport failed"),
        InterruptedError("cancelled"),
        GenerationEvidenceError("context failed", details={"kind": "context_capacity"}),
    ],
)
def test_transport_cancellation_and_context_errors_propagate_without_regeneration(
    monkeypatch, error
):
    calls = transport(monkeypatch, transport_error=error)
    with pytest.raises(type(error)) as caught:
        subject._author(client(), subject.exercise_request("1", 42, []), "1")
    assert caught.value is error
    assert len(calls) == 1


def test_unsafe_code_is_not_a_provider_format_regeneration(monkeypatch):
    raw = raw_exercise()
    raw["questions"][0]["answer"] = "```python\nimport os\n```"
    calls = transport(monkeypatch, [raw])
    with pytest.raises(ValueError, match="non autorisé"):
        subject._author(client(), subject.exercise_request("1", 42, []), "1")
    assert len(calls) == 1


def test_provider_contract_failure_in_blind_stage_is_not_regenerated(monkeypatch):
    calls = transport(monkeypatch)
    original = __import__(
        "Backend.Core.providers", fromlist=["urllib_request"]
    ).urllib_request

    def bad_blind(url, data, headers, **options):
        payload = json.loads(data)
        if "answers" in payload["text"]["format"]["schema"]["properties"]:
            envelope = response()
            envelope["output"][1]["content"][0]["text"] = '{"answers":{},}'
            calls.append((payload, options))
            return io.BytesIO(json.dumps(envelope).encode())
        return original(url, data, headers, **options)

    monkeypatch.setattr("Backend.Core.providers.urllib_request", bad_blind)
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    with pytest.raises(GenerationEvidenceError):
        subject._review(client(), exercise, 42, [])
    assert len(calls) == 1


def test_negative_semantic_review_is_not_a_format_regeneration(monkeypatch):
    def reject(envelope):
        part = envelope["output"][1]["content"][0]
        candidate = json.loads(part["text"])
        if "1" in candidate and isinstance(candidate["1"], dict):
            candidate["1"]["correct"] = False
            part["text"] = json.dumps(candidate)

    calls = transport(monkeypatch, envelope_change=reject)
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    with pytest.raises(GenerationEvidenceError, match="refuse") as caught:
        subject._review(client(), exercise, 42, [])
    assert type(caught.value).__name__ != "ProviderOutputContractError"
    assert len(calls) == 2


def test_invalid_owned_schema_refuses_before_any_physical_call(monkeypatch):
    from jsonschema.exceptions import SchemaError

    calls = transport(monkeypatch)
    request = subject.GenerationRequest(
        "Write a draft.",
        "french_nsi_authoring",
        {"type": "object", "maxProperties": "invalid"},
    )
    with pytest.raises(SchemaError):
        subject._author(client(), request, "1")
    assert not calls


def test_existing_local_rejection_record_still_rehashes_its_original_draft(
    monkeypatch, tmp_path
):
    original = raw_exercise()
    original["questions"][0]["answer"] = "def total():\n    return 1"
    transport(monkeypatch, [original, raw_exercise()])
    package = make_package(tmp_path, client())
    rejected = package["authoring_attempts"][0]["rejected"][0]
    assert set(rejected) == {"response", "response_sha256", "issue"}
    assert rejected["response"] == original
    assert rejected["response_sha256"] == subject._digest(original)
    assert subject.validate_package(package)


@pytest.mark.parametrize(
    "change", ["provider", "failure", "hash", "raw", "path", "issue"]
)
def test_opaque_failure_evidence_is_strict_on_replay(monkeypatch, tmp_path, change):
    transport(monkeypatch, ['{"id":1,}', raw_exercise()])
    package = make_package(tmp_path, client())
    rejected = package["authoring_attempts"][0]["rejected"][0]
    if change == "provider":
        rejected["provider"] = "ollama"
    elif change == "failure":
        rejected["failure"] = "correctness"
    elif change == "hash":
        rejected["response_sha256"] = "bad"
    elif change == "raw":
        rejected["response"] = {"hidden": "not allowed"}
    elif change == "path":
        rejected["schema_path"] = [KEY * 100]
    else:
        rejected["issue"] = KEY
    resign(package)
    with pytest.raises(ValueError):
        subject.validate_package(package)
