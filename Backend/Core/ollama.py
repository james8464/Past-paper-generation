from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from Backend.Core.events import emit, emit_progress, run_subprocess_json

OLLAMA_FALLBACK_COMMANDS = (
    "/opt/homebrew/bin/ollama",
    "/usr/local/bin/ollama",
    "/Applications/Ollama.app/Contents/Resources/ollama",
)


def ollama_command() -> str | None:
    if found := shutil.which("ollama"):
        return found
    return next((candidate for candidate in OLLAMA_FALLBACK_COMMANDS if Path(candidate).exists()), None)


def handle_ollama_status(_args: argparse.Namespace) -> int:
    command = ollama_command()
    if not command:
        emit("ollama_status", installed=False, running=False, message="Ollama is not installed.")
        return 0

    try:
        subprocess.run([command, "list"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        running = True
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        running = False

    emit(
        "ollama_status",
        installed=True,
        running=running,
        command=command,
        message="Ollama is available." if running else "Ollama is installed but not responding.",
    )
    return 0


def handle_list_models(_args: argparse.Namespace) -> int:
    command = ollama_command()
    if not command:
        emit("models", models=[], message="Ollama is not installed.")
        return 0

    try:
        result = subprocess.run([command, "list"], check=True, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        emit("error", message=f"Could not list Ollama models: {error}")
        return 1

    models = [fields[0] for line in result.stdout.splitlines()[1:] if (fields := line.split())]
    emit("models", models=models, message=f"Found {len(models)} Ollama model(s).")
    return 0


def handle_pull_model(args: argparse.Namespace) -> int:
    command = ollama_command()
    if not command:
        emit("error", message="Ollama is not installed. Install Ollama first.")
        return 1
    emit_progress(f"Pulling {args.model}", stage="pull-model", progress=0.05)
    code = run_subprocess_json([command, "pull", args.model], stage="pull-model")
    if code == 0:
        emit_progress(f"Model {args.model} is ready", stage="pull-model", progress=1.0)
        emit("done", message=f"Model {args.model} is ready.")
    else:
        emit("error", message=f"Ollama pull exited with code {code}.")
    return code
