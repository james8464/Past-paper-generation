from __future__ import annotations

import argparse
import secrets
from collections.abc import Callable
from pathlib import Path

from Backend.Core.family_adapter import (
    ArtifactSpec,
    BuildResult,
    FamilyAdapter,
    run_family_adapter,
)
from Backend.Core.model_recommendations import default_ollama_model
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import OllamaClient, generate_questions_with_ollama
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    render_mark_scheme,
    render_question_paper,
    render_source_booklet,
)
from pastpapergen.syllabus import load_syllabus
from pastpapergen.validation import validate_blueprint


def _load_rule(paper: str):
    return load_builtin_paper_config(_normalise_paper_id(paper))


def _build(config, syllabus, seed: int | None) -> BuildResult:
    return BuildResult(
        build_paper_blueprint(config, syllabus, seed=seed),
        {"seed": seed},
    )


def _improve(blueprint, syllabus, _config, client, progress, checkpoint_store):
    return generate_questions_with_ollama(
        client,
        blueprint,
        syllabus,
        progress=progress,
        checkpoint_store=checkpoint_store,
    )


def _artifacts(blueprint, _context, syllabus, _paper: str) -> tuple[ArtifactSpec, ...]:
    stem = blueprint.paper_id.replace("_", "-")
    return (
        ArtifactSpec(
            "question_paper",
            f"{stem}-question-paper.pdf",
            lambda path: render_question_paper(blueprint, path),
            "Rendering question paper",
        ),
        ArtifactSpec(
            "source_booklet",
            f"{stem}-source-booklet.pdf",
            lambda path: render_source_booklet(blueprint, syllabus, path),
            "Rendering source booklet",
        ),
        ArtifactSpec(
            "mark_scheme",
            f"{stem}-mark-scheme.pdf",
            lambda path: render_mark_scheme(blueprint, syllabus, path),
            "Rendering mark scheme",
        ),
    )


ADAPTER = FamilyAdapter(
    id="pearson-edexcel/economics-a-2015",
    subject_label="Pearson Edexcel A-level Economics A",
    backend_subject="economics",
    load_message="Loading syllabus",
    build_message="Building paper blueprint",
    prompt_version="edexcel-economics-v1",
    load_syllabus=load_syllabus,
    load_rule=_load_rule,
    build=_build,
    artifacts=_artifacts,
    stem=lambda config, _paper: config.id.replace("_", "-"),
    preview_message="Using built-in draft questions",
    validation_message="Validating paper",
    resolve_seed=lambda seed: seed if seed is not None else secrets.randbits(64),
    seed_message=lambda seed: f"Using seed {seed}",
    validate=lambda blueprint, config, syllabus: validate_blueprint(
        blueprint, config, syllabus
    ),
    improve=_improve,
    client_factory=lambda model, url: OllamaClient(base_url=url, model=model),
    checkpoint_identity=lambda blueprint, _config, _paper: {
        "paper_id": blueprint.paper_id,
        "seed": blueprint.seed,
        "blueprint": blueprint.model_dump(mode="json"),
    },
)


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    model: str,
    ollama_url: str,
    dry_run: bool,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Path]:
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
        description="Generate an unofficial Edexcel A-Level Economics A practice paper."
    )
    parser.add_argument("--paper", required=True)
    parser.add_argument("--syllabus", default="data/syllabus_seed.json")
    parser.add_argument("--out", default=str(default_output_dir()))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model", default=default_ollama_model())
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    paths = generate_package(
        paper=args.paper,
        syllabus_path=Path(args.syllabus),
        output_dir=Path(args.out),
        seed=args.seed,
        model=args.model,
        ollama_url=args.ollama_url,
        dry_run=args.dry_run,
    )
    print(paths["question_paper"])
    print(paths["source_booklet"])
    print(paths["mark_scheme"])
    return 0


def _normalise_paper_id(value: str) -> str:
    mapping = {
        "1": "paper_1",
        "2": "paper_2",
        "3": "paper_3",
        "paper1": "paper_1",
        "paper2": "paper_2",
        "paper3": "paper_3",
        "paper_1": "paper_1",
        "paper_2": "paper_2",
        "paper_3": "paper_3",
    }
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    try:
        return mapping[key]
    except KeyError as error:
        raise SystemExit(
            "--paper must be one of: 1, 2, 3, paper_1, paper_2, paper_3"
        ) from error


if __name__ == "__main__":
    raise SystemExit(main())
