from __future__ import annotations

import csv
import json
import os
import re
import shutil
import tempfile
import uuid
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from Backend.Core.psychometrics import (
    Response,
    calibrate_responses,
    evidence_fingerprint,
)

SCHEMA_VERSION = 1
ALLOWED_COLUMNS = {
    "candidate_id",
    "item_id",
    "score",
    "max_score",
    "time_seconds",
    "group",
    "marker_id",
    "specification_version",
}
DIRECT_IDENTIFIER_COLUMNS = {
    "name",
    "candidate_name",
    "email",
    "phone",
    "address",
    "date_of_birth",
    "dob",
    "school_id",
}
PSEUDONYM_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}\Z")


@dataclass(frozen=True)
class CalibrationMetadata:
    family: str
    paper: str
    form_id: str
    specification_version: str
    source: str
    collector_role: str
    collected_at: str
    consent_basis: str

    def validate(self) -> None:
        for field, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"calibration provenance requires {field}")


@dataclass(frozen=True)
class ConsentRecord:
    candidate_id: str
    consented: bool
    recorded_at: str
    provenance: str

    def validate(self) -> None:
        _validate_pseudonym(self.candidate_id)
        if self.consented is not True:
            raise ValueError(f"candidate {self.candidate_id} has not consented")
        if not self.recorded_at.strip() or not self.provenance.strip():
            raise ValueError("consent records require date and provenance")


class CalibrationStore:
    """Encrypted local storage for row-level calibration evidence.

    Keys are deliberately supplied by the caller so a macOS client can keep
    them in Keychain. Dataset files contain only authenticated ciphertext;
    aggregate reports never contain candidate or marker identifiers.
    """

    def __init__(self, root: Path, *, key: bytes | str) -> None:
        self.root = root
        encoded_key = key.encode("ascii") if isinstance(key, str) else key
        try:
            self._cipher = Fernet(encoded_key)
        except (TypeError, ValueError) as error:
            raise ValueError("calibration encryption key is invalid") from error
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

    def import_csv(
        self,
        path: Path,
        *,
        metadata: CalibrationMetadata,
        consents: Iterable[ConsentRecord],
    ) -> str:
        metadata.validate()
        consent_records = list(consents)
        consent_by_candidate: dict[str, ConsentRecord] = {}
        for record in consent_records:
            record.validate()
            if record.candidate_id in consent_by_candidate:
                raise ValueError(f"duplicate consent for {record.candidate_id}")
            consent_by_candidate[record.candidate_id] = record

        rows = _read_rows(path, metadata=metadata)
        candidates = {str(row["candidate_id"]) for row in rows}
        missing_consent = candidates - set(consent_by_candidate)
        if missing_consent:
            raise ValueError(
                "missing consent for candidate pseudonyms: "
                + ", ".join(sorted(missing_consent))
            )

        dataset_id = str(uuid.uuid4())
        document = {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "metadata": asdict(metadata),
            "consents": [asdict(consent_by_candidate[value]) for value in sorted(candidates)],
            "responses": rows,
        }
        plaintext = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._atomic_write(self.dataset_path(dataset_id), self._cipher.encrypt(plaintext))
        return dataset_id

    def aggregate(
        self,
        dataset_id: str,
        *,
        review: dict[str, Any] | None = None,
        policy_path: Path | None = None,
    ) -> dict[str, Any]:
        document = self._load(dataset_id)
        metadata = CalibrationMetadata(**document["metadata"])
        responses = [Response(**row) for row in document["responses"]]
        report = calibrate_responses(
            responses,
            family=metadata.family,
            paper=metadata.paper,
            form_id=metadata.form_id,
            review=review,
            policy_path=policy_path,
        )
        report["provenance"] = {
            "source": metadata.source,
            "collector_role": metadata.collector_role,
            "collected_at": metadata.collected_at,
            "consent_basis": metadata.consent_basis,
            "specification_version": metadata.specification_version,
            "dataset_id": dataset_id,
            "row_level_data": "encrypted-local-only",
        }
        report.pop("evidence_fingerprint", None)
        report["evidence_fingerprint"] = evidence_fingerprint(report)
        return report

    def require_empirical_qualification(
        self,
        dataset_id: str,
        *,
        review: dict[str, Any] | None = None,
        policy_path: Path | None = None,
    ) -> dict[str, Any]:
        report = self.aggregate(
            dataset_id,
            review=review,
            policy_path=policy_path,
        )
        if report["difficulty_independently_verified"] is not True:
            failed = [name for name, passed in report["checks"].items() if not passed]
            raise ValueError(
                "insufficient evidence for empirical qualification: "
                + ", ".join(failed)
            )
        return report

    def export_encrypted(self, dataset_id: str, destination: Path) -> Path:
        source = self.dataset_path(dataset_id)
        if not source.is_file():
            raise FileNotFoundError(f"calibration dataset {dataset_id} does not exist")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
        return destination

    def delete(self, dataset_id: str) -> bool:
        path = self.dataset_path(dataset_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def dataset_path(self, dataset_id: str) -> Path:
        try:
            canonical = str(uuid.UUID(dataset_id))
        except (ValueError, AttributeError) as error:
            raise ValueError("calibration dataset id is invalid") from error
        return self.root / f"{canonical}.pcal"

    def _load(self, dataset_id: str) -> dict[str, Any]:
        path = self.dataset_path(dataset_id)
        try:
            plaintext = self._cipher.decrypt(path.read_bytes())
        except InvalidToken as error:
            raise ValueError(
                "could not decrypt calibration dataset with the supplied key"
            ) from error
        document = json.loads(plaintext)
        if (
            not isinstance(document, dict)
            or document.get("schema_version") != SCHEMA_VERSION
            or document.get("dataset_id") != dataset_id
        ):
            raise ValueError("calibration dataset schema or identity is invalid")
        if not isinstance(document.get("responses"), list):
            raise TypeError("calibration dataset has no responses")
        return document

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def _read_rows(path: Path, *, metadata: CalibrationMetadata) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or ())
        direct = columns & DIRECT_IDENTIFIER_COLUMNS
        unsupported = columns - ALLOWED_COLUMNS
        if direct or unsupported:
            names = sorted(direct | unsupported)
            raise ValueError(
                "direct identifier or unsupported column: " + ", ".join(names)
            )
        required = {
            "candidate_id",
            "item_id",
            "score",
            "max_score",
            "specification_version",
        }
        if missing := required - columns:
            raise ValueError("response CSV is missing columns: " + ", ".join(sorted(missing)))
        rows = [
            _normalise_row(row, row_number=index, metadata=metadata)
            for index, row in enumerate(reader, 2)
        ]
    if not rows:
        raise ValueError("response CSV contains no response rows")
    identities: set[tuple[str, str, str | None]] = set()
    for row in rows:
        identity = (row["candidate_id"], row["item_id"], row["marker_id"])
        if identity in identities:
            raise ValueError(
                "duplicate candidate/item/marker response: " + "/".join(filter(None, identity))
            )
        identities.add(identity)
    return rows


def _normalise_row(
    row: dict[str, str],
    *,
    row_number: int,
    metadata: CalibrationMetadata,
) -> dict[str, Any]:
    candidate_id = (row.get("candidate_id") or "").strip()
    item_id = (row.get("item_id") or "").strip()
    _validate_pseudonym(candidate_id)
    if not item_id:
        raise ValueError(f"response row {row_number} has a blank item id")
    specification = (row.get("specification_version") or "").strip()
    if specification != metadata.specification_version:
        raise ValueError(
            f"response row {row_number} uses specification {specification!r}; "
            f"expected {metadata.specification_version!r}"
        )
    try:
        score = float(row["score"])
        max_score = float(row["max_score"])
        raw_time = (row.get("time_seconds") or "").strip()
        time_seconds = float(raw_time) if raw_time else None
    except (TypeError, ValueError) as error:
        raise ValueError(f"response row {row_number} has non-numeric values") from error
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError(f"response row {row_number} has an invalid score range")
    if time_seconds is not None and time_seconds <= 0:
        raise ValueError(f"response row {row_number} has invalid timing")
    return {
        "candidate_id": candidate_id,
        "item_id": item_id,
        "score": score,
        "max_score": max_score,
        "time_seconds": time_seconds,
        "group": (row.get("group") or "").strip() or None,
        "marker_id": (row.get("marker_id") or "").strip() or None,
    }


def _validate_pseudonym(value: str) -> None:
    if not PSEUDONYM_PATTERN.fullmatch(value) or "@" in value:
        raise ValueError(
            "candidate_id must be a non-identifying pseudonym of 3-64 safe characters"
        )
