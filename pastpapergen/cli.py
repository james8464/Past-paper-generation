from __future__ import annotations

import argparse
import secrets
from pathlib import Path
from typing import Callable

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
    parser.add_argument("--model", default="qwen2.5:14b")
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
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading syllabus")
    syllabus = load_syllabus(syllabus_path)
    paper_id = _normalise_paper_id(paper)
    config = load_builtin_paper_config(paper_id)
    run_seed = seed if seed is not None else secrets.randbits(64)
    emit(f"Using seed {run_seed}")
    emit("Building paper blueprint")
    blueprint = build_paper_blueprint(config, syllabus, seed=run_seed)

    if not dry_run:
        emit(f"Generating questions with Ollama model {model}")
        client = OllamaClient(base_url=ollama_url, model=model)
        blueprint = generate_questions_with_ollama(client, blueprint, syllabus, progress=progress)
    else:
        emit("Using built-in draft questions")

    emit("Validating paper")
    validate_blueprint(blueprint, config, syllabus)

    stem = paper_id.replace("_", "-")
    question_paper = output_dir / f"{stem}-question-paper.pdf"
    source_booklet = output_dir / f"{stem}-source-booklet.pdf"
    mark_scheme = output_dir / f"{stem}-mark-scheme.pdf"

    emit("Rendering question paper")
    render_question_paper(blueprint, question_paper)
    emit("Rendering source booklet")
    render_source_booklet(blueprint, syllabus, source_booklet)
    emit("Rendering mark scheme")
    render_mark_scheme(blueprint, syllabus, mark_scheme)
    emit("Done")

    return {
        "question_paper": question_paper,
        "source_booklet": source_booklet,
        "mark_scheme": mark_scheme,
    }


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
        raise SystemExit("--paper must be one of: 1, 2, 3, paper_1, paper_2, paper_3") from error
