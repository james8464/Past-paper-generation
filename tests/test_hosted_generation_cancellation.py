"""Cancellation must not wait for a hosted provider's unfinished socket work."""

import subprocess
import sys
from threading import Barrier, Event, Lock

import pytest

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
)
from Backend.Core.review_workers import map_hosted_jobs, map_reviews
from tests.test_assessment_checkpoints import identity


def test_shared_hosted_generation_cancellation_does_not_join_provider_workers():
    script = """
import os, signal, time
from threading import Barrier, Timer
from types import SimpleNamespace
from Backend.Core import ai_assessment as subject
barrier = Barrier(2)
def generate(*args, **kwargs):
    barrier.wait(timeout=2)
    time.sleep(30)
    return {}
subject._tasks = lambda *args: [1, 2]
subject._batches_for_client = lambda *args, **kwargs: [[1], [2]]
subject._generate_batch = generate
def cancelled(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
timer = Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM))
timer.daemon = True
timer.start()
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
    subprocess.run([sys.executable, "-c", script], check=True, timeout=3)


@pytest.mark.parametrize("family", ["aqa_cs", "edexcel"])
def test_specialist_hosted_cancellation_does_not_join_provider_workers(family):
    script = r"""
import os, signal, time, sys
from pathlib import Path
from threading import Barrier, Timer
from types import SimpleNamespace
family = sys.argv[1]
barrier = Barrier(2)
def blocked(*args, **kwargs):
    barrier.wait(timeout=2)
    time.sleep(30)
    return {}
client = SimpleNamespace(provider="openai", supports_parallel_generation=True, generate_json=blocked)
if family == "aqa_cs":
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.ollama_client import improve_questions_with_ollama as run
    from cspapergen.syllabus import load_syllabus
    syllabus = load_syllabus()
    paper = build_paper2_blueprint(syllabus, seed=7)
else:
    from pastpapergen.generator import build_paper_blueprint
    from pastpapergen.ollama_client import generate_questions_with_ollama as run
    from pastpapergen.paper_configs import load_builtin_paper_config
    from pastpapergen.syllabus import load_syllabus
    syllabus = load_syllabus(Path("Resources/economics/edexcel-a/generator/data/syllabus_seed.json"))
    paper = build_paper_blueprint(load_builtin_paper_config("paper_1"), syllabus, seed=7)
def cancelled(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancelled)
timer = Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM))
timer.daemon = True
timer.start()
try: run(client, paper, syllabus)
except KeyboardInterrupt: pass
"""
    subprocess.run([sys.executable, "-c", script, family], check=True, timeout=3)


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

    monkeypatch.setattr(subject, "_tasks", lambda *args: [0, 1])
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
