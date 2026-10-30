"""Typed hooks joining a family's rule, syllabus, assessment and render context."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from Backend.Core.assessment_checkpoints import AssessmentCheckpointStore
from Backend.Core.json_client import JSONGenerationClient

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class BuildResult[Assessment, Context]:
    assessment: Assessment
    context: Context | None = None


@dataclass(frozen=True)
class ArtifactSpec:
    role: str
    filename: str
    renderer: Callable[[Path], None]
    progress_message: str


@dataclass(frozen=True)
class FamilyAdapter[Syllabus, Rule, Assessment, Context]:
    id: str
    subject_label: str
    backend_subject: str
    load_message: str
    build_message: str
    prompt_version: str
    load_syllabus: Callable[[Path], Syllabus]
    load_rule: Callable[[str], Rule]
    build: Callable[
        [Rule, Syllabus, int | None], BuildResult[Assessment, Context] | Assessment
    ]
    artifacts: Callable[
        [Assessment, Context | None, Syllabus, str], Sequence[ArtifactSpec]
    ]
    stem: Callable[[Rule, str], str]
    preview_message: str = "Using the deterministic blueprint preview"
    validation_message: str = "Validating assessment package"
    resolve_seed: Callable[[int | None], int | None] | None = None
    seed_message: Callable[[int | None], str] | None = None
    validate: Callable[[Assessment, Rule, Syllabus], None] | None = None
    improve: (
        Callable[
            [
                Assessment,
                Syllabus,
                Rule,
                JSONGenerationClient,
                ProgressCallback | None,
                AssessmentCheckpointStore | None,
            ],
            Assessment,
        ]
        | None
    ) = None
    calibrate_difficulty: (
        Callable[
            [Assessment, Syllabus, Rule, JSONGenerationClient, ProgressCallback | None],
            Assessment,
        ]
        | None
    ) = None
    client_factory: Callable[[str, str], JSONGenerationClient] | None = None
    checkpoint_identity: Callable[[Assessment, Rule, str], object] | None = None
    supporting_artifacts: (
        Callable[
            [Assessment, Context | None, Syllabus, str, Path, ProgressCallback],
            Mapping[str, Path],
        ]
        | None
    ) = None
    output_order: tuple[str, ...] = ()
