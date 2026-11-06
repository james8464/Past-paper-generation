import AppKit
import Combine
import Foundation
import SwiftUI
import XCTest
@testable import Keldin

final class GenerationCancellationInteractiveTests: XCTestCase {
    @MainActor
    func testUserCancelsFailedGenerationAndRetriesInIsolatedWorkspace() async throws {
        guard ProcessInfo.processInfo.environment["KELDIN_INTERACTIVE_GENERATION_RECOVERY_CHECK"] == "1" else {
            throw XCTSkip("Opt-in controlled Cancel/failure/retry window; no installed user data is used.")
        }
        let domains = Set(["com.jamesdurup.Keldin", Bundle.main.bundleIdentifier].compactMap { $0 })
        let standardBefore = Dictionary(uniqueKeysWithValues: domains.map {
            ($0, NSDictionary(dictionary: UserDefaults.standard.persistentDomain(forName: $0) ?? [:]))
        })
        let suite = "Keldin.GenerationRecovery.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        defaults.set("en", forKey: "interfaceLanguage")
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(suite)
        let backend = RecoveryFixtureBackend()
        let application = ApplicationCoordinator(defaults: defaults, secrets: RecoveryFixtureSecrets(),
            historyDirectory: folder.appendingPathComponent("history"), backend: backend,
            appleIntelligenceChecker: { _ in .unchecked })
        let window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 1_100, height: 850),
            styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        defer {
            window.contentView = nil
            window.close()
            application.cancelGeneration()
            defaults.removePersistentDomain(forName: suite)
            try? FileManager.default.removeItem(at: folder)
            for (domain, original) in standardBefore {
                XCTAssertEqual(original, NSDictionary(dictionary:
                    UserDefaults.standard.persistentDomain(forName: domain) ?? [:]))
            }
        }
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let sentinel = folder.appendingPathComponent("owned-sentinel.txt")
        let bytes = Data("Existing owned fixture data must survive retries.\n".utf8)
        try bytes.write(to: sentinel)
        application.outputFolder = folder.appendingPathComponent("output")
        try FileManager.default.createDirectory(at: application.outputFolder, withIntermediateDirectories: true)
        application.aiProvider = .ollama
        application.selectedModel = RecoveryFixtureBackend.model
        application.availableModels = [RecoveryFixtureBackend.model]
        application.hasLoadedOllamaModels = true
        application.ollamaState = OllamaState(installed: true, running: true, message: "Ready")
        application.selectBoard(try XCTUnwrap(ExamCatalog.readyBoards.first {
            $0.usesAI && $0.supports(.ollama)
        }))
        application.setDryRun(false)
        XCTAssertTrue(application.canGenerate)
        application.generate()
        XCTAssertEqual(backend.runs.requests.count, 1)
        backend.runs.requests.first?.onEvent(.progress(stage: "review",
            message: "Reviewing owned fixture content", progress: 0.35))

        let finished = expectation(description: "Human Cancel/failure/retry journey completed")
        let controls = RecoveryFixtureControls(application: application, backend: backend.runs,
            finish: { finished.fulfill() })
        let content = VStack(spacing: 0) {
            ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
            RecoveryFixtureControlBar(controls: controls)
        }.defaultAppStorage(defaults)
        window.title = "Keldin generation recovery check"
        window.contentView = NSHostingView(rootView: content)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        print("KELDIN_INTERACTIVE_GENERATION_RECOVERY_READY: use only this window's sidebar, real Cancel/Create/OK buttons, and labelled fixture checks; no app menus, shortcuts or Settings.")
        print("RECOVERY_BOARD: \(application.selectedBoard.subjectTitle), \(application.selectedBoard.title)")
        await fulfillment(of: [finished], timeout: 240)
        XCTAssertEqual(controls.phase, 4)
        XCTAssertEqual(try Data(contentsOf: sentinel), bytes)
        XCTAssertFalse(application.isRunning)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertTrue(application.generatedFiles.isEmpty)
    }
}

@MainActor
private final class RecoveryFixtureControls: ObservableObject {
    @Published private(set) var phase = 0
    let application: ApplicationCoordinator
    let backend: ControlledRunBackend
    private let finish: () -> Void

    init(application: ApplicationCoordinator, backend: ControlledRunBackend, finish: @escaping () -> Void) {
        self.application = application
        self.backend = backend
        self.finish = finish
    }

    func checkCancel() {
        guard phase == 0, backend.requests.count == 1, !application.isRunning else {
            return XCTFail("Press the real generation Cancel before Check Cancel.")
        }
        XCTAssertEqual(backend.cancelledProcessIDs.count, 1)
        XCTAssertEqual(application.status, "Cancelled")
        XCTAssertNil(application.generationProgress)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertTrue(application.canGenerate)
        XCTAssertEqual(application.recentDocumentStore.records.map(\.state), [.cancelled])
        phase = 1
        print("KELDIN_RECOVERY_CANCEL_CHECKED: return to the selected board and press its real Create button.")
    }

    func failSecondRun() {
        guard phase == 1, backend.requests.count == 2, application.isRunning else {
            return XCTFail("Start the replacement with the real Create button first.")
        }
        backend.requests[1].onEvent(.error(message: "Owned fixture model is unavailable. Choose a model and try again.",
            code: "generation_failed"))
        backend.requests[1].onFinish(.success(1))
        XCTAssertTrue(application.showError)
        XCTAssertFalse(application.isRunning)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertEqual(application.recentDocumentStore.records.map { $0.state.rawValue }.sorted(),
            ["cancelled", "failed"])
        phase = 2
        print("KELDIN_RECOVERY_FAILURE_READY: inspect the real error alert, press OK, then the real Create button again.")
    }

    func checkRetry() {
        guard phase == 2, backend.requests.count == 3, application.isRunning, !application.showError else {
            return XCTFail("Dismiss the real error alert and start the retry with Create first.")
        }
        let currentID = application.generationCoordinator.activeJob?.id
        XCTAssertNotNil(currentID)
        backend.requests[2].onEvent(.progress(stage: "review", message: "Owned retry is running", progress: 0.45))
        let status = application.status
        for request in backend.requests.prefix(2) {
            request.onEvent(.progress(stage: "late", message: "Stale progress must be ignored", progress: 0.99))
            request.onEvent(.file(role: "question_paper", path: "/owned-stale-callback/not-a-real-file.pdf"))
            request.onEvent(.done(message: "Stale completion must be ignored"))
            request.onEvent(.error(message: "Stale error must be ignored", code: "generation_failed"))
            request.onFinish(.success(0))
        }
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, currentID)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.generationProgress, 0.45)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
        XCTAssertEqual(backend.requests.count, 3)
        phase = 3
        print("KELDIN_RECOVERY_RETRY_CHECKED: inspect unchanged running progress, press real Cancel, then Finish recovery check.")
    }

    func complete() {
        guard phase == 3, !application.isRunning else {
            return XCTFail("Cancel the retry with the real Cancel button before finishing.")
        }
        XCTAssertEqual(backend.cancelledProcessIDs.count, 2)
        XCTAssertEqual(backend.requests.count, 3)
        XCTAssertEqual(application.recentDocumentStore.records.count, 3)
        XCTAssertFalse(application.recentDocumentStore.records.contains { $0.state == .completed })
        phase = 4
        finish()
    }
}

@MainActor
private struct RecoveryFixtureControlBar: View {
    @ObservedObject var controls: RecoveryFixtureControls
    var body: some View {
        HStack {
            Text("Owned fake-provider check \(controls.phase + 1)/4")
            Button("Check Cancel", action: controls.checkCancel).disabled(controls.phase != 0)
            Button("Fail second run", action: controls.failSecondRun).disabled(controls.phase != 1)
            Button("Check retry", action: controls.checkRetry).disabled(controls.phase != 2)
            Button("Finish recovery check", action: controls.complete).disabled(controls.phase != 3)
        }.padding(10)
    }
}

private struct RecoveryFixtureBackend: BackendRunning {
    static let model = "owned-fixture-model"
    let runs = ControlledRunBackend()
    func run(arguments: [String], environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void) throws -> Process {
        try runs.run(arguments: arguments, environment: environment, onEvent: onEvent, onFinish: onFinish)
    }
    func collect(arguments: [String]) async throws -> [BackendEvent] {
        [.ollamaStatus(installed: true, running: true, command: nil, message: "Owned fake provider"),
         .models([Self.model], message: "Owned fake model")]
    }
    func cancel(_ process: Process) { runs.cancel(process) }
}

private final class RecoveryFixtureSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
