"""Cached local preparation must not require space for a new model download."""

from argparse import Namespace
from functools import partial

import pytest

from Backend.Core import mlx_setup as subject

GIB = 1024**3
REVISION = "a" * 40


@pytest.fixture
def setup_environment(monkeypatch):
    monkeypatch.setattr(
        subject,
        "validate_mlx_setup_environment",
        partial(
            subject.validate_mlx_setup_environment,
            machine="arm64",
            python_version=(3, 12),
            free_bytes=2 * GIB,
        ),
    )
    monkeypatch.setattr(subject.sys, "frozen", True, raising=False)
    monkeypatch.setattr(subject, "mlx_runtime_available", lambda: True)
    monkeypatch.setattr(
        subject,
        "install_mlx_runtime",
        lambda: pytest.fail("unexpected runtime install"),
    )
    calls = []
    monkeypatch.setattr(
        subject,
        "load_mlx_model",
        lambda model, **kwargs: calls.append((model, kwargs)),
    )
    return calls


def arguments(*, local_only=True):
    return Namespace(model="owner/model", revision=REVISION, local_only=local_only)


def test_cached_ready_runtime_can_prepare_at_two_gib_free(setup_environment, capsys):
    assert subject.handle_setup_mlx(arguments()) == 0
    assert setup_environment == [
        ("owner/model", {"revision": REVISION, "local_only": True})
    ]
    assert '"type": "done"' in capsys.readouterr().out


@pytest.mark.parametrize("runtime_ready", [False, True])
def test_download_keeps_storage_floor(
    monkeypatch, setup_environment, capsys, runtime_ready
):
    monkeypatch.setattr(subject, "mlx_runtime_available", lambda: runtime_ready)
    assert subject.handle_setup_mlx(arguments(local_only=False)) == 1
    assert not setup_environment
    assert "8 GB" in capsys.readouterr().out


def test_missing_runtime_keeps_storage_floor_for_local_only(
    monkeypatch, setup_environment, capsys
):
    monkeypatch.setattr(subject, "mlx_runtime_available", lambda: False)
    assert subject.handle_setup_mlx(arguments()) == 1
    assert not setup_environment
    assert "8 GB" in capsys.readouterr().out


@pytest.mark.parametrize(
    "environment", [{"machine": "x86_64"}, {"python_version": (3, 14)}]
)
def test_cached_preparation_still_checks_architecture_and_python(
    monkeypatch, setup_environment, environment
):
    monkeypatch.setattr(
        subject,
        "validate_mlx_setup_environment",
        partial(subject.validate_mlx_setup_environment, **environment),
    )
    assert subject.handle_setup_mlx(arguments()) == 1
    assert not setup_environment


def test_missing_cached_snapshot_is_not_hidden_by_download_headroom(
    monkeypatch, setup_environment, capsys
):
    def missing(*_args, **_kwargs):
        raise subject.MLXModelSetupRequired("Owned missing cached snapshot")

    monkeypatch.setattr(subject, "load_mlx_model", missing)
    assert subject.handle_setup_mlx(arguments()) == 1
    assert "Owned missing cached snapshot" in capsys.readouterr().out


def test_python_version_error_uses_current_app_name():
    with pytest.raises(subject.MLXSetupError, match="Keldin"):
        subject.validate_mlx_setup_environment(
            python_version=(3, 14), machine="arm64", free_bytes=20 * GIB
        )
