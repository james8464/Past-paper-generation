import Foundation
import Security
import XCTest
@testable import Keldin

final class StorageLocalizationTests: XCTestCase {
    func testTypedCredentialMessagesFollowTheSelectedLanguage() {
        let cases: [(SecretStoreError, String, String)] = [
            (.status(operation: .read, status: errSecAuthFailed), "The API key couldn't be read from Keychain. Check Keychain access and try again.", "Impossible de lire la clé API dans le trousseau. Vérifiez l’accès au trousseau, puis réessayez."),
            (.status(operation: .write, status: errSecAuthFailed), "The API key couldn't be saved in Keychain. Check Keychain access and try again.", "Impossible d’enregistrer la clé API dans le trousseau. Vérifiez l’accès au trousseau, puis réessayez."),
            (.status(operation: .clear, status: errSecAuthFailed), "The API key couldn't be fully removed from Keychain. Retry to finish removing the saved entries.", "La clé API n’a pas pu être entièrement supprimée du trousseau. Réessayez pour supprimer les entrées restantes."),
            (.invalidData, "The saved API key couldn't be read. Replace it in Settings.", "Impossible de lire la clé API enregistrée. Remplacez-la dans Réglages."),
        ]
        for (error, english, french) in cases {
            XCTAssertEqual(error.message(language: "en"), english)
            XCTAssertEqual(error.message(language: "fr"), french)
        }
        for operation in [SecretStoreOperation.read, .write, .clear] {
            XCTAssertEqual(SecretStoreError.unexpected(operation: operation).message(language: "fr"), SecretStoreError.status(operation: operation, status: errSecAuthFailed).message(language: "fr"))
        }
    }

    func testRetentionWarningCatalogueHasFrenchAndEnglishCopy() {
        let history: LocalizedStringResource = "Some older history items couldn't be removed. They remain listed. Keldin will retry when history is saved or Keldin is reopened."
        let settings: LocalizedStringResource = "Some older history items couldn't be removed. They remain listed in History until cleanup succeeds."
        XCTAssertEqual(InterfaceText.resolve(history, language: "fr"), "Certains anciens éléments de l’historique n’ont pas pu être supprimés. Ils restent affichés. Keldin réessaiera lors du prochain enregistrement de l’historique ou au redémarrage.")
        XCTAssertEqual(InterfaceText.resolve(settings, language: "fr"), "Certains anciens éléments de l’historique n’ont pas pu être supprimés. Ils restent affichés dans Historique tant que leur suppression échoue.")
        XCTAssertTrue(InterfaceText.resolve(history, language: "en").contains("Keldin is reopened"))
        XCTAssertTrue(InterfaceText.resolve(settings, language: "en").hasPrefix("Some older history items"))
    }

    @MainActor
    func testHistoryAlertsUseSelectedLanguageAndKeepSystemDetails() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinStorageLocale-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let defaults = UserDefaults(suiteName: "StorageLocalization-\(UUID().uuidString)")!
        defaults.set("fr", forKey: "interfaceLanguage")
        let application = ApplicationCoordinator(defaults: defaults, secrets: LocalizationSecrets(), historyDirectory: directory, historyRecordRemover: { _ in
            throw NSError(domain: "StorageLocaleTest", code: 1, userInfo: [NSLocalizedDescriptionKey: "DETAIL_SENTINEL"])
        })
        let record = record()
        try application.recentDocumentStore.save(record)
        application.removeHistory(record)
        XCTAssertEqual(application.errorMessage, "Impossible de supprimer cet élément de l’historique. DETAIL_SENTINEL")
        defaults.set("en", forKey: "interfaceLanguage")
        application.removeHistory(record)
        XCTAssertEqual(application.errorMessage, "Couldn't remove this history item. DETAIL_SENTINEL")

        let blocked = directory.appendingPathComponent("blocked")
        try Data("preserved".utf8).write(to: blocked)
        defaults.set("fr", forKey: "interfaceLanguage")
        let failed = ApplicationCoordinator(defaults: defaults, secrets: LocalizationSecrets(), historyDirectory: blocked)
        XCTAssertTrue(failed.errorMessage.hasPrefix("Impossible de charger l’historique de création. "))
    }

    @MainActor
    func testSettingsAndCoordinatorKeepCredentialErrorsInChosenLanguage() {
        let defaults = UserDefaults(suiteName: "StorageLocalization-\(UUID().uuidString)")!
        defaults.set("fr", forKey: "interfaceLanguage")
        let settings = SettingsStore(defaults: defaults, secrets: LocalizationSecrets(failReads: true))
        let expected = "Impossible de lire la clé API dans le trousseau. Vérifiez l’accès au trousseau, puis réessayez."
        XCTAssertEqual(settings.secretFailureMessage(language: "fr"), expected)
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinCredentialLocale-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: directory) }
        let application = ApplicationCoordinator(defaults: defaults, secrets: LocalizationSecrets(failReads: true), historyDirectory: directory)
        XCTAssertEqual(application.errorMessage, expected)
        application.showError = false
        _ = application.saveSettingsAndReportSecretFailure()
        XCTAssertEqual(application.errorMessage, expected)
    }

    private func record() -> GenerationJobRecord {
        GenerationJobRecord(configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 1, dryRun: false), provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"), state: .completed, artifacts: [], qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false))
    }
}

private final class LocalizationSecrets: SecretStoring {
    var failReads = false
    init(failReads: Bool = false) { self.failReads = failReads }
    func read(_ account: String) throws -> String {
        if failReads { throw SecretStoreError.status(operation: .read, status: errSecAuthFailed) }
        return ""
    }
    func save(_ value: String, account: String) throws {}
}
