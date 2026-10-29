from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from Backend.Core.qualification.manifest import (
    ArtifactEvidence,
    EvidenceRecord,
    GateState,
    ModelIdentity,
    QualificationManifest,
    QualificationPolicy,
    VersionIdentity,
)

ROOT = Path(__file__).resolve().parents[1]


def manifest() -> QualificationManifest:
    return QualificationManifest(
        generator_id="aqa/economics",
        paper_id="1",
        seed=26080100,
        model=ModelIdentity(provider="ollama", name="gemma4:12b"),
        versions=VersionIdentity(
            contract="assessment-contract:v1",
            blueprint="aqa-economics-paper-1:v3",
            prompt="ai-assessment:v4",
            syllabus="7136:2025",
            renderer="aqa-document:v5",
        ),
        artifacts=[],
        gate_results={
            "generation": GateState.PASSED,
            "pdf": GateState.PASSED,
            "visual": GateState.NOT_RUN,
            "expert_review": GateState.NOT_RUN,
            "student_calibration": GateState.NOT_RUN,
        },
        evidence=[],
        reviewer_identity_class="automation",
        tool_versions={"keldin-backend": "2.0.0"},
        created_at=datetime(2026, 8, 26, tzinfo=UTC),
    )


def test_manifest_requires_reproducibility_identity() -> None:
    payload = manifest().model_dump()
    del payload["versions"]

    with pytest.raises(ValidationError, match="versions"):
        QualificationManifest.model_validate(payload)


def test_artifact_evidence_hashes_file_content(tmp_path: Path) -> None:
    artifact = tmp_path / "paper.pdf"
    artifact.write_bytes(b"paper-content")

    evidence = ArtifactEvidence.from_path("question_paper", artifact)

    assert evidence.filename == "paper.pdf"
    assert evidence.bytes == len(b"paper-content")
    assert evidence.sha256 == hashlib.sha256(b"paper-content").hexdigest()


def test_record_evidence_returns_a_new_manifest() -> None:
    original = manifest()
    updated = original.record_evidence(
        "visual",
        EvidenceRecord(
            path="qualification/visual.json",
            sha256="a" * 64,
            reviewer_identity_class="internal_reviewer",
        ),
        state=GateState.PASSED,
    )

    assert original.gate_results["visual"] is GateState.NOT_RUN
    assert original.evidence == []
    assert updated.gate_results["visual"] is GateState.PASSED
    assert updated.evidence[0].gate == "visual"


def test_qualification_levels_require_every_policy_gate() -> None:
    policy = QualificationPolicy.load(ROOT / "Resources" / "qualification-policy.json")
    value = manifest()

    assert value.is_qualified("engineering", policy) is True
    assert value.is_qualified("visual", policy) is False
    assert value.is_qualified("empirical", policy) is False


def test_manifest_round_trips_canonical_json(tmp_path: Path) -> None:
    path = tmp_path / "qualification.json"
    value = manifest()

    value.save(path)
    loaded = QualificationManifest.load(path)

    assert loaded == value
    assert path.read_text(encoding="utf-8") == value.canonical_json() + "\n"
    assert json.loads(value.canonical_json())["schema_version"] == 1


def test_resource_schema_names_all_required_evidence_fields() -> None:
    schema = json.loads(
        (ROOT / "Resources" / "qualification-schema.json").read_text(encoding="utf-8")
    )

    assert set(schema["required"]) >= {
        "generator_id",
        "paper_id",
        "seed",
        "model",
        "versions",
        "artifacts",
        "gate_results",
        "evidence",
        "created_at",
        "reviewer_identity_class",
        "tool_versions",
    }
    assert set(schema["properties"]["versions"]["required"]) == {
        "contract",
        "blueprint",
        "prompt",
        "syllabus",
        "renderer",
    }


def test_manifest_save_does_not_unlink_after_committed_replace(tmp_path: Path):
    path = tmp_path / "qualification.json"
    value = manifest()
    with patch.object(Path, "unlink", side_effect=PermissionError("cleanup denied")):
        value.save(path)
    assert QualificationManifest.load(path) == value
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("operation", ["fsync", "replace"])
@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt, SystemExit])
def test_manifest_save_preserves_primary_failure_when_cleanup_fails(
    tmp_path, operation, failure
):
    path = tmp_path / "qualification.json"
    path.write_bytes(b"previous")
    primary = failure("publication failed")
    with (
        patch(
            f"Backend.Core.qualification.manifest.os.{operation}", side_effect=primary
        ),
        patch.object(Path, "unlink", side_effect=PermissionError("cleanup denied")),
        pytest.raises(failure) as caught,
    ):
        manifest().save(path)
    assert caught.value is primary
    assert "cleanup denied" in " ".join(caught.value.__notes__)
    assert path.read_bytes() == b"previous"
    assert len(list(tmp_path.glob(".qualification.json.*.tmp"))) == 1


def test_manifest_closes_descriptor_when_stream_construction_fails(tmp_path):
    descriptors = []

    def fail_open(descriptor, *_args, **_kwargs):
        descriptors.append(descriptor)
        raise OSError("stream construction failed")

    with (
        patch("Backend.Core.qualification.manifest.os.fdopen", side_effect=fail_open),
        pytest.raises(OSError, match="stream construction failed"),
    ):
        manifest().save(tmp_path / "qualification.json")
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(descriptors[0])
    assert list(tmp_path.iterdir()) == []
