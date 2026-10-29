"""Publish one complete JSON document without truncating retained evidence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_json_atomically(
    path: Path,
    value: Any,
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> None:
    # Serialize first: unsupported data must not disturb the previous result.
    rendered = (
        json.dumps(value, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as cleanup_error:
            error.add_note(
                f"Temporary JSON cleanup failed for {temporary}: {cleanup_error}"
            )
        raise
