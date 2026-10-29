from __future__ import annotations

import json
import sys
from argparse import Namespace
from types import ModuleType

import pytest

from Backend.Core.mlx_setup import (
    MLXSetupError,
    handle_setup_mlx,
    load_mlx_model,
    resolve_local_mlx_model,
)

SHA = "a" * 40


def fake_runtime(monkeypatch):
    loads = []
    module = ModuleType("mlx_lm")
    module.load = lambda path, **kwargs: loads.append((path, kwargs))
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    return loads


def test_remote_setup_pins_approved_revision_and_later_local_resolution(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    loads = fake_runtime(monkeypatch)
    snapshot = tmp_path / SHA
    snapshot.mkdir()
    calls = []

    def resolve(**kwargs):
        calls.append(kwargs)
        return str(snapshot)

    load_mlx_model("owner/model", revision=SHA, snapshot_resolver=resolve)
    assert len(calls) == 1
    assert calls[0]["revision"] == SHA and calls[0]["local_files_only"] is False
    assert loads[0][1]["tokenizer_config"] == {
        "trust_remote_code": False,
        "local_files_only": True,
    }
    assert resolve_local_mlx_model("owner/model", snapshot_resolver=resolve) == str(
        snapshot
    )
    assert calls[-1]["revision"] == SHA and calls[-1]["local_files_only"] is True


def test_cached_consent_never_enables_network_or_resolves_main_after_load(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    fake_runtime(monkeypatch)
    calls = []
    load_mlx_model(
        "owner/model",
        revision=SHA,
        local_only=True,
        snapshot_resolver=lambda **kwargs: calls.append(kwargs) or str(tmp_path),
    )
    assert len(calls) == 1 and calls[0]["local_files_only"] is True
    assert calls[0]["revision"] == SHA


def test_missing_approved_cache_requests_recheck_without_network_fallback(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    fake_runtime(monkeypatch)
    calls = []

    def missing(**kwargs):
        calls.append(kwargs)
        raise FileNotFoundError("deleted cached snapshot")

    with pytest.raises(MLXSetupError, match=r"[Cc]heck|[Aa]pprove"):
        load_mlx_model(
            "owner/model", revision=SHA, local_only=True, snapshot_resolver=missing
        )
    assert len(calls) == 1 and calls[0]["local_files_only"] is True


@pytest.mark.parametrize(
    "revision", ["main", "../escape", "A" * 40, "a" * 39, "a" * 65, True, 0]
)
def test_untrusted_revision_refuses_before_snapshot_or_model_loading(
    monkeypatch, revision
):
    fake_runtime(monkeypatch)
    with pytest.raises(MLXSetupError, match="revision"):
        load_mlx_model(
            "owner/model",
            revision=revision,
            snapshot_resolver=lambda **_: pytest.fail(
                "invalid revision reached resolver"
            ),
        )


def test_failed_model_load_never_records_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    module = ModuleType("mlx_lm")

    def fail(*_args, **_kwargs):
        raise ValueError("cannot load")

    module.load = fail
    monkeypatch.setitem(sys.modules, "mlx_lm", module)
    with pytest.raises(MLXSetupError):
        load_mlx_model(
            "owner/model", revision=SHA, snapshot_resolver=lambda **_: str(tmp_path)
        )
    assert not list((tmp_path / "hub").rglob("*.json"))


def test_cli_passes_bound_setup_options_without_changing_legacy_loaders(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "Backend.Core.mlx_setup.validate_mlx_setup_environment", lambda: None
    )
    monkeypatch.setattr("Backend.Core.mlx_setup.mlx_runtime_available", lambda: True)
    monkeypatch.setattr(
        "Backend.Core.mlx_setup.load_mlx_model",
        lambda model, **kwargs: calls.append((model, kwargs)),
    )
    assert (
        handle_setup_mlx(Namespace(model="owner/model", revision=SHA, local_only=True))
        == 0
    )
    assert calls == [("owner/model", {"revision": SHA, "local_only": True})]


def test_cli_parser_accepts_optional_binding_flags():
    from Backend.Core.cli import build_parser

    args = build_parser().parse_args(
        ["setup-mlx", "--model", "owner/model", "--revision", SHA, "--local-only"]
    )
    assert args.revision == SHA and args.local_only is True


@pytest.mark.parametrize(
    "mutation", ["oversized", "wrong-model", "bad-revision", "extra-path", "symlink"]
)
def test_corrupt_approval_never_falls_back_to_main_or_an_external_path(
    monkeypatch, tmp_path, mutation
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    fake_runtime(monkeypatch)
    load_mlx_model(
        "owner/model", revision=SHA, snapshot_resolver=lambda **_: str(tmp_path)
    )
    record = next((tmp_path / "hub" / "keldin-model-approvals").glob("*.json"))
    raw = json.loads(record.read_text())
    assert raw == {"schema_version": 1, "model": "owner/model", "revision": SHA}
    if mutation == "oversized":
        record.write_text("x" * 1025)
    elif mutation == "symlink":
        other = tmp_path / "external.json"
        other.write_text(json.dumps(raw))
        record.unlink()
        record.symlink_to(other)
    else:
        if mutation == "wrong-model":
            raw["model"] = "other/model"
        elif mutation == "bad-revision":
            raw["revision"] = "../../outside"
        else:
            raw["path"] = "/outside/model"
        record.write_text(json.dumps(raw))
    with pytest.raises(MLXSetupError):
        resolve_local_mlx_model(
            "owner/model",
            snapshot_resolver=lambda **_: pytest.fail(
                "invalid approval reached snapshot resolver"
            ),
        )


def test_missing_approved_snapshot_has_one_pinned_offline_attempt(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    fake_runtime(monkeypatch)
    load_mlx_model(
        "owner/model", revision=SHA, snapshot_resolver=lambda **_: str(tmp_path)
    )
    calls = []

    def missing(**kwargs):
        calls.append(kwargs)
        raise FileNotFoundError("approved snapshot removed")

    with pytest.raises(MLXSetupError):
        resolve_local_mlx_model("owner/model", snapshot_resolver=missing)
    assert len(calls) == 1 and calls[0]["revision"] == SHA
    assert calls[0]["local_files_only"] is True


def test_failed_new_setup_preserves_previous_approval_and_cleans_staging(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    fake_runtime(monkeypatch)
    load_mlx_model(
        "owner/model", revision=SHA, snapshot_resolver=lambda **_: str(tmp_path)
    )
    folder = tmp_path / "hub" / "keldin-model-approvals"
    record = next(folder.glob("*.json"))
    original = record.read_bytes()

    def refuse_replace(*_):
        raise OSError("fixture cannot replace approval")

    monkeypatch.setattr("Backend.Core.mlx_setup.os.replace", refuse_replace)
    with pytest.raises(MLXSetupError):
        load_mlx_model(
            "owner/model",
            revision="b" * 40,
            snapshot_resolver=lambda **_: str(tmp_path),
        )
    assert record.read_bytes() == original
    assert list(folder.iterdir()) == [record]


def test_pinned_setup_rejects_path_like_model_id_before_any_resolver_call(monkeypatch):
    fake_runtime(monkeypatch)
    with pytest.raises(MLXSetupError, match="model ID"):
        load_mlx_model(
            "../outside",
            revision=SHA,
            snapshot_resolver=lambda **_: pytest.fail("invalid ID reached resolver"),
        )


def test_explicit_local_folder_can_prepare_offline_without_approval_pointer(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hub"))
    loads = fake_runtime(monkeypatch)
    load_mlx_model(
        str(tmp_path),
        local_only=True,
        snapshot_resolver=lambda **_: pytest.fail("local folder reached network"),
    )
    assert loads[0][0] == str(tmp_path)
    assert not (tmp_path / "hub").exists()
