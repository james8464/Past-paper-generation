# Run subject-family hooks through shared authoring, validation and rendering steps.

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

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
from Backend.Core.document_publication import publish_document_set
from Backend.Core.family_contracts import ArtifactSpec as ArtifactSpec
from Backend.Core.family_contracts import BuildResult as BuildResult
from Backend.Core.family_contracts import FamilyAdapter as FamilyAdapter
from Backend.Core.family_contracts import ProgressCallback as ProgressCallback
from Backend.Core.json_client import JSONGenerationClient
from Backend.Core.model_recommendations import default_ollama_model
from Backend.Core.numeric_integrity import NUMERIC_INTEGRITY_VERSION
from Backend.Core.preview_presentation import preview_presentation, validate_preview_pdf
from Backend.Core.providers import HostedLLMClient
from Backend.Core.reference_demand import profile_for
from Backend.Core.render_transaction import render_pdf_atomically


def run_family_adapter[Syllabus, Rule, Assessment, Context](
    adapter: FamilyAdapter[Syllabus, Rule, Assessment, Context],
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    model: str = default_ollama_model(),
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: ProgressCallback | None = None,
    client: JSONGenerationClient | None = None,
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

    # Preview uses the seeded blueprint and makes no authoring requests.
    question_client = client
    if dry_run:
        emit(adapter.preview_message)
    else:
        emit(f"Generating and independently reviewing questions with {model}")
        factory = adapter.client_factory or _hosted_client
        question_client = question_client or factory(model, ollama_url)
        # Resumed items must match the family blueprint, provider and review versions.
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
    # Direct family CLIs do not have the bridge's outer output transaction.
    # Keep every role private until rendering, support and packaging all succeed.
    with TemporaryDirectory(prefix=".keldin-family-", dir=output_dir) as temporary:
        staging_dir = Path(temporary)
        paths: dict[str, Path] = {}
        # Scope includes supporting PDFs; disabled scopes override outer previews.
        with preview_presentation(dry_run):
            for artifact in adapter.artifacts(assessment, context, syllabus, paper):
                if Path(artifact.filename).name != artifact.filename:
                    raise ValueError("Artifact filenames must be direct children")
                destination = staging_dir / artifact.filename
                emit(artifact.progress_message)

                def render(path: Path, artifact: ArtifactSpec = artifact) -> None:
                    artifact.renderer(path)
                    if dry_run:
                        validate_preview_pdf(path)

                render_pdf_atomically(
                    destination,
                    render,
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
                        staging_dir,
                        emit,
                    )
                )
            if dry_run:
                for path in paths.values():
                    if path.suffix.casefold() == ".pdf":
                        validate_preview_pdf(path)

        if adapter.output_order:
            paths = {
                role: paths[role] for role in adapter.output_order if role in paths
            } | {
                role: path
                for role, path in paths.items()
                if role not in adapter.output_order
            }

        assessment_path = staging_dir / f"{adapter.stem(rule, paper)}-assessment.json"
        if assessment_path.parent.resolve() != staging_dir.resolve():
            raise ValueError("Assessment filename must be a direct child")
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
        if any(
            path.is_symlink()
            or not path.is_file()
            or path.resolve().parent != staging_dir.resolve()
            for path in paths.values()
        ):
            raise ValueError(
                "Family outputs must be files inside their staging directory"
            )
        # The bridge may still need to validate and publish these files itself.
        paths = publish_document_set(paths, output_dir, final_publication=False)
    emit("Done")
    return paths


def _hosted_client(model: str, ollama_url: str) -> JSONGenerationClient:
    return HostedLLMClient(
        provider="ollama",
        model=model,
        api_key="",
        base_url=ollama_url,
    )
