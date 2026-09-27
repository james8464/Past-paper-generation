from __future__ import annotations

import json
import os
import signal
from argparse import Namespace
from functools import partial
from pathlib import Path

import pytest

from Backend.Core.cli import build_parser
from Backend.Core.mlx_setup import (
    MLXModelSetupRequired,
    MLXSetupCancelled,
    MLXSetupError,
    ensure_mlx_ready,
    handle_mlx_status,
    handle_setup_mlx,
    install_mlx_runtime,
    resolve_local_mlx_model,
    validate_mlx_setup_environment,
)


@pytest.fixture
def supported_mlx_environment(monkeypatch):
    # Handler behavior must not depend on the CI host's CPU, Python or disk.
    # Keep the real validation, with explicit supported environment inputs.
    monkeypatch.setattr(
        "Backend.Core.mlx_setup.validate_mlx_setup_environment",
        partial(validate_mlx_setup_environment, python_version=(3, 12),
                machine="arm64", free_bytes=20 * 1024**3),
    )


def test_missing_direct_runtime_is_installed_before_model_is_prepared() -> None:
    actions: list[str] = []

    result = ensure_mlx_ready(
        "mlx-community/test-model",
        runtime_available=lambda: False,
        install_runtime=lambda: actions.append("install") or True,
        load_model=lambda model: actions.append(f"load:{model}"),
        frozen=False,
        managed_environment=lambda: True,
    )

    assert actions == ["install", "load:mlx-community/test-model"]
    assert result.installed_runtime is True
    assert result.model_ready is True


def test_frozen_build_never_downloads_executable_runtime() -> None:
    install_attempted = False

    def install_runtime() -> bool:
        nonlocal install_attempted
        install_attempted = True
        return True

    with pytest.raises(MLXSetupError, match="reinstall"):
        ensure_mlx_ready(
            "mlx-community/test-model",
            runtime_available=lambda: False,
            install_runtime=install_runtime,
            load_model=lambda _model: None,
            frozen=True,
        )

    assert install_attempted is False


def test_failed_runtime_install_does_not_start_model_download() -> None:
    model_loaded = False

    def load_model(_model: str) -> None:
        nonlocal model_loaded
        model_loaded = True

    with pytest.raises(MLXSetupError, match="could not be installed"):
        ensure_mlx_ready(
            "mlx-community/test-model",
            runtime_available=lambda: False,
            install_runtime=lambda: False,
            load_model=load_model,
            frozen=False,
            managed_environment=lambda: True,
        )

    assert model_loaded is False


def test_empty_model_is_rejected_before_any_setup_work() -> None:
    with pytest.raises(MLXSetupError, match="Choose an Apple MLX model"):
        ensure_mlx_ready(
            "  ",
            runtime_available=lambda: True,
            install_runtime=lambda: True,
            load_model=lambda _model: None,
            frozen=False,
        )


def test_missing_runtime_never_modifies_an_unmanaged_python() -> None:
    install_attempted = False

    def install_runtime() -> bool:
        nonlocal install_attempted
        install_attempted = True
        return True

    with pytest.raises(MLXSetupError, match="managed development environment"):
        ensure_mlx_ready(
            "mlx-community/test-model",
            runtime_available=lambda: False,
            install_runtime=install_runtime,
            load_model=lambda _model: None,
            frozen=False,
            managed_environment=lambda: False,
        )

    assert install_attempted is False


def test_local_model_resolution_never_enables_network_download(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()

    resolved = resolve_local_mlx_model(
        "mlx-community/test-model",
        snapshot_resolver=lambda **kwargs: calls.append(kwargs) or str(snapshot),
    )

    assert resolved == str(snapshot)
    assert calls == [{"repo_id": "mlx-community/test-model", "local_files_only": True}]


def test_missing_local_model_requests_setup_again() -> None:
    def missing_snapshot(**_kwargs) -> str:
        raise FileNotFoundError

    with pytest.raises(MLXModelSetupRequired, match="Approve setup again"):
        resolve_local_mlx_model(
            "mlx-community/test-model",
            snapshot_resolver=missing_snapshot,
        )


def test_cli_accepts_guided_mlx_setup_command() -> None:
    args = build_parser().parse_args(
        ["setup-mlx", "--model", "mlx-community/test-model"]
    )

    assert args.model == "mlx-community/test-model"
    assert args.handler is handle_setup_mlx


def test_setup_handler_reports_success_without_terminal_instructions(
    monkeypatch,
    capsys,
    supported_mlx_environment,
) -> None:
    monkeypatch.setattr("Backend.Core.mlx_setup.mlx_runtime_available", lambda: True)
    monkeypatch.setattr("Backend.Core.mlx_setup.load_mlx_model", lambda _model: None)

    code = handle_setup_mlx(Namespace(model="mlx-community/test-model"))

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0
    assert events[-1]["type"] == "done"
    assert events[-1]["message"] == "Apple MLX is ready."
    assert all("pip" not in event.get("message", "").lower() for event in events)


def test_setup_handler_reports_plain_recovery_error(monkeypatch, capsys, supported_mlx_environment) -> None:
    def fail_to_load(_model: str) -> None:
        raise MLXSetupError("The model could not be prepared. Try Setup Again.")

    monkeypatch.setattr("Backend.Core.mlx_setup.mlx_runtime_available", lambda: True)
    monkeypatch.setattr("Backend.Core.mlx_setup.load_mlx_model", fail_to_load)

    code = handle_setup_mlx(Namespace(model="mlx-community/test-model"))

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 1
    assert events[-1]["type"] == "error"
    assert events[-1]["message"] == "The model could not be prepared. Try Setup Again."


def test_mlx_status_reports_whether_runtime_is_packaged(monkeypatch, capsys) -> None:
    monkeypatch.setattr("Backend.Core.mlx_setup.mlx_runtime_available", lambda: False)

    code = handle_mlx_status(Namespace())

    event = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code == 1
    assert event["type"] == "mlx_status"
    assert event["runtime_installed"] is False


def test_runtime_installer_keeps_package_manager_output_out_of_the_ui(capsys) -> None:
    class FailedProcess:
        pid = 123

        def wait(self, **_kwargs) -> int:
            return 1

        def poll(self) -> int:
            return 1

    def process_factory(*_args, **_kwargs) -> FailedProcess:
        return FailedProcess()

    assert install_mlx_runtime(process_factory=process_factory) is False
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [event["message"] for event in events] == [
        "Installing Apple MLX support in Paper Creator’s managed environment…"
    ]


def test_runtime_installer_terminates_its_child_when_setup_is_cancelled() -> None:
    previous_handler = signal.getsignal(signal.SIGTERM)

    class RunningProcess:
        pid = 999_999_999
        return_code: int | None = None
        terminated = False

        def wait(self, timeout=None) -> int:
            if timeout is not None:
                return self.return_code or 143
            os.kill(os.getpid(), signal.SIGTERM)
            return 143

        def poll(self) -> int | None:
            return self.return_code

        def terminate(self) -> None:
            self.terminated = True
            self.return_code = 143

        def kill(self) -> None:
            self.return_code = 137

    process = RunningProcess()

    with pytest.raises(MLXSetupCancelled):
        install_mlx_runtime(process_factory=lambda *_args, **_kwargs: process)

    assert process.terminated is True
    assert signal.getsignal(signal.SIGTERM) == previous_handler


def test_mlx_setup_rejects_unsupported_python_with_plain_diagnostic() -> None:
    with pytest.raises(MLXSetupError, match=r"Python 3.10 through 3.13"):
        validate_mlx_setup_environment(
            python_version=(3, 14),
            machine="arm64",
            free_bytes=20 * 1024**3,
        )


def test_mlx_setup_rejects_insufficient_storage_before_installing() -> None:
    with pytest.raises(MLXSetupError, match="at least 8 GB"):
        validate_mlx_setup_environment(
            python_version=(3, 12),
            machine="arm64",
            free_bytes=2 * 1024**3,
        )


def test_mlx_setup_rejects_non_apple_silicon_without_package_manager_copy() -> None:
    with pytest.raises(MLXSetupError, match="Apple silicon"):
        validate_mlx_setup_environment(
            python_version=(3, 12),
            machine="x86_64",
            free_bytes=20 * 1024**3,
        )
