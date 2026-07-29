from __future__ import annotations

import importlib
import json
import sys

from Backend.Core.generator_registry import (
    REGISTRY_PATH,
    generator_capabilities,
    generator_capability,
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

    assert payload["schema_version"] == 2
    assert generator_subjects() == tuple(advertised)
    assert set(generator_capabilities()) == set(advertised)


def test_capabilities_distinguish_ai_and_constrained_generators() -> None:
    edexcel = generator_capability("economics")
    aqa = generator_capability("economics_aqa")

    assert edexcel.uses_ai
    assert set(edexcel.supported_providers) == {
        "ollama",
        "openai",
        "anthropic",
        "apple",
    }
    assert not aqa.uses_ai
    assert aqa.supported_providers == ()


def test_every_paper_declares_complete_output_roles() -> None:
    for capability in generator_capabilities().values():
        for paper in capability.papers:
            roles = capability.outputs_for(paper)
            assert "question_paper" in roles
            assert "mark_scheme" in roles
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
    for capability in generator_capabilities().values():
        assert f"--collect-submodules {capability.package}" not in script
