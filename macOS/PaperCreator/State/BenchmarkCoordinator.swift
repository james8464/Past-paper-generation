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

    func begin() {
        isRunning = true
        progress = 0
        samples.removeAll()
        metrics.removeAll()
        verdict = nil
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
        default:
            break
        }
    }

    func cancel() {
        isRunning = false
        progress = nil
    }
}
