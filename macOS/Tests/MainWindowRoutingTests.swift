import Foundation
import XCTest
@testable import Keldin

final class MainWindowRoutingTests: XCTestCase {
    @MainActor
    func testDestinationsOpenTheStableMainIdentityAfterUpdatingSelection() {
        let cases: [(MainWindowRoute, String)] = [
            (.creation, "creation"),
            (.documents, "documents"),
            (.history, "history"),
            (.benchmark, "benchmark"),
            (.help(.choosingAModel), "help:choosingAModel"),
            (.welcome, "welcome"),
            (.latestPreview(role: "question_paper"), "preview:question_paper"),
        ]
        for (route, expected) in cases {
            let navigator = NavigationRecorder()
            MainWindowRouting.navigate(route, application: navigator) { identity in
                XCTAssertEqual(identity, .primary)
                navigator.calls.append("open")
            }
            XCTAssertEqual(navigator.calls, [expected, "open"])
        }
    }

    @MainActor
    func testRunBenchmarkShowsItsDestinationBeforeStartingWork() {
        let navigator = NavigationRecorder()
        MainWindowRouting.navigate(.runBenchmark, application: navigator) { _ in
            navigator.calls.append("open")
        }
        XCTAssertEqual(navigator.calls, ["benchmark", "open", "runBenchmark"])
    }

    @MainActor
    func testRepeatedNavigationUsesOneLogicalWindowIdentity() {
        let navigator = NavigationRecorder()
        var opened: [MainWindowIdentity] = []
        for route in [MainWindowRoute.documents, .history] {
            MainWindowRouting.navigate(route, application: navigator) { opened.append($0) }
        }
        XCTAssertEqual(opened, [.primary, .primary])
        XCTAssertEqual(MainWindowRouting.sceneID, "main")
    }

    func testStableIdentityRoundTripsForSceneRestoration() throws {
        let encoded = try JSONEncoder().encode(MainWindowIdentity.primary)
        XCTAssertEqual(
            try JSONDecoder().decode(MainWindowIdentity.self, from: encoded), .primary
        )
    }
}

@MainActor
private final class NavigationRecorder: MainWindowNavigating {
    var calls: [String] = []

    func showCreationWorkspace() { calls.append("creation") }
    func showDocuments() { calls.append("documents") }
    func showHistory() { calls.append("history") }
    func showBenchmarkPage() { calls.append("benchmark") }
    func showHelpGuide(topic: HelpTopic) { calls.append("help:\(topic.rawValue)") }
    func showWelcomeGuide() { calls.append("welcome") }
    func previewGeneratedFile(role: String) { calls.append("preview:\(role)") }
    func startBenchmark() { calls.append("runBenchmark") }
}
