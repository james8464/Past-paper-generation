import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "macOS/Keldin"


def test_model_quality_guidance_is_separate_from_memory_suggestions():
    policy = (APP / "Domain/PaperQualityGuidance.swift").read_text()
    assert "llama-3.2-3b-instruct-4bit" in policy
    assert "gemma4:12b" in policy
    assert "case answerChecksFailed, reviewIncomplete, unverified" in policy
    assert "case passed" not in policy
    for relative in [
        "Features/Settings/SettingsPane.swift",
        "Features/Generation/GeneratorWorkspaceView.swift",
    ]:
        source = (APP / relative).read_text()
        assert "ModelQualityAdviceView(" in source
        assert "application.activeModelName" in source
    workspace = (APP / "Features/Generation/GeneratorWorkspaceView.swift").read_text()
    settings = (APP / "Features/Settings/SettingsPane.swift").read_text()
    assert 'Text("Memory fit")' in workspace
    assert 'Text("Recommended")' not in workspace
    assert 'LabeledContent("Memory-fit suggestion")' in settings
    assert 'Label("Recommended model selected"' not in settings


def test_last_result_summary_uses_reported_evidence_without_an_all_clear():
    source = (APP / "Domain/PaperQualityGuidance.swift").read_text()
    view = (APP / "Features/Generation/GenerationGuidanceViews.swift").read_text()
    assert "GenerationIssueSummary" in source
    assert "report.referenceDemandFailedChecks" in source
    assert "report.evidenceGaps" in source
    assert "report.empiricallyCalibrated != true" in source
    assert "report.visuallyCalibrated != true" in source
    for label in ["Reported issues", "Warnings", "Not checked"]:
        assert label in view
    assert "selectedPaper.readiness" not in view
    assert "All checks passed" not in view
    assert ".foregroundStyle(.primary)" in view


def test_quality_guidance_copy_has_french_translations():
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    for key in [
        "Known answer-check failure",
        "Paper-quality review incomplete",
        "Paper quality unverified",
        "Memory-fit suggestion",
        "Memory fit",
        "Reported issues",
        "Warnings",
        "Not checked",
        "No quality record is available for this result.",
        "This Apple MLX model failed answer checks in an Accounting test. Memory fit does not establish paper quality.",
    ]:
        value = catalog[key]["localizations"]["fr"]["stringUnit"]["value"]
        assert value and value != key
        assert "—" not in value and "–" not in value
