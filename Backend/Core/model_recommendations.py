from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from typing import Any

from Backend.Core.paths import REPO_ROOT

MODEL_RECOMMENDATIONS_PATH = (
    REPO_ROOT / "Resources" / "ollama-model-recommendations.json"
)


@dataclass(frozen=True)
class OllamaModelTier:
    id: str
    minimum_memory_gb: float
    maximum_memory_gb: float | None
    model: str
    validated_for_full_matrix: bool


@dataclass(frozen=True)
class OllamaModelRecommendations:
    default_model: str
    other_model_warning: str
    tiers: tuple[OllamaModelTier, ...]


@lru_cache(maxsize=1)
def model_recommendations() -> OllamaModelRecommendations:
    payload = json.loads(MODEL_RECOMMENDATIONS_PATH.read_text(encoding="utf-8"))
    return parse_model_recommendations(payload)


def parse_model_recommendations(
    payload: dict[str, Any],
) -> OllamaModelRecommendations:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported Ollama model recommendation schema")
    default_model = _required_text(payload, "default_model")
    warning = _required_text(payload, "other_model_warning")
    raw_tiers = payload.get("tiers")
    if not isinstance(raw_tiers, list) or not raw_tiers:
        raise ValueError("Ollama model recommendations require at least one tier")

    tiers: list[OllamaModelTier] = []
    for raw in raw_tiers:
        if not isinstance(raw, dict):
            raise ValueError("each Ollama model tier must be an object")
        minimum = raw.get("minimum_memory_gb")
        maximum = raw.get("maximum_memory_gb")
        if not isinstance(minimum, (int, float)) or minimum < 0:
            raise ValueError("minimum_memory_gb must be non-negative")
        if maximum is not None and (
            not isinstance(maximum, (int, float)) or maximum <= minimum
        ):
            raise ValueError("maximum_memory_gb must be greater than its minimum")
        tiers.append(
            OllamaModelTier(
                id=_required_text(raw, "id"),
                minimum_memory_gb=float(minimum),
                maximum_memory_gb=float(maximum) if maximum is not None else None,
                model=_required_text(raw, "model"),
                validated_for_full_matrix=bool(
                    raw.get("validated_for_full_matrix", False)
                ),
            )
        )

    tiers.sort(key=lambda tier: tier.minimum_memory_gb)
    if tiers[0].minimum_memory_gb != 0:
        raise ValueError("Ollama model tiers must begin at zero GB")
    for left, right in pairwise(tiers):
        if left.maximum_memory_gb != right.minimum_memory_gb:
            raise ValueError("Ollama model tiers must be contiguous and non-overlapping")
    if tiers[-1].maximum_memory_gb is not None:
        raise ValueError("the final Ollama model tier must have no upper bound")
    if default_model not in {tier.model for tier in tiers}:
        raise ValueError("default_model must appear in an Ollama model tier")
    return OllamaModelRecommendations(
        default_model=default_model,
        other_model_warning=warning,
        tiers=tuple(tiers),
    )


def default_ollama_model() -> str:
    return model_recommendations().default_model


def _required_text(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()
