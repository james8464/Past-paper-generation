import io
import json

from Backend.Core.france.pipeline import _prompt


def test_french_transport_has_own_schema_seed_and_output_budget(monkeypatch):
    from Backend.Core.france.provider import FrenchOllamaClient

    requests = []

    def request(url, data, headers, **kwargs):
        requests.append(json.loads(data))
        return io.BytesIO(
            json.dumps(
                {"done": True, "done_reason": "stop", "message": {"content": "{}"}}
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.france.provider.ollama_request", request)
    client = FrenchOllamaClient(
        model="fixture", base_url="http://localhost:11434", seed=42
    )
    prompt = _prompt(
        {
            "exercise_id": "1",
            "topics": ["algorithmique"],
            "minutes": 70,
            "required_curriculum_codes": ["ALG-GRAPHES"],
        },
        [],
        42,
        1,
        "",
    )
    client.generate_json(prompt)
    client.generate_json(prompt)
    payload = requests[0]
    assert payload["format"]["title"] == "NSIExercise"
    assert payload["options"]["num_predict"] == 6144
    assert payload["options"]["num_ctx"] == 16384
    assert payload["options"]["seed"] != 0
    assert payload == requests[1]


def test_french_transport_refuses_redirects_and_environment_proxy(monkeypatch):
    from urllib.request import Request

    import pytest

    from Backend.Core.france.network import NoRedirects, open_ollama_request

    with pytest.raises(ValueError, match="redirection"):
        NoRedirects().redirect_request(
            Request("http://localhost:11434/api/tags"),
            None,
            302,
            "",
            {},
            "https://remote.test/",
        )
    handlers = []

    class Opener:
        def open(self, request, timeout):
            return "fixture"

    def build(*items):
        handlers.extend(items)
        return Opener()

    monkeypatch.setattr("Backend.Core.france.network.build_opener", build)
    assert (
        open_ollama_request(Request("http://localhost:11434/api/tags"), timeout=15)
        == "fixture"
    )
    assert handlers[0].proxies == {}
    assert isinstance(handlers[1], NoRedirects)


def test_french_transport_allows_slow_local_generation(monkeypatch):
    from Backend.Core.france.network import ollama_request

    observed = {}

    def open_request(request, *, timeout):
        observed["url"] = request.full_url
        observed["timeout"] = timeout
        return io.BytesIO(b"{}")

    monkeypatch.setattr(
        "Backend.Core.france.network.open_ollama_request", open_request
    )

    ollama_request(
        "http://localhost:11434/api/chat",
        b"{}",
        {"Content-Type": "application/json"},
    )

    assert observed == {
        "url": "http://localhost:11434/api/chat",
        "timeout": 900,
    }
