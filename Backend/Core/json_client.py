"""Structural contract for clients that return one generated JSON object."""

from __future__ import annotations

from typing import Protocol


class JSONGenerationClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...
