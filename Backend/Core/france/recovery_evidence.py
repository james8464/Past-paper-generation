"""Keep complete recovery snapshots inside an existing private job directory."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from contextlib import ExitStack, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_EVIDENCE_BYTES = 32 * 1024 * 1024


def _encode(value: object) -> bytes:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_BYTES:
        raise ValueError("Recovery evidence exceeds its size limit.")
    return encoded


def save_recovery_evidence(
    private_job_directory: Path,
    snapshot: dict[str, Any],
    *,
    secrets: tuple[str, ...] = (),
) -> Path:
    """Store evidence, not approval; the caller must validate its source and policy.

    The caller supplies an existing private job root, never a user export folder.
    Its parent directories belong to the application. Final root and evidence
    folder symlinks are refused; descriptor-relative writes stay in that folder.
    """
    if not private_job_directory.is_absolute():
        raise ValueError(
            "Recovery evidence requires an absolute private job directory."
        )
    canonical = _encode(snapshot)
    record = {
        "schema_version": 1,
        "kind": "french_recovery_evidence",
        "approval": "not_assessed",
        "created_at": datetime.now(UTC).isoformat(),
        "snapshot": json.loads(canonical),
        "snapshot_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    payload = _encode(record)
    text = payload.decode("utf-8")
    if any(
        secret and json.dumps(secret, ensure_ascii=False)[1:-1] in text
        for secret in secrets
    ):
        raise ValueError("Recovery evidence contains a configured credential.")

    name = f"recovery-{uuid.uuid4().hex}.json"
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as descriptors:
        root = os.open(private_job_directory, flags)
        descriptors.callback(os.close, root)
        with suppress(FileExistsError):
            os.mkdir(".keldin-recovery", mode=0o700, dir_fd=root)
        folder = os.open(".keldin-recovery", flags, dir_fd=root)
        descriptors.callback(os.close, folder)
        os.fchmod(folder, 0o700)
        temporary = None
        published = False
        candidate = f".{name}.tmp"
        try:
            descriptor = os.open(
                candidate,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=folder,
            )
            temporary = candidate
            try:
                os.fchmod(descriptor, 0o600)
                remaining = memoryview(payload)
                while remaining:
                    written = os.write(descriptor, remaining)
                    if written <= 0:
                        raise OSError("Recovery evidence write made no progress.")
                    remaining = remaining[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            # Link only the complete, synced file. Unlike replace(), a collision
            # cannot overwrite an earlier snapshot or follow a destination symlink.
            os.link(
                temporary,
                name,
                src_dir_fd=folder,
                dst_dir_fd=folder,
                follow_symlinks=False,
            )
            published = True
            os.unlink(temporary, dir_fd=folder)
            temporary = None
            os.fsync(folder)
            os.fsync(root)
            if not os.path.samestat(
                os.fstat(root), os.stat(private_job_directory, follow_symlinks=False)
            ) or not os.path.samestat(
                os.fstat(folder),
                os.stat(".keldin-recovery", dir_fd=root, follow_symlinks=False),
            ):
                raise OSError("Recovery evidence directory changed during publication.")
            return private_job_directory / ".keldin-recovery" / name
        except BaseException:
            if published:
                os.unlink(name, dir_fd=folder)
            raise
        finally:
            if temporary is not None:
                os.unlink(temporary, dir_fd=folder)
