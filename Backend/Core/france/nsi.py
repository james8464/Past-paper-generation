"""Native French NSI authoring records and prompts, not translated A-level items."""

import json
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from Backend.Core.education_context import points

TOPICS = frozenset(
    {
        "structures-donnees",
        "bases-donnees",
        "architectures-reseaux",
        "langages-programmation",
        "algorithmique",
    }
)


class Credit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    points: str
    criterion: str = Field(min_length=3, max_length=1200)

    @field_validator("points")
    @classmethod
    def valid_points(cls, value):
        if points(value) <= 0:
            raise ValueError("Crédit strictement positif requis")
        return value


class NSIQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[1-9][0-9]?[a-z]?$", max_length=3)
    prompt: str = Field(min_length=10, max_length=4000)
    points: str
    answer: str = Field(min_length=1, max_length=6000)
    marking: tuple[Credit, ...] = Field(min_length=1, max_length=12)
    verification: dict[str, Any] = Field(default_factory=lambda: {"kind": "human"})

    @model_validator(mode="after")
    def credit_matches(self):
        if points(self.points) <= 0 or sum(
            points(item.points) for item in self.marking
        ) != points(self.points):
            raise ValueError("Le barème ne correspond pas aux points de la question")
        if len(json.dumps(self.verification, ensure_ascii=False)) > 16000:
            raise ValueError("Contrat de vérification trop long")
        return self


class NSIExercise(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[123]$")
    title: str = Field(min_length=3, max_length=160)
    context: str = Field(min_length=10, max_length=12000)
    topics: tuple[str, ...] = Field(min_length=1, max_length=5)
    minutes: int = Field(strict=True, ge=40, le=80)
    questions: tuple[NSIQuestion, ...] = Field(min_length=4, max_length=16)

    @model_validator(mode="after")
    def validate_structure(self):
        if set(self.topics) - TOPICS or len(set(self.topics)) != len(self.topics):
            raise ValueError("Thème absent du programme NSI")
        identifiers = [question.id for question in self.questions]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Les identifiants de questions doivent être uniques")
        if self.credit != Decimal("6"):
            raise ValueError("Ce prototype réserve six points techniques par exercice")
        return self

    @property
    def credit(self) -> Decimal:
        return sum((points(question.points) for question in self.questions), Decimal(0))

    def candidate_view(self) -> dict:
        return self.model_dump(
            exclude={"questions": {"__all__": {"answer", "marking", "verification"}}},
            mode="json",
        )


def solver_prompt(exercise: NSIExercise) -> str:
    return (
        "Résous indépendamment cet exercice de spécialité NSI, Terminale, bac général. "
        "N'invente aucune donnée manquante. Signale toute ambiguïté ou impossibilité. "
        'Réponds en français, en JSON : {"answers": {identifiant: réponse détaillée}, '
        '"issues": [problèmes], "minutes": estimation}. Aucun corrigé n\'est fourni.\n'
        + json.dumps(exercise.candidate_view(), ensure_ascii=False)
    )
