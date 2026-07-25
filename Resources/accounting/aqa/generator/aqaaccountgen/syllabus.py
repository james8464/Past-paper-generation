from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    points: list[str]

    @field_validator("points")
    @classmethod
    def require_points(cls, value: list[str]) -> list[str]:
        if len(value) < 3:
            raise ValueError("each accounting topic requires at least three points")
        return value


class Syllabus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qualification: str
    topics: list[Topic]

    @property
    def topic_ids(self) -> set[str]:
        return {topic.id for topic in self.topics}


def load_syllabus(path: Path) -> Syllabus:
    syllabus = Syllabus.model_validate_json(path.read_text(encoding="utf-8"))
    if len(syllabus.topic_ids) != len(syllabus.topics):
        raise ValueError("duplicate accounting topic id")
    return syllabus
