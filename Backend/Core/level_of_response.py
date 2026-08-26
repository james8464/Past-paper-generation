from __future__ import annotations

import json
import math
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from Backend.Core.response_simulation import CandidateResponse


class LevelDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: int = Field(ge=0)
    minimum_mark: int = Field(ge=0)
    maximum_mark: int = Field(ge=0)
    minimum_coverage: float = Field(ge=0, le=1)
    descriptor: str = Field(min_length=1)


class BoardLevelPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    board: str
    maximum_mark: int = Field(gt=0)
    best_fit: bool = True
    levels: list[LevelDescriptor]
    misconception_cap_level: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_levels(self) -> BoardLevelPolicy:
        if not self.levels:
            raise ValueError("level policy requires descriptors")
        if [level.level for level in self.levels] != sorted(
            level.level for level in self.levels
        ):
            raise ValueError("level descriptors must be ordered")
        if self.levels[-1].maximum_mark != self.maximum_mark:
            raise ValueError("highest level must end at the policy maximum")
        return self


class MarkAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)

    mark: int
    awarded: bool
    reason: str


class MarkDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    mark: int
    level: int
    descriptor: str
    rationale: list[str]
    annotations: list[MarkAnnotation]
    cap_applied: str | None = None


class LevelOfResponseEngine:
    def mark(
        self,
        response: CandidateResponse,
        policy: BoardLevelPolicy,
    ) -> MarkDecision:
        demonstrated = len(set(response.demonstrated_mark_points))
        denominator = max(4, response.available_mark_points, demonstrated)
        coverage = demonstrated / denominator
        selected = max(
            (level for level in policy.levels if coverage >= level.minimum_coverage),
            key=lambda level: level.level,
        )
        cap_applied = None
        if (
            response.misconceptions
            and policy.misconception_cap_level is not None
            and selected.level >= policy.misconception_cap_level
        ):
            selected = max(
                (
                    level
                    for level in policy.levels
                    if level.level <= policy.misconception_cap_level
                ),
                key=lambda level: level.level,
            )
            cap_applied = (
                f"Level {policy.misconception_cap_level} cap: unresolved "
                + "; ".join(response.misconceptions)
            )
        next_threshold = next(
            (
                level.minimum_coverage
                for level in policy.levels
                if level.level == selected.level + 1
            ),
            1.0,
        )
        span = max(next_threshold - selected.minimum_coverage, 0.01)
        position = min(
            max((coverage - selected.minimum_coverage) / span, 0.0),
            1.0,
        )
        mark = min(
            selected.maximum_mark,
            selected.minimum_mark
            + math.floor(
                position * (selected.maximum_mark - selected.minimum_mark + 1)
            ),
        )
        rationale = [
            f"Best-fit Level {selected.level}: {selected.descriptor}",
            f"Observed {demonstrated} distinct creditworthy feature(s).",
        ]
        if cap_applied:
            rationale.append(cap_applied)
        annotations = [
            MarkAnnotation(
                mark=index,
                awarded=index <= mark,
                reason=(
                    f"Awarded within best-fit Level {selected.level}; "
                    f"feature coverage {coverage:.0%}."
                    if index <= mark
                    else f"Withheld above best-fit Level {selected.level} evidence."
                ),
            )
            for index in range(1, policy.maximum_mark + 1)
        ]
        return MarkDecision(
            mark=mark,
            level=selected.level,
            descriptor=selected.descriptor,
            rationale=rationale,
            annotations=annotations,
            cap_applied=cap_applied,
        )


def load_level_policies(path: Path) -> dict[str, BoardLevelPolicy]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported level-of-response policy schema")
    policies = [
        BoardLevelPolicy.model_validate(item) for item in payload.get("policies", [])
    ]
    result = {policy.id: policy for policy in policies}
    if len(result) != len(policies):
        raise ValueError("level-of-response policy identifiers must be unique")
    return result


def scale_level_policy(
    policy: BoardLevelPolicy,
    maximum_mark: int,
) -> BoardLevelPolicy:
    if maximum_mark <= 0:
        raise ValueError("scaled level policy requires a positive maximum")
    if maximum_mark == policy.maximum_mark:
        return policy
    levels: list[LevelDescriptor] = []
    previous_maximum = -1
    for index, level in enumerate(policy.levels):
        if level.level == 0:
            minimum = maximum = 0
        else:
            minimum = max(1, previous_maximum + 1)
            maximum = (
                maximum_mark
                if index == len(policy.levels) - 1
                else max(
                    minimum,
                    round(level.maximum_mark * maximum_mark / policy.maximum_mark),
                )
            )
        levels.append(
            level.model_copy(update={"minimum_mark": minimum, "maximum_mark": maximum})
        )
        previous_maximum = maximum
    return policy.model_copy(update={"maximum_mark": maximum_mark, "levels": levels})
