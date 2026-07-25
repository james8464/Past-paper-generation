from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    component: int
    title: str
    points: list[str] = Field(min_length=3)


class Syllabus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qualification: str
    source: str
    source_urls: list[str]
    topics: list[Topic] = Field(min_length=1)

    @property
    def topic_ids(self) -> set[str]:
        return {topic.id for topic in self.topics}


def load_syllabus(path: Path) -> Syllabus:
    syllabus = Syllabus.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if len(syllabus.topic_ids) != len(syllabus.topics):
        raise ValueError("duplicate OCR Computer Science topic id")
    return syllabus
