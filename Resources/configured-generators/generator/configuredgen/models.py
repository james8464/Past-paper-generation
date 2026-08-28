from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from Backend.Core.exam_blueprints import PaperRule, SectionRule


class Topic(BaseModel):
    id: str
    title: str
    points: list[str] = Field(min_length=3)
    papers: list[str] = Field(min_length=1)


class PaperSpecification(BaseModel):
    id: str
    code: str
    title: str
    duration_minutes: int = Field(gt=0)
    marks: int = Field(gt=0)
    instructions: list[str] = Field(min_length=1)
    sections: list[SectionRule] = Field(min_length=1)
    output_roles: list[str] = Field(
        default_factory=lambda: [
            "question_paper",
            "mark_scheme",
            "assessment_package",
        ]
    )


class ConfiguredSyllabus(BaseModel):
    schema_version: int
    family_id: str
    backend_subject: str
    subject_label: str
    subject_plugin: str
    board_profile: str
    specification_version: str
    blueprint_version: str
    provenance: list[str] = Field(min_length=1)
    topics: list[Topic] = Field(min_length=1)
    papers: list[PaperSpecification] = Field(min_length=1)

    @property
    def topic_ids(self) -> set[str]:
        return {topic.id for topic in self.topics}

    def paper(self, identifier: str) -> PaperSpecification:
        normalized = identifier.strip().removeprefix("paper_").removeprefix(
            "paper"
        )
        try:
            return next(paper for paper in self.papers if paper.id == normalized)
        except StopIteration as error:
            raise ValueError(
                f"{self.family_id} has no paper {identifier}"
            ) from error

    def rule(self, identifier: str) -> PaperRule:
        paper = self.paper(identifier)
        allowed = {
            topic.id for topic in self.topics if paper.id in topic.papers
        }
        return PaperRule(
            id=f"paper_{paper.id}",
            code=paper.code,
            title=paper.title,
            duration_minutes=paper.duration_minutes,
            total_marks=paper.marks,
            allowed_topic_ids=allowed,
            sections=paper.sections,
        )


def load_syllabus(path: Path) -> ConfiguredSyllabus:
    payload = json.loads(path.read_text(encoding="utf-8"))
    syllabus = ConfiguredSyllabus.model_validate(payload)
    if syllabus.schema_version != 1:
        raise ValueError("configured syllabus schema is unsupported")
    if len({paper.id for paper in syllabus.papers}) != len(syllabus.papers):
        raise ValueError("configured syllabus repeats a paper id")
    if len(syllabus.topic_ids) != len(syllabus.topics):
        raise ValueError("configured syllabus repeats a topic id")
    for paper in syllabus.papers:
        if not any(paper.id in topic.papers for topic in syllabus.topics):
            raise ValueError(f"paper {paper.id} has no syllabus topics")
    return syllabus
