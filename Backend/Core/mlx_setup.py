from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import os
import platform
import shutil
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Backend.Core.events import emit, emit_progress

MLX_PACKAGE_SPECS = (
    "mlx-lm==0.30.2",
    "mlx==0.29.3",
    "mlx-metal==0.29.3",
)
MINIMUM_MLX_FREE_BYTES = 8 * 1024**3
SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX = (3, 13)


class MLXSetupError(RuntimeError):
    """A recoverable Apple MLX setup failure suitable for the app UI."""


class MLXSetupCancelled(MLXSetupError):
    """Apple MLX setup was cancelled by the user."""


class MLXModelSetupRequired(MLXSetupError):
    """The selected model no longer has a complete local snapshot."""


@dataclass(frozen=True)
class MLXSetupResult:
    installed_runtime: bool
    model_ready: bool


def validate_mlx_setup_environment(
    *,
    python_version: tuple[int, int] | None = None,
    machine: str | None = None,
    free_bytes: int | None = None,
) -> None:
    """Fail before download when the local MLX environment cannot succeed."""

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


def mlx_runtime_available() -> bool:
    """Exercise the packaged runtime instead of merely checking module metadata."""

    try:
        import mlx.core as mx
        from mlx_lm import generate, load

        expected_versions = {
            spec.partition("==")[0]: spec.partition("==")[2]
            for spec in MLX_PACKAGE_SPECS
        }
        for package, expected in expected_versions.items():
            if importlib.metadata.version(package) != expected:
                return False
        if not callable(load) or not callable(generate):
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


def is_managed_development_environment() -> bool:
    """Only permit package installation inside the repository-owned virtualenv."""

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
        "Installing Apple MLX support in Paper Creator’s managed environment…",
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


def resolve_local_mlx_model(
    model: str,
    *,
    snapshot_resolver: Callable[..., str] | None = None,
) -> str:
    """Return a complete local model path without allowing a network download."""

    local_path = Path(model).expanduser()
    if local_path.exists():
        return str(local_path.resolve())

    try:
        if snapshot_resolver is None:
            from huggingface_hub import snapshot_download

            snapshot_resolver = snapshot_download
        return str(snapshot_resolver(repo_id=model, local_files_only=True))
    except Exception as error:
        raise MLXModelSetupRequired(
            "The selected Apple MLX model is no longer stored on this Mac. "
            "Approve setup again to restore it."
        ) from error


def load_mlx_model(model: str) -> None:
    emit_progress(
        "Preparing the selected model. The first download may take several minutes…",
        stage="mlx-model",
        progress=0.55,
    )
    try:
        from mlx_lm import load

        load(model)
        resolve_local_mlx_model(model)
    except MLXModelSetupRequired:
        raise
    except Exception as error:
        raise MLXSetupError(
            "The Apple MLX model could not be prepared. Check your internet "
            "connection and available storage, then try Setup Again."
        ) from error


def ensure_mlx_ready(
    model: str,
    *,
    runtime_available: Callable[[], bool],
    install_runtime: Callable[[], bool],
    load_model: Callable[[str], None],
    frozen: bool,
    managed_environment: Callable[[], bool] = is_managed_development_environment,
) -> MLXSetupResult:
    """Install a development runtime if needed, then prepare the chosen model."""

    model = model.strip()
    if not model:
        raise MLXSetupError("Choose an Apple MLX model in Settings, then try again.")

    installed_runtime = False
    if not runtime_available():
        if frozen:
            raise MLXSetupError(
                "Apple MLX support is missing from this copy of Paper Creator. "
                "Please reinstall or update the app, then try again."
            )
        if not managed_environment():
            raise MLXSetupError(
                "Paper Creator’s managed development environment is incomplete. "
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
        validate_mlx_setup_environment()
        ensure_mlx_ready(
            args.model,
            runtime_available=mlx_runtime_available,
            install_runtime=install_mlx_runtime,
            load_model=load_mlx_model,
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
