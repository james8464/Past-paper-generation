import AppKit
import PDFKit
import SwiftUI
import XCTest
@testable import Keldin

final class PreviousDataImportInteractiveTests: XCTestCase {
    @MainActor
    func testNavigationAndSettingsDuringControlledImport() async throws {
        guard ProcessInfo.processInfo.environment["KELDIN_INTERACTIVE_IMPORT_CHECK"] == "1" else {
            throw XCTSkip("Opt-in controlled import window check; no installed user data is used.")
        }
        let suite = "Keldin.ImportWindowCheck.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        defaults.set("en", forKey: "interfaceLanguage")
        defaults.set("output", forKey: AppStorageKey.settingsPane)
        defaults.set(2, forKey: KeldinMigration.completionKey)
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(suite)
        let source = folder.appendingPathComponent("previous")
        let destination = folder.appendingPathComponent("imported")
        let backend = ControlledRunBackend()
        let application = ApplicationCoordinator(
            defaults: defaults, secrets: ImportWindowSecrets(),
            historyDirectory: destination.appendingPathComponent("JobHistory"),
            backend: backend, distributionMode: .appStore
        )
        let state = ImportWindowCleanup()
        let successGate = ImportWindowGate()
        let failureGate = ImportWindowGate()
        addTeardownBlock { @MainActor in
            // Release-before-pause is remembered. Never remove files while a copy
            // task can still reach them, including on timeout or assertion failure.
            await successGate.release()
            await failureGate.release()
            for task in state.tasks { await task.value }
            application.cancelGeneration()
            state.windows.forEach { $0.close() }
            defaults.removePersistentDomain(forName: suite)
            try? FileManager.default.removeItem(at: folder)
        }
        application.showWelcome = false
        application.showDocuments()
        application.outputFolder = folder.appendingPathComponent("exports")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        let sourcePDF = source.appendingPathComponent("owned-sample.pdf")
        let sample = PDFDocument()
        sample.insert(PDFPage(), at: 0)
        XCTAssertTrue(sample.write(to: sourcePDF))
        let originalBytes = try Data(contentsOf: sourcePDF)
        let historyVisited = expectation(description: "History visited during held import")
        let documentsVisited = expectation(description: "Documents visited during held import")
        let successReleased = expectation(description: "Successful import released visually")
        let failureReleased = expectation(description: "Failed import released visually")
        let finished = expectation(description: "Import error and cleanup inspected")
        let controls = ImportWindowControls()
        var accessEvents: [String] = []
        let successfulImport = try XCTUnwrap(application.beginPreviousAppDataImport(
            from: source, destination: destination, presentation: application.settingsPresentation,
            copyFiles: { from, to in
                await successGate.pause()
                try await PreviousAppDataFileImporter.shared.copy(from: from, to: to)
            },
            startAccess: { _ in accessEvents.append("start"); return true },
            stopAccess: { _ in accessEvents.append("stop") }
        ))
        state.tasks.append(successfulImport)
        await successGate.waitForStart()

        let main = ContentView()
            .environmentObject(application)
            .environment(application.catalogStore)
            .environment(application.benchmarkCoordinator)
            .environment(application.generationCoordinator)
            .defaultAppStorage(defaults)
        let settings = VStack {
            SettingsPane().environmentObject(application)
            ImportWindowButtons(controls: controls,
                recordHistory: {
                    XCTAssertTrue(application.isImportingPreviousData)
                    XCTAssertEqual(application.sidebarSelection, .history)
                    historyVisited.fulfill()
                }, recordDocuments: {
                    XCTAssertTrue(application.isImportingPreviousData)
                    XCTAssertEqual(application.sidebarSelection, .documents)
                    documentsVisited.fulfill()
                }, releaseSuccess: {
                    Task { await successGate.release(); successReleased.fulfill() }
                }, releaseFailure: {
                    Task { await failureGate.release(); failureReleased.fulfill() }
                }, finish: { finished.fulfill() })
        }.defaultAppStorage(defaults)
        let mainWindow = importWindow(title: "Keldin controlled import navigation", root: main,
                                      rect: NSRect(x: 30, y: 70, width: 900, height: 700))
        state.windows.append(mainWindow)
        let settingsWindow = importWindow(title: "Keldin controlled import settings", root: settings,
                                          rect: NSRect(x: 950, y: 70, width: 680, height: 650))
        state.windows.append(settingsWindow)
        NSApp.activate(ignoringOtherApps: true)
        XCTAssertTrue(application.isImportingPreviousData)
        XCTAssertFalse(application.canImportPreviousData)
        print("KELDIN_INTERACTIVE_IMPORT_READY: inspect Output progress and disabled Import; visit History and Documents, record each, then release success.")
        await fulfillment(of: [historyVisited, documentsVisited, successReleased], timeout: 180)
        await successfulImport.value
        XCTAssertFalse(application.isImportingPreviousData)
        XCTAssertTrue(application.canImportPreviousData)
        XCTAssertEqual(accessEvents, ["start", "stop"])
        XCTAssertEqual(try Data(contentsOf: destination.appendingPathComponent("owned-sample.pdf")), originalBytes)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(backend.requests.isEmpty)
        controls.phase = 1

        let failedImport = try XCTUnwrap(application.beginPreviousAppDataImport(
            from: source, destination: destination, presentation: application.settingsPresentation,
            copyFiles: { _, _ in
                await failureGate.pause()
                throw CocoaError(.fileReadNoPermission)
            },
            startAccess: { _ in accessEvents.append("start"); return true },
            stopAccess: { _ in accessEvents.append("stop") }
        ))
        state.tasks.append(failedImport)
        await failureGate.waitForStart()
        XCTAssertTrue(application.isImportingPreviousData)
        print("KELDIN_INTERACTIVE_IMPORT_FAILURE_READY: inspect busy state again; release failure, inspect Settings error, dismiss it, then Finish.")
        await fulfillment(of: [failureReleased], timeout: 180)
        await failedImport.value
        XCTAssertFalse(application.isImportingPreviousData)
        XCTAssertTrue(application.canImportPreviousData)
        XCTAssertEqual(accessEvents, ["start", "stop", "start", "stop"])
        XCTAssertEqual(application.status, "Error")
        guard case .error = application.settingsPresentation.request?.kind else {
            return XCTFail("Import failure must be presented in Settings.")
        }
        controls.phase = 2
        await fulfillment(of: [finished], timeout: 180)
        XCTAssertEqual(try Data(contentsOf: sourcePDF), originalBytes)
        XCTAssertEqual(try Data(contentsOf: destination.appendingPathComponent("owned-sample.pdf")), originalBytes)
        XCTAssertTrue(backend.requests.isEmpty)
        print("KELDIN_INTERACTIVE_IMPORT_COMPLETE")
    }

    @MainActor
    private func importWindow<Content: View>(title: String, root: Content, rect: NSRect) -> NSWindow {
        let window = NSWindow(contentRect: rect, styleMask: [.titled, .closable, .resizable],
                              backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        window.title = title
        window.contentView = NSHostingView(rootView: root)
        window.makeKeyAndOrderFront(nil)
        return window
    }
}

@MainActor
private final class ImportWindowCleanup {
    var tasks: [Task<Void, Never>] = []
    var windows: [NSWindow] = []
}

@MainActor
private final class ImportWindowControls: ObservableObject {
    @Published var phase = 0
}

private struct ImportWindowButtons: View {
    @ObservedObject var controls: ImportWindowControls
    let recordHistory: () -> Void
    let recordDocuments: () -> Void
    let releaseSuccess: () -> Void
    let releaseFailure: () -> Void
    let finish: () -> Void
    var body: some View {
        VStack {
            HStack {
                Button("Record History while busy", action: recordHistory)
                Button("Record Documents while busy", action: recordDocuments)
                Button("Release successful import", action: releaseSuccess)
            }.disabled(controls.phase != 0)
            HStack {
                Button("Release failing import", action: releaseFailure).disabled(controls.phase != 1)
                Button("Finish import check", action: finish).disabled(controls.phase != 2)
            }
        }.padding(10)
    }
}

private actor ImportWindowGate {
    private var started = false
    private var released = false
    private var startWaiter: CheckedContinuation<Void, Never>?
    private var copyWaiter: CheckedContinuation<Void, Never>?
    func pause() async {
        started = true
        startWaiter?.resume()
        startWaiter = nil
        if !released { await withCheckedContinuation { copyWaiter = $0 } }
    }
    func waitForStart() async {
        if !started { await withCheckedContinuation { startWaiter = $0 } }
    }
    func release() {
        released = true
        copyWaiter?.resume()
        copyWaiter = nil
    }
}

private final class ImportWindowSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
