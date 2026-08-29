from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from Backend.Core.board_profiles import board_profile as load_board_profile
from Backend.Core.paths import REPO_ROOT
from Backend.Core.subject_plugins import discover_subject_plugin

REGISTRY_PATH = REPO_ROOT / "Resources" / "generator-registry.json"
KNOWN_PROVIDERS = frozenset({"ollama", "openai", "anthropic", "apple"})
KNOWN_CONTENT_MODES = frozenset({"deterministic", "ai-assisted"})
KNOWN_QUALIFICATION_STATES = frozenset(
    {"not_run", "passed", "failed", "not_applicable"}
)


@dataclass(frozen=True)
class PaperQualification:
    engineering_validated: bool
    visually_calibrated: bool
    empirically_calibrated: bool
    evidence_by_level: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class GeneratorCapability:
    manifest_version: int
    id: str
    backend_subject: str
    resource_path: str
    python_path: str
    package: str
    entry_point: str
    syllabus_path: str
    subject_plugin: str
    board_profile: str
    specification_version: str
    blueprint_version: str
    reference_demand_profile: str
    content_mode: str
    supported_providers: tuple[str, ...]
    papers: tuple[str, ...]
    outputs_by_paper: dict[str, tuple[str, ...]]
    evidence_by_paper: dict[str, dict[str, bool]]
    qualification_by_paper: dict[str, PaperQualification]

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
    if payload.get("schema_version") not in {2, 3, 4}:
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
            for gate, passed in item.get("checks", item.get("gates", {})).items()
        }
        for item in raw.get("papers", [])
    }
    if set(evidence) != set(papers):
        raise ValueError(f"{raw['id']} is missing per-paper evidence")
    qualification = {
        str(item["id"]): _paper_qualification(item)
        for item in raw.get("papers", [])
    }
    entry_point = str(raw.get("entry_point", ""))
    package = str(raw.get("package", ""))
    if not entry_point.startswith(f"{package}.") or ":" not in entry_point:
        raise ValueError(f"{raw['id']} has an invalid entry point")
    resource_path = _relative_path(raw, "resource_path")
    python_path = _relative_path(raw, "python_path")
    syllabus_path = _relative_path(raw, "syllabus_path")
    manifest_version = int(raw.get("manifest_version", 1))
    if manifest_version != 1:
        raise ValueError(f"{raw['id']} has an unsupported manifest version")
    legacy_subject = {
        "economics-a-2015": "economics",
    }.get(str(raw.get("subject", "")), str(raw.get("subject", "")))
    subject_plugin = str(raw.get("subject_plugin", legacy_subject)).strip()
    board_profile = str(raw.get("board_profile", raw.get("board", ""))).strip()
    specification_version = str(
        raw.get("specification_version", "legacy-registry-v3")
    ).strip()
    blueprint_version = str(
        raw.get("blueprint_version", "legacy-registry-v3")
    ).strip()
    reference_demand_profile = (
        _relative_path(raw, "reference_demand_profile")
        if raw.get("reference_demand_profile")
        else ""
    )
    if raw.get("advertised") and mode == "ai-assisted" and not reference_demand_profile:
        raise ValueError(f"{raw['id']} is missing its reference demand profile")
    if not all(
        (subject_plugin, board_profile, specification_version, blueprint_version)
    ):
        raise ValueError(f"{raw['id']} has incomplete declarative capability metadata")
    discover_subject_plugin(subject_plugin)
    load_board_profile(board_profile)
    return GeneratorCapability(
        manifest_version=manifest_version,
        id=str(raw["id"]),
        backend_subject=str(raw["backend_subject"]),
        resource_path=resource_path,
        python_path=python_path,
        package=package,
        entry_point=entry_point,
        syllabus_path=syllabus_path,
        subject_plugin=subject_plugin,
        board_profile=board_profile,
        specification_version=specification_version,
        blueprint_version=blueprint_version,
        reference_demand_profile=reference_demand_profile,
        content_mode=mode,
        supported_providers=providers,
        papers=papers,
        outputs_by_paper=outputs,
        evidence_by_paper=evidence,
        qualification_by_paper=qualification,
    )


def _paper_qualification(raw: dict[str, Any]) -> PaperQualification:
    payload = raw.get("qualification")
    if payload is None:
        gates = raw.get("gates", {})
        if not isinstance(gates, dict):
            raise ValueError("legacy paper gates must be an object")
        return PaperQualification(
            engineering_validated=bool(gates.get("release", False)),
            visually_calibrated=bool(gates.get("visual", False)),
            empirically_calibrated=bool(gates.get("difficulty", False)),
            evidence_by_level={},
        )
    if not isinstance(payload, dict) or set(payload) != {
        "engineering",
        "visual",
        "empirical",
    }:
        raise ValueError("paper qualification levels must be engineering, visual, empirical")

    def level(name: str) -> tuple[bool, tuple[str, ...]]:
        value = payload[name]
        if not isinstance(value, dict):
            raise TypeError(f"paper qualification {name} must be an object")
        state = str(value.get("state", ""))
        if state not in KNOWN_QUALIFICATION_STATES:
            raise ValueError(f"paper qualification {name} has invalid state: {state}")
        evidence = value.get("evidence", [])
        if not isinstance(evidence, list) or not all(
            isinstance(path, str) and path for path in evidence
        ):
            raise ValueError(f"paper qualification {name} evidence must be paths")
        return state in {"passed", "not_applicable"}, tuple(evidence)

    engineering, engineering_evidence = level("engineering")
    visual, visual_evidence = level("visual")
    empirical, empirical_evidence = level("empirical")
    return PaperQualification(
        engineering_validated=engineering,
        visually_calibrated=visual,
        empirically_calibrated=empirical,
        evidence_by_level={
            "engineering": engineering_evidence,
            "visual": visual_evidence,
            "empirical": empirical_evidence,
        },
    )


def _relative_path(raw: dict[str, Any], name: str) -> str:
    value = str(raw.get(name, ""))
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{raw['id']} has an unsafe {name}")
    return value
