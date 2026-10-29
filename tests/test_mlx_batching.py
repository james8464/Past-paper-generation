from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import CancelledError, ThreadPoolExecutor
from threading import Barrier, Event, get_ident
from types import ModuleType, SimpleNamespace

import pytest

from Backend.Core.mlx_batching import BatchUnavailable, CoalescingRunner, generate_batch
from Backend.Core.providers import HostedLLMClient
from Backend.Core.review_workers import local_generation_workers


def test_two_callers_share_one_owner_and_get_ordered_individual_results():
    batches = []
    caller_threads = []
    barrier = Barrier(2)

    def batch(values, _cancelled):
        batches.append((get_ident(), values))
        return [value * 10 for value in values]

    runner = CoalescingRunner(batch, wait_seconds=0.1)

    def call(value):
        caller_threads.append(get_ident())
        barrier.wait(timeout=2)
        return runner.call(value)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(call, [1, 2])) == [10, 20]
        assert len(batches) == 1
        assert sorted(batches[0][1]) == [1, 2]
        assert batches[0][0] not in caller_threads
    finally:
        runner.close()


def test_bad_request_does_not_poison_neighbour_or_future_request():
    runner = CoalescingRunner(
        lambda values, _: [
            ValueError("bad") if value == 1 else value for value in values
        ]
    )
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(runner.call, 1), pool.submit(runner.call, 2)
            with pytest.raises(ValueError, match="bad"):
                first.result(timeout=2)
            assert second.result(timeout=2) == 2
        assert runner.call(3) == 3
    finally:
        runner.close()


def test_close_releases_waiters_and_refuses_new_work():
    started = Event()

    def batch(values, cancelled):
        started.set()
        assert cancelled.wait(timeout=2)
        return values

    runner = CoalescingRunner(batch)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runner.call, 1)
        assert started.wait(timeout=2)
        runner.close()
        with pytest.raises(Exception, match="cancelled"):
            future.result(timeout=2)
    with pytest.raises(Exception, match="cancelled"):
        runner.call(2)


def test_main_process_cancellation_does_not_wait_on_owner():
    script = """
import signal, time
from threading import Timer
from Backend.Core.mlx_batching import CoalescingRunner
def cancelled(*_): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
runner = CoalescingRunner(lambda values, _: (time.sleep(30), values)[1])
timer = Timer(0.1, lambda: signal.raise_signal(signal.SIGTERM))
timer.daemon = True
timer.start()
try: runner.call(1)
except KeyboardInterrupt: pass
"""
    subprocess.run([sys.executable, "-c", script], check=True, timeout=3)


class Tokenizer:
    eos_token_ids = (0,)
    bos_token = None

    def encode(self, text, **_kwargs):
        return [ord(char) for char in text]

    def decode(self, tokens):
        return "".join(chr(token) for token in tokens)


def test_batch_uses_separate_processors_and_uid_order_and_always_closes():
    captured = {}

    class Generator:
        def __init__(self, model, **kwargs):
            captured.update(kwargs)
            self.rows = iter(
                [
                    [SimpleNamespace(uid=3, token=ord("B"), finish_reason=None)],
                    [SimpleNamespace(uid=17, token=ord("A"), finish_reason=None)],
                    [
                        SimpleNamespace(uid=3, token=0, finish_reason="stop"),
                        SimpleNamespace(uid=17, token=0, finish_reason="stop"),
                    ],
                    [],
                ]
            )

        def insert(self, prompts, **kwargs):
            captured.update(kwargs)
            captured["prompts"] = prompts
            return [17, 3]

        def next(self):
            return next(self.rows)

        def close(self):
            captured["closed"] = True

    processors = [object(), object()]
    assert generate_batch(
        object(),
        Tokenizer(),
        ["first", "second"],
        processors,
        Event(),
        generator_factory=Generator,
    ) == ["A", "B"]
    assert captured["logits_processors"] == [[processors[0]], [processors[1]]]
    assert captured["completion_batch_size"] == captured["prefill_batch_size"] == 2
    assert captured["closed"]


def test_large_pair_refuses_batch_before_constructing_generator():
    with pytest.raises(BatchUnavailable, match="context"):
        generate_batch(
            object(),
            Tokenizer(),
            ["a" * 5000, "b" * 5000],
            [object(), object()],
            Event(),
            generator_factory=lambda *args, **kwargs: pytest.fail(
                "large pair was batched"
            ),
        )


@pytest.mark.parametrize("enabled", ["0", "1"])
def test_mlx_requires_its_own_captured_opt_in(monkeypatch, enabled):
    monkeypatch.setenv("KELDIN_PARALLEL_LOCAL_REVIEWS", "1")
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", enabled)
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", "0")
    assert client.parallel_review_workers == 1
    assert client.parallel_generation_workers == (2 if enabled == "1" else 1)
    assert local_generation_workers(client) == client.parallel_generation_workers
    assert client.supports_parallel_generation is False


def test_each_batched_response_keeps_its_schema_and_failure_isolation(monkeypatch):
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", "1")
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    calls = []

    def batch(requests, _cancelled):
        calls.append((get_ident(), requests))
        return [
            json.dumps(
                {
                    "answer": "wrong"
                    if prompt.startswith("bad")
                    else schema["properties"]["answer"]["enum"][0]
                }
            )
            for prompt, schema in requests
        ]

    monkeypatch.setattr(client, "_run_apple_batch", batch)
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"enum": ["valid"]}},
        "additionalProperties": False,
    }
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            bad = pool.submit(client._apple, "bad", schema=schema, identifiers=())
            good = pool.submit(client._apple, "good", schema=schema, identifiers=())
            with pytest.raises(ValueError, match="required output schema"):
                bad.result(timeout=2)
            assert good.result(timeout=2) == {"answer": "valid"}
        assert client._apple("again", schema=schema, identifiers=()) == {
            "answer": "valid"
        }
        assert len({thread for thread, _ in calls}) == 1
    finally:
        assert client._apple_batcher is not None
        client._apple_batcher.close()


def test_unbatchable_pair_uses_the_existing_constrained_serial_path(monkeypatch):
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(client, "_load_apple_model", lambda: None)
    monkeypatch.setattr(
        client,
        "_mlx_batch_structured_responses",
        lambda *args: (_ for _ in ()).throw(BatchUnavailable("cache")),
    )
    requests = [("first", {"required": ["a"]}), ("second", {"required": ["b"]})]
    seen = []

    def serial(prompt, schema):
        seen.append((prompt, schema))
        assert schema["required"]
        return prompt

    monkeypatch.setattr(client, "_apple_response", serial)
    assert client._run_apple_batch(requests, Event()) == ["first", "second"]
    assert seen == requests


def test_fallback_still_loads_one_model_on_one_owner_thread(monkeypatch):
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", "1")
    module = ModuleType("mlx_lm")
    loaded = []

    def load(path, **kwargs):
        loaded.append((get_ident(), path, kwargs))
        return object(), object()

    module.load = load
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model", lambda _: "/local/model"
    )
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(
        client,
        "_mlx_batch_structured_responses",
        lambda *args: (_ for _ in ()).throw(BatchUnavailable("cache")),
    )
    threads = []

    def constrained(prompt, schema):
        threads.append(get_ident())
        return '{"answer":"valid"}'

    monkeypatch.setattr(client, "_mlx_structured_response", constrained)
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string"}},
    }
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(client._apple, prompt, schema=schema, identifiers=())
                for prompt in ["first", "second"]
            ]
            assert [future.result(timeout=2) for future in futures] == [
                {"answer": "valid"},
                {"answer": "valid"},
            ]
        assert len(loaded) == 1
        assert loaded[0][2]["tokenizer_config"] == {
            "trust_remote_code": False,
            "local_files_only": True,
        }
        assert threads == [loaded[0][0], loaded[0][0]]
    finally:
        assert client._apple_batcher is not None
        client._apple_batcher.close()


@pytest.mark.parametrize(
    "failure", ["unknown_uid", "missing_finish", "duplicate_uid", "cancel"]
)
def test_batch_integrity_failures_close_generator(failure):
    cancelled = Event()
    state = {"closed": False, "called": False}

    class Generator:
        def __init__(self, *args, **kwargs):
            pass

        def insert(self, *args, **kwargs):
            return [7, 7] if failure == "duplicate_uid" else [7, 9]

        def next(self):
            if state["called"]:
                return []
            state["called"] = True
            if failure == "cancel":
                cancelled.set()
            return [
                SimpleNamespace(
                    uid=999 if failure == "unknown_uid" else 7,
                    token=65,
                    finish_reason=None,
                )
            ]

        def close(self):
            state["closed"] = True

    with pytest.raises((ValueError, CancelledError)):
        generate_batch(
            object(),
            Tokenizer(),
            ["a", "b"],
            [object(), object()],
            cancelled,
            generator_factory=Generator,
        )
    assert state["closed"]


def test_one_truncated_sequence_does_not_discard_completed_neighbour():
    class Generator:
        def __init__(self, *args, **kwargs):
            self.rows = iter(
                [
                    [
                        SimpleNamespace(uid=3, token=ord("B"), finish_reason=None),
                        SimpleNamespace(uid=1, token=ord("A"), finish_reason="length"),
                    ],
                    [SimpleNamespace(uid=3, token=0, finish_reason="stop")],
                    [],
                ]
            )

        def insert(self, *args, **kwargs):
            return [1, 3]

        def next(self):
            return next(self.rows)

        def close(self):
            pass

    responses = generate_batch(
        object(),
        Tokenizer(),
        ["a", "b"],
        [object(), object()],
        Event(),
        generator_factory=Generator,
    )
    assert isinstance(responses[0], ValueError)
    assert responses[1] == "B"


@pytest.mark.parametrize(
    "text",
    [
        '{"answer":"partial"',
        '{"answer":"first","answer":"second"}',
        'Text {"answer":"valid"}',
        '[{"answer":"valid"}]',
    ],
)
def test_parallel_mode_never_salvages_malformed_structured_output(monkeypatch, text):
    monkeypatch.setenv("KELDIN_PARALLEL_MLX_GENERATION", "1")
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    monkeypatch.setattr(
        client, "_run_apple_batch", lambda requests, _: [text] * len(requests)
    )
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string"}},
    }
    try:
        with pytest.raises(ValueError):
            client._apple("prompt", schema=schema, identifiers=())
    finally:
        assert client._apple_batcher is not None
        client._apple_batcher.close()


@pytest.mark.parametrize("budgets", [None, [6000, 1200]])
def test_batch_builds_a_fresh_decoder_for_each_original_schema(monkeypatch, budgets):
    from Backend.Core import providers

    schemas = [
        {"type": "object", "required": ["left"]},
        {"type": "object", "required": ["right"]},
    ]
    grammar_module = ModuleType("llguidance")
    grammar_module.grammar_from = lambda _, value: value
    grammar_module.LLMatcher = SimpleNamespace(validate_grammar=lambda _: "")
    monkeypatch.setitem(sys.modules, "llguidance", grammar_module)
    monkeypatch.setitem(sys.modules, "outlines", ModuleType("outlines"))
    backend_module = ModuleType("outlines.backends.llguidance")
    processors = []
    decoded_schemas = []

    class Backend:
        def __init__(self, model):
            pass

        def get_json_schema_logits_processor(self, schema):
            decoded_schemas.append(json.loads(schema))
            processor = object()
            processors.append(processor)
            return processor

    backend_module.LLGuidanceBackend = Backend
    monkeypatch.setitem(sys.modules, "outlines.backends.llguidance", backend_module)
    monkeypatch.setattr(providers, "_mlx_json_prompt", lambda tokenizer, prompt: prompt)
    captured = []
    options = []
    monkeypatch.setattr(
        providers,
        "generate_batch",
        lambda model, tokenizer, prompts, decoders, cancelled, **kwargs: (
            options.append(kwargs) or captured.append(decoders) or ["left", "right"]
        ),
    )
    client = HostedLLMClient(provider="apple", model="fixture", api_key="")
    client._apple_structured_model = object()
    requests = [("first", schemas[0]), ("second", schemas[1])]
    if budgets is not None:
        requests = [
            (*request, budget)
            for request, budget in zip(requests, budgets, strict=True)
        ]
    assert client._mlx_batch_structured_responses(requests, Event()) == [
        "left",
        "right",
    ]
    assert decoded_schemas == schemas
    assert processors[0] is not processors[1]
    assert captured == [processors]
    assert options == [{} if budgets is None else {"output_budgets": budgets}]
