import SwiftUI

@main
struct PaperCreator: App {
    @StateObject private var appModel = AppViewModel()

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
