from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from cspapergen.generator import build_paper2_blueprint
from cspapergen.notes import DEFAULT_NOTES_SOURCE, cache_notes
from cspapergen.ollama_client import OllamaClient, improve_questions_with_ollama
from cspapergen.render_pdf import render_mark_scheme, render_question_paper
from cspapergen.syllabus import DEFAULT_SYLLABUS_PATH, load_syllabus
from cspapergen.validation import validate_blueprint


def default_output_dir() -> Path:
    return Path.home() / "Downloads"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an unofficial AQA A-Level Computer Science Paper 2 practice paper.")
    parser.add_argument("--out", default=str(default_output_dir()))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model", default="qwen2.5:14b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--syllabus", default=str(DEFAULT_SYLLABUS_PATH))
    parser.add_argument("--notes", default=str(DEFAULT_NOTES_SOURCE))
    args = parser.parse_args(argv)

    paths = generate_package(
        output_dir=Path(args.out),
        seed=args.seed,
        model=args.model,
        ollama_url=args.ollama_url,
        dry_run=args.dry_run,
        syllabus_path=Path(args.syllabus),
        notes_source=Path(args.notes),
        progress=print,
    )
    print(paths["question_paper"])
    print(paths["mark_scheme"])
    return 0


def generate_package(
    *,
    output_dir: Path,
    seed: int | None,
    dry_run: bool,
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    syllabus_path: Path = DEFAULT_SYLLABUS_PATH,
    notes_source: Path = DEFAULT_NOTES_SOURCE,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Caching notes")
    cache_notes(notes_source)
    emit("Loading syllabus")
    syllabus = load_syllabus(syllabus_path)
    emit(f"Using seed {seed if seed is not None else 'random'}")
    emit("Building Paper 2 blueprint")
    blueprint = build_paper2_blueprint(syllabus, seed=seed)
    emit(f"Using seed {blueprint.seed}")

    if dry_run:
        emit("Using built-in draft questions")
    else:
        emit(f"Generating questions with model {model}")
        question_client = client or OllamaClient(base_url=ollama_url, model=model)
        blueprint = improve_questions_with_ollama(question_client, blueprint, syllabus, progress=progress)

    emit("Validating paper")
    validate_blueprint(blueprint, syllabus)

    question_paper = output_dir / "cs-paper-2-question-paper.pdf"
    mark_scheme = output_dir / "cs-paper-2-mark-scheme.pdf"
    emit("Rendering question paper")
    render_question_paper(blueprint, question_paper)
    emit("Rendering mark scheme")
    render_mark_scheme(blueprint, mark_scheme)
    emit("Done")
    return {"question_paper": question_paper, "mark_scheme": mark_scheme}
