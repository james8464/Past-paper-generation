from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from Backend.Core.paths import REPO_ROOT


REGISTRY_PATH = REPO_ROOT / "Resources" / "generator-registry.json"
KNOWN_PROVIDERS = frozenset({"ollama", "openai", "anthropic", "apple"})
KNOWN_CONTENT_MODES = frozenset({"deterministic", "ai-assisted"})


@dataclass(frozen=True)
class GeneratorCapability:
    id: str
    backend_subject: str
    resource_path: str
    python_path: str
    package: str
    entry_point: str
    syllabus_path: str
    content_mode: str
    supported_providers: tuple[str, ...]
    papers: tuple[str, ...]
    outputs_by_paper: dict[str, tuple[str, ...]]
    evidence_by_paper: dict[str, dict[str, bool]]

    @property
    def uses_ai(self) -> bool:
        return self.content_mode == "ai-assisted"

    def outputs_for(self, paper: str) -> tuple[str, ...]:
        try:
            return self.outputs_by_paper[paper]
        except KeyError as error:
            raise ValueError(
                f"{self.backend_subject} does not support paper {paper}"
            ) from error


@lru_cache(maxsize=1)
def generator_capabilities() -> dict[str, GeneratorCapability]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError(
            f"unsupported generator registry schema: {payload.get('schema_version')}"
        )
    result: dict[str, GeneratorCapability] = {}
    for raw in payload.get("families", []):
        if not raw.get("advertised"):
            continue
        capability = _capability(raw)
        if capability.backend_subject in result:
            raise ValueError(
                f"duplicate backend subject: {capability.backend_subject}"
            )
        result[capability.backend_subject] = capability
    if not result:
        raise ValueError("generator registry has no advertised families")
    return result


def generator_capability(subject: str) -> GeneratorCapability:
    try:
        return generator_capabilities()[subject]
    except KeyError as error:
        raise ValueError(f"unsupported subject: {subject}") from error


def generator_subjects() -> tuple[str, ...]:
    return tuple(generator_capabilities())


def _capability(raw: dict[str, Any]) -> GeneratorCapability:
    papers = tuple(str(item["id"]) for item in raw.get("papers", []))
    declared = tuple(str(item) for item in raw.get("declared_papers", []))
    if not papers or papers != declared:
        raise ValueError(
            f"{raw.get('id', 'unknown')} declared papers do not match paper records"
        )
    mode = str(raw.get("content_mode", ""))
    if mode not in KNOWN_CONTENT_MODES:
        raise ValueError(f"{raw['id']} has unsupported content mode: {mode}")
    providers = tuple(str(item) for item in raw.get("supported_providers", []))
    unknown_providers = set(providers) - KNOWN_PROVIDERS
    if unknown_providers:
        raise ValueError(
            f"{raw['id']} has unknown providers: {sorted(unknown_providers)}"
        )
    if (mode == "ai-assisted") != bool(providers):
        raise ValueError(
            f"{raw['id']} AI mode and supported providers disagree"
        )
    output_payload = raw.get("outputs_by_paper", {})
    outputs = {
        paper: tuple(str(role) for role in output_payload.get(paper, ()))
        for paper in papers
    }
    if any(not roles for roles in outputs.values()):
        raise ValueError(f"{raw['id']} is missing declared output roles")
    evidence = {
        str(item["id"]): {
            str(gate): bool(passed)
            for gate, passed in item.get("gates", {}).items()
        }
        for item in raw.get("papers", [])
    }
    if set(evidence) != set(papers):
        raise ValueError(f"{raw['id']} is missing per-paper evidence")
    entry_point = str(raw.get("entry_point", ""))
    package = str(raw.get("package", ""))
    if not entry_point.startswith(f"{package}.") or ":" not in entry_point:
        raise ValueError(f"{raw['id']} has an invalid entry point")
    resource_path = _relative_path(raw, "resource_path")
    python_path = _relative_path(raw, "python_path")
    syllabus_path = _relative_path(raw, "syllabus_path")
    return GeneratorCapability(
        id=str(raw["id"]),
        backend_subject=str(raw["backend_subject"]),
        resource_path=resource_path,
        python_path=python_path,
        package=package,
        entry_point=entry_point,
        syllabus_path=syllabus_path,
        content_mode=mode,
        supported_providers=providers,
        papers=papers,
        outputs_by_paper=outputs,
        evidence_by_paper=evidence,
    )


def _relative_path(raw: dict[str, Any], name: str) -> str:
    value = str(raw.get(name, ""))
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{raw['id']} has an unsafe {name}")
    return value
