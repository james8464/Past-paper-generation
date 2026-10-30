import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "macOS/Keldin"


def test_uk_model_accessibility_refresh_is_scoped_to_the_read_only_row():
    workspace = (APP / "Features/Generation/GeneratorWorkspaceView.swift").read_text()
    model_row = workspace.split('LabeledContent("Model") {', 1)[1].split(
        "if board.usesAI && !application.dryRun", 1
    )[0]
    assert ".id(" not in model_row
    assert "Text(application.activeModelName)" in model_row
    assert ".help(application.activeModelName)" in model_row
    assert 'Text("Memory fit")' in model_row
    assert ".accessibilityElement(children: .ignore)" in model_row
    assert '.accessibilityLabel("Model")' in model_row
    assert ".accessibilityValue(Text(verbatim: modelAccessibilityValue))" in model_row
    assert 'InterfaceText.localizedResource("Memory fit", locale: locale)' in workspace
    assert (
        "guard application.aiProvider == .ollama, application.selectedModelIsRecommended"
        in workspace
    )
    assert "get: { application.dryRun }" in workspace
    assert "set: { application.setDryRun($0) }" in workspace
    assert "Form {\n" in workspace
    assert ".formStyle(.grouped)\n        .disabled(application.isRunning)" in workspace


def test_uk_provider_picker_labels_deepseek_without_making_it_selectable():
    workspace = (APP / "Features/Generation/GeneratorWorkspaceView.swift").read_text()
    selected_only = workspace.split("if application.aiProvider == .deepSeek {", 1)[
        1
    ].split("ForEach(board.supportedProviders)", 1)[0]
    assert 'Label("DeepSeek (French NSI only)"' in selected_only
    assert (
        ".tag(AIProvider.deepSeek)\n                            .selectionDisabled(true)"
        in selected_only
    )
    assert "ForEach(board.supportedProviders)" in workspace
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    assert (
        catalog["DeepSeek (French NSI only)"]["localizations"]["fr"]["stringUnit"][
            "value"
        ]
        == "DeepSeek (NSI française uniquement)"
    )


def test_hosted_provider_label_and_disclosure_summary_have_french_copy():
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    for key, expected in (
        ("AI provider", "Fournisseur d’IA"),
        (
            "Prompts and subject context may be sent to the selected provider.",
            "Les consignes et le contexte de la matière peuvent être transmis au fournisseur sélectionné.",
        ),
    ):
        unit = catalog[key]["localizations"]["fr"]["stringUnit"]
        assert unit["state"] == "translated"
        assert unit["value"] == expected


def test_model_quality_guidance_is_separate_from_memory_suggestions():
    policy = (APP / "Domain/PaperQualityGuidance.swift").read_text()
    assert "llama-3.2-3b-instruct-4bit" in policy
    assert "gemma4:12b" in policy
    for evidence in [
        "answerChecksFailed",
        "nsiProbeFailed",
        "reviewIncomplete",
        "unverified",
    ]:
        assert evidence in policy
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


def test_qwen_warning_is_scoped_to_tested_nsi_probe_not_full_paper_qualification():
    source = (APP / "Domain/PaperQualityGuidance.swift").read_text()
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    message = (
        "A tested revision returned wrong answers in a small NSI reasoning probe "
        "with reasoning off. Full-paper quality remains unverified."
    )
    assert 'provider == .ollama, model == "qwen3.5:9b"' in source
    assert message in source
    assert catalog[message]["localizations"]["fr"]["stringUnit"]["value"]


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
