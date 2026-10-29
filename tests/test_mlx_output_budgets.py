import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

from Backend.Core.generation_requests import GenerationRequest
from Backend.Core.mlx_batching import BatchUnavailable, generate_batch
from Backend.Core.providers import HostedLLMClient


def test_typed_apple_request_forwards_its_budget(monkeypatch):
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    seen = []
    monkeypatch.setattr(
        client, "_apple", lambda *args, **kwargs: seen.append(kwargs) or {}
    )
    request = GenerationRequest(
        prompt="Solve the task.",
        operation="solver",
        schema={"type": "object"},
        output_budget=14000,
    )
    assert client.generate_request(request) == {}
    assert seen[0]["output_budget"] == 14000


@pytest.mark.parametrize("budget", [0, -1, True, 16385, 1.5])
def test_invalid_apple_budget_refuses_before_loading_model(monkeypatch, budget):
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(
        client, "_load_apple_model", lambda: pytest.fail("loaded model")
    )
    with pytest.raises(ValueError, match="budget"):
        client._apple("prompt", output_budget=budget)


def test_serial_structured_path_uses_typed_budget(monkeypatch):
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(client, "_load_apple_model", lambda: None)
    seen = []
    monkeypatch.setattr(
        client, "_mlx_structured_response", lambda *args: seen.append(args) or "{}"
    )
    assert client._apple_response("prompt", {"required": ["answer"]}, 12000) == "{}"
    assert seen == [("prompt", {"required": ["answer"]}, 12000)]


def test_serial_fallback_keeps_each_request_budget(monkeypatch):
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(client, "_load_apple_model", lambda: None)
    monkeypatch.setattr(
        client,
        "_mlx_batch_structured_responses",
        lambda *args: (_ for _ in ()).throw(BatchUnavailable("memory")),
    )
    seen = []
    monkeypatch.setattr(
        client, "_apple_response", lambda *args: seen.append(args) or args[0]
    )
    requests = [
        ("first", {"required": ["a"]}, 14000),
        ("second", {"required": ["b"]}, 6000),
    ]
    assert client._run_apple_batch(requests, Event()) == ["first", "second"]
    assert seen == requests


def test_opt_in_queue_keeps_typed_budgets_separate(monkeypatch):
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", "1")
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    seen = []

    def batch(requests, cancelled):
        seen.extend(requests)
        return [json.dumps({"answer": str(request[2])}) for request in requests]

    monkeypatch.setattr(client, "_run_apple_batch", batch)
    barrier = Barrier(2)

    def call(budget):
        barrier.wait(timeout=2)
        return client.generate_request(
            GenerationRequest(
                prompt="Solve the task.",
                operation="solver",
                schema={
                    "type": "object",
                    "required": ["answer"],
                    "properties": {"answer": {"type": "string"}},
                },
                output_budget=budget,
            )
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            assert list(workers.map(call, [14000, 6000])) == [
                {"answer": "14000"},
                {"answer": "6000"},
            ]
        assert sorted(request[2] for request in seen) == [6000, 14000]
    finally:
        assert client._apple_batcher is not None
        client._apple_batcher.close()


class Tokenizer:
    bos_token = None
    eos_token_ids = (0,)

    def encode(self, text, **kwargs):
        return [1] * len(text)

    def decode(self, tokens):
        return ""


def test_batch_passes_unequal_budgets_to_corresponding_uids():
    seen = {}

    class Generator:
        def __init__(self, model, **kwargs):
            seen["constructor"] = kwargs
            self.rows = iter(
                [
                    [
                        SimpleNamespace(uid=9, token=0, finish_reason="stop"),
                        SimpleNamespace(uid=3, token=0, finish_reason="stop"),
                    ],
                    [],
                ]
            )

        def insert(self, prompts, **kwargs):
            seen["insert"] = kwargs
            return [9, 3]

        def next(self):
            return next(self.rows)

        def close(self):
            pass

    assert generate_batch(
        object(),
        Tokenizer(),
        ["a", "b"],
        [object(), object()],
        Event(),
        output_budgets=[6000, 1200],
        generator_factory=Generator,
    ) == ["", ""]
    assert seen["constructor"]["max_tokens"] == 6000
    assert seen["insert"]["max_tokens"] == [6000, 1200]


def test_pair_context_and_output_memory_bound_refuses_before_generator():
    with pytest.raises(BatchUnavailable, match="context"):
        generate_batch(
            object(),
            Tokenizer(),
            ["a", "b"],
            [object(), object()],
            Event(),
            output_budgets=[14000, 12000],
            generator_factory=lambda *args, **kwargs: pytest.fail("allocated pair"),
        )


@pytest.mark.parametrize(
    "budgets", [[True, 1], [None, 1], [0, 1], [16385, 1], [1], [1, 2, 3]]
)
def test_invalid_batch_budgets_are_rejected(budgets):
    with pytest.raises(ValueError, match="budget"):
        generate_batch(
            object(),
            Tokenizer(),
            ["a", "b"],
            [object(), object()],
            Event(),
            output_budgets=budgets,
            generator_factory=lambda *args, **kwargs: pytest.fail("allocated pair"),
        )
