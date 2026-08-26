from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class SimulationClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


class CandidateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    band: str
    text: str
    demonstrated_mark_points: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    available_mark_points: int = Field(default=0, ge=0)


class ResponseSimulator:
    """Create diagnostic responses without exposing a drafted mark scheme."""

    def __init__(self, client: SimulationClient | None = None) -> None:
        self.client = client

    def responses(
        self,
        item: Any,
        bands: Sequence[str] = ("weak", "average", "excellent"),
    ) -> list[CandidateResponse]:
        raw_item = _mapping(item)
        safe_item = {
            key: value
            for key, value in raw_item.items()
            if key
            not in {
                "mark_scheme",
                "structured_mark_scheme",
                "marking",
                "indicative_content",
            }
        }
        if self.client is not None:
            raw = self.client.generate_json(
                "Write independent candidate responses at the requested ability "
                "bands. Do not invent source facts. Return JSON with responses, "
                "each containing band, text, demonstrated_mark_points, "
                "evidence_ids and misconceptions.\n"
                + json.dumps(
                    {"item": safe_item, "bands": list(bands)},
                    ensure_ascii=False,
                )
            )
            values = raw.get("responses")
            if not isinstance(values, list):
                raise ValueError("response simulator returned no responses")
            responses = [CandidateResponse.model_validate(value) for value in values]
            if [response.band for response in responses] != list(bands):
                raise ValueError("response simulator returned the wrong ability bands")
            return responses

        context = dict(raw_item.get("authoring_context") or {})
        points = _strings(context.get("observable_mark_points"))
        misconceptions = _strings(context.get("misconception_targets"))
        ratios = _band_ratios(bands)
        result = []
        for band, ratio in zip(bands, ratios, strict=True):
            count = (
                min(len(points), max(1, math.ceil(len(points) * ratio)))
                if points
                else 0
            )
            demonstrated = points[:count]
            errors = misconceptions[:1] if ratio < 0.5 else []
            text_parts = [
                f"Candidate response at {band} band.",
                *demonstrated,
            ]
            if errors:
                text_parts.append(f"Common error: {errors[0]}")
            result.append(
                CandidateResponse(
                    band=band,
                    text=" ".join(text_parts),
                    demonstrated_mark_points=demonstrated,
                    misconceptions=errors,
                    available_mark_points=len(points),
                )
            )
        return result


def _band_ratios(bands: Sequence[str]) -> list[float]:
    if len(bands) == 1:
        return [1.0]
    return [index / (len(bands) - 1) for index in range(len(bands))]


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        raw = value.model_dump(mode="json")
        if isinstance(raw, dict):
            return raw
    raise TypeError("response simulation requires an assessment item")


def _strings(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
