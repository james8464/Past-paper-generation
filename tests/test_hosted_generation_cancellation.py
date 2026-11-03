"""Cancellation must not wait for a hosted provider's unfinished socket work."""

import os
import selectors
import signal
import subprocess
import sys
import time
from threading import Barrier, Event, Lock

import pytest

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
)
from Backend.Core.review_workers import map_hosted_jobs, map_reviews
from tests.test_assessment_checkpoints import identity


def _cancel_after_workers_are_ready(script, *arguments, cold_start_seconds=0):
    script = f"import time; time.sleep({cold_start_seconds!r})\n" + script
    process = subprocess.Popen(
        [sys.executable, "-c", script, *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = b""
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            startup_deadline = time.monotonic() + 20
            while b"WORKERS_READY\n" not in output:
                remaining = startup_deadline - time.monotonic()
                assert remaining > 0 and selector.select(remaining), (
                    "Provider workers did not become ready: "
                    + output.decode(errors="replace")
                )
                chunk = os.read(process.stdout.fileno(), 4096)
                assert chunk, "Child exited before worker readiness: " + output.decode(
                    errors="replace"
                )
                output += chunk
        # Import/build time is not cancellation time. Keep the original deadline.
        process.send_signal(signal.SIGTERM)
        tail, _ = process.communicate(timeout=3)
        assert process.returncode == 0, (output + tail).decode(errors="replace")
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=3)


def test_readiness_harness_still_rejects_post_signal_worker_join(monkeypatch):
    script = """
import os, signal, time
from threading import Barrier, Event, Thread
barrier = Barrier(2, action=lambda: os.write(1, b"WORKERS_READY\\n"))
def blocked():
    barrier.wait(timeout=20)
    time.sleep(30)
def cancelled(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
for _ in range(2): Thread(target=blocked, daemon=False).start()
try: Event().wait()
except KeyboardInterrupt: pass
"""
    children = []
    spawn = subprocess.Popen

    def track_child(*args, **kwargs):
        process = spawn(*args, **kwargs)
        children.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", track_child)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        _cancel_after_workers_are_ready(script)
    assert caught.value.timeout == 3
    assert len(children) == 1 and children[0].poll() is not None
    assert children[0].stdout.closed


@pytest.mark.parametrize("cold_start_seconds", [0, 3.2])
def test_shared_hosted_generation_cancellation_does_not_join_provider_workers(
    cold_start_seconds,
):
    script = """
import os, signal, time
from threading import Barrier
from types import SimpleNamespace
from Backend.Core import ai_assessment as subject
barrier = Barrier(2, action=lambda: os.write(1, b"WORKERS_READY\\n"))
def generate(*args, **kwargs):
    barrier.wait(timeout=20)
    time.sleep(30)
    return {}
subject._tasks = lambda *args: [SimpleNamespace(key=(0, 0, i), id=f'0/0/{i}') for i in range(2)]
subject._batches_for_client = lambda *args, **kwargs: [[1], [2]]
subject._generate_batch = generate
def cancelled(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
try:
    subject.generate_unique_paper(
        SimpleNamespace(seed=1), rule=None, syllabus_topics=[],
        syllabus_topic_ids=[], client=SimpleNamespace(
            provider='openai', supports_parallel_generation=True
        ), subject='Scheduling fixture'
    )
except KeyboardInterrupt:
    pass
"""
    _cancel_after_workers_are_ready(script, cold_start_seconds=cold_start_seconds)


@pytest.mark.parametrize("family", ["aqa_cs", "edexcel"])
@pytest.mark.parametrize("cold_start_seconds", [0, 3.2])
def test_specialist_hosted_cancellation_does_not_join_provider_workers(
    family, cold_start_seconds
):
    script = r"""
import os, signal, time, sys
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
family = sys.argv[1]
barrier = Barrier(2, action=lambda: os.write(1, b"WORKERS_READY\n"))
def blocked(*args, **kwargs):
    barrier.wait(timeout=20)
    time.sleep(30)
    return {}
client = SimpleNamespace(provider="openai", supports_parallel_generation=True, generate_json=blocked)
if family == "aqa_cs":
    sys.path.insert(0, str(Path.cwd() / "Resources/computer-science/aqa/generator"))
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.ollama_client import improve_questions_with_ollama as run
    from cspapergen.syllabus import load_syllabus
    syllabus = load_syllabus()
    paper = build_paper2_blueprint(syllabus, seed=7)
else:
    sys.path.insert(0, str(Path.cwd() / "Resources/economics/edexcel-a/generator"))
    from pastpapergen.generator import build_paper_blueprint
    from pastpapergen.ollama_client import generate_questions_with_ollama as run
    from pastpapergen.paper_configs import load_builtin_paper_config
    from pastpapergen.syllabus import load_syllabus
    syllabus = load_syllabus(Path("Resources/economics/edexcel-a/generator/data/syllabus_seed.json"))
    paper = build_paper_blueprint(load_builtin_paper_config("paper_1"), syllabus, seed=7)
import inspect
assert Path(inspect.getfile(run)).resolve().is_relative_to(Path.cwd().resolve())
def cancelled(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
try: run(client, paper, syllabus)
except KeyboardInterrupt: pass
"""
    _cancel_after_workers_are_ready(
        script, family, cold_start_seconds=cold_start_seconds
    )


def test_hosted_has_a_separate_four_worker_cap_and_preserves_result_order():
    barrier, lock = Barrier(4), Lock()
    active = maximum = 0

    def job(index):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        barrier.wait(timeout=2)
        with lock:
            active -= 1
        return index * 10

    assert map_hosted_jobs(list(range(12)), job, workers=4) == [
        index * 10 for index in range(12)
    ]
    assert maximum == 4
    with pytest.raises(ValueError):
        map_reviews([1], lambda value: value, workers=4)


@pytest.mark.parametrize("workers", [0, 5, True, "2"])
def test_invalid_hosted_worker_counts_refuse(workers):
    with pytest.raises(ValueError):
        map_hosted_jobs([1], lambda value: value, workers=workers)


def test_hosted_failure_never_commits_a_late_worker_checkpoint(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from Backend.Core import ai_assessment as subject

    store = AssessmentCheckpointStore(tmp_path / "accepted.json", identity())
    store.save_payload("old", {"approved": True})
    before = store.path.read_bytes()
    started, release, finished = Event(), Event(), Event()

    def generate(batch, *, checkpoint_store, **kwargs):
        assert isinstance(checkpoint_store, DeferredCheckpoints)
        if batch == [0]:
            assert started.wait(timeout=2)
            raise ValueError("rejected hosted batch")
        started.set()
        assert release.wait(timeout=2)
        checkpoint_store.save_payload("late", {"approved": True})
        finished.set()
        return {}

    monkeypatch.setattr(
        subject,
        "_tasks",
        lambda *args: [
            SimpleNamespace(key=(0, 0, index), id=f"0/0/{index}") for index in range(2)
        ],
    )
    monkeypatch.setattr(
        subject, "_batches_for_client", lambda *args, **kwargs: [[0], [1]]
    )
    monkeypatch.setattr(subject, "_generate_batch", generate)
    try:
        with pytest.raises(ValueError, match="rejected hosted batch"):
            subject.generate_unique_paper(
                SimpleNamespace(seed=1),
                rule=None,
                syllabus_topics=[],
                syllabus_topic_ids=[],
                client=SimpleNamespace(
                    provider="anthropic", supports_parallel_generation=True
                ),
                subject="Scheduling fixture",
                checkpoint_store=store,
            )
    finally:
        release.set()
    assert finished.wait(timeout=2)
    assert store.path.read_bytes() == before
