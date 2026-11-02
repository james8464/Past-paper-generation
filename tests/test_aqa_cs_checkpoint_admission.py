"""AQA admission follows its existing exact part-prompt duplicate rule."""

from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path

import pytest
from cspapergen import ollama_client as subject
from cspapergen.generator import build_paper2_blueprint
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint
from jsonschema import Draft202012Validator

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
    identity_for_blueprint,
)
from Backend.Core.computer_science_authoring import reviewed_question_metadata
from Backend.Core.events import GenerationUpdate
from Backend.Core.model_review import ReviewResult

COMMON = "Explain the technical and legal considerations relevant to the organisation."
STEM = "An organisation is planning changes to its services."


def fixture(numbers=(4, 5)):
    assert (
        Path(subject.__file__)
        .resolve()
        .is_relative_to(Path(__file__).resolve().parents[1])
    )
    syllabus = load_syllabus()
    full = build_paper2_blueprint(syllabus, seed=270100)
    selected = [q for q in full.questions if q.number in numbers]
    assert len(selected) == len(numbers)
    assert all(not subject._uses_review_only_generation(q) for q in selected)
    return full, full.model_copy(update={"questions": selected}), syllabus


class Client:
    model = "owned-aqa-admission-fixture"

    def __init__(self, mode, *, prompts=None, failure=None, admitted=None, before=None):
        self.provider = "openai" if mode == "hosted" else "ollama"
        self.supports_parallel_generation = mode == "hosted"
        self.parallel_generation_workers = 2 if mode == "local" else 1
        self.calls = []
        self.lock = threading.Lock()
        self.prompts = prompts or {}
        self.failure = failure
        self.admitted = admitted
        self.before = before

    def generate_request(self, request):
        match = re.search(r"question-(\d+)", request.prompt)
        number = (
            int(match.group(1))
            if match
            else next(
                number
                for style, number in {
                    "legal_issues_short": 4,
                    "client_server_short": 5,
                    "ipv4_extended": 8,
                }.items()
                if f"({style})" in request.prompt
            )
        )
        with self.lock:
            self.calls.append((request.operation, number))
        if request.operation == "aqa_cs":
            if self.before is not None:
                self.before(number)
            if self.failure is not None and number == 5:
                if self.admitted is not None:
                    assert self.admitted.wait(5)
                raise self.failure
            response = {
                "stem": STEM,
                "parts": [{"label": "1", "prompt": self.prompts.get(number, COMMON)}],
            }
        else:
            assert request.operation == "review"
            response = {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        Draft202012Validator(request.schema).validate(response)
        return response


def store_for(path, paper, client):
    return AssessmentCheckpointStore(
        path,
        identity_for_blueprint(
            {
                "paper_id": "aqa-pattern",
                "seed": paper.seed,
                "blueprint": paper.model_dump(mode="json"),
            },
            provider=client.provider,
            model=client.model,
            prompt_version="owned-unchanged-admission",
        ),
    )


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
@pytest.mark.parametrize("variant", [COMMON, "  " + COMMON.upper() + "  "])
def test_colliding_questions_are_not_both_durable_or_reported_accepted(
    tmp_path, mode, variant
):
    _, paper, syllabus = fixture()
    client = Client(mode, prompts={5: variant})
    store = store_for(tmp_path / "job.json", paper, client)
    store.save_payload("unrelated", {"retained": True})
    events = []
    with pytest.raises(ValueError, match="duplicates another prompt"):
        subject.improve_questions_with_ollama(
            client, paper, syllabus, checkpoint_store=store, progress=events.append
        )
    assert (
        sum(
            store.load_payload(f"question-{q.number}") is not None
            for q in paper.questions
        )
        == 1
    )
    assert store.load_payload("unrelated") == {"retained": True}
    assert (
        len(
            [
                e
                for e in events
                if isinstance(e, str) and e.startswith("Generated and reviewed")
            ]
        )
        <= 1
    )
    accepted = [
        e.completed_units
        for e in events
        if isinstance(e, GenerationUpdate) and e.stage == "checkpoint"
    ]
    assert not accepted or max(accepted) == 1


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_legacy_conflict_is_evicted_and_only_refused_question_is_reauthored(
    tmp_path, mode
):
    _, paper, syllabus = fixture()
    client = Client(mode)
    store = store_for(tmp_path / "job.json", paper, client)
    for question in paper.questions:
        candidate = subject._merge_question(
            question, {"stem": STEM, "parts": [{"label": "1", "prompt": COMMON}]}
        )
        subject._validate_ai_question(question, candidate)
        candidate = candidate.model_copy(
            update=reviewed_question_metadata(
                question.model_dump(mode="json"),
                candidate.model_dump(mode="json"),
                ReviewResult(approved=True),
            )
        )
        store.save_payload(
            f"question-{question.number}", candidate.model_dump(mode="json")
        )
    with pytest.raises(ValueError, match="duplicates another prompt"):
        subject.improve_questions_with_ollama(
            client, paper, syllabus, checkpoint_store=store
        )
    assert client.calls == []
    survivors = {
        q.number: store.load_payload(f"question-{q.number}")
        for q in paper.questions
        if store.load_payload(f"question-{q.number}") is not None
    }
    assert len(survivors) == 1
    missing = ({4, 5} - survivors.keys()).pop()
    prompt = (
        "Explain why uncertain legal definitions complicate regulation of automated decisions."
        if missing == 4
        else "Explain how centralised authentication and shared storage benefit a growing business network."
    )
    repaired = Client(mode, prompts={missing: prompt})
    result = subject.improve_questions_with_ollama(
        repaired, paper, syllabus, checkpoint_store=store
    )
    assert repaired.calls == [("aqa_cs", missing), ("review", missing)]
    assert len(result.questions) == 2
    for number, payload in survivors.items():
        assert store.load_payload(f"question-{number}") == payload


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
@pytest.mark.parametrize("error", [RuntimeError, KeyboardInterrupt])
def test_earlier_question_survives_later_failure_or_cancellation(tmp_path, mode, error):
    _, paper, syllabus = fixture()
    admitted = threading.Event()
    client = Client(mode, failure=error("controlled stop"), admitted=admitted)
    store = store_for(tmp_path / "job.json", paper, client)

    def progress(event):
        if (isinstance(event, GenerationUpdate) and event.stage == "checkpoint") or (
            isinstance(event, str)
            and event.startswith("Generated and reviewed question")
        ):
            admitted.set()

    with pytest.raises(error, match="controlled stop"):
        subject.improve_questions_with_ollama(
            client, paper, syllabus, checkpoint_store=store, progress=progress
        )
    assert store.load_payload("question-4") is not None
    assert store.load_payload("question-5") is None


def test_nearby_but_unequal_part_prompts_keep_existing_exact_predicate(tmp_path):
    _, paper, syllabus = fixture()
    client = Client("serial", prompts={5: COMMON.removesuffix(".") + " clearly."})
    store = store_for(tmp_path / "job.json", paper, client)
    result = subject.improve_questions_with_ollama(
        client, paper, syllabus, checkpoint_store=store
    )
    assert len(result.questions) == 2


def test_actual_complete_blueprint_rejects_case_and_space_only_duplicates():
    full, paper, syllabus = fixture()
    replacements = {
        q.number: q.model_copy(
            update={
                "parts": [
                    q.parts[0].model_copy(
                        update={
                            "prompt": COMMON
                            if q.number == 4
                            else "  " + COMMON.upper() + "  "
                        }
                    )
                ]
            }
        )
        for q in paper.questions
    }
    candidate = full.model_copy(
        update={"questions": [replacements.get(q.number, q) for q in full.questions]}
    )
    with pytest.raises(ValueError, match="duplicates another prompt"):
        validate_blueprint(candidate, syllabus)


def test_late_hosted_question_stays_deferred_after_another_question_fails(
    tmp_path, monkeypatch
):
    _, paper, syllabus = fixture((4, 5, 8))
    late_started, release_late, late_staged = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )
    admitted = threading.Event()
    caller = threading.get_ident()

    def before(number):
        if number == 8:
            late_started.set()
            assert release_late.wait(5)
        elif number == 4:
            assert late_started.wait(5)

    client = Client(
        "hosted",
        failure=RuntimeError("controlled stop"),
        admitted=admitted,
        before=before,
    )
    store = store_for(tmp_path / "job.json", paper, client)
    original_write = store.save_payload
    original_stage = DeferredCheckpoints.save_payload
    writes = []

    def record_write(key, payload):
        writes.append(threading.get_ident())
        original_write(key, payload)

    def observe_stage(deferred, key, payload):
        original_stage(deferred, key, payload)
        if key == "question-8":
            late_staged.set()

    monkeypatch.setattr(store, "save_payload", record_write)
    monkeypatch.setattr(DeferredCheckpoints, "save_payload", observe_stage)

    def progress(event):
        if isinstance(event, str) and event.startswith(
            "Generated and reviewed question"
        ):
            admitted.set()

    try:
        with pytest.raises(RuntimeError, match="controlled stop"):
            subject.improve_questions_with_ollama(
                client, paper, syllabus, checkpoint_store=store, progress=progress
            )
        before_release = hashlib.sha256(store.path.read_bytes()).hexdigest()
    finally:
        release_late.set()
        assert late_staged.wait(5)
    assert hashlib.sha256(store.path.read_bytes()).hexdigest() == before_release
    assert store.load_payload("question-4") is not None
    assert store.load_payload("question-5") is None
    assert store.load_payload("question-8") is None
    assert writes == [caller]
