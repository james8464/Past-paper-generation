from __future__ import annotations

import importlib
import json
import sys

from Backend.Core.generator_registry import (
    REGISTRY_PATH,
    _capability,
    _paper_qualification,
    generator_capabilities,
    generator_subjects,
)
from Backend.Core.paths import REPO_ROOT


def test_registry_is_the_canonical_backend_subject_list() -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    advertised = [
        family["backend_subject"]
        for family in payload["families"]
        if family["advertised"]
    ]

    assert payload["schema_version"] == 4
    assert generator_subjects() == tuple(advertised)
    assert set(generator_capabilities()) == set(advertised)


def test_registry_migrates_legacy_gates_without_false_empirical_readiness() -> None:
    readiness = _paper_qualification(
        {
            "gates": {
                "release": True,
                "visual": True,
                "difficulty": False,
            }
        }
    )

    assert readiness.engineering_validated is True
    assert readiness.visually_calibrated is True
    assert readiness.empirically_calibrated is False


def test_schema_v3_family_metadata_migrates_deterministically() -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    legacy = dict(payload["families"][0])
    for field in (
        "manifest_version",
        "subject_plugin",
        "board_profile",
        "specification_version",
        "blueprint_version",
    ):
        legacy.pop(field)

    capability = _capability(legacy)

    assert capability.manifest_version == 1
    assert capability.subject_plugin == "accounting"
    assert capability.board_profile == "aqa"
    assert capability.specification_version == "legacy-registry-v3"
    assert capability.blueprint_version == "legacy-registry-v3"


def test_every_current_paper_has_truthful_qualification_levels() -> None:
    readiness = {
        (capability.id, paper): capability.qualification_by_paper[paper]
        for capability in generator_capabilities().values()
        for paper in capability.papers
    }

    assert len(readiness) == 21
    assert all(value.engineering_validated for value in readiness.values())
    assert all(not value.empirically_calibrated for value in readiness.values())
    assert all(
        value.visually_calibrated
        for (_family, paper), value in readiness.items()
        if not paper.startswith("bank-")
    )
    assert all(
        not value.visually_calibrated
        for (_family, paper), value in readiness.items()
        if paper.startswith("bank-")
    )


def test_every_advertised_generator_creates_unique_ai_content() -> None:
    for capability in generator_capabilities().values():
        assert capability.uses_ai
        assert set(capability.supported_providers) == {
            "ollama",
            "openai",
            "anthropic",
            "apple",
        }


def test_every_paper_declares_complete_output_roles() -> None:
    for capability in generator_capabilities().values():
        for paper in capability.papers:
            roles = capability.outputs_for(paper)
            assert "question_paper" in roles
            assert "mark_scheme" in roles
            assert "assessment_package" in roles
            assert len(roles) == len(set(roles))


def test_every_entry_point_and_declared_resource_is_loadable() -> None:
    for capability in generator_capabilities().values():
        generator_root = REPO_ROOT / "Resources" / capability.python_path
        syllabus = REPO_ROOT / "Resources" / capability.syllabus_path
        assert generator_root.is_dir()
        assert syllabus.is_file()
        sys.path.insert(0, str(generator_root))
        try:
            module_name, function_name = capability.entry_point.split(":", 1)
            function = getattr(importlib.import_module(module_name), function_name)
            assert callable(function)
        finally:
            sys.path.remove(str(generator_root))


def test_backend_bundle_script_is_registry_driven() -> None:
    script = (REPO_ROOT / "macOS" / "scripts" / "build_backend.sh").read_text()
    assert "generator_capabilities" in script
    assert "--hidden-import" in script
    assert "bundle-check" in script
    for capability in generator_capabilities().values():
        assert f"--collect-submodules {capability.package}" not in script


def test_backend_bundle_includes_declarative_profile_resources() -> None:
    script = (REPO_ROOT / "macOS" / "scripts" / "build_backend.sh").read_text()

    assert "generator-capability.schema.json" in script
    assert "empirical-calibration-policy.json" in script
    assert "Resources/board-profiles:Resources/board-profiles" in script
