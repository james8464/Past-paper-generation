from __future__ import annotations

import io
import json
import subprocess
from types import SimpleNamespace

import pytest

from Backend.Core import ollama_admission as admission
from Backend.Core import providers
from Backend.Core.france.provider import FrenchOllamaClient
from Backend.Core.generation_requests import GenerationRequest

GIB = 1 << 30


@pytest.fixture(autouse=True)
def no_real_resources(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must not inspect this host or contact Ollama")

    monkeypatch.setattr(admission, "_memory_snapshot", forbidden)
    monkeypatch.setattr(admission, "open_ollama_request", forbidden)
    monkeypatch.setattr(admission.platform, "system", lambda: "Darwin")


def resources(monkeypatch, *, ram=18 * GIB, pressure=1, size=8 * GIB):
    monkeypatch.setattr(admission, "_memory_snapshot", lambda: (ram, pressure))
    monkeypatch.setattr(admission, "_installed_model_size", lambda *args: size)


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]", "127.0.0.2"])
def test_fitting_local_model_admitted(monkeypatch, host):
    resources(monkeypatch)
    admission.require_local_ollama_capacity(f"http://{host}:11434", "any-model")


@pytest.mark.parametrize("pressure", [2, 4, 3, 0, None, True, "1"])
def test_non_normal_or_unknown_pressure_refused(monkeypatch, pressure):
    resources(monkeypatch, pressure=pressure)
    with pytest.raises(admission.ResourceAdmissionError, match="memory pressure"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


@pytest.mark.parametrize("ram", [0, -1, None, True, "18000000000"])
def test_unknown_physical_memory_refused(monkeypatch, ram):
    resources(monkeypatch, ram=ram)
    with pytest.raises(admission.ResourceAdmissionError, match="physical memory"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


def test_weight_plus_overhead_boundary(monkeypatch):
    resources(monkeypatch, ram=16 * GIB, size=10 * GIB)
    with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")
    resources(monkeypatch, ram=16 * GIB, size=9 * GIB)
    admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


def test_minimum_reserve_and_overhead_boundary(monkeypatch):
    resources(monkeypatch, ram=8 * GIB, size=2 * GIB)
    admission.require_local_ollama_capacity("http://localhost:11434", "fixture")
    resources(monkeypatch, ram=8 * GIB, size=2 * GIB + 1)
    with pytest.raises(admission.ResourceAdmissionError):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


def test_remote_ollama_does_not_read_local_resources():
    admission.require_local_ollama_capacity("https://remote.example", "fixture")


def test_resource_refusal_has_stable_presentation_code():
    assert admission.ResourceAdmissionError("detail").code == "local_memory_unavailable"


@pytest.mark.parametrize(
    "name", ["namespace/fixture", "namespace/fixture:tag", "fixture:latest"]
)
def test_metadata_resolves_namespaced_and_explicit_tags(monkeypatch, name):
    installed = name if ":" in name else f"{name}:latest"
    content = json.dumps(
        {"models": [{"name": installed, "model": installed, "size": 123}]}
    ).encode()
    monkeypatch.setattr(
        admission, "open_ollama_request", lambda *args, **kwargs: io.BytesIO(content)
    )
    assert admission._installed_model_size("http://localhost:11434", name) == 123


@pytest.mark.parametrize("size", [0, -1, None, True, "123", 1.5])
def test_invalid_size_refused(monkeypatch, size):
    resources(monkeypatch, size=size)
    with pytest.raises(admission.ResourceAdmissionError, match="model size"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


@pytest.mark.parametrize("kind", ["shared", "typed", "french"])
def test_refusal_bypasses_all_repair_and_generation(monkeypatch, kind):
    calls = []

    def refuse(*args):
        calls.append(args)
        raise admission.ResourceAdmissionError("Not enough memory headroom")

    monkeypatch.setattr(providers, "require_local_ollama_capacity", refuse)
    client = (
        FrenchOllamaClient(model="fixture", base_url="http://localhost:11434", seed=1)
        if kind == "french"
        else providers.OllamaClient("http://localhost:11434", "fixture")
    )
    if kind == "french":
        monkeypatch.setattr(
            "Backend.Core.france.provider.response_policy",
            lambda prompt: ({"type": "object"}, 777),
        )
    with pytest.raises(admission.ResourceAdmissionError):
        if kind == "typed":
            client.generate_request(
                GenerationRequest(
                    "Question.", "french_nsi_authoring", {"type": "object"}
                ),
                retries=3,
            )
        else:
            client.generate_json("Independently solve this question.", retries=3)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "provider, method",
    [("apple", "_apple"), ("openai", "_openai"), ("anthropic", "_anthropic")],
)
def test_non_ollama_providers_never_enter_admission(monkeypatch, provider, method):
    def forbidden(*args):
        pytest.fail("Non-Ollama generation entered resource admission")

    monkeypatch.setattr(providers, "require_local_ollama_capacity", forbidden)
    client = providers.HostedLLMClient(provider=provider, model="fixture", api_key="")
    monkeypatch.setattr(client, method, lambda *args: {"answer": 1})
    assert client.generate_json("Question.") == {"answer": 1}


def test_allowed_request_preserves_options_and_prompt(monkeypatch):
    resources(monkeypatch)
    captured = []
    monkeypatch.setattr(
        providers.HostedLLMClient,
        "_ollama_thinking_policy",
        lambda *args: {"requested": False},
    )

    def request(url, data, headers, **kwargs):
        captured.append((url, json.loads(data)))
        return io.BytesIO(
            json.dumps(
                {
                    "message": {"content": '{"answer":1}'},
                    "done": True,
                    "done_reason": "stop",
                }
            ).encode()
        )

    client = providers.OllamaClient("http://localhost:11434", "fixture")
    result = client._ollama(
        "Original prompt.",
        schema={"type": "object"},
        output_budget=777,
        seed=42,
        request_function=request,
    )
    assert result == {"answer": 1}
    assert captured == [
        (
            "http://localhost:11434/api/chat",
            {
                "model": "fixture",
                "messages": [{"role": "user", "content": "Original prompt."}],
                "stream": False,
                "think": False,
                "format": {"type": "object"},
                "options": {
                    "temperature": providers._ollama_temperature("Original prompt."),
                    "top_p": 0.9,
                    "num_ctx": 16384,
                    "num_predict": 777,
                    "repeat_last_n": 256,
                    "repeat_penalty": 1.15,
                    "seed": 42,
                },
            },
        )
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"models": []},
        {"models": [{"name": "fixture:latest", "size": True}]},
        {
            "models": [
                {"name": "fixture:latest", "size": 123},
                {"name": "fixture", "size": 123},
            ]
        },
        {"models": "invalid"},
    ],
)
def test_metadata_missing_malformed_or_ambiguous(monkeypatch, payload):
    monkeypatch.setattr(
        admission,
        "open_ollama_request",
        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()),
    )
    with pytest.raises(admission.ResourceAdmissionError):
        admission._installed_model_size("http://localhost:11434", "fixture")


def test_metadata_uses_bounded_direct_get(monkeypatch):
    captured = []

    def open_request(request, *, timeout):
        captured.append((request.full_url, request.get_method(), timeout))
        return io.BytesIO(b'{"models":[{"name":"fixture:latest","size":123}]}')

    monkeypatch.setattr(admission, "open_ollama_request", open_request)
    assert admission._installed_model_size("http://localhost:11434", "fixture") == 123
    assert captured == [("http://localhost:11434/api/tags", "GET", 5)]


@pytest.mark.parametrize(
    "content", [b"invalid", b"x" * (4 * 1024 * 1024 + 1), b'{"models":[],"models":[]}']
)
def test_metadata_invalid_or_oversized(monkeypatch, content):
    monkeypatch.setattr(
        admission, "open_ollama_request", lambda *args, **kwargs: io.BytesIO(content)
    )
    with pytest.raises(admission.ResourceAdmissionError):
        admission._installed_model_size("http://localhost:11434", "fixture")


def test_metadata_transport_failure_is_resource_refusal(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(admission, "open_ollama_request", fail)
    with pytest.raises(admission.ResourceAdmissionError, match="model size"):
        admission._installed_model_size("http://localhost:11434", "fixture")


def test_native_sensor_commands_bounded_and_numeric(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            stdout=str(18 * GIB if command[-1] == "hw.memsize" else 1)
        )

    monkeypatch.setattr(admission.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(admission.subprocess, "run", run)
    assert admission._read_memory_snapshot() == (18 * GIB, 1)
    assert all(item[1]["timeout"] == 2 for item in calls)
    assert {item[0][-1] for item in calls} == {
        "hw.memsize",
        "kern.memorystatus_vm_pressure_level",
    }


def test_sensor_timeout_refuses_without_guess(monkeypatch):
    monkeypatch.setattr(admission.platform, "system", lambda: "Darwin")

    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired("sysctl", 2)

    monkeypatch.setattr(admission.subprocess, "run", run)
    with pytest.raises(admission.ResourceAdmissionError, match="memory"):
        admission._read_memory_snapshot()


def test_linux_uses_kernel_physical_memory_without_invented_pressure(monkeypatch):
    monkeypatch.setattr(admission.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        admission.Path,
        "read_text",
        lambda *args, **kwargs: "MemTotal:       18874368 kB\nMemAvailable: 10 kB\n",
    )
    assert admission._read_memory_snapshot() == (18 * GIB, None)
    resources(monkeypatch, pressure=None)
    admission.require_local_ollama_capacity("http://localhost:11434", "fixture")
    resources(monkeypatch, pressure=None, size=14 * GIB)
    with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


@pytest.mark.parametrize(
    "content", ["", "MemTotal: unknown kB", "MemTotal: 100 MB", "MemTotal: 0 kB"]
)
def test_linux_unknown_physical_memory_refuses(monkeypatch, content):
    monkeypatch.setattr(admission.platform, "system", lambda: "Linux")
    monkeypatch.setattr(admission.Path, "read_text", lambda *args, **kwargs: content)
    monkeypatch.setattr(admission, "_memory_snapshot", admission._read_memory_snapshot)
    with pytest.raises(admission.ResourceAdmissionError, match="memory"):
        admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


def test_unknown_platform_refuses(monkeypatch):
    monkeypatch.setattr(admission.platform, "system", lambda: "unknown")
    with pytest.raises(admission.ResourceAdmissionError, match="memory"):
        admission._read_memory_snapshot()


def test_native_sensor_cancellation_remains_interruption(monkeypatch):
    interruption = InterruptedError("cancelled")

    def run(*args, **kwargs):
        raise interruption

    monkeypatch.setattr(admission.subprocess, "run", run)
    with pytest.raises(InterruptedError) as caught:
        admission._read_memory_snapshot()
    assert caught.value is interruption


@pytest.mark.parametrize("wrapped", ["none", "url", "runtime"])
def test_metadata_cancellation_remains_interruption(monkeypatch, wrapped):
    from urllib.error import URLError

    interruption = InterruptedError("cancelled")
    error = interruption
    if wrapped == "url":
        error = URLError(interruption)
    elif wrapped == "runtime":
        error = RuntimeError("wrapped")
        error.__cause__ = URLError(interruption)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(admission, "open_ollama_request", fail)
    with pytest.raises(InterruptedError) as caught:
        admission._installed_model_size("http://localhost:11434", "fixture")
    assert caught.value is interruption
