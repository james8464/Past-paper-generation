import json
from argparse import Namespace
from pathlib import Path

import pytest


def test_public_cli_defaults_to_model_authored_french():
    from Backend.Core.cli import build_parser

    args = build_parser().parse_args(
        [
            "generate-assessment",
            "--assessment",
            "fr-bac-general-nsi-written-2027",
            "--reference-index",
            "references.sqlite",
            "--seed",
            "42",
        ]
    )
    assert args.provider == "ollama"
    assert args.authoring_version == "v36"


@pytest.mark.parametrize(
    "provider", ["ollama", "apple", "openai", "anthropic", "deepseek"]
)
def test_new_public_route_never_calls_the_catalogue(monkeypatch, provider):
    from Backend.Core.france import llm_runtime, runtime

    seen = []
    monkeypatch.setattr(
        llm_runtime,
        "handle_generate_llm_assessment",
        lambda args: seen.append(args) or 7,
    )
    monkeypatch.setattr(
        runtime, "generate_assessment", lambda **kwargs: pytest.fail("catalogue called")
    )
    args = Namespace(provider=provider, authoring_version="v36")
    assert runtime.handle_generate_assessment(args) == 7
    assert seen == [args]


@pytest.fixture
def publication(tmp_path, monkeypatch):
    from Backend.Core.france import llm_runtime
    from tests.test_french_llm_pipeline import Client
    from tests.test_nsi_pipeline import make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        provider="ollama",
        model="mock-model",
        seed=42,
        reference_index=index,
        output=tmp_path / "private-output",
        ollama_url="http://localhost:11434",
        large_print=False,
        api_key="",
    )
    events = []
    monkeypatch.setattr(llm_runtime, "HostedLLMClient", lambda **kwargs: Client())
    monkeypatch.setattr(llm_runtime, "_model_snapshot", lambda args: "a" * 64)
    monkeypatch.setattr(
        llm_runtime,
        "emit",
        lambda kind, **fields: events.append({"type": kind, **fields}),
    )
    return llm_runtime, args, events


@pytest.mark.parametrize("large_print", [False, True])
def test_real_pdf_publication_keeps_model_identity_and_private_evidence(
    publication, large_print
):
    subject, args, events = publication
    args.large_print = large_print
    assert subject.handle_generate_llm_assessment(args) == 0, events
    files = {
        event["role"]: Path(event["path"])
        for event in events
        if event["type"] == "file"
    }
    assert set(files) == {
        "question_paper",
        "mark_scheme",
        "assessment_package",
        "package_manifest",
    }
    assert all(path.is_file() for path in files.values())
    manifest = json.loads(files["package_manifest"].read_text())
    assert manifest["identity"]["model"] == args.model
    assert manifest["identity"]["seed"] == args.seed
    assert manifest["model_used"] is True
    assert manifest["model_snapshot_sha256"] == "a" * 64
    assert manifest["teacher_review"] == manifest["empirical_calibration"] == "not_run"
    assert manifest["large_print"] is large_print
    assert manifest["warnings"]
    assert not list(args.output.glob(".nsi-llm-*"))
    assert events[-1]["type"] == "done"


def test_render_failure_never_publishes_partial_output(publication, monkeypatch):
    subject, args, events = publication

    def fail(*args, **kwargs):
        raise ValueError("Corrigé illisible")

    monkeypatch.setattr(subject, "validate_llm_pdf", fail)
    assert subject.handle_generate_llm_assessment(args) == 1
    assert not any(event["type"] in {"file", "done"} for event in events)
    assert not list(args.output.glob(".nsi-llm-*"))
    assert not list(args.output.rglob("*.pdf"))


def test_different_actual_model_is_not_published_under_requested_identity(
    publication, monkeypatch
):
    subject, args, events = publication
    from tests.test_french_llm_pipeline import Client

    client = Client()
    client.model = "different-model"
    monkeypatch.setattr(subject, "HostedLLMClient", lambda **kwargs: client)
    assert subject.handle_generate_llm_assessment(args) == 1
    assert "modèle" in events[-1]["message"]
    assert not any(event["type"] in {"file", "done"} for event in events)


def test_cancelled_model_call_never_publishes_a_draft(publication, monkeypatch):
    subject, args, events = publication

    def cancel(**kwargs):
        raise InterruptedError("Création annulée")

    monkeypatch.setattr(subject.llm_pipeline, "generate", cancel)
    assert subject.handle_generate_llm_assessment(args) == 130
    assert events[-1]["code"] == "cancelled"
    assert not any(event["type"] in {"file", "done"} for event in events)


@pytest.mark.parametrize("changed", ["model", "source", "references"])
def test_changed_generation_inputs_prevent_publication(
    publication, monkeypatch, changed
):
    subject, args, events = publication
    if changed == "model":
        values = iter(["a" * 64, "b" * 64])
        monkeypatch.setattr(subject, "_model_snapshot", lambda args: next(values))
    elif changed == "source":
        values = iter([subject.implementation_identity(), "b" * 64])
        monkeypatch.setattr(subject, "implementation_identity", lambda: next(values))
    else:
        original = subject._file_hash
        calls = 0

        def changed_hash(path):
            nonlocal calls
            if path == args.reference_index:
                calls += 1
                return str(calls) * 64
            return original(path)

        monkeypatch.setattr(subject, "_file_hash", changed_hash)
    assert subject.handle_generate_llm_assessment(args) == 1
    assert "ont changé" in events[-1]["message"]
    assert not any(event["type"] in {"file", "done"} for event in events)
    assert not list(args.output.rglob("*.pdf"))
