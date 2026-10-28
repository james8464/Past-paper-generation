import Foundation
import XCTest
@testable import Keldin

final class HistoryDeletionTests: XCTestCase {
    private var directory: URL!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinHistoryDeletion-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        if let directory { try FileManager.default.removeItem(at: directory) }
    }

    @MainActor
    func testRemovalFailureKeepsRecordOnDiskAndInMemory() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, recordRemover: { _ in
            throw CocoaError(.fileWriteNoPermission)
        })
        let record = job(1)
        try store.save(record)
        let original = try Data(contentsOf: recordURL(record))

        XCTAssertThrowsError(try store.remove(record))

        XCTAssertEqual(store.records.map(\.id), [record.id])
        XCTAssertEqual(try Data(contentsOf: recordURL(record)), original)
        let restarted = RecentDocumentStore(directory: directory, retentionLimit: 10)
        try restarted.load()
        XCTAssertEqual(restarted.records.map(\.id), [record.id])
    }

    @MainActor
    func testRemovalOfAlreadyAbsentRecordIsIdempotent() throws {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)
        let record = job(1)
        try store.save(record)
        try FileManager.default.removeItem(at: recordURL(record))

        XCTAssertNoThrow(try store.remove(record))
        XCTAssertTrue(store.records.isEmpty)
    }

    @MainActor
    func testRemovingHistoryNeverRemovesGeneratedArtifacts() throws {
        let artifact = directory.appendingPathComponent("paper.pdf")
        let bytes = Data("preserved generated document".utf8)
        try bytes.write(to: artifact)
        let record = job(1, artifacts: [GeneratedFile(role: "question_paper", url: artifact)])
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)
        try store.save(record)

        try store.remove(record)

        XCTAssertTrue(store.records.isEmpty)
        XCTAssertFalse(FileManager.default.fileExists(atPath: recordURL(record).path))
        XCTAssertEqual(try Data(contentsOf: artifact), bytes)
    }

    @MainActor
    func testPartialRetentionFailureStaysVisibleAndRestartRetriesIt() throws {
        let first = job(1)
        let second = job(2)
        let third = job(3)
        var deletionFails = true
        let remover: (URL) throws -> Void = { url in
            if deletionFails, url.lastPathComponent == "\(first.id.uuidString).json" {
                throw CocoaError(.fileWriteNoPermission)
            }
            try FileManager.default.removeItem(at: url)
        }
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, recordRemover: remover)
        for record in [first, second, third] { try store.save(record) }

        store.updateRetentionLimit(1)

        XCTAssertEqual(store.records.map(\.id), [third.id, first.id])
        XCTAssertEqual(store.retentionFailureIDs, [first.id])
        XCTAssertTrue(FileManager.default.fileExists(atPath: recordURL(first).path))
        XCTAssertFalse(FileManager.default.fileExists(atPath: recordURL(second).path))
        let restarted = RecentDocumentStore(directory: directory, retentionLimit: 1, recordRemover: remover)
        XCTAssertNoThrow(try restarted.load())
        XCTAssertEqual(restarted.records.map(\.id), [third.id, first.id])
        XCTAssertEqual(restarted.retentionFailureIDs, [first.id])

        deletionFails = false
        restarted.updateRetentionLimit(1)
        XCTAssertEqual(restarted.records.map(\.id), [third.id])
        XCTAssertTrue(restarted.retentionFailureIDs.isEmpty)
        let final = RecentDocumentStore(directory: directory, retentionLimit: 1)
        try final.load()
        XCTAssertEqual(final.records.map(\.id), [third.id])
    }

    @MainActor
    func testCommittedGenerationBeginIsNotFailedByRetentionMaintenance() throws {
        let older = job(1)
        let history = RecentDocumentStore(directory: directory, retentionLimit: 1, recordRemover: { _ in
            throw CocoaError(.fileWriteNoPermission)
        })
        try history.save(older)
        let coordinator = GenerationCoordinator(history: history)
        let pending = job(2)

        XCTAssertNoThrow(try coordinator.begin(pending))

        XCTAssertEqual(coordinator.activeJob?.id, pending.id)
        XCTAssertEqual(coordinator.activeJob?.state, .running)
        XCTAssertEqual(history.records.map(\.id), [pending.id, older.id])
        XCTAssertEqual(history.retentionFailureIDs, [older.id])
        let decoded = try JSONDecoder.history.decode(GenerationJobRecord.self, from: Data(contentsOf: recordURL(pending)))
        XCTAssertEqual(decoded.state, .running)
    }

    @MainActor
    func testHistoryRemovalFailureIsPresentedByApplication() throws {
        let defaults = UserDefaults(suiteName: "HistoryDeletionTests-\(UUID().uuidString)")!
        let application = ApplicationCoordinator(defaults: defaults, secrets: DeletionTestSecrets(), historyDirectory: directory, historyRecordRemover: { _ in
            throw CocoaError(.fileWriteNoPermission)
        })
        let record = job(1)
        try application.recentDocumentStore.save(record)

        application.removeHistory(record)

        XCTAssertTrue(application.showError)
        XCTAssertFalse(application.errorMessage.isEmpty)
        XCTAssertEqual(application.recentDocumentStore.records.map(\.id), [record.id])
    }

    @MainActor
    func testChangingPreferenceAppliesRetentionImmediately() throws {
        let defaults = UserDefaults(suiteName: "HistoryDeletionTests-\(UUID().uuidString)")!
        let application = ApplicationCoordinator(defaults: defaults, secrets: DeletionTestSecrets(), historyDirectory: directory)
        let first = job(1)
        let second = job(2)
        try application.recentDocumentStore.save(first)
        try application.recentDocumentStore.save(second)

        application.setHistoryRetentionLimit(1)

        XCTAssertEqual(application.settingsStore.historyRetentionLimit, 1)
        XCTAssertEqual(application.recentDocumentStore.records.map(\.id), [second.id])
        XCTAssertFalse(FileManager.default.fileExists(atPath: recordURL(first).path))
    }

    @MainActor
    func testRetentionUpdatesClampWithoutRecursiveObservation() {
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)
        store.updateRetentionLimit(10)
        XCTAssertEqual(store.retentionLimit, 10)
        store.updateRetentionLimit(0)
        XCTAssertEqual(store.retentionLimit, 1)
        store.updateRetentionLimit(-5)
        XCTAssertEqual(store.retentionLimit, 1)
        store.updateRetentionLimit(20)
        XCTAssertEqual(store.retentionLimit, 20)
    }

    @MainActor
    func testStartupHistoryAccessFailureIsShownWithoutLegacyFallback() throws {
        let blocked = directory.appendingPathComponent("not-a-directory")
        let original = Data("leave this file alone".utf8)
        try original.write(to: blocked)
        let defaults = UserDefaults(suiteName: "HistoryDeletionTests-\(UUID().uuidString)")!
        let stale = GeneratedFile(role: "question_paper", url: directory.appendingPathComponent("legacy.pdf"))
        defaults.set(try JSONEncoder().encode([stale]), forKey: AppStorageKey.recentDocuments)

        let application = ApplicationCoordinator(defaults: defaults, secrets: DeletionTestSecrets(), historyDirectory: blocked)

        XCTAssertTrue(application.showError)
        XCTAssertTrue(application.errorMessage.contains("history"))
        XCTAssertTrue(application.generatedFiles.isEmpty)
        XCTAssertEqual(try Data(contentsOf: blocked), original)
    }

    private func job(_ timestamp: TimeInterval, artifacts: [GeneratedFile] = []) -> GenerationJobRecord {
        GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 1, dryRun: false),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: artifacts,
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false),
            createdAt: Date(timeIntervalSince1970: timestamp), updatedAt: Date(timeIntervalSince1970: timestamp)
        )
    }

    private func recordURL(_ record: GenerationJobRecord) -> URL {
        directory.appendingPathComponent("\(record.id.uuidString).json")
    }
}

private extension JSONDecoder {
    static var history: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}

private final class DeletionTestSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
