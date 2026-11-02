"""Duration admission must precede benchmark side effects; no real probes run."""

import json
from types import SimpleNamespace

import pytest

from Backend.Core import benchmark
from Backend.Core.cli import build_parser


@pytest.mark.parametrize("duration", ["nan", "inf", "-inf", "1e309"])
def test_nonfinite_duration_refuses_before_output_or_probe_work(
    monkeypatch, tmp_path, capsys, duration
):
    output = tmp_path / "must-not-exist"
    args = build_parser().parse_args(
        ["benchmark", f"--duration={duration}", "--output", str(output)]
    )

    def unexpected(*_args, **_kwargs):
        pytest.fail("Invalid duration reached output resolution or benchmark work")

    # The old implementation safely fails here, never entering its infinite
    # loop or touching hardware, the filesystem, network or model services.
    monkeypatch.setattr(benchmark, "absolute_user_path", unexpected)
    monkeypatch.setattr(benchmark, "emit_static_metrics", unexpected)
    monkeypatch.setattr(benchmark.os, "urandom", unexpected)
    for name in ("cpu_probe", "disk_probe", "network_probe", "pdf_probe"):
        monkeypatch.setattr(benchmark, name, unexpected)

    assert args.handler(args) == 1
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "invalid_benchmark_duration"
    assert events[0]["message"] == "Benchmark duration must be finite."
    assert not output.exists()


@pytest.mark.parametrize(
    "duration,expected",
    [(None, 30.0), ("-2", 1.0), ("0", 1.0), ("0.25", 1.0), ("1.5", 1.5)],
)
def test_finite_duration_preserves_default_minimum_and_fractional_timing(
    monkeypatch, tmp_path, capsys, duration, expected
):
    values = ["benchmark", "--output", str(tmp_path / "owned-output")]
    if duration is not None:
        values.append(f"--duration={duration}")
    args = build_parser().parse_args(values)
    clock = SimpleNamespace(now=0.0, sleeps=[], probes=0)

    def sleep(seconds):
        assert 0 <= seconds <= 1
        clock.sleeps.append(seconds)
        clock.now += seconds

    def cpu_probe(payload):
        assert payload == b"owned-fixture"
        clock.probes += 1
        assert clock.probes <= 31, "Fake benchmark must remain bounded"
        clock.now += 0.25
        return 650.0

    monkeypatch.setattr(
        benchmark, "time", SimpleNamespace(perf_counter=lambda: clock.now, sleep=sleep)
    )
    monkeypatch.setattr(benchmark, "emit_static_metrics", lambda: None)
    monkeypatch.setattr(benchmark.os, "urandom", lambda _size: b"owned-fixture")
    monkeypatch.setattr(benchmark, "cpu_probe", cpu_probe)
    monkeypatch.setattr(benchmark, "disk_probe", lambda *_: (400, 700, 20, 0))
    monkeypatch.setattr(benchmark, "memory_snapshot", lambda: (8, 0, 0))
    monkeypatch.setattr(benchmark, "cpu_load_percent", lambda: 0)
    monkeypatch.setattr(benchmark, "network_probe", lambda: (0, 12))
    monkeypatch.setattr(benchmark, "ollama_latency_ms", lambda: None)
    monkeypatch.setattr(benchmark, "thermal_speed_limit_percent", lambda: 100)
    monkeypatch.setattr(benchmark, "pdf_probe", lambda _output: 18)
    monkeypatch.setattr(benchmark, "power_status", lambda: ("AC Power", None, 1))

    assert args.handler(args) == 0
    assert clock.now == expected
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    samples = [event for event in events if event["type"] == "benchmark_sample"]
    assert len(samples) == clock.probes
    assert all(0 < sample["elapsed"] <= expected for sample in samples)
    assert events[-1]["type"] == "benchmark_done"
    assert events[-1]["score"] == 1.0
    assert (tmp_path / "owned-output").is_dir()
