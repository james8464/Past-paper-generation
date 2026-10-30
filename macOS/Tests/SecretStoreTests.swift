import Foundation
import Security
import XCTest
@testable import Keldin

final class SecretStoreTests: XCTestCase {
    private let account = "fixture-account"

    @MainActor
    func testFreshHostedDefaultsAreCurrentCandidatesWithoutWritingOrReplacingStoredModels() {
        for mode in [DistributionMode.appStore, .direct] {
            let defaults = isolatedDefaults()
            let fresh = SettingsStore(defaults: defaults, secrets: FakeCredentialStore(), distributionMode: mode)
            XCTAssertEqual(fresh.openAIModel, "gpt-6.1-sol")
            XCTAssertEqual(fresh.anthropicModel, "claude-sonnet-5-5")
            XCTAssertNil(defaults.object(forKey: AppStorageKey.openAIModel))
            XCTAssertNil(defaults.object(forKey: AppStorageKey.anthropicModel))
            for saved in ["custom-pinned-model", "", "claude-sonnet-4-20250514"] {
                defaults.set(saved, forKey: AppStorageKey.openAIModel)
                defaults.set(saved, forKey: AppStorageKey.anthropicModel)
                let restored = SettingsStore(defaults: defaults, secrets: FakeCredentialStore(), distributionMode: mode)
                XCTAssertEqual(restored.openAIModel, saved)
                XCTAssertEqual(restored.anthropicModel, saved)
                XCTAssertEqual(defaults.string(forKey: AppStorageKey.openAIModel), saved)
                XCTAssertEqual(defaults.string(forKey: AppStorageKey.anthropicModel), saved)
            }
        }
        XCTAssertEqual(HostedModelCandidate.forProvider(.openAI).map(\.model), ["gpt-6.1-sol", "gpt-6-astra"])
        XCTAssertEqual(HostedModelCandidate.forProvider(.anthropic).map(\.model), ["claude-sonnet-5-5", "claude-opus-5-5"])
        XCTAssertTrue(HostedModelCandidate.forProvider(.apple).isEmpty)
        XCTAssertTrue(HostedModelCandidate.forProvider(.ollama).isEmpty)
    }

    @MainActor
    func testFreshProviderDefaultUsesBundledEngineOnlyForStoreDistribution() {
        for (mode, expected) in [(DistributionMode.appStore, AIProvider.apple), (.direct, .ollama)] {
            let defaults = isolatedDefaults()
            let settings = SettingsStore(defaults: defaults, secrets: FakeCredentialStore(), distributionMode: mode)
            XCTAssertEqual(settings.provider, expected)
            XCTAssertNil(defaults.object(forKey: AppStorageKey.aiProvider))
        }
    }

    @MainActor
    func testDistributionDefaultPreservesEverySavedProviderChoice() {
        for mode in [DistributionMode.appStore, .direct] {
            for provider in AIProvider.allCases {
                let defaults = isolatedDefaults()
                defaults.set(provider.rawValue, forKey: AppStorageKey.aiProvider)
                let settings = SettingsStore(defaults: defaults, secrets: FakeCredentialStore(), distributionMode: mode)
                XCTAssertEqual(settings.provider, provider)
                XCTAssertEqual(defaults.string(forKey: AppStorageKey.aiProvider), provider.rawValue)
            }
        }
    }

    func testMissingItemsAreDifferentFromReadFailures() throws {
        let missing = FakeKeychainAccess()
        XCTAssertEqual(try SecretStore.read(account, keychain: missing), "")

        let denied = FakeKeychainAccess()
        denied.enqueue(.read, service: "Keldin", status: errSecAuthFailed)
        XCTAssertThrowsError(try SecretStore.read(account, keychain: denied)) { error in
            XCTAssertEqual(error as? SecretStoreError, .status(operation: .read, status: errSecAuthFailed))
        }
        XCTAssertEqual(denied.calls.map(\.service), ["Keldin"])
    }

    func testUnreadableCurrentItemDoesNotFallBackToLegacy() throws {
        let keychain = FakeKeychainAccess()
        keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)
        keychain.enqueue(.read, service: "Keldin", status: errSecInteractionNotAllowed)

        XCTAssertThrowsError(try SecretStore.read(account, keychain: keychain))

        XCTAssertEqual(keychain.calls.map(\.service), ["Keldin"])
        XCTAssertEqual(keychain.value(account, service: KeldinMigration.legacyKeychainService), "legacy-fixture")
    }

    func testMalformedCurrentDataIsReportedInsteadOfTreatedAsMissing() throws {
        let keychain = FakeKeychainAccess()
        keychain.entries[keychain.key(account, service: "Keldin")] = Data([0xFF])
        XCTAssertThrowsError(try SecretStore.read(account, keychain: keychain)) { error in
            XCTAssertEqual(error as? SecretStoreError, .invalidData)
        }
    }

    func testLegacyImportKeepsTheOriginalAfterSuccessfulCurrentWrite() throws {
        let keychain = FakeKeychainAccess()
        keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)

        XCTAssertEqual(try SecretStore.read(account, keychain: keychain), "legacy-fixture")

        XCTAssertEqual(keychain.value(account, service: "Keldin"), "legacy-fixture")
        XCTAssertEqual(keychain.value(account, service: KeldinMigration.legacyKeychainService), "legacy-fixture")
        XCTAssertFalse(keychain.calls.contains { $0.action == .delete })
    }

    func testFailedLegacyImportDoesNotClaimPersistenceOrRemoveOriginal() throws {
        let keychain = FakeKeychainAccess()
        keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)
        keychain.enqueue(.add, service: "Keldin", status: errSecAuthFailed)

        XCTAssertThrowsError(try SecretStore.read(account, keychain: keychain))

        XCTAssertNil(keychain.value(account, service: "Keldin"))
        XCTAssertEqual(keychain.value(account, service: KeldinMigration.legacyKeychainService), "legacy-fixture")
        XCTAssertFalse(keychain.calls.contains { $0.action == .delete })
    }

    func testUpdateAndAddFailuresAreReportedWithoutDeletingCredentials() throws {
        for action in [FakeKeychainAccess.Action.update, .add] {
            let keychain = FakeKeychainAccess()
            if action == .update { keychain.put("current-fixture", account: account, service: "Keldin") }
            keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)
            keychain.enqueue(action, service: "Keldin", status: errSecAuthFailed)

            XCTAssertThrowsError(try SecretStore.save("replacement-fixture", account: account, keychain: keychain))

            XCTAssertFalse(keychain.calls.contains { $0.action == .delete })
            XCTAssertEqual(keychain.value(account, service: KeldinMigration.legacyKeychainService), "legacy-fixture")
            XCTAssertEqual(keychain.value(account, service: "Keldin"), action == .update ? "current-fixture" : nil)
        }
    }

    func testConcurrentAddUsesOneBoundedUpdateRetry() throws {
        let keychain = FakeKeychainAccess()
        keychain.put("concurrent-fixture", account: account, service: "Keldin")
        keychain.enqueue(.update, service: "Keldin", status: errSecItemNotFound)
        keychain.enqueue(.add, service: "Keldin", status: errSecDuplicateItem)

        try SecretStore.save("replacement-fixture", account: account, keychain: keychain)

        XCTAssertEqual(keychain.calls.map(\.action), [.update, .add, .update])
        XCTAssertEqual(keychain.value(account, service: "Keldin"), "replacement-fixture")
    }

    func testExplicitClearDeletesCurrentAndLegacyEntries() throws {
        let keychain = populatedKeychain()

        try SecretStore.save("", account: account, keychain: keychain)

        XCTAssertNil(keychain.value(account, service: "Keldin"))
        XCTAssertNil(keychain.value(account, service: KeldinMigration.legacyKeychainService))
        XCTAssertEqual(try SecretStore.read(account, keychain: keychain), "")
    }

    func testPartialDeleteFailureLeavesAnEmptyCurrentMarkerUntilReadFinishesCleanup() throws {
        for service in ["Keldin", KeldinMigration.legacyKeychainService] {
            let keychain = populatedKeychain()
            keychain.enqueue(.delete, service: service, status: errSecAuthFailed)

            XCTAssertThrowsError(try SecretStore.save("", account: account, keychain: keychain))

            XCTAssertEqual(keychain.value(account, service: "Keldin"), "")
            keychain.calls.removeAll()
            XCTAssertEqual(try SecretStore.read(account, keychain: keychain), "")
            XCTAssertFalse(keychain.calls.contains { $0.action == .read && $0.service == KeldinMigration.legacyKeychainService })
            XCTAssertEqual(keychain.calls.filter { $0.action == .delete }.count, 2)
            XCTAssertNil(keychain.value(account, service: "Keldin"))
            XCTAssertNil(keychain.value(account, service: KeldinMigration.legacyKeychainService))
        }
    }

    @MainActor
    func testFreshSettingsStoreRetainsAndRetriesAnIncompleteCredentialClear() {
        let account = SecretAccount.openAIAPIKey
        let keychain = FakeKeychainAccess()
        keychain.put("current-fixture", account: account, service: "Keldin")
        keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)
        let defaults = isolatedDefaults()
        let secrets = KeychainSecretStore(keychain: keychain)
        let first = SettingsStore(defaults: defaults, secrets: secrets)
        keychain.enqueue(.delete, service: KeldinMigration.legacyKeychainService, status: errSecAuthFailed)
        first.openAIAPIKey = ""
        XCTAssertFalse(first.save())
        XCTAssertEqual(keychain.value(account, service: "Keldin"), "")

        // Simulate another launch while cleanup is still denied. The empty
        // marker suppresses the legacy value, but must not erase its failure.
        keychain.enqueue(.delete, service: KeldinMigration.legacyKeychainService, status: errSecAuthFailed)
        let reopened = SettingsStore(defaults: defaults, secrets: secrets)
        XCTAssertEqual(reopened.openAIAPIKey, "")
        XCTAssertNotNil(reopened.credentialFailure(for: account))
        XCTAssertFalse(reopened.save(includeCredentials: false))

        // Retrying the unchanged empty field once access returns finishes the
        // same explicit clear, without writing the old credential back.
        XCTAssertTrue(reopened.save())
        XCTAssertNil(reopened.credentialFailure(for: account))
        XCTAssertNil(keychain.value(account, service: "Keldin"))
        XCTAssertNil(keychain.value(account, service: KeldinMigration.legacyKeychainService))
    }

    func testClearWriteFailureLeavesBothOriginalsAndDoesNotAttemptDeletion() throws {
        for currentExists in [true, false] {
            let keychain = populatedKeychain()
            if !currentExists { keychain.entries.removeValue(forKey: keychain.key(account, service: "Keldin")) }
            keychain.enqueue(currentExists ? .update : .add, service: "Keldin", status: errSecAuthFailed)

            XCTAssertThrowsError(try SecretStore.save("", account: account, keychain: keychain))

            XCTAssertFalse(keychain.calls.contains { $0.action == .delete })
            XCTAssertEqual(keychain.value(account, service: "Keldin"), currentExists ? "current-fixture" : nil)
            XCTAssertEqual(keychain.value(account, service: KeldinMigration.legacyKeychainService), "legacy-fixture")
        }
    }

    func testErrorsDoNotContainCredentialsOrAccountInput() throws {
        let keychain = FakeKeychainAccess()
        keychain.enqueue(.add, service: "Keldin", status: errSecAuthFailed)
        XCTAssertThrowsError(try SecretStore.save("PRIVATE_VALUE_SENTINEL", account: "PRIVATE_ACCOUNT_SENTINEL", keychain: keychain)) { error in
            XCTAssertFalse(error.localizedDescription.contains("PRIVATE_"))
            XCTAssertFalse(String(describing: error).contains("PRIVATE_"))
        }
    }

    @MainActor
    func testSettingsDoNotWriteUnchangedKeysOrClearAnUnreadableKey() {
        let secrets = FakeCredentialStore()
        secrets.values[SecretAccount.anthropicAPIKey] = "healthy-fixture"
        secrets.readFailures.insert(SecretAccount.openAIAPIKey)
        let defaults = isolatedDefaults()
        let settings = SettingsStore(defaults: defaults, secrets: secrets)
        settings.dryRun = true

        XCTAssertFalse(settings.save())

        XCTAssertTrue(defaults.bool(forKey: AppStorageKey.dryRun))
        XCTAssertTrue(secrets.writes.isEmpty)
        XCTAssertNotNil(settings.credentialFailure(for: SecretAccount.openAIAPIKey))
        XCTAssertEqual(settings.anthropicAPIKey, "healthy-fixture")
    }

    @MainActor
    func testChangedKeyPersistenceFailureRemainsVisibleUntilSuccessfulRetry() {
        let secrets = FakeCredentialStore()
        secrets.writeFailures.insert(SecretAccount.openAIAPIKey)
        let settings = SettingsStore(defaults: isolatedDefaults(), secrets: secrets)
        settings.openAIAPIKey = "replacement-fixture"

        XCTAssertFalse(settings.save())
        XCTAssertNotNil(settings.credentialFailure(for: SecretAccount.openAIAPIKey))

        secrets.writeFailures.removeAll()
        XCTAssertTrue(settings.save())
        XCTAssertNil(settings.credentialFailure(for: SecretAccount.openAIAPIKey))
        XCTAssertEqual(secrets.values[SecretAccount.openAIAPIKey], "replacement-fixture")
        let savedCount = secrets.writes.count
        settings.notificationsEnabled.toggle()
        XCTAssertTrue(settings.save())
        XCTAssertEqual(secrets.writes.count, savedCount)
    }

    @MainActor
    func testRevertingAFailedEditConfirmsThePreviouslySavedValue() {
        let secrets = FakeCredentialStore()
        secrets.values[SecretAccount.openAIAPIKey] = "current-fixture"
        let settings = SettingsStore(defaults: isolatedDefaults(), secrets: secrets)
        secrets.writeFailures.insert(SecretAccount.openAIAPIKey)
        settings.openAIAPIKey = "replacement-fixture"
        XCTAssertFalse(settings.save())

        secrets.writeFailures.removeAll()
        settings.openAIAPIKey = "current-fixture"

        XCTAssertTrue(settings.save())
        XCTAssertEqual(secrets.writes.count, 1)
        XCTAssertNil(settings.credentialFailure(for: SecretAccount.openAIAPIKey))
    }

    @MainActor
    func testPreferenceOnlySaveDoesNotRetryPendingCredentialChanges() {
        let secrets = FakeCredentialStore()
        let settings = SettingsStore(defaults: isolatedDefaults(), secrets: secrets)
        settings.openAIAPIKey = "pending-fixture"
        settings.dryRun = true

        XCTAssertTrue(settings.save(includeCredentials: false))
        XCTAssertTrue(secrets.writes.isEmpty)
        XCTAssertTrue(settings.save())
        XCTAssertEqual(secrets.writes.count, 1)
    }

    @MainActor
    func testArbitraryStoreErrorDescriptionsAreNotExposed() {
        let secrets = FakeCredentialStore()
        secrets.untypedReadFailure = true
        let settings = SettingsStore(defaults: isolatedDefaults(), secrets: secrets)

        XCTAssertEqual(settings.credentialFailure(for: SecretAccount.openAIAPIKey), .unexpected(operation: .read))
        XCTAssertFalse(settings.secretFailureMessage?.contains("PRIVATE_") ?? true)
    }

    @MainActor
    func testHostedGenerationDoesNotLaunchWhenItsChangedKeyCannotBeSaved() throws {
        let secrets = FakeCredentialStore()
        secrets.values[SecretAccount.openAIAPIKey] = "current-fixture"
        secrets.writeFailures.insert(SecretAccount.openAIAPIKey)
        let backend = CredentialTestBackend()
        let application = application(secrets: secrets, backend: backend)
        application.openAIAPIKey = "UNSAVED_VALUE_SENTINEL"

        application.generate()

        XCTAssertEqual(backend.runCount, 0)
        XCTAssertFalse(application.isRunning)
        XCTAssertTrue(application.showError)
        XCTAssertFalse(application.errorMessage.contains("UNSAVED_VALUE_SENTINEL"))
    }

    @MainActor
    func testPreviewCanRunWithoutTouchingAnUnreadableHostedKey() throws {
        let secrets = FakeCredentialStore()
        secrets.readFailures.insert(SecretAccount.openAIAPIKey)
        let backend = CredentialTestBackend()
        let application = application(secrets: secrets, backend: backend)
        application.setDryRun(true)

        application.generate()

        XCTAssertEqual(backend.runCount, 1)
        XCTAssertTrue(secrets.writes.isEmpty)
        application.cancelGeneration()
    }

    @MainActor
    func testLocalAndPreviewGenerationDoNotRetryPendingHostedCredentials() throws {
        for preview in [false, true] {
            let secrets = FakeCredentialStore()
            let backend = CredentialTestBackend()
            let application = application(secrets: secrets, backend: backend)
            secrets.writeFailures.insert(SecretAccount.openAIAPIKey)
            application.openAIAPIKey = "pending-fixture"
            application.saveAISettings()
            if preview {
                application.setDryRun(true)
            } else {
                application.selectAIProvider(.ollama)
                application.ollamaState = OllamaState(installed: true, running: true, command: nil, message: "Ollama is available.")
            }
            secrets.writeFailures.removeAll()
            secrets.saveAttempts.removeAll()

            application.generate()

            XCTAssertEqual(backend.runCount, 1)
            XCTAssertTrue(secrets.saveAttempts.isEmpty)
            application.cancelGeneration()
        }
    }

    private func populatedKeychain() -> FakeKeychainAccess {
        let keychain = FakeKeychainAccess()
        keychain.put("current-fixture", account: account, service: "Keldin")
        keychain.put("legacy-fixture", account: account, service: KeldinMigration.legacyKeychainService)
        return keychain
    }

    @MainActor
    private func application(secrets: FakeCredentialStore, backend: CredentialTestBackend) -> ApplicationCoordinator {
        let defaults = isolatedDefaults()
        defaults.set(AIProvider.openAI.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(true, forKey: AppStorageKey.hostedAIConsentAccepted)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        let history = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinSecretTests-\(UUID().uuidString)")
        addTeardownBlock { try? FileManager.default.removeItem(at: history) }
        let application = ApplicationCoordinator(defaults: defaults, secrets: secrets, historyDirectory: history, backend: backend)
        if let board = ExamCatalog.readyBoards.first(where: { $0.usesAI && $0.supports(.openAI) }) {
            application.selectBoard(board)
        }
        return application
    }
}

private final class FakeKeychainAccess: KeychainAccessing {
    enum Action: String { case read, update, add, delete }
    struct Call { let action: Action; let service: String }
    var entries: [String: Data] = [:]
    var calls: [Call] = []
    private var queued: [String: [OSStatus]] = [:]

    func key(_ account: String, service: String) -> String { "\(service):\(account)" }
    func put(_ value: String, account: String, service: String) { entries[key(account, service: service)] = Data(value.utf8) }
    func value(_ account: String, service: String) -> String? { entries[key(account, service: service)].flatMap { String(data: $0, encoding: .utf8) } }
    func enqueue(_ action: Action, service: String, status: OSStatus) { queued["\(action):\(service)", default: []].append(status) }

    func copyMatching(_ query: [String: Any]) -> KeychainReadResult {
        let (service, entry) = identifiers(query)
        let status = next(.read, service: service) ?? (entries[entry] == nil ? errSecItemNotFound : errSecSuccess)
        return KeychainReadResult(status: status, data: status == errSecSuccess ? entries[entry] : nil)
    }

    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus {
        let (service, entry) = identifiers(query)
        let status = next(.update, service: service) ?? (entries[entry] == nil ? errSecItemNotFound : errSecSuccess)
        if status == errSecSuccess { entries[entry] = attributes[kSecValueData as String] as? Data }
        return status
    }

    func add(_ attributes: [String: Any]) -> OSStatus {
        let (service, entry) = identifiers(attributes)
        let status = next(.add, service: service) ?? (entries[entry] == nil ? errSecSuccess : errSecDuplicateItem)
        if status == errSecSuccess { entries[entry] = attributes[kSecValueData as String] as? Data }
        return status
    }

    func delete(_ query: [String: Any]) -> OSStatus {
        let (service, entry) = identifiers(query)
        let status = next(.delete, service: service) ?? (entries[entry] == nil ? errSecItemNotFound : errSecSuccess)
        if status == errSecSuccess { entries.removeValue(forKey: entry) }
        return status
    }

    private func identifiers(_ query: [String: Any]) -> (String, String) {
        let service = query[kSecAttrService as String] as! String
        let account = query[kSecAttrAccount as String] as! String
        return (service, key(account, service: service))
    }

    private func next(_ action: Action, service: String) -> OSStatus? {
        calls.append(Call(action: action, service: service))
        let key = "\(action):\(service)"
        guard var statuses = queued[key], !statuses.isEmpty else { return nil }
        let value = statuses.removeFirst()
        queued[key] = statuses
        return value
    }
}

private final class FakeCredentialStore: SecretStoring {
    var values: [String: String] = [:]
    var readFailures: Set<String> = []
    var writeFailures: Set<String> = []
    var writes: [(String, String)] = []
    var saveAttempts: [String] = []
    var untypedReadFailure = false

    func read(_ account: String) throws -> String {
        if untypedReadFailure { throw PrivateCredentialError.fixture }
        if readFailures.contains(account) { throw SecretStoreError.status(operation: .read, status: errSecAuthFailed) }
        return values[account] ?? ""
    }

    func save(_ value: String, account: String) throws {
        saveAttempts.append(account)
        if writeFailures.contains(account) { throw SecretStoreError.status(operation: .write, status: errSecAuthFailed) }
        writes.append((account, value))
        values[account] = value
    }
}

private enum PrivateCredentialError: LocalizedError {
    case fixture
    var errorDescription: String? { "PRIVATE_VALUE_SENTINEL must never be shown." }
}

// Test calls are synchronous on the main actor; no helper or Keychain is launched.
private final class CredentialTestBackend: BackendRunning, @unchecked Sendable {
    private(set) var runCount = 0
    func run(arguments: [String], environment: [String: String], onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void, onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void) throws -> Process {
        runCount += 1
        return CredentialTestProcess()
    }
    func collect(arguments: [String]) async throws -> [BackendEvent] { [] }
}

private final class CredentialTestProcess: Process, @unchecked Sendable {
    override func terminate() {}
}
