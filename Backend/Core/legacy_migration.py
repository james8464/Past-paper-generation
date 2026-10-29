# Read pre-Keldin settings and copy local data without replacing newer files.

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path

# These spellings are read-only compatibility inputs. New jobs use Keldin names.
LEGACY_ENVIRONMENT_PREFIX = "PAPER_CREATOR_"
LEGACY_OUTPUT_DIRECTORIES = {
    ".keldin-checkpoints": ".papercreator-checkpoints",
    ".keldin-diagnostics": ".papercreator-diagnostics",
}
LEGACY_APP_FOLDER = "Paper creator"
LEGACY_PUBLISHER = "Paper Creator"
LEGACY_V32_ORIGIN = f"{LEGACY_PUBLISHER} application-owned French cases v32".encode()
LEGACY_FRENCH_FOOTER = f"{LEGACY_PUBLISHER} — entraînement non officiel — non relu"


# Prefer a Keldin setting, including an explicitly empty value, over its alias.
def environment_value(
    name: str,
    default: str | None = "",
    *,
    environment: Mapping[str, str] | None = None,
) -> str | None:
    values = os.environ if environment is None else environment
    if name in values:
        return values[name]
    legacy = name.replace("KELDIN_", LEGACY_ENVIRONMENT_PREFIX, 1)
    return values.get(legacy, default)


# Copy ordinary files only; leave both the originals and newer data intact.
def copy_missing_tree(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        return
    if destination.is_symlink():
        raise OSError(f"Migration destination is a symbolic link: {destination}")
    if destination.resolve().is_relative_to(source.resolve()):
        raise OSError("Migration destination must be outside the source tree")
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_symlink() or target.is_symlink():
            continue
        if child.is_dir():
            if not target.exists() or target.is_dir():
                copy_missing_tree(child, target)
        elif child.is_file() and not target.exists():
            # Publish a complete copy without replacing a concurrent writer's file.
            with tempfile.NamedTemporaryFile(
                dir=destination, prefix=".keldin-import-", delete=False
            ) as copied:
                temporary = Path(copied.name)
                try:
                    with child.open("rb") as original:
                        shutil.copyfileobj(original, copied)
                    copied.flush()
                    os.fsync(copied.fileno())
                    with suppress(FileExistsError):
                        os.link(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)


# Import old checkpoints or diagnostics before returning their current folder.
def output_directory(parent: Path, name: str) -> Path:
    target = parent / name
    legacy = LEGACY_OUTPUT_DIRECTORIES.get(name)
    marker = target / ".legacy-import-complete"
    if legacy and not marker.exists() and not marker.is_symlink():
        source = parent / legacy
        if source.is_dir() and not source.is_symlink():
            copy_missing_tree(source, target)
            # A retired checkpoint must not reappear from its preserved original.
            with suppress(FileExistsError), marker.open("xb"):
                pass
    return target
