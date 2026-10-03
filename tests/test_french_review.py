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


def test_review_cli_writes_an_immutable_hash_bound_record(tmp_path):
    from argparse import Namespace

    from Backend.Core.france.teacher_review import handle_record_review, review_status

    document = tmp_path / "sujet.pdf"
    document.write_bytes(b"paper")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifacts": {
                    "question_paper": {
                        "file": document.name,
                        "sha256": sha256(document.read_bytes()).hexdigest(),
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    args = Namespace(
        manifest=manifest,
        reviewer="Mme Martin",
        decision="revise",
        scores_json=json.dumps(
            {
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
            }
        ),
        notes="Revoir la formulation de la question 2.",
    )
    assert handle_record_review(args) == 0
    records = list(tmp_path.glob("teacher-review-*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert review_status(manifest, record) == "revise"


def test_cli_exposes_french_teacher_review_without_changing_legacy_generation():
    from Backend.Core.cli import build_parser

    args = build_parser().parse_args(
        [
            "review-french-assessment",
            "--manifest",
            "/tmp/manifest.json",
            "--reviewer",
            "Mme Martin",
            "--decision",
            "revise",
            "--scores-json",
            "{}",
            "--notes",
            "À revoir",
        ]
    )
    assert args.manifest.name == "manifest.json"
    assert args.decision == "revise"
