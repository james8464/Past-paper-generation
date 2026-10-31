"""Per-paper request admission limits for the sequential French authoring path."""

from __future__ import annotations

import time
from typing import Any

from Backend.Core.generation_requests import GenerationRequest, request_json
from Backend.Core.json_client import JSONGenerationClient

MAX_REQUESTS = 24
MAX_RESERVED_OUTPUT_TOKENS = 589824
MAX_ELAPSED_SECONDS = 30 * 60


class GenerationLimitError(RuntimeError):
    """Stop without treating a resource limit as a rejected exercise."""


class FrenchGenerationBudget:
    """Count dispatches before calling a provider; never retry a failure here.

    Callers check elapsed time after recording a returned object, so a late
    result is retained for diagnosis rather than silently lost. This cannot
    interrupt an in-flight provider or guarantee that remote billing stops.
    """

    def __init__(self, client: JSONGenerationClient) -> None:
        self._client = client
        self._started = time.monotonic()
        self._requests = 0
        self._completed = 0
        self._reserved = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def check(self) -> None:
        if time.monotonic() - self._started >= MAX_ELAPSED_SECONDS:
            raise GenerationLimitError(
                "La création du sujet a dépassé 30 minutes; aucun autre appel au modèle ne sera lancé."
            )

    def generate_request(self, request: GenerationRequest) -> dict[str, object]:
        if not isinstance(request, GenerationRequest):
            raise TypeError("A typed French generation request is required.")
        self.check()
        if (
            self._requests >= MAX_REQUESTS
            or self._reserved + request.output_budget > MAX_RESERVED_OUTPUT_TOKENS
        ):
            raise GenerationLimitError(
                "La limite d'appels au modèle pour ce sujet est atteinte; création interrompue."
            )
        self._requests += 1
        self._reserved += request.output_budget
        result = request_json(self._client, request)
        self._completed += 1
        return result

    def snapshot(self) -> dict[str, int | float | str]:
        return {
            "max_requests": MAX_REQUESTS,
            "max_reserved_output_tokens": MAX_RESERVED_OUTPUT_TOKENS,
            "max_elapsed_seconds": MAX_ELAPSED_SECONDS,
            "started_requests": self._requests,
            "completed_requests": self._completed,
            "reserved_output_tokens": self._reserved,
            "elapsed_seconds": max(0.0, time.monotonic() - self._started),
            "elapsed_policy": "admission_and_result_checks_not_remote_cancellation",
        }
