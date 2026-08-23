from __future__ import annotations

import json
from pathlib import Path

import pytest

from Backend.Core.ai_assessment import GenerationPolicy, generate_unique_paper
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    CheckpointIdentity,
    CheckpointMismatch,
)
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


def test_checkpoint_rejects_model_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    AssessmentCheckpointStore(path, identity()).save_item("0/0/0", question())

    with pytest.raises(CheckpointMismatch, match="model"):
        AssessmentCheckpointStore(path, identity(model="qwen3:8b"))


def test_checkpoint_write_is_atomic_and_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())

    store.save_item("0/0/0", question())

    assert not list(tmp_path.glob("*.tmp"))
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["items"]["0/0/0"]["prompt"] == question().prompt


def test_generate_unique_paper_resumes_without_another_model_call(
    tmp_path: Path,
) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    paper, rule, topics = paper_fixture()

    first = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=FirstPassClient(),
        subject="Economics",
        policy=GenerationPolicy(attempts=1),
        checkpoint_store=store,
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
