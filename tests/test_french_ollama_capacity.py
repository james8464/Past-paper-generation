import io
import json
from urllib.error import HTTPError

import pytest

from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.providers import HostedLLMClient, urllib_request


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
    assert payload["truncate"] is False and payload["shift"] is False
    assert payload["options"]["num_ctx"] == 16384
    assert payload["options"]["num_predict"] == 8192
    assert options == {"attempts": 1, "timeout_seconds": 600}
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

    monkeypatch.setattr("urllib.request.urlopen", send)
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
    assert calls == [{"attempts": 1, "timeout_seconds": 600}]
