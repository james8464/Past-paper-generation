"""Discovery stays on its configured endpoint; fixtures never contact Ollama."""

import argparse
import io
import json
import os
from urllib.error import URLError

import pytest

from Backend.Core import ollama
from Backend.Core.cli import build_parser


def transport(monkeypatch, *, failure=False):
    seen = []

    def open_request(request, **_kwargs):
        seen.append(getattr(request, "full_url", request))
        if failure:
            raise URLError("fixture unavailable")
        return io.BytesIO(b'{"models":[{"name":"fixture:latest"}]}')

    monkeypatch.setattr(ollama.urllib.request, "urlopen", open_request)
    monkeypatch.setattr(ollama, "open_ollama_request", open_request, raising=False)
    return seen


@pytest.mark.parametrize("command", ["ollama-status", "list-models"])
def test_cli_discovery_accepts_configured_url_and_explicit_remote_consent(command):
    args = build_parser().parse_args(
        [command, "--ollama-url", "http://127.0.0.1:11435"]
    )
    assert args.ollama_url == "http://127.0.0.1:11435"
    assert args.allow_remote is False
    remote = build_parser().parse_args(
        [command, "--ollama-url", "https://fixture.example", "--allow-remote"]
    )
    assert remote.allow_remote is True


@pytest.mark.parametrize(
    "handler", [ollama.handle_ollama_status, ollama.handle_list_models]
)
def test_discovery_queries_custom_port_not_default(monkeypatch, capsys, handler):
    seen = transport(monkeypatch)
    assert handler(argparse.Namespace(ollama_url="http://127.0.0.1:11435/")) == 0
    assert seen == ["http://127.0.0.1:11435/api/tags"]
    event = json.loads(capsys.readouterr().out)
    assert event.get("running", True) is True
    assert event.get("models", ["fixture:latest"]) == ["fixture:latest"]


@pytest.mark.parametrize(
    "url", [None, "http://localhost:11434", "http://127.0.0.1:11434/"]
)
def test_default_discovery_compatibility(monkeypatch, capsys, url):
    seen = transport(monkeypatch)
    args = argparse.Namespace() if url is None else argparse.Namespace(ollama_url=url)
    assert ollama.handle_list_models(args) == 0
    expected = (url or ollama.OLLAMA_API).rstrip("/") + "/api/tags"
    assert seen == [expected]
    assert json.loads(capsys.readouterr().out)["models"] == ["fixture:latest"]


@pytest.mark.parametrize(
    "handler", [ollama.handle_ollama_status, ollama.handle_list_models]
)
def test_failed_custom_endpoint_never_falls_back_to_default_cli(
    monkeypatch, capsys, handler
):
    seen = transport(monkeypatch, failure=True)
    monkeypatch.setattr(
        ollama, "ollama_command", lambda: pytest.fail("default CLI fallback")
    )
    result = handler(argparse.Namespace(ollama_url="http://127.0.0.1:11435"))
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert seen == ["http://127.0.0.1:11435/api/tags"]
    if handler is ollama.handle_ollama_status:
        assert events[0]["running"] is False
    else:
        assert result == 1
        assert events[0]["models"] == []
        assert events[-1]["type"] == "error"


def test_malformed_custom_catalogue_never_uses_cli(monkeypatch, capsys):
    monkeypatch.setattr(
        ollama, "open_ollama_request", lambda *_a, **_k: io.BytesIO(b'{"models":null}')
    )
    monkeypatch.setattr(
        ollama, "ollama_command", lambda: pytest.fail("default CLI fallback")
    )
    assert (
        ollama.handle_list_models(
            argparse.Namespace(ollama_url="http://localhost:11435")
        )
        == 1
    )
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[0]["models"] == []


@pytest.mark.parametrize("url", ["http://localhost:11434", "http://127.0.0.1:11434/"])
def test_default_endpoint_still_has_legacy_cli_fallback(monkeypatch, capsys, url):
    from types import SimpleNamespace

    transport(monkeypatch, failure=True)
    calls = []
    monkeypatch.setattr(ollama, "ollama_command", lambda: "fixture-ollama")

    def run(command, **_kwargs):
        calls.append(command)
        return SimpleNamespace(stdout="NAME ID\nlegacy:latest fixture\n")

    monkeypatch.setattr(ollama.subprocess, "run", run)
    assert ollama.handle_list_models(argparse.Namespace(ollama_url=url)) == 0
    assert calls == [["fixture-ollama", "list"]]
    assert json.loads(capsys.readouterr().out)["models"] == ["legacy:latest"]


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/fixture",
        "http://user:secret@localhost:11435",
        "http://localhost:bad",
        "http://localhost:0",
        "http://localhost:70000",
        "http://localhost:11435/path",
        "http://localhost:11435?token=secret",
        "http://localhost:11435#fragment",
        "https://fixture.example",
        "http://fixture.example",
    ],
)
def test_invalid_or_unconsented_remote_endpoint_refuses_before_io(monkeypatch, url):
    seen = transport(monkeypatch)
    with pytest.raises(ValueError):
        ollama.api_models(url)
    assert seen == []


def test_remote_discovery_requires_consent_and_https(monkeypatch):
    seen = transport(monkeypatch)
    assert ollama.api_models("https://fixture.example", allow_remote=True) == [
        "fixture:latest"
    ]
    with pytest.raises(ValueError):
        ollama.api_models("http://fixture.example", allow_remote=True)
    assert seen == ["https://fixture.example/api/tags"]


def test_discovery_uses_existing_no_proxy_no_redirect_transport(monkeypatch):
    from Backend.Core.france import network

    seen = []

    class Opener:
        def open(self, request, *, timeout):
            seen.append((request.full_url, timeout))
            return io.BytesIO(b'{"models":[]}')

    def build(*handlers):
        assert any(
            isinstance(item, network.ProxyHandler) and item.proxies == {}
            for item in handlers
        )
        assert any(isinstance(item, network.NoRedirects) for item in handlers)
        return Opener()

    monkeypatch.setattr(network, "build_opener", build)
    monkeypatch.setattr(
        ollama.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("default opener"),
    )
    assert ollama.api_models("http://127.0.0.1:11435") == []
    assert seen == [("http://127.0.0.1:11435/api/tags", 5)]


@pytest.mark.parametrize(
    "endpoint",
    ["http://localhost:11434", "http://127.0.0.1:11435", "http://[::1]:11436/"],
)
def test_pull_routes_owned_child_to_selected_local_endpoint(monkeypatch, endpoint):
    from Backend.Core import events
    from tests.test_events_subprocess import FakeChild

    monkeypatch.setenv("OLLAMA_HOST", "https://unselected.example")
    monkeypatch.setenv("KELDIN_FIXTURE_KEEP", "preserved")
    monkeypatch.setattr(ollama, "ollama_command", lambda: "/fixture/ollama")
    child = FakeChild()
    child.wait = lambda timeout=None: 0
    calls = []

    def spawn(command, **kwargs):
        calls.append((command, kwargs))
        return child

    monkeypatch.setattr(events.subprocess, "Popen", spawn)
    args = build_parser().parse_args(
        ["pull-model", "--model", "fixture:latest", "--ollama-url", endpoint]
    )
    assert ollama.handle_pull_model(args) == 0
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == ["/fixture/ollama", "pull", "fixture:latest"]
    assert kwargs["env"]["OLLAMA_HOST"] == endpoint.rstrip("/")
    assert kwargs["env"]["KELDIN_FIXTURE_KEEP"] == "preserved"
    assert os.environ["OLLAMA_HOST"] == "https://unselected.example"
    assert child.stdout.closed


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://remote.example",
        "http://remote.example",
        "http://user:secret@localhost:11434",
        "http://localhost:0",
    ],
)
def test_pull_refuses_remote_or_invalid_endpoint_before_child_lookup(
    monkeypatch, endpoint
):
    monkeypatch.setattr(ollama, "ollama_command", lambda: pytest.fail("child lookup"))
    with pytest.raises(ValueError):
        ollama.handle_pull_model(
            argparse.Namespace(model="fixture", ollama_url=endpoint)
        )


@pytest.mark.parametrize(
    "handler", [ollama.handle_ollama_status, ollama.handle_list_models]
)
def test_default_cli_discovery_fallback_overrides_inherited_alternate_host(
    monkeypatch, handler
):
    from types import SimpleNamespace

    transport(monkeypatch, failure=True)
    monkeypatch.setenv("OLLAMA_HOST", "https://unselected.example")
    monkeypatch.setattr(ollama, "ollama_command", lambda: "/fixture/ollama")
    seen = []

    def run(command, **kwargs):
        seen.append(kwargs["env"]["OLLAMA_HOST"])
        return SimpleNamespace(stdout="NAME ID\nfixture:latest id\n")

    monkeypatch.setattr(ollama.subprocess, "run", run)
    assert handler(argparse.Namespace(ollama_url="http://127.0.0.1:11434/")) == 0
    assert seen == ["http://127.0.0.1:11434"]
