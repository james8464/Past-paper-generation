"""Cross-generation overlap is evidence, not a repeat-practice publication gate."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from Backend.Core import generation
from Backend.Core.assessment_quality import validate_package_novelty


def package(path: Path, prompts: list[str], *, subject="accounting", paper="2"):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "items": [
                    {
                        "id": str(index),
                        "subject": subject,
                        "paper": paper,
                        "prompt": prompt,
                    }
                    for index, prompt in enumerate(prompts)
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


PROMPT = "Calculate contribution when selling price is £45 and variable cost is £10."


def test_repeat_practice_records_overlap_without_claiming_originality(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    historic = package(tmp_path / "earlier-assessment.json", [PROMPT])
    before = historic.read_bytes()
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["cross_generation_policy"] == "repeat-practice-v1"
    assert report["within_paper_passed"] is True
    assert report["historical_overlap"] is True
    assert report.get("passed") is not True
    assert report["historic_comparisons"] == 1
    assert report["nearest_match"]["similarity"] == 1
    assert historic.read_bytes() == before


def test_default_policy_still_rejects_historical_overlap(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    package(tmp_path / "earlier-assessment.json", [PROMPT])
    with pytest.raises(ValueError, match="too similar"):
        validate_package_novelty(current, history_root=tmp_path)


def test_repeat_practice_still_rejects_within_paper_duplicates(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT, PROMPT])
    with pytest.raises(ValueError, match="too similar"):
        validate_package_novelty(
            current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
        )


def test_repeat_practice_reports_no_overlap_without_history(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["historical_overlap"] is False
    assert report["nearest_match"] is None
    assert report["within_paper_passed"] is True


def test_history_comparison_still_scopes_subject_and_paper(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    package(tmp_path / "other-subject-assessment.json", [PROMPT], subject="physics")
    package(tmp_path / "other-paper-assessment.json", [PROMPT], paper="1")
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["historic_comparisons"] == 0
    assert report["historical_overlap"] is False


def test_repeat_practice_keeps_comparing_after_a_historical_match(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    package(tmp_path / "earlier-a-assessment.json", [PROMPT])
    package(tmp_path / "earlier-b-assessment.json", [PROMPT])
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["historic_comparisons"] == 2
    assert report["historical_overlap"] is True
    assert report["passed"] is False


def test_unknown_cross_generation_policy_fails_closed(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    with pytest.raises(ValueError, match="policy"):
        validate_package_novelty(
            current, history_root=tmp_path, cross_generation_policy="allow-anything"
        )


def test_public_generation_explicitly_uses_repeat_practice(tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    staging.mkdir()
    current = package(staging / "current-assessment.json", [PROMPT])
    captured = {}

    def novelty(path, **kwargs):
        captured.update(kwargs)
        return {"within_paper_passed": True, "historical_overlap": True}

    monkeypatch.setattr(generation, "validate_assessment_package", lambda *a, **k: {})
    monkeypatch.setattr(generation, "validate_package_novelty", novelty)
    monkeypatch.setattr(generation, "conform_generated_documents", lambda *a: {})
    manifest = staging / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(generation, "_write_package_manifest", lambda **k: manifest)
    monkeypatch.setattr(generation, "_atomic_publish", lambda src, dst: dst)
    generation.finalize_generated_documents(
        args=argparse.Namespace(
            subject="accounting_aqa",
            paper="2",
            dry_run=False,
            provider="ollama",
            model="diagnostic",
        ),
        capability=SimpleNamespace(outputs_for=lambda _: ["assessment_package"]),
        staging_dir=staging,
        output_dir=tmp_path,
        paths={"assessment_package": current},
    )
    assert captured["cross_generation_policy"] == "repeat-practice-v1"
