from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from Backend.Core.calibration_store import (
    CalibrationMetadata,
    CalibrationStore,
    ConsentRecord,
)
from Backend.Core.psychometrics import validate_calibration, write_calibration


def _csv(path: Path, *, rows: int = 4, specification: str = "aqa-7136-v1.2") -> Path:
    lines = [
        "candidate_id,item_id,score,max_score,time_seconds,group,marker_id,specification_version"
    ]
    for candidate in range(rows):
        lines.append(
            f"p-{candidate},q1,{candidate % 2},1,60,A,m1,{specification}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _metadata() -> CalibrationMetadata:
    return CalibrationMetadata(
        family="aqa/economics",
        paper="1",
        form_id="form-260826",
        specification_version="aqa-7136-v1.2",
        source="Consented school pilot",
        collector_role="Assessment research lead",
        collected_at="2026-08-26",
        consent_basis="Explicit participant consent with withdrawal route",
    )


def _consents(count: int) -> list[ConsentRecord]:
    return [
        ConsentRecord(
            candidate_id=f"p-{candidate}",
            consented=True,
            recorded_at="2026-08-26",
            provenance="Signed pilot consent register",
        )
        for candidate in range(count)
    ]


def test_store_encrypts_rows_and_exports_only_encrypted_data(tmp_path: Path) -> None:
    store = CalibrationStore(tmp_path / "store", key=Fernet.generate_key())
    dataset_id = store.import_csv(
        _csv(tmp_path / "responses.csv"),
        metadata=_metadata(),
        consents=_consents(4),
    )

    encrypted = store.dataset_path(dataset_id).read_bytes()
    assert b"p-0" not in encrypted
    assert b"candidate_id" not in encrypted
    exported = store.export_encrypted(dataset_id, tmp_path / "export.pcal")
    assert exported.read_bytes() == encrypted


def test_import_rejects_direct_identifiers_and_missing_consent(tmp_path: Path) -> None:
    key = Fernet.generate_key()
    store = CalibrationStore(tmp_path / "store", key=key)
    direct = tmp_path / "direct.csv"
    direct.write_text(
        "candidate_id,candidate_name,item_id,score,max_score,specification_version\n"
        "p-1,Alice,q1,1,1,aqa-7136-v1.2\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"direct identifier|unsupported column"):
        store.import_csv(direct, metadata=_metadata(), consents=_consents(1))

    with pytest.raises(ValueError, match="consent"):
        store.import_csv(
            _csv(tmp_path / "missing-consent.csv"),
            metadata=_metadata(),
            consents=_consents(3),
        )

    missing_provenance = CalibrationMetadata(
        **{**_metadata().__dict__, "source": ""}
    )
    with pytest.raises(ValueError, match="provenance"):
        store.import_csv(
            _csv(tmp_path / "missing-provenance.csv"),
            metadata=missing_provenance,
            consents=_consents(4),
        )


def test_import_rejects_mixed_versions_duplicates_and_impossible_values(
    tmp_path: Path,
) -> None:
    store = CalibrationStore(tmp_path / "store", key=Fernet.generate_key())
    mixed = _csv(tmp_path / "mixed.csv")
    mixed.write_text(
        mixed.read_text(encoding="utf-8").replace(
            "p-3,q1,1,1,60,A,m1,aqa-7136-v1.2",
            "p-3,q1,1,1,60,A,m1,aqa-7136-v2",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="specification"):
        store.import_csv(mixed, metadata=_metadata(), consents=_consents(4))

    duplicate = _csv(tmp_path / "duplicate.csv")
    duplicate.write_text(
        duplicate.read_text(encoding="utf-8")
        + "p-0,q1,0,1,60,A,m1,aqa-7136-v1.2\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        store.import_csv(duplicate, metadata=_metadata(), consents=_consents(4))

    impossible = _csv(tmp_path / "impossible.csv")
    impossible.write_text(
        impossible.read_text(encoding="utf-8").replace(
            "p-0,q1,0,1,60", "p-0,q1,2,1,-4"
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"score range|timing"):
        store.import_csv(impossible, metadata=_metadata(), consents=_consents(4))


def test_aggregate_report_never_exposes_rows_and_small_cohort_cannot_promote(
    tmp_path: Path,
) -> None:
    store = CalibrationStore(tmp_path / "store", key=Fernet.generate_key())
    dataset_id = store.import_csv(
        _csv(tmp_path / "responses.csv"),
        metadata=_metadata(),
        consents=_consents(4),
    )
    report = store.aggregate(dataset_id)
    encoded = json.dumps(report, sort_keys=True)

    assert "candidate_id" not in encoded
    assert "marker_id" not in encoded
    assert report["sample"]["candidates"] == 4
    assert report["difficulty_independently_verified"] is False
    evidence_path = write_calibration(report, tmp_path / "aggregate.json")
    summary = validate_calibration(
        evidence_path,
        family="aqa/economics",
        paper="1",
        form_id="form-260826",
    )
    assert summary["candidates"] == 4
    with pytest.raises(ValueError, match="insufficient evidence"):
        store.require_empirical_qualification(dataset_id)


def test_delete_is_complete_and_wrong_key_cannot_decrypt(tmp_path: Path) -> None:
    first = CalibrationStore(tmp_path / "store", key=Fernet.generate_key())
    dataset_id = first.import_csv(
        _csv(tmp_path / "responses.csv"),
        metadata=_metadata(),
        consents=_consents(4),
    )
    second = CalibrationStore(tmp_path / "store", key=Fernet.generate_key())
    with pytest.raises(ValueError, match="decrypt"):
        second.aggregate(dataset_id)

    assert first.delete(dataset_id)
    assert not first.dataset_path(dataset_id).exists()
    assert not first.delete(dataset_id)


def test_aggregate_schema_requires_privacy_and_evidence_fields() -> None:
    schema = json.loads(
        Path("Resources/empirical-calibration.schema.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(schema["required"])
    assert {
        "sample",
        "items",
        "checks",
        "thresholds",
        "provenance",
        "evidence_fingerprint",
        "policy",
    } <= required
    encoded = json.dumps(schema)
    assert "encrypted-local-only" in encoded
    assert '"candidate_id"' in encoded
    assert '"marker_id"' in encoded
