import io
import json
from hashlib import sha256

import pytest

from Backend.Core.france.pipeline import _prompt


def test_french_transport_retains_each_rejected_raw_response(monkeypatch):
    from Backend.Core.france.graph_tree_authoring import part_selection_prompt
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _tasks_for_seed
    from Backend.Core.france.provider import FrenchOllamaClient
    from Backend.Core.generation_diagnostics import GenerationEvidenceError

    responses = iter(
        [
            {
                "done": False,
                "done_reason": "length",
                "message": {"content": '{"questions":'},
            },
            {"done": True, "done_reason": "stop", "message": {"content": "{bad json}"}},
        ]
    )

    def request(url, data, headers, **kwargs):
        return io.BytesIO(json.dumps(next(responses)).encode())

    monkeypatch.setattr("Backend.Core.france.provider.ollama_request", request)
    client = FrenchOllamaClient(
        model="fixture", base_url="http://localhost:11434", seed=42
    )
    prompt = part_selection_prompt(
        "A", _tasks_for_seed(270100)[0], build_graph_tree_contract(270100, "1"), []
    )
    with pytest.raises(GenerationEvidenceError) as caught:
        client.generate_json(prompt)
    attempts = caught.value.details["attempts"]
    assert [item["raw_response"] for item in attempts] == [
        '{"questions":',
        "{bad json}",
    ]
    assert [item["raw_response_sha256"] for item in attempts] == [
        sha256(item["raw_response"].encode()).hexdigest() for item in attempts
    ]
    assert [item["attempt"] for item in attempts] == [1, 2]
    assert attempts[0]["prompt_sha256"] == sha256(prompt.encode()).hexdigest()
    assert attempts[1]["prompt_sha256"] != attempts[0]["prompt_sha256"]
    assert attempts[0]["stop_reason"] == "length"
    assert "incomplete" in attempts[0]["error"]


@pytest.mark.parametrize(
    "wrapper",
    ["A et F sont directement reliés. {}", "```json\n{}\n```", "{} commentaire libre"],
)
def test_french_selection_transport_rejects_json_wrapped_in_prose(monkeypatch, wrapper):
    from Backend.Core.france.graph_tree_authoring import part_selection_prompt
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _tasks_for_seed
    from Backend.Core.france.provider import FrenchOllamaClient
    from Backend.Core.generation_diagnostics import GenerationEvidenceError

    def request(url, data, headers, **kwargs):
        return io.BytesIO(
            json.dumps(
                {"done": True, "done_reason": "stop", "message": {"content": wrapper}}
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.france.provider.ollama_request", request)
    client = FrenchOllamaClient(
        model="fixture", base_url="http://localhost:11434", seed=42
    )
    prompt = part_selection_prompt(
        "A", _tasks_for_seed(270100)[0], build_graph_tree_contract(270100, "1"), []
    )
    with pytest.raises(GenerationEvidenceError) as caught:
        client.generate_json(prompt)
    assert [item["raw_response"] for item in caught.value.details["attempts"]] == [
        wrapper,
        wrapper,
    ]


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
    assert "materials" in payload["format"]["required"]
    assert payload["format"]["properties"]["materials"]["minItems"] == 1
    assert {"material_ids", "verification"} <= set(
        payload["format"]["$defs"]["NSIQuestion"]["required"]
    )
    prompt_schema = json.loads(
        prompt.split("schéma JSON :\n", 1)[1].split("\nDONNÉES_JSON", 1)[0]
    )
    assert payload["format"] == prompt_schema
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

    monkeypatch.setattr("Backend.Core.france.network.open_ollama_request", open_request)

    ollama_request(
        "http://localhost:11434/api/chat",
        b"{}",
        {"Content-Type": "application/json"},
    )

    assert observed == {
        "url": "http://localhost:11434/api/chat",
        "timeout": 900,
    }


def test_alignment_transport_requires_per_question_evidence():
    from Backend.Core.france.provider import response_policy

    prompt = (
        "Contrôle indépendant des capacités\nDONNÉES_JSON\n"
        '{"question_blueprint":[{"id":"1a","required_curriculum_code":"SD-GRAPHE"}]}'
    )
    schema, budget = response_policy(prompt)
    item = schema["properties"]["questions"]["items"]
    assert set(item["required"]) == {
        "question_id",
        "objective_code",
        "aligned",
        "rationale",
        "issues",
    }
    assert budget >= 2048


def test_repair_transport_requires_material_and_verification_contracts():
    from Backend.Core.france.provider import response_policy

    schema, budget = response_policy(
        'Répare uniquement la question\nDONNÉES_JSON\n{"question":{"id":"1a"}}'
    )
    assert {"material_ids", "verification"} <= set(schema["required"])
    assert budget >= 2048


def test_marking_repair_uses_french_question_schema_without_uk_fallback():
    from Backend.Core.france.provider import response_policy
    from Backend.Core.france.question_review import repair_marking_prompt

    prompt = repair_marking_prompt(
        {
            "id": "1a",
            "points": "0.5",
            "marking": [{"points": "0", "criterion": "Résultat."}],
        },
        {"id": "1a", "points": "0.5"},
    )
    schema, budget = response_policy(prompt)
    assert schema["title"] == "NSIQuestion"
    assert {"material_ids", "verification"} <= set(schema["required"])
    assert budget >= 2048
