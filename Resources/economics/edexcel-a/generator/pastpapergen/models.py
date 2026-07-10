from __future__ import annotations

from pydantic import BaseModel, Field


class SyllabusTopic(BaseModel):
    id: str
    theme: int = Field(ge=1, le=4)
    title: str
    points: list[str] = Field(default_factory=list)


class Syllabus(BaseModel):
    qualification: str
    source: str
    topics: list[SyllabusTopic]

    @property
    def topic_count(self) -> int:
        return len(self.topics)

    def topics_for_themes(self, themes: set[int]) -> list[SyllabusTopic]:
        return [topic for topic in self.topics if topic.theme in themes]

    def topic_ids_for_themes(self, themes: set[int]) -> set[str]:
        return {topic.id for topic in self.topics_for_themes(themes)}

    def get_topic(self, topic_id: str) -> SyllabusTopic:
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        raise KeyError(f"Unknown syllabus topic: {topic_id}")


class SectionConfig(BaseModel):
    name: str
    title: str
    marks: int
    answer_marks: int
    question_marks: list[int]
    command_words: list[str]
    part_marks: list[list[int]] = Field(default_factory=list)
    part_command_words: list[list[str]] = Field(default_factory=list)
    stimulus_kinds: list[str] = Field(default_factory=list)
    choice_groups: list[list[int]] = Field(default_factory=list)


class QuestionPart(BaseModel):
    label: str
    marks: int
    command_word: str
    prompt: str
    options: list["MultipleChoiceOption"] = Field(default_factory=list)
    correct_option: str = ""
    mark_breakdown: str = ""
    mark_scheme: list[str] = Field(default_factory=list)
    indicative_content: list[str] = Field(default_factory=list)


class MultipleChoiceOption(BaseModel):
    label: str
    text: str


class PaperConfig(BaseModel):
    id: str
    code: str
    title: str
    allowed_themes: set[int]
    duration_minutes: int
    total_marks: int
    sections: list[SectionConfig]


class QuestionBlueprint(BaseModel):
    section: str
    number: str
    marks: int
    command_word: str
    topic_id: str
    prompt: str
    parts: list[QuestionPart] = Field(default_factory=list)
    stimulus_kind: str = ""
    choice_group: str | None = None
    source_reference: str = ""
    source_title: str = ""
    source_text: str = ""
    mark_breakdown: str = ""
    mark_scheme: list[str] = Field(default_factory=list)
    indicative_content: list[str] = Field(default_factory=list)
    graph_params: dict[str, object] = Field(default_factory=dict)


class PaperBlueprint(BaseModel):
    paper_id: str
    paper_code: str
    title: str
    duration_minutes: int
    total_marks: int
    questions: list[QuestionBlueprint]
