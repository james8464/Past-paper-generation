"""French commit/cleanup boundaries, not model, PDF or native-history acceptance.

Real owned-directory renames use prevalidated fake artifact bytes. Cancellation
is injected synchronously; no process signal, provider or renderer is invoked.
"""

import importlib
import signal
import socket
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(params=["runtime", "llm_runtime"])
def publication(request, tmp_path, monkeypatch):
    subject = importlib.import_module(f"Backend.Core.france.{request.param}")
    model_authored = request.param == "llm_runtime"
    output = tmp_path / "owned-output"
    output.mkdir()
    previous = output / "existing-user-file.txt"
    previous.write_bytes(b"preserve this owned sentinel")
    index = tmp_path / "references.sqlite"
    index.write_bytes(b"fake reference input; never opened as a database")
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        provider="ollama" if model_authored else "application-owned",
        authoring_version="v36" if model_authored else "v32",
        model="fixture-model",
        seed=42,
        reference_index=index,
        output=output,
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=False,
        api_key="",
        repeat_practice=False,
        exclude_family=[],
    )
    identity = {
        "provider": args.provider,
        "model": args.model,
        "seed": args.seed,
        "implementation_sha256": "a" * 64,
    }
    package = {"identity": identity, "exercises": [{}, {}, {}], "warnings": []}
    events = []
    emitted_failure = {"kind": None}

    def emit(kind, **fields):
        if kind == "file" and emitted_failure["kind"] is not None:
            error = emitted_failure.pop("kind")
            emitted_failure["kind"] = None
            raise error
        events.append({"type": kind, **fields})

    def forbidden(*_args, **_kwargs):
        pytest.fail("Publication fixture must not contact a model or network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subject, "emit", emit)
    monkeypatch.setattr(subject, "emit_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(subject, "implementation_identity", lambda: "a" * 64)
    monkeypatch.setattr(
        subject,
        "assessment_framework",
        lambda _identifier: SimpleNamespace(id=args.assessment),
    )

    def fake_render(path, _render, **_kwargs):
        path.write_bytes(
            b"complete prevalidated fixture artifact: " + path.name.encode()
        )

    monkeypatch.setattr(subject, "render_pdf_atomically", fake_render)
    if model_authored:
        identity.update(
            layout_policy=subject.CODE_LAYOUT_POLICY,
            sql_source_policy=subject.SQL_SOURCE_POLICY,
            review_recovery_policy=subject.llm_pipeline.REVIEW_RECOVERY_POLICY,
            large_print=False,
            print_policy={},
        )
        monkeypatch.setattr(
            subject, "_model_snapshot", lambda _args: "fixture-snapshot"
        )
        monkeypatch.setattr(subject, "HostedLLMClient", lambda **_kwargs: object())
        monkeypatch.setattr(
            subject,
            "FrenchGenerationBudget",
            lambda _client: SimpleNamespace(check=lambda: None, snapshot=lambda: {}),
        )
        monkeypatch.setattr(
            subject,
            "RecoveryEvidenceRecorder",
            lambda *_args, **_kwargs: SimpleNamespace(retention_warning=False),
        )
        monkeypatch.setattr(subject.llm_pipeline, "generate", lambda **_kwargs: package)
        monkeypatch.setattr(
            subject.llm_pipeline,
            "validate_package",
            lambda _package: package["exercises"],
        )
        monkeypatch.setattr(subject, "validate_llm_pdf", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(
            subject, "save_failure_diagnostic", lambda *_args, **_kwargs: None
        )
        handle = subject.handle_generate_llm_assessment
    else:
        from Backend.Core.france import whole_case_pdf

        identity["prompt_version"] = subject.EXPANDED_VERSION
        monkeypatch.setattr(
            subject,
            "ApplicationOwnedFrenchClient",
            lambda: SimpleNamespace(model_digest="fixture-digest"),
        )
        monkeypatch.setattr(subject, "FrenchOllamaClient", forbidden)
        monkeypatch.setattr(subject, "model_identity", forbidden)
        monkeypatch.setattr(subject, "load_originality_history", lambda _output: [])
        monkeypatch.setattr(subject, "choose_fresh_seed", lambda seed, **_kwargs: seed)
        monkeypatch.setattr(subject, "generate_assessment", lambda **_kwargs: package)
        monkeypatch.setattr(subject, "validate_package", lambda _package: None)
        monkeypatch.setattr(
            subject, "NSIExercise", SimpleNamespace(model_validate=lambda raw: raw)
        )
        monkeypatch.setattr(subject, "validate_pdf", lambda _path: None)
        monkeypatch.setattr(
            whole_case_pdf, "validate_whole_case_pdf", lambda *_args, **_kwargs: None
        )
        handle = subject.handle_generate_assessment
    return SimpleNamespace(
        subject=subject,
        args=args,
        handle=handle,
        output=output,
        events=events,
        emit_failure=emitted_failure,
        previous=previous,
        previous_handler=signal.getsignal(signal.SIGTERM),
    )


def inject_rename_interrupt(publication, monkeypatch, *, after_commit, error=None):
    original = publication.subject.os.rename
    commits = []

    def rename(source, destination):
        if after_commit:
            original(source, destination)
            commits.append(Path(destination))
        if error is not None:
            raise error
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)
        pytest.fail("The installed cancellation handler must interrupt publication")

    monkeypatch.setattr(publication.subject.os, "rename", rename)
    return commits


def assert_preserved_state(publication):
    assert publication.previous.read_bytes() == b"preserve this owned sentinel"
    assert not list(publication.output.glob(".nsi-*"))
    assert signal.getsignal(signal.SIGTERM) == publication.previous_handler


def assert_complete_bundle(publication):
    (bundle,) = publication.output.glob("nsi-2027-*")
    assert {path.name for path in bundle.iterdir()} == {
        "sujet.pdf",
        "corrige.pdf",
        "assessment.json",
        "manifest.json",
    }
    for name in ("sujet.pdf", "corrige.pdf"):
        assert (bundle / name).read_bytes() == (
            b"complete prevalidated fixture artifact: " + name.encode()
        )
    return bundle


def test_postrename_sigterm_does_not_mask_cancellation(publication, monkeypatch):
    commits = inject_rename_interrupt(publication, monkeypatch, after_commit=True)
    # A complete retained bundle does not manufacture successful event delivery.
    assert publication.handle(publication.args) == 130
    assert commits == [assert_complete_bundle(publication)]
    assert publication.events[-1]["code"] == "cancelled"
    assert not any(event["type"] in {"file", "done"} for event in publication.events)
    assert_preserved_state(publication)


def test_postrename_keyboardinterrupt_is_not_masked(publication, monkeypatch):
    cancellation = KeyboardInterrupt("owned postrename keyboard fixture")
    commits = inject_rename_interrupt(
        publication, monkeypatch, after_commit=True, error=cancellation
    )
    with pytest.raises(KeyboardInterrupt) as caught:
        publication.handle(publication.args)
    assert caught.value is cancellation
    assert commits == [assert_complete_bundle(publication)]
    assert not any(event["type"] in {"file", "done"} for event in publication.events)
    assert_preserved_state(publication)


@pytest.mark.parametrize("keyboard", [False, True])
def test_precommit_cancellation_keeps_output_absent(publication, monkeypatch, keyboard):
    cancellation = KeyboardInterrupt("owned precommit fixture") if keyboard else None
    inject_rename_interrupt(
        publication, monkeypatch, after_commit=False, error=cancellation
    )
    if keyboard:
        with pytest.raises(KeyboardInterrupt) as caught:
            publication.handle(publication.args)
        assert caught.value is cancellation
    else:
        assert publication.handle(publication.args) == 130
        assert publication.events[-1]["code"] == "cancelled"
    assert not list(publication.output.glob("nsi-2027-*"))
    assert not any(event["type"] in {"file", "done"} for event in publication.events)
    assert_preserved_state(publication)


def test_success_still_delivers_committed_files_then_done(publication):
    assert publication.handle(publication.args) == 0
    bundle = assert_complete_bundle(publication)
    assert [event["type"] for event in publication.events] == ["file"] * 4 + ["done"]
    assert len({event["path"] for event in publication.events[:-1]}) == 4
    assert all(
        Path(event["path"]).parent == bundle for event in publication.events[:-1]
    )
    assert_preserved_state(publication)


@pytest.mark.parametrize("broken_pipe", [False, True])
def test_emit_failure_after_commit_is_not_done(publication, broken_pipe):
    publication.emit_failure["kind"] = (
        BrokenPipeError("owned event channel fixture")
        if broken_pipe
        else InterruptedError("owned postcommit event fixture")
    )
    assert publication.handle(publication.args) == (1 if broken_pipe else 130)
    assert_complete_bundle(publication)
    assert publication.events[-1]["type"] == "error"
    assert publication.events[-1]["code"] == (
        "french_generation_failed" if broken_pipe else "cancelled"
    )
    assert not any(event["type"] in {"file", "done"} for event in publication.events)
    assert_preserved_state(publication)


def test_owned_staging_cleanup_removes_only_its_existing_root(tmp_path):
    from Backend.Core.temporary_cleanup import remove_owned_staging

    staging = tmp_path / "owned-staging"
    staging.mkdir()
    (staging / "child").write_bytes(b"owned fixture")
    unrelated = tmp_path / "unrelated"
    unrelated.write_bytes(b"preserve fixture")
    remove_owned_staging(staging)
    assert not staging.exists()
    assert unrelated.read_bytes() == b"preserve fixture"


def test_owned_staging_cleanup_accepts_a_truly_absent_root(tmp_path):
    from Backend.Core.temporary_cleanup import remove_owned_staging

    staging = tmp_path / "already-absent"
    remove_owned_staging(staging)
    assert not staging.exists()


def test_owned_staging_cleanup_does_not_swallow_permission_error(tmp_path, monkeypatch):
    from Backend.Core import temporary_cleanup

    staging = tmp_path / "owned-staging"
    staging.mkdir()
    error = PermissionError("owned cleanup fixture")

    def refuse(_path):
        raise error

    monkeypatch.setattr(temporary_cleanup.shutil, "rmtree", refuse)
    with pytest.raises(PermissionError) as caught:
        temporary_cleanup.remove_owned_staging(staging)
    assert caught.value is error
    assert staging.is_dir()


def test_missing_child_cleanup_error_is_not_ignored_while_root_exists(
    tmp_path, monkeypatch
):
    from Backend.Core import temporary_cleanup

    staging = tmp_path / "owned-staging"
    staging.mkdir()
    error = FileNotFoundError("owned missing child fixture")

    def missing_child(_path):
        raise error

    monkeypatch.setattr(temporary_cleanup.shutil, "rmtree", missing_child)
    with pytest.raises(FileNotFoundError) as caught:
        temporary_cleanup.remove_owned_staging(staging)
    assert caught.value is error
    assert staging.is_dir()
