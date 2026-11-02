import Foundation
import XCTest
@testable import Keldin

final class GenerationEstimatorTests: XCTestCase {
    func testPreviewLearnsCompletedTimingAcrossProviderModelAndWorkerSelections() throws {
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(board.papers.first)
        let record = timingRecord(board: board.id, paper: paper.id, seconds: 3,
            provider: "openai", model: "previous-model", workers: 1)
        let estimate = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .anthropic, model: "different-model", dryRun: true, benchmark: nil,
            recentRuns: [record], localGenerationWorkers: 2)
        XCTAssertEqual(estimate.totalSeconds, 3)
        XCTAssertEqual(estimate.remainingSeconds, 3)
        XCTAssertTrue(estimate.factors.contains { $0.title == "Runtime history" })
    }

    func testObservedPreviewMedianIsNotClampedToLiveMinimum() throws {
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(board.papers.first)
        let records = [2.0, 3.0, 4.0].map {
            timingRecord(board: board.id, paper: paper.id, seconds: $0)
        }
        let estimate = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: true, benchmark: nil, recentRuns: records)
        XCTAssertEqual(estimate.totalSeconds, 3)
        XCTAssertEqual(estimate.remainingSeconds, 3)
        let live = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: false, benchmark: nil,
            recentRuns: [timingRecord(board: board.id, paper: paper.id, seconds: 3, preview: false)])
        XCTAssertEqual(live.totalSeconds, 20)
        XCTAssertEqual(live.remainingSeconds, 20)
    }

    func testIneligiblePreviewHistoryPreservesColdStartHeuristic() throws {
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(board.papers.first)
        var records = [GenerationJobState.failed, .cancelled, .interrupted, .pending, .running, .missingArtifacts].map {
            timingRecord(board: board.id, paper: paper.id, seconds: 3, state: $0)
        }
        records += [0, -1, 0.5, 90_000, Double.infinity, Double.nan].map {
            timingRecord(board: board.id, paper: paper.id, seconds: $0)
        }
        records += [
            timingRecord(board: "different-board", paper: paper.id, seconds: 3),
            timingRecord(board: board.id, paper: "different-paper", seconds: 3),
            timingRecord(board: board.id, paper: paper.id, seconds: 3, preview: false),
        ]
        let cold = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: true, benchmark: nil)
        let estimate = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: true, benchmark: nil, recentRuns: records)
        XCTAssertEqual(estimate.totalSeconds, cold.totalSeconds)
        XCTAssertEqual(estimate.remainingSeconds, cold.remainingSeconds)
        XCTAssertGreaterThanOrEqual(cold.totalSeconds, 20)
        XCTAssertFalse(estimate.factors.contains { $0.title == "Runtime history" })
    }

    private func timingRecord(board: String, paper: String, seconds: Double,
        provider: String = "ollama", model: String = "fixture", workers: Int = 1,
        preview: Bool = true, state: GenerationJobState = .completed) -> GenerationJobRecord {
        let start = Date(timeIntervalSince1970: 1_000)
        return GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: board, paperID: paper,
                provider: provider, model: model, seed: 1, dryRun: preview),
            provenance: GenerationProvenance(appVersion: "test", provider: provider, model: model,
                localGenerationWorkers: workers), state: state, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false),
            createdAt: start, updatedAt: start.addingTimeInterval(seconds))
    }

    func testRuntimeHistorySeparatesSerialAndParallelModesWithLegacyFallback() throws {
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(board.papers.first)
        func record(_ seconds: Double, current: Int? = nil, legacy: Int? = nil) -> GenerationJobRecord {
            let start = Date(timeIntervalSince1970: 1_000)
            return GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: board.id, paperID: paper.id,
                    provider: "ollama", model: "fixture", seed: 1, dryRun: false),
                provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture",
                    localReviewWorkers: legacy, localGenerationWorkers: current),
                state: .completed, artifacts: [],
                qualification: QualificationSnapshot(engineeringValidated: true, visuallyCalibrated: false, empiricallyCalibrated: false),
                createdAt: start, updatedAt: start.addingTimeInterval(seconds))
        }
        let records = [record(600), record(660, current: 1), record(300, current: 2),
                       record(360, legacy: 2), record(340, current: 2, legacy: 1)]
        let serial = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: false, benchmark: nil,
            recentRuns: records, localGenerationWorkers: 1)
        let parallel = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: false, benchmark: nil,
            recentRuns: records, localGenerationWorkers: 2)
        XCTAssertEqual(serial.totalSeconds, 630)
        XCTAssertEqual(parallel.totalSeconds, 340)
        let oldJSON = #"{"appVersion":"test","provider":"ollama","model":"fixture"}"#.data(using: .utf8)!
        let old = try JSONDecoder().decode(GenerationProvenance.self, from: oldJSON)
        XCTAssertEqual(old.effectiveLocalGenerationWorkers, 1)
    }

    func testRapidProgressEventsUseActualElapsedTimeForSmoothing() {
        let start = Date(timeIntervalSince1970: 1_000)
        let initial = GenerationEstimate(startedAt: start, totalSeconds: 600,
            remainingSeconds: 600, confidence: 0.5, factors: [])
        let first = GenerationEstimator.update(estimate: initial, progress: 0.1,
            now: start.addingTimeInterval(100))
        let next = GenerationEstimator.update(estimate: first, progress: 0.9,
            now: start.addingTimeInterval(100.05))
        XCTAssertLessThanOrEqual(abs(next.remainingSeconds - first.remainingSeconds), 0.151)
    }

    func testSlowReviewDoesNotKeepPromisingOneSecondRemaining() {
        let estimate = GenerationEstimate(startedAt: Date(), totalSeconds: 60,
            remainingSeconds: 0.5, confidence: 0.5, factors: [],
            lastUpdatedAt: Date(), lastObservedProgress: 0.8)
        XCTAssertEqual(GenerationPresentation.estimatedTime(estimate, locale: Locale(identifier: "en")), "Updating time estimate…")
        XCTAssertEqual(GenerationPresentation.estimatedTime(estimate, locale: Locale(identifier: "fr")), "Actualisation de l’estimation…")
    }

    func testMatchingCompletedRunsProvideARobustInitialDuration() throws {
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(board.papers.first)
        func record(_ seconds: Double, model: String = "fixture", provider: String = "ollama", state: GenerationJobState = .completed, preview: Bool = false) -> GenerationJobRecord {
            let start = Date(timeIntervalSince1970: 1_000)
            return GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: board.id, paperID: paper.id,
                    provider: provider, model: model, seed: 1, dryRun: preview),
                provenance: GenerationProvenance(appVersion: "test", provider: provider, model: model),
                state: state, artifacts: [],
                qualification: QualificationSnapshot(engineeringValidated: true, visuallyCalibrated: false, empiricallyCalibrated: false),
                createdAt: start, updatedAt: start.addingTimeInterval(seconds))
        }
        let estimate = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: false, benchmark: nil,
            recentRuns: [record(600), record(660), record(720), record(100, model: "other"),
                         record(100, state: .failed), record(100, preview: true), record(1, provider: "openai"), record(-10), record(90_000)])
        XCTAssertEqual(estimate.totalSeconds, 660)
        XCTAssertEqual(estimate.remainingSeconds, 660)
    }

    func testClockReversalAndInvalidProgressDoNotCorruptTheCountdown() {
        let start = Date(timeIntervalSince1970: 1_000)
        let initial = GenerationEstimate(startedAt: start, totalSeconds: 600,
                                         remainingSeconds: 600, confidence: 0.5, factors: [])
        let first = GenerationEstimator.update(estimate: initial, progress: 0.4,
                                               now: start.addingTimeInterval(100))
        XCTAssertEqual(GenerationEstimator.update(estimate: first, progress: 0.5,
            now: start.addingTimeInterval(90)), first)
        for value in [Double.nan, .infinity, -.infinity] {
            let next = GenerationEstimator.update(estimate: first, progress: value,
                now: start.addingTimeInterval(101))
            XCTAssertTrue(next.remainingSeconds.isFinite)
            XCTAssertGreaterThanOrEqual(next.remainingSeconds, 0)
            XCTAssertEqual(next.lastObservedProgress, first.lastObservedProgress)
        }
    }

    func testOneSecondUpdatesDoNotMakeLargeCountdownJumps() {
        let start = Date(timeIntervalSince1970: 1_000)
        let initial = GenerationEstimate(startedAt: start, totalSeconds: 600,
                                         remainingSeconds: 600, confidence: 0.5, factors: [])
        let first = GenerationEstimator.update(estimate: initial, progress: 0.1,
                                               now: start.addingTimeInterval(100))
        let next = GenerationEstimator.update(estimate: first, progress: 0.9,
                                              now: start.addingTimeInterval(101))
        XCTAssertLessThanOrEqual(abs(next.remainingSeconds - first.remainingSeconds), 3.01)
        let duplicate = GenerationEstimator.update(estimate: next, progress: 0.9,
                                                   now: start.addingTimeInterval(101))
        XCTAssertEqual(duplicate, next)
    }
}
