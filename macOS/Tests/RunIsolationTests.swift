import Combine
import Foundation
import XCTest
@testable import Keldin

final class RunIsolationTests: XCTestCase {
    @MainActor
    func testCancelledGenerationCannotChangeItsReplacement() throws {
        for french in [false, true] {
            let backend = ControlledRunBackend()
            let application = application(backend: backend)
            if french {
                application.generateFrenchPaper(largePrint: false)
            } else {
                let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
                application.selectBoard(board)
                application.setDryRun(true)
                application.generate()
            }
            let cancelled = try XCTUnwrap(backend.requests.first)
            application.cancelGeneration()
            application.generateFrenchPaper(largePrint: true)
            XCTAssertEqual(backend.requests.count, 2)
            let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
            let replacementStatus = application.status

            cancelled.onEvent(.progress(stage: "late", message: "Cancelled progress", progress: 0.9))
            cancelled.onEvent(.file(role: "question_paper", path: "/cancelled/sujet.pdf"))
            cancelled.onEvent(.done(message: "Cancelled completion"))
            cancelled.onEvent(.error(message: "Cancelled error", code: "generation_failed"))
            cancelled.onFinish(.success(1))

            XCTAssertTrue(application.isRunning)
            XCTAssertEqual(application.status, replacementStatus)
            XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
            XCTAssertTrue(application.currentGenerationFiles.isEmpty)
            XCTAssertFalse(application.showError)
            XCTAssertTrue(application.progressEntries.isEmpty)
            backend.requests[1].onEvent(.progress(stage: "current", message: "Current progress", progress: 0.2))
            XCTAssertEqual(application.generationProgress, 0.2)
            application.cancelGeneration()
        }
    }

    @MainActor
    func testCancelledGenerationIgnoresBufferedEventsBeforeAnotherRun() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.generateFrenchPaper(largePrint: false)
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        let status = application.status
        let entries = application.progressEntries

        cancelled.onEvent(.progress(stage: "late", message: "Late progress", progress: 0.8))
        cancelled.onEvent(.file(role: "question_paper", path: "/cancelled/sujet.pdf"))
        cancelled.onEvent(.done(message: "Late completion"))
        cancelled.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
        XCTAssertFalse(application.showError)
    }

    @MainActor
    func testFinishedGenerationIgnoresRepeatedCallbacks() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.generateFrenchPaper(largePrint: false)
        let finished = try XCTUnwrap(backend.requests.first)
        finished.onFinish(.success(1))
        let status = application.status
        let entries = application.progressEntries

        finished.onEvent(.file(role: "question_paper", path: "/finished/sujet.pdf"))
        finished.onEvent(.progress(stage: "late", message: "Late progress", progress: 0.8))
        finished.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
    }

    @MainActor
    func testCancelledModelPullCannotSelectModelOrFinishReplacement() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let originalModel = application.selectedModel
        application.modelToPull = "cancelled-model"
        application.confirmPullModel()
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        application.generateFrenchPaper(largePrint: false)
        let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)

        cancelled.onFinish(.success(0))

        XCTAssertEqual(application.selectedModel, originalModel)
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testMLXCancellationWaitsForItsOwnExitWithoutRestartingGeneration() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        let application = application(backend: backend, defaults: defaults)
        application.confirmMLXSetup()
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        XCTAssertTrue(application.isRunning)
        cancelled.onEvent(.error(message: "Cancelled setup", code: "mlx_setup_failed"))
        cancelled.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertFalse(application.showError)
        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertNil(defaults.object(forKey: AppStorageKey.preparedMLXModels))
        application.generateFrenchPaper(largePrint: false)
        let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
        cancelled.onFinish(.success(0))
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testSuccessfulMLXSetupHandsOwnershipToTheGenerationRun() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI && $0.supports(.apple) })
        application.selectBoard(board)
        application.aiProvider = .apple
        application.confirmMLXSetup()
        let setup = try XCTUnwrap(backend.requests.first)
        setup.onFinish(.success(0))

        XCTAssertEqual(backend.requests.count, 2)
        XCTAssertTrue(application.isRunning)
        let generationID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
        setup.onEvent(.error(message: "Late setup error", code: "mlx_setup_failed"))
        setup.onFinish(.success(0))
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, generationID)
        XCTAssertTrue(application.isRunning)
        XCTAssertFalse(application.showError)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testCancelledBenchmarkCannotChangeItsReplacement() throws {
        let backend = ControlledRunBackend()
        let benchmark = BenchmarkCoordinator(backend: backend)
        benchmark.start(generationIsRunning: false)
        let cancelled = try XCTUnwrap(backend.requests.first)
        benchmark.cancel()
        benchmark.start(generationIsRunning: false)
        XCTAssertEqual(backend.requests.count, 2)

        cancelled.onEvent(.error(message: "Cancelled failure", code: "benchmark_failed"))
        cancelled.onEvent(.benchmarkDone(BenchmarkVerdict(score: 99, verdict: "Old", detail: "Old result")))
        cancelled.onFinish(.success(1))

        XCTAssertTrue(benchmark.isRunning)
        XCTAssertNil(benchmark.errorMessage)
        XCTAssertNil(benchmark.verdict)
        XCTAssertEqual(benchmark.progress, 0)
        backend.requests[1].onEvent(.benchmarkDone(BenchmarkVerdict(score: 2, verdict: "Current", detail: "Current result")))
        backend.requests[1].onFinish(.success(0))
        XCTAssertFalse(benchmark.isRunning)
        XCTAssertEqual(benchmark.verdict?.score, 2)
        XCTAssertNil(benchmark.errorMessage)
    }

    @MainActor
    func testLateOllamaStatusCannotPoisonModelFreeFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let status = application.status
        let jobID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)

        backend.resumeNext(.success([.error(message: "Stale Ollama status", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, jobID)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
        application.cancelGeneration()
    }

    @MainActor
    func testLateOllamaModelsCannotPoisonFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend(defersModels: true)
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        backend.resumeNext(.success([]))
        await fulfillment(of: [backend.modelsStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: true)
        let status = application.status

        backend.resumeNext(.success([.error(message: "Stale Ollama models", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        application.cancelGeneration()
    }

    @MainActor
    func testLateOllamaCollectionFailureCannotPoisonFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let status = application.status

        backend.resumeNext(.failure(CocoaError(.fileReadUnknown)))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        application.cancelGeneration()
    }

    @MainActor
    func testRefreshStaysObsoleteAfterTheNewRunFinishes() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let generation = try XCTUnwrap(backend.runs.requests.first)
        generation.onFinish(.success(1))
        XCTAssertFalse(application.isRunning)
        let error = application.errorMessage
        let entries = application.progressEntries

        backend.resumeNext(.success([.error(message: "Stale refresh after completion", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertEqual(application.errorMessage, error)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
    }

    @MainActor
    func testLateOllamaRefreshCannotChangeAnActiveBenchmark() async {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.startBenchmark()
        let status = application.status

        backend.resumeNext(.success([.error(message: "Stale refresh during benchmark", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.benchmarkCoordinator.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertNil(application.benchmarkCoordinator.errorMessage)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
        application.cancelBenchmark()
    }

    @MainActor
    private func waitForRefreshCompletion(_ application: ApplicationCoordinator) async {
        let finished = expectation(description: "Ollama refresh finished")
        let subscription = application.$isRefreshingOllama
            .filter { !$0 }
            .prefix(1)
            .sink { _ in finished.fulfill() }
        await fulfillment(of: [finished], timeout: 2)
        subscription.cancel()
    }

    @MainActor
    private func application(backend: any BackendRunning, defaults: UserDefaults? = nil) -> ApplicationCoordinator {
        let defaults = defaults ?? isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        let history = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinRunIsolation-\(UUID().uuidString)")
        addTeardownBlock { try? FileManager.default.removeItem(at: history) }
        return ApplicationCoordinator(
            defaults: defaults, secrets: RunIsolationSecrets(), historyDirectory: history, backend: backend
        )
    }
}

// Each instance is driven synchronously by one main-actor test. Captured callbacks
// retain the production main-actor contract without launching a helper or model.
private final class ControlledRunBackend: BackendRunning, @unchecked Sendable {
    struct Request {
        let onEvent: @Sendable @MainActor (BackendEvent) -> Void
        let onFinish: @Sendable @MainActor (Result<Int32, Error>) -> Void
    }

    private(set) var requests: [Request] = []

    func run(
        arguments: [String], environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        requests.append(Request(onEvent: onEvent, onFinish: onFinish))
        return ControlledProcess()
    }

    func collect(arguments: [String]) async throws -> [BackendEvent] { [] }
}

private final class ControlledProcess: Process, @unchecked Sendable {
    override func terminate() {}
}

// Continuations may be installed on a background executor. Protect their queue
// while tests drive the public refresh and generation actions on the main actor.
private final class DeferredRefreshBackend: BackendRunning, @unchecked Sendable {
    let runs = ControlledRunBackend()
    let statusStarted = XCTestExpectation(description: "Ollama status collection started")
    let modelsStarted = XCTestExpectation(description: "Ollama models collection started")
    private let lock = NSLock()
    private let defersModels: Bool
    private var arguments: [[String]] = []
    private var continuations: [CheckedContinuation<[BackendEvent], Error>] = []

    init(defersModels: Bool = false) {
        self.defersModels = defersModels
    }

    var collectionArguments: [[String]] { lock.withLock { arguments } }

    func run(
        arguments: [String], environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        try runs.run(arguments: arguments, environment: environment, onEvent: onEvent, onFinish: onFinish)
    }

    func collect(arguments: [String]) async throws -> [BackendEvent] {
        lock.withLock { self.arguments.append(arguments) }
        let isStatus = arguments.first == "ollama-status"
        guard isStatus || defersModels else { return [] }
        return try await withCheckedThrowingContinuation { continuation in
            lock.withLock { continuations.append(continuation) }
            (isStatus ? statusStarted : modelsStarted).fulfill()
        }
    }

    func resumeNext(_ result: Result<[BackendEvent], Error>) {
        let continuation = lock.withLock { continuations.removeFirst() }
        continuation.resume(with: result)
    }
}

private struct RunIsolationSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
