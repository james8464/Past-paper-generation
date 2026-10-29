# French interface copy survives scene boundaries and reusable help views.

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "macOS/Keldin"


def translated(key):
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    unit = catalog[key]["localizations"]["fr"]["stringUnit"]
    assert unit["state"] == "translated"
    assert unit["value"] and unit["value"] != key
    assert "—" not in unit["value"] and "–" not in unit["value"]
    return unit["value"]


def test_custom_commands_resolve_the_selected_language():
    source = (APP / "Application/AppCommands.swift").read_text()
    assert '@AppStorage("interfaceLanguage")' in source
    assert "InterfaceText.resolve(resource, language: interfaceLanguage)" in source
    keys = re.findall(r'localized\("([^"]+)"\)', source)
    assert len(set(keys)) >= 20
    for key in keys:
        translated(key)


def test_creation_commands_do_not_run_behind_guidance_sheets():
    source = (APP / "Application/AppCommands.swift").read_text()
    assert "application.showWelcome || application.showHelp" in source


def test_document_commands_do_not_target_the_document_behind_a_guide():
    source = (APP / "Application/AppCommands.swift").read_text()
    access = source.split("private var canAccessDocument: Bool", 1)[1].split(
        "private", 1
    )[0]
    assert "canNavigate" in access
    assert "documentActions?.canAccessDocument == true" in access
    assert source.count(".disabled(!canAccessDocument)") == 4
    assert source.count("guard canAccessDocument else { return }") == 4
    provenance = source.split("private var canCopyProvenance: Bool", 1)[1].split(
        "private", 1
    )[0]
    assert "canNavigate" in provenance
    assert "documentActions?.provenance != nil" in provenance
    assert ".disabled(!canCopyProvenance)" in source
    assert "guard canCopyProvenance else { return }" in source
    navigation = source.split("private var canNavigate: Bool", 1)[1].split(
        "private", 1
    )[0]
    assert "KeldinCreationContext.allowsNavigation(" in navigation
    assert "applicationModal: application.hasCommandBlockingPresentation" in navigation
    coordinator = (APP / "State/ApplicationCoordinator.swift").read_text()
    modal = coordinator.split("var hasCommandBlockingPresentation: Bool", 1)[1].split(
        "private", 1
    )[0]
    for presentation in (
        "showWelcome",
        "showHelp",
        "showError",
        "showHostedAIConsent",
        "showMLXSetupConfirmation",
    ):
        assert presentation in modal
    assert "showPullConfirmation" not in coordinator
    assert "modelDownloadPresentation?.blocksCommands == true" in navigation
    assert "settingsPresentation?.blocksCommands == true" in navigation
    assert "mainSceneIsFocused: mainWindowIdentity != nil" in navigation
    assert "@FocusedObject private var modelDownloadPresentation" in source
    settings = (APP / "Features/Settings/SettingsPane.swift").read_text()
    assert ".focusedSceneObject(downloadPresentation)" in settings
    assert "presenting: downloadPresentation.request" in settings
    assert "downloadPresentation.consume(id: request.id)" in settings
    assert "downloadPresentation.presentationDidDismiss(id: requestID)" in settings
    assert ".focusedSceneObject(presentation)" in settings
    assert "presentation: application.settingsPresentation" in settings
    assert "AISettingsTab(presentation: application.settingsPresentation)" in settings
    assert "@ObservedObject var presentation: SettingsActionPresentation" in settings
    assert "presentation.providerSelection(active: application.aiProvider)" in settings
    assert "MainWindowRouting.navigate(.help(.choosingAModel)" in settings
    main = (APP / "Navigation/ContentView.swift").read_text()
    assert "showPullConfirmation" not in main
    assert '"Pull Model"' not in main
    assert r".focusedSceneValue(\.keldinMainWindowIdentity, .primary)" in main


def test_help_containers_keep_localisable_resources_and_stable_identity():
    source = (APP / "Features/Onboarding/WelcomeHelpViews.swift").read_text()
    assert "let rows: [LocalizedStringResource]" in source
    assert "let rows: [(LocalizedStringResource, LocalizedStringResource)]" in source
    assert "HelpScreenshot" not in source
    assert "TutorialFrenchNSI" not in source
    assert "id: \\.element.0.key" in source
    assert "id: \\.offset" not in source
    assert (
        "InterfaceText.localizedResource(topic.titleResource, locale: locale)" in source
    )
    assert "Label(InterfaceText.localizedResource" not in source
    settings = (APP / "Features/Settings/SettingsPane.swift").read_text()
    assert (
        "Text(InterfaceText.localizedResource(OllamaModelGuide.document.otherModelWarningResource"
        in settings
    )


def test_french_help_explains_internal_review_without_fabricated_attestation():
    source = (APP / "Features/Onboarding/WelcomeHelpViews.swift").read_text()
    french = source.split("private var frenchBaccalaureat:", 1)[1].split(
        "private var", 1
    )[0]
    assert '"Work through the paper"' in french
    assert '"Record teacher review"' not in french
    key = (
        "Difficulty and completion time are uncalibrated. An optional teacher-review "
        "record can be attached to the exact artifact hashes; the app does not invent one."
    )
    assert key in french
    assert "facultative" in translated(key)


def test_generic_alert_and_model_warning_do_not_use_stale_names():
    source = (APP / "Navigation/ContentView.swift").read_text()
    assert '.alert("Couldn\'t complete the action"' in source
    translated("Couldn't complete the action")
    guide = json.loads(
        (ROOT / "Resources/ollama-model-recommendations.json").read_text()
    )
    warning = guide["other_model_warning"]
    assert "memory" in warning
    assert "not passed a complete paper-quality review" in warning
    assert "Paper Creator" not in warning and "PaperMaker" not in warning
    translated(warning)


def test_alerts_sheets_and_settings_receive_the_selected_locale():
    content = (APP / "Navigation/ContentView.swift").read_text()
    assert content.rfind(".environment(\\.locale") > content.index(
        ".sheet(isPresented: $application.showHelp)"
    )
    for sheet in ("HelpSheet()", "WelcomeSheet()"):
        assert (
            ".environment(\\.locale, interfaceLocale)"
            in content.split(sheet, 1)[1].split("}", 1)[0]
        )
    settings = (APP / "Features/Settings/SettingsPane.swift").read_text()
    assert '@AppStorage("interfaceLanguage")' in settings
    assert ".environment(\\.locale" in settings
