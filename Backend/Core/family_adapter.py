from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Backend.Core.ai_assessment import (
    ASSESSMENT_REVIEW_VERSION,
    GenerationPolicy,
    generate_unique_paper,
)
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    identity_for_blueprint,
)
from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.model_recommendations import default_ollama_model
from Backend.Core.numeric_integrity import NUMERIC_INTEGRITY_VERSION
from Backend.Core.providers import HostedLLMClient
from Backend.Core.reference_demand import profile_for
from Backend.Core.render_transaction import render_pdf_atomically

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class BuildResult:
    assessment: Any
    context: Any = None


@dataclass(frozen=True)
class ArtifactSpec:
    role: str
    filename: str
    renderer: Callable[[Path], None]
    progress_message: str


@dataclass(frozen=True)
class FamilyAdapter:
    id: str
    subject_label: str
    backend_subject: str
    load_message: str
    build_message: str
    prompt_version: str
    load_syllabus: Callable[[Path], Any]
    load_rule: Callable[[str], Any]
    build: Callable[[Any, Any, int | None], BuildResult | Any]
    artifacts: Callable[[Any, Any, Any, str], Sequence[ArtifactSpec]]
    stem: Callable[[Any, str], str]
    preview_message: str = "Using the deterministic blueprint preview"
    validation_message: str = "Validating assessment package"
    resolve_seed: Callable[[int | None], int | None] | None = None
    seed_message: Callable[[int | None], str] | None = None
    validate: Callable[[Any, Any, Any], None] | None = None
    improve: Callable[
        [Any, Any, Any, object, ProgressCallback | None, AssessmentCheckpointStore | None],
        Any,
    ] | None = None
    calibrate_difficulty: Callable[
        [Any, Any, Any, object, ProgressCallback | None], Any
    ] | None = None
    client_factory: Callable[[str, str], object] | None = None
    checkpoint_identity: Callable[[Any, Any, str], Any] | None = None
    supporting_artifacts: Callable[
        [Any, Any, Any, str, Path, ProgressCallback], Mapping[str, Path]
    ] | None = None
    output_order: tuple[str, ...] = ()


def run_family_adapter(
    adapter: FamilyAdapter,
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    model: str = default_ollama_model(),
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: ProgressCallback | None = None,
    client: object | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit(adapter.load_message)
    syllabus = adapter.load_syllabus(syllabus_path)
    rule = adapter.load_rule(paper)
    effective_seed = adapter.resolve_seed(seed) if adapter.resolve_seed else seed
    if adapter.seed_message is not None:
        emit(adapter.seed_message(effective_seed))
    emit(adapter.build_message)
    built = adapter.build(rule, syllabus, effective_seed)
    if isinstance(built, BuildResult):
        assessment, context = built.assessment, built.context
    else:
        assessment, context = built, None

    question_client = client
    if dry_run:
        emit(adapter.preview_message)
    else:
        emit(f"Generating and independently reviewing questions with {model}")
        factory = adapter.client_factory or _hosted_client
        question_client = question_client or factory(model, ollama_url)
        identity_payload = (
            adapter.checkpoint_identity(assessment, rule, paper)
            if adapter.checkpoint_identity
            else assessment
        )
        checkpoint_store = (
            AssessmentCheckpointStore(
                checkpoint_path,
                identity_for_blueprint(
                    identity_payload,
                    provider=str(getattr(question_client, "provider", "ollama")),
                    model=str(getattr(question_client, "model", model)),
                    prompt_version=(
                        f"{adapter.prompt_version}:{NUMERIC_INTEGRITY_VERSION}:"
                        f"{ASSESSMENT_REVIEW_VERSION}"
                    ),
                ),
            )
            if checkpoint_path is not None
            else None
        )
        if adapter.improve is not None:
            assessment = adapter.improve(
                assessment,
                syllabus,
                rule,
                question_client,
                progress,
                checkpoint_store,
            )
            if adapter.calibrate_difficulty is None:
                raise ValueError(
                    f"{adapter.id} has a custom AI pipeline without a "
                    "reference-demand reviewer"
                )
            assessment = adapter.calibrate_difficulty(
                assessment,
                syllabus,
                rule,
                question_client,
                progress,
            )
        else:
            demand_profile = profile_for(adapter.id, paper)
            assessment = generate_unique_paper(
                assessment,
                rule=rule,
                syllabus_topics=syllabus.topics,
                syllabus_topic_ids=syllabus.topic_ids,
                client=question_client,
                subject=adapter.subject_label,
                progress=progress,
                checkpoint_store=checkpoint_store,
                policy=GenerationPolicy(
                    require_independent_solution=True,
                    require_difficulty_review=True,
                ),
                demand_profile=demand_profile,
            )

    if adapter.validate is not None:
        emit(adapter.validation_message)
        adapter.validate(assessment, rule, syllabus)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact in adapter.artifacts(assessment, context, syllabus, paper):
        destination = output_dir / artifact.filename
        emit(artifact.progress_message)
        render_pdf_atomically(
            destination,
            artifact.renderer,
            role=artifact.role.replace("_", " "),
        )
        paths[artifact.role] = destination

    if adapter.supporting_artifacts is not None:
        paths.update(
            adapter.supporting_artifacts(
                assessment,
                context,
                syllabus,
                paper,
                output_dir,
                emit,
            )
        )

    if adapter.output_order:
        paths = {
            role: paths[role]
            for role in adapter.output_order
            if role in paths
        } | {role: path for role, path in paths.items() if role not in adapter.output_order}

    assessment_path = output_dir / f"{adapter.stem(rule, paper)}-assessment.json"
    write_assessment_package(
        assessment,
        assessment_path,
        subject=adapter.backend_subject,
        paper_number=paper,
        preview=dry_run,
        provider=(
            getattr(question_client, "provider", "ollama") if not dry_run else None
        ),
        model=getattr(question_client, "model", model) if not dry_run else None,
    )
    paths["assessment_package"] = assessment_path
    emit("Done")
    return paths


def _hosted_client(model: str, ollama_url: str) -> object:
    return HostedLLMClient(
        provider="ollama",
        model=model,
        api_key="",
        base_url=ollama_url,
    )
