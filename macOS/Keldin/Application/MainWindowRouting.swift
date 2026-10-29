// One logical main window, regardless of which scene initiates navigation.

enum MainWindowIdentity: String, Codable, Hashable, Sendable {
    case primary
}

enum MainWindowRoute: Equatable {
    case creation
    case documents
    case history
    case benchmark
    case help(HelpTopic)
    case welcome
    case latestPreview(role: String)
    case runBenchmark
}

@MainActor
protocol MainWindowNavigating: AnyObject {
    func showCreationWorkspace()
    func showDocuments()
    func showHistory()
    func showBenchmarkPage()
    func showHelpGuide(topic: HelpTopic)
    func showWelcomeGuide()
    func previewGeneratedFile(role: String)
    func startBenchmark()
}

extension ApplicationCoordinator: MainWindowNavigating { }

@MainActor
enum MainWindowRouting {
    static let sceneID = "main"

    static func navigate(
        _ route: MainWindowRoute,
        application: any MainWindowNavigating,
        openWindow: (MainWindowIdentity) -> Void
    ) {
        switch route {
        case .creation: application.showCreationWorkspace()
        case .documents: application.showDocuments()
        case .history: application.showHistory()
        case .benchmark: application.showBenchmarkPage()
        case let .help(topic): application.showHelpGuide(topic: topic)
        case .welcome: application.showWelcomeGuide()
        case let .latestPreview(role): application.previewGeneratedFile(role: role)
        case .runBenchmark:
            application.showBenchmarkPage()
            openWindow(.primary)
            application.startBenchmark()
            return
        }
        openWindow(.primary)
    }
}
