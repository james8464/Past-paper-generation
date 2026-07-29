from __future__ import annotations

import sys
from types import ModuleType

from Backend.Core.providers import HostedLLMClient


def test_apple_provider_loads_model_once(monkeypatch) -> None:
    calls = {"load": 0, "generate": 0}
    module = ModuleType("mlx_lm")

    def load(model_name: str) -> tuple[object, object]:
        calls["load"] += 1
        assert model_name == "test-model"
        return object(), object()

    def generate(
        _model: object,
        _tokenizer: object,
        *,
        prompt: str,
        max_tokens: int,
        verbose: bool,
    ) -> str:
        calls["generate"] += 1
        assert max_tokens == 4096
        assert verbose is False
        return f'{{"prompt": "{prompt}"}}'

    module.load = load
    module.generate = generate
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    client = HostedLLMClient(
        provider="apple",
        model="test-model",
        api_key="",
    )

    assert client.generate_json("first") == {"prompt": "first"}
    assert client.generate_json("second") == {"prompt": "second"}
    assert calls == {"load": 1, "generate": 2}
    assert client.supports_parallel_generation is False


def test_remote_hosted_providers_allow_parallel_generation() -> None:
    assert HostedLLMClient(
        provider="openai",
        model="test-model",
        api_key="test-key",
    ).supports_parallel_generation
    assert HostedLLMClient(
        provider="anthropic",
        model="test-model",
        api_key="test-key",
    ).supports_parallel_generation
