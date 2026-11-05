import io
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from Backend.Core.ollama_thinking import structured_thinking_policy
from Backend.Core.providers import HostedLLMClient


@pytest.mark.parametrize(
    "metadata, expected, status",
    [
        ({"values": [False, True], "default": True}, False, "disabled"),
        ({"values": ["low", "medium", "high"], "default": "medium"}, "low", "reduced"),
        (
            {"values": ["minimal", "deep"], "default": "deep"},
            "deep",
            "reduction_unavailable",
        ),
        ({"values": [True], "default": True}, True, "reduction_unavailable"),
    ],
)
def test_advertised_controls(metadata, expected, status):
    policy = structured_thinking_policy({"thinking": metadata})
    assert type(policy["requested"]) is type(expected)
    assert policy["requested"] == expected
    assert policy["status"] == status


@pytest.mark.parametrize("envelope", [{}, {"capabilities": ["thinking"]}, None])
def test_absent_metadata_is_explicitly_unknown(envelope):
    policy = structured_thinking_policy(envelope)
    assert policy["requested"] is False
    assert policy["status"] == "legacy_unknown"


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        {},
        {"values": [], "default": False},
        {"values": [0, True], "default": True},
        {"values": [False], "default": 0},
        {"values": [False, False], "default": False},
        {"values": ["low"], "default": "high"},
        {"values": [""], "default": ""},
        {"values": [False, {}], "default": False},
    ],
)
def test_malformed_present_metadata_is_refused(metadata):
    with pytest.raises(ValueError, match="thinking metadata"):
        structured_thinking_policy({"thinking": metadata})


def test_metadata_once_and_reasoning_not_retained():
    calls = []

    def send(url, data, headers, **settings):
        calls.append((url, json.loads(data), settings))
        if url.endswith("/show"):
            return io.BytesIO(
                json.dumps(
                    {"thinking": {"values": [False, True], "default": True}}
                ).encode()
            )
        return io.BytesIO(
            json.dumps(
                {
                    "done": True,
                    "done_reason": "length",
                    "eval_count": 8192,
                    "message": {"content": "", "thinking": "private reasoning"},
                }
            ).encode()
        )

    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    for _ in range(2):
        with pytest.raises(ValueError) as caught:
            client._ollama("owned", request_function=send)
        evidence = caught.value.details
        assert evidence["thinking_policy"]["requested"] is False
        assert evidence["thinking_present"] is True
        assert evidence["thinking_characters"] == 17
        assert "private reasoning" not in json.dumps(evidence)
    assert [url.rsplit("/", 1)[-1] for url, _, _ in calls] == ["show", "chat", "chat"]
    assert calls[0][2]["attempts"] == 1
    assert calls[0][2]["timeout_seconds"] <= 5
    assert calls[1][1]["think"] is False


def test_malformed_metadata_never_reaches_inference_or_repair(monkeypatch):
    calls = []

    def send(url, data, headers, **settings):
        calls.append(url)
        assert url.endswith("/show")
        return io.BytesIO(b'{"thinking":{"values":[0],"default":0}}')

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    for _ in range(2):
        with pytest.raises(ValueError, match="thinking metadata"):
            client.generate_json("owned", retries=3)
    assert len(calls) == 1


def test_unavailable_metadata_cached_without_leaking_transport_error():
    calls = []

    def send(url, data, headers, **settings):
        calls.append(url)
        if url.endswith("/show"):
            raise RuntimeError("private server detail")
        payload = json.loads(data)
        assert payload["think"] is False
        return io.BytesIO(b'{"done":true,"message":{"content":"{}"}}')

    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    assert client._ollama("owned", request_function=send) == {}
    assert client._ollama("owned", request_function=send) == {}
    assert len(calls) == 3
    assert client._ollama_policies["owned"]["metadata"] == "unavailable"


@pytest.mark.parametrize("french", [False, True])
@pytest.mark.parametrize(
    "values, default, expected",
    [
        ([False, True], True, False),
        (["low", "medium", "high"], "medium", "low"),
    ],
)
def test_policy_changes_only_control_not_schema_or_token_limits(
    french, values, default, expected
):
    sent = []
    schema = {"type": "object", "properties": {"owned": {"type": "boolean"}}}

    def send(url, data, headers, **settings):
        payload = json.loads(data)
        if url.endswith("/show"):
            return io.BytesIO(
                json.dumps(
                    {"thinking": {"values": values, "default": default}}
                ).encode()
            )
        sent.append(payload)
        return io.BytesIO(
            b'{"done":true,"done_reason":"stop","prompt_eval_count":100,"eval_count":20,"message":{"content":"{}"}}'
        )

    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    assert (
        client._ollama(
            "unchanged prompt",
            schema=schema,
            output_budget=8192,
            seed=123,
            french_nsi=french,
            request_function=send,
        )
        == {}
    )
    assert len(sent) == 1
    assert type(sent[0]["think"]) is type(expected)
    assert sent[0]["think"] == expected
    assert sent[0]["format"] == schema
    assert sent[0]["messages"] == [{"role": "user", "content": "unchanged prompt"}]
    assert sent[0]["options"]["num_predict"] == 8192
    assert sent[0]["options"]["num_ctx"] == 16384
    assert sent[0]["options"]["seed"] == 123
    if french:
        assert sent[0]["truncate"] is sent[0]["shift"] is False


def test_parallel_lookup_is_once_per_model_and_returns_copies():
    calls = []

    def send(url, data, headers, **settings):
        calls.append(json.loads(data)["model"])
        return io.BytesIO(b'{"thinking":{"values":[false,true],"default":true}}')

    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    with ThreadPoolExecutor(max_workers=8) as pool:
        policies = list(
            pool.map(lambda _: client._ollama_thinking_policy(send), range(16))
        )
    assert calls == ["owned"]
    policies[0]["values"].append("mutated")
    assert client._ollama_thinking_policy(send)["values"] == [False, True]
    client.model = "second-owned"
    assert client._ollama_thinking_policy(send)["requested"] is False
    assert calls == ["owned", "second-owned"]


def test_historical_french_adapter_bounds_lookup_preserves_inference_timeout(
    monkeypatch,
):
    from Backend.Core.france import network

    seen = []

    def open_request(request, *, timeout):
        seen.append((request.full_url, timeout))
        if request.full_url.endswith("/show"):
            return io.BytesIO(b'{"thinking":{"values":[false,true],"default":true}}')
        return io.BytesIO(b'{"done":true,"message":{"content":"{}"}}')

    monkeypatch.setattr(network, "open_ollama_request", open_request)
    client = HostedLLMClient(provider="ollama", model="owned", api_key="")
    assert client._ollama("owned", request_function=network.ollama_request) == {}
    assert [timeout for _, timeout in seen] == [5, 900]


@pytest.mark.parametrize("timeout", [0, -1, 901, True, 5.0, "5", None])
def test_historical_adapter_rejects_invalid_timeout_before_transport(
    monkeypatch, timeout
):
    from Backend.Core.france import network

    monkeypatch.setattr(
        network,
        "open_ollama_request",
        lambda *args, **kwargs: pytest.fail("invalid timeout reached transport"),
    )
    with pytest.raises(ValueError, match="timeout"):
        network.ollama_request(
            "http://localhost:11434/api/show",
            b"{}",
            {},
            attempts=1,
            timeout_seconds=timeout,
        )
