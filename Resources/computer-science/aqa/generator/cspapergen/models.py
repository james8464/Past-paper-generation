from __future__ import annotations

from pydantic import BaseModel, Field


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


class MarkingGuidance(BaseModel):
    ao: str
    points: list[str] = Field(default_factory=list)
    accept: list[str] = Field(default_factory=list)
    reject: list[str] = Field(default_factory=list)
    levels: list[str] = Field(default_factory=list)


class QuestionPart(BaseModel):
    label: str
    prompt: str
    marks: int = Field(gt=0)
    answer_lines: int = Field(default=3, ge=0)
    answer_unit: str = ""
    options: list[MultipleChoiceOption] = Field(default_factory=list)
    correct_option: str = ""
    marking: MarkingGuidance


class Question(BaseModel):
    number: int = Field(ge=1)
    topic_id: str
    style_id: str
    title: str
    stem: str
    stimulus: Stimulus | None = None
    parts: list[QuestionPart]

    @property
    def total_marks(self) -> int:
        return sum(part.marks for part in self.parts)


class PaperBlueprint(BaseModel):
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
