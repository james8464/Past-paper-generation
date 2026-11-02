"""Real specialist contracts and owned caches; schema-valid fake calls only."""

import hashlib
import json
import re
import threading
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pastpapergen import ollama_client
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus
from pastpapergen.validation import validate_blueprint

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    DeferredCheckpoints,
    identity_for_blueprint,
)
from Backend.Core.events import GenerationUpdate

ROOT = Path(__file__).resolve().parents[1]
SHARED = "Evaluate solutions to economic problems with reference to Extract C."
ALTERNATIVE = (
    "Evaluate alternative approaches to economic policy with reference to Extract C."
)


def fixture():
    assert Path(ollama_client.__file__).resolve().is_relative_to(ROOT)
    syllabus = load_syllabus(
        ROOT / "Resources/economics/edexcel-a/generator/data/syllabus_seed.json"
    )
    config = load_builtin_paper_config("paper_3")
    full = build_paper_blueprint(config, syllabus, seed=270100)
    selected = [q for q in full.questions if q.number in {"1(d)", "1(e)"}]
    assert len(selected) == 2
    assert {q.source_reference for q in selected} == {"Extract C"}
    assert all(not ollama_client._required_scope_terms(q) for q in selected)
    return full, full.model_copy(update={"questions": selected}), config, syllabus


class Client:
    model = "owned-edexcel-no-inference"

    def __init__(self, mode, *, prompts=None, before=None):
        self.provider = "openai" if mode == "hosted" else "ollama"
        self.supports_parallel_generation = mode == "hosted"
        self.parallel_generation_workers = 2 if mode == "local" else 1
        self.prompts = prompts or {}
        self.before = before
        self.calls = []
        self.lock = threading.Lock()

    def generate_request(self, request):
        if request.operation == "edexcel":
            number = re.search(
                r"^Question number: (.+)$", request.prompt, re.MULTILINE
            ).group(1)
        else:
            assert request.operation == "review"
            number = json.loads(request.prompt.rsplit("\n", 1)[1])[
                "item_id"
            ].removeprefix("question-")
        with self.lock:
            self.calls.append((request.operation, number))
        if self.before is not None:
            self.before(number, request.operation)
        if request.operation == "edexcel":
            value = {
                "question_text": self.prompts.get(number, SHARED),
                "graph_params": {},
                "parts": [],
            }
        else:
            value = {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        Draft202012Validator(request.schema).validate(value)
        return value


def store_for(path, full, client):
    return AssessmentCheckpointStore(
        path,
        identity_for_blueprint(
            {
                "paper_id": full.paper_id,
                "seed": full.seed,
                "blueprint": full.model_dump(mode="json"),
            },
            provider=client.provider,
            model=client.model,
            prompt_version="owned-edexcel-admission-test",
        ),
    )


def run(client, full, subset, config, syllabus, store, *, progress=None):
    improved = ollama_client.generate_questions_with_ollama(
        client, subset, syllabus, checkpoint_store=store, progress=progress
    )
    replacements = {q.number: q for q in improved.questions}
    candidate = full.model_copy(
        update={"questions": [replacements.get(q.number, q) for q in full.questions]}
    )
    validate_blueprint(candidate, config, syllabus)
    return candidate


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_duplicate_parent_refusal_never_persists_both_questions(tmp_path, mode):
    full, subset, config, syllabus = fixture()
    original = full.model_dump(mode="json")
    client = Client(mode)
    store = store_for(tmp_path / "checkpoint.json", full, client)
    store.save_payload("unrelated", {"sentinel": "kept"})
    with pytest.raises(ValueError, match="empty or duplicated"):
        run(client, full, subset, config, syllabus, store)
    assert len(client.calls) == 4
    assert (
        sum(
            store.load_payload(f"question-{q.number}") is not None
            for q in subset.questions
        )
        == 1
    )
    assert store.load_payload("unrelated") == {"sentinel": "kept"}
    assert full.model_dump(mode="json") == original


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_old_conflict_evicts_only_refused_key_and_next_retry_reauthors_it(
    tmp_path, mode
):
    full, subset, config, syllabus = fixture()
    seed_client = Client(mode)
    store = store_for(tmp_path / "checkpoint.json", full, seed_client)
    for question in subset.questions:
        ollama_client.generate_questions_with_ollama(
            seed_client,
            subset.model_copy(update={"questions": [question]}),
            syllabus,
            checkpoint_store=store,
        )
    store.save_payload("unrelated", {"sentinel": "kept"})
    retry = Client(mode)
    with pytest.raises(ValueError, match="empty or duplicated"):
        run(retry, full, subset, config, syllabus, store)
    assert retry.calls == []
    survivors = {
        q.number: store.load_payload(f"question-{q.number}")
        for q in subset.questions
        if store.load_payload(f"question-{q.number}") is not None
    }
    assert len(survivors) == 1
    missing = ({q.number for q in subset.questions} - survivors.keys()).pop()
    repaired = Client(mode, prompts={missing: ALTERNATIVE})
    result = run(repaired, full, subset, config, syllabus, store)
    assert repaired.calls == [("edexcel", missing), ("review", missing)]
    for number, payload in survivors.items():
        assert store.load_payload(f"question-{number}") == payload
    for original in subset.questions:
        candidate = next(q for q in result.questions if q.number == original.number)
        assert candidate.model_dump(
            exclude={"prompt", "provenance"}
        ) == original.model_dump(exclude={"prompt", "provenance"})
    assert store.load_payload("unrelated") == {"sentinel": "kept"}


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_accepted_question_survives_later_failure_or_cancellation(
    tmp_path, mode, failure
):
    full, subset, config, syllabus = fixture()
    admitted = threading.Event()

    def before(number, operation):
        if number == "1(e)" and operation == "edexcel":
            assert admitted.wait(5), "first question was not admitted"
            raise failure("controlled stop")

    def progress(event):
        if (isinstance(event, GenerationUpdate) and event.stage == "checkpoint") or (
            isinstance(event, str)
            and event.startswith("Generated and reviewed question")
        ):
            admitted.set()

    client = Client(mode, before=before)
    store = store_for(tmp_path / "checkpoint.json", full, client)
    with pytest.raises(failure, match="controlled stop"):
        run(client, full, subset, config, syllabus, store, progress=progress)
    assert store.load_payload("question-1(d)") is not None
    assert store.load_payload("question-1(e)") is None


@pytest.mark.parametrize("mode", ["serial", "local", "hosted"])
def test_admission_still_refuses_duplicates_without_a_checkpoint_store(mode):
    full, subset, config, syllabus = fixture()
    with pytest.raises(ValueError, match="empty or duplicated"):
        run(Client(mode), full, subset, config, syllabus, None)


def test_write_failure_preserves_prior_item_and_retry_authors_only_missing_item(
    tmp_path, monkeypatch
):
    full, subset, config, syllabus = fixture()
    client = Client("serial", prompts={"1(e)": ALTERNATIVE})
    store = store_for(tmp_path / "checkpoint.json", full, client)
    save = store.save_payload

    def fail_second(key, payload):
        if key == "question-1(e)":
            raise OSError("controlled checkpoint failure")
        save(key, payload)

    monkeypatch.setattr(store, "save_payload", fail_second)
    with pytest.raises(OSError, match="controlled checkpoint failure"):
        run(client, full, subset, config, syllabus, store)
    first = store.load_payload("question-1(d)")
    assert first is not None
    assert store.load_payload("question-1(e)") is None
    monkeypatch.setattr(store, "save_payload", save)
    retry = Client("serial", prompts={"1(e)": ALTERNATIVE})
    run(retry, full, subset, config, syllabus, store)
    assert retry.calls == [("edexcel", "1(e)"), ("review", "1(e)")]
    assert store.load_payload("question-1(d)") == first


def test_late_hosted_worker_only_stages_and_cannot_write_after_refusal(
    tmp_path, monkeypatch
):
    full, subset, config, syllabus = fixture()
    # A real third question keeps its own immutable source/marking contract.
    late = next(
        q
        for q in full.questions
        if q.number not in {"1(d)", "1(e)"}
        and not q.parts
        and q.command_word.casefold() == "evaluate"
        and not ollama_client._required_scope_terms(q)
    )
    subset = subset.model_copy(update={"questions": [*subset.questions, late]})
    late_started = threading.Event()
    release_late = threading.Event()
    late_staged = threading.Event()
    admitted = threading.Event()
    caller = threading.get_ident()
    writes = []

    def before(number, operation):
        if number == late.number:
            late_started.set()
            assert release_late.wait(5), "late worker not released"
        elif number == "1(d)" and operation == "edexcel":
            assert late_started.wait(5), "late worker not started"
        elif number == "1(e)" and operation == "edexcel":
            assert admitted.wait(5), "first item not admitted"
            raise RuntimeError("controlled stop")

    client = Client(
        "hosted",
        before=before,
        prompts={
            late.number: f"Evaluate solutions to economic problems with reference to {late.source_reference}."
        },
    )
    store = store_for(tmp_path / "checkpoint.json", full, client)
    save = store.save_payload
    stage = DeferredCheckpoints.save_payload

    def record_write(key, payload):
        writes.append(threading.get_ident())
        save(key, payload)

    def record_stage(self, key, payload):
        stage(self, key, payload)
        if key == f"question-{late.number}":
            late_staged.set()

    monkeypatch.setattr(store, "save_payload", record_write)
    monkeypatch.setattr(DeferredCheckpoints, "save_payload", record_stage)

    def progress(event):
        if isinstance(event, str) and event.startswith(
            "Generated and reviewed question"
        ):
            admitted.set()

    try:
        with pytest.raises(RuntimeError, match="controlled stop"):
            run(client, full, subset, config, syllabus, store, progress=progress)
        before_bytes = hashlib.sha256(store.path.read_bytes()).hexdigest()
    finally:
        release_late.set()
        assert late_staged.wait(5), "late worker did not finish staging"
    assert hashlib.sha256(store.path.read_bytes()).hexdigest() == before_bytes
    assert store.load_payload("question-1(d)") is not None
    assert store.load_payload("question-1(e)") is None
    assert store.load_payload(f"question-{late.number}") is None
    assert writes == [caller]
