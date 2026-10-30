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


def test_historical_prompt_whitespace_keeps_complete_comparison_evidence(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    historic = package(tmp_path / "earlier-assessment.json", [f"\n  {PROMPT}\n"])
    before = historic.read_bytes()
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["history_complete"] is True
    assert report["skipped_history_packages"] == 0
    assert report["historical_overlap"] is True
    assert report["passed"] is False
    assert historic.read_bytes() == before


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


@pytest.mark.parametrize(
    "corrupt_bytes",
    [b'{"schema_version":1,"items":null}', b'{"schema_version":1,"items":', b"\xff"],
)
@pytest.mark.parametrize("policy", ["strict-cross-generation-v1", "repeat-practice-v1"])
def test_corrupt_history_is_preserved_and_comparison_is_unknown(
    tmp_path, corrupt_bytes, policy
):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    historic = tmp_path / "corrupt-assessment.json"
    historic.write_bytes(corrupt_bytes)
    current_before = current.read_bytes()

    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy=policy
    )

    assert report["passed"] is None
    assert report["history_complete"] is False
    assert report["skipped_history_packages"] == 1
    assert report["historic_comparisons"] == 0
    assert report["within_paper_passed"] is True
    assert historic.read_bytes() == corrupt_bytes
    assert current.read_bytes() == current_before
    assert historic.name not in json.dumps(report)


def test_corrupt_history_does_not_hide_observed_repeat_overlap(tmp_path):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    package(tmp_path / "earlier-assessment.json", [PROMPT])
    (tmp_path / "corrupt-assessment.json").write_text(
        '{"schema_version":1,"items":null}', encoding="utf-8"
    )
    report = validate_package_novelty(
        current, history_root=tmp_path, cross_generation_policy="repeat-practice-v1"
    )
    assert report["passed"] is False
    assert report["historical_overlap"] is True
    assert report["historic_comparisons"] == 1
    assert report["history_complete"] is False
    with pytest.raises(ValueError, match="too similar"):
        validate_package_novelty(current, history_root=tmp_path)


@pytest.mark.parametrize(
    "change",
    [
        {"items": []},
        {"items": [None]},
        {"items": [{}]},
        *[
            {"field": field, "value": value}
            for field in ("id", "subject", "paper", "prompt")
            for value in (None, True, "", " ")
        ],
        {"field": "subject", "value": " accounting "},
        {"field": "subject", "value": "account ing"},
        {"field": "id", "value": "q\n1"},
        {"field": "prompt", "value": "???"},
        {"field": "paper", "value": 2},
        {"mixed": True},
        {"missing_items": True},
        *[{"missing_field": field} for field in ("id", "subject", "paper", "prompt")],
    ],
)
def test_unusable_historical_items_never_claim_complete_history(tmp_path, change):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    historic = package(tmp_path / "earlier-assessment.json", [PROMPT])
    raw = json.loads(historic.read_text(encoding="utf-8"))
    if "items" in change:
        raw["items"] = change["items"]
    elif change.get("mixed"):
        raw["items"].append(None)
    elif change.get("missing_items"):
        raw.pop("items")
    elif "missing_field" in change:
        raw["items"][0].pop(change["missing_field"])
    else:
        raw["items"][0][change["field"]] = change["value"]
    historic.write_text(json.dumps(raw), encoding="utf-8")
    before = historic.read_bytes()
    report = validate_package_novelty(current, history_root=tmp_path)
    assert report["passed"] is None
    assert report["history_complete"] is False
    assert report["skipped_history_packages"] == 1
    assert report["historic_comparisons"] == 0
    assert historic.read_bytes() == before


def test_actual_exported_history_has_usable_similarity_items(tmp_path):
    from Backend.Core.assessment_package import write_assessment_package
    from tests.test_accounting_objectives import paper_for

    history = tmp_path / "history"
    history.mkdir()
    historic = history / "actual-assessment.json"
    write_assessment_package(
        paper_for(),
        historic,
        subject="accounting",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )
    current = package(tmp_path / "current-assessment.json", [PROMPT], paper="2")
    before = historic.read_bytes()
    report = validate_package_novelty(current, history_root=history)
    assert report["passed"] is True
    assert report["history_complete"] is True
    assert report["skipped_history_packages"] == 0
    assert historic.read_bytes() == before


def test_corrupt_current_package_is_not_skipped(tmp_path):
    current = tmp_path / "current-assessment.json"
    current.write_text('{"schema_version":1,"items":null}', encoding="utf-8")
    before = current.read_bytes()
    with pytest.raises(ValueError, match="items must be a list"):
        validate_package_novelty(current, history_root=tmp_path)
    assert current.read_bytes() == before


def test_manifest_preserves_unknown_history_evidence(tmp_path, monkeypatch):
    current = package(tmp_path / "current-assessment.json", [PROMPT])
    (tmp_path / "corrupt-assessment.json").write_text(
        '{"schema_version":1,"items":null}', encoding="utf-8"
    )
    evidence = validate_package_novelty(current, history_root=tmp_path)
    monkeypatch.setattr(generation, "_repository_commit", lambda: "a" * 40)
    monkeypatch.setattr(generation, "_generator_version", lambda _: "test")
    monkeypatch.setattr(generation, "_sha256", lambda _: "b" * 64)
    path = generation._write_package_manifest(
        args=argparse.Namespace(
            subject="accounting_aqa",
            paper="2",
            seed=1,
            dry_run=False,
            provider="ollama",
            model="test",
        ),
        capability=generation.generator_capability("accounting_aqa"),
        staging_dir=tmp_path,
        paths={"assessment_package": current},
        pdf_validation={},
        assessment_validation={},
        novelty_validation=evidence,
    )
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["evidence"]["novelty_validation"] == evidence
    assert saved["evidence"]["novelty_validation"]["passed"] is None


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
