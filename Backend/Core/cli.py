from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

from Backend.Core.benchmark import handle_benchmark
from Backend.Core.events import BACKEND_VERSION, emit
from Backend.Core.generation import handle_generate
from Backend.Core.generator_registry import generator_capabilities, generator_subjects
from Backend.Core.mlx_setup import handle_mlx_status, handle_setup_mlx
from Backend.Core.model_recommendations import default_ollama_model
from Backend.Core.ollama import (
    handle_list_models,
    handle_ollama_status,
    handle_pull_model,
)
from Backend.Core.paths import REPO_ROOT

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"
DEFAULT_MODEL = os.environ.get("PAPER_CREATOR_DEFAULT_MODEL", default_ollama_model())
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_BENCHMARK_DURATION_SECONDS = 30.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSON-lines bridge for Paper creator.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("ollama-status")
    status.set_defaults(handler=handle_ollama_status)

    bundle_check = subparsers.add_parser(
        "bundle-check",
        help=argparse.SUPPRESS,
    )
    bundle_check.set_defaults(handler=handle_bundle_check)

    models = subparsers.add_parser("list-models")
    models.set_defaults(handler=handle_list_models)

    pull = subparsers.add_parser("pull-model")
    pull.add_argument("--model", required=True)
    pull.set_defaults(handler=handle_pull_model)

    mlx_setup = subparsers.add_parser("setup-mlx")
    mlx_setup.add_argument("--model", required=True)
    mlx_setup.set_defaults(handler=handle_setup_mlx)

    mlx_status = subparsers.add_parser("mlx-status")
    mlx_status.set_defaults(handler=handle_mlx_status)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--duration", type=float, default=DEFAULT_BENCHMARK_DURATION_SECONDS)
    benchmark.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    benchmark.set_defaults(handler=handle_benchmark)

    generate = subparsers.add_parser("generate")
    generate.add_argument(
        "--subject",
        choices=generator_subjects(),
        required=True,
    )
    generate.add_argument("--paper", default="1")
    generate.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    generate.add_argument("--seed", type=int, default=None)
    generate.add_argument("--model", default=DEFAULT_MODEL)
    generate.add_argument("--provider", choices=["ollama", "openai", "anthropic", "apple"], default="ollama")
    generate.add_argument("--api-key", default=os.environ.get("PAPER_CREATOR_API_KEY", ""))
    generate.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--notes", default="")
    generate.set_defaults(handler=handle_generate)

    assessment = subparsers.add_parser("generate-assessment", help="Generate a national-framework practice assessment")
    assessment.add_argument("--assessment", required=True)
    assessment.add_argument("--reference-index", type=Path, required=True)
    assessment.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    assessment.add_argument("--seed", type=int, required=True)
    assessment.add_argument("--model", default=DEFAULT_MODEL)
    assessment.add_argument("--provider", choices=["ollama"], default="ollama")
    assessment.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    assessment.add_argument("--large-print", action="store_true")
    assessment.add_argument("--allow-remote", action="store_true")
    assessment.set_defaults(handler=handle_framework_generate)
    references = subparsers.add_parser("prepare-french-references", help="Download the registered official French reference PDFs")
    references.add_argument("--output", type=Path, required=True)
    references.set_defaults(handler=handle_french_references)
    return parser


def handle_framework_generate(args: argparse.Namespace) -> int:
    from Backend.Core.france.runtime import handle_generate_assessment

    return handle_generate_assessment(args)


def handle_french_references(args: argparse.Namespace) -> int:
    from Backend.Core.france.corpus import ingest
    try:
        report = ingest(REPO_ROOT / "Resources/france/nsi/source-register.json", args.output)
        if report["failures"]:
            emit("error", code="french_sources_incomplete", message="Téléchargement incomplet : " + "; ".join(item["error"] for item in report["failures"]))
            return 1
        emit("done", message="Sources initiales préparées. L'archive complète reste en cours de vérification.")
        return 0
    except Exception as error:
        emit("error", message=str(error), code="french_sources_failed")
        return 1


def handle_bundle_check(_args: argparse.Namespace) -> int:
    """Fail fast when a packaged backend is missing a dynamic generator."""
    loaded: list[str] = []
    errors: list[str] = []
    for capability in generator_capabilities().values():
        generator_root = REPO_ROOT / "Resources" / capability.python_path
        root_text = str(generator_root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        module_name, function_name = capability.entry_point.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
            if not callable(getattr(module, function_name, None)):
                raise TypeError(f"missing callable {function_name}")
            syllabus = REPO_ROOT / "Resources" / capability.syllabus_path
            if not syllabus.is_file():
                raise FileNotFoundError(f"missing syllabus {capability.syllabus_path}")
            loaded.append(capability.backend_subject)
        except Exception as error:
            errors.append(f"{capability.backend_subject}: {error}")
    emit(
        "bundle_status",
        healthy=not errors,
        generators=loaded,
        errors=errors,
        message=(
            f"Loaded {len(loaded)} generator families."
            if not errors
            else "Generator bundle validation failed."
        ),
    )
    return 0 if not errors else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    emit(
        "hello",
        backend_version=BACKEND_VERSION,
        capabilities=["cancel", "eta", "manifest", "transactional-output"],
        message="Backend ready",
    )
    handler: Callable[[argparse.Namespace], int] = args.handler
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
