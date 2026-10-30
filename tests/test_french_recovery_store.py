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
