from __future__ import annotations

import json
from pathlib import Path

import pytest

from Backend.Core.ai_assessment import GenerationPolicy, generate_unique_paper
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    CheckpointCorrupt,
    CheckpointIdentity,
    CheckpointMismatch,
    identity_for_blueprint,
)
from Backend.Core.events import GenerationUpdate
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    SectionRule,
)


def identity(*, model: str = "gemma4:12b") -> CheckpointIdentity:
    return CheckpointIdentity(
        paper_id="paper-1",
        seed=123,
        provider="ollama",
        model=model,
        blueprint_sha256="a" * 64,
        prompt_version="assessment-v1",
    )


def question() -> GeneratedQuestion:
    return GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain why higher costs reduce profit.",
        mark_scheme=["Credit a correct causal relationship."],
        assessment_objectives={"AO1": 1},
    )


def test_checkpoint_round_trips_an_accepted_question(tmp_path: Path) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())

    store.save_item("0/0/0", question())

    assert store.load_item("0/0/0") == question()
    assert store.load_item("0/0/1") is None


def test_checkpoint_can_discard_one_rejected_item(tmp_path: Path) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    store.save_item("0/0/0", question())
    store.save_item("0/0/1", question())

    store.discard_item("0/0/0")

    assert store.load_item("0/0/0") is None
    assert store.load_item("0/0/1") == question()


def test_checkpoint_rejects_model_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    AssessmentCheckpointStore(path, identity()).save_item("0/0/0", question())

    with pytest.raises(CheckpointMismatch, match="model"):
        AssessmentCheckpointStore(path, identity(model="qwen3:8b"))


def test_checkpoint_retains_items_across_blueprint_revision_for_revalidation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "job.json"
    AssessmentCheckpointStore(path, identity()).save_item("0/0/0", question())
    revised = identity().model_copy(update={"blueprint_sha256": "b" * 64})

    store = AssessmentCheckpointStore(path, revised)

    assert store.load_item("0/0/0") == question()
    assert json.loads(path.read_text())["identity"]["blueprint_sha256"] == "b" * 64


def test_checkpoint_write_is_atomic_and_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())

    store.save_item("0/0/0", question())

    assert not list(tmp_path.glob("*.tmp"))
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["items"]["0/0/0"]["prompt"] == question().prompt


def test_corrupt_checkpoint_fails_closed_with_actionable_identity(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    path.write_text('{"schema_version": 1, "items": ', encoding="utf-8")

    with pytest.raises(CheckpointCorrupt, match="checkpoint is unreadable.*job.json"):
        AssessmentCheckpointStore(path, identity())


def test_checkpoint_round_trips_family_specific_payload(tmp_path: Path) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    payload = {"number": "1", "prompt": "Explain the relationship."}

    store.save_payload("question-1", payload)

    assert store.load_payload("question-1") == payload


def test_blueprint_identity_changes_when_immutable_blueprint_changes() -> None:
    first = identity_for_blueprint(
        {"paper_id": "paper-1", "seed": 123, "questions": [1]},
        provider="ollama",
        model="gemma4:12b",
        prompt_version="assessment-v1",
    )
    second = identity_for_blueprint(
        {"paper_id": "paper-1", "seed": 123, "questions": [1, 2]},
        provider="ollama",
        model="gemma4:12b",
        prompt_version="assessment-v1",
    )

    assert first.paper_id == "paper-1"
    assert first.seed == 123
    assert first.blueprint_sha256 != second.blueprint_sha256


def test_generate_unique_paper_resumes_without_another_model_call(
    tmp_path: Path,
) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    paper, rule, topics = paper_fixture()
    events: list[object] = []

    first = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=FirstPassClient(),
        subject="Economics",
        policy=GenerationPolicy(attempts=1),
        checkpoint_store=store,
        progress=events.append,
    )
    resumed = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=NoCallsClient(),
        subject="Economics",
        policy=GenerationPolicy(attempts=1),
        checkpoint_store=store,
    )

    assert resumed == first
    assert resumed.sections[0].options[0].questions[0].prompt == question().prompt
    assert any(
        isinstance(event, GenerationUpdate)
        and event.stage == "checkpoint"
        and event.completed_units == 1
        and event.total_units == 1
        for event in events
    )


def paper_fixture() -> tuple[GeneratedPaper, PaperRule, list[object]]:
    draft = question().model_copy(
        update={
            "prompt": "Explain how a change in costs can affect profit.",
            "mark_scheme": ["Credit a valid relationship."],
        }
    )
    paper = GeneratedPaper(
        paper_id="paper-1",
        paper_code="TEST/1",
        title="Test paper",
        duration_minutes=60,
        total_marks=1,
        seed=123,
        sections=[
            GeneratedSection(
                id="A",
                title="Section A",
                instructions="Answer the question.",
                options=[
                    GeneratedOption(
                        id="option",
                        title="Option",
                        questions=[draft],
                    )
                ],
            )
        ],
    )
    rule = PaperRule(
        id="paper-1",
        code="TEST/1",
        title="Test paper",
        duration_minutes=60,
        total_marks=1,
        allowed_topic_ids={"topic"},
        sections=[
            SectionRule(
                id="A",
                title="Section A",
                option_count=1,
                answer_options=1,
                option_marks=1,
                questions=[
                    QuestionRule(
                        id="q1",
                        marks=1,
                        kind="explain",
                        command_word="explain",
                        assessment_objectives={"AO1": 1},
                    )
                ],
            )
        ],
    )
    topic = type(
        "Topic",
        (),
        {"id": "topic", "title": "Costs and profit", "points": []},
    )()
    return paper, rule, [topic]


class FirstPassClient:
    provider = "ollama"
    model = "gemma4:12b"
    supports_parallel_generation = False

    def __init__(self) -> None:
        self.responses = iter(
            [
                {
                    "questions": [
                        {
                            "id": "0/0/0",
                            "prompt": question().prompt,
                            "mark_scheme": [
                                {
                                    "text": question().mark_scheme[0],
                                    "marks": 1,
                                    "assessment_objective": "AO1",
                                }
                            ],
                        }
                    ]
                },
                {
                    "reviews": [
                        {
                            "id": "0/0/0",
                            "approved": True,
                            "factual_issues": [],
                            "marking_issues": [],
                            "source_issues": [],
                            "difficulty_issues": [],
                            "ambiguity_issues": [],
                        }
                    ]
                },
            ]
        )

    def generate_json(self, _prompt: str) -> dict[str, object]:
        return next(self.responses)


class NoCallsClient:
    provider = "ollama"
    model = "gemma4:12b"
    supports_parallel_generation = False

    def generate_json(self, _prompt: str) -> dict[str, object]:
        raise AssertionError("a valid checkpoint must avoid another model call")
