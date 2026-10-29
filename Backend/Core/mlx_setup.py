# Prepare local MLX models and report setup failures the app can act on.

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Backend.Core.events import emit, emit_progress

MLX_PACKAGE_SPECS = (
    "mlx-lm==0.30.2",
    "mlx==0.29.3",
    "mlx-metal==0.29.3",
    "outlines==1.3.3",
    "llguidance==1.9.1",
)
# Only model data may be downloaded. Architecture and tokenizer implementation
# must come from the packaged runtime, never from a model repository's Python.
MLX_MODEL_PATTERNS = [
    "*.json",
    "model*.safetensors",
    "tokenizer.model",
    "*.tiktoken",
    "tiktoken.model",
    "*.txt",
    "*.jsonl",
    "*.jinja",
]
MINIMUM_MLX_FREE_BYTES = 8 * 1024**3
SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX = (3, 13)
_APPROVED_REVISION = re.compile(r"[0-9a-f]{40,64}\Z")
_MODEL_ID = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z"
)


# A recoverable Apple MLX setup failure suitable for the app UI.
class MLXSetupError(RuntimeError):
    pass


# Apple MLX setup was cancelled by the user.
class MLXSetupCancelled(MLXSetupError):
    pass


# The selected model no longer has a complete local snapshot.
class MLXModelSetupRequired(MLXSetupError):
    pass


@dataclass(frozen=True)
class MLXSetupResult:
    installed_runtime: bool
    model_ready: bool


# Fail before download when the local MLX environment cannot succeed.
def validate_mlx_setup_environment(
    *,
    python_version: tuple[int, int] | None = None,
    machine: str | None = None,
    free_bytes: int | None = None,
) -> None:

    version = python_version or (sys.version_info.major, sys.version_info.minor)
    architecture = (machine or platform.machine()).lower()
    if architecture not in {"arm64", "aarch64"}:
        raise MLXSetupError(
            "Apple MLX requires a Mac with Apple silicon. Choose Ollama or a "
            "hosted provider on this Mac."
        )
    if not SUPPORTED_PYTHON_MIN <= version <= SUPPORTED_PYTHON_MAX:
        raise MLXSetupError(
            "Apple MLX setup requires Python 3.10 through 3.13 in Paper "
            "Creator’s managed environment. Reinstall or update the app, then try again."
        )
    available = free_bytes if free_bytes is not None else _available_cache_bytes()
    if available < MINIMUM_MLX_FREE_BYTES:
        available_gb = max(0, int(available / 1024**3))
        raise MLXSetupError(
            "Apple MLX setup needs at least 8 GB of free storage. "
            f"This Mac currently has about {available_gb} GB available in the model location."
        )


def _available_cache_bytes() -> int:
    cache = Path(os.environ.get("HF_HOME", "~/.cache/huggingface")).expanduser()
    probe = cache
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return shutil.disk_usage(probe).free


# Exercise the packaged runtime instead of merely checking module metadata.
def mlx_runtime_available() -> bool:

    try:
        import mlx.core as mx
        from llguidance import grammar_from
        from mlx_lm import generate, load
        from outlines import from_mlxlm

        expected_versions = {
            spec.partition("==")[0]: spec.partition("==")[2]
            for spec in MLX_PACKAGE_SPECS
        }
        for package, expected in expected_versions.items():
            if importlib.metadata.version(package) != expected:
                return False
        if not all(
            callable(function)
            for function in (load, generate, from_mlxlm, grammar_from)
        ):
            return False
        value = mx.array([1])
        mx.eval(value)
        return int(value[0].item()) == 1
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        importlib.metadata.PackageNotFoundError,
    ):
        return False


# Only permit package installation inside the repository-owned virtualenv.
def is_managed_development_environment() -> bool:

    prefix = Path(sys.prefix).resolve()
    executable = Path(sys.executable).absolute()
    return (
        sys.prefix != sys.base_prefix
        and prefix.name == ".venv"
        and (prefix / "pyvenv.cfg").is_file()
        and executable.is_relative_to(prefix)
    )


def _stop_installer(process: Any) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (AttributeError, OSError, ProcessLookupError):
        process.terminate()
    try:
        process.wait(timeout=10)
    except (subprocess.TimeoutExpired, TypeError):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (AttributeError, OSError, ProcessLookupError):
            process.kill()
        process.wait()


def install_mlx_runtime(
    *,
    process_factory: Callable[..., Any] = subprocess.Popen,
) -> bool:
    emit_progress(
        "Installing Apple MLX support in Keldin’s managed environment…",
        stage="mlx-runtime",
        progress=0.15,
    )
    process: Any | None = None
    previous_handler = signal.getsignal(signal.SIGTERM)

    def cancel_install(_signal_number: int, _frame: Any) -> None:
        if process is not None:
            _stop_installer(process)
        raise MLXSetupCancelled("Apple MLX setup was cancelled.")

    signal.signal(signal.SIGTERM, cancel_install)
    try:
        process = process_factory(
            [sys.executable, "-m", "pip", "install", *MLX_PACKAGE_SPECS],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return_code = process.wait()
    except MLXSetupCancelled:
        raise
    except OSError:
        return False
    finally:
        if process is not None and process.poll() is None:
            _stop_installer(process)
        signal.signal(signal.SIGTERM, previous_handler)

    importlib.invalidate_caches()
    return return_code == 0 and mlx_runtime_available()


def _validate_setup_binding(revision: str | None, local_only: bool) -> None:
    if revision is not None and (
        not isinstance(revision, str) or not _APPROVED_REVISION.fullmatch(revision)
    ):
        raise MLXSetupError(
            "The approved model revision is invalid. Check the download size again."
        )
    if type(local_only) is not bool:
        raise MLXSetupError("The local-only setup policy must be a Boolean.")


def _approval_path(model: str) -> Path:
    cache = Path(os.environ.get("HF_HOME", "~/.cache/huggingface")).expanduser()
    name = hashlib.sha256(model.encode("utf-8")).hexdigest() + ".json"
    return cache / "keldin-model-approvals" / name


def _approved_revision(model: str) -> str | None:
    path = _approval_path(model)
    try:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError("linked approval record")
        if not path.exists():
            return None
        with path.open("rb") as stream:
            data = stream.read(1025)
        if len(data) > 1024:
            raise ValueError("oversized approval record")
        raw = json.loads(data)
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema_version", "model", "revision"}
            or type(raw["schema_version"]) is not int
            or raw["schema_version"] != 1
            or raw["model"] != model
        ):
            raise ValueError("invalid approval record")
        revision = raw["revision"]
        _validate_setup_binding(revision, True)
        if revision is None:
            raise ValueError("missing approved revision")
        return str(revision)
    except (OSError, ValueError, MLXSetupError) as error:
        raise MLXModelSetupRequired(
            "The saved model approval could not be verified. Check the download size and approve setup again."
        ) from error


def _save_approved_revision(model: str, revision: str) -> None:
    _validate_setup_binding(revision, True)
    if not _MODEL_ID.fullmatch(model) or ".." in model or "--" in model:
        raise MLXSetupError("The approved model ID is invalid.")
    path = _approval_path(model)
    if path.is_symlink() or path.parent.is_symlink():
        raise MLXSetupError("The model approval location is invalid.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".approval-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                {"schema_version": 1, "model": model, "revision": revision}, stream
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


# Return a complete local model path without allowing a network download.
def resolve_local_mlx_model(
    model: str,
    *,
    snapshot_resolver: Callable[..., str] | None = None,
) -> str:

    local_path = Path(model).expanduser()
    if local_path.exists():
        return str(local_path.resolve())

    try:
        if snapshot_resolver is None:
            from huggingface_hub import snapshot_download

            snapshot_resolver = snapshot_download
        approved = _approved_revision(model)
        binding = {"revision": approved} if approved is not None else {}
        return str(
            snapshot_resolver(
                repo_id=model,
                local_files_only=True,
                allow_patterns=MLX_MODEL_PATTERNS,
                **binding,
            )
        )
    except Exception as error:
        raise MLXModelSetupRequired(
            "The selected Apple MLX model is no longer stored on this Mac. "
            "Approve setup again to restore it."
        ) from error


def load_mlx_model(
    model: str,
    *,
    snapshot_resolver: Callable[..., str] | None = None,
    revision: str | None = None,
    local_only: bool = False,
) -> None:
    _validate_setup_binding(revision, local_only)
    if revision is not None and (
        not _MODEL_ID.fullmatch(model) or ".." in model or "--" in model
    ):
        raise MLXSetupError("The approved model ID is invalid.")
    emit_progress(
        "Preparing the selected model. The first download may take several minutes…",
        stage="mlx-model",
        progress=0.55,
    )
    try:
        from mlx_lm import load

        path = Path(model).expanduser()
        if path.exists() and revision is not None:
            raise MLXSetupError(
                "A local model folder cannot be bound to a repository revision. Check its setup again."
            )
        if not path.exists():
            if snapshot_resolver is None:
                from huggingface_hub import snapshot_download

                snapshot_resolver = snapshot_download
            if local_only and revision is None:
                path = Path(
                    resolve_local_mlx_model(model, snapshot_resolver=snapshot_resolver)
                )
            else:
                binding = {"revision": revision} if revision is not None else {}
                path = Path(
                    snapshot_resolver(
                        repo_id=model,
                        local_files_only=local_only,
                        allow_patterns=MLX_MODEL_PATTERNS,
                        **binding,
                    )
                )
        load(
            str(path.resolve()),
            tokenizer_config={
                "trust_remote_code": False,
                "local_files_only": True,
            },
        )
        if revision is not None:
            _save_approved_revision(model, revision)
    except MLXModelSetupRequired:
        raise
    except Exception as error:
        if local_only:
            raise MLXModelSetupRequired(
                "The approved local model could not be prepared. Check its download size and approve setup again. No model data was downloaded."
            ) from error
        raise MLXSetupError(
            "The Apple MLX model could not be prepared. Check your internet "
            "connection and available storage, then try Setup Again."
        ) from error


# Install a development runtime if needed, then prepare the chosen model.
def ensure_mlx_ready(
    model: str,
    *,
    runtime_available: Callable[[], bool],
    install_runtime: Callable[[], bool],
    load_model: Callable[[str], None],
    frozen: bool,
    managed_environment: Callable[[], bool] = is_managed_development_environment,
) -> MLXSetupResult:

    model = model.strip()
    if not model:
        raise MLXSetupError("Choose an Apple MLX model in Settings, then try again.")

    installed_runtime = False
    if not runtime_available():
        if frozen:
            raise MLXSetupError(
                "Apple MLX support is missing from this copy of Keldin. "
                "Please reinstall or update the app, then try again."
            )
        if not managed_environment():
            raise MLXSetupError(
                "Keldin’s managed development environment is incomplete. "
                "Recreate the project environment, then try Setup Again."
            )
        if not install_runtime():
            raise MLXSetupError(
                "Apple MLX support could not be installed. Check your internet "
                "connection and available storage, then try Setup Again."
            )
        installed_runtime = True

    load_model(model)
    return MLXSetupResult(installed_runtime=installed_runtime, model_ready=True)


def handle_setup_mlx(args: argparse.Namespace) -> int:
    emit_progress("Checking Apple MLX support…", stage="mlx-check", progress=0.05)
    try:
        revision = getattr(args, "revision", None)
        local_only = getattr(args, "local_only", False)
        _validate_setup_binding(revision, local_only)
        validate_mlx_setup_environment()

        def loader(model: str) -> None:
            if revision is None and not local_only:
                load_mlx_model(model)
            else:
                load_mlx_model(model, revision=revision, local_only=local_only)

        ensure_mlx_ready(
            args.model,
            runtime_available=mlx_runtime_available,
            install_runtime=install_mlx_runtime,
            load_model=loader,
            frozen=bool(getattr(sys, "frozen", False)),
        )
    except MLXSetupCancelled:
        emit_progress("Apple MLX setup cancelled", stage="cancel", progress=0.0)
        return 130
    except MLXSetupError as error:
        emit("error", message=str(error))
        return 1

    emit("done", message="Apple MLX is ready.")
    return 0


def handle_mlx_status(_args: argparse.Namespace) -> int:
    installed = mlx_runtime_available()
    emit(
        "mlx_status",
        runtime_installed=installed,
        message=(
            "Apple MLX support is available."
            if installed
            else "Apple MLX setup is required."
        ),
    )
    return 0 if installed else 1
