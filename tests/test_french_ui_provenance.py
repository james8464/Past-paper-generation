# Keep visible French authoring claims aligned with the current catalogue.

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "macOS" / "Keldin"


def test_fixed_assessment_values_defer_localization_to_swiftui():
    workspace = (
        ROOT / "Features/Generation/FrenchAssessmentWorkspace.swift"
    ).read_text()
    for key in (
        "2027 · 3 h 30 · 3 independent exercises",
        "18 technical + 2 French language = 20",
    ):
        assert f'Text("{key}")' in workspace
    for row in ("written-exam", "indicative-credit"):
        assert f'.id("{row}-\\(interfaceLanguage)")' in workspace


def test_french_workspace_explains_application_owned_cases_in_both_languages():
    workspace = (
        ROOT / "Features/Generation/FrenchAssessmentWorkspace.swift"
    ).read_text()
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    for key in (
        "Five paper families are available. The app selects an unused family and blocks repeats.",
        "This catalogue runs locally without an AI model or Ollama. It does not test model quality.",
        "Official sources are downloaded with your permission. Papers are built on this Mac without model prompts or cloud generation.",
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
    assert "French papers are built locally from a fixed catalogue." in french
    assert "Ollama generation uses" not in french
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    key = (
        "French papers are built locally from a fixed catalogue. "
        "No AI model, Ollama installation or cloud service is needed."
    )
    assert key in french
    unit = catalog[key]["localizations"]["fr"]["stringUnit"]
    assert unit["state"] == "translated"
    assert "catalogue fixe" in unit["value"]
    assert "Aucun modèle" in unit["value"]


def test_french_local_progress_has_selected_language_copy():
    source = (ROOT / "Domain/GenerationPresentation.swift").read_text()
    assert '"Construction des exercices vérifiés, sans appel à un modèle."' in source
    key = "Preparing the practice paper."
    assert key in source
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    assert (
        catalog[key]["localizations"]["fr"]["stringUnit"]["value"]
        == "Préparation du sujet d’entraînement."
    )
