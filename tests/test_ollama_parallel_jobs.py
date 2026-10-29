from __future__ import annotations

import time
from importlib import import_module
from pathlib import Path
from threading import Barrier, Event, Lock, get_ident

import pytest

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
)
from Backend.Core.providers import HostedLLMClient
from Backend.Core.review_workers import local_generation_workers, map_reviews
from tests.test_assessment_checkpoints import identity


@pytest.mark.parametrize("provider", ["ollama", "apple", "openai", "anthropic"])
@pytest.mark.parametrize("enabled", ["0", "1"])
def test_only_enabled_ollama_gets_two_generation_workers(
    monkeypatch, provider, enabled
):
    monkeypatch.setenv("KELDIN_PARALLEL_LOCAL_REVIEWS", enabled)
    client = HostedLLMClient(provider=provider, model="fixture", api_key="")
    assert local_generation_workers(client) == (
        2 if provider == "ollama" and enabled == "1" else 1
    )
    # Hosted batching and local fallback contracts are separate from scheduling.
    assert client.supports_parallel_generation == (provider in {"openai", "anthropic"})


def test_checkpoint_writes_wait_for_main_thread_acceptance(tmp_path):
    store = AssessmentCheckpointStore(tmp_path / "accepted.json", identity())
    store.save_payload("old", {"value": "retained"})
    barrier = Barrier(2)
    caller = get_ident()
    accepted = []

    def job(index):
        deferred = DeferredCheckpoints(store)
        deferred.save_payload(str(index), {"value": index})
        deferred.discard_item("old")
        assert store.load_payload(str(index)) is None
        barrier.wait(timeout=2)
        return deferred

    def accept(index, deferred):
        assert get_ident() == caller
        deferred.commit()
        accepted.append(index)

    map_reviews([0, 1], job, workers=2, on_result=accept)
    assert sorted(accepted) == [0, 1]
    assert store.load_payload("old") is None
    assert store.load_payload("0") == {"value": 0}
    assert store.load_payload("1") == {"value": 1}


def test_unaccepted_checkpoint_changes_are_not_published(tmp_path):
    store = AssessmentCheckpointStore(tmp_path / "accepted.json", identity())
    store.save_payload("old", {"value": "retained"})
    before = store.path.read_bytes()
    deferred = DeferredCheckpoints(store)
    deferred.discard_item("old")
    deferred.save_payload("failed", {"approved": False})
    assert deferred.load_payload("old") is None
    assert deferred.load_payload("failed") == {"approved": False}
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "module",
    [
        "aqaaccountgen.cli",
        "aqabizgen.cli",
        "aqaecongen.cli",
        "ocregen.cli",
        "ocrcsgen.cli",
    ],
)
def test_shared_subjects_use_the_parallel_capable_pipeline(module):
    assert import_module(module).ADAPTER.improve is None


@pytest.mark.parametrize(
    "module",
    [
        "aqaaccountgen.cli",
        "aqabizgen.cli",
        "aqaecongen.cli",
        "ocregen.cli",
        "ocrcsgen.cli",
    ],
)
def test_shared_pipeline_overlaps_two_jobs_preserving_order_and_checkpoints(
    module, monkeypatch, tmp_path
):
    from Backend.Core import ai_assessment as subject
    from Backend.Core.assessment_checkpoints import identity_for_blueprint
    from Backend.Core.events import GenerationUpdate

    cli = import_module(module)
    adapter = cli.ADAPTER
    syllabus = adapter.load_syllabus(
        Path(cli.__file__).parents[1] / "data" / "syllabus.json"
    )
    rule = adapter.load_rule("1")
    paper = adapter.build(rule, syllabus, 123)
    barrier, lock = Barrier(2), Lock()
    active = maximum = calls = 0
    caller = get_ident()
    store = AssessmentCheckpointStore(
        tmp_path / "accepted.json",
        identity_for_blueprint(
            paper, provider="ollama", model="fixture", prompt_version="test"
        ),
    )

    def generate(batch, *, checkpoint_store, **kwargs):
        nonlocal active, maximum, calls
        assert get_ident() != caller
        with lock:
            active += 1
            maximum = max(maximum, active)
            calls += 1
            first_pair = calls <= 2
        if first_pair:
            barrier.wait(timeout=3)
        time.sleep(0.005)
        for task in batch:
            checkpoint_store.save_item(task.id, task.question)
            assert store.load_item(task.id) is None
        with lock:
            active -= 1
        return {task.key: task.question for task in batch}

    # Scheduling probe uses unchanged blueprint items, not AI-quality evidence.
    monkeypatch.setattr(subject, "_generate_batch", generate)
    monkeypatch.setattr(subject, "assert_distinct_items", lambda *args, **kwargs: None)
    monkeypatch.setenv("KELDIN_PARALLEL_LOCAL_REVIEWS", "1")
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    events = []
    result = subject.generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=syllabus.topics,
        syllabus_topic_ids=syllabus.topic_ids,
        client=client,
        subject=adapter.subject_label,
        checkpoint_store=store,
        progress=events.append,
    )
    assert result == paper
    assert maximum == 2
    completed = [
        event.completed_units for event in events if isinstance(event, GenerationUpdate)
    ]
    assert completed == sorted(set(completed))
    tasks = subject._tasks(paper, {str(topic.id): topic for topic in syllabus.topics})
    assert completed[-1] == len(tasks)
    assert all(store.load_item(task.id) == task.question for task in tasks)


@pytest.mark.parametrize("family", ["edexcel", "aqa_cs"])
def test_specialist_pipelines_overlap_exactly_two_ollama_calls(family):
    active = maximum = 0
    lock = Lock()

    class Client:
        provider = "ollama"
        supports_parallel_generation = False
        parallel_review_workers = 2

        def generate_json(self, _prompt):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return {}  # Deliberately rejected; parallelism must not bypass gates.

    if family == "edexcel":
        from pastpapergen.generator import build_paper_blueprint
        from pastpapergen.ollama_client import generate_questions_with_ollama
        from pastpapergen.paper_configs import load_builtin_paper_config
        from pastpapergen.syllabus import load_syllabus

        path = (
            Path(__file__).parents[1]
            / "Resources/economics/edexcel-a/generator/data/syllabus_seed.json"
        )
        syllabus = load_syllabus(path)
        paper = build_paper_blueprint(
            load_builtin_paper_config("paper_1"), syllabus, seed=7
        )
        run = generate_questions_with_ollama
    else:
        from cspapergen.generator import build_paper2_blueprint
        from cspapergen.ollama_client import improve_questions_with_ollama
        from cspapergen.syllabus import load_syllabus

        syllabus = load_syllabus()
        paper = build_paper2_blueprint(syllabus, seed=7)
        run = improve_questions_with_ollama
    with pytest.raises(ValueError):
        run(Client(), paper, syllabus)
    assert maximum == 2


def test_late_worker_cannot_commit_after_failure(tmp_path):
    store = AssessmentCheckpointStore(tmp_path / "accepted.json", identity())
    store.save_payload("old", {"approved": True})
    before = store.path.read_bytes()
    started, release, finished = Event(), Event(), Event()

    def job(index):
        if index == 0:
            assert started.wait(timeout=2)
            raise ValueError("rejected")
        deferred = DeferredCheckpoints(store)
        started.set()
        assert release.wait(timeout=2)
        deferred.save_payload("late", {"approved": True})
        finished.set()
        return deferred

    with pytest.raises(ValueError, match="rejected"):
        map_reviews(
            [0, 1], job, workers=2, on_result=lambda _, deferred: deferred.commit()
        )
    release.set()
    assert finished.wait(timeout=2)
    assert store.path.read_bytes() == before


def test_specialist_cs_acceptance_and_resume_preserve_fixed_questions(tmp_path):
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.ollama_client import (
        _uses_review_only_generation,
        improve_questions_with_ollama,
    )
    from cspapergen.syllabus import load_syllabus

    from Backend.Core.assessment_checkpoints import identity_for_blueprint

    syllabus = load_syllabus()
    full = build_paper2_blueprint(syllabus, seed=7)
    questions = [
        question
        for question in full.questions
        if _uses_review_only_generation(question)
    ][:2]
    assert len(questions) == 2
    paper = full.model_copy(update={"questions": questions})
    store = AssessmentCheckpointStore(
        tmp_path / "accepted.json",
        identity_for_blueprint(
            {"paper_id": "cs", "seed": 7, "paper": paper.model_dump(mode="json")},
            provider="ollama",
            model="fixture",
            prompt_version="test",
        ),
    )

    class Client:
        provider = "ollama"
        supports_parallel_generation = False
        parallel_review_workers = 2

        def generate_json(self, _prompt):
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }

    generated = improve_questions_with_ollama(
        Client(), paper, syllabus, checkpoint_store=store
    )
    assert [question.parts for question in generated.questions] == [
        question.parts for question in paper.questions
    ]
    assert [question.number for question in generated.questions] == [
        question.number for question in paper.questions
    ]

    class NoCalls(Client):
        def generate_json(self, _prompt):
            raise AssertionError("accepted questions must resume")

    assert (
        improve_questions_with_ollama(
            NoCalls(), paper, syllabus, checkpoint_store=store
        )
        == generated
    )
