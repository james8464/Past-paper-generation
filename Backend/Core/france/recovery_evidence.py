"""Keep complete recovery snapshots inside an existing private job directory."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from contextlib import ExitStack, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_EVIDENCE_BYTES = 32 * 1024 * 1024


def _ordered_rounds(snapshot: dict[str, Any]) -> list[bytes]:
    histories = snapshot.get("exercise_attempts")
    if not isinstance(histories, list) or not 1 <= len(histories) <= 3:
        raise ValueError("Recovery snapshot must extend ordered exercise rounds.")
    rounds: list[bytes] = []
    for index, history in enumerate(histories, 1):
        if (
            not isinstance(history, dict)
            or history.get("exercise_id") != str(index)
            or not isinstance(history.get("rounds"), list)
            or len(history["rounds"]) > 2
            or (not history["rounds"] and index != len(histories))
        ):
            raise ValueError("Recovery snapshot must extend ordered exercise rounds.")
        rounds.extend(_encode([str(index), record]) for record in history["rounds"])
    return rounds


class RecoveryEvidenceRecorder:
    """Retire only this recorder's previous file after a complete cumulative save."""

    def __init__(self, directory: Path, *, secrets: tuple[str, ...] = ()):
        self.directory = directory
        self.secrets = secrets
        self.retention_warning: str | None = None
        self._previous: tuple[str, bytes, tuple[int, int]] | None = None
        self._snapshot: dict[str, Any] | None = None

    def __call__(self, snapshot: dict[str, Any]) -> Path:
        canonical = _encode(snapshot)
        rounds = _ordered_rounds(snapshot)
        bindings = (
            "review_recovery_policy",
            "recovery_identity",
            "curriculum_plan",
            "teacher_review",
            "empirical_calibration",
        )
        if any(key not in snapshot for key in bindings):
            raise ValueError(
                "Recovery snapshot must extend a declared source identity."
            )
        if self._snapshot is not None:
            before = _ordered_rounds(self._snapshot)
            if (
                len(rounds) < len(before)
                or rounds[: len(before)] != before
                or len(snapshot["exercise_attempts"])
                < len(self._snapshot["exercise_attempts"])
                or any(
                    previous.get("accepted_round") is not None
                    and _encode(previous.get("accepted_round"))
                    != _encode(current.get("accepted_round"))
                    for previous, current in zip(
                        self._snapshot["exercise_attempts"],
                        snapshot["exercise_attempts"],
                        strict=False,
                    )
                )
                or any(
                    key not in snapshot
                    or key not in self._snapshot
                    or _encode(snapshot[key]) != _encode(self._snapshot[key])
                    for key in bindings
                )
            ):
                raise ValueError(
                    "Recovery snapshot must extend its original source and rounds."
                )
        path = save_recovery_evidence(self.directory, snapshot, secrets=self.secrets)
        # Cleanup errors cannot turn a genuinely saved snapshot into a false
        # snapshot_saved=False report. Keep both records and expose a warning.
        ownership = None
        try:
            information = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(information.st_mode):
                raise OSError("Saved recovery evidence changed.")
            ownership = (path.name, canonical, (information.st_dev, information.st_ino))
            self._retire_previous()
        except OSError:
            self.retention_warning = "The latest recovery evidence was saved, but cleanup of earlier records could not be confirmed."
        self._previous = ownership
        self._snapshot = json.loads(canonical)
        return path

    def _retire_previous(self) -> None:
        if self._previous is None:
            return
        name, expected_snapshot, inode = self._previous
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with ExitStack() as descriptors:
            root = os.open(self.directory, flags)
            descriptors.callback(os.close, root)
            folder = os.open(".keldin-recovery", flags, dir_fd=root)
            descriptors.callback(os.close, folder)
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=folder)
            descriptors.callback(os.close, descriptor)
            original = os.fstat(descriptor)
            if (
                not stat.S_ISREG(original.st_mode)
                or (original.st_dev, original.st_ino) != inode
                or original.st_size > MAX_EVIDENCE_BYTES
            ):
                raise OSError("Previous recovery evidence changed.")
            raw = bytearray()
            while chunk := os.read(
                descriptor, min(65536, MAX_EVIDENCE_BYTES + 1 - len(raw))
            ):
                raw.extend(chunk)
                if len(raw) > MAX_EVIDENCE_BYTES:
                    raise OSError("Previous recovery evidence changed.")
            try:
                record = json.loads(raw)
                unchanged = (
                    isinstance(record, dict)
                    and _encode(record.get("snapshot")) == expected_snapshot
                    and record.get("snapshot_sha256")
                    == hashlib.sha256(expected_snapshot).hexdigest()
                )
            except (ValueError, UnicodeDecodeError):
                unchanged = False
            if not unchanged or not os.path.samestat(
                original, os.stat(name, dir_fd=folder, follow_symlinks=False)
            ):
                raise OSError("Previous recovery evidence changed.")
            os.unlink(name, dir_fd=folder)
            os.fsync(folder)


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
