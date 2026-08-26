from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from typing import Any

from Backend.Core.paths import REPO_ROOT

PROFILE_ROOT = REPO_ROOT / "Resources" / "board-profiles"


@dataclass(frozen=True)
class BoardProfile:
    id: str
    schema_version: int
    page_size: str
    page_width_mm: float
    page_height_mm: float
    margins_mm: dict[str, float]
    typography: dict[str, Any]
    components: dict[str, Any]
    scheme_policy: str
    output_roles: tuple[str, ...]


@cache
def board_profile(identifier: str) -> BoardProfile:
    normalized = _normalise_identifier(identifier)
    path = PROFILE_ROOT / f"{normalized}.json"
    if not path.is_file():
        raise ValueError(f"unknown board profile: {identifier}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("id") != normalized or payload.get("schema_version") != 1:
        raise ValueError(f"invalid board profile: {identifier}")
    return BoardProfile(
        id=normalized,
        schema_version=1,
        page_size=str(payload["page_size"]),
        page_width_mm=float(payload["page_width_mm"]),
        page_height_mm=float(payload["page_height_mm"]),
        margins_mm={str(key): float(value) for key, value in payload["margins_mm"].items()},
        typography=dict(payload["typography"]),
        components=dict(payload["components"]),
        scheme_policy=str(payload["scheme_policy"]),
        output_roles=tuple(str(role) for role in payload["output_roles"]),
    )


def board_profile_ids() -> tuple[str, ...]:
    if not PROFILE_ROOT.is_dir():
        return ()
    return tuple(sorted(path.stem for path in PROFILE_ROOT.glob("*.json")))


def _normalise_identifier(identifier: str) -> str:
    normalized = identifier.strip().lower()
    aliases = {"edexcel": "pearson-edexcel", "edexcel-a": "pearson-edexcel"}
    normalized = aliases.get(normalized, normalized)
    if (
        not normalized
        or normalized.startswith(".")
        or "/" in normalized
        or "\\" in normalized
        or ":" in normalized
    ):
        raise ValueError(f"unknown board profile: {identifier}")
    return normalized
