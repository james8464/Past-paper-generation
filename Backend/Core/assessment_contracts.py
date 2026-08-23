from __future__ import annotations

from enum import StrEnum
import re
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from Backend.Core.assessment_quality import NUMBER_PATTERN


class NumericRole(StrEnum):
    ASSESSMENT_DATA = "assessment_data"
    MARK = "mark"
    DATE = "date"
    ITEM_IDENTIFIER = "item_identifier"
    DISPLAY_LABEL = "display_label"
    CODE_LINE_LABEL = "code_line_label"


class NumericValueContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    role: NumericRole = NumericRole.ASSESSMENT_DATA
    ordered: bool = False


class GeneratedNumericField(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    minimum: float
    maximum: float

    @model_validator(mode="after")
    def validate_range(self) -> GeneratedNumericField:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self

    def validate_value(self, value: float) -> float:
        if not self.minimum <= value <= self.maximum:
            raise ValueError(
                f"{self.name} must be between {self.minimum} and {self.maximum}"
            )
        return value


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class GraphContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = ""
    labels: list[str] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None

    @model_validator(mode="after")
    def validate_geometry(self) -> GraphContract:
        if len(self.labels) != len(self.values):
            raise ValueError("graph labels and values must have equal length")
        for name, minimum, maximum in (
            ("x", self.x_min, self.x_max),
            ("y", self.y_min, self.y_max),
        ):
            if minimum is not None and maximum is not None and minimum >= maximum:
                raise ValueError(f"graph {name} minimum must be below its maximum")
        return self


class AssessmentContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str = Field(min_length=1)
    marks: int = Field(gt=0)
    assessment_objectives: dict[str, int]
    numeric_values: list[NumericValueContract] = Field(default_factory=list)
    generated_numeric_fields: list[GeneratedNumericField] = Field(
        default_factory=list
    )
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    allowed_evidence_ids: set[str] = Field(default_factory=set)
    graph: GraphContract | None = None

    @model_validator(mode="after")
    def validate_assessment_metadata(self) -> AssessmentContract:
        if sum(self.assessment_objectives.values()) != self.marks:
            raise ValueError(
                "assessment objective marks must equal the item marks"
            )
        evidence_ids = [record.id for record in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence record identifiers must be unique")
        if not set(evidence_ids).issubset(self.allowed_evidence_ids):
            raise ValueError("evidence records must be included in allowed evidence ids")
        field_names = [field.name for field in self.generated_numeric_fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError("generated numeric field names must be unique")
        return self

    def validate_evidence_ids(self, references: Iterable[str]) -> None:
        unknown = set(references) - self.allowed_evidence_ids
        if unknown:
            raise ValueError(
                f"{self.item_id} cites unknown evidence: {sorted(unknown)}"
            )


def contract_for_question(question: Any) -> AssessmentContract:
    """Return an explicit item contract or hydrate one for a legacy blueprint."""

    explicit = getattr(question, "contract", None)
    if isinstance(explicit, AssessmentContract):
        return explicit

    context = getattr(question, "authoring_context", {})
    raw_contract = context.get("assessment_contract") if isinstance(context, dict) else None
    if isinstance(raw_contract, dict):
        return AssessmentContract.model_validate(raw_contract)

    prompt = str(getattr(question, "prompt", ""))
    references = {
        str(reference)
        for reference in getattr(question, "source_references", [])
        if str(reference).strip()
    }
    return AssessmentContract(
        item_id=str(getattr(question, "rule_id")),
        marks=int(getattr(question, "marks")),
        assessment_objectives=dict(
            getattr(question, "assessment_objectives", {})
        ),
        numeric_values=_numeric_contracts(prompt),
        allowed_evidence_ids=references,
    )


def _numeric_contracts(prompt: str) -> list[NumericValueContract]:
    contracts: list[NumericValueContract] = []
    for match in NUMBER_PATTERN.finditer(prompt):
        prefix = prompt[max(0, match.start() - 24) : match.start()]
        suffix = prompt[match.end() : match.end() + 16]
        if re.search(r"\bline\s*$", prefix, flags=re.IGNORECASE):
            role = NumericRole.CODE_LINE_LABEL
        elif re.search(
            r"\b(?:question|extract|figure|table)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            role = NumericRole.DISPLAY_LABEL
        elif re.match(r"\s*marks?\s*\]", suffix, flags=re.IGNORECASE):
            role = NumericRole.MARK
        else:
            role = NumericRole.ASSESSMENT_DATA
        contracts.append(
            NumericValueContract(text=match.group(0), role=role)
        )
    return contracts
