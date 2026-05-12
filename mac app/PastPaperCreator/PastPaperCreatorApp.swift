import SwiftUI

@main
struct PastPaperCreator: App {
    @StateObject private var appModel = AppViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appModel)
        }

        Settings {
            SettingsPane()
                .environmentObject(appModel)
        }
    }
}
