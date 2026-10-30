import io
import json
from argparse import Namespace
from urllib.error import HTTPError

import pytest

from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.providers import HostedLLMClient, urllib_request

KEY = "fixture-secret-not-a-real-credential"
SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "additionalProperties": False,
    "properties": {"answer": {"type": "integer"}},
}


def typed_request(schema=SCHEMA):
    return GenerationRequest(
        "Return the answer as JSON.", "french_nsi_authoring", schema, output_budget=8192
    )


def response(**updates):
    return {
        "id": "fixture-response",
        "status": "completed",
        "model": "deepseek-flash",
        "output": [
            {
                "type": "reasoning",
                "content": [{"type": "reasoning_text", "text": "not the answer"}],
            },
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": '{"answer":42}'}],
            },
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 200,
            "input_tokens_details": {"cached_tokens": 20},
            "output_tokens_details": {"reasoning_tokens": 150},
        },
        **updates,
    }


def mock_transport(monkeypatch, envelope):
    calls = []

    def send(url, data, headers, **kwargs):
        calls.append((url, json.loads(data), headers, kwargs))
        return io.BytesIO(json.dumps(envelope).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    return calls


def client(**kwargs):
    return HostedLLMClient(
        provider="deepseek", model="deepseek-flash", api_key=KEY, **kwargs
    )


def test_typed_vendor_payload_is_fixed_schema_bound_and_budgeted(monkeypatch):
    calls = mock_transport(monkeypatch, response())
    actual = client(base_url="https://unrelated.invalid").generate_request(
        typed_request()
    )
    assert actual == {"answer": 42}
    url, body, headers, options = calls[0]
    assert url == "https://api.deepseek.com/responses"
    assert body == {
        "model": "deepseek-flash",
        "input": typed_request().prompt,
        "stream": False,
        "reasoning": {"effort": "low"},
        "max_output_tokens": 8192,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "keldin_generation",
                "schema": SCHEMA,
            }
        },
    }
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert options == {
        "attempts": 1,
        "timeout_seconds": 600,
        "fixed_host": "api.deepseek.com",
        "secrets": (KEY,),
    }
    assert len(calls) == 1


@pytest.mark.parametrize(
    "updates,kind",
    [
        ({"status": "incomplete"}, "provider_structure"),
        (
            {
                "status": "completed",
                "incomplete_details": {"reason": "max_output_tokens"},
            },
            "provider_structure",
        ),
        ({"model": "different-model"}, "provider_identity"),
        ({"usage": {}}, "provider_usage"),
        ({"usage": {"input_tokens": 100, "output_tokens": 0}}, "provider_usage"),
        ({"usage": {"input_tokens": True, "output_tokens": 1}}, "provider_usage"),
        ({"usage": {"input_tokens": 100, "output_tokens": 8193}}, "provider_usage"),
        (
            {
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "output_tokens_details": {"reasoning_tokens": 201},
                }
            },
            "provider_usage",
        ),
    ],
)
def test_incomplete_identity_or_usage_failures_never_retry(monkeypatch, updates, kind):
    calls = mock_transport(monkeypatch, response(**updates))
    with pytest.raises(GenerationEvidenceError) as failure:
        client().generate_request(typed_request())
    assert failure.value.details["kind"] == kind
    assert len(calls) == 1
    assert KEY not in str(failure.value) + json.dumps(failure.value.details)


@pytest.mark.parametrize(
    "text",
    [
        '{"answer":"wrong type"}',
        '{"answer":42,"answer":43}',
        'prefix {"answer":42}',
        "{}",
        "",
    ],
)
def test_untrusted_candidate_requires_exact_original_schema_and_strict_json(
    monkeypatch, text
):
    calls = mock_transport(
        monkeypatch,
        response(
            output=[
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": text}],
                }
            ]
        ),
    )
    with pytest.raises(GenerationEvidenceError, match="structured"):
        client().generate_request(typed_request())
    assert len(calls) == 1


@pytest.mark.parametrize(
    "model,key",
    [
        ("deepseek-flash", ""),
        ("deepseek-flash", "  "),
        ("deepseek-chat", KEY),
        ("local-model", KEY),
    ],
)
def test_missing_key_or_unsupported_model_refuses_before_network(
    monkeypatch, model, key
):
    calls = mock_transport(monkeypatch, response())
    with pytest.raises(ValueError):
        HostedLLMClient(provider="deepseek", model=model, api_key=key).generate_request(
            typed_request()
        )
    assert not calls


def test_remote_schema_reference_refuses_before_network(monkeypatch):
    calls = mock_transport(monkeypatch, response())
    with pytest.raises(ValueError, match="reference"):
        client().generate_request(
            typed_request(
                {"type": "object", "$ref": "https://unrelated.invalid/schema"}
            )
        )
    assert not calls


def test_only_french_cli_advertises_deepseek(capsys):
    from Backend.Core.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "generate-assessment",
            "--assessment",
            "fr-bac-general-nsi-written-2027",
            "--reference-index",
            "fixture.sqlite",
            "--seed",
            "42",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-flash",
        ]
    )
    assert args.provider == "deepseek"
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["generate", "--subject", "economics_aqa", "--provider", "deepseek"]
        )
    assert "--provider: invalid choice: 'deepseek'" in capsys.readouterr().err


@pytest.mark.parametrize("key", ["", "   "])
def test_french_missing_vendor_key_prevents_launch_and_output(
    monkeypatch, tmp_path, capsys, key
):
    from Backend.Core.france import llm_runtime

    index = tmp_path / "references.sqlite"
    index.touch()
    monkeypatch.setattr(
        llm_runtime,
        "HostedLLMClient",
        lambda **kwargs: pytest.fail("launched provider"),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        provider="deepseek",
        model="deepseek-flash",
        seed=42,
        reference_index=index,
        output=tmp_path / "output",
        api_key=key,
    )
    assert llm_runtime.handle_generate_llm_assessment(args) == 1
    assert not args.output.exists()
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert "clé" in events[-1]["message"]


@pytest.mark.parametrize(
    "url",
    [
        "https://unrelated.invalid/responses",
        "http://api.deepseek.com/responses",
        "https://api.deepseek.com:444/responses",
        "https://api.deepseek.com/responses?key=fixture",
        "https://api.deepseek.com/responses#fragment",
        "https://name@api.deepseek.com/responses",
    ],
)
def test_fixed_host_transport_refuses_wrong_destination_before_open(monkeypatch, url):
    monkeypatch.setattr(
        "urllib.request.build_opener", lambda *args: pytest.fail("opened transport")
    )
    with pytest.raises(ValueError, match="host"):
        urllib_request(
            url,
            b"{}",
            {},
            fixed_host="api.deepseek.com",
        )


def test_usage_is_recorded_without_reasoning_text_or_headers(monkeypatch, capsys):
    mock_transport(monkeypatch, response())
    provider = client()
    provider.generate_request(typed_request())
    event = json.loads(capsys.readouterr().out)
    assert event["usage"] == provider.usage_records[0]
    assert event["usage"]["input_tokens"] == 100
    assert event["usage"]["reasoning_tokens"] == 150
    assert event["usage"]["cached_tokens"] == 20
    assert "not the answer" not in json.dumps(event) and KEY not in json.dumps(event)


@pytest.mark.parametrize("budget", [8192, 6000, 4096])
def test_french_low_effort_preserves_each_tasks_shared_output_allowance(
    monkeypatch, budget
):
    calls = mock_transport(monkeypatch, response())
    request = GenerationRequest(
        "Return JSON.", "french_nsi_authoring", SCHEMA, output_budget=budget
    )
    assert client().generate_request(request) == {"answer": 42}
    assert calls[0][1]["reasoning"] == {"effort": "low"}
    assert calls[0][1]["max_output_tokens"] == budget


def test_other_typed_deepseek_tasks_keep_the_existing_effort_policy(monkeypatch):
    calls = mock_transport(monkeypatch, response())
    request = GenerationRequest("Return JSON.", "solver", SCHEMA, output_budget=8192)
    assert client().generate_request(request) == {"answer": 42}
    assert calls[0][1]["reasoning"] == {"effort": "high"}


def test_pro_is_an_explicit_supported_model_not_a_silent_fallback(monkeypatch):
    calls = mock_transport(monkeypatch, response(model="deepseek-v4-pro"))
    provider = HostedLLMClient(
        provider="deepseek", model="deepseek-v4-pro", api_key=KEY
    )
    assert provider.generate_request(typed_request()) == {"answer": 42}
    assert calls[0][1]["model"] == "deepseek-v4-pro"


def test_fixed_vendor_transport_disallows_redirects_and_redacts_exact_secret(
    monkeypatch,
):
    handlers = []

    class Opener:
        def open(self, request, *, timeout):
            assert request.full_url == "https://api.deepseek.com/responses"
            raise HTTPError(
                request.full_url,
                401,
                "Denied",
                {},
                io.BytesIO(f"rejected credential {KEY}".encode()),
            )

    def opener(handler):
        handlers.append(handler)
        return Opener()

    monkeypatch.setattr("urllib.request.build_opener", opener)
    with pytest.raises(RuntimeError) as error:
        urllib_request(
            "https://api.deepseek.com/responses",
            b"{}",
            {},
            attempts=1,
            fixed_host="api.deepseek.com",
            secrets=(KEY,),
        )
    assert KEY not in str(error.value) and "[redacted]" in str(error.value)
    assert (
        handlers[0].redirect_request(
            None, None, 302, "Found", {}, "https://unrelated.invalid"
        )
        is None
    )


def test_vendor_echo_cannot_leak_credentials_through_usage_or_errors(
    monkeypatch, capsys
):
    mock_transport(monkeypatch, response(id=KEY, model=KEY))
    with pytest.raises(GenerationEvidenceError) as error:
        client().generate_request(typed_request())
    assert (
        KEY
        not in str(error.value)
        + json.dumps(error.value.details)
        + capsys.readouterr().out
    )


def test_french_package_keeps_the_requested_vendor_identity(tmp_path):
    from tests.test_french_llm_pipeline import Client, generate

    provider = Client()
    provider.provider = "deepseek"
    provider.model = "deepseek-flash"
    package = generate(tmp_path, provider)
    assert package["identity"]["provider"] == "deepseek"
    assert package["identity"]["model"] == "deepseek-flash"
    assert package["status"] == "unreviewed_draft"
    assert package["teacher_review"] == package["empirical_calibration"] == "not_run"


def test_untyped_generation_does_not_guess_a_vendor_schema(monkeypatch):
    calls = mock_transport(monkeypatch, response())
    with pytest.raises(ValueError, match="typed"):
        client().generate_json("Legacy prompt")
    assert not calls


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_json_numeric_constants_refuse_even_without_a_property_type(
    monkeypatch, constant
):
    mock_transport(
        monkeypatch,
        response(
            output=[
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": '{"answer":' + constant + "}"}
                    ],
                }
            ]
        ),
    )
    with pytest.raises(GenerationEvidenceError, match="structured"):
        client().generate_request(typed_request({"type": "object"}))
