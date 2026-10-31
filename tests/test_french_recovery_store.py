import hashlib
import json
import os
import stat
from types import SimpleNamespace

import pytest

from Backend.Core.france import recovery_evidence as subject


def job(tmp_path):
    directory = tmp_path / "private-job"
    directory.mkdir(mode=0o700)
    return directory


def test_complete_snapshot_is_published_with_private_permissions(tmp_path):
    directory = job(tmp_path)
    snapshot = {"rounds": [{"outcome": "rejected", "text": "é" * 9000}]}
    path = subject.save_recovery_evidence(directory, snapshot)
    record = json.loads(path.read_text())
    assert record["snapshot"] == snapshot
    assert record["kind"] == "french_recovery_evidence"
    assert record["approval"] == "not_assessed"
    canonical = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    assert record["snapshot_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert list(path.parent.iterdir()) == [path]


def test_each_snapshot_preserves_earlier_files(tmp_path):
    directory = job(tmp_path)
    first = subject.save_recovery_evidence(directory, {"rounds": [1]})
    before = first.read_bytes()
    second = subject.save_recovery_evidence(directory, {"rounds": [1, 2]})
    assert first != second
    assert first.read_bytes() == before
    assert json.loads(second.read_bytes())["snapshot"] == {"rounds": [1, 2]}


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_snapshot_creates_no_evidence_files(tmp_path, number):
    directory = job(tmp_path)
    with pytest.raises(ValueError):
        subject.save_recovery_evidence(directory, {"value": number})
    assert list(directory.iterdir()) == []


def test_size_bound_counts_utf8_bytes_before_writing(tmp_path, monkeypatch):
    directory = job(tmp_path)
    monkeypatch.setattr(subject, "MAX_EVIDENCE_BYTES", 1024)
    with pytest.raises(ValueError, match="size"):
        subject.save_recovery_evidence(directory, {"text": "é" * 800})
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize(
    "secret", ['key-"quoted"', "key-\\escaped", "key-\nline", "clé-privée"]
)
@pytest.mark.parametrize("in_key", [False, True])
def test_configured_credentials_are_not_persisted(tmp_path, secret, in_key):
    directory = job(tmp_path)
    value = {secret: "value"} if in_key else {"text": f"prefix {secret} suffix"}
    with pytest.raises(ValueError, match="credential") as caught:
        subject.save_recovery_evidence(directory, value, secrets=(secret,))
    assert secret not in str(caught.value)
    assert list(directory.iterdir()) == []


def test_symlinked_evidence_folder_is_refused(tmp_path):
    directory = job(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (directory / ".keldin-recovery").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        subject.save_recovery_evidence(directory, {"rounds": []})
    assert list(outside.iterdir()) == []


def test_symlinked_job_root_is_refused(tmp_path):
    outside = job(tmp_path)
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        subject.save_recovery_evidence(linked, {"rounds": []})
    assert list(outside.iterdir()) == []


def test_failed_publication_preserves_previous_evidence(tmp_path, monkeypatch):
    directory = job(tmp_path)
    first = subject.save_recovery_evidence(directory, {"rounds": [1]})
    before = first.read_bytes()

    def fail(*args, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(OSError, match="disk failure"):
        subject.save_recovery_evidence(directory, {"rounds": [1, 2]})
    assert first.read_bytes() == before
    assert list(first.parent.iterdir()) == [first]


def test_publication_collision_never_replaces_an_earlier_snapshot(
    tmp_path, monkeypatch
):
    directory = job(tmp_path)
    monkeypatch.setattr(subject.uuid, "uuid4", lambda: SimpleNamespace(hex="0" * 32))
    first = subject.save_recovery_evidence(directory, {"rounds": [1]})
    before = first.read_bytes()
    with pytest.raises(FileExistsError):
        subject.save_recovery_evidence(directory, {"rounds": [1, 2]})
    assert first.read_bytes() == before
    assert list(first.parent.iterdir()) == [first]


def test_temporary_collision_is_not_unlinked_or_overwritten(tmp_path, monkeypatch):
    directory = job(tmp_path)
    folder = directory / ".keldin-recovery"
    folder.mkdir(mode=0o700)
    existing = folder / f".recovery-{'0' * 32}.json.tmp"
    existing.write_text("retain")
    monkeypatch.setattr(subject.uuid, "uuid4", lambda: SimpleNamespace(hex="0" * 32))
    with pytest.raises(FileExistsError):
        subject.save_recovery_evidence(directory, {"rounds": []})
    assert existing.read_text() == "retain"
    assert list(folder.iterdir()) == [existing]


def test_partial_write_failure_leaves_no_published_or_temporary_file(
    tmp_path, monkeypatch
):
    directory = job(tmp_path)
    write = os.write
    calls = 0

    def partial_then_fail(descriptor, data):
        nonlocal calls
        calls += 1
        if calls == 1:
            return write(descriptor, data[:10])
        raise OSError("write failure")

    monkeypatch.setattr(os, "write", partial_then_fail)
    with pytest.raises(OSError, match="write failure"):
        subject.save_recovery_evidence(directory, {"rounds": [1]})
    assert list((directory / ".keldin-recovery").iterdir()) == []


def test_success_syncs_the_file_and_both_directory_entries(tmp_path, monkeypatch):
    directory = job(tmp_path)
    sync = os.fsync
    synced = []

    def recording_sync(descriptor):
        synced.append(os.fstat(descriptor).st_mode)
        sync(descriptor)

    monkeypatch.setattr(os, "fsync", recording_sync)
    subject.save_recovery_evidence(directory, {"rounds": []})
    assert sum(stat.S_ISREG(mode) for mode in synced) == 1
    assert sum(stat.S_ISDIR(mode) for mode in synced) == 2


def test_directory_sync_failure_is_not_reported_as_saved(tmp_path, monkeypatch):
    directory = job(tmp_path)
    sync = os.fsync

    def fail_directory_sync(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("directory sync failure")
        sync(descriptor)

    monkeypatch.setattr(os, "fsync", fail_directory_sync)
    with pytest.raises(OSError, match="directory sync failure"):
        subject.save_recovery_evidence(directory, {"rounds": []})
    assert list((directory / ".keldin-recovery").iterdir()) == []


@pytest.mark.parametrize("replace_root", [False, True])
def test_renamed_directory_cannot_return_a_false_saved_path(
    tmp_path, monkeypatch, replace_root
):
    directory = job(tmp_path)
    moved = tmp_path / "moved"
    outside = tmp_path / "outside"
    outside.mkdir()
    link = os.link

    def change_visible_path(*args, **kwargs):
        link(*args, **kwargs)
        if replace_root:
            directory.rename(moved)
            directory.mkdir()
        else:
            (directory / ".keldin-recovery").rename(moved)
            (directory / ".keldin-recovery").symlink_to(
                outside, target_is_directory=True
            )

    monkeypatch.setattr(os, "link", change_visible_path)
    with pytest.raises(OSError, match="changed"):
        subject.save_recovery_evidence(directory, {"rounds": []})
    assert list(outside.iterdir()) == []
    evidence_folder = moved / ".keldin-recovery" if replace_root else moved
    assert list(evidence_folder.iterdir()) == []


def test_filename_failure_opens_no_descriptors(tmp_path, monkeypatch):
    directory = job(tmp_path)
    opened = []

    def fail_uuid():
        raise RuntimeError("entropy failure")

    def unexpected_open(*args, **kwargs):
        opened.append(args)
        raise AssertionError("descriptor opened too early")

    monkeypatch.setattr(subject.uuid, "uuid4", fail_uuid)
    monkeypatch.setattr(os, "open", unexpected_open)
    with pytest.raises(RuntimeError, match="entropy failure"):
        subject.save_recovery_evidence(directory, {"rounds": []})
    assert not opened


def cumulative(rounds):
    return {
        "review_recovery_policy": "test-policy",
        "recovery_identity": {"implementation_sha256": "a" * 64, "seed": 42},
        "curriculum_plan": [{"exercise_id": "1"}],
        "teacher_review": "not_run",
        "empirical_calibration": "not_run",
        "exercise_attempts": [
            {
                "exercise_id": "1",
                "accepted_round": None,
                "rounds": [{"number": value} for value in rounds],
            }
        ],
    }


def test_cumulative_recorder_keeps_newest_with_all_earlier_rounds(tmp_path):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    second = recorder(cumulative([1, 2]))
    assert not first.exists()
    assert list(second.parent.iterdir()) == [second]
    assert json.loads(second.read_bytes())["snapshot"] == cumulative([1, 2])
    assert recorder.retention_warning is None


@pytest.mark.parametrize("change", ["round", "identity", "policy", "plan"])
def test_changed_prefix_or_identity_preserves_prior(tmp_path, change):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    before = first.read_bytes()
    changed = cumulative([1, 2])
    if change == "round":
        changed["exercise_attempts"][0]["rounds"][0]["number"] = 9
    elif change == "identity":
        changed["recovery_identity"]["seed"] = 43
    elif change == "policy":
        changed["review_recovery_policy"] = "other"
    else:
        changed["curriculum_plan"] = []
    with pytest.raises(ValueError, match="extend"):
        recorder(changed)
    assert first.read_bytes() == before
    assert list(first.parent.iterdir()) == [first]


def test_new_save_failure_preserves_prior_snapshot(tmp_path, monkeypatch):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    before = first.read_bytes()
    monkeypatch.setattr(
        subject,
        "save_recovery_evidence",
        lambda *a, **k: (_ for _ in ()).throw(OSError("write failure")),
    )
    with pytest.raises(OSError, match="write failure"):
        recorder(cumulative([1, 2]))
    assert first.read_bytes() == before


def test_cleanup_failure_keeps_new_snapshot_and_warns(tmp_path, monkeypatch):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    unlink = os.unlink

    def fail_previous(name, **kwargs):
        if name == first.name:
            raise OSError("retirement failure")
        return unlink(name, **kwargs)

    monkeypatch.setattr(os, "unlink", fail_previous)
    second = recorder(cumulative([1, 2]))
    assert first.exists() and second.exists()
    assert recorder.retention_warning
    assert first.name not in recorder.retention_warning


@pytest.mark.parametrize("symlink", [False, True])
def test_replaced_prior_file_is_never_retired(tmp_path, symlink):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    first.unlink()
    outside = tmp_path / "outside"
    outside.write_text("retain")
    if symlink:
        first.symlink_to(outside)
    else:
        first.write_text("replacement")
    second = recorder(cumulative([1, 2]))
    assert second.exists() and first.exists()
    assert recorder.retention_warning
    assert outside.read_text() == "retain"


def test_partial_stop_and_empty_next_history_keep_completed_rounds(tmp_path):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    stopped = cumulative([1])
    stopped["state"] = "stopped"
    stopped["partial_round"] = {"stage": "blind", "author": {"raw": "retained"}}
    second = recorder(stopped)
    assert not first.exists()
    extended = cumulative([1])
    extended["exercise_attempts"].append(
        {"exercise_id": "2", "accepted_round": None, "rounds": []}
    )
    third = recorder(extended)
    assert not second.exists()
    assert json.loads(third.read_bytes())["snapshot"] == extended


def test_first_partial_round_can_be_saved_without_completed_rounds(tmp_path):
    snapshot = cumulative([])
    snapshot["state"] = "stopped"
    snapshot["partial_round"] = {"stage": "author"}
    path = subject.RecoveryEvidenceRecorder(job(tmp_path))(snapshot)
    assert json.loads(path.read_bytes())["snapshot"] == snapshot


def test_new_directory_sync_failure_preserves_prior_snapshot(tmp_path, monkeypatch):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    before = first.read_bytes()
    sync = os.fsync

    def fail_directory(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("sync failure")
        sync(descriptor)

    monkeypatch.setattr(os, "fsync", fail_directory)
    with pytest.raises(OSError, match="sync failure"):
        recorder(cumulative([1, 2]))
    assert first.read_bytes() == before
    assert list(first.parent.iterdir()) == [first]


def test_foreign_replacement_with_identical_bytes_is_preserved(tmp_path):
    recorder = subject.RecoveryEvidenceRecorder(job(tmp_path))
    first = recorder(cumulative([1]))
    moved = tmp_path / "moved-original"
    first.rename(moved)
    first.write_bytes(moved.read_bytes())
    second = recorder(cumulative([1, 2]))
    assert first.exists() and second.exists() and moved.exists()
    assert recorder.retention_warning
