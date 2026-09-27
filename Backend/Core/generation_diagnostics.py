"""Private, bounded evidence for rejected generation; never approved checkpoints."""

from __future__ import annotations

import json
import os
import re
import stat
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class GenerationEvidenceError(ValueError):
    def __init__(self, message: str, *, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details


def _bounded(value: Any, secrets: tuple[str, ...], depth: int = 0) -> Any:
    if depth > 5:
        return "[depth limit]"
    if isinstance(value, dict):
        return {
            str(_bounded(str(key), secrets)): _bounded(child, secrets, depth + 1)
            for key, child in list(value.items())[:24]
        }
    if isinstance(value, (list, tuple)):
        return [_bounded(child, secrets, depth + 1) for child in value[:24]]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:2048]


def save_failure_diagnostic(
    output_dir: Path,
    error: BaseException,
    *,
    secrets: tuple[str, ...] = (),
    context: dict[str, Any] | None = None,
) -> Path | None:
    """Save only explicitly supplied evidence, not arbitrary errors or prompts.

    Failure to save must never mask the original generation failure. Directory
    descriptors prevent a replaced/symlinked report folder redirecting writes.
    """
    seen: set[int] = set()
    while not isinstance(error, GenerationEvidenceError):
        if id(error) in seen or len(seen) >= 16:
            return None
        seen.add(id(error))
        next_error = error.__cause__ or error.__context__
        if next_error is None:
            return None
        error = next_error
    details = _bounded(error.details, secrets)
    encoded_details = json.dumps(details, ensure_ascii=True)
    if len(encoded_details) > 24_000:
        details = {"excerpt": encoded_details[:8000], "truncated": True}
    record = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "context": _bounded(context or {}, secrets),
        "details": details,
    }
    payload = json.dumps(record, ensure_ascii=True, indent=2).encode()
    if len(payload) > 32_768:
        return None
    directory = output_dir / ".papercreator-diagnostics"
    descriptor = None
    try:
        directory.mkdir(mode=0o700, exist_ok=True)
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        os.fchmod(descriptor, 0o700)
        filename = f"failure-{time.time_ns()}-{uuid.uuid4().hex}.json"
        fd = os.open(
            filename,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=descriptor,
        )
        with os.fdopen(fd, "wb") as report:
            report.write(payload)
        reports = []
        for name in os.listdir(descriptor):
            if re.fullmatch(r"failure-\d+-[0-9a-f]{32}\.json", name):
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISREG(info.st_mode):
                    reports.append((info.st_mtime_ns, name))
        for _, name in sorted(reports)[:-20]:
            os.unlink(name, dir_fd=descriptor)
        return directory / filename
    except OSError:
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)
