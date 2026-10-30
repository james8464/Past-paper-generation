"""Apple's system model has a distinct local provider and strict transport."""

import json
from pathlib import Path

import pytest

from Backend.Core import apple_intelligence as service
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.providers import HostedLLMClient


def reply(payload, output='{"answer":4}'):
    return {
        "protocol_version": 1,
        "request_id": payload["request_id"],
        "provider": service.PROVIDER,
        "model": service.MODEL,
        "os_version": "26.4",
        "available": True,
        "context_size": 8192,
        "french_supported": True,
        "status": "ok",
        "generation_mode": "structured_text",
        "input_token_count": 100,
        "raw_output": output,
    }


@pytest.fixture
def transport(monkeypatch):
    seen = []

    def roundtrip(payload):
        seen.append(payload)
        for field in ("questions", "reviews"):
            if field in payload["schema"].get("properties", {}):
                return reply(payload, json.dumps({field: [{"id": "1/1/1"}]}))
        return reply(payload)

    monkeypatch.setattr(service, "roundtrip", roundtrip)
    return seen


def test_system_provider_routes_typed_request_without_using_mlx(monkeypatch):
    client = HostedLLMClient(
        provider="apple_intelligence", model="apple-system-on-device", api_key=""
    )
    seen = []

    def generate(prompt, *, request=None):
        seen.append((prompt, request))
        return {"answer": 4}

    monkeypatch.setattr(client, "_apple_intelligence", generate, raising=False)
    request = GenerationRequest(
        "Compute 2+2", "solver", {"type": "object"}, output_budget=1024
    )
    assert client.generate_request(request) == {"answer": 4}
    assert seen == [(request.prompt, request)]
    assert client.parallel_generation_workers == 1


def test_system_provider_is_known_without_reinterpreting_legacy_apple():
    from Backend.Core.generator_registry import KNOWN_PROVIDERS

    assert {"apple", "apple_intelligence"} <= KNOWN_PROVIDERS


@pytest.mark.parametrize(
    "phase,expected", [("author", 4096), ("blind", 2048), ("review", 2048)]
)
def test_french_system_model_budget_reserves_room_for_context(phase, expected):
    from Backend.Core.france.llm_pipeline import _phase_output_budget

    client = HostedLLMClient(
        provider="apple_intelligence", model="apple-system-on-device", api_key=""
    )
    assert _phase_output_budget(client, phase) == expected


def test_complete_original_schema_and_local_identity_are_preserved(transport):
    client = HostedLLMClient(
        provider=service.PROVIDER, model=service.MODEL, api_key="not-sent"
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["answer"],
        "properties": {"answer": {"type": "integer", "const": 4}},
    }
    request = GenerationRequest(
        "Original source and full instructions", "solver", schema, output_budget=1024
    )
    assert client.generate_request(request) == {"answer": 4}
    assert len(transport) == 1
    assert transport[0]["prompt"] == service.complete_prompt(request.prompt, schema)
    assert transport[0]["prompt"].startswith(request.prompt)
    assert transport[0]["prompt_includes_schema"] is True
    assert transport[0]["schema"] == schema
    assert transport[0]["schema_mode"] == "structured_text"
    assert transport[0]["max_output_tokens"] == 1024
    assert "not-sent" not in json.dumps(transport)
    assert client.usage_records[-1]["schema_validation"] == "postvalidated_original"


@pytest.mark.parametrize(
    "operation,cap",
    [
        ("authoring", 4096),
        ("review", 2048),
        ("solver", 2048),
        ("batch_review", 2048),
        ("difficulty", 2048),
    ],
)
def test_explicit_system_model_caps_are_recorded_not_unbounded(
    operation, cap, transport
):
    client = HostedLLMClient(provider=service.PROVIDER, model=service.MODEL, api_key="")
    schema = {"type": "object"}
    expected_ids = ()
    if operation in {"authoring", "batch_review"}:
        field = "questions" if operation == "authoring" else "reviews"
        schema.update(
            properties={
                field: {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "string", "enum": ["1/1/1"]}},
                    },
                }
            },
            required=[field],
        )
        expected_ids = ("1/1/1",)
    request = GenerationRequest(
        "Generate bounded JSON",
        operation,
        schema,
        output_budget=8192,
        expected_ids=expected_ids,
    )
    assert client.generate_request(request)
    assert transport[0]["max_output_tokens"] == cap
    assert client.usage_records[-1]["requested_output_budget"] == 8192


@pytest.mark.parametrize(
    "raw",
    [
        '```json\n{"answer":4}\n```',
        "[]",
        '{"answer":4}{"answer":4}',
        '{"answer":4,"answer":5}',
        '{"answer":NaN}',
        '{"answer":1e999}',
    ],
)
def test_invalid_or_nonfinite_output_is_not_salvaged_or_retried(monkeypatch, raw):
    calls = []

    def bad(payload):
        calls.append(payload)
        return reply(payload, raw)

    monkeypatch.setattr(service, "roundtrip", bad)
    client = HostedLLMClient(provider=service.PROVIDER, model=service.MODEL, api_key="")
    with pytest.raises(ValueError):
        client.generate_request(
            GenerationRequest("Original", "solver", {"type": "object"})
        )
    assert len(calls) == 1


def test_original_schema_patterns_and_required_values_are_checked_after_generation(
    monkeypatch,
):
    monkeypatch.setattr(
        service, "roundtrip", lambda payload: reply(payload, '{"answer":"wrong"}')
    )
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string", "pattern": "^correct$"}},
    }
    with pytest.raises(GenerationEvidenceError, match="invalid structured output"):
        service.generate(
            "Original", schema, budget=512, temperature=0.2, locale="en_GB"
        )


@pytest.mark.parametrize("inputs", [True, None, 8000, 0])
def test_missing_or_over_capacity_counts_never_publish_candidate(monkeypatch, inputs):
    monkeypatch.setattr(
        service,
        "roundtrip",
        lambda payload: {**reply(payload), "input_token_count": inputs},
    )
    with pytest.raises(ValueError, match="capacity-safe"):
        service.generate(
            "Original", {"type": "object"}, budget=512, temperature=0.2, locale="fr_FR"
        )


def test_wrong_model_is_not_reinterpreted_as_mlx(transport):
    client = HostedLLMClient(
        provider=service.PROVIDER, model="mlx-community/model", api_key=""
    )
    with pytest.raises(ValueError, match="system model"):
        client.generate_request(
            GenerationRequest("Original", "solver", {"type": "object"})
        )
    assert not transport


def test_legacy_apple_still_routes_to_mlx(monkeypatch):
    client = HostedLLMClient(provider="apple", model="cached-mlx-model", api_key="")
    seen = []
    monkeypatch.setattr(
        client, "_apple", lambda prompt, **kwargs: seen.append(kwargs) or {"answer": 4}
    )
    assert client.generate_request(
        GenerationRequest("Original", "solver", {"type": "object"})
    ) == {"answer": 4}
    assert len(seen) == 1


def test_roundtrip_validates_identity_and_cancels_owned_process(monkeypatch):
    processes = []

    class Process:
        returncode = None

        def __init__(self, *args, **kwargs):
            self.stopped = False
            processes.append(self)

        def communicate(self, data, timeout):
            raise InterruptedError("cancelled")

        def poll(self):
            return self.returncode

        def terminate(self):
            self.stopped = True
            self.returncode = 0

        def wait(self, timeout):
            return self.returncode

    monkeypatch.setattr(
        service, "helper_path", lambda: Path("/signed/KeldinAppleIntelligence")
    )
    monkeypatch.setattr(service.subprocess, "Popen", Process)
    with pytest.raises(InterruptedError):
        service.roundtrip({"request_id": "test"})
    assert len(processes) == 1 and processes[0].stopped


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider", "apple"),
        ("model", "mlx-model"),
        ("request_id", "other"),
        ("protocol_version", True),
        ("context_size", 8192.0),
        ("available", 1),
    ],
)
def test_roundtrip_refuses_forged_helper_metadata(monkeypatch, field, value):
    class Process:
        returncode = 0

        def __init__(self, *args, **kwargs):
            pass

        def communicate(self, data, timeout):
            payload = json.loads(data)
            return json.dumps({**reply(payload), field: value}).encode(), b""

        def poll(self):
            return 0

    monkeypatch.setattr(
        service, "helper_path", lambda: Path("/signed/KeldinAppleIntelligence")
    )
    monkeypatch.setattr(service.subprocess, "Popen", Process)
    with pytest.raises(ValueError, match="identity"):
        service.roundtrip({"request_id": "test"})


def test_cli_accepts_system_provider_for_shared_and_french_routes():
    from Backend.Core.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "generate",
            "--subject",
            "accounting_aqa",
            "--provider",
            service.PROVIDER,
            "--model",
            service.MODEL,
        ]
    )
    assert args.provider == service.PROVIDER


def test_exact_embedded_schema_is_not_duplicated_or_reformatted():
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "integer"}},
        "required": ["answer"],
    }
    prompt = "Complete original reference text\nOUTPUT_SCHEMA=" + json.dumps(
        schema, ensure_ascii=False
    )
    assert service.complete_prompt(prompt, schema) == prompt
    assert (
        service.complete_prompt("No schema yet", schema).count("\nOUTPUT_SCHEMA=") == 1
    )


@pytest.mark.parametrize(
    "suffix",
    [
        '{"type":"array"}',
        '{"type":"object"} trailing prose',
        '{"type":"object","type":"array"}',
        '{"type":"object","description":"value\\nOUTPUT_SCHEMA=not a schema"}',
    ],
)
def test_marker_or_partial_json_cannot_skip_binding_the_complete_owned_schema(suffix):
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "integer"}},
    }
    prompt = "Unchanged text\nOUTPUT_SCHEMA=" + suffix
    result = service.complete_prompt(prompt, schema)
    assert result.startswith(prompt + "\nOUTPUT_SCHEMA=")
    assert service.strict_object(result.rpartition("\nOUTPUT_SCHEMA=")[2]) == schema


def test_real_french_author_request_keeps_one_owned_schema_binding():
    from Backend.Core.france.llm_pipeline import exercise_request

    request = exercise_request("1", 42, [])
    assert service.complete_prompt(request.prompt, request.schema) == request.prompt


@pytest.mark.parametrize("raw", ['{"id":1,}', '{"wrong":"shape"}'])
def test_french_owner_does_not_retry_an_unreturned_system_candidate(monkeypatch, raw):
    from Backend.Core.france import llm_pipeline

    calls = []

    def invalid(payload):
        calls.append(payload)
        return reply(payload, raw)

    monkeypatch.setattr(service, "roundtrip", invalid)
    client = HostedLLMClient(provider=service.PROVIDER, model=service.MODEL, api_key="")
    with pytest.raises(GenerationEvidenceError) as error:
        llm_pipeline._author(
            client, llm_pipeline.exercise_request("1", 42, [], output_budget=4096), "1"
        )
    assert error.value.details["kind"] == "provider_structure"
    assert len(calls) == 1


def test_helper_does_not_inherit_hosted_credentials(monkeypatch):
    captured = []
    monkeypatch.setenv("KELDIN_API_KEY", "fixture-not-a-real-key")

    class Process:
        returncode = 0

        def __init__(self, *args, **kwargs):
            captured.append(kwargs)

        def communicate(self, data, timeout):
            return json.dumps(reply(json.loads(data))).encode(), b""

        def poll(self):
            return 0

    monkeypatch.setattr(
        service, "helper_path", lambda: Path("/signed/KeldinAppleIntelligence")
    )
    monkeypatch.setattr(service.subprocess, "Popen", Process)
    assert service.roundtrip({"request_id": "owned"})
    assert "KELDIN_API_KEY" not in captured[0]["env"]


def test_cli_accepts_system_provider_for_french_route():
    from Backend.Core.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "generate-assessment",
            "--assessment",
            "fr-bac-general-nsi-written-2027",
            "--reference-index",
            "references.sqlite",
            "--seed",
            "42",
            "--provider",
            service.PROVIDER,
            "--model",
            service.MODEL,
        ]
    )
    assert args.provider == service.PROVIDER


def test_old_os_unavailable_error_does_not_require_success_capability_fields(
    monkeypatch,
):
    class Process:
        returncode = 0

        def __init__(self, *args, **kwargs):
            pass

        def communicate(self, data, timeout):
            payload = json.loads(data)
            unavailable = {
                "protocol_version": 1,
                "request_id": payload["request_id"],
                "provider": service.PROVIDER,
                "model": service.MODEL,
                "os_version": "25.0",
                "status": "error",
                "error": {"code": "unavailable", "message": "fixed"},
            }
            return json.dumps(unavailable).encode(), b""

        def poll(self):
            return 0

    monkeypatch.setattr(
        service, "helper_path", lambda: Path("/signed/KeldinAppleIntelligence")
    )
    monkeypatch.setattr(service.subprocess, "Popen", Process)
    with pytest.raises(GenerationEvidenceError, match="unavailable") as error:
        service.roundtrip({"request_id": "owned"})
    assert error.value.details["code"] == "unavailable"


def test_oversized_prepared_prompt_refuses_before_launch(transport):
    with pytest.raises(GenerationEvidenceError, match="context capacity"):
        service.generate(
            "a" * 131073,
            {"type": "object"},
            budget=512,
            temperature=0.2,
            locale="en_GB",
        )
    assert not transport
