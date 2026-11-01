# Find the local Ollama service and report model status or download progress.

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from Backend.Core.events import emit, emit_progress, run_subprocess_json
from Backend.Core.france.network import open_ollama_request, validate_endpoint

OLLAMA_FALLBACK_COMMANDS = (
    "/opt/homebrew/bin/ollama",
    "/usr/local/bin/ollama",
    "/Applications/Ollama.app/Contents/Resources/ollama",
)
OLLAMA_API = "http://127.0.0.1:11434"


def api_models(
    url: str = OLLAMA_API, *, allow_remote: bool = False
) -> list[str] | None:
    validate_endpoint(url, allow_remote=allow_remote)
    try:
        with open_ollama_request(
            urllib.request.Request(f"{url.rstrip('/')}/api/tags"), timeout=5
        ) as response:
            content = response.read(4 * 1024 * 1024 + 1)
            if len(content) > 4 * 1024 * 1024:
                return None
            payload = json.loads(content.decode("utf-8"))
    except (OSError, urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return None
    if any(
        not isinstance(model, dict)
        or not isinstance(model.get("name"), str)
        or not model["name"].strip()
        for model in payload["models"]
    ):
        return None
    return [model["name"] for model in payload["models"]]


def ollama_command() -> str | None:
    if found := shutil.which("ollama"):
        return found
    return next(
        (
            candidate
            for candidate in OLLAMA_FALLBACK_COMMANDS
            if Path(candidate).exists()
        ),
        None,
    )


def _default_endpoint(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
        and parsed.port == 11434
    )


def handle_ollama_status(args: argparse.Namespace) -> int:
    endpoint = getattr(args, "ollama_url", OLLAMA_API)
    models = api_models(endpoint, allow_remote=getattr(args, "allow_remote", False))
    if models is not None:
        emit(
            "ollama_status",
            installed=True,
            running=True,
            message="Ollama is available.",
        )
        return 0

    if not _default_endpoint(endpoint):
        emit(
            "ollama_status",
            installed=True,
            running=False,
            message="The configured Ollama server is not responding.",
        )
        return 0

    command = ollama_command()
    if not command:
        emit(
            "ollama_status",
            installed=False,
            running=False,
            message="Ollama is not installed.",
        )
        return 0

    try:
        subprocess.run(
            [command, "list"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        running = True
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        running = False

    emit(
        "ollama_status",
        installed=True,
        running=running,
        command=command,
        message="Ollama is available."
        if running
        else "Ollama is installed but not responding.",
    )
    return 0


def handle_list_models(args: argparse.Namespace) -> int:
    endpoint = getattr(args, "ollama_url", OLLAMA_API)
    api_result = api_models(endpoint, allow_remote=getattr(args, "allow_remote", False))
    if api_result is not None:
        emit(
            "models",
            models=api_result,
            message=f"Found {len(api_result)} Ollama model(s).",
        )
        return 0

    if not _default_endpoint(endpoint):
        emit(
            "models",
            models=[],
            message="No models received from the configured Ollama server.",
        )
        emit(
            "error", message="Could not list models from the configured Ollama server."
        )
        return 1

    command = ollama_command()
    if not command:
        emit("models", models=[], message="Ollama is not installed.")
        return 0

    try:
        result = subprocess.run(
            [command, "list"], check=True, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        emit("error", message=f"Could not list Ollama models: {error}")
        return 1

    models = [
        fields[0] for line in result.stdout.splitlines()[1:] if (fields := line.split())
    ]
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
