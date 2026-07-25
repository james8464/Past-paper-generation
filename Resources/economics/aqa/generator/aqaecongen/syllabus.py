from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Topic(BaseModel):
    id: str
    paper: int = Field(ge=1, le=2)
    title: str
    points: list[str]


class Syllabus(BaseModel):
    qualification: str
    source: str
    source_urls: list[str]
    topics: list[Topic]

    @property
    def topic_ids(self) -> set[str]:
        return {topic.id for topic in self.topics}


def load_syllabus(path: Path) -> Syllabus:
    return Syllabus.model_validate_json(path.read_text(encoding="utf-8"))
