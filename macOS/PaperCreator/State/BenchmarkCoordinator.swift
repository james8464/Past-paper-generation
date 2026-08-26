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
    var outputFolder = AppDefaults.defaultOutputFolder()

    @ObservationIgnored private let backend: BackendClient
    @ObservationIgnored private var process: Process?

    init(backend: BackendClient = BackendClient()) {
        self.backend = backend
    }

    func start(generationIsRunning: Bool) {
        guard !generationIsRunning, !isRunning else { return }
        begin()
        do {
            process = try backend.run(arguments: [
                "benchmark",
                "--duration",
                String(Int(AppDefaults.benchmarkDurationSeconds)),
                "--output",
                outputFolder.path,
            ]) { [weak self] event in
                self?.receive(event)
            } onFinish: { [weak self] result in
                self?.finish(result)
            }
        } catch {
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
            verdict = result
            progress = 1
            isRunning = false
        case let .error(message, _):
            errorMessage = message
        default:
            break
        }
    }

    func cancel() {
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
            errorMessage = "Benchmark exited with code \(code)."
        case let .failure(error):
            errorMessage = error.localizedDescription
        default:
            break
        }
    }
}
