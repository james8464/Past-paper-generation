# Keep visible French authoring claims aligned with the model-authored route.

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


def test_provider_and_model_refresh_only_their_read_only_accessibility_rows():
    workspace = (
        ROOT / "Features/Generation/FrenchAssessmentWorkspace.swift"
    ).read_text()
    identity = (
        r"\(application.aiProvider.rawValue)-\(application.activeModelName)-"
        r"\(interfaceLanguage)"
    )
    for label, value, row in (
        ("AI provider", "application.aiProvider.title", "ai-provider"),
        ("Model", "application.activeModelName", "ai-model"),
    ):
        expected = (
            f'LabeledContent("{label}", value: {value})\n'
            f'                    .id("{row}-{identity}")'
        )
        assert expected in workspace
    # Identities belong to these display-only rows, not the Form or its controls.
    assert workspace.count(r"\(application.aiProvider.rawValue)") == 2
    assert '@State private var largePrint = false' in workspace
    assert 'Toggle("Enlarged print", isOn: $largePrint)' in workspace


def test_french_workspace_explains_model_authoring_in_both_languages():
    workspace = (
        ROOT / "Features/Generation/FrenchAssessmentWorkspace.swift"
    ).read_text()
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    for key in (
        "The selected AI model writes a new draft from French references. Answers and difficulty still need review.",
        "Local models run on this Mac. Hosted providers receive the generation prompts only after your consent.",
        "Official sources are downloaded with your permission. The chosen provider creates the draft; no official approval or calibrated difficulty is implied.",
    ):
        assert f'Text("{key}")' in workspace
        unit = catalog[key]["localizations"]["fr"]["stringUnit"]
        assert unit["state"] == "translated"
        assert unit["value"] and unit["value"] != key
    assert "French generation uses Ollama" not in workspace
    assert "Gemma 4 12B is the comparison baseline" not in workspace
    assert "blocks repeats" not in workspace
    assert "This catalogue runs locally without an AI model" not in workspace
    assert "ModelQualityAdviceView" in workspace


def test_french_help_explains_provider_readiness_without_fixed_catalogue_claim():
    source = (ROOT / "Features/Onboarding/WelcomeHelpViews.swift").read_text()
    french = source.split("private var frenchBaccalaureat:", 1)[1].split(
        "private var", 1
    )[0]
    assert "French papers are built locally from a fixed catalogue." not in french
    assert "Ollama generation uses" not in french
    catalog = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    key = (
        "French drafts use the provider and model selected in Settings. "
        "Local providers run on this Mac; hosted providers require consent and an API key."
    )
    assert key in french
    unit = catalog[key]["localizations"]["fr"]["stringUnit"]
    assert unit["state"] == "translated"
    assert "modèle" in unit["value"]
    assert "clé API" in unit["value"]


def test_public_french_request_uses_model_without_family_fallback_and_verifies_identity():
    request = (ROOT / "Domain/FrenchLLMAssessmentRequest.swift").read_text()
    application = (ROOT / "State/ApplicationCoordinator.swift").read_text()
    public = application.split("func generateFrenchPaper", 1)[1].split(
        "func generateOccitanieActivity", 1
    )[0]
    for flag in ('"--provider"', '"--model"', '"--authoring-version", "v36"'):
        assert flag in request
    assert "savedFrenchFamilies" not in public
    assert "excludedFamilies" not in public
    assert "KELDIN_API_KEY" in public
    assert "--api-key" not in request
    for field in ("provider", "model", "seed"):
        assert f"publication.identity.{field} == configuration.{field}" in request
    assert 'generationOrigin == "model_authored"' in request
    assert "publication.modelUsed" in request
    assert "target.frenchLargePrint" in application
    assert "metadata.artifacts[artifact.role]" in request
    assert "hash == record.sha256" in request
    assert "packageIdentity" in request and "manifestIdentity" in request
    assert "record.file == artifact.url.lastPathComponent" in request
    publisher = (ROOT / "Services/UKArtifactPublisher.swift").read_text()
    assert "try fileHash(copy) == sourceHash" in publisher


def test_french_review_discloses_model_and_contract_limits_with_question_warnings():
    source = (ROOT / "Features/Generation/GenerationGuidanceViews.swift").read_text()
    report = (ROOT / "Domain/FrenchDraftQualityReport.swift").read_text()
    catalogue = json.loads((ROOT / "Localizable.xcstrings").read_text())["strings"]
    for key in (
        "Model review is not proof. Executable contract checks do not certify the printed answers.",
        "Printed-answer correctness, difficulty and completion time are not certified.",
        "No entries in this part of the record. This is not an all-clear.",
    ):
        assert key in source
        assert catalogue[key]["localizations"]["fr"]["stringUnit"]["value"]
    assert 'package["checks"]' in report
    assert 'package["reviews"]' in report
    assert 'package["warnings"]' in report
    assert "expected.subtracting(checked)" in report
    assert '"sql", "python_trace", "shortest_path"' in report
    assert 'findings("Not checked", report.notChecked)' in source


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
