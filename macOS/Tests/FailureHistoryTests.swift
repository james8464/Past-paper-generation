import Foundation
import XCTest
@testable import Keldin

final class FailureHistoryTests: XCTestCase {
    private var directory: URL!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory
            .appendingPathComponent("KeldinFailureHistory-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        if let directory { try FileManager.default.removeItem(at: directory) }
    }

    @MainActor
    func testFailureKindSurvivesReloadWithoutSavingRawMessage() throws {
        let defaults = isolatedDefaults()
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: defaults)
        let coordinator = GenerationCoordinator(history: store, clock: FailureHistoryClock())
        let job = record()
        let privateMessage = "sk-owned-secret /Users/owned/private/draft.json PRIVATE_MODEL_DRAFT"
        try coordinator.begin(job)
        try coordinator.fail(message: privateMessage, failureKind: .qualityChecksFailed, expectedJobID: job.id)
        XCTAssertEqual(coordinator.status, privateMessage)

        let bytes = try Data(contentsOf: recordURL(job))
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: bytes) as? [String: Any])
        XCTAssertEqual(json["failureKind"] as? String, "quality-checks-failed")
        let text = try XCTUnwrap(String(data: bytes, encoding: .utf8))
        for secret in [privateMessage, "sk-owned-secret", "/Users/owned/private", "PRIVATE_MODEL_DRAFT"] {
            XCTAssertFalse(text.contains(secret))
        }
        let reopened = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: isolatedDefaults())
        try reopened.load()
        XCTAssertEqual(reopened.records.first?.state, .failed)
        XCTAssertEqual(reopened.records.first?.failureKind, .qualityChecksFailed)
        XCTAssertNotNil(reopened.records.first?.failureDetailResource)
        XCTAssertEqual(try Data(contentsOf: recordURL(job)), bytes)
    }

    @MainActor
    func testEveryOwnedFailureKindRoundTripsWithoutChangingSchema() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 20, defaults: isolatedDefaults())
        for kind in GenerationFailureKind.allCases {
            var job = record(state: .failed)
            job.failureKind = kind
            try store.save(job)
        }
        let reopened = RecentDocumentStore(directory: directory, retentionLimit: 20, defaults: isolatedDefaults())
        try reopened.load()
        XCTAssertEqual(Set(reopened.records.compactMap(\.failureKind)), Set(GenerationFailureKind.allCases))
        XCTAssertTrue(reopened.records.allSatisfy { $0.schemaVersion == 1 && $0.failureDetailResource != nil })
    }

    @MainActor
    func testOldFailedRecordsHaveUnavailableDetailsWithoutInventingAReason() throws {
        for version in [0, 1] {
            let job = record(schemaVersion: version, state: .failed)
            var object = try XCTUnwrap(JSONSerialization.jsonObject(with: encoded(job)) as? [String: Any])
            object.removeValue(forKey: "failureKind")
            try JSONSerialization.data(withJSONObject: object).write(to: recordURL(job))
        }
        let reopened = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: isolatedDefaults())
        try reopened.load()
        XCTAssertEqual(reopened.records.count, 2)
        XCTAssertEqual(reopened.quarantinedRecordCount, 0)
        for record in reopened.records {
            XCTAssertEqual(record.state, .failed)
            XCTAssertNil(record.failureKind)
            var detail = try XCTUnwrap(record.failureDetailResource)
            detail.locale = Locale(identifier: "en")
            XCTAssertEqual(String(localized: detail), "Failure details were not recorded for this run.")
        }
    }

    @MainActor
    func testBeginningAndEndingAReusedJobClearOldFailure() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: isolatedDefaults())
        let coordinator = GenerationCoordinator(history: store, clock: FailureHistoryClock())
        for cancel in [false, true] {
            var job = record(state: .failed)
            job.failureKind = .modelSetupRequired
            try coordinator.begin(job)
            XCTAssertNil(coordinator.activeJob?.failureKind)
            XCTAssertNil(store.records.first { $0.id == job.id }?.failureKind)
            if cancel { try coordinator.cancel(expectedJobID: job.id) }
            else { try coordinator.complete(expectedJobID: job.id) }
            let saved = try XCTUnwrap(store.records.first { $0.id == job.id })
            XCTAssertNil(saved.failureKind)
            XCTAssertNil(saved.failureDetailResource)
            XCTAssertEqual(saved.state, cancel ? .cancelled : .completed)
        }
    }

    @MainActor
    func testStartingAnotherJobDoesNotEraseThePreviousFailureKind() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: isolatedDefaults())
        let coordinator = GenerationCoordinator(history: store, clock: FailureHistoryClock())
        let failed = record()
        try coordinator.begin(failed)
        try coordinator.fail(message: "Transient failure", failureKind: .frenchPaperFailed, expectedJobID: failed.id)
        try coordinator.begin(record())
        XCTAssertEqual(store.records.first { $0.id == failed.id }?.failureKind, .frenchPaperFailed)
    }

    @MainActor
    func testWrongJobCannotReplaceAnotherFailureKind() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: isolatedDefaults())
        let coordinator = GenerationCoordinator(history: store, clock: FailureHistoryClock())
        let job = record()
        try coordinator.begin(job)
        XCTAssertThrowsError(try coordinator.fail(message: "Private", failureKind: .publicationFailed, expectedJobID: UUID()))
        XCTAssertEqual(coordinator.activeJob?.id, job.id)
        XCTAssertNil(coordinator.activeJob?.failureKind)
        XCTAssertEqual(store.records.first?.state, .running)
    }

    private func record(schemaVersion: Int = GenerationJobRecord.currentSchemaVersion,
                        state: GenerationJobState = .pending) -> GenerationJobRecord {
        GenerationJobRecord(
            schemaVersion: schemaVersion,
            configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1",
                provider: "ollama", model: "owned-model", seed: 1, dryRun: false),
            provenance: GenerationProvenance(appVersion: "owned-test", provider: "ollama", model: "owned-model"),
            state: state, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false,
                visuallyCalibrated: false, empiricallyCalibrated: false),
            createdAt: FailureHistoryClock().now, updatedAt: FailureHistoryClock().now
        )
    }

    private func recordURL(_ job: GenerationJobRecord) -> URL {
        directory.appendingPathComponent("\(job.id.uuidString).json")
    }

    private func encoded(_ job: GenerationJobRecord) throws -> Data {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return try encoder.encode(job)
    }
}

private struct FailureHistoryClock: AppClock {
    let now = Date(timeIntervalSince1970: 100)
}
