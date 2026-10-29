from __future__ import annotations

import json
from argparse import Namespace
from types import SimpleNamespace

import pytest

from Backend.Core.mlx_download_info import handle_mlx_download_info, model_download_info
from Backend.Core.mlx_setup import MLXSetupError


def no_cache(_model):
    raise MLXSetupError("not cached")


def metadata(**changes):
    return SimpleNamespace(
        sha="a" * 40,
        siblings=[
            SimpleNamespace(rfilename="config.json", size=100),
            SimpleNamespace(rfilename="model.safetensors", size=300),
            SimpleNamespace(rfilename="tokenizer.json", size=50),
            SimpleNamespace(rfilename="remote.py", size=999),
            SimpleNamespace(rfilename="README.md", size=500),
        ],
        **changes,
    )


def test_only_allowed_data_contributes_to_size():
    calls = []
    result = model_download_info(
        "mlx-community/example",
        local_resolver=no_cache,
        metadata_loader=lambda model: calls.append(model) or metadata(),
    )
    assert calls == ["mlx-community/example"]
    assert result == {
        "model": "mlx-community/example",
        "download_bytes": 450,
        "model_data_bytes": 450,
        "cached": False,
        "revision": "a" * 40,
    }


def test_complete_cache_works_offline_without_metadata_or_model_import(tmp_path):
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "model.safetensors").write_bytes(b"123")
    (tmp_path / "tokenizer.json").write_text("{}")
    result = model_download_info(
        "mlx-community/example",
        local_resolver=lambda _: str(tmp_path),
        metadata_loader=lambda _: pytest.fail("complete cache must remain offline"),
    )
    assert result["cached"] is True and result["download_bytes"] == 0
    assert result["model_data_bytes"] == 7


@pytest.mark.parametrize("size", [None, True, -1, 0, 1.5, "300", 2**63])
def test_missing_or_unsafe_weight_size_refuses(size):
    record = metadata()
    record.siblings[1].size = size
    with pytest.raises(MLXSetupError):
        model_download_info(
            "mlx-community/example",
            local_resolver=no_cache,
            metadata_loader=lambda _: record,
        )


@pytest.mark.parametrize(
    "model", ["", "../private", "/missing/model", "https://host/repo", "a/b/c"]
)
def test_invalid_ids_never_contact_metadata(model):
    with pytest.raises(MLXSetupError):
        model_download_info(
            model,
            local_resolver=no_cache,
            metadata_loader=lambda _: pytest.fail("invalid model reached network"),
        )


def test_network_failure_is_actionable_and_does_not_prepare_model():
    def unavailable(_):
        raise OSError("offline")

    with pytest.raises(MLXSetupError, match="download size"):
        model_download_info(
            "mlx-community/example",
            local_resolver=no_cache,
            metadata_loader=unavailable,
        )


def test_handler_emits_typed_info_without_inference(monkeypatch, capsys):
    monkeypatch.setattr(
        "Backend.Core.mlx_download_info.model_download_info",
        lambda _: {
            "model": "mlx-community/example",
            "download_bytes": 450,
            "model_data_bytes": 450,
            "cached": False,
            "revision": "a" * 40,
        },
    )
    assert handle_mlx_download_info(Namespace(model="mlx-community/example")) == 0
    event = json.loads(capsys.readouterr().out)
    assert event["type"] == "mlx_download_info" and event["download_bytes"] == 450
