"""Allocation-free content wire and assembly from a product-owned mark plan.

Question estimated_minutes/difficulty and quantitative source/graph data remain
authored content. Only credit allocations, IDs, and exercise totals are owned.
"""

from __future__ import annotations

from copy import deepcopy
from types import GenericAlias

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, create_model

from Backend.Core.france.mark_plan import ExerciseMarkPlan, decimal_text
from Backend.Core.france.nsi import NSIExercise, NSIQuestion


class CriterionContent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    criterion: str = Field(min_length=3, max_length=1200)


class ContentContractError(ValueError):
    """The wire keys do not match their independently owned plan slots."""


def _fields(model, excluded):
    return {
        name: (field.annotation, deepcopy(field))
        for name, field in model.model_fields.items()
        if name not in excluded
    }


QuestionContent = create_model(
    "QuestionContent",
    __config__=ConfigDict(extra="forbid", frozen=True),
    **_fields(NSIQuestion, {"id", "points", "marking"}),
    marking=(dict[str, CriterionContent], ...),
)
ExerciseContent = create_model(
    "ExerciseContent",
    __config__=ConfigDict(extra="forbid", frozen=True),
    **_fields(NSIExercise, {"minutes", "target_points", "questions"}),
    # Dynamic model types need a runtime annotation, not a static type alias.
    questions=(GenericAlias(dict, (str, QuestionContent)), ...),
)


def content_schema(plan: ExerciseMarkPlan, canonical_schema: dict) -> dict:
    """Use portable exact object properties; object key order is immaterial."""
    plan = ExerciseMarkPlan.model_validate(plan.model_dump(mode="json"))
    schema = deepcopy(canonical_schema)
    for name in ("minutes", "target_points"):
        schema["properties"].pop(name)
        schema["required"].remove(name)
    question = schema["$defs"]["NSIQuestion"]
    for name in ("id", "points"):
        question["properties"].pop(name)
        question["required"].remove(name)
    criterion = schema["$defs"]["Credit"]
    criterion["properties"].pop("points")
    criterion["required"].remove("points")
    # Share the large verification/material contract, not one copy per slot.
    # JSON Schema admits only this exercise's criterion IDs; the host below
    # enforces the exact per-question partition before canonical assembly.
    question["properties"]["marking"] = {
        "type": "object",
        "additionalProperties": False,
        "minProperties": 1,
        "maxProperties": 2,
        "properties": {
            c.id: {"$ref": "#/$defs/Credit"}
            for slot in plan.questions
            for c in slot.criteria
        },
    }
    schema["$defs"]["QuestionContent"] = schema["$defs"].pop("NSIQuestion")
    schema["properties"]["questions"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            q.id: {"$ref": "#/$defs/QuestionContent"} for q in plan.questions
        },
        "required": [q.id for q in plan.questions],
    }
    return schema


def assemble_exercise(plan: ExerciseMarkPlan, raw: dict) -> NSIExercise:
    # Revalidate instances too: frozen model_copy(update=...) is not validation.
    plan = ExerciseMarkPlan.model_validate(plan.model_dump(mode="json"))
    content = ExerciseContent.model_validate(raw)
    if content.id != plan.exercise_id:
        raise ContentContractError("Identité du contenu différente du plan")
    if set(content.questions) != {q.id for q in plan.questions}:
        raise ContentContractError("Questions du contenu différentes du plan")
    questions = []
    for slot in plan.questions:
        source = content.questions[slot.id]
        if set(source.marking) != {c.id for c in slot.criteria}:
            raise ContentContractError("Critères du contenu différents du plan")
        question = source.model_dump(mode="json", exclude={"marking"})
        question.update(
            id=slot.id,
            points=decimal_text(slot.points),
            marking=[
                {
                    "points": decimal_text(c.points),
                    "criterion": source.marking[c.id].criterion,
                }
                for c in slot.criteria
            ],
        )
        questions.append(question)
    assembled = content.model_dump(mode="json", exclude={"questions"})
    assembled.update(minutes=70, target_points="6", questions=questions)
    return NSIExercise.model_validate(
        assembled, context={"authoring_profile": "v36-model-authored"}
    )


def validate_content_response(
    raw: dict, plan: ExerciseMarkPlan, schema: dict
) -> NSIExercise:
    Draft202012Validator(schema).validate(raw)
    return assemble_exercise(plan, raw)
