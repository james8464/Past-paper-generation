import SwiftUI

@main
struct PastPaperCreator: App {
    @StateObject private var appModel = AppViewModel()

    var body: some Scene {
        WindowGroup("Past Paper Creator", id: "main") {
            ContentView()
                .environmentObject(appModel)
        }
        .restorationBehavior(.disabled)
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
