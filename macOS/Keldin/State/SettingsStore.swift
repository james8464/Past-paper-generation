// Persist user preferences and manage access to the selected output folder.

import Foundation
import Observation

@MainActor
@Observable
final class SettingsStore {
    var provider: AIProvider
    var ollamaModel: String
    var openAIModel: String
    var anthropicModel: String
    var deepSeekModel: String
    var appleModel: String
    var dryRun: Bool
    var parallelLocalReviews: Bool
    var parallelMLXGeneration: Bool
    var notificationsEnabled: Bool
    var historyRetentionLimit: Int
    var openAIAPIKey = ""
    var anthropicAPIKey = ""
    var deepSeekAPIKey = ""

    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored private let secrets: SecretStoring
    @ObservationIgnored private var savedCredentials: [String: String] = [:]
    private var credentialFailures: [String: SecretStoreError] = [:]

    init(
        defaults: UserDefaults = .standard,
        secrets: SecretStoring = KeychainSecretStore(),
        distributionMode: DistributionMode = .current
    ) {
        self.defaults = defaults
        self.secrets = secrets
        provider = AIProvider(
            rawValue: defaults.string(forKey: AppStorageKey.aiProvider) ?? ""
        ) ?? (distributionMode == .appStore ? .apple : .ollama)
        ollamaModel = defaults.string(forKey: AppStorageKey.ollamaModel)
            ?? AppDefaults.ollamaModel
        openAIModel = defaults.string(forKey: AppStorageKey.openAIModel)
            ?? AppDefaults.openAIModel
        anthropicModel = defaults.string(forKey: AppStorageKey.anthropicModel)
            ?? AppDefaults.anthropicModel
        deepSeekModel = defaults.string(forKey: AppStorageKey.deepSeekModel)
            ?? AppDefaults.deepSeekModel
        appleModel = defaults.string(forKey: AppStorageKey.appleModel)
            ?? AppDefaults.appleModel
        dryRun = defaults.bool(forKey: AppStorageKey.dryRun)
        parallelLocalReviews = defaults.object(forKey: AppStorageKey.parallelLocalReviews) as? Bool ?? false
        parallelMLXGeneration = defaults.object(forKey: AppStorageKey.parallelMLXGeneration) as? Bool ?? false
        notificationsEnabled = defaults.object(
            forKey: AppStorageKey.notificationsEnabled
        ) as? Bool ?? true
        let retention = defaults.integer(forKey: AppStorageKey.historyRetentionLimit)
        historyRetentionLimit = retention > 0 ? retention : 60
        openAIAPIKey = loadCredential(SecretAccount.openAIAPIKey)
        anthropicAPIKey = loadCredential(SecretAccount.anthropicAPIKey)
        deepSeekAPIKey = loadCredential(SecretAccount.deepSeekAPIKey)
    }

    @discardableResult
    func save(includeCredentials: Bool = true) -> Bool {
        historyRetentionLimit = min(500, max(1, historyRetentionLimit))
        defaults.set(provider.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set(ollamaModel, forKey: AppStorageKey.ollamaModel)
        defaults.set(openAIModel, forKey: AppStorageKey.openAIModel)
        defaults.set(anthropicModel, forKey: AppStorageKey.anthropicModel)
        defaults.set(deepSeekModel, forKey: AppStorageKey.deepSeekModel)
        defaults.set(appleModel, forKey: AppStorageKey.appleModel)
        defaults.set(dryRun, forKey: AppStorageKey.dryRun)
        defaults.set(parallelLocalReviews, forKey: AppStorageKey.parallelLocalReviews)
        defaults.set(parallelMLXGeneration, forKey: AppStorageKey.parallelMLXGeneration)
        defaults.set(notificationsEnabled, forKey: AppStorageKey.notificationsEnabled)
        defaults.set(
            historyRetentionLimit,
            forKey: AppStorageKey.historyRetentionLimit
        )
        if includeCredentials {
            saveCredential(openAIAPIKey, account: SecretAccount.openAIAPIKey)
            saveCredential(anthropicAPIKey, account: SecretAccount.anthropicAPIKey)
            saveCredential(deepSeekAPIKey, account: SecretAccount.deepSeekAPIKey)
        }
        return credentialFailures.isEmpty
    }

    var secretFailureMessage: String? {
        secretFailureMessage(language: "system")
    }

    func secretFailureMessage(language: String) -> String? {
        for account in [SecretAccount.openAIAPIKey, SecretAccount.anthropicAPIKey, SecretAccount.deepSeekAPIKey] {
            if let error = credentialFailures[account] { return error.message(language: language) }
        }
        return nil
    }

    func credentialFailure(for account: String) -> SecretStoreError? {
        credentialFailures[account]
    }

    private func loadCredential(_ account: String) -> String {
        do {
            let value = try secrets.read(account)
            savedCredentials[account] = value
            credentialFailures.removeValue(forKey: account)
            return value
        } catch {
            let failure = (error as? SecretStoreError) ?? .unexpected(operation: .read)
            if failure == .incompleteClear { savedCredentials[account] = "" }
            credentialFailures[account] = failure
            return ""
        }
    }

    private func saveCredential(_ value: String, account: String) {
        // A failed read leaves no known baseline. Its empty UI placeholder is
        // not an instruction to erase an inaccessible credential.
        guard let saved = savedCredentials[account] else {
            if !value.isEmpty { writeCredential(value, account: account) }
            return
        }
        // A failed clear can already have replaced the current item with an
        // empty marker. Reverting the field still needs a confirmed write.
        guard saved != value || credentialFailures[account] != nil else { return }
        writeCredential(value, account: account)
    }

    private func writeCredential(_ value: String, account: String) {
        do {
            try secrets.save(value, account: account)
            savedCredentials[account] = value
            credentialFailures.removeValue(forKey: account)
        } catch {
            // Injected stores can throw arbitrary errors. Expose only the safe
            // typed operation, never their description or credential data.
            credentialFailures[account] = (error as? SecretStoreError) ?? .unexpected(operation: .write)
        }
    }
}
