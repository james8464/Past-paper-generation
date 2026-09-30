from __future__ import annotations

import builtins
import io
import json
import sys
import urllib.error
from types import ModuleType

import pytest

from Backend.Core.providers import (
    HostedLLMClient,
    _ollama_json_schema,
    _ollama_output_budget,
    _ollama_temperature,
    urllib_request,
)


@pytest.mark.parametrize(
    "module", ["cspapergen.ollama_client", "pastpapergen.ollama_client"]
)
def test_standalone_ollama_uses_shared_schema_and_repair(module, monkeypatch):
    from importlib import import_module

    requests = []
    replies = iter(['{"broken":', '{"answer":"repaired"}'])

    def request(url, data, headers, **kwargs):
        requests.append((url, json.loads(data)))
        return io.BytesIO(
            json.dumps(
                {
                    "message": {"content": next(replies)},
                    "done": True,
                    "done_reason": "stop",
                }
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.providers.urllib_request", request)
    client = import_module(module).OllamaClient("http://localhost:11434", "test-model")
    assert client.generate_json("Independently solve this question.") == {
        "answer": "repaired"
    }
    assert len(requests) == 2
    assert all(url.endswith("/api/chat") for url, _ in requests)
    assert requests[0][1]["think"] is False
    assert isinstance(requests[0][1]["format"], dict)
    assert "REPAIR INSTRUCTION" in requests[1][1]["messages"][0]["content"]
    assert client.supports_parallel_generation is False


@pytest.mark.parametrize(
    "status",
    [
        {"done": False},
        {"done_reason": "length"},
        {},
        {"done": True, "done_reason": "unexpected"},
    ],
)
def test_ollama_rejects_incomplete_generation_even_if_json_parses(status, monkeypatch):
    calls = []

    def request(*args, **kwargs):
        calls.append(args)
        return io.BytesIO(
            json.dumps(
                {"message": {"content": '{"answer":"partial"}'}, **status}
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.providers.urllib_request", request)
    client = HostedLLMClient(provider="ollama", model="test", api_key="")
    with pytest.raises(ValueError, match="incomplete"):
        client.generate_json("Solve this question.")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "provider,reply",
    [
        ("openai", {"status": "incomplete", "output_text": '{"answer":"partial"}'}),
        ("openai", {"output_text": '{"answer":"partial"}'}),
        ("anthropic", {"content": [{"type": "text", "text": '{"answer":"partial"}'}]}),
        (
            "anthropic",
            {
                "stop_reason": "max_tokens",
                "content": [{"type": "text", "text": '{"answer":"partial"}'}],
            },
        ),
    ],
)
def test_hosted_providers_reject_incomplete_generation(provider, reply, monkeypatch):
    monkeypatch.setattr(
        "Backend.Core.providers.urllib_request",
        lambda *args, **kwargs: io.BytesIO(json.dumps(reply).encode()),
    )
    client = HostedLLMClient(provider=provider, model="test", api_key="private-key")
    with pytest.raises(ValueError, match="incomplete") as raised:
        client.generate_json("Private prompt must not be saved.")
    assert raised.value.details["provider"] == provider
    assert "Private prompt" not in json.dumps(raised.value.details)
    assert "private-key" not in json.dumps(raised.value.details)


@pytest.mark.parametrize(
    "provider,reply",
    [
        ("openai", {"status": "completed", "output_text": '{"answer":"complete"}'}),
        (
            "anthropic",
            {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"answer":"complete"}'}],
            },
        ),
        (
            "ollama",
            {
                "done": True,
                "done_reason": "stop",
                "message": {"content": '{"answer":"complete"}'},
            },
        ),
    ],
)
def test_completed_provider_response_is_accepted(provider, reply, monkeypatch):
    monkeypatch.setattr(
        "Backend.Core.providers.urllib_request",
        lambda *args, **kwargs: io.BytesIO(json.dumps(reply).encode()),
    )
    client = HostedLLMClient(provider=provider, model="test", api_key="")
    assert client.generate_json("Return JSON.") == {"answer": "complete"}


def test_apple_provider_loads_model_once(monkeypatch) -> None:
    calls = {"load": 0, "generate": 0}
    module = ModuleType("mlx_lm")

    def load(model_name: str) -> tuple[object, object]:
        calls["load"] += 1
        assert model_name == "/local/test-model"
        return object(), object()

    def generate(
        _model: object,
        _tokenizer: object,
        *,
        prompt: str,
        max_tokens: int,
        verbose: bool,
    ) -> str:
        calls["generate"] += 1
        assert max_tokens == 4096
        assert verbose is False
        return f'{{"prompt": "{prompt}"}}'

    module.load = load
    module.generate = generate
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model",
        lambda model: f"/local/{model}",
    )
    client = HostedLLMClient(
        provider="apple",
        model="test-model",
        api_key="",
    )

    assert client.generate_json("first") == {"prompt": "first"}
    assert client.generate_json("second") == {"prompt": "second"}
    assert calls == {"load": 1, "generate": 2}
    assert client.supports_parallel_generation is False


def test_apple_provider_missing_runtime_uses_human_recovery_message(
    monkeypatch,
) -> None:
    real_import = builtins.__import__

    def import_without_mlx(name, *args, **kwargs):
        if name == "mlx_lm":
            raise ImportError("simulated missing runtime")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_mlx)
    client = HostedLLMClient(provider="apple", model="test-model", api_key="")

    with pytest.raises(RuntimeError) as error:
        client.generate_json("question")

    message = str(error.value)
    assert "Settings" in message
    assert "pip" not in message.lower()


def test_remote_hosted_providers_allow_parallel_generation() -> None:
    assert HostedLLMClient(
        provider="openai",
        model="test-model",
        api_key="test-key",
    ).supports_parallel_generation
    assert HostedLLMClient(
        provider="anthropic",
        model="test-model",
        api_key="test-key",
    ).supports_parallel_generation


def test_client_repairs_one_invalid_structured_response(monkeypatch) -> None:
    client = HostedLLMClient(
        provider="ollama",
        model="test-model",
        api_key="",
    )
    prompts: list[str] = []

    def generate(prompt: str) -> dict[str, object]:
        prompts.append(prompt)
        if len(prompts) == 1:
            raise ValueError("truncated JSON")
        return {"ok": True}

    monkeypatch.setattr(client, "_ollama", generate)

    assert client.generate_json("Return JSON.") == {"ok": True}
    assert len(prompts) == 2
    assert "REPAIR INSTRUCTION" in prompts[1]


def test_client_stops_after_one_structured_response_repair(monkeypatch) -> None:
    client = HostedLLMClient(
        provider="ollama",
        model="test-model",
        api_key="",
    )
    monkeypatch.setattr(
        client,
        "_ollama",
        lambda _prompt: (_ for _ in ()).throw(ValueError("invalid")),
    )

    with pytest.raises(ValueError, match="invalid"):
        client.generate_json("Return JSON.")


def test_ollama_schema_constrains_shared_generation_and_review() -> None:
    generation = _ollama_json_schema(
        "Return one JSON object with a `questions` array. "
        'BLUEPRINT_DATA=[{"id":"0/0/0"},{"id":"0/0/1"}]'
    )
    review = _ollama_json_schema(
        "Return JSON only: `reviews` must contain one object per id. "
        'REVIEW_DATA=[{"id":"0/0/0"},{"id":"0/0/1"}]'
    )

    assert generation["required"] == ["questions"]
    assert generation["properties"]["questions"]["type"] == "array"
    assert generation["properties"]["questions"]["minItems"] == 2
    assert generation["properties"]["questions"]["maxItems"] == 2
    assert review["required"] == ["reviews"]
    assert review["properties"]["reviews"]["minItems"] == 2
    assert review["properties"]["reviews"]["maxItems"] == 2
    review_fields = review["properties"]["reviews"]["items"]["required"]
    assert "difficulty_issues" in review_fields
    assert "ambiguity_issues" in review_fields
    assert _ollama_output_budget(generation) == 3072
    assert _ollama_output_budget(review) == 1024


def test_ollama_schema_constrains_the_separate_difficulty_judge() -> None:
    schema = _ollama_json_schema(
        'Return JSON only: {"approved":true|false,'
        '"estimated_demand":"low|standard|high","reasoning_steps":0,'
        '"tariff_fit":true|false,"command_word_fit":true|false,'
        '"context_fit":true|false,"profile_fit":true|false,'
        '"observed_cognitive_operations":[],"cognitive_operations_fit":true|false,'
        '"reasoning_range_fit":true|false,"shortcut_resistant":true|false,'
        '"timing_fit":true|false,"scaffolding_fit":true|false,'
        '"estimated_minutes":0,"issues":[]}.'
    )

    assert set(schema["required"]) == {
        "approved",
        "estimated_demand",
        "reasoning_steps",
        "tariff_fit",
        "command_word_fit",
        "context_fit",
        "profile_fit",
        "observed_cognitive_operations",
        "cognitive_operations_fit",
        "reasoning_range_fit",
        "shortcut_resistant",
        "timing_fit",
        "scaffolding_fit",
        "estimated_minutes",
        "issues",
    }
    assert schema["properties"]["estimated_demand"]["enum"] == [
        "low",
        "standard",
        "high",
    ]
    assert schema["properties"]["observed_cognitive_operations"] == {
        "type": "array",
        "items": {
            "type": "string",
            "enum": [
                "retrieve",
                "contextualise",
                "apply",
                "transform",
                "describe",
                "explain",
                "analyse",
                "integrate",
                "judge",
                "design",
                "program",
                "trace",
            ],
        },
        "maxItems": 12,
        "uniqueItems": True,
    }


def test_ollama_schema_omits_verified_marking_output() -> None:
    generation = _ollama_json_schema(
        "Return one JSON object with a `questions` array. "
        'BLUEPRINT_DATA=[{"id":"0/0/0","mark_scheme_locked": true}]'
    )

    question = generation["properties"]["questions"]["items"]
    assert question["properties"]["mark_scheme"]["maxItems"] == 0
    assert _ollama_output_budget(generation) == 512


def test_ollama_schema_bounds_specialist_question_parts() -> None:
    computer_science = _ollama_json_schema(
        'Return JSON only: {"stem": "string", "parts": ['
    )
    economics = _ollama_json_schema(
        'Return JSON only: {"question_text": "string", "parts": ['
    )

    cs_parts = computer_science["properties"]["parts"]
    economics_parts = economics["properties"]["parts"]
    assert cs_parts["maxItems"] == 8
    assert cs_parts["items"]["additionalProperties"] is False
    assert cs_parts["items"]["properties"]["marking_points"]["maxItems"] == 8
    assert economics_parts["maxItems"] == 6
    assert economics_parts["items"]["additionalProperties"] is False
    assert economics_parts["items"]["properties"]["mark_scheme"]["maxItems"] == 10
    assert _ollama_output_budget(computer_science) == 1024
    assert _ollama_output_budget(economics) == 1536

    compact_economics = _ollama_json_schema(
        "Parts: (a) 4 marks, explain: x; (b) 1 mark, mcq: y\n"
        "VERIFIED MARKING IS IMMUTABLE\n"
        'Return JSON only: {"question_text": "string", "parts": ['
    )
    compact_parts = compact_economics["properties"]["parts"]
    assert compact_parts["minItems"] == 2
    assert compact_parts["maxItems"] == 2
    assert set(compact_parts["items"]["properties"]) == {"label", "prompt"}
    assert _ollama_output_budget(compact_economics) == 384

    compact_computer_science = _ollama_json_schema(
        "- Part 1: 4 marks, Explain x\n- Part 2: 2 marks, State y\n"
        "VERIFIED MARKING IS IMMUTABLE\n"
        'Return JSON only: {"stem": "string", "parts": ['
    )
    compact_cs_parts = compact_computer_science["properties"]["parts"]
    assert compact_cs_parts["minItems"] == 2
    assert compact_cs_parts["maxItems"] == 2
    assert set(compact_cs_parts["items"]["properties"]) == {"label", "prompt"}
    assert _ollama_output_budget(compact_computer_science) == 384

    scenario_only = _ollama_json_schema(
        'Do not repeat, rewrite or answer the parts. Return {"stem": "string", "parts": ['
    )
    assert scenario_only["properties"]["parts"]["maxItems"] == 0
    assert _ollama_output_budget(scenario_only) == 256


def test_ollama_uses_structured_chat_with_bounded_output(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, _limit: int) -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": '{"questions":[]}',
                    },
                    "done_reason": "stop",
                    "done": True,
                }
            ).encode()

    def request(
        url: str,
        data: bytes,
        _headers: dict[str, str],
        *,
        attempts: int,
    ) -> _Response:
        captured.update(
            {
                "url": url,
                "payload": json.loads(data),
                "attempts": attempts,
            }
        )
        return _Response()

    monkeypatch.setattr("Backend.Core.providers.urllib_request", request)
    client = HostedLLMClient(
        provider="ollama",
        model="gemma4:12b",
        api_key="",
    )

    assert client.generate_json("Return one JSON object with a `questions` array.") == {
        "questions": []
    }
    payload = captured["payload"]
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["attempts"] == 2
    assert payload["messages"][0]["role"] == "user"
    assert payload["think"] is False
    assert payload["options"]["temperature"] == 0.2
    assert payload["options"]["seed"] == 0
    assert payload["options"]["num_predict"] == 2304
    question_schema = payload["format"]["properties"]["questions"]["items"]
    assert question_schema["additionalProperties"] is False
    assert question_schema["properties"]["mark_scheme"]["maxItems"] == 10


def test_second_pass_review_is_deterministic() -> None:
    assert (
        _ollama_temperature("Act as a second-pass UK A-level assessment editor.") == 0
    )


def test_offline_provider_retries_then_reports_plain_connection_error(
    monkeypatch,
) -> None:
    attempts = 0

    def offline(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", offline)
    monkeypatch.setattr("Backend.Core.providers.time.sleep", lambda _delay: None)

    with pytest.raises(
        RuntimeError, match="Could not reach the provider API after 2 attempts"
    ):
        urllib_request("https://example.invalid", b"{}", {}, attempts=2)

    assert attempts == 2
