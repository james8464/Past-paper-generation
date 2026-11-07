"""Remove an owned failed temporary without hiding its original failure."""

import shutil
from pathlib import Path


def remove_failed_temporary(path: Path, original_error: BaseException) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanup_error:
        original_error.add_note(f"Temporary cleanup failed for {path}: {cleanup_error}")


def remove_owned_staging(path: Path) -> None:
    """Remove caller-owned staging; only an absent root needs no cleanup."""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        try:
            path.lstat()
        except FileNotFoundError:
            return
        # A missing descendant is not the same as an already-removed root.
        raise
