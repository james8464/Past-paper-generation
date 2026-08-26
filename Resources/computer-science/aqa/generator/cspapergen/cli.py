from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from Backend.Core.family_adapter import (
    ArtifactSpec,
    BuildResult,
    FamilyAdapter,
    run_family_adapter,
)
from Backend.Core.model_recommendations import default_ollama_model
from cspapergen.generator import build_paper1_blueprint, build_paper2_blueprint
from cspapergen.notes import DEFAULT_NOTES_SOURCE, cache_notes
from cspapergen.ollama_client import OllamaClient, improve_questions_with_ollama
from cspapergen.paper1_assets import write_paper1_supporting_files
from cspapergen.render_pdf import render_mark_scheme, render_question_paper
from cspapergen.syllabus import DEFAULT_SYLLABUS_PATH, load_syllabus
from cspapergen.validation import validate_blueprint


def _load_rule(paper: str) -> str:
    if paper not in {"1", "2"}:
        raise ValueError(f"Unsupported Computer Science paper: {paper}")
    return paper


def _build(paper: str, syllabus, seed: int | None) -> BuildResult:
    if paper == "1":
        blueprint, context = build_paper1_blueprint(syllabus, seed=seed)
        return BuildResult(blueprint, context)
    return BuildResult(build_paper2_blueprint(syllabus, seed=seed))


def _improve(blueprint, syllabus, _paper, client, progress, checkpoint_store):
    return improve_questions_with_ollama(
        client,
        blueprint,
        syllabus,
        progress=progress,
        checkpoint_store=checkpoint_store,
    )


def _artifacts(blueprint, _context, _syllabus, paper: str) -> tuple[ArtifactSpec, ...]:
    stem = f"cs-paper-{paper}"
    return (
        ArtifactSpec(
            "question_paper",
            f"{stem}-question-paper.pdf",
            lambda path: render_question_paper(blueprint, path),
            "Rendering question paper",
        ),
        ArtifactSpec(
            "mark_scheme",
            f"{stem}-mark-scheme.pdf",
            lambda path: render_mark_scheme(blueprint, path),
            "Rendering mark scheme",
        ),
    )


def _supporting(blueprint, context, _syllabus, paper, output, emit):
    if paper != "1" or context is None:
        return {}
    emit("Rendering Paper 1 supporting materials")
    return write_paper1_supporting_files(blueprint, context, output)


ADAPTER = FamilyAdapter(
    id="aqa/computer-science",
    subject_label="AQA A-level Computer Science",
    backend_subject="computer_science",
    load_message="Loading AQA Computer Science specification map",
    build_message="Building AQA 7517 paper blueprint",
    prompt_version="aqa-computer-science-v1",
    load_syllabus=load_syllabus,
    load_rule=_load_rule,
    build=_build,
    artifacts=_artifacts,
    stem=lambda _paper_rule, paper: f"cs-paper-{paper}",
    validate=lambda blueprint, _paper, syllabus: validate_blueprint(
        blueprint, syllabus
    ),
    improve=_improve,
    client_factory=lambda model, url: OllamaClient(base_url=url, model=model),
    checkpoint_identity=lambda blueprint, _paper_rule, paper: {
        "paper_id": f"paper-{paper}",
        "seed": blueprint.seed,
        "blueprint": blueprint.model_dump(mode="json"),
    },
    supporting_artifacts=_supporting,
    output_order=(
        "question_paper",
        "preliminary_material",
        "electronic_answer_document",
        "skeleton_program",
        "data_file",
        "mark_scheme",
    ),
)


def generate_package(
    *,
    output_dir: Path,
    paper: str = "2",
    seed: int | None,
    dry_run: bool,
    model: str = default_ollama_model(),
    ollama_url: str = "http://localhost:11434",
    syllabus_path: Path = DEFAULT_SYLLABUS_PATH,
    notes_source: Path = DEFAULT_NOTES_SOURCE,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Path]:
    if progress is not None:
        progress("Caching notes")
    cache_notes(notes_source)
    return run_family_adapter(
        ADAPTER,
        paper=paper,
        syllabus_path=syllabus_path,
        output_dir=output_dir,
        seed=seed,
        model=model,
        ollama_url=ollama_url,
        dry_run=dry_run,
        progress=progress,
        client=client,
        checkpoint_path=checkpoint_path,
    )


def default_output_dir() -> Path:
    return Path.home() / "Downloads"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate an unofficial AQA A-Level Computer Science practice paper."
    )
    parser.add_argument("--paper", choices=["1", "2"], default="2")
    parser.add_argument("--out", default=str(default_output_dir()))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model", default=default_ollama_model())
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--syllabus", default=str(DEFAULT_SYLLABUS_PATH))
    parser.add_argument("--notes", default=str(DEFAULT_NOTES_SOURCE))
    args = parser.parse_args(argv)
    paths = generate_package(
        output_dir=Path(args.out),
        paper=args.paper,
        seed=args.seed,
        model=args.model,
        ollama_url=args.ollama_url,
        dry_run=args.dry_run,
        syllabus_path=Path(args.syllabus),
        notes_source=Path(args.notes),
        progress=print,
    )
    for path in paths.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
