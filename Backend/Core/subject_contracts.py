"""Shared subject interfaces, independent of plugin implementations and discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class SubjectValidation:
    passed: bool
    diagnostics: tuple[str, ...] = ()


@runtime_checkable
class SubjectPlugin(Protocol):
    id: str

    def validate_item(self, item: Any) -> SubjectValidation: ...

    def solve(self, item: Any) -> Any: ...

    def render_visual(self, specification: Any) -> Any: ...

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation: ...

    def calibration_features(self, item: Any) -> dict[str, float | str]: ...
