from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import tomllib
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from Backend.Core.events import BACKEND_VERSION, PROTOCOL_VERSION, emit, emit_progress, progress_emitter
from Backend.Core.generator_registry import GeneratorCapability, generator_capability
from Backend.Core.layout_conformance import conform_generated_documents
from Backend.Core.paths import REPO_ROOT, absolute_user_path
from Backend.Core.pdf_validation import validate_pdf_for_release
from Backend.Core.providers import hosted_client


class GenerationCancelled(Exception):
    pass


def _cancel_generation(_signal_number: int, _frame: Any) -> None:
    raise GenerationCancelled


def handle_generate(args: argparse.Namespace) -> int:
    try:
        output_dir = absolute_user_path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=output_dir):
            pass
    except OSError as error:
        emit("error", message=f"Could not use output folder: {error}")
        return 2

    args.api_key = args.api_key.strip()
    args.model = args.model.strip()
    capability = generator_capability(args.subject)
    validation_error = _validate_request(args, capability)
    if validation_error:
        emit("error", message=validation_error, code="invalid_request")
        return 2

    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".papercreator-{args.subject}-{args.paper}-",
            dir=output_dir,
        )
    )
    previous_signal_handler = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, _cancel_generation)
    try:
        if not capability.uses_ai:
            emit_progress(
                "Using the built-in constrained generator",
                stage="provider",
                progress=0.04,
            )
        generated = _invoke_plugin(capability, args, staging_dir)
        published = finalize_generated_documents(
            args=args,
            capability=capability,
            staging_dir=staging_dir,
            output_dir=output_dir,
            paths=generated,
        )
        emit_generated_files(published)
        return 0
    except GenerationCancelled:
        emit_progress("Creation cancelled", stage="cancel", progress=0.0)
        return 130
    except Exception as error:  # noqa: BLE001 - surfaced as actionable JSON.
        if os.environ.get("PAPER_CREATOR_DEBUG") == "1":
            emit("error", message=f"{error}\n{traceback.format_exc()}", code="generation_failed")
        else:
            emit("error", message=str(error), code="generation_failed")
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous_signal_handler)
        shutil.rmtree(staging_dir, ignore_errors=True)


def _validate_request(
    args: argparse.Namespace,
    capability: GeneratorCapability,
) -> str | None:
    if args.paper not in capability.papers:
        return f"{args.subject} does not support paper {args.paper}."
    if capability.uses_ai and args.provider not in capability.supported_providers:
        return f"{args.provider} is not supported by {capability.id}."
    if capability.uses_ai and not args.dry_run and not args.model:
        return "Choose a model or run in preview mode."
    if (
        capability.uses_ai
        and args.provider in {"openai", "anthropic"}
        and not args.api_key
        and not args.dry_run
    ):
        return f"Enter a {args.provider.title()} API key or use preview mode."
    return None


def _invoke_plugin(
    capability: GeneratorCapability,
    args: argparse.Namespace,
    output_dir: Path,
) -> dict[str, Path]:
    generator_root = REPO_ROOT / "Resources" / capability.python_path
    if str(generator_root) not in sys.path:
        sys.path.insert(0, str(generator_root))
    entry_point = _load_entry_point(capability.entry_point)
    parameters = inspect.signature(entry_point).parameters
    candidate_arguments: dict[str, Any] = {
        "paper": args.paper,
        "syllabus_path": REPO_ROOT / "Resources" / capability.syllabus_path,
        "output_dir": output_dir,
        "seed": args.seed,
        "model": args.model,
        "ollama_url": args.ollama_url,
        "dry_run": args.dry_run,
        "progress": progress_emitter(),
    }
    if args.notes:
        candidate_arguments["notes_source"] = Path(args.notes).expanduser()
    if capability.uses_ai:
        candidate_arguments["client"] = hosted_client(
            provider=args.provider,
            dry_run=args.dry_run,
            model=args.model,
            api_key=args.api_key,
        )
    keyword_arguments = {
        name: value
        for name, value in candidate_arguments.items()
        if name in parameters
    }
    missing = [
        name
        for name, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind
        in {inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
        and name not in keyword_arguments
    ]
    if missing:
        raise RuntimeError(
            f"{capability.id} entry point requires unsupported arguments: {missing}"
        )

    emit_progress(
        f"Creating {capability.id} paper {args.paper}",
        stage="start",
        progress=0.02,
    )
    result = entry_point(**keyword_arguments)
    if not isinstance(result, dict):
        raise RuntimeError(f"{capability.id} entry point did not return document paths")
    return {str(role): Path(path) for role, path in result.items()}


def _load_entry_point(value: str) -> Callable[..., dict[str, Path]]:
    module_name, function_name = value.split(":", maxsplit=1)
    function = getattr(importlib.import_module(module_name), function_name, None)
    if not callable(function):
        raise RuntimeError(f"generator entry point is not callable: {value}")
    return function


def finalize_generated_documents(
    *,
    args: argparse.Namespace,
    capability: GeneratorCapability,
    staging_dir: Path,
    output_dir: Path,
    paths: dict[str, Path],
) -> dict[str, Path]:
    expected = set(capability.outputs_for(args.paper))
    actual = set(paths)
    if actual != expected:
        raise RuntimeError(
            f"{args.subject} paper {args.paper} produced roles {sorted(actual)}; "
            f"expected {sorted(expected)}"
        )
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(
            "generator reported files that do not exist: " + ", ".join(missing)
        )
    outside_staging = [
        str(path)
        for path in paths.values()
        if path.parent.absolute() != staging_dir.absolute()
    ]
    if outside_staging:
        raise RuntimeError(
            "generator wrote outside its transaction directory: "
            + ", ".join(outside_staging)
        )

    conform_generated_documents(args.subject, args.paper, paths)
    pdf_validation = {
        role: validate_pdf_for_release(path, subject=args.subject)
        for role, path in paths.items()
        if path.suffix.casefold() == ".pdf"
    }
    manifest_path = _write_package_manifest(
        args=args,
        capability=capability,
        staging_dir=staging_dir,
        paths=paths,
        pdf_validation=pdf_validation,
    )
    published = {
        role: _atomic_publish(path, output_dir / path.name)
        for role, path in paths.items()
    }
    published["package_manifest"] = _atomic_publish(
        manifest_path,
        output_dir / manifest_path.name,
    )
    return published


def _write_package_manifest(
    *,
    args: argparse.Namespace,
    capability: GeneratorCapability,
    staging_dir: Path,
    paths: dict[str, Path],
    pdf_validation: dict[str, dict[str, Any]],
) -> Path:
    repository_commit = _repository_commit()
    gate_results = capability.evidence_by_paper[args.paper]
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job_id": os.environ.get("PAPER_CREATOR_JOB_ID", ""),
        "protocol_version": PROTOCOL_VERSION,
        "app": {
            "version": os.environ.get("PAPER_CREATOR_APP_VERSION"),
            "build": os.environ.get("PAPER_CREATOR_APP_BUILD"),
        },
        "backend": {
            "version": BACKEND_VERSION,
            "repository_commit": repository_commit,
        },
        "generator": {
            "id": capability.id,
            "entry_point": capability.entry_point,
            "content_mode": capability.content_mode,
            "version": _generator_version(capability),
            "repository_commit": repository_commit,
        },
        "request": {
            "subject": args.subject,
            "paper": args.paper,
            "seed": args.seed,
            "preview_mode": bool(args.dry_run),
            "provider": args.provider if capability.uses_ai else None,
            "model": args.model if capability.uses_ai else None,
        },
        "evidence": {
            "gates": gate_results,
            "visual_calibration": gate_results.get("visual", False),
            "difficulty_independently_verified": gate_results.get(
                "difficulty", False
            ),
            "warning": (
                "Intended demand and document structure are validated; "
                "difficulty is not established by student-response calibration."
            ),
        },
        "inputs": {
            "syllabus": capability.syllabus_path,
            "syllabus_sha256": _sha256(
                REPO_ROOT / "Resources" / capability.syllabus_path
            ),
            "generator_registry_sha256": _sha256(
                REPO_ROOT / "Resources" / "generator-registry.json"
            ),
            "layout_profile_sha256": _sha256(
                REPO_ROOT / "Resources" / "layout-master-runtime.json"
            ),
            "assessment_schema": "Backend.Core.exam_blueprints:v2",
            "validator": "Backend.Core.pdf_validation:v1",
        },
        "outputs": {
            role: {
                "filename": path.name,
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
                "pdf_validation": pdf_validation.get(role),
            }
            for role, path in paths.items()
        },
    }
    manifest_path = staging_dir / (
        f"{args.subject.replace('_', '-')}-paper-{args.paper}-package.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _atomic_publish(source: Path, destination: Path) -> Path:
    os.replace(source, destination)
    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _repository_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def _generator_version(capability: GeneratorCapability) -> str | None:
    pyproject = (
        REPO_ROOT
        / "Resources"
        / capability.python_path
        / "pyproject.toml"
    )
    try:
        value = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return str(value["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return None


def emit_generated_files(paths: dict[str, Path]) -> None:
    for role, path in paths.items():
        emit("file", role=role, path=str(path))
    emit_progress("Creation complete", stage="done", progress=1.0)
    emit("done", message="Creation complete.")
