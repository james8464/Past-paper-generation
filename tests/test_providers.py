from __future__ import annotations

import builtins
import io
import json
import sys
import urllib.error
from types import ModuleType, SimpleNamespace

import pytest

from Backend.Core.providers import (
    HostedLLMClient,
    _mlx_decoder_schema,
    _ollama_json_schema,
    _ollama_output_budget,
    _ollama_temperature,
    urllib_request,
)


@pytest.mark.parametrize("provider", ["ollama", "apple", "openai", "anthropic"])
def test_parallel_local_review_setting_is_captured_and_never_enables_mlx(
    provider, monkeypatch
):
    monkeypatch.setenv("KELDIN_PARALLEL_LOCAL_REVIEWS", "1")
    client = HostedLLMClient(provider=provider, model="fixture", api_key="")
    monkeypatch.setenv("KELDIN_PARALLEL_LOCAL_REVIEWS", "0")
    assert client.parallel_review_workers == (2 if provider == "ollama" else 1)


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

    def load(model_name: str, *, tokenizer_config) -> tuple[object, object]:
        calls["load"] += 1
        assert model_name == "/local/test-model"
        assert tokenizer_config == {
            "trust_remote_code": False,
            "local_files_only": True,
        }
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


def test_solver_schema_bounds_multiple_choice_to_candidate_options():
    choices = ["Cash book", "Purchases journal", "Sales journal", "General journal"]
    schema = _ollama_json_schema(
        "Independently solve this item.\n"
        + json.dumps(
            {"item": {"kind": "multiple_choice", "marks": 1, "choices": choices}}
        )
    )
    properties = schema["properties"]
    assert properties["answer"]["enum"] == choices
    assert properties["mark_points"]["items"]["enum"] == choices
    assert properties["mark_points"]["minItems"] == 1
    assert properties["mark_points"]["maxItems"] == 1
    assert properties["alternatives"]["maxItems"] == 0
    assert "correct_choice" not in json.dumps(schema)


def test_solver_schema_reads_compact_closed_slots_before_choice_shape():
    schema = _ollama_json_schema(
        'Independently solve this item.\n{"item":{"kind":"multiple_choice",'
        '"choices":["A","B"],"response_slots":["row-1","row-2"]}}'
    )
    assert schema["properties"]["answer"]["required"] == ["row-1", "row-2"]


def test_apple_provider_applies_the_models_chat_template(monkeypatch) -> None:
    module = ModuleType("mlx_lm")
    calls = []

    class Tokenizer:
        has_chat_template = True

        def apply_chat_template(self, messages, **kwargs):
            calls.append((messages, kwargs))
            return "formatted conversation"

    module.load = lambda _path, **kwargs: (object(), Tokenizer())

    def generate(_model, _tokenizer, *, prompt, **_kwargs):
        assert prompt == "formatted conversation"
        return '{"answer":"ready"}'

    module.generate = generate
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model", lambda _: "/local/model"
    )
    client = HostedLLMClient(provider="apple", model="test-model", api_key="")
    assert client.generate_json("Return JSON.") == {"answer": "ready"}
    assert calls == [
        (
            [{"role": "user", "content": "Return JSON."}],
            {
                "tokenize": False,
                "add_generation_prompt": True,
                "enable_thinking": False,
            },
        )
    ]


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


def test_apple_batch_format_and_identifier_repair(monkeypatch):
    module = ModuleType("mlx_lm")
    prompts = []
    replies = iter(
        [
            '{"questions":[{"id":"1/0/0"}]}',
            '{"questions":[{"id":"0/0/0"}]}',
        ]
    )
    module.load = lambda _, **kwargs: (object(), object())

    def generate(_model, _tokenizer, *, prompt, **kwargs):
        prompts.append(prompt)
        return next(replies)

    module.generate = generate
    monkeypatch.setattr(
        HostedLLMClient,
        "_mlx_structured_response",
        lambda self, prompt, schema: generate(None, None, prompt=prompt),
    )
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model", lambda _: "/local/model"
    )
    client = HostedLLMClient(provider="apple", model="test", api_key="")
    prompt = (
        "Return one JSON object with a `questions` array. BLUEPRINT_DATA="
        '[{"id":"0/0/0","prompt_numeric_contract":{"required_exact_tokens":[]}}]'
    )
    assert client.generate_json(prompt)["questions"] == [{"id": "0/0/0"}]
    assert len(prompts) == 2
    assert "OUTPUT_SCHEMA=" in prompts[0]
    assert '"enum":["0/0/0"]' in prompts[0]
    assert "question identifiers or count did not match" in prompts[1]


@pytest.mark.parametrize(
    "items",
    [[], [{"id": "0/0/0"}, {"id": "0/0/0"}], [{"id": []}], [{}], "not an array"],
)
@pytest.mark.parametrize(
    "field,prompt",
    [
        (
            "questions",
            "Return one JSON object with a `questions` array. BLUEPRINT_DATA=",
        ),
        (
            "reviews",
            "Return JSON only: `reviews` must contain one object per id. REVIEW_DATA=",
        ),
    ],
)
def test_apple_rejects_missing_or_extra_batch_items(monkeypatch, items, field, prompt):
    module = ModuleType("mlx_lm")
    module.load = lambda _, **kwargs: (object(), object())
    module.generate = lambda *args, **kwargs: json.dumps({field: items})
    monkeypatch.setattr(
        HostedLLMClient,
        "_mlx_structured_response",
        lambda self, prompt, schema: json.dumps({field: items}),
    )
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model", lambda _: "/local/model"
    )
    client = HostedLLMClient(provider="apple", model="test", api_key="")
    with pytest.raises(ValueError, match="identifiers or count did not match"):
        client.generate_json(
            prompt + '[{"id":"0/0/0"}]',
            retries=1,
        )


@pytest.mark.parametrize("duplicate", [False, True])
@pytest.mark.parametrize("chat", [False, True])
def test_apple_structured_decoder_caches_adapter_not_generation_state(
    monkeypatch, duplicate, chat
):
    calls = []
    adapters = []
    templates = []

    class Tokenizer:
        has_chat_template = chat

        def apply_chat_template(self, messages, **kwargs):
            templates.append((messages, kwargs))
            assert kwargs == {
                "tokenize": False,
                "add_generation_prompt": True,
                "enable_thinking": False,
            }
            return "formatted conversation"

    outlines = ModuleType("outlines")
    types = ModuleType("outlines.types")
    types.JsonSchema = lambda schema: {"schema": schema}

    def adapter(model, tokenizer):
        adapters.append((model, tokenizer))

        def generate(prompt, output_type, **kwargs):
            assert generate.type_adapter.has_chat_template is False
            calls.append((prompt, output_type, kwargs))
            return '{"answer":["ready","ready"]}' if duplicate else '{"answer":"ready"}'

        generate.type_adapter = SimpleNamespace(has_chat_template=True)
        return generate

    outlines.from_mlxlm = adapter
    monkeypatch.setitem(sys.modules, "outlines", outlines)
    monkeypatch.setitem(sys.modules, "outlines.types", types)
    llguidance = ModuleType("llguidance")
    llguidance.grammar_from = lambda format, text: text

    class Matcher:
        @staticmethod
        def validate_grammar(grammar):
            assert "uniqueItems" not in grammar
            return ""

    llguidance.LLMatcher = Matcher
    monkeypatch.setitem(sys.modules, "llguidance", llguidance)
    client = HostedLLMClient(provider="apple", model="test", api_key="")
    client._apple_tokenizer = Tokenizer()
    schema = {"type": "object", "required": ["answer"]}
    if duplicate:
        schema["properties"] = {"answer": {"type": "array", "uniqueItems": True}}
        with pytest.raises(ValueError, match="required output schema"):
            client._mlx_structured_response("prompt", schema)
        return
    for _ in range(2):
        assert (
            client._mlx_structured_response("unformatted prompt", schema)
            == '{"answer":"ready"}'
        )
    assert len(adapters) == 1
    assert len(calls) == 2
    assert len(templates) == (2 if chat else 0)
    assert calls[0] == (
        "formatted conversation" if chat else "unformatted prompt",
        {"schema": schema},
        {"backend": "llguidance", "max_tokens": 4096, "verbose": False},
    )


def test_mlx_decoder_schema_preserves_property_names_and_original_contract():
    schema = {
        "type": "object",
        "properties": {
            "uniqueItems": {"type": "boolean"},
            "values": {"type": "array", "uniqueItems": True, "maxItems": 3},
        },
    }
    adapted = _mlx_decoder_schema(schema)
    assert adapted["properties"]["uniqueItems"] == {"type": "boolean"}
    assert adapted["properties"]["values"] == {"type": "array", "maxItems": 3}
    assert schema["properties"]["values"]["uniqueItems"] is True


def test_apple_structured_decoder_missing_dependency_is_actionable(monkeypatch):
    monkeypatch.setitem(sys.modules, "outlines", None)
    client = HostedLLMClient(provider="apple", model="test", api_key="")
    with pytest.raises(RuntimeError, match="guided setup"):
        client._mlx_structured_response("prompt", {"required": ["answer"]})


@pytest.mark.parametrize(
    "response",
    [
        '{"answer":"partial"',
        '{"answer":"first","answer":"second"}',
        'Commentary {"answer":"complete"}',
        '[{"answer":"complete"}]',
    ],
)
def test_apple_constrained_output_is_not_salvaged(monkeypatch, response):
    module = ModuleType("mlx_lm")
    module.load = lambda _, **kwargs: (object(), object())
    module.generate = lambda *args, **kwargs: pytest.fail("unconstrained generation")
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model", lambda _: "/local/model"
    )
    monkeypatch.setattr(
        HostedLLMClient,
        "_mlx_structured_response",
        lambda self, prompt, schema: response,
    )
    client = HostedLLMClient(provider="apple", model="test", api_key="")
    with pytest.raises(ValueError):
        client.generate_json("Independently solve this question.", retries=1)


def test_batch_schema_ignores_nested_candidate_identifiers():
    schema = _ollama_json_schema(
        'Return one JSON object with a `questions` array. BLUEPRINT_DATA=[{"id":"0/0/0",'
        '"candidate":{"id":"9/9/9"}}] REPAIR_DATA={"id":"8/8/8"}'
    )
    items = schema["properties"]["questions"]
    assert items["minItems"] == items["maxItems"] == 1
    assert items["items"]["properties"]["id"]["enum"] == ["0/0/0"]


def test_review_schema_ignores_a_blueprint_marker_inside_candidate_text():
    data = [{"id": "0/0/0", "candidate": {"prompt": 'BLUEPRINT_DATA=[{"id":"9/9/9"}]'}}]
    schema = _ollama_json_schema(
        "Return JSON only: `reviews` must contain one object per id.\nREVIEW_DATA="
        + json.dumps(data)
    )
    assert schema["properties"]["reviews"]["items"]["properties"]["id"]["enum"] == [
        "0/0/0"
    ]


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
    assert generation["properties"]["questions"]["items"]["properties"]["id"][
        "enum"
    ] == ["0/0/0", "0/0/1"]
    assert review["required"] == ["reviews"]
    assert review["properties"]["reviews"]["minItems"] == 2
    assert review["properties"]["reviews"]["maxItems"] == 2
    assert review["properties"]["reviews"]["items"]["properties"]["id"]["enum"] == [
        "0/0/0",
        "0/0/1",
    ]
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
