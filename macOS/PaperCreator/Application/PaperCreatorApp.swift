// Create Keldin's scenes and connect shared application state to the interface.

import SwiftUI
import TipKit

enum AppLaunchPolicy {
    static func presentsMainWindow(environment: [String: String] = ProcessInfo.processInfo.environment) -> Bool {
        environment["XCTestConfigurationFilePath"] == nil
    }

    @MainActor
    static func makeApplication(environment: [String: String] = ProcessInfo.processInfo.environment) -> ApplicationCoordinator {
        guard !presentsMainWindow(environment: environment) else { return ApplicationCoordinator() }
        // XCTest launches the app before individual test fixtures are created.
        let suite = "Keldin.TestHost.\(UUID().uuidString)"
        return ApplicationCoordinator(
            defaults: UserDefaults(suiteName: suite)!,
            secrets: TestHostSecrets(),
            historyDirectory: FileManager.default.temporaryDirectory.appendingPathComponent(suite, isDirectory: true)
        )
    }
}

private final class TestHostSecrets: SecretStoring {
    private var values: [String: String] = [:]
    func read(_ account: String) -> String { values[account] ?? "" }
    func save(_ value: String, account: String) { values[account] = value }
}

@main
struct PaperCreator: App {
    @StateObject private var application = AppLaunchPolicy.makeApplication()

    init() {
        try? Tips.configure()
    }

    var body: some Scene {
        WindowGroup("Keldin", id: "main") {
            ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        }
        .defaultLaunchBehavior(AppLaunchPolicy.presentsMainWindow() ? .presented : .suppressed)
        .commands {
            AppCommands(application: application)
        }

        Settings {
            SettingsPane()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        }
    }
}
