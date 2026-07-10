from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable

from Backend.Core.benchmark import handle_benchmark
from Backend.Core.generation import handle_generate
from Backend.Core.ollama import handle_list_models, handle_ollama_status, handle_pull_model
from Backend.Core.paths import REPO_ROOT

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"
DEFAULT_MODEL = os.environ.get("PAPER_CREATOR_DEFAULT_MODEL", "qwen2.5:14b")
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_BENCHMARK_DURATION_SECONDS = 30.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSON-lines bridge for the ExamForge app.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("ollama-status")
    status.set_defaults(handler=handle_ollama_status)

    models = subparsers.add_parser("list-models")
    models.set_defaults(handler=handle_list_models)

    pull = subparsers.add_parser("pull-model")
    pull.add_argument("--model", required=True)
    pull.set_defaults(handler=handle_pull_model)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--duration", type=float, default=DEFAULT_BENCHMARK_DURATION_SECONDS)
    benchmark.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    benchmark.set_defaults(handler=handle_benchmark)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--subject", choices=["economics", "computer_science"], required=True)
    generate.add_argument("--paper", default="1")
    generate.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    generate.add_argument("--seed", type=int, default=None)
    generate.add_argument("--model", default=DEFAULT_MODEL)
    generate.add_argument("--provider", choices=["ollama", "openai", "anthropic", "apple"], default="ollama")
    generate.add_argument("--api-key", default="")
    generate.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--notes", default="")
    generate.set_defaults(handler=handle_generate)
    return parser


def main(argv: list[str] | None = None) -> int:
    os.chdir(REPO_ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = args.handler
    return handler(args)
