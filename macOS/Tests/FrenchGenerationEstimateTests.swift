import Foundation
import XCTest
@testable import Keldin

final class FrenchGenerationEstimateTests: XCTestCase {
    private let start = Date(timeIntervalSince1970: 10_000)

    private func configuration(provider: String = "ollama", model: String = "fixture", version: String = "v36") -> GenerationConfiguration {
        GenerationConfiguration(boardID: "fr-national-nsi", paperID: "written-2027",
            provider: provider, model: model, seed: 42, dryRun: false,
            educationSystem: "fr-national", assessmentID: FrenchAssessmentRequest.assessmentID,
            documentLanguage: "fr-FR", authoringVersion: version)
    }

    private func record(_ seconds: Double, configuration: GenerationConfiguration? = nil,
                        state: GenerationJobState = .completed, workers: Int? = 1) -> GenerationJobRecord {
        let config = configuration ?? self.configuration()
        let created = start.addingTimeInterval(-2_000)
        return GenerationJobRecord(configuration: config,
            provenance: GenerationProvenance(appVersion: "fixture", provider: config.provider, model: config.model,
                localGenerationWorkers: workers), state: state, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false),
            createdAt: created, updatedAt: created.addingTimeInterval(seconds))
    }

    func testNoFrenchHistoryShowsElapsedButDoesNotInventAnETAFromUKOrPhaseProgress() {
        let estimate = GenerationEstimator.initialFrenchEstimate(configuration: configuration(), recentRuns: [], now: start)
        XCTAssertFalse(estimate.hasDurationEstimate)
        XCTAssertEqual(estimate.elapsedSeconds, 0)
        XCTAssertEqual(estimate.remainingSeconds, 0)
        let later = GenerationEstimator.update(estimate: estimate, progress: 0.8, now: start.addingTimeInterval(120))
        XCTAssertFalse(later.hasDurationEstimate)
        XCTAssertEqual(later.elapsedSeconds, 120)
        XCTAssertEqual(later.remainingSeconds, 0)
        XCTAssertEqual(GenerationPresentation.estimatedTime(later, locale: Locale(identifier: "en")), "Time remaining is not yet known.")
        XCTAssertEqual(GenerationPresentation.estimatedTime(later, locale: Locale(identifier: "fr")), "Le temps restant n’est pas encore connu.")
        XCTAssertEqual(GenerationPresentation.elapsedTime(120, locale: Locale(identifier: "en")), "Elapsed: 2m")
        XCTAssertEqual(GenerationPresentation.elapsedTime(120, locale: Locale(identifier: "fr")), "Temps écoulé : 2m")
    }

    func testOnlyMatchingCompletedSerialFrenchV36HistoryProvidesTheMedian() {
        var wrongAssessment = configuration()
        wrongAssessment.assessmentID = "uk"
        var wrongLanguage = configuration()
        wrongLanguage.documentLanguage = "en-GB"
        let estimate = GenerationEstimator.initialFrenchEstimate(configuration: configuration(), recentRuns: [
            record(600), record(660), record(720, workers: nil),
            record(40, configuration: configuration(provider: "apple")),
            record(40, configuration: configuration(model: "other")),
            record(40, configuration: configuration(version: "v35")),
            record(40, configuration: wrongAssessment), record(40, configuration: wrongLanguage),
            record(40, state: .failed), record(40, state: .cancelled), record(40, workers: 2),
            record(-10), record(90_000),
        ], now: start)
        XCTAssertTrue(estimate.hasDurationEstimate)
        XCTAssertEqual(estimate.totalSeconds, 660)
        XCTAssertEqual(estimate.remainingSeconds, 660)
        XCTAssertEqual(estimate.elapsedSeconds, 0)
    }

    func testKnownFrenchETAUsesExistingSmoothingAndMonotonicProgress() {
        let estimate = GenerationEstimator.initialFrenchEstimate(configuration: configuration(),
            recentRuns: [record(600)], now: start)
        let first = GenerationEstimator.update(estimate: estimate, progress: 0.5, now: start.addingTimeInterval(100))
        let second = GenerationEstimator.update(estimate: first, progress: 0.2, now: start.addingTimeInterval(101))
        XCTAssertTrue(second.hasDurationEstimate)
        XCTAssertEqual(second.elapsedSeconds, 101)
        XCTAssertEqual(second.lastObservedProgress, 0.5)
        XCTAssertLessThanOrEqual(abs(second.remainingSeconds - first.remainingSeconds), 3.01)
        XCTAssertEqual(GenerationEstimator.update(estimate: second, progress: 0.9, now: start), second)
    }

    @MainActor
    func testFrenchRunStartsItsOwnClockAndRecordsActualSerialWorkDespiteUKPreference() throws {
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let backend = ControlledRunBackend()
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.settingsStore.parallelLocalReviews = true
        app.generateFrenchFixture(largePrint: false)
        let estimate = try XCTUnwrap(app.generationEstimate)
        XCTAssertFalse(estimate.hasDurationEstimate)
        XCTAssertEqual(app.generationCoordinator.activeJob?.configuration.authoringVersion, "v36")
        XCTAssertEqual(app.generationCoordinator.activeJob?.provenance.localGenerationWorkers, 1)
        app.showDocuments()
        let request = try XCTUnwrap(backend.requests.last)
        request.onEvent(.progress(stage: "french_generation", message: "Drafting", progress: 0.4))
        XCTAssertEqual(app.generationEstimate?.startedAt, estimate.startedAt)
        XCTAssertNotNil(app.generationEstimate?.elapsedSeconds)
        app.cancelGeneration()
        XCTAssertNil(app.generationEstimate)
        request.onEvent(.progress(stage: "french_generation", message: "Late event", progress: 0.8))
        XCTAssertNil(app.generationEstimate)
    }
}
