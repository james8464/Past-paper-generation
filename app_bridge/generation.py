from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from app_bridge.events import emit, emit_progress, progress_emitter
from app_bridge.paths import CS_PACK_ROOT, CS_ROOT, ECONOMICS_ROOT
from app_bridge.providers import hosted_client


def handle_generate(args: argparse.Namespace) -> int:
    try:
        output_dir = expand_path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        emit("error", message=f"Could not use output folder: {error}")
        return 2

    args.api_key = args.api_key.strip()
    args.model = args.model.strip()

    if not args.dry_run and not args.model:
        emit("error", message="Choose an Ollama model or run in dry-run mode.")
        return 2

    if args.provider in {"openai", "anthropic"} and not args.api_key and not args.dry_run:
        emit("error", message=f"Enter a {args.provider.title()} API key or use dry-run mode.")
        return 2

    try:
        if args.subject == "economics":
            return generate_economics(args, output_dir)
        return generate_computer_science(args, output_dir)
    except Exception as error:  # noqa: BLE001 - surfaced to UI as actionable JSON.
        if os.environ.get("PAPER_CREATOR_DEBUG") == "1":
            emit("error", message=f"{error}\n{traceback.format_exc()}")
        else:
            emit("error", message=str(error))
        return 1


def generate_economics(args: argparse.Namespace, output_dir: Path) -> int:
    if str(ECONOMICS_ROOT) not in sys.path:
        sys.path.insert(0, str(ECONOMICS_ROOT))
    from pastpapergen.cli import generate_package

    emit_progress(f"Generating Economics Paper {args.paper}", stage="start", progress=0.02)
    paths = generate_package(
        paper=args.paper,
        syllabus_path=ECONOMICS_ROOT / "data" / "syllabus_seed.json",
        output_dir=output_dir,
        seed=args.seed,
        model=args.model,
        ollama_url=args.ollama_url,
        dry_run=args.dry_run,
        progress=progress_emitter(),
        client=hosted_client(
            provider=args.provider,
            dry_run=args.dry_run,
            model=args.model,
            api_key=args.api_key,
        ),
    )
    emit_generated_files(paths)
    return 0


def generate_computer_science(args: argparse.Namespace, output_dir: Path) -> int:
    if str(CS_ROOT) not in sys.path:
        sys.path.insert(0, str(CS_ROOT))
    from cspapergen.cli import generate_package

    notes = Path(args.notes).expanduser() if args.notes else CS_PACK_ROOT / "notes"
    reference_dir = Path(args.template_reference_dir).expanduser() if args.template_reference_dir else None

    emit_progress("Generating AQA Computer Science Paper 2", stage="start", progress=0.02)
    paths = generate_package(
        output_dir=output_dir,
        seed=args.seed,
        dry_run=args.dry_run,
        model=args.model,
        ollama_url=args.ollama_url,
        syllabus_path=CS_ROOT / "data" / "syllabus_seed.json",
        notes_source=notes,
        template_overlay=not args.no_template_overlay,
        template_reference_dir=reference_dir,
        progress=progress_emitter(),
        client=hosted_client(
            provider=args.provider,
            dry_run=args.dry_run,
            model=args.model,
            api_key=args.api_key,
        ),
    )
    emit_generated_files(paths)
    return 0


def emit_generated_files(paths: dict[str, Path]) -> None:
    for role, path in paths.items():
        emit("file", role=role, path=str(path))
    emit_progress("Generation complete", stage="done", progress=1.0)
    emit("done", message="Generation complete.")


def expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()
