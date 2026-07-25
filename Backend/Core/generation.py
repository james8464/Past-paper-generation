from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from Backend.Core.events import emit, emit_progress, progress_emitter
from Backend.Core.paths import (
    ACCOUNTING_ROOT,
    AQA_ECONOMICS_ROOT,
    BUSINESS_ROOT,
    CS_PACK_ROOT,
    CS_ROOT,
    ECONOMICS_ROOT,
    OCR_ECONOMICS_ROOT,
    OCR_CS_ROOT,
)
from Backend.Core.providers import hosted_client


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
        if args.subject == "economics_aqa":
            return generate_aqa_economics(args, output_dir)
        if args.subject == "economics_ocr":
            return generate_ocr_economics(args, output_dir)
        if args.subject == "computer_science_ocr":
            return generate_ocr_computer_science(args, output_dir)
        if args.subject == "business_aqa":
            return generate_aqa_business(args, output_dir)
        if args.subject == "accounting_aqa":
            return generate_aqa_accounting(args, output_dir)
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

    emit_progress(f"Generating AQA Computer Science Paper {args.paper}", stage="start", progress=0.02)
    paths = generate_package(
        output_dir=output_dir,
        paper=args.paper,
        seed=args.seed,
        dry_run=args.dry_run,
        model=args.model,
        ollama_url=args.ollama_url,
        syllabus_path=CS_ROOT / "data" / "syllabus_seed.json",
        notes_source=notes,
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


def generate_aqa_economics(args: argparse.Namespace, output_dir: Path) -> int:
    if str(AQA_ECONOMICS_ROOT) not in sys.path:
        sys.path.insert(0, str(AQA_ECONOMICS_ROOT))
    from aqaecongen.cli import generate_package

    emit_progress(f"Generating AQA Economics Paper {args.paper}", stage="start", progress=0.02)
    paths = generate_package(
        paper=args.paper,
        syllabus_path=AQA_ECONOMICS_ROOT / "data" / "syllabus.json",
        output_dir=output_dir,
        seed=args.seed,
        progress=progress_emitter(),
    )
    emit_generated_files(paths)
    return 0


def generate_ocr_economics(args: argparse.Namespace, output_dir: Path) -> int:
    if str(OCR_ECONOMICS_ROOT) not in sys.path:
        sys.path.insert(0, str(OCR_ECONOMICS_ROOT))
    from ocregen.cli import generate_package

    emit_progress(f"Generating OCR Economics Paper {args.paper}", stage="start", progress=0.02)
    paths = generate_package(
        paper=args.paper,
        syllabus_path=OCR_ECONOMICS_ROOT / "data" / "syllabus.json",
        output_dir=output_dir,
        seed=args.seed,
        progress=progress_emitter(),
    )
    emit_generated_files(paths)
    return 0


def generate_ocr_computer_science(
    args: argparse.Namespace, output_dir: Path
) -> int:
    if str(OCR_CS_ROOT) not in sys.path:
        sys.path.insert(0, str(OCR_CS_ROOT))
    from ocrcsgen.cli import generate_package

    emit_progress(
        f"Generating OCR Computer Science Paper {args.paper}",
        stage="start",
        progress=0.02,
    )
    paths = generate_package(
        paper=args.paper,
        syllabus_path=OCR_CS_ROOT / "data" / "syllabus.json",
        output_dir=output_dir,
        seed=args.seed,
        progress=progress_emitter(),
    )
    emit_generated_files(paths)
    return 0


def generate_aqa_business(args: argparse.Namespace, output_dir: Path) -> int:
    if str(BUSINESS_ROOT) not in sys.path:
        sys.path.insert(0, str(BUSINESS_ROOT))
    from aqabizgen.cli import generate_package

    emit_progress(
        f"Generating AQA Business Paper {args.paper}",
        stage="start",
        progress=0.02,
    )
    paths = generate_package(
        paper=args.paper,
        syllabus_path=BUSINESS_ROOT / "data" / "syllabus.json",
        output_dir=output_dir,
        seed=args.seed,
        progress=progress_emitter(),
    )
    emit_generated_files(paths)
    return 0


def generate_aqa_accounting(args: argparse.Namespace, output_dir: Path) -> int:
    if str(ACCOUNTING_ROOT) not in sys.path:
        sys.path.insert(0, str(ACCOUNTING_ROOT))
    from aqaaccountgen.cli import generate_package

    emit_progress(
        f"Generating AQA Accounting Paper {args.paper}",
        stage="start",
        progress=0.02,
    )
    paths = generate_package(
        paper=args.paper,
        syllabus_path=ACCOUNTING_ROOT / "data" / "syllabus.json",
        output_dir=output_dir,
        seed=args.seed,
        progress=progress_emitter(),
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
