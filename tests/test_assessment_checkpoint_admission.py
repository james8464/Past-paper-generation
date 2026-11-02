"""Checkpoint durability follows cumulative caller-owned item admission."""

from __future__ import annotations

import hashlib
import threading

import pytest
from jsonschema import Draft202012Validator

from Backend.Core.ai_assessment import (
    ASSESSMENT_REVIEW_VERSION,
    GenerationPolicy,
    _generate_batch,
    _tasks,
    generate_unique_paper,
)
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
    identity_for_blueprint,
)
from Backend.Core.events import GenerationUpdate
from Backend.Core.exam_blueprints import GeneratedOption, GeneratedSection
from tests.test_assessment_checkpoints import paper_fixture

SHARED = "Explain why higher costs reduce profit."
ALTERNATIVE = "Explain how advertising improves consumer awareness of a product."


def fixture(count=2):
    paper, rule, topics = paper_fixture()
    original = paper.sections[0].options[0].questions[0]
    questions = [
        original.model_copy(
            update={
                "rule_id": f"q{index + 1}",
                "number": str(index + 1),
                "prompt": f"Explain a commercial decision concerning {'inventory' if index else 'costs'}.",
            }
        )
        for index in range(count)
    ]
    section = GeneratedSection(
        id="A",
        title="Section A",
        instructions="Answer all questions.",
        answer_options=1,
        candidate_marks=count,
        options=[GeneratedOption(id="option", title="Option", questions=questions)],
    )
    paper = paper.model_copy(update={"total_marks": count, "sections": [section]})
    section_rule = rule.sections[0].model_copy(
        update={
            "option_marks": count,
            "questions": [
                rule.sections[0].questions[0].model_copy(update={"id": f"q{index + 1}"})
                for index in range(count)
            ],
        }
    )
    return (
        paper,
        rule.model_copy(update={"total_marks": count, "sections": [section_rule]}),
        topics,
    )


class SchemaClient:
    model = "owned-schema-fixture"

    def __init__(
        self,
        mode,
        *,
        prompts=None,
        failure=None,
        admitted=None,
        failure_id="0/0/1",
        before_authoring=None,
    ):
        self.provider = "openai" if mode == "hosted" else "ollama"
        self.supports_parallel_generation = mode == "hosted"
        self.parallel_generation_workers = 2 if mode == "local" else 1
        self.calls = []
        self.prompts = prompts or {}
        self.failure = failure
        self.admitted = admitted
        self.failure_id = failure_id
        self.before_authoring = before_authoring
        self.lock = threading.Lock()

    def generate_request(self, request):
        identifier = request.expected_ids[0]
        with self.lock:
            self.calls.append((request.operation, identifier))
        if request.operation == "authoring":
            if self.before_authoring is not None:
                self.before_authoring(identifier)
            if self.failure is not None and identifier == self.failure_id:
                if self.admitted is not None:
                    assert self.admitted.wait(5), "first item was not admitted"
                raise self.failure
            prompt = self.prompts.get(identifier, SHARED)
            answer = (
                "Advertising improves awareness because more consumers encounter product information."
                if prompt == ALTERNATIVE
                else "Higher costs reduce profit because profit is total revenue minus total cost."
            )
            response = {
                "questions": [
                    {
                        "id": identifier,
                        "prompt": prompt,
                        "choices": [],
                        "correct_choice": None,
                        "mark_scheme": [
                            {
                                "text": answer,
                                "marks": 1,
                                "credit_type": "point",
                                "assessment_objective": "AO1",
                            }
                        ],
                    }
                ]
            }
        else:
            assert request.operation == "batch_review"
            response = {
                "reviews": [
                    {
                        "id": identifier,
                        "approved": True,
                        "factual_issues": [],
                        "marking_issues": [],
                        "source_issues": [],
                        "difficulty_issues": [],
                        "ambiguity_issues": [],
                    }
                ]
            }
        Draft202012Validator(request.schema).validate(response)
        return response


def store_for(path, paper, client):
    return AssessmentCheckpointStore(
        path,
        identity_for_blueprint(
            paper,
            provider=client.provider,
            model=client.model,
            prompt_version=ASSESSMENT_REVIEW_VERSION,
        ),
    )


def run(paper, rule, topics, client, store, *, progress=None, batch_size=1):
    return generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=client,
        subject="Economics",
        policy=GenerationPolicy(batch_size=batch_size, attempts=1),
        checkpoint_store=store,
        progress=progress,
    )


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_cross_batch_duplicates_never_both_become_durable(tmp_path, mode):
    paper, rule, topics = fixture()
    client = SchemaClient(mode)
    store = store_for(tmp_path / "job.json", paper, client)
    progress = []
    with pytest.raises(ValueError, match=r"duplicat|similar"):
        run(paper, rule, topics, client, store, progress=progress.append)
    assert len([key for key in ("0/0/0", "0/0/1") if store.load_item(key)]) == 1
    accepted = [
        event
        for event in progress
        if isinstance(event, GenerationUpdate) and event.stage == "checkpoint"
    ]
    assert accepted and max(event.completed_units for event in accepted) == 1


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_existing_poison_is_evicted_then_retry_reauthors_only_refused_batch(
    tmp_path, mode
):
    paper, rule, topics = fixture()
    seed_client = SchemaClient(mode)
    store = store_for(tmp_path / "job.json", paper, seed_client)
    for task in _tasks(paper, {topic.id: topic for topic in topics}):
        _generate_batch(
            [task],
            client=seed_client,
            subject="Economics",
            seed=paper.seed,
            policy=GenerationPolicy(attempts=1),
            progress=None,
            checkpoint_store=store,
        )
    retry = SchemaClient(mode)
    with pytest.raises(ValueError, match=r"duplicat|similar"):
        run(paper, rule, topics, retry, store)
    assert retry.calls == []
    survivors = {
        key: store.load_item(key) for key in ("0/0/0", "0/0/1") if store.load_item(key)
    }
    assert len(survivors) == 1
    missing = ({"0/0/0", "0/0/1"} - survivors.keys()).pop()
    repaired = SchemaClient(mode, prompts={missing: ALTERNATIVE})
    run(paper, rule, topics, repaired, store)
    assert repaired.calls == [("authoring", missing), ("batch_review", missing)]
    for key, previous in survivors.items():
        assert store.load_item(key) == previous


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_admitted_work_survives_later_failure_or_cancellation(
    tmp_path, mode, error_type
):
    paper, rule, topics = fixture()
    admitted = threading.Event()
    client = SchemaClient(
        mode, failure=error_type("controlled stop"), admitted=admitted
    )
    store = store_for(tmp_path / "job.json", paper, client)

    def progress(event):
        if isinstance(event, GenerationUpdate) and event.stage == "checkpoint":
            admitted.set()

    with pytest.raises(error_type, match="controlled stop"):
        run(paper, rule, topics, client, store, progress=progress)
    assert store.load_item("0/0/0") is not None
    assert store.load_item("0/0/1") is None


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_serial_batch_retains_valid_prefix_when_next_item_stops(tmp_path, error_type):
    paper, rule, topics = fixture(6)
    prompts = [
        SHARED,
        ALTERNATIVE,
        "Explain why a firm might hold a buffer stock of raw materials.",
        "Explain how staff training can reduce production mistakes.",
        "Explain why a patent may limit competition in a market.",
    ]
    client = SchemaClient(
        "serial",
        failure=error_type("controlled stop"),
        failure_id="0/0/5",
        prompts={f"0/0/{index}": prompt for index, prompt in enumerate(prompts)},
    )
    client.supports_parallel_generation = True
    store = store_for(tmp_path / "job.json", paper, client)
    with pytest.raises(error_type, match="controlled stop"):
        run(paper, rule, topics, client, store, batch_size=6)
    for index in range(5):
        assert store.load_item(f"0/0/{index}") is not None
    assert store.load_item("0/0/5") is None


def test_single_deferred_commit_failure_retains_only_its_retryable_entry(
    tmp_path, monkeypatch
):
    paper, _, _ = fixture()
    client = SchemaClient("serial")
    store = store_for(tmp_path / "job.json", paper, client)
    deferred = DeferredCheckpoints(store)
    deferred.save_item("first", paper.sections[0].options[0].questions[0])
    deferred.save_item("second", paper.sections[0].options[0].questions[1])
    original = store.save_payload

    def fail_once(*_args):
        raise OSError("controlled write failure")

    monkeypatch.setattr(store, "save_payload", fail_once)
    with pytest.raises(OSError, match="controlled write failure"):
        deferred.commit_item("first")
    assert set(deferred.changes) == {"first", "second"}
    monkeypatch.setattr(store, "save_payload", original)
    deferred.commit_item("first")
    assert set(deferred.changes) == {"second"}
    assert store.load_item("first") is not None
    assert store.load_item("second") is None
    deferred.discard_item("first")
    original_discard = store.discard_item
    monkeypatch.setattr(store, "discard_item", fail_once)
    with pytest.raises(OSError, match="controlled write failure"):
        deferred.commit_item("first")
    assert deferred.changes["first"] is None
    assert store.load_item("first") is not None
    monkeypatch.setattr(store, "discard_item", original_discard)
    deferred.commit_item("first")
    assert store.load_item("first") is None
    assert set(deferred.changes) == {"second"}


def test_late_hosted_worker_cannot_commit_after_another_batch_refuses(
    tmp_path, monkeypatch
):
    from Backend.Core import ai_assessment

    paper, rule, topics = fixture(3)
    late_started = threading.Event()
    release_late = threading.Event()
    late_finished = threading.Event()
    admitted = threading.Event()
    caller = threading.get_ident()
    writes = []

    def before_authoring(identifier):
        if identifier == "0/0/2":
            late_started.set()
            assert release_late.wait(5)
        elif identifier == "0/0/0":
            assert late_started.wait(5)

    client = SchemaClient(
        "hosted",
        failure=RuntimeError("controlled stop"),
        admitted=admitted,
        before_authoring=before_authoring,
    )
    store = store_for(tmp_path / "job.json", paper, client)
    original_write = store.save_payload

    def record_write(key, payload):
        writes.append(threading.get_ident())
        original_write(key, payload)

    monkeypatch.setattr(store, "save_payload", record_write)
    generate_batch = ai_assessment._generate_batch

    def observe_finish(tasks, **kwargs):
        try:
            return generate_batch(tasks, **kwargs)
        finally:
            if tasks[0].id == "0/0/2":
                late_finished.set()

    monkeypatch.setattr(ai_assessment, "_generate_batch", observe_finish)

    def progress(event):
        if isinstance(event, GenerationUpdate) and event.stage == "checkpoint":
            admitted.set()

    try:
        with pytest.raises(RuntimeError, match="controlled stop"):
            run(paper, rule, topics, client, store, progress=progress)
        before = hashlib.sha256(store.path.read_bytes()).hexdigest()
    finally:
        release_late.set()
        assert late_finished.wait(5)
    assert hashlib.sha256(store.path.read_bytes()).hexdigest() == before
    assert store.load_item("0/0/0") is not None
    assert store.load_item("0/0/1") is None
    assert store.load_item("0/0/2") is None
    assert writes == [caller]


@pytest.mark.parametrize("stale_cache", [False, True])
def test_trusted_original_never_uses_a_stale_cached_payload_for_admission(
    tmp_path, stale_cache
):
    from Backend.Core.exam_blueprints import MarkSchemePoint

    paper, rule, topics = fixture()
    option = paper.sections[0].options[0]
    first = option.questions[0].model_copy(
        update={
            "prompt": SHARED,
            "mark_scheme": [
                "Higher costs reduce profit because profit is revenue minus costs."
            ],
            "structured_mark_scheme": [
                MarkSchemePoint(
                    text="Higher costs reduce profit because profit is revenue minus costs.",
                    marks=1,
                    assessment_objective="AO1",
                )
            ],
            "authoring_context": {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            },
        }
    )
    second = first.model_copy(
        update={"rule_id": "q2", "number": "2", "prompt": ALTERNATIVE}
    )
    paper = paper.model_copy(
        update={
            "sections": [
                paper.sections[0].model_copy(
                    update={
                        "options": [
                            option.model_copy(update={"questions": [first, second]})
                        ]
                    }
                )
            ]
        }
    )
    client = SchemaClient("serial")
    store = store_for(tmp_path / "job.json", paper, client)
    if stale_cache:
        store.save_item("0/0/1", second.model_copy(update={"prompt": SHARED}))
    result = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=client,
        subject="Economics",
        policy=GenerationPolicy(batch_size=1, require_model_review=False),
        checkpoint_store=store,
    )
    assert [q.prompt for q in result.sections[0].options[0].questions] == [
        SHARED,
        ALTERNATIVE,
    ]
    assert client.calls == []


def test_resumed_metadata_is_admitted_without_duplicate_counting(tmp_path):
    paper, rule, topics = fixture()
    option = paper.sections[0].options[0]
    current = [
        q.model_copy(update={"authoring_context": {"max_prompt_words": 80}})
        for q in option.questions
    ]
    paper = paper.model_copy(
        update={
            "sections": [
                paper.sections[0].model_copy(
                    update={
                        "options": [option.model_copy(update={"questions": current})]
                    }
                )
            ]
        }
    )
    client = SchemaClient("serial", prompts={"0/0/1": ALTERNATIVE})
    store = store_for(tmp_path / "job.json", paper, client)
    for task in _tasks(paper, {topic.id: topic for topic in topics}):
        previous = task.question.model_copy(update={"authoring_context": {}})
        old_task = type(task)(
            key=task.key, question=previous, option=task.option, topic=task.topic
        )
        _generate_batch(
            [old_task],
            client=client,
            subject="Economics",
            seed=paper.seed,
            policy=GenerationPolicy(attempts=1),
            progress=None,
            checkpoint_store=store,
        )
    client.calls.clear()
    progress = []
    run(paper, rule, topics, client, store, progress=progress.append, batch_size=6)
    assert client.calls == []
    for task in _tasks(paper, {topic.id: topic for topic in topics}):
        assert store.load_item(task.id).authoring_context["max_prompt_words"] == 80
    assert [
        event.completed_units
        for event in progress
        if isinstance(event, GenerationUpdate) and event.stage == "checkpoint"
    ] == [1, 2]


def test_serial_admission_follows_solver_review_and_difficulty_gates(
    tmp_path, monkeypatch
):
    from Backend.Core import ai_assessment
    from Backend.Core.exam_blueprints import MarkSchemePoint
    from Backend.Core.independent_solver import CanonicalSolution
    from Backend.Core.model_review import DifficultyReviewResult
    from tests.test_ai_assessment import _demand_profile

    paper, rule, topics = fixture(1)
    option = paper.sections[0].options[0]
    point = MarkSchemePoint(
        text="Higher costs reduce profit because profit is revenue minus costs.",
        marks=1,
        assessment_objective="AO1",
    )
    question = option.questions[0].model_copy(
        update={
            "prompt": SHARED,
            "mark_scheme": [point.text],
            "structured_mark_scheme": [point],
            "authoring_context": {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            },
        }
    )
    paper = paper.model_copy(
        update={
            "sections": [
                paper.sections[0].model_copy(
                    update={
                        "options": [option.model_copy(update={"questions": [question]})]
                    }
                )
            ]
        }
    )
    client = SchemaClient("serial")
    store = store_for(tmp_path / "job.json", paper, client)
    gates = []

    def solve(*_args, **_kwargs):
        gates.append("solve")
        assert store.load_item("0/0/0") is None
        return CanonicalSolution(
            item_id="0/0/0",
            answer=point.text,
            steps=["Subtract costs from revenue"],
            mark_points=[point.text],
            assessment_objectives={"AO1": 1},
        )

    def difficulty(*_args, **_kwargs):
        gates.append("difficulty")
        assert client.calls == [("batch_review", "0/0/0")]
        assert store.load_item("0/0/0") is None
        return DifficultyReviewResult(
            approved=True,
            estimated_demand="standard",
            reasoning_steps=2,
            tariff_fit=True,
            command_word_fit=True,
            context_fit=True,
            profile_fit=True,
            observed_cognitive_operations=["explain", "analyse"],
        )

    monkeypatch.setattr(ai_assessment, "_independently_validate_candidate", solve)
    monkeypatch.setattr(ai_assessment, "require_difficulty_review", difficulty)
    generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=client,
        subject="Economics",
        checkpoint_store=store,
        demand_profile=_demand_profile(),
        policy=GenerationPolicy(
            require_independent_solution=True, require_difficulty_review=True
        ),
    )
    assert gates == ["solve", "difficulty"]
    assert (
        store.load_item("0/0/0").authoring_context["difficulty_evidence"]["approved"]
        is True
    )
