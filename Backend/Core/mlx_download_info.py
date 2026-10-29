"""Estimate selected model data before download consent, without loading MLX."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from Backend.Core.events import emit
from Backend.Core.mlx_setup import (
    MLX_MODEL_PATTERNS,
    MLXSetupError,
    resolve_local_mlx_model,
)

_MAX_MODEL_BYTES = 1024**4
_REPOSITORY_ID = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}"
)


def _data_file(name: str) -> bool:
    path = Path(name)
    return (
        bool(name)
        and not path.is_absolute()
        and ".." not in path.parts
        and any(fnmatchcase(name, pattern) for pattern in MLX_MODEL_PATTERNS)
    )


def _complete_cache(path: Path) -> tuple[bool, int]:
    if not path.is_dir():
        return False, 0
    files = [
        file
        for file in path.rglob("*")
        if file.is_file() and _data_file(str(file.relative_to(path)))
    ]
    names = {str(file.relative_to(path)) for file in files}
    has_tokenizer = bool(
        names & {"tokenizer.json", "tokenizer.model", "tiktoken.model"}
    )
    has_tokenizer = has_tokenizer or {"vocab.json", "merges.txt"} <= names
    complete = (
        "config.json" in names
        and has_tokenizer
        and any(
            fnmatchcase(str(file.relative_to(path)), "model*.safetensors")
            and file.stat().st_size > 0
            for file in files
        )
    )
    index = path / "model.safetensors.index.json"
    if complete and index.exists():
        # A snapshot directory can exist before every shard has arrived.
        # Do not describe a partial download as an offline-ready cache.
        try:
            weights = json.loads(index.read_text(encoding="utf-8"))["weight_map"]
            complete = (
                isinstance(weights, dict)
                and bool(weights)
                and all(
                    isinstance(name, str)
                    and _data_file(name)
                    and name.endswith(".safetensors")
                    and name in names
                    and (path / name).stat().st_size > 0
                    for name in weights.values()
                )
            )
        except (OSError, ValueError, KeyError, TypeError):
            complete = False
    size = sum(file.stat().st_size for file in files)
    return complete and size <= _MAX_MODEL_BYTES, size


def _public_metadata(model: str) -> Any:
    from huggingface_hub import HfApi

    # Size lookup needs public metadata only, never a user's saved Hub token.
    return HfApi(token=False).model_info(repo_id=model, files_metadata=True, timeout=15)


def model_download_info(
    model: str,
    *,
    local_resolver: Callable[[str], str] = resolve_local_mlx_model,
    metadata_loader: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    model = model.strip()
    explicit_path = Path(model).expanduser()
    if model and explicit_path.is_dir():
        try:
            complete, size = _complete_cache(explicit_path)
        except OSError as error:
            raise MLXSetupError(
                "The local model folder could not be inspected. Check its location and permissions."
            ) from error
        if not complete:
            raise MLXSetupError(
                "The selected local model folder is incomplete. Choose a complete model or a model ID."
            )
        return {
            "model": model,
            "download_bytes": 0,
            "model_data_bytes": size,
            "cached": True,
            "revision": None,
        }
    if not _REPOSITORY_ID.fullmatch(model) or ".." in model or "--" in model:
        raise MLXSetupError(
            "Choose a Hugging Face model ID or a complete local model folder."
        )
    try:
        cache = Path(local_resolver(model))
        complete, size = _complete_cache(cache)
    except (MLXSetupError, OSError, ValueError):
        complete, size = False, 0
    if complete:
        return {
            "model": model,
            "download_bytes": 0,
            "model_data_bytes": size,
            "cached": True,
            "revision": cache.name
            if re.fullmatch(r"[0-9a-f]{40,64}", cache.name)
            else None,
        }
    try:
        record = (metadata_loader or _public_metadata)(model)
        revision = record.sha
        siblings = record.siblings
        if not isinstance(revision, str) or not re.fullmatch(
            r"[0-9a-f]{40,64}", revision
        ):
            raise ValueError("missing revision")
        if not isinstance(siblings, list) or not 1 <= len(siblings) <= 10_000:
            raise ValueError("missing file sizes")
        names: set[str] = set()
        total = 0
        for sibling in siblings:
            name = sibling.rfilename
            if not isinstance(name, str) or not _data_file(name):
                continue
            size = sibling.size
            if (
                name in names
                or type(size) is not int
                or not 0 <= size <= _MAX_MODEL_BYTES
            ):
                raise ValueError("invalid file size")
            if fnmatchcase(name, "model*.safetensors") and size == 0:
                raise ValueError("empty model weights")
            names.add(name)
            total += size
        if (
            "config.json" not in names
            or not any(fnmatchcase(name, "model*.safetensors") for name in names)
            or not 0 < total <= _MAX_MODEL_BYTES
        ):
            raise ValueError("incomplete model data")
    except Exception as error:
        raise MLXSetupError(
            "Could not check this model's download size. Check the model ID and internet connection, then try again. No model data was downloaded."
        ) from error
    return {
        "model": model,
        "download_bytes": total,
        "model_data_bytes": total,
        "cached": False,
        "revision": revision,
    }


def handle_mlx_download_info(args: argparse.Namespace) -> int:
    try:
        info = model_download_info(args.model)
    except MLXSetupError as error:
        emit("error", code="mlx_download_info_failed", message=str(error))
        return 1
    emit("mlx_download_info", **info)
    return 0
