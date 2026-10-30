// Create Keldin's scenes and connect shared application state to the interface.

import SwiftUI
import TipKit

enum AppLaunchPolicy {
    static func presentsMainWindow(environment: [String: String] = ProcessInfo.processInfo.environment) -> Bool {
        environment["XCTestConfigurationFilePath"] == nil
    }

    @MainActor
    static func makeApplication(environment: [String: String] = ProcessInfo.processInfo.environment) -> ApplicationCoordinator {
        if presentsMainWindow(environment: environment) {
            let failures = KeldinMigration.prepare()
            let application = ApplicationCoordinator()
            if !failures.isEmpty {
                application.errorMessage = InterfaceText.resolve(
                    "Some previous app data could not be imported. Use Import previous app data in Output Settings to retry.",
                    language: UserDefaults.standard.string(forKey: "interfaceLanguage") ?? "system"
                )
                application.showError = true
            }
            return application
        }
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
struct Keldin: App {
    @NSApplicationDelegateAdaptor(BackendTerminationDelegate.self) private var terminationDelegate
    @StateObject private var application = AppLaunchPolicy.makeApplication()

    init() {
        try? Tips.configure()
    }

    var body: some Scene {
        WindowGroup("Keldin", id: MainWindowRouting.sceneID, for: MainWindowIdentity.self) { _ in
            ContentView()
                .tint(Color("AccentColor"))
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        } defaultValue: {
            MainWindowIdentity.primary
        }
        .defaultLaunchBehavior(AppLaunchPolicy.presentsMainWindow() ? .presented : .suppressed)
        .commands {
            AppCommands(application: application)
        }

        Settings {
            SettingsPane()
                .tint(Color("AccentColor"))
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        }
    }
}
