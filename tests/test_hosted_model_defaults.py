import json
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "macOS/Keldin"


def test_new_hosted_defaults_do_not_replace_saved_preferences():
    defaults = (APP / "Application/AppConfiguration.swift").read_text()
    settings = (APP / "State/SettingsStore.swift").read_text()
    assert 'static let openAIModel = "gpt-6.1-sol"' in defaults
    assert 'static let anthropicModel = "claude-sonnet-5-5"' in defaults
    for key in ("openAIModel", "anthropicModel"):
        assert f"defaults.string(forKey: AppStorageKey.{key})" in settings
        assert f"?? AppDefaults.{key}" in settings


def test_retired_warning_and_explicit_vendor_choices_are_not_quality_approvals():
    advice = (APP / "Domain/PaperQualityGuidance.swift").read_text()
    candidates = (APP / "Domain/HostedModelCandidate.swift").read_text()
    view = (APP / "Features/Settings/HostedModelCandidatesView.swift").read_text()
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    assert 'provider == .anthropic, model == "claude-sonnet-4-20250514"' in advice
    for model in ("gpt-6-astra", "claude-opus-5-5"):
        assert model in candidates
    assert "Button" in view and "model = candidate.model" in view
    key = (
        "These are vendor model candidates, not paper-quality approvals from Keldin. "
        "Hosted generation requires your own API credits."
    )
    assert key in view
    assert catalog[key]["localizations"]["fr"]["stringUnit"]["value"]
