"""Product-owned numeric topologies, not question or answer catalogues."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from typing import Annotated, Final, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from Backend.Core.education_context import points

MARK_PLAN_POLICY: Final = "fr-nsi-product-mark-plan-v1"
MARK_PLAN_AUTHORING_POLICY = "fr-nsi-v36-planned-content-v1"
CONTENT_ASSEMBLY_POLICY = "fr-nsi-content-assembly-v1"
PROFILES = (
    ("1", "1", "2", "2"),
    ("0.5", "1", "1", "1.5", "2"),
    ("0.5", "0.5", "1", "1", "1.5", "1.5"),
)


def decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _amount(value):
    if type(value) is str:
        amount = points(value)
        if decimal_text(amount) != value:
            raise ValueError("Allocation décimale non canonique")
    elif isinstance(value, Decimal):
        amount = value
    else:
        raise ValueError("Allocation Decimal ou chaîne canonique requise")
    if (
        not amount.is_finite()
        or not Decimal(0) < amount <= Decimal("999999.9999")
        or amount.as_tuple().exponent < -4
    ):
        raise ValueError("Allocation positive bornée requise")
    return amount


Amount = Annotated[Decimal, BeforeValidator(_amount)]


class CriterionAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    points: Amount

    @field_serializer("points")
    def serialize_points(self, value):
        return decimal_text(value)


def _partition(amount: Decimal) -> tuple[Decimal, ...]:
    return {
        Decimal("0.5"): (Decimal("0.5"),),
        Decimal("1"): (Decimal("1"),),
        Decimal("1.5"): (Decimal("0.5"), Decimal("1")),
        Decimal("2"): (Decimal("1"), Decimal("1")),
    }[amount]


class QuestionMarkPlan(CriterionAllocation):
    criteria: tuple[CriterionAllocation, ...] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def valid_partition(self):
        if self.points not in {
            Decimal("0.5"),
            Decimal("1"),
            Decimal("1.5"),
            Decimal("2"),
        }:
            raise ValueError("Tarif absent du profil produit")
        if tuple(c.points for c in self.criteria) != _partition(self.points) or tuple(
            c.id for c in self.criteria
        ) != tuple(f"{self.id}.{i}" for i in range(1, len(self.criteria) + 1)):
            raise ValueError("Partition ou identifiants de critères invalides")
        return self


class ExerciseMarkPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy: Literal["fr-nsi-product-mark-plan-v1"] = MARK_PLAN_POLICY
    exercise_id: Literal["1", "2", "3"]
    profile_index: int = Field(strict=True, ge=0, le=2)
    questions: tuple[QuestionMarkPlan, ...] = Field(min_length=4, max_length=6)

    @model_validator(mode="after")
    def valid_exercise(self):
        if tuple(decimal_text(q.points) for q in self.questions) != PROFILES[
            self.profile_index
        ] or sum((q.points for q in self.questions), Decimal(0)) != Decimal("6"):
            raise ValueError("Le plan doit suivre son profil et totaliser six points")
        if tuple(q.id for q in self.questions) != tuple(
            f"{self.exercise_id}{chr(97 + i)}" for i in range(len(self.questions))
        ):
            raise ValueError("Identifiants de questions invalides")
        return self


def build_mark_plan(seed: int, exercise_id: str) -> ExerciseMarkPlan:
    if type(seed) is not int or exercise_id not in {"1", "2", "3"}:
        raise ValueError("Graine et exercice du plan invalides")
    index = int.from_bytes(
        sha256(f"{MARK_PLAN_POLICY}:{seed}:{exercise_id}".encode()).digest(), "big"
    ) % len(PROFILES)
    questions = []
    for i, value in enumerate(PROFILES[index]):
        identifier = f"{exercise_id}{chr(97 + i)}"
        amount = Decimal(value)
        questions.append(
            QuestionMarkPlan(
                id=identifier,
                points=amount,
                criteria=tuple(
                    CriterionAllocation(id=f"{identifier}.{j}", points=credit)
                    for j, credit in enumerate(_partition(amount), 1)
                ),
            )
        )
    return ExerciseMarkPlan(
        exercise_id=exercise_id, profile_index=index, questions=tuple(questions)
    )


def build_mark_plans(seed: int) -> tuple[ExerciseMarkPlan, ...]:
    return tuple(build_mark_plan(seed, str(i)) for i in (1, 2, 3))


def plan_payload(plans: tuple[ExerciseMarkPlan, ...]) -> list[dict]:
    return [plan.model_dump(mode="json") for plan in plans]


def mark_plans_digest(plans: tuple[ExerciseMarkPlan, ...]) -> str:
    return sha256(
        json.dumps(
            plan_payload(plans),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def validate_mark_plans(raw, seed: int) -> tuple[ExerciseMarkPlan, ...]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("Trois plans de barème requis")
    plans = tuple(ExerciseMarkPlan.model_validate(value) for value in raw)
    if raw != plan_payload(plans) or plans != build_mark_plans(seed):
        raise ValueError("Plan du barème modifié ou autre graine")
    return plans
