import Foundation
import Observation

@MainActor
@Observable
final class SettingsStore {
    var provider: AIProvider
    var ollamaModel: String
    var openAIModel: String
    var anthropicModel: String
    var appleModel: String
    var dryRun: Bool
    var notificationsEnabled: Bool
    var historyRetentionLimit: Int
    var openAIAPIKey: String
    var anthropicAPIKey: String

    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored private let secrets: SecretStoring

    init(
        defaults: UserDefaults = .standard,
        secrets: SecretStoring = KeychainSecretStore()
    ) {
        self.defaults = defaults
        self.secrets = secrets
        provider = AIProvider(
            rawValue: defaults.string(forKey: AppStorageKey.aiProvider) ?? ""
        ) ?? .ollama
        ollamaModel = defaults.string(forKey: AppStorageKey.ollamaModel)
            ?? AppDefaults.ollamaModel
        openAIModel = defaults.string(forKey: AppStorageKey.openAIModel)
            ?? AppDefaults.openAIModel
        anthropicModel = defaults.string(forKey: AppStorageKey.anthropicModel)
            ?? AppDefaults.anthropicModel
        appleModel = defaults.string(forKey: AppStorageKey.appleModel)
            ?? AppDefaults.appleModel
        dryRun = defaults.bool(forKey: AppStorageKey.dryRun)
        notificationsEnabled = defaults.object(
            forKey: AppStorageKey.notificationsEnabled
        ) as? Bool ?? true
        let retention = defaults.integer(forKey: AppStorageKey.historyRetentionLimit)
        historyRetentionLimit = retention > 0 ? retention : 60
        openAIAPIKey = secrets.read(SecretAccount.openAIAPIKey)
        anthropicAPIKey = secrets.read(SecretAccount.anthropicAPIKey)
    }

    func save() {
        historyRetentionLimit = min(500, max(1, historyRetentionLimit))
        defaults.set(provider.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set(ollamaModel, forKey: AppStorageKey.ollamaModel)
        defaults.set(openAIModel, forKey: AppStorageKey.openAIModel)
        defaults.set(anthropicModel, forKey: AppStorageKey.anthropicModel)
        defaults.set(appleModel, forKey: AppStorageKey.appleModel)
        defaults.set(dryRun, forKey: AppStorageKey.dryRun)
        defaults.set(notificationsEnabled, forKey: AppStorageKey.notificationsEnabled)
        defaults.set(
            historyRetentionLimit,
            forKey: AppStorageKey.historyRetentionLimit
        )
        secrets.save(openAIAPIKey, account: SecretAccount.openAIAPIKey)
        secrets.save(anthropicAPIKey, account: SecretAccount.anthropicAPIKey)
    }
}
