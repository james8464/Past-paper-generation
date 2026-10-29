from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tools.live_generation_matrix import (
    MatrixJob,
    _model_digest,
    _request_identity,
    _resumable_result,
    _sha256,
)


def test_mlx_identity_binds_weight_and_tokenizer_bytes_without_path_leakage(
    tmp_path, monkeypatch
):
    root = tmp_path / "private-model"
    root.mkdir()
    (root / "config.json").write_text('{"model_type":"llama"}')
    weight = root / "model.safetensors"
    weight.write_bytes(b"first")
    tokenizer = root / "tokenizer.json"
    tokenizer.write_text("{}")
    monkeypatch.setattr(
        "Backend.Core.mlx_setup.resolve_local_mlx_model", lambda _: str(root)
    )
    first = _model_digest("apple", "cached/model", "http://unused")
    assert isinstance(first, str) and len(first) == 64
    before = weight.stat()
    weight.write_bytes(b"other")
    os.utime(weight, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert _model_digest("apple", "cached/model", "http://unused") != first
    weight.write_bytes(b"first")
    assert _model_digest("apple", "cached/model", "http://unused") == first
    tokenizer.write_text('{"changed":true}')
    assert _model_digest("apple", "cached/model", "http://unused") != first


def test_missing_or_unprepared_mlx_model_has_no_resumable_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "Backend.Core.mlx_setup.resolve_local_mlx_model", lambda _: str(tmp_path)
    )
    assert _model_digest("apple", "missing", "http://unused") is None


@pytest.mark.parametrize(
    "provider,flag",
    [
        ("ollama", "KELDIN_PARALLEL_LOCAL_REVIEWS"),
        ("apple", "KELDIN_PARALLEL_MLX_GENERATION"),
    ],
)
def test_request_identity_binds_local_scheduling_mode(provider, flag, monkeypatch):
    job = MatrixJob(0, "test", "test", "1", "Test", "Fixture", ("assessment_package",))

    def current():
        return _request_identity(
            job,
            seed=1,
            model="fixture",
            provider=provider,
            ollama_url="http://unused",
            dry_run=False,
            command_prefix=["backend"],
            model_digest="a" * 64,
            runtime_sha256="b" * 64,
        )

    monkeypatch.setenv(flag, "0")
    serial = current()
    monkeypatch.setenv(flag, "1")
    parallel = current()
    assert serial != parallel
    assert serial["local_generation_workers"] == 1
    assert parallel["local_generation_workers"] == 2


@pytest.mark.parametrize("pin,expected", [(None, False), ("a" * 64, True)])
def test_mlx_result_requires_model_pin_before_resume(tmp_path, pin, expected):
    identity = {
        "provider": "apple",
        "model_digest": pin,
        "expected_roles": ["assessment_package"],
    }
    files = {}
    for role in ["assessment_package", "package_manifest"]:
        path = tmp_path / f"{role}.json"
        path.write_text(json.dumps({"reference_demand": {"passed": True}}))
        files[role] = str(path)
    events = tmp_path / "events.jsonl"
    events.write_text('{"type":"done"}\n')
    result = {
        "passed": True,
        "request_identity": identity,
        "files": files,
        "artifact_sha256": {role: _sha256(Path(path)) for role, path in files.items()},
        "events_sha256": _sha256(events),
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(result))
    assert (_resumable_result(path, request_identity=identity) is not None) is expected
