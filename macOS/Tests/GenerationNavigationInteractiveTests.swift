import AppKit
import PDFKit
import SwiftUI
import XCTest
@testable import Keldin

final class GenerationNavigationInteractiveTests: XCTestCase {
    @MainActor
    func testCompactSidebarCanBeRevealedDuringControlledGeneration() async throws {
        guard ProcessInfo.processInfo.environment["KELDIN_INTERACTIVE_COMPACT_SIDEBAR_CHECK"] == "1" else {
            throw XCTSkip("Opt-in native compact-window check.")
        }
        let suite = "Keldin.CompactSidebarCheck.\(UUID().uuidString)"
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
        application.setDryRun(true)
        application.generate()
        let original = try XCTUnwrap(application.generationCoordinator.activeJob)
        let finished = expectation(description: "Sidebar revealed, French selected, sidebar hidden and window returned compact")
        // Capture the actual window before hosting; no geometry changes are made
        // after construction. The operator alone reveals/navigates/resizes it.
        let window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 760, height: 760),
            styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        window.title = "Keldin compact navigation acceptance check"
        defer { window.close() }
        recordCompactGeometry(window, phase: "before hosting")
        let content = VStack(spacing: 0) {
            ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
                .defaultAppStorage(defaults)
            HStack {
                Button("Record compact geometry") {
                    self.recordCompactGeometry(window, phase: "operator record")
                    print("COMPACT_SELECTION: \(String(describing: application.sidebarSelection)); visibility=\(defaults.string(forKey: AppStorageKey.navigationColumnVisibility) ?? "unset")")
                }
                Button("Finish compact sidebar check") {
                    self.recordCompactGeometry(window, phase: "after user actions")
                    finished.fulfill()
                }
            }.padding(10)
        }.defaultAppStorage(defaults)
        window.contentView = NSHostingView(rootView: content)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        recordCompactGeometry(window, phase: "after hosting, before user actions")
        let layoutReady = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard Thread.isMainThread else { return false }
            return MainActor.assumeIsolated { abs(window.contentMinSize.width - 720) < 0.01 }
        }, object: nil)
        await fulfillment(of: [layoutReady], timeout: 10)
        guard abs(window.contentMinSize.width - 720) < 0.01 else {
            return XCTFail("Initial compact layout did not settle; do not start the manual journey.")
        }
        recordCompactGeometry(window, phase: "settled initial layout, before user actions")
        let initialContentMinWidth = window.contentMinSize.width
        XCTAssertGreaterThanOrEqual(window.contentLayoutRect.width, 720)
        XCTAssertLessThan(window.contentLayoutRect.width, 840)
        XCTAssertEqual(initialContentMinWidth, 720, accuracy: 0.01)
        print("KELDIN_INTERACTIVE_COMPACT_SIDEBAR_READY")
        print("Start compact; record geometry, show the sidebar and select Baccalauréat · NSI. Native sidebar presentation may grow the window to about 904 points. Hide the sidebar, use standard Window > Move & Resize > Left to return compact, record geometry, then finish. No unchanged-width requirement applies while the sidebar is shown.")
        await fulfillment(of: [finished], timeout: 180)
        XCTAssertLessThan(window.contentLayoutRect.width, 840)
        XCTAssertEqual(window.contentMinSize.width, initialContentMinWidth, accuracy: 0.01)
        XCTAssertEqual(application.sidebarSelection, .frenchBaccalaureat)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.navigationColumnVisibility), "detail")
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob, original)
        XCTAssertEqual(backend.requests.count, 1)
    }

    @MainActor
    private func recordCompactGeometry(_ window: NSWindow, phase: String) {
        print("COMPACT_GEOMETRY [\(phase)]: frame=\(window.frame); contentLayoutRect=\(window.contentLayoutRect); contentMinSize=\(window.contentMinSize); minSize=\(window.minSize)")
        func visit(_ view: NSView, path: String) {
            if let split = view as? NSSplitView {
                print("COMPACT_SPLIT [\(phase)] \(path) \(type(of: split)): frame=\(split.frame); bounds=\(split.bounds); vertical=\(split.isVertical); divider=\(split.dividerThickness)")
                for (index, column) in split.arrangedSubviews.enumerated() {
                    let role = index == 0 ? "sidebar/first" : "detail/column\(index)"
                    print("COMPACT_COLUMN [\(phase)] \(path) \(role) \(type(of: column)): frame=\(column.frame); bounds=\(column.bounds); hidden=\(column.isHidden); collapsed=\(split.isSubviewCollapsed(column))")
                }
            }
            for (index, child) in view.subviews.enumerated() {
                visit(child, path: "\(path)/\(index)")
            }
        }
        if let content = window.contentView { visit(content, path: "content") }
    }

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
