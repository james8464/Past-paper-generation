from __future__ import annotations

import json

from tools.coverage_matrix import GENERATOR_REGISTRY
from tools.ocr_computer_science_calibration import OUTPUT


def report() -> dict[str, object]:
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def test_reference_evidence_is_aggregate_only() -> None:
    value = report()
    reference = value["reference"]
    assert reference["documents"] == 8
    assert reference["derived_aggregate_only"] is True
    assert reference["retains_source_text"] is False
    rendered = json.dumps(value)
    assert "Reference Corpus" not in rendered
    assert "question-paper-" not in rendered


def test_multi_seed_structural_demand_passes() -> None:
    value = report()
    for paper in value["generated"]["papers"].values():
        assert paper["seeds"] == 20
        assert paper["unique_fingerprints"] == 20
        assert paper["unique_stimulus_fingerprints"] == 20
        assert all(paper["checks"].values())


def test_difficulty_remains_external_evidence_gated() -> None:
    gates = report()["gates"]
    assert gates["automated_structural_demand"] is True
    assert gates["independent_subject_review"] is False
    assert gates["student_trial"] is False
    assert gates["psychometric_equivalence"] is False
    assert gates["difficulty_verified"] is False


def test_registry_links_calibration_without_false_difficulty_claim() -> None:
    registry = json.loads(GENERATOR_REGISTRY.read_text(encoding="utf-8"))
    family = next(
        item for item in registry["families"] if item["id"] == "ocr/computer-science"
    )
    assert family["calibration_path"] == (
        "computer-science/ocr/generator/data/difficulty-calibration.json"
    )
    assert all(paper["gates"]["difficulty"] is False for paper in family["papers"])
