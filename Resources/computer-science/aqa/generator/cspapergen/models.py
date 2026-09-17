from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from Backend.Core.subjects.sql_contracts import SQLSourceContract, render_sql_schema
from Backend.Core.topic_task_contract import ReferenceTaskContract


class SyllabusTopic(BaseModel):
    id: str
    title: str
    points: list[str] = Field(default_factory=list)


class Syllabus(BaseModel):
    qualification: str
    source: str
    topics: list[SyllabusTopic]

    @property
    def topic_ids(self) -> set[str]:
        return {topic.id for topic in self.topics}

    def get_topic(self, topic_id: str) -> SyllabusTopic:
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        raise KeyError(f"Unknown syllabus topic: {topic_id}")


class MultipleChoiceOption(BaseModel):
    label: str
    text: str


class Stimulus(BaseModel):
    kind: str
    title: str = ""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    lines: list[str] = Field(default_factory=list)
    code: str = ""
    diagram: str = ""
    sql_contract: SQLSourceContract | None = None

    @model_validator(mode="after")
    def sql_source_is_derived_from_contract(self) -> Stimulus:
        if self.sql_contract is not None and self.code != render_sql_schema(
            self.sql_contract
        ):
            raise ValueError("SQL source text differs from its typed public contract")
        return self


class MarkingGuidance(BaseModel):
    ao: str
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    points: list[str] = Field(default_factory=list)
    accept: list[str] = Field(default_factory=list)
    reject: list[str] = Field(default_factory=list)
    levels: list[str] = Field(default_factory=list)
    closed_answers: dict[str, list[str]] = Field(default_factory=dict)
    credit_allocations: list[dict[str, object]] = Field(default_factory=list)


class QuestionPart(BaseModel):
    label: str
    prompt: str
    marks: int = Field(gt=0)
    answer_lines: int = Field(default=3, ge=0)
    answer_unit: str = ""
    options: list[MultipleChoiceOption] = Field(default_factory=list)
    correct_option: str = ""
    marking: MarkingGuidance
    difficulty_evidence: dict[str, object] = Field(default_factory=dict)
    open_credit_contract: dict[str, object] = Field(default_factory=dict)
    open_credit_review: dict[str, object] = Field(default_factory=dict)
    response_slots: list[str] = Field(default_factory=list)
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    expected_minutes: float | None = Field(default=None, gt=0)
    task_operation: str = ""
    reference_source_dependency: Literal["self-contained", "task-context"] = (
        "self-contained"
    )
    reference_task_contract: ReferenceTaskContract | None = None
    sql_intent_id: str = ""

    def set_closed_answers(self, answers: dict[str, list[str]]) -> None:
        """Attach the immutable marking key separately from candidate slot IDs."""
        self.response_slots = list(answers)
        self.marking.closed_answers = answers


class Question(BaseModel):
    number: int = Field(ge=1)
    topic_id: str
    style_id: str
    title: str
    stem: str
    stimulus: Stimulus | None = None
    parts: list[QuestionPart]
    provenance: Literal["built-in", "reviewed-fixed", "ai-authored"] = "built-in"
    content_review: dict[str, object] = Field(default_factory=dict)
    reviewed_content_sha256: str = ""
    reviewed_blueprint_sha256: str = ""

    @property
    def total_marks(self) -> int:
        return sum(part.marks for part in self.parts)


class PaperBlueprint(BaseModel):
    assessment_kind: str = "full-paper"
    focus_topic_id: str = ""
    paper_code: str = "7517/2"
    title: str = "A-level COMPUTER SCIENCE Paper 2"
    paper_number: str = "2"
    delivery_mode: str = "written"
    session: str = "Morning"
    materials: list[str] = Field(default_factory=lambda: ["a calculator"])
    duration_minutes: int = 150
    total_marks: int = 100
    seed: int
    questions: list[Question]


class Paper1Context(BaseModel):
    scenario_title: str
    scenario_summary: str
    record_name: str
    category_names: list[str]
    command_names: list[str]
    skeleton_program: str
    data_file: str
