from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

QualificationLevel = Literal["engineering", "visual", "empirical"]
ReviewerIdentityClass = Literal[
    "automation",
    "internal_reviewer",
    "subject_specialist",
    "examiner",
    "psychometrician",
]


class GateState(StrEnum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class ModelIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str | None
    name: str | None
    digest: str | None = None


class VersionIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract: str = Field(min_length=1)
    blueprint: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    syllabus: str = Field(min_length=1)
    renderer: str = Field(min_length=1)


class ArtifactEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)

    @classmethod
    def from_path(cls, role: str, path: Path) -> ArtifactEvidence:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return cls(
            role=role,
            filename=path.name,
            sha256=digest.hexdigest(),
            bytes=path.stat().st_size,
        )


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    gate: str = ""
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_identity_class: ReviewerIdentityClass

    @field_validator("path")
    @classmethod
    def require_relative_evidence_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("evidence path must be repository-relative")
        return value


class QualificationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    levels: dict[QualificationLevel, tuple[str, ...]]

    @classmethod
    def load(cls, path: Path) -> QualificationPolicy:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def required_gates(self, level: QualificationLevel) -> tuple[str, ...]:
        return self.levels[level]


class QualificationManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    generator_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    seed: int
    model: ModelIdentity
    versions: VersionIdentity
    artifacts: list[ArtifactEvidence]
    gate_results: dict[str, GateState]
    evidence: list[EvidenceRecord]
    created_at: datetime
    reviewer_identity_class: ReviewerIdentityClass
    tool_versions: dict[str, str]

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        return value

    def record_evidence(
        self,
        gate: str,
        evidence: EvidenceRecord,
        *,
        state: GateState,
    ) -> QualificationManifest:
        if gate not in self.gate_results:
            raise ValueError(f"unknown qualification gate: {gate}")
        recorded = evidence.model_copy(update={"gate": gate})
        results = {**self.gate_results, gate: state}
        records = [item for item in self.evidence if item.gate != gate]
        records.append(recorded)
        return self.model_copy(
            update={"gate_results": results, "evidence": records},
            deep=True,
        )

    def is_qualified(
        self,
        level: QualificationLevel,
        policy: QualificationPolicy,
    ) -> bool:
        return all(
            self.gate_results.get(gate) in {
                GateState.PASSED,
                GateState.NOT_APPLICABLE,
            }
            for gate in policy.required_gates(level)
        )

    def canonical_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(self.canonical_json() + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def load(cls, path: Path) -> QualificationManifest:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
