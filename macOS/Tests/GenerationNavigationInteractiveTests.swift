import AppKit
import PDFKit
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
        defer {
            application.cancelGeneration()
            defaults.removePersistentDomain(forName: suite)
            try? FileManager.default.removeItem(at: folder)
        }
        application.outputFolder = folder.appendingPathComponent("output")
        try FileManager.default.createDirectory(at: application.outputFolder, withIntermediateDirectories: true)
        let olderURL = folder.appendingPathComponent("older-controlled.pdf")
        let currentURL = application.outputFolder.appendingPathComponent("current-controlled.pdf")
        for url in [olderURL, currentURL] {
            let pdf = PDFDocument()
            pdf.insert(PDFPage(), at: 0)
            XCTAssertTrue(pdf.write(to: url))
        }
        let older = GeneratedFile(role: "mark_scheme", url: olderURL,
            subject: "Older controlled paper", paper: "Saved before this run")
        application.generatedFiles = [older]
        application.dryRun = true
        application.generate()
        let original = try XCTUnwrap(application.generationCoordinator.activeJob)
        backend.requests.first?.onEvent(.file(role: "question_paper", path: currentURL.path))
        let current = try XCTUnwrap(application.currentGenerationFiles.first)
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
        defer { window.close() }
        print("KELDIN_INTERACTIVE_NAVIGATION_READY")
        print("RECENTS_CHECK: current-controlled.pdf must refuse removal; remove only older-controlled.pdf before finishing.")
        await fulfillment(of: [finished], timeout: 180)
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob, original)
        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertTrue(application.currentGenerationFiles.contains { $0.id == current.id })
        XCTAssertFalse(application.generatedFiles.contains { $0.id == older.id })
        XCTAssertTrue(FileManager.default.fileExists(atPath: olderURL.path))
    }
}

private final class NavigationCheckSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
