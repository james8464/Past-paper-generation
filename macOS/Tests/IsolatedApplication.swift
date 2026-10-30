import Foundation
import XCTest
@testable import Keldin

extension XCTestCase {
    func isolatedDefaults() -> UserDefaults {
        let suite = "KeldinTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        addTeardownBlock { UserDefaults(suiteName: suite)?.removePersistentDomain(forName: suite) }
        return defaults
    }

    @MainActor
    func isolatedApplication(
        defaults suppliedDefaults: UserDefaults? = nil, backend: any BackendRunning = BackendClient(),
        distributionMode: DistributionMode = .current
    ) -> ApplicationCoordinator {
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
            historyDirectory: history,
            backend: backend,
            distributionMode: distributionMode
        )
    }
}

extension ApplicationCoordinator {
    /// Legacy isolation fixtures need an available model now that French drafts use an LLM.
    @MainActor
    func generateFrenchFixture(largePrint: Bool) {
        if aiProvider == .ollama {
            ollamaState = OllamaState(installed: true, running: true, message: "Ready")
        }
        generateFrenchPaper(largePrint: largePrint)
    }
}

private final class IsolatedSecrets: SecretStoring {
    private var values: [String: String] = [:]

    func read(_ account: String) -> String { values[account] ?? "" }
    func save(_ value: String, account: String) { values[account] = value }
}
