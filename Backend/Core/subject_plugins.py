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


@dataclass(frozen=True)
class ContractSubjectPlugin:
    """Safe baseline plugin for families with validation in their own contracts."""

    id: str

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        question = str(item.get("question", "")).strip()
        marks = item.get("marks")
        diagnostics: list[str] = []
        if not question:
            diagnostics.append("question text is required")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        if isinstance(item, dict) and "canonical_solution" in item:
            return item["canonical_solution"]
        raise ValueError(f"{self.id} item has no deterministic canonical solution")

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict) or "kind" not in specification:
            raise ValueError("visual specification must declare a kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict):
            return SubjectValidation(False, ("mark scheme must be an object",))
        points = scheme.get("mark_points")
        if not isinstance(points, list) or not points:
            return SubjectValidation(False, ("mark scheme requires mark points",))
        return SubjectValidation(True)

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "command": str(payload.get("command", "unknown")),
        }


_PLUGINS: dict[str, SubjectPlugin] = {
    identifier: ContractSubjectPlugin(identifier)
    for identifier in ("accounting", "business", "computer-science", "economics")
}


def register_subject_plugin(plugin: SubjectPlugin) -> None:
    identifier = _normalise_identifier(plugin.id)
    if identifier in _PLUGINS:
        raise ValueError(f"subject plugin already registered: {identifier}")
    _PLUGINS[identifier] = plugin


def discover_subject_plugin(identifier: str) -> SubjectPlugin:
    normalized = _normalise_identifier(identifier)
    try:
        return _PLUGINS[normalized]
    except KeyError as error:
        raise ValueError(f"unknown subject plugin: {identifier}") from error


def subject_plugin_ids() -> tuple[str, ...]:
    return tuple(sorted(_PLUGINS))


def _normalise_identifier(identifier: str) -> str:
    normalized = identifier.strip().lower()
    if (
        not normalized
        or normalized.startswith(".")
        or "/" in normalized
        or "\\" in normalized
        or ":" in normalized
        or normalized.endswith(".py")
    ):
        raise ValueError(f"unknown subject plugin: {identifier}")
    return normalized


# Imported after the protocol and registry exist so subject engines can reuse
# SubjectValidation without a module-initialisation cycle.
from Backend.Core.subjects.biology import BiologyPlugin  # noqa: E402
from Backend.Core.subjects.chemistry import ChemistryPlugin  # noqa: E402
from Backend.Core.subjects.essay import EssaySubjectPlugin  # noqa: E402
from Backend.Core.subjects.mathematics import (  # noqa: E402
    FurtherMathematicsPlugin,
    MathematicsPlugin,
)
from Backend.Core.subjects.physics import PhysicsPlugin  # noqa: E402

_PLUGINS[MathematicsPlugin.id] = MathematicsPlugin()
_PLUGINS[BiologyPlugin.id] = BiologyPlugin()
_PLUGINS[ChemistryPlugin.id] = ChemistryPlugin()
_PLUGINS[PhysicsPlugin.id] = PhysicsPlugin()
_PLUGINS[FurtherMathematicsPlugin.id] = FurtherMathematicsPlugin()
for _essay_subject in (
    "english-literature",
    "geography",
    "history",
    "psychology",
    "sociology",
):
    _PLUGINS[_essay_subject] = EssaySubjectPlugin(_essay_subject)
