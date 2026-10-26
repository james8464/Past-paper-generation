import Foundation
import XCTest
@testable import PaperCreator

extension XCTestCase {
    func isolatedDefaults() -> UserDefaults {
        let suite = "KeldinTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        addTeardownBlock { UserDefaults(suiteName: suite)?.removePersistentDomain(forName: suite) }
        return defaults
    }

    @MainActor
    func isolatedApplication(defaults suppliedDefaults: UserDefaults? = nil) -> ApplicationCoordinator {
        let suite = "KeldinTests.\(UUID().uuidString)"
        let defaults = suppliedDefaults ?? isolatedDefaults()
        let history = FileManager.default.temporaryDirectory
            .appendingPathComponent(suite, isDirectory: true)
        addTeardownBlock {
            if FileManager.default.fileExists(atPath: history.path) {
                try FileManager.default.removeItem(at: history)
            }
        }
        return ApplicationCoordinator(
            defaults: defaults,
            secrets: IsolatedSecrets(),
            historyDirectory: history
        )
    }
}

private final class IsolatedSecrets: SecretStoring {
    private var values: [String: String] = [:]

    func read(_ account: String) -> String { values[account] ?? "" }
    func save(_ value: String, account: String) { values[account] = value }
}
