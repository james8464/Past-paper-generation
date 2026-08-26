import SwiftUI
import TipKit

@main
struct PaperCreator: App {
    @StateObject private var appModel = AppViewModel()

    init() {
        try? Tips.configure()
    }

    var body: some Scene {
        WindowGroup("Paper creator", id: "main") {
            ContentView()
                .environmentObject(appModel)
        }
        .defaultLaunchBehavior(.presented)
        .commands {
            AppCommands(appModel: appModel)
        }

        Settings {
            SettingsPane()
                .environmentObject(appModel)
        }
    }
}
