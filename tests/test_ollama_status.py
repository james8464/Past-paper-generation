"""Malformed local metadata is unavailable, never a healthy model catalogue."""

import argparse
import io
import json

import pytest

from Backend.Core import ollama


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "not-an-object",
        {},
        {"models": None},
        {"models": {}},
        {"models": [None]},
        {"models": [{"name": True}]},
        {"models": [{"name": "  "}]},
        {"models": [{}]},
    ],
)
def test_unexpected_json_shape_returns_unavailable(monkeypatch, payload):
    monkeypatch.setattr(
        ollama.urllib.request,
        "urlopen",
        lambda *a, **k: io.BytesIO(json.dumps(payload).encode()),
    )
    assert ollama.api_models() is None


@pytest.mark.parametrize("body", [b"\xff", b"{bad json"])
def test_bad_utf8_and_json_are_unavailable(monkeypatch, body):
    monkeypatch.setattr(
        ollama.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(body)
    )
    assert ollama.api_models() is None


def test_valid_empty_and_named_catalogues_preserve_exact_names(monkeypatch):
    for models in ([], [{"name": "fixture:7b", "details": {}}]):
        monkeypatch.setattr(
            ollama.urllib.request,
            "urlopen",
            lambda *a, models=models, **k: io.BytesIO(
                json.dumps({"models": models}).encode()
            ),
        )
        assert ollama.api_models() == [model["name"] for model in models]


def test_unexpected_programmer_error_is_not_swallowed(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("programming defect")

    monkeypatch.setattr(ollama.urllib.request, "urlopen", broken)
    with pytest.raises(RuntimeError, match="programming defect"):
        ollama.api_models()


def test_malformed_catalogue_uses_existing_cli_fallback(monkeypatch, capsys):
    monkeypatch.setattr(
        ollama.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b'{"models":null}')
    )
    monkeypatch.setattr(ollama, "ollama_command", lambda: None)
    assert ollama.handle_list_models(argparse.Namespace()) == 0
    assert json.loads(capsys.readouterr().out)["models"] == []
