import json
from hashlib import sha256

import pytest


@pytest.mark.parametrize("reviewer", ["Professeur test", "  Professeur test  "])
def test_review_is_bound_to_all_artifacts_and_becomes_stale(tmp_path, reviewer):
    from Backend.Core.france.teacher_review import record_review, review_status

    document = tmp_path / "sujet.pdf"
    document.write_bytes(b"example test artifact")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifacts": {
                    "question_paper": {
                        "file": "sujet.pdf",
                        "sha256": sha256(document.read_bytes()).hexdigest(),
                    }
                }
            }
        )
    )
    record = record_review(
        manifest,
        reviewer=reviewer,
        decision="revise",
        scores={
            key: 3
            for key in (
                "correctness",
                "curriculum",
                "language",
                "difficulty",
                "timing",
                "marking",
                "layout",
                "originality",
            )
        },
        notes="Corriger le premier exercice.",
    )
    assert review_status(manifest, record) == "revise"
    document.write_bytes(b"edited artifact")
    assert review_status(manifest, record) == "stale"


def test_review_rejects_unsafe_manifest_and_incomplete_rubric(tmp_path):
    from Backend.Core.france.teacher_review import record_review

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifacts": {
                    "question_paper": {"file": "../outside.pdf", "sha256": "0" * 64}
                }
            }
        )
    )
    with pytest.raises(ValueError):
        record_review(manifest, reviewer="", decision="approved", scores={}, notes="")
