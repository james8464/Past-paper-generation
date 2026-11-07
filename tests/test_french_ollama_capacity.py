import io
import json
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler

import pytest

from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.ollama_thinking import structured_thinking_policy
from Backend.Core.providers import HostedLLMClient, urllib_request


@pytest.fixture(autouse=True)
def chat_transport_only(monkeypatch):
    monkeypatch.setattr(
        "Backend.Core.ollama_admission._memory_snapshot", lambda: (16 << 30, 1)
    )
    monkeypatch.setattr(
        "Backend.Core.ollama_admission._installed_model_state",
        lambda *args: (4 << 30, False),
    )
    monkeypatch.setattr(
        "Backend.Core.ollama_admission._headroom_snapshot", lambda physical: 12 << 30
    )
    # These tests isolate inference transport/count bounds. Metadata transport
    # and capability selection have their own provider integration controls.
    monkeypatch.setattr(
        HostedLLMClient,
        "_ollama_thinking_policy",
        lambda self, request_function: structured_thinking_policy({}),
    )


def closed_opener(monkeypatch, send):
    from Backend.Core.france import network

    captured = []

    def build(*handlers):
        captured.extend(handlers)
        assert len(handlers) == 2
        assert isinstance(handlers[0], ProxyHandler)
        assert handlers[0].proxies == {}
        assert isinstance(handlers[1], network.NoRedirects)

        class Opener:
            def open(self, outgoing, *, timeout):
                return send(outgoing, timeout=timeout, redirect=handlers[1])

        return Opener()

    monkeypatch.setattr(network, "build_opener", build)
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: pytest.fail("French inference used the default opener"),
    )
    return captured


def request():
    return GenerationRequest(
        "Exercice français sans omission.",
        "french_nsi_authoring",
        {"type": "object"},
        output_budget=8192,
    )


def reply(**updates):
    return {
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 5000,
        "eval_count": 1200,
        "message": {"content": '{"answer":"ready"}'},
        **updates,
    }


def test_public_french_inference_uses_proxy_free_opener_and_identical_payload(
    monkeypatch, capsys
):
    outgoing = []

    def send(item, *, timeout, redirect):
        outgoing.append((item, timeout))
        return io.BytesIO(json.dumps(reply()).encode())

    handlers = closed_opener(monkeypatch, send)
    client = HostedLLMClient(
        provider="ollama", model="fixture", api_key="unused-secret"
    )
    owned = request()
    assert client.generate_request(owned) == {"answer": "ready"}
    assert len(handlers) == 2
    assert len(outgoing) == 1
    item, timeout = outgoing[0]
    assert item.full_url == "http://localhost:11434/api/chat"
    assert item.get_method() == "POST"
    assert timeout == 600
    assert dict(item.header_items()) == {"Content-type": "application/json"}

    injected = []

    def capture(url, data, headers, **settings):
        injected.append((url, data, headers, settings))
        return io.BytesIO(json.dumps(reply()).encode())

    assert client._ollama(
        owned.prompt,
        schema=owned.schema,
        output_budget=owned.output_budget,
        seed=owned.seed,
        temperature=owned.temperature,
        request_function=capture,
        french_nsi=True,
    ) == {"answer": "ready"}
    assert injected == [
        (
            item.full_url,
            item.data,
            {"Content-Type": "application/json"},
            {"attempts": 1, "timeout_seconds": 600},
        )
    ]
    assert "unused-secret" not in capsys.readouterr().out
    assert b"unused-secret" not in item.data


def test_public_french_inference_refuses_redirect_without_retry_or_success(
    monkeypatch, capsys
):
    calls = []

    def send(item, *, timeout, redirect):
        calls.append(item.full_url)
        return redirect.redirect_request(
            item, None, 302, "Found", {}, "https://other.invalid/"
        )

    closed_opener(monkeypatch, send)
    client = HostedLLMClient(
        provider="ollama", model="fixture", api_key="unused-secret"
    )
    with pytest.raises(ValueError, match="redirection") as failure:
        client.generate_request(request())
    assert calls == ["http://localhost:11434/api/chat"]
    assert capsys.readouterr().out == ""
    assert "unused-secret" not in str(failure.value)


@pytest.mark.parametrize("failure", ["busy", "connection", "timeout"])
def test_public_french_transport_failures_never_add_a_physical_retry(
    monkeypatch, failure
):
    calls = []

    def send(item, *, timeout, redirect):
        calls.append(timeout)
        if failure == "busy":
            raise HTTPError(item.full_url, 503, "Busy", {}, io.BytesIO(b"busy"))
        if failure == "connection":
            raise URLError("unavailable")
        raise TimeoutError("fixture timeout")

    closed_opener(monkeypatch, send)
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    with pytest.raises(RuntimeError):
        client.generate_request(request())
    assert calls == [600]


def test_direct_ollama_policy_cannot_replace_a_fixed_host_policy(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: pytest.fail("Unexpected network request"),
    )
    with pytest.raises(ValueError, match="transport policies"):
        urllib_request(
            "https://api.openai.com/v1/responses",
            b"{}",
            {},
            fixed_host="api.openai.com",
            direct_ollama=True,
        )


def test_neutral_repetition_penalty_is_exclusive_to_french_nsi(monkeypatch):
    calls = []

    def transport(url, data, headers, **kwargs):
        calls.append((json.loads(data), kwargs))
        return io.BytesIO(json.dumps(reply()).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", transport)
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    for operation in ("french_nsi_authoring", "solver"):
        client.generate_request(
            GenerationRequest(
                "Exercice français sans omission.",
                operation,
                {"type": "object"},
                generation_seed=42,
                temperature=0.6,
                output_budget=8192,
            )
        )
    french, legacy = [payload for payload, _ in calls]
    common = {
        "temperature": 0.6,
        "top_p": 0.9,
        "num_ctx": 16384,
        "num_predict": 8192,
        "repeat_last_n": 256,
        "seed": 104771,
    }
    assert french["options"] == {**common, "repeat_penalty": 1.0}
    assert legacy["options"] == {**common, "repeat_penalty": 1.15}
    assert french["format"] == legacy["format"] == {"type": "object"}
    assert french["messages"] == legacy["messages"]
    assert french["think"] is False and legacy["think"] is False
    assert french["truncate"] is False and french["shift"] is False
    assert "truncate" not in legacy and "shift" not in legacy
    assert [options for _, options in calls] == [
        {"attempts": 1, "timeout_seconds": 600, "direct_ollama": True},
        {"attempts": 2},
    ]


def test_french_uses_no_truncation_no_shift_one_http_attempt_and_scoped_timeout(
    monkeypatch, capsys
):
    calls = []

    def transport(url, data, headers, **kwargs):
        calls.append((json.loads(data), kwargs))
        return io.BytesIO(json.dumps(reply()).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", transport)
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    assert client.generate_request(request()) == {"answer": "ready"}
    payload, options = calls[0]
    assert payload["think"] is False  # Unknown legacy metadata requests direct output.
    assert payload["truncate"] is False and payload["shift"] is False
    assert payload["options"]["num_ctx"] == 16384
    assert payload["options"]["num_predict"] == 8192
    assert options == {"attempts": 1, "timeout_seconds": 600, "direct_ollama": True}
    event = json.loads(capsys.readouterr().out)
    assert event["stage"] == "provider_context"
    assert "5000" in event["message"] and "1200" in event["message"]


@pytest.mark.parametrize(
    "counts",
    [
        {"prompt_eval_count": None},
        {"prompt_eval_count": True},
        {"eval_count": None},
        {"eval_count": -1},
        {"prompt_eval_count": 8200},
        {"prompt_eval_count": 16000, "eval_count": 1000},
        {"eval_count": 9000},
    ],
)
def test_unverified_or_over_capacity_french_response_never_becomes_candidate_or_retries(
    monkeypatch, counts
):
    calls = []
    monkeypatch.setattr(
        "Backend.Core.providers.urllib_request",
        lambda *args, **kwargs: (
            calls.append(1) or io.BytesIO(json.dumps(reply(**counts)).encode())
        ),
    )
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    with pytest.raises(GenerationEvidenceError) as failure:
        client.generate_request(request())
    assert failure.value.details["kind"] == "context_capacity"
    assert len(calls) == 1
    assert failure.value.details["context_window"] == 16384


def test_legacy_ollama_keeps_transport_and_does_not_require_counts(monkeypatch):
    calls = []

    def transport(url, data, headers, **kwargs):
        calls.append((json.loads(data), kwargs))
        return io.BytesIO(
            json.dumps(reply(prompt_eval_count=None, eval_count=None)).encode()
        )

    monkeypatch.setattr("Backend.Core.providers.urllib_request", transport)
    assert HostedLLMClient(
        provider="ollama", model="fixture", api_key=""
    ).generate_json("prompt") == {"answer": "ready"}
    assert "truncate" not in calls[0][0] and "shift" not in calls[0][0]
    assert calls[0][0]["think"] is False
    assert calls[0][1] == {"attempts": 2}


def test_scoped_urllib_timeout_is_forwarded_without_network(monkeypatch):
    seen = []
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, *, timeout: seen.append(timeout) or io.BytesIO(),
    )
    urllib_request(
        "http://localhost:11434/api/chat", b"{}", {}, attempts=1, timeout_seconds=600
    )
    urllib_request("http://localhost:11434/api/chat", b"{}", {}, attempts=1)
    assert seen == [600, 180]


@pytest.mark.parametrize(
    "message,expected",
    [
        ("the input length exceeds the context length", GenerationEvidenceError),
        (
            "the prompt is longer than the context length currently available to the model",
            GenerationEvidenceError,
        ),
        ("invalid response schema", RuntimeError),
    ],
)
def test_native_context_http_refusal_is_distinct_from_question_failure(
    monkeypatch, message, expected
):
    calls = []

    def send(request, *, timeout):
        calls.append(timeout)
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            {},
            io.BytesIO(json.dumps({"error": message}).encode()),
        )

    closed_opener(
        monkeypatch,
        lambda outgoing, *, timeout, redirect: send(outgoing, timeout=timeout),
    )
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    with pytest.raises(expected) as failure:
        client.generate_request(request())
    if expected is GenerationEvidenceError:
        assert failure.value.details["kind"] == "context_capacity"
    assert calls == [600]


def test_french_refuses_json_salvage_after_valid_capacity_counts(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "Backend.Core.providers.urllib_request",
        lambda *args, **kwargs: (
            calls.append(1)
            or io.BytesIO(
                json.dumps(
                    reply(message={"content": 'comment {"answer":"ready"} tail'})
                ).encode()
            )
        ),
    )
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    with pytest.raises(GenerationEvidenceError, match="invalid structured output"):
        client.generate_request(request())
    assert calls == [1]


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_french_hosted_calls_also_have_one_physical_attempt(monkeypatch, provider):
    calls = []

    def send(url, data, headers, **kwargs):
        calls.append(kwargs)
        result = (
            {"status": "completed", "output_text": '{"answer":"ready"}'}
            if provider == "openai"
            else {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"answer":"ready"}'}],
            }
        )
        return io.BytesIO(json.dumps(result).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    assert HostedLLMClient(
        provider=provider, model="fixture", api_key="private"
    ).generate_request(request()) == {"answer": "ready"}
    assert calls == [
        {
            "attempts": 1,
            "timeout_seconds": 600,
            "fixed_host": f"api.{provider}.com",
            "secrets": ("private",),
        }
    ]
