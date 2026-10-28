from __future__ import annotations

import errno
import json
import multiprocessing
import threading
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from Backend.Core import assessment_checkpoints as checkpoints
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    CheckpointIdentity,
    CheckpointMismatch,
)


def identity(**changes) -> CheckpointIdentity:
    return CheckpointIdentity(
        paper_id="paper-1",
        seed=123,
        provider="ollama",
        model="fixture",
        blueprint_sha256="a" * 64,
        prompt_version="fixture-v1",
    ).model_copy(update=changes)


def _process_save(path, key, ready, release, started, done):
    started.set()
    store = AssessmentCheckpointStore(Path(path), identity())
    if key == "first":
        original = store._write_document

        def paused(document):
            ready.set()
            if not release.wait(15):
                raise RuntimeError("test writer release timed out")
            original(document)

        store._write_document = paused
    store.save_payload(key, {"value": key})
    done.set()


def _process_lease(path, ready):
    with checkpoints.checkpoint_job_lease(Path(path)):
        ready.set()
        threading.Event().wait(30)


def _process_interrupted_write(path, ready):
    store = AssessmentCheckpointStore(Path(path), identity())

    def pause_before_replace(*_args):
        ready.set()
        threading.Event().wait(30)
        raise RuntimeError("test writer was not killed")

    checkpoints.os.replace = pause_before_replace
    store.save_payload("unfinished", {"value": 2})


def test_separate_instances_serialize_read_modify_write(tmp_path):
    path = tmp_path / "job.json"
    first, second = (AssessmentCheckpointStore(path, identity()) for _ in range(2))
    ready, release, second_started, second_done = (threading.Event() for _ in range(4))
    original = first._write_document

    def paused(document):
        ready.set()
        assert release.wait(10)
        original(document)

    first._write_document = paused

    def save_second():
        second_started.set()
        second.save_payload("second", {"value": 2})
        second_done.set()

    with ThreadPoolExecutor(2) as pool:
        one = pool.submit(first.save_payload, "first", {"value": 1})
        assert ready.wait(10)
        two = pool.submit(save_second)
        assert second_started.wait(10)
        try:
            assert not second_done.wait(0.2)
        finally:
            release.set()
        one.result(timeout=10)
        two.result(timeout=10)
    assert set(json.loads(path.read_text())["items"]) == {"first", "second"}


def test_spawned_processes_preserve_both_accepted_payloads(tmp_path):
    context = multiprocessing.get_context("spawn")
    ready, release, first_started, first_done, second_started, second_done = (
        context.Event() for _ in range(6)
    )
    path = tmp_path / "job.json"
    first = context.Process(
        target=_process_save,
        args=(str(path), "first", ready, release, first_started, first_done),
    )
    second = context.Process(
        target=_process_save,
        args=(str(path), "second", ready, release, second_started, second_done),
    )
    first.start()
    try:
        assert ready.wait(15)
        second.start()
        assert second_started.wait(15)
        try:
            assert not second_done.wait(0.3)
        finally:
            release.set()
        first.join(15)
        second.join(15)
        assert (first.exitcode, second.exitcode) == (0, 0)
        assert set(json.loads(path.read_text())["items"]) == {"first", "second"}
    finally:
        release.set()
        for process in (first, second):
            if process.pid is not None and process.is_alive():
                process.terminate()
                process.join(10)


def test_job_lease_is_canonical_nonblocking_and_keeps_sidecar(tmp_path):
    path = tmp_path / "job.json"
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with checkpoints.checkpoint_job_lease(path):
        with (
            pytest.raises(checkpoints.CheckpointBusy),
            checkpoints.checkpoint_job_lease(alias / "job.json"),
        ):
            pytest.fail("same job acquired twice")
        with checkpoints.checkpoint_job_lease(tmp_path / "other.json"):
            pass
    sidecar = path.with_suffix(".json.job.lock")
    inode = sidecar.stat().st_ino
    with checkpoints.checkpoint_job_lease(path):
        pass
    assert sidecar.stat().st_ino == inode


@pytest.mark.parametrize("code", [errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK])
def test_job_contention_errno_variants_are_busy(tmp_path, monkeypatch, code):
    def contention(*_args):
        raise OSError(code, "lock contention")

    monkeypatch.setattr(checkpoints.fcntl, "flock", contention)
    with (
        pytest.raises(checkpoints.CheckpointBusy),
        checkpoints.checkpoint_job_lease(tmp_path / "job.json"),
    ):
        pytest.fail("contended job entered")


@pytest.mark.parametrize(
    "job,code", [(False, errno.EACCES), (False, errno.EAGAIN), (True, errno.EIO)]
)
def test_other_lock_errors_propagate(tmp_path, monkeypatch, job, code):
    failure = OSError(code, "original lock failure")

    def fail(*_args):
        raise failure

    monkeypatch.setattr(checkpoints.fcntl, "flock", fail)
    with (
        pytest.raises(OSError) as raised,
        checkpoints._file_lock(tmp_path / "job.json", job=job),
    ):
        pytest.fail("failed lock entered")
    assert raised.value is failure


def test_job_sidecar_open_permission_error_is_not_contention(tmp_path, monkeypatch):
    failure = PermissionError(errno.EACCES, "sidecar denied")

    def fail(*_args):
        raise failure

    monkeypatch.setattr(checkpoints.os, "open", fail)
    with (
        pytest.raises(PermissionError) as raised,
        checkpoints.checkpoint_job_lease(tmp_path / "job.json"),
    ):
        pytest.fail("denied sidecar entered")
    assert raised.value is failure


def test_killed_owner_releases_lease_without_deleting_checkpoint(tmp_path):
    path = tmp_path / "job.json"
    AssessmentCheckpointStore(path, identity()).save_payload("accepted", {"value": 1})
    original = path.read_bytes()
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    owner = context.Process(target=_process_lease, args=(str(path), ready))
    owner.start()
    try:
        assert ready.wait(15)
        owner.kill()
        owner.join(15)
        with checkpoints.checkpoint_job_lease(path):
            assert path.read_bytes() == original
    finally:
        if owner.is_alive():
            owner.kill()
            owner.join(10)


def test_replace_failure_preserves_original_and_unrelated_temporary(
    tmp_path, monkeypatch
):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    before = path.read_bytes()
    unrelated = tmp_path / "job.json.tmp"
    unrelated.write_bytes(b"another writer owns this")

    def fail_replace(*_args):
        raise OSError("injected replacement failure")

    monkeypatch.setattr(checkpoints.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement failure"):
        store.save_payload("later", {"value": 2})
    assert path.read_bytes() == before
    assert unrelated.read_bytes() == b"another writer owns this"
    assert sorted(item.name for item in tmp_path.glob("*.tmp")) == ["job.json.tmp"]


def test_serialization_failure_cleans_only_own_temp(tmp_path):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    before = path.read_bytes()
    with pytest.raises(TypeError):
        store.save_payload("invalid", {"value": object()})
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_successful_replace_does_not_attempt_a_second_temporary_unlink(
    tmp_path, monkeypatch
):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    original_replace = checkpoints.os.replace
    original_unlink = Path.unlink
    committed = False
    cleanup_attempts = []

    def replace(source, destination):
        nonlocal committed
        original_replace(source, destination)
        committed = True

    def unlink(temporary, *args, **kwargs):
        if committed and temporary.suffix == ".tmp":
            cleanup_attempts.append(temporary)
            raise PermissionError(errno.EACCES, "post-replacement cleanup denied")
        return original_unlink(temporary, *args, **kwargs)

    monkeypatch.setattr(checkpoints.os, "replace", replace)
    monkeypatch.setattr(Path, "unlink", unlink)
    failure = None
    try:
        store.save_payload("later", {"value": 2})
    except OSError as error:
        failure = error

    assert committed
    assert json.loads(path.read_text())["items"] == {
        "accepted": {"value": 1},
        "later": {"value": 2},
    }
    assert not list(tmp_path.glob("*.tmp"))
    assert failure is None
    assert cleanup_attempts == []


def test_file_sync_failure_preserves_previous_checkpoint(tmp_path, monkeypatch):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    before = path.read_bytes()

    def fail_sync(_descriptor):
        raise OSError("injected sync failure")

    monkeypatch.setattr(checkpoints.os, "fsync", fail_sync)
    with pytest.raises(OSError, match="sync failure"):
        store.save_payload("unfinished", {"value": 2})
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("operation", ["serialize", "sync", "replace"])
def test_failed_temporary_cleanup_does_not_mask_original_failure(
    tmp_path, monkeypatch, operation
):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    before = path.read_bytes()
    original_unlink = Path.unlink

    def fail_cleanup(temporary, *args, **kwargs):
        if temporary.suffix == ".tmp":
            raise OSError("secondary cleanup failure")
        return original_unlink(temporary, *args, **kwargs)

    def fail_operation(*_args):
        raise OSError("original operation failure")

    monkeypatch.setattr(Path, "unlink", fail_cleanup)
    payload = {"value": object()} if operation == "serialize" else {"value": 2}
    if operation == "sync":
        monkeypatch.setattr(checkpoints.os, "fsync", fail_operation)
    elif operation == "replace":
        monkeypatch.setattr(checkpoints.os, "replace", fail_operation)
    expected_type = TypeError if operation == "serialize" else OSError
    expected_message = (
        "serializable" if operation == "serialize" else "original operation failure"
    )
    with pytest.raises(expected_type, match=expected_message):
        store.save_payload("unfinished", payload)
    assert path.read_bytes() == before
    assert len(list(tmp_path.glob("*.tmp"))) == 1


def test_clear_and_recreate_preserve_transaction_lock_inode(tmp_path):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    sidecar = path.with_suffix(".json.lock")
    inode = sidecar.stat().st_ino
    store.clear()
    store.clear()
    store.save_payload("next", {"value": 2})
    assert sidecar.stat().st_ino == inode
    assert set(json.loads(path.read_text())["items"]) == {"next"}


@pytest.mark.parametrize(
    "field,value", [("model", "other"), ("blueprint_sha256", "b" * 64)]
)
def test_clear_refuses_replaced_identity(tmp_path, field, value):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    document = json.loads(path.read_text())
    document["identity"][field] = value
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    with pytest.raises(CheckpointMismatch, match=field):
        store.clear()
    assert path.read_bytes() == before


def test_conditional_retirement_retains_changed_checkpoint(tmp_path):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    receipt = checkpoints.checkpoint_receipt(path)
    store.save_payload("later", {"value": 2})
    before = path.read_bytes()
    assert not checkpoints.retire_checkpoint(path, receipt)
    assert path.read_bytes() == before
    assert checkpoints.retire_checkpoint(path, checkpoints.checkpoint_receipt(path))
    assert not path.exists()
    assert checkpoints.retire_checkpoint(path, receipt)
    assert path.with_suffix(".json.lock").is_file()


def test_absent_receipt_cannot_delete_newly_created_checkpoint(tmp_path):
    path = tmp_path / "job.json"
    receipt = checkpoints.checkpoint_receipt(path)
    assert receipt is None
    AssessmentCheckpointStore(path, identity()).save_payload("accepted", {})
    assert not checkpoints.retire_checkpoint(path, receipt)
    assert path.exists()


def test_killed_writer_before_replace_preserves_accepted_json_and_other_temps(tmp_path):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    before = path.read_bytes()
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    writer = context.Process(target=_process_interrupted_write, args=(str(path), ready))
    writer.start()
    try:
        assert ready.wait(15)
        writer.kill()
        writer.join(15)
        assert path.read_bytes() == before
        abandoned = {item: item.read_bytes() for item in tmp_path.glob("*.tmp")}
        assert len(abandoned) == 1
        store.save_payload("retry", {"value": 3})
        assert {item: item.read_bytes() for item in abandoned} == abandoned
        assert set(json.loads(path.read_text())["items"]) == {"accepted", "retry"}
    finally:
        if writer.is_alive():
            writer.kill()
            writer.join(10)


def test_blueprint_migration_waits_for_existing_transaction(tmp_path):
    path = tmp_path / "job.json"
    store = AssessmentCheckpointStore(path, identity())
    store.save_payload("accepted", {"value": 1})
    started, done = threading.Event(), threading.Event()

    def migrate():
        started.set()
        revised = AssessmentCheckpointStore(path, identity(blueprint_sha256="b" * 64))
        done.set()
        return revised

    with ThreadPoolExecutor(1) as pool:
        with store._transaction():
            future = pool.submit(migrate)
            assert started.wait(10)
            assert not done.wait(0.2)
        migrated = future.result(timeout=10)
    assert migrated.load_payload("accepted") == {"value": 1}
    assert json.loads(path.read_text())["identity"]["blueprint_sha256"] == "b" * 64


def _request(path):
    return Namespace(
        output=str(path),
        api_key="",
        model="fixture",
        subject="economics",
        paper="1",
        provider="ollama",
        dry_run=False,
        seed=123,
    )


def test_handler_busy_refuses_before_authoring(tmp_path, monkeypatch, capsys):
    from Backend.Core import generation

    request = _request(tmp_path)
    path = generation.checkpoint_path_for_job(request, tmp_path)
    invoked = []
    monkeypatch.setattr(
        generation, "_invoke_plugin", lambda *_args, **_kwargs: invoked.append(True)
    )
    with checkpoints.checkpoint_job_lease(path):
        assert generation.handle_generate(request) == 1
    assert not invoked
    assert (
        json.loads(capsys.readouterr().out.splitlines()[-1])["code"]
        == "checkpoint_busy"
    )
    assert not list(tmp_path.glob(".keldin-economics-*"))


def test_preview_publication_does_not_retire_accepted_live_checkpoint(
    tmp_path, monkeypatch
):
    from Backend.Core import generation

    request = _request(tmp_path)
    request.dry_run = True
    path = generation.checkpoint_path_for_job(request, tmp_path)
    AssessmentCheckpointStore(path, identity()).save_payload("accepted", {"value": 1})
    before = path.read_bytes()
    monkeypatch.setattr(generation, "_invoke_plugin", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        generation, "finalize_generated_documents", lambda **_kwargs: {}
    )
    monkeypatch.setattr(generation, "emit_generated_files", lambda *_args: None)
    assert generation.handle_generate(request) == 0
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "cleanup",
    [
        "changed",
        "retire_error",
        "receipt_error",
        "unchanged",
        "publication_failure",
        "retire_sync_error",
        "retire_cancelled",
        "publication_cancelled",
    ],
)
def test_handler_holds_lease_and_separates_publication_from_cleanup(
    tmp_path, monkeypatch, cleanup
):
    from Backend.Core import generation

    request = _request(tmp_path)
    path = generation.checkpoint_path_for_job(request, tmp_path)
    events, emitted = [], []
    monkeypatch.setattr(
        generation,
        "emit_progress",
        lambda message, **fields: events.append((message, fields)),
    )
    monkeypatch.setattr(generation, "emit_generated_files", emitted.append)

    def author(*_args, **_kwargs):
        AssessmentCheckpointStore(path, identity()).save_payload(
            "accepted", {"value": 1}
        )
        return {"question_paper": tmp_path / "paper.pdf"}

    def publish(**kwargs):
        with (
            pytest.raises(checkpoints.CheckpointBusy),
            checkpoints.checkpoint_job_lease(path),
        ):
            pytest.fail("publication lost its job lease")
        if cleanup == "changed":
            AssessmentCheckpointStore(path, identity()).save_payload(
                "later", {"value": 2}
            )
        if cleanup == "publication_failure":
            raise OSError("publication failed")
        if cleanup == "publication_cancelled":
            raise generation.GenerationCancelled
        return kwargs["paths"]

    def unavailable(*_args):
        raise OSError("injected cleanup error")

    def cancelled(*_args):
        raise generation.GenerationCancelled

    monkeypatch.setattr(generation, "_invoke_plugin", author)
    monkeypatch.setattr(generation, "finalize_generated_documents", publish)
    if cleanup == "retire_error":
        monkeypatch.setattr(generation, "retire_checkpoint", unavailable)
    elif cleanup == "receipt_error":
        monkeypatch.setattr(generation, "checkpoint_receipt", unavailable)
    elif cleanup == "retire_cancelled":
        monkeypatch.setattr(generation, "retire_checkpoint", cancelled)
    elif cleanup == "retire_sync_error":
        original_sync = checkpoints._sync_directory

        def sync_after_removal(directory):
            if not path.exists():
                raise OSError("injected directory sync failure after retirement")
            original_sync(directory)

        monkeypatch.setattr(checkpoints, "_sync_directory", sync_after_removal)
    result = generation.handle_generate(request)
    if cleanup in {"publication_failure", "publication_cancelled"}:
        assert result == (130 if cleanup == "publication_cancelled" else 1)
        assert not emitted
        assert path.exists()
    else:
        assert result == 0
        assert len(emitted) == 1
        assert path.exists() == (cleanup not in {"unchanged", "retire_sync_error"})
        assert any(
            fields.get("stage") == "checkpoint_cleanup" for _, fields in events
        ) == (cleanup != "unchanged")
        if cleanup == "retire_sync_error":
            assert all("retained" not in message for message, _ in events)
    with checkpoints.checkpoint_job_lease(path):
        pass


@pytest.mark.parametrize(
    "outcome",
    [
        "changed",
        "read_error",
        "retire_error",
        "sync_error",
        "postcommit_cancel",
        "unchanged",
        "precommit_cancel",
    ],
)
def test_actual_json_protocol_finishes_after_checkpoint_maintenance(
    tmp_path, monkeypatch, capsys, outcome
):
    from Backend.Core import generation

    request = _request(tmp_path)
    checkpoint = generation.checkpoint_path_for_job(request, tmp_path)
    destination = tmp_path / "question-paper.pdf"
    content = b"Publication fixture bytes, not a PDF validation claim."

    def author(_capability, _request, staging, **_kwargs):
        AssessmentCheckpointStore(checkpoint, identity()).save_payload(
            "accepted", {"value": 1}
        )
        source = staging / destination.name
        source.write_bytes(content)
        return {"question_paper": source}

    def publish(**kwargs):
        if outcome == "precommit_cancel":
            raise generation.GenerationCancelled
        kwargs["paths"]["question_paper"].replace(destination)
        if outcome == "changed":
            AssessmentCheckpointStore(checkpoint, identity()).save_payload(
                "later", {"value": 2}
            )
        return {"question_paper": destination}

    def unavailable(*_args):
        raise OSError("injected checkpoint maintenance failure")

    def cancelled(*_args):
        raise generation.GenerationCancelled

    monkeypatch.setattr(generation, "_invoke_plugin", author)
    monkeypatch.setattr(generation, "finalize_generated_documents", publish)
    if outcome == "read_error":
        monkeypatch.setattr(generation, "checkpoint_receipt", unavailable)
    elif outcome == "retire_error":
        monkeypatch.setattr(generation, "retire_checkpoint", unavailable)
    elif outcome == "postcommit_cancel":
        monkeypatch.setattr(generation, "retire_checkpoint", cancelled)
    elif outcome == "sync_error":
        original_sync = checkpoints._sync_directory

        def fail_after_retirement(directory):
            if not checkpoint.exists():
                raise OSError("injected retirement sync failure")
            original_sync(directory)

        monkeypatch.setattr(checkpoints, "_sync_directory", fail_after_retirement)

    result = generation.handle_generate(request)
    # Capture actual emit_generated_files/emit_progress JSON, not mocked events.
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert not any(event["type"] == "error" for event in events)
    if outcome == "precommit_cancel":
        assert result == 130
        assert not destination.exists()
        assert not any(event["type"] in {"file", "done"} for event in events)
        assert events[-1]["stage"] == "cancel"
        return
    assert result == 0
    assert destination.read_bytes() == content
    assert events[-1]["type"] == "done"
    assert sum(event["type"] == "done" for event in events) == 1
    files = [event for event in events if event["type"] == "file"]
    assert len(files) == 1
    assert Path(files[0]["path"]).read_bytes() == content
    cleanup = [
        index
        for index, event in enumerate(events)
        if event.get("stage") == "checkpoint_cleanup"
    ]
    assert bool(cleanup) == (outcome != "unchanged")
    if cleanup:
        assert cleanup[0] < next(
            index for index, event in enumerate(events) if event["type"] == "file"
        )
