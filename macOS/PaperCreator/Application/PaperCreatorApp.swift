import SwiftUI
import TipKit

@main
struct PaperCreator: App {
    @StateObject private var application = ApplicationCoordinator()

    init() {
        try? Tips.configure()
    }

    var body: some Scene {
        WindowGroup("Paper creator", id: "main") {
            ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        }
        .defaultLaunchBehavior(.presented)
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
