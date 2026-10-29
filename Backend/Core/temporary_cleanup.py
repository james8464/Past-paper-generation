"""Remove an owned failed temporary without hiding its original failure."""

from pathlib import Path


def remove_failed_temporary(path: Path, original_error: BaseException) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanup_error:
        original_error.add_note(f"Temporary cleanup failed for {path}: {cleanup_error}")
