import Foundation
import XCTest
@testable import Keldin

final class DeepSeekProviderTests: XCTestCase {
    @MainActor
    func testCredentialsAndModelsStaySeparateAndSaveFailuresRemainVisible() {
        let defaults = isolatedDefaults()
        let secrets = DeepSeekTestSecrets()
        secrets.values = [SecretAccount.openAIAPIKey: "openai-fixture", SecretAccount.anthropicAPIKey: "anthropic-fixture", SecretAccount.deepSeekAPIKey: "deepseek-fixture"]
        let settings = SettingsStore(defaults: defaults, secrets: secrets)
        XCTAssertEqual(settings.deepSeekModel, "deepseek-flash")
        XCTAssertEqual(settings.deepSeekAPIKey, "deepseek-fixture")
        XCTAssertNil(defaults.string(forKey: AppStorageKey.deepSeekModel))
        settings.deepSeekModel = "deepseek-v4-pro"
        settings.deepSeekAPIKey = "replacement-fixture"
        secrets.failures.insert(SecretAccount.deepSeekAPIKey)
        XCTAssertFalse(settings.save())
        XCTAssertNotNil(settings.credentialFailure(for: SecretAccount.deepSeekAPIKey))
        XCTAssertEqual(secrets.values[SecretAccount.deepSeekAPIKey], "deepseek-fixture")
        secrets.failures.removeAll()
        XCTAssertTrue(settings.save())
        settings.deepSeekAPIKey = ""
        secrets.failures.insert(SecretAccount.deepSeekAPIKey)
        XCTAssertFalse(settings.save())
        secrets.failures.removeAll()
        XCTAssertTrue(settings.save())
        XCTAssertEqual(secrets.values[SecretAccount.deepSeekAPIKey], "")
        XCTAssertEqual(secrets.values[SecretAccount.openAIAPIKey], "openai-fixture")
        XCTAssertEqual(secrets.values[SecretAccount.anthropicAPIKey], "anthropic-fixture")
        let restored = SettingsStore(defaults: defaults, secrets: secrets)
        XCTAssertEqual(restored.deepSeekModel, "deepseek-v4-pro")
        XCTAssertEqual(restored.openAIModel, settings.openAIModel)
    }

    @MainActor
    func testDeepSeekConsentIsVersionedAndNeverBorrowedFromOtherProviders() {
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hostedAIConsentAccepted)
        let backend = ControlledRunBackend()
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.selectAIProvider(.deepSeek)
        XCTAssertEqual(app.aiProvider, .ollama)
        XCTAssertTrue(app.showHostedAIConsent)
        XCTAssertTrue(InterfaceText.resolve(app.pendingHostedDisclosureResource, language: "en").contains("DeepSeek receives"))
        app.cancelHostedAIConsent()
        XCTAssertEqual(app.aiProvider, .ollama)
        XCTAssertTrue(backend.requests.isEmpty)
        app.selectAIProvider(.deepSeek)
        app.acceptHostedAIConsent()
        XCTAssertEqual(app.aiProvider, .deepSeek)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.deepSeekConsentVersion), AppDefaults.deepSeekConsentVersion)
        XCTAssertTrue(app.hasHostedAIConsent)
        defaults.set("older-version", forKey: AppStorageKey.deepSeekConsentVersion)
        XCTAssertFalse(app.hasHostedAIConsent)
        XCTAssertTrue(backend.requests.isEmpty)
        let text = InterfaceText.resolve(AIProvider.deepSeek.hostedDisclosureResource, language: "en")
        for term in ["DeepSeek", "api.deepseek.com", "French", "references", "Keychain"] {
            XCTAssertTrue(text.contains(term), term)
        }
    }

    @MainActor
    func testSettingsConsentCancelLeavesPreviousProviderAndCredentialsUntouched() throws {
        let app = isolatedApplication()
        let presentation = SettingsActionPresentation()
        presentation.activate()
        app.selectAIProvider(.deepSeek, presentation: presentation)
        XCTAssertEqual(app.aiProvider, .ollama)
        let request = try XCTUnwrap(presentation.request)
        XCTAssertEqual(request.kind, .hostedConsent(.deepSeek))
        presentation.dismiss(id: request.id)
        XCTAssertEqual(app.aiProvider, .ollama)
        XCTAssertFalse(app.hasHostedAIConsent(for: .deepSeek))
    }

    @MainActor
    func testDeepSeekConsentDoesNotAuthorizeOtherVendorsAndSettingsCanAcceptIt() {
        let defaults = isolatedDefaults()
        let app = isolatedApplication(defaults: defaults)
        let presentation = SettingsActionPresentation()
        presentation.activate()
        app.selectAIProvider(.deepSeek, presentation: presentation)
        app.acceptHostedAIConsent(for: .deepSeek, presentation: presentation)
        XCTAssertEqual(app.aiProvider, .deepSeek)
        XCTAssertTrue(app.hasHostedAIConsent(for: .deepSeek))
        XCTAssertFalse(app.hasHostedAIConsent(for: .openAI))
        XCTAssertFalse(app.hasHostedAIConsent(for: .anthropic))
        XCTAssertFalse(defaults.bool(forKey: AppStorageKey.hostedAIConsentAccepted))
    }

    @MainActor
    func testSavedDeepSeekChoiceIsPreservedWithoutReplacingOtherModelsOrConsent() {
        let defaults = isolatedDefaults()
        defaults.set(AIProvider.deepSeek.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set("deepseek-v4-pro", forKey: AppStorageKey.deepSeekModel)
        defaults.set("my-openai-model", forKey: AppStorageKey.openAIModel)
        defaults.set("my-anthropic-model", forKey: AppStorageKey.anthropicModel)
        let app = isolatedApplication(defaults: defaults)
        XCTAssertEqual(app.aiProvider, .deepSeek)
        XCTAssertEqual(app.activeModelName, "deepseek-v4-pro")
        XCTAssertEqual(app.openAIModel, "my-openai-model")
        XCTAssertEqual(app.anthropicModel, "my-anthropic-model")
        XCTAssertFalse(app.hasHostedAIConsent)
        XCTAssertNil(defaults.string(forKey: AppStorageKey.deepSeekConsentVersion))
    }

    @MainActor
    func testFrenchRequestCapturesDeepSeekModelKeyAndEnlargedChoiceAfterConsent() throws {
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let backend = ControlledRunBackend()
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .deepSeek
        app.deepSeekModel = "deepseek-v4-pro"
        app.deepSeekAPIKey = "fixture-only-key"
        app.generateFrenchPaper(largePrint: true)
        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertTrue(app.showHostedAIConsent)
        app.acceptHostedAIConsent()
        let request = try XCTUnwrap(backend.requests.last)
        XCTAssertEqual(request.arguments.first, "generate-assessment")
        for value in ["deepseek", "deepseek-v4-pro", "--large-print", "v36"] {
            XCTAssertTrue(request.arguments.contains(value), value)
        }
        XCTAssertEqual(request.environment["KELDIN_API_KEY"], "fixture-only-key")
        XCTAssertFalse(request.arguments.contains("fixture-only-key"))
        XCTAssertEqual(app.generationCoordinator.activeJob?.configuration.provider, "deepseek")
        XCTAssertEqual(app.generationCoordinator.activeJob?.configuration.model, "deepseek-v4-pro")
        app.cancelGeneration()
    }

    @MainActor
    func testDeepSeekCannotGenerateUKEvenInPreviewAndRejectsOtherModelNames() {
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(AppDefaults.deepSeekConsentVersion, forKey: AppStorageKey.deepSeekConsentVersion)
        let backend = ControlledRunBackend()
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .deepSeek
        app.deepSeekAPIKey = "fixture-only-key"
        app.setDryRun(true)
        XCTAssertFalse(app.canGenerate)
        XCTAssertTrue(app.generationBlocker?.contains("French") == true)
        app.generate()
        XCTAssertTrue(backend.requests.isEmpty)
        app.deepSeekModel = "custom-unapproved-model"
        app.generateFrenchPaper(largePrint: false)
        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertTrue(app.showError)
    }

    func testDeepSeekIdentityAndUntestedChoices() {
        XCTAssertEqual(AIProvider(backendID: "deepseek"), .deepSeek)
        XCTAssertTrue(AIProvider.deepSeek.sendsPromptsOffDevice)
        XCTAssertEqual(HostedModelCandidate.forProvider(.deepSeek).map(\.model), ["deepseek-flash", "deepseek-v4-pro"])
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .deepSeek, model: "deepseek-v4-pro"), .unverified)
        let disclosure = InterfaceText.resolve(AIProvider.deepSeek.hostedDisclosureResource, language: "fr")
        XCTAssertTrue(disclosure.contains("références françaises publiques"))
        XCTAssertTrue(disclosure.contains("crédits API payants"))
        XCTAssertFalse(disclosure.contains("DeepSeek receives"))
    }

    func testPublicationRequiresSelectedDeepSeekIdentityRatherThanOpenAICompatibility() throws {
        let configuration = GenerationConfiguration(boardID: "fr-national-nsi", paperID: "written-2027",
            provider: "deepseek", model: "deepseek-v4-pro", seed: 42, dryRun: false,
            assessmentID: FrenchAssessmentRequest.assessmentID, authoringVersion: "v36")
        var identity: [String: Any] = ["provider": "deepseek", "model": "deepseek-v4-pro", "seed": 42,
            "prompt_version": FrenchLLMAssessmentRequest.promptVersion, "print_policy": FrenchLLMAssessmentRequest.printPolicy,
            "sql_source_policy": FrenchLLMAssessmentRequest.sqlSourcePolicy]
        let file = FileManager.default.temporaryDirectory.appendingPathComponent("DeepSeek-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: file) }
        func write() throws {
            try JSONSerialization.data(withJSONObject: ["schema_version": 1,
                "assessment": FrenchAssessmentRequest.assessmentID, "status": "unreviewed_draft",
                "generation_origin": "model_authored", "model_used": true,
                "teacher_review": "not_run", "empirical_calibration": "not_run", "identity": identity]).write(to: file)
        }
        try write()
        XCTAssertNoThrow(try FrenchLLMAssessmentRequest.validatePublication(at: file, configuration: configuration))
        identity["provider"] = "openai"
        try write()
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(at: file, configuration: configuration))
        identity["provider"] = "deepseek"
        identity["model"] = "deepseek-flash"
        try write()
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(at: file, configuration: configuration))
    }
}

private final class DeepSeekTestSecrets: SecretStoring {
    var values: [String: String] = [:]
    var failures: Set<String> = []
    func read(_ account: String) throws -> String { values[account] ?? "" }
    func save(_ value: String, account: String) throws {
        if failures.contains(account) { throw SecretStoreError.unexpected(operation: .write) }
        values[account] = value
    }
}
