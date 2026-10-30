import io
import json

import pytest

from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.providers import HostedLLMClient


@pytest.mark.parametrize(
    "provider,key", [("openai", "max_output_tokens"), ("anthropic", "max_tokens")]
)
def test_typed_hosted_requests_honor_budgets_without_new_schema_modes(
    monkeypatch, provider, key
):
    payloads = []

    def transport(url, data, headers):
        payloads.append(json.loads(data))
        reply = (
            {"status": "completed", "output_text": '{"answer":"ready"}'}
            if provider == "openai"
            else {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"answer":"ready"}'}],
            }
        )
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", transport)
    client = HostedLLMClient(provider=provider, model="fixture", api_key="private")
    for budget in [14000, 6000]:
        request = GenerationRequest(
            "Solve this.", "solver", {"type": "object"}, output_budget=budget
        )
        assert client.generate_request(request) == {"answer": "ready"}
    assert [payload[key] for payload in payloads] == [14000, 6000]
    if provider == "openai":
        assert all(
            payload["text"] == {"format": {"type": "json_object"}}
            for payload in payloads
        )
        assert all(payload["store"] is False for payload in payloads)
    else:
        assert all(
            "output_config" not in payload and "response_format" not in payload
            for payload in payloads
        )


@pytest.mark.parametrize(
    "provider,budget",
    [
        ("openai", 15),
        ("openai", True),
        ("openai", 16385),
        ("anthropic", 0),
        ("anthropic", True),
        ("anthropic", 16385),
    ],
)
def test_invalid_hosted_budget_refuses_before_network(monkeypatch, provider, budget):
    monkeypatch.setattr(
        "Backend.Core.providers.urllib_request",
        lambda *args, **kwargs: pytest.fail("made request"),
    )
    client = HostedLLMClient(provider=provider, model="fixture", api_key="private")
    with pytest.raises(ValueError, match="budget"):
        getattr(client, "_" + provider)("prompt", output_budget=budget)
