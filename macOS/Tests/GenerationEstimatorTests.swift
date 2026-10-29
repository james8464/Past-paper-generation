import Foundation
import XCTest
@testable import Keldin

final class GenerationEstimatorTests: XCTestCase {
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
        func record(_ seconds: Double, model: String = "fixture", state: GenerationJobState = .completed, preview: Bool = false) -> GenerationJobRecord {
            let start = Date(timeIntervalSince1970: 1_000)
            return GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: board.id, paperID: paper.id,
                    provider: "ollama", model: model, seed: 1, dryRun: preview),
                provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: model),
                state: state, artifacts: [],
                qualification: QualificationSnapshot(engineeringValidated: true, visuallyCalibrated: false, empiricallyCalibrated: false),
                createdAt: start, updatedAt: start.addingTimeInterval(seconds))
        }
        let estimate = GenerationEstimator.initialEstimate(board: board, paper: paper,
            provider: .ollama, model: "fixture", dryRun: false, benchmark: nil,
            recentRuns: [record(600), record(660), record(720), record(100, model: "other"),
                         record(100, state: .failed), record(100, preview: true), record(-10), record(90_000)])
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
