// Track benchmark events and retain the resulting performance measurements.

import Foundation
import Observation

@MainActor
@Observable
final class BenchmarkCoordinator {
    private(set) var isRunning = false
    private(set) var progress: Double?
    private(set) var samples: [BenchmarkSample] = []
    private(set) var metrics: [BenchmarkMetric] = []
    private(set) var verdict: BenchmarkVerdict?
    private(set) var errorMessage: String?
    var outputFolder = AppDefaults.jobHistoryFolder().appendingPathComponent("Benchmarks", isDirectory: true)

    @ObservationIgnored private let backend: any BackendRunning
    @ObservationIgnored private var process: Process?
    @ObservationIgnored private var activeRunSession: RunSession?

    init(backend: any BackendRunning = BackendClient()) {
        self.backend = backend
    }

    func start(generationIsRunning: Bool) {
        guard !generationIsRunning, !isRunning else { return }
        begin()
        let session = RunSession()
        activeRunSession = session
        do {
            process = try backend.run(arguments: [
                "benchmark",
                "--duration",
                String(Int(AppDefaults.benchmarkDurationSeconds)),
                "--output",
                outputFolder.path,
            ], environment: [:]) { [weak self] event in
                guard let self, self.activeRunSession == session else { return }
                self.receive(event)
            } onFinish: { [weak self] result in
                guard let self, self.activeRunSession == session else { return }
                self.activeRunSession = nil
                self.finish(result)
            }
        } catch {
            activeRunSession = nil
            finish(.failure(error))
        }
    }

    func begin() {
        isRunning = true
        progress = 0
        samples.removeAll()
        metrics.removeAll()
        verdict = nil
        errorMessage = nil
    }

    func receive(_ event: BackendEvent) {
        switch event {
        case let .benchmarkMetric(metric):
            metrics.append(metric)
        case let .benchmarkSample(sample):
            samples.append(sample)
            progress = min(1, sample.elapsed / AppDefaults.benchmarkDurationSeconds)
        case let .benchmarkDone(result):
            guard result.validatedScore != nil else {
                verdict = nil
                progress = nil
                errorMessage = BenchmarkVerdict.invalidScoreMessage
                return
            }
            verdict = result
            progress = 1
        case let .error(message, _):
            errorMessage = message
        default:
            break
        }
    }

    func cancel() {
        activeRunSession = nil
        process?.terminate()
        process = nil
        isRunning = false
        progress = nil
    }

    private func finish(_ result: Result<Int32, Error>) {
        process = nil
        isRunning = false
        progress = verdict == nil ? nil : 1
        switch result {
        case let .success(code) where code != 0:
            if errorMessage == nil { errorMessage = "Benchmark exited with code \(code)." }
        case let .failure(error):
            errorMessage = error.localizedDescription
        default:
            break
        }
    }

    private struct RunSession: Equatable, Sendable {
        let id = UUID()
    }
}
