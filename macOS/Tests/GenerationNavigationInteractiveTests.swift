import AppKit
import SwiftUI
import XCTest
@testable import Keldin

final class GenerationNavigationInteractiveTests: XCTestCase {
    @MainActor
    func testNavigationDuringControlledGeneration() async throws {
        guard ProcessInfo.processInfo.environment["KELDIN_INTERACTIVE_NAVIGATION_CHECK"] == "1" else {
            throw XCTSkip("Opt-in computer-control check; ordinary CI runs the deterministic navigation tests.")
        }
        let suite = "Keldin.NavigationCheck.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        defaults.set("en", forKey: "interfaceLanguage")
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(suite)
        let backend = ControlledRunBackend()
        let application = ApplicationCoordinator(defaults: defaults, secrets: NavigationCheckSecrets(),
            historyDirectory: folder.appendingPathComponent("history"), backend: backend)
        application.outputFolder = folder.appendingPathComponent("output")
        application.dryRun = true
        application.generate()
        let original = try XCTUnwrap(application.generationCoordinator.activeJob)
        backend.requests.first?.onEvent(.progress(stage: "review",
            message: "Checking reference demand 2/17: 1b", progress: 0.8))

        let finished = expectation(description: "Computer-control navigation completed")
        let content = VStack(spacing: 0) {
            ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
            Button("Finish navigation check") { finished.fulfill() }
                .padding(10)
        }
        let window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 1_000, height: 760),
            styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        window.title = "Keldin navigation check"
        window.contentView = NSHostingView(rootView: content)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer {
            application.cancelGeneration()
            window.close()
            defaults.removePersistentDomain(forName: suite)
            try? FileManager.default.removeItem(at: folder)
        }
        print("KELDIN_INTERACTIVE_NAVIGATION_READY")
        await fulfillment(of: [finished], timeout: 180)
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob, original)
        XCTAssertEqual(backend.requests.count, 1)
    }
}

private final class NavigationCheckSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
