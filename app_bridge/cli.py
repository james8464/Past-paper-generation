from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable

from app_bridge.generation import handle_generate
from app_bridge.ollama import handle_list_models, handle_ollama_status, handle_pull_model
from app_bridge.paths import REPO_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSON-lines bridge for the Past Paper Creator app.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("ollama-status")
    status.set_defaults(handler=handle_ollama_status)

    models = subparsers.add_parser("list-models")
    models.set_defaults(handler=handle_list_models)

    pull = subparsers.add_parser("pull-model")
    pull.add_argument("--model", required=True)
    pull.set_defaults(handler=handle_pull_model)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--subject", choices=["economics", "computer_science"], required=True)
    generate.add_argument("--paper", default="1")
    generate.add_argument("--output", default=str(Path.home() / "Downloads"))
    generate.add_argument("--seed", type=int, default=None)
    generate.add_argument("--model", default="qwen2.5:14b")
    generate.add_argument("--provider", choices=["ollama", "openai", "anthropic"], default="ollama")
    generate.add_argument("--api-key", default="")
    generate.add_argument("--ollama-url", default="http://localhost:11434")
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--notes", default=str(Path("/Users/james/Downloads/CS Notes")))
    generate.add_argument("--no-template-overlay", action="store_true")
    generate.add_argument("--template-reference-dir", default=None)
    generate.set_defaults(handler=handle_generate)
    return parser


def main(argv: list[str] | None = None) -> int:
    os.chdir(REPO_ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = args.handler
    return handler(args)
