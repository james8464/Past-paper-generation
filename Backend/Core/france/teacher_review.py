"""Self-attested human review records; hashes bind scope, not reviewer credentials."""

import json
import os
import tempfile
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from Backend.Core.france.pipeline import digest

RUBRIC = frozenset(
    {
        "correctness",
        "curriculum",
        "language",
        "difficulty",
        "timing",
        "marking",
        "layout",
        "originality",
    }
)


def artifact_identity(manifest: Path) -> dict:
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Manifest has no artifacts")
    for entry in artifacts.values():
        name = entry["file"]
        if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
            raise ValueError("Unsafe artifact path")
        path = manifest.parent / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Artifact missing or redirected")
        if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Artifact hash changed")
    return {
        "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
        "artifacts": artifacts,
    }


def record_review(
    manifest: Path, *, reviewer: str, decision: str, scores: dict, notes: str
) -> dict:
    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
        or decision not in {"approved", "revise", "rejected"}
    ):
        raise ValueError("Named human reviewer and explicit decision required")
    if set(scores) != RUBRIC or any(
        type(value) is not int or not 1 <= value <= 4 for value in scores.values()
    ):
        raise ValueError("Complete rubric scores from 1 to 4 required")
    if decision == "approved" and (
        min(scores.values()) < 3 or scores["correctness"] != 4 or scores["marking"] != 4
    ):
        raise ValueError("Unresolved correctness or marking issues prevent approval")
    if not isinstance(notes, str) or not notes.strip():
        raise ValueError("Human review notes required")
    return {
        "schema_version": 1,
        "identity": artifact_identity(manifest),
        "reviewer": reviewer.strip(),
        "credential_status": "self_attested_not_verified",
        "decision": decision,
        "scores": scores,
        "notes": notes,
        "created_at": datetime.now(UTC).isoformat(),
        "record_id": digest([reviewer.strip(), decision, scores, notes]),
    }


def review_status(manifest: Path, record: dict) -> str:
    try:
        if record.get("schema_version") != 1 or record.get(
            "identity"
        ) != artifact_identity(manifest):
            return "stale"
        # Reapply the same substantive gates; a JSON edit must not bypass them.
        checked = record_review(
            manifest,
            reviewer=record["reviewer"],
            decision=record["decision"],
            scores=record["scores"],
            notes=record["notes"],
        )
        if checked["record_id"] != record.get("record_id"):
            return "stale"
        return record["decision"]
    except (ValueError, OSError, KeyError, TypeError):
        return "stale"


def _write_record(manifest: Path, record: dict) -> Path:
    destination = manifest.parent / f"teacher-review-{record['record_id'][:12]}.json"
    rendered = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    if destination.exists():
        if destination.is_symlink() or destination.read_text(encoding="utf-8") != rendered:
            raise ValueError("Un enregistrement différent utilise déjà cet identifiant")
        return destination
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".teacher-review-", suffix=".json", dir=manifest.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def handle_record_review(args) -> int:
    from Backend.Core.events import emit

    try:
        scores = json.loads(args.scores_json)
        if not isinstance(scores, dict):
            raise ValueError("La grille de relecture doit être un objet JSON")
        record = record_review(
            args.manifest,
            reviewer=args.reviewer,
            decision=args.decision,
            scores=scores,
            notes=args.notes,
        )
        destination = _write_record(args.manifest, record)
        emit("file", role="teacher_review", path=str(destination))
        emit(
            "done",
            message=(
                "Relecture enregistrée et liée aux empreintes des documents. "
                "Toute modification la rend caduque."
            ),
        )
        return 0
    except Exception as error:
        emit("error", message=str(error), code="french_review_failed")
        return 1
