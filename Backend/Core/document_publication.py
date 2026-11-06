"""Commit a complete document set under one output-folder publication lease."""

import os
import shutil
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from Backend.Core.assessment_checkpoints import CheckpointBusy, checkpoint_job_lease
from Backend.Core.events import emit_progress
from Backend.Core.legacy_migration import output_directory


class GenerationCancelled(Exception):
    pass


def atomic_publish(source: Path, destination: Path) -> Path:
    os.replace(source, destination)
    return destination


@contextmanager
def publication_lease(
    output_dir: Path, *, timeout_seconds: float = 30
) -> Iterator[None]:
    # Different generation identities can still replace the same filenames.
    # Keep one persistent, hidden lock inode for the whole output directory.
    lock_path = (
        output_directory(output_dir.resolve(), ".keldin-checkpoints") / "publication"
    )
    deadline = time.monotonic() + timeout_seconds
    with ExitStack() as stack:
        while True:
            try:
                stack.enter_context(checkpoint_job_lease(lock_path))
                break
            except CheckpointBusy as error:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CheckpointBusy(
                        "Another paper is being saved to this folder. Try again or choose another output folder."
                    ) from error
                # Unlike a blocking flock, bounded waits preserve cancellation
                # and do not wait indefinitely for a stalled publisher.
                time.sleep(min(0.05, remaining))
        yield


def publish_document_set(
    paths: dict[str, Path], output_dir: Path, *, final_publication: bool = True
) -> dict[str, Path]:
    with publication_lease(output_dir):
        return publish_document_set_locked(
            paths, output_dir, final_publication=final_publication
        )


def publish_document_set_locked(
    paths: dict[str, Path],
    output_dir: Path,
    *,
    replace_document: Callable[[Path, Path], Path] | None = None,
    final_publication: bool = True,
) -> dict[str, Path]:
    replace_document = replace_document or atomic_publish
    destinations = {role: output_dir / source.name for role, source in paths.items()}
    if len(set(destinations.values())) != len(destinations):
        raise OSError("Generated document filenames must be distinct")
    for destination in destinations.values():
        if destination.is_symlink() or (
            destination.exists() and not destination.is_file()
        ):
            raise OSError(f"Cannot replace a non-file output: {destination}")

    # Keep old inodes outside render staging so a failed rollback remains recoverable.
    recovery = Path(tempfile.mkdtemp(prefix=".keldin-publish-", dir=output_dir))
    backups: dict[Path, Path] = {}
    attempted: list[Path] = []
    retain_recovery = False
    committed = False
    try:
        for destination in destinations.values():
            if destination.exists():
                backup = recovery / destination.name
                os.link(destination, backup)
                backups[destination] = backup
        published = {}
        try:
            for role, source in paths.items():
                destination = destinations[role]
                attempted.append(destination)
                published[role] = replace_document(source, destination)
        except BaseException as error:
            rollback_errors = []
            for destination in reversed(attempted):
                try:
                    if destination in backups:
                        os.replace(backups[destination], destination)
                    else:
                        destination.unlink(missing_ok=True)
                except BaseException as rollback_error:
                    rollback_errors.append(rollback_error)
            if rollback_errors:
                retain_recovery = True
                raise RuntimeError(
                    f"Publication failed and some previous files could not be restored. "
                    f"Recovery copies remain in {recovery}. Original error: {error}"
                ) from error
            raise
        committed = True
        return published
    finally:
        if not retain_recovery:
            try:
                shutil.rmtree(recovery, ignore_errors=True)
            except GenerationCancelled:
                # A commit into another transaction's staging is not final.
                # Cancellation there must still stop the outer publication.
                if not committed or not final_publication:
                    raise
                emit_progress(
                    f"The paper was saved. Backup cleanup was interrupted; recovery copies may remain in {recovery}.",
                    stage="publication_cleanup",
                )
