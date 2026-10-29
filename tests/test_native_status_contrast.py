# Status text stays readable independently of its symbol colour.

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "macOS" / "Keldin"


def test_model_status_labels_use_semantic_primary_text():
    settings = (ROOT / "Features/Settings/SettingsPane.swift").read_text()
    workspace = (ROOT / "Features/Generation/GeneratorWorkspaceView.swift").read_text()
    labels = (
        settings.split('Label("Recommended model selected"', 1)[1].split("} else", 1)[
            0
        ],
        settings.split("OllamaModelGuide.document.otherModelWarningResource,", 1)[
            1
        ].split("HStack", 1)[0],
        workspace.split(
            "if application.aiProvider == .ollama && !application.selectedModelIsRecommended {",
            1,
        )[1].split('LabeledContent("Save to")', 1)[0],
    )
    for label in labels:
        assert ".foregroundStyle(.primary)" in label
        assert ".foregroundStyle(.orange)" not in label
        assert ".foregroundStyle(.green)" not in label


def test_warning_keeps_a_symbol_and_explanation_without_colour():
    workspace = (ROOT / "Features/Generation/GeneratorWorkspaceView.swift").read_text()
    warning = workspace.split('Section("Action required")', 1)[1].split(
        ".accessibilityElement", 1
    )[0]
    assert 'Image(systemName: "exclamationmark.triangle.fill")' in warning
    assert "Text(InterfaceText.localizedResource(blocker, locale: locale))" in warning
    assert 'Text("Open Settings…")' in warning
