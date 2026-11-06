"""Versioned source admission must not migrate unrelated old recovery files."""

import hashlib
import importlib
import json
from argparse import Namespace
from contextlib import contextmanager

import pytest

from Backend.Core.ai_assessment import ASSESSMENT_REVIEW_VERSION
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    identity_for_blueprint,
)
from Backend.Core.generation import checkpoint_path_for_job
from Backend.Core.generator_registry import generator_subjects
from Backend.Core.legacy_migration import output_directory


def request(subject="economics"):
    return Namespace(
        subject=subject,
        paper="2",
        seed=270100,
        provider="ollama",
        model="owned-no-model",
    )


def historical_path(args, output, source_version=None):
    identity = {
        "assessment_review_version": ASSESSMENT_REVIEW_VERSION,
        "subject": args.subject,
        "paper": args.paper,
        "seed": args.seed,
        "provider": args.provider,
        "model": args.model,
    }
    if source_version is not None:
        identity["economics_source_binding_version"] = source_version
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return (
        output_directory(output, ".keldin-checkpoints")
        / f"{args.subject}-paper-{args.paper}-{digest}.json"
    )


def test_new_economics_namespace_preserves_old_bytes_and_explicit_replay(tmp_path):
    args = request()
    old_path, new_path = (
        historical_path(args, tmp_path),
        checkpoint_path_for_job(args, tmp_path),
    )
    assert new_path != old_path
    assert "edexcel-instance-v2" in new_path.name
    marked = historical_path(args, tmp_path, source_version="edexcel-instance-v2")
    assert new_path == marked.with_name("edexcel-instance-v2." + marked.name)
    options = {
        "provider": args.provider,
        "model": args.model,
        "prompt_version": "owned-stable-policy",
    }
    old = identity_for_blueprint(
        {
            "paper_id": "paper_2",
            "seed": args.seed,
            "source_version": "edexcel-instance-v1",
        },
        **options,
    )
    new = identity_for_blueprint(
        {
            "paper_id": "paper_2",
            "seed": args.seed,
            "source_version": "edexcel-instance-v2",
        },
        **options,
    )
    AssessmentCheckpointStore(old_path, old).save_payload(
        "owned-accepted", {"sentinel": "preserved"}
    )
    before = old_path.read_bytes()
    current = AssessmentCheckpointStore(new_path, new)
    assert current.load_payload("owned-accepted") is None
    current.save_payload("new-owned", {"source_version": "v2"})
    assert old_path.read_bytes() == before
    retained = AssessmentCheckpointStore(old_path, old)
    assert retained.load_payload("owned-accepted") == {"sentinel": "preserved"}
    assert old_path.read_bytes() == before


@pytest.mark.parametrize(
    "subject", [s for s in generator_subjects() if s != "economics"]
)
def test_other_advertised_subject_checkpoint_paths_are_byte_identical(
    subject, tmp_path
):
    for provider, model in [("ollama", "owned-local"), ("openai", "owned-hosted")]:
        for paper in ["1", "2", "3"]:
            args = request(subject)
            args.provider, args.model, args.paper = provider, model, paper
            assert checkpoint_path_for_job(args, tmp_path) == historical_path(
                args, tmp_path
            )


@pytest.mark.parametrize("module_name", ["pastpapergen.cli", "keldin_edexcel.cli"])
@pytest.mark.parametrize("already_namespaced", [False, True])
@pytest.mark.parametrize("outcome", ["success", "failure", "cancel"])
@pytest.mark.parametrize("filename", ["retained.json", "no-extension"])
def test_explicit_package_checkpoint_path_is_versioned_once(
    module_name, already_namespaced, outcome, filename, tmp_path, monkeypatch
):
    from Backend.Core.document_publication import GenerationCancelled

    implementation = importlib.import_module("pastpapergen.cli")
    facade = importlib.import_module(module_name)
    received = []

    def run(*_args, **kwargs):
        received.append(kwargs)
        if outcome == "failure":
            raise RuntimeError("owned failure")
        if outcome == "cancel":
            raise GenerationCancelled
        return {}

    monkeypatch.setattr(implementation, "run_family_adapter", run)
    old_path = tmp_path / filename
    current_path = tmp_path / ("edexcel-instance-v2." + filename)
    supplied = current_path if already_namespaced else old_path
    old_path.write_bytes(b"owned legacy recovery sentinel")

    def invoke():
        return facade.generate_package(
            paper="2",
            syllabus_path=tmp_path / "owned.json",
            output_dir=tmp_path,
            seed=270100,
            model="owned-no-model",
            ollama_url="http://invalid.example",
            dry_run=False,
            checkpoint_path=supplied,
        )

    if outcome == "success":
        invoke()
    else:
        with pytest.raises(
            RuntimeError if outcome == "failure" else GenerationCancelled
        ):
            invoke()
    assert received[0]["checkpoint_path"] == current_path
    assert old_path.read_bytes() == b"owned legacy recovery sentinel"


@pytest.mark.parametrize("module_name", ["pastpapergen.cli", "keldin_edexcel.cli"])
def test_cli_default_uses_no_checkpoint_file(module_name, tmp_path, monkeypatch):
    implementation = importlib.import_module("pastpapergen.cli")
    facade = importlib.import_module(module_name)
    received = []
    monkeypatch.setattr(
        implementation,
        "run_family_adapter",
        lambda *_args, **kwargs: (
            received.append(kwargs)
            or {
                "question_paper": tmp_path / "qp.pdf",
                "source_booklet": tmp_path / "source.pdf",
                "mark_scheme": tmp_path / "ms.pdf",
            }
        ),
    )
    assert (
        facade.main(
            ["--paper", "2", "--seed", "270100", "--out", str(tmp_path), "--dry-run"]
        )
        == 0
    )
    assert received[0]["checkpoint_path"] is None


def test_bridge_lease_plugin_receipt_and_retirement_share_final_namespace(
    tmp_path, monkeypatch
):
    from Backend.Core import generation

    args = request()
    args.output, args.api_key, args.dry_run = str(tmp_path), "", False
    expected = checkpoint_path_for_job(args, tmp_path)
    seen = []

    @contextmanager
    def lease(path):
        seen.append(("lease", path))
        yield

    def invoke(*_args, checkpoint_path):
        seen.append(("plugin", checkpoint_path))
        return {}

    def receipt(path):
        seen.append(("receipt", path))
        return "owned-receipt"

    def retire(path, value):
        assert value == "owned-receipt"
        seen.append(("retire", path))
        return True

    monkeypatch.setattr(generation, "checkpoint_job_lease", lease)
    monkeypatch.setattr(generation, "_invoke_plugin", invoke)
    monkeypatch.setattr(
        generation, "finalize_generated_documents", lambda **_kwargs: {}
    )
    monkeypatch.setattr(generation, "checkpoint_receipt", receipt)
    monkeypatch.setattr(generation, "retire_checkpoint", retire)
    assert generation.handle_generate(args) == 0
    assert seen == [
        (name, expected) for name in ("lease", "plugin", "receipt", "retire")
    ]
