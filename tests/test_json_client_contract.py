from __future__ import annotations

import importlib
import sys
from dataclasses import replace
from typing import get_args, get_type_hints

import pytest

from Backend.Core.family_adapter import FamilyAdapter, run_family_adapter


class MinimalClient:
    def __init__(self, response=None):
        self.response = response or {}
        self.prompts = []

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.prompts.append(prompt)
        return self.response


def test_compatibility_names_share_one_minimal_protocol():
    from cspapergen.ollama_client import JSONGenerationClient as SpecialistClient

    from Backend.Core.independent_solver import SolverClient
    from Backend.Core.json_client import JSONGenerationClient
    from Backend.Core.model_review import JSONClient
    from Backend.Core.response_simulation import SimulationClient

    assert (
        SolverClient
        is JSONClient
        is SimulationClient
        is SpecialistClient
        is JSONGenerationClient
    )
    from Backend.Core.ai_assessment import AssessmentLLMClient

    assert JSONGenerationClient in AssessmentLLMClient.__mro__
    assert {"provider", "model"} <= AssessmentLLMClient.__annotations__.keys()


def test_adapter_annotations_retain_the_json_client_boundary():
    from Backend.Core.family_adapter import _hosted_client
    from Backend.Core.json_client import JSONGenerationClient

    assert get_type_hints(run_family_adapter)["client"] == JSONGenerationClient | None
    assert get_type_hints(_hosted_client)["return"] is JSONGenerationClient
    hints = get_type_hints(FamilyAdapter)
    for name in ("improve", "calibrate_difficulty"):
        callback = next(
            item for item in get_args(hints[name]) if item is not type(None)
        )
        assert get_args(callback)[0][3] is JSONGenerationClient
    factory = next(
        item for item in get_args(hints["client_factory"]) if item is not type(None)
    )
    assert get_args(factory)[1] is JSONGenerationClient


def test_every_dynamic_entrypoint_keeps_optional_client_signature():
    from Backend.Core.generator_registry import generator_capabilities
    from Backend.Core.json_client import JSONGenerationClient
    from Backend.Core.paths import REPO_ROOT

    for capability in generator_capabilities().values():
        root = str(REPO_ROOT / "Resources" / capability.python_path)
        sys.path.insert(0, root)
        try:
            module_name, function_name = capability.entry_point.split(":", 1)
            function = getattr(importlib.import_module(module_name), function_name)
            assert get_type_hints(function)["client"] == JSONGenerationClient | None
        finally:
            sys.path.remove(root)


@pytest.mark.parametrize("supplied", [True, False])
def test_adapter_passes_the_same_minimal_client_without_requiring_metadata(
    tmp_path, monkeypatch, supplied
):
    from Backend.Core import family_adapter

    client = MinimalClient()
    factories, observed, packages = [], [], []

    def factory(model, url):
        factories.append((model, url))
        return client

    def improve(assessment, _syllabus, _rule, actual, _progress, _checkpoint):
        observed.append(actual)
        return assessment

    adapter = FamilyAdapter(
        id="fixture",
        subject_label="Fixture",
        backend_subject="fixture",
        load_message="load",
        build_message="build",
        prompt_version="fixture-v1",
        load_syllabus=lambda _: None,
        load_rule=lambda _: None,
        build=lambda *_: {"paper_id": "fixture", "seed": 123},
        artifacts=lambda *_: (),
        stem=lambda *_: "fixture",
        improve=improve,
        calibrate_difficulty=lambda assessment, _syllabus, _rule, actual, _progress: (
            observed.append(actual) or assessment
        ),
        client_factory=factory,
    )
    monkeypatch.setattr(
        family_adapter,
        "write_assessment_package",
        lambda *args, **kwargs: packages.append(kwargs),
    )
    run_family_adapter(
        adapter,
        paper="1",
        syllabus_path=tmp_path / "syllabus.json",
        output_dir=tmp_path / "out",
        seed=123,
        model="fixture-model",
        dry_run=False,
        client=client if supplied else None,
    )
    assert all(actual is client for actual in observed)
    assert len(observed) == 2
    assert factories == (
        [] if supplied else [("fixture-model", "http://localhost:11434")]
    )
    assert packages[0]["provider"] == "ollama"
    assert packages[0]["model"] == "fixture-model"
    assert client.prompts == []

    def forbidden(*_args):
        pytest.fail("preview attempted AI work")

    preview = replace(
        adapter,
        client_factory=forbidden,
        improve=forbidden,
        calibrate_difficulty=forbidden,
    )
    run_family_adapter(
        preview,
        paper="1",
        syllabus_path=tmp_path / "syllabus.json",
        output_dir=tmp_path / "preview",
        seed=123,
        dry_run=True,
    )
    assert packages[-1]["preview"] is True
    assert packages[-1]["provider"] is packages[-1]["model"] is None


def test_minimal_fake_still_supports_model_review():
    from Backend.Core.model_review import ReviewResult, independent_review

    client = MinimalClient(ReviewResult(approved=True).model_dump())
    result = independent_review(
        client,
        item_id="q1",
        subject="Economics",
        blueprint={},
        candidate={},
        specification={},
    )
    assert result.approved
    assert len(client.prompts) == 1
    assert client.prompts[0].startswith(
        "Act as a second-pass UK A-level assessment editor."
    )


def test_minimal_fake_simulation_keeps_private_source_out_of_prompt():
    from Backend.Core.response_simulation import ResponseSimulator

    client = MinimalClient(
        {
            "responses": [
                {
                    "band": "weak",
                    "text": "A response.",
                    "demonstrated_mark_points": [],
                    "evidence_ids": [],
                    "misconceptions": [],
                }
            ]
        }
    )
    responses = ResponseSimulator(client).responses(
        {
            "id": "q1",
            "prompt": "Explain the decision.",
            "mark_scheme": ["PRIVATE_SENTINEL"],
        },
        bands=("weak",),
    )
    assert responses[0].band == "weak"
    assert len(client.prompts) == 1
    assert "PRIVATE_SENTINEL" not in client.prompts[0]


def test_minimal_fake_solver_keeps_private_answer_out_of_prompt():
    from Backend.Core.independent_solver import IndependentSolver

    client = MinimalClient(
        {
            "steps": ["Use the public task."],
            "answer": "A supported explanation.",
            "mark_points": ["A supported explanation."],
            "evidence_ids": [],
            "alternatives": [],
            "partial_credit_boundaries": [],
            "follow_through_rules": [],
        }
    )
    result = IndependentSolver(client).solve(
        {
            "id": "q1",
            "prompt": "Explain a possible decision.",
            "marks": 1,
            "mark_scheme": ["PRIVATE_SENTINEL"],
            "correct_choice": "PRIVATE_SENTINEL",
        },
        [],
    )
    assert result.answer == "A supported explanation."
    assert len(client.prompts) == 1
    assert "PRIVATE_SENTINEL" not in client.prompts[0]
