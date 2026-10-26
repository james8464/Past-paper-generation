"""Keep visible French authoring claims aligned with the V32 runtime."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "macOS" / "PaperCreator"


def test_french_workspace_explains_application_owned_cases_in_both_languages():
    workspace = (
        ROOT / "Features/Generation/FrenchAssessmentWorkspace.swift"
    ).read_text()
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    for key in (
        "V32 uses three app-authored case families, not model-generated questions. New drafts may repeat a family.",
        "No AI model or Ollama installation is needed for V32. These papers do not qualify an AI model.",
        "Official sources are downloaded with your permission. V32 builds papers on this Mac without model prompts or cloud generation.",
    ):
        assert f'Text("{key}")' in workspace
        unit = catalog[key]["localizations"]["fr"]["stringUnit"]
        assert unit["state"] == "translated"
        assert unit["value"] and unit["value"] != key
    assert "French generation uses Ollama" not in workspace
    assert "Gemma 4 12B is the comparison baseline" not in workspace


def test_french_help_does_not_claim_ollama_authors_current_papers():
    source = (ROOT / "Features/Onboarding/WelcomeHelpViews.swift").read_text()
    french = source.split("private var frenchBaccalaureat:", 1)[1].split(
        "private var", 1
    )[0]
    assert (
        "V32 uses finite app-authored cases, not model-generated questions." in french
    )
    assert "Ollama generation uses" not in french
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    key = (
        "V32 uses finite app-authored cases, not model-generated questions. "
        "No AI model or Ollama installation is needed; papers are built locally without cloud generation."
    )
    assert key in french
    unit = catalog[key]["localizations"]["fr"]["stringUnit"]
    assert unit["state"] == "translated"
    assert "sans génération" in unit["value"]
