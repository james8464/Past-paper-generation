# Persist accepted items with the blueprint identity needed to resume them safely.

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from pathlib import Path
from threading import RLock
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from Backend.Core.exam_blueprints import GeneratedQuestion


class CheckpointMismatch(ValueError):
    pass


class CheckpointCorrupt(ValueError):
    pass


class CheckpointBusy(RuntimeError):
    pass


@contextmanager
def _file_lock(path: Path, *, job: bool = False) -> Iterator[Path]:
    # Resolve aliases before choosing a sidecar. Never unlink sidecars: waiters
    # must keep using the same inode, including after a checkpoint is retired.
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".job.lock" if job else ".lock"
    descriptor = os.open(
        path.with_name(path.name + suffix), os.O_CREAT | os.O_RDWR, 0o600
    )
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | (fcntl.LOCK_NB if job else 0))
        except OSError as error:
            if job and error.errno in {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK}:
                raise CheckpointBusy(
                    "This generation job is already running. Wait for it to finish before retrying."
                ) from error
            raise
        yield path
    finally:
        # Closing also releases the lock if cancellation interrupted acquisition.
        os.close(descriptor)


@contextmanager
def checkpoint_job_lease(path: Path) -> Iterator[None]:
    """Own one CLI authoring/publication job on a local macOS/Linux filesystem."""
    with _file_lock(path, job=True):
        yield


def checkpoint_receipt(path: Path) -> str | None:
    with _file_lock(path) as canonical:
        try:
            return hashlib.sha256(canonical.read_bytes()).hexdigest()
        except FileNotFoundError:
            return None


def retire_checkpoint(path: Path, receipt: str | None) -> bool:
    """Retire only the exact checkpoint observed after authoring, not later work."""
    with _file_lock(path) as canonical:
        try:
            current = hashlib.sha256(canonical.read_bytes()).hexdigest()
        except FileNotFoundError:
            return True
        if receipt != current:
            return False
        canonical.unlink()
        _sync_directory(canonical.parent)
        return True


def _sync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class CheckpointIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal[1] = 1
    paper_id: str = Field(min_length=1)
    seed: int = Field(strict=True)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    blueprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_version: str = Field(min_length=1)


def identity_for_blueprint(
    blueprint: Any,
    *,
    provider: str,
    model: str,
    prompt_version: str,
) -> CheckpointIdentity:
    if hasattr(blueprint, "model_dump"):
        payload = blueprint.model_dump(mode="json")
    elif isinstance(blueprint, Mapping):
        payload = dict(blueprint)
    else:
        raise TypeError("checkpoint blueprint must be a Pydantic model or mapping")
    paper_id = str(payload.get("paper_id") or payload.get("id") or "").strip()
    if not paper_id:
        raise ValueError("checkpoint blueprint has no paper identity")
    seed = payload.get("seed")
    if type(seed) is not int:
        raise ValueError("checkpoint blueprint has no integer seed")
    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return CheckpointIdentity(
        paper_id=paper_id,
        seed=seed,
        provider=provider,
        model=model,
        blueprint_sha256=digest,
        prompt_version=prompt_version,
    )


# Persist independently accepted questions without partial JSON writes.
class AssessmentCheckpointStore:
    def __init__(self, path: Path, identity: CheckpointIdentity) -> None:
        self.path = path.resolve()
        self.identity = identity
        self._lock = RLock()
        with self._transaction():
            self._read_document()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        # Consistent order: instance lock, then cross-instance/process file lock.
        with self._lock, _file_lock(self.path):
            yield

    def load_item(self, key: str) -> GeneratedQuestion | None:
        raw = self.load_payload(key)
        if raw is None:
            return None
        try:
            return GeneratedQuestion.model_validate(raw)
        except ValidationError as error:
            raise CheckpointCorrupt(
                f"checkpoint item {key} does not match the question schema"
            ) from error

    def save_item(self, key: str, question: GeneratedQuestion) -> None:
        self.save_payload(key, question.model_dump(mode="json"))

    def load_payload(self, key: str) -> dict[str, Any] | None:
        with self._transaction():
            raw = self._read_document()["items"].get(key)
            if raw is None:
                return None
            if not isinstance(raw, dict):
                raise CheckpointCorrupt(f"checkpoint item {key} is not an object")
            return dict(raw)

    def save_payload(self, key: str, payload: Mapping[str, Any]) -> None:
        with self._transaction():
            document = self._read_document()
            items = document["items"]
            if not isinstance(items, dict):
                raise CheckpointCorrupt("checkpoint item storage is invalid")
            items[key] = dict(payload)
            self._write_document(document)

    def discard_item(self, key: str) -> None:
        with self._transaction():
            document = self._read_document()
            items = document["items"]
            if not isinstance(items, dict):
                raise CheckpointCorrupt("checkpoint item storage is invalid")
            if items.pop(key, None) is not None:
                self._write_document(document)

    def clear(self) -> None:
        with self._transaction():
            self._read_document(allow_blueprint_revision=False)
            self.path.unlink(missing_ok=True)

    def _write_document(self, document: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    document, handle, indent=2, sort_keys=True, ensure_ascii=False
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            _sync_directory(self.path.parent)
        except BaseException:
            # A cleanup fault must not hide the write or cancellation failure.
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise

    def _read_document(
        self, *, allow_blueprint_revision: bool = True
    ) -> dict[str, object]:
        if not self.path.exists():
            return {
                "schema_version": 1,
                "identity": self.identity.model_dump(mode="json"),
                "items": {},
            }
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CheckpointCorrupt(f"checkpoint is unreadable: {self.path}") from error
        if not isinstance(document, dict) or document.get("schema_version") != 1:
            raise CheckpointCorrupt("checkpoint has an unsupported schema version")
        raw_identity = document.get("identity")
        items = document.get("items")
        if not isinstance(raw_identity, dict) or not isinstance(items, dict):
            raise CheckpointCorrupt("checkpoint is missing identity or item data")
        try:
            stored_identity = CheckpointIdentity.model_validate(raw_identity)
        except ValidationError as error:
            raise CheckpointCorrupt("checkpoint identity is invalid") from error
        mismatches = [
            field_name
            for field_name in CheckpointIdentity.model_fields
            if getattr(stored_identity, field_name)
            != getattr(self.identity, field_name)
        ]
        if mismatches == ["blueprint_sha256"] and allow_blueprint_revision:
            # Retain expensive accepted items across a blueprint revision. Every
            # caller revalidates each payload against the current immutable item
            # contract before it is allowed back into the paper.
            document["identity"] = self.identity.model_dump(mode="json")
            self._write_document(document)
        elif mismatches:
            raise CheckpointMismatch(
                f"checkpoint {mismatches[0]} does not match this generation job"
            )
        return document
