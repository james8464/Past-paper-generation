"""Separate CLI jobs must not interleave one output folder's commit or rollback."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from Backend.Core import generation


def document_set(root, name):
    stage = root / name
    stage.mkdir()
    paths = {
        "question_paper": stage / "question.pdf",
        "mark_scheme": stage / "scheme.pdf",
        "package_manifest": stage / "manifest.json",
    }
    for role, path in paths.items():
        path.write_bytes(f"{name}:{role}".encode())
    return paths


@pytest.mark.parametrize("first_fails", [False, True])
def test_separate_jobs_cannot_mix_success_or_rollback_over_a_success(
    tmp_path, monkeypatch, first_fails
):
    output = tmp_path / "output"
    output.mkdir()
    first = document_set(tmp_path, "first")
    second = document_set(tmp_path, "second")
    for path in first.values():
        (output / path.name).write_bytes(b"original")
    first_written, release_first = Event(), Event()
    second_started, second_entered = Event(), Event()
    publish = generation._atomic_publish

    def controlled_publish(source, destination):
        result = publish(source, destination)
        if source == first["question_paper"]:
            first_written.set()
            assert release_first.wait(5), "first publication was not released"
            if first_fails:
                raise OSError("owned first-commit failure")
        if source.parent == second["question_paper"].parent:
            second_entered.set()
        return result

    def second_job():
        second_started.set()
        return generation._publish_document_set(second, output)

    monkeypatch.setattr(generation, "_atomic_publish", controlled_publish)
    with ThreadPoolExecutor(max_workers=2) as workers:
        first_job = workers.submit(generation._publish_document_set, first, output)
        try:
            assert first_written.wait(3)
            later_job = workers.submit(second_job)
            assert second_started.wait(3)
            entered_while_first_pending = second_entered.wait(0.15)
            if entered_while_first_pending:
                # On the old implementation this forces the successful second
                # commit to finish before the first resumes or rolls back.
                later_job.result(timeout=3)
        finally:
            release_first.set()
        if first_fails:
            with pytest.raises(OSError, match="owned first-commit failure"):
                first_job.result(timeout=3)
        else:
            first_job.result(timeout=3)
        later_job.result(timeout=3)
    for role, path in second.items():
        assert (output / path.name).read_bytes() == f"second:{role}".encode()
    assert not entered_while_first_pending, (
        "a second commit entered the owned transaction"
    )
    assert not list(output.glob(".keldin-publish-*"))


def test_distinct_output_roots_publish_independently(tmp_path):
    occupied, independent = tmp_path / "occupied", tmp_path / "independent"
    occupied.mkdir()
    independent.mkdir()
    paths = document_set(tmp_path, "independent-stage")
    with generation._publication_lease(occupied):
        published = generation._publish_document_set(paths, independent)
    assert all(path.is_file() for path in published.values())
    assert not list(occupied.glob("*.pdf"))


@pytest.mark.parametrize("alias", [False, True])
def test_busy_output_wait_has_a_deadline_and_preserves_sources(tmp_path, alias):
    output = tmp_path / "output"
    output.mkdir()
    target = output
    if alias:
        target = tmp_path / "alias"
        target.symlink_to(output, target_is_directory=True)
    paths = document_set(tmp_path, "stage")
    before = {role: path.read_bytes() for role, path in paths.items()}
    with (
        generation._publication_lease(output),
        pytest.raises(generation.CheckpointBusy, match="Another paper is being saved"),
        generation._publication_lease(target, timeout_seconds=0),
    ):
        pytest.fail("busy publication was admitted")
    assert {role: path.read_bytes() for role, path in paths.items()} == before
    assert not list(output.glob("*.pdf"))


def test_cancelled_wait_does_not_enter_publication_or_remove_lock(
    tmp_path, monkeypatch
):
    output = tmp_path / "output"
    output.mkdir()
    cancelled = generation.GenerationCancelled()
    waits = []

    def cancel(delay):
        waits.append(delay)
        raise cancelled

    monkeypatch.setattr(generation.time, "sleep", cancel)
    with generation._publication_lease(output):
        lock = output / ".keldin-checkpoints" / "publication.job.lock"
        inode = lock.stat().st_ino
        with (
            pytest.raises(generation.GenerationCancelled) as failure,
            generation._publication_lease(output),
        ):
            pytest.fail("cancelled waiter acquired publication")
        assert failure.value is cancelled
        assert lock.stat().st_ino == inode
    with generation._publication_lease(output):
        assert lock.stat().st_ino == inode
    assert waits == [0.05]


def test_busy_error_from_owned_body_is_not_retried(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(
        generation.time, "sleep", lambda _: pytest.fail("owned body was retried")
    )
    with (
        pytest.raises(generation.CheckpointBusy, match="owned body"),
        generation._publication_lease(output),
    ):
        raise generation.CheckpointBusy("owned body")


def test_separate_process_cannot_publish_through_an_occupied_output_lease(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    paths = document_set(tmp_path, "stage")
    script = """
import sys
from pathlib import Path
from Backend.Core import generation
output, stage = map(Path, sys.argv[1:])
original = generation._publication_lease
generation._publication_lease = lambda root: original(root, timeout_seconds=0.1)
paths = {role: stage / filename for role, filename in (
    ('question_paper', 'question.pdf'), ('mark_scheme', 'scheme.pdf'),
    ('package_manifest', 'manifest.json'))}
try:
    generation._publish_document_set(paths, output)
except generation.CheckpointBusy:
    print('BLOCKED')
else:
    print('PUBLISHED')
"""

    def child():
        return subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(output),
                str(next(iter(paths.values())).parent),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )

    with generation._publication_lease(output):
        assert child().stdout.strip() == "BLOCKED"
        assert not list(output.glob("*.pdf"))
        assert all(path.is_file() for path in paths.values())
    assert child().stdout.strip() == "PUBLISHED"
    assert all((output / path.name).is_file() for path in paths.values())
