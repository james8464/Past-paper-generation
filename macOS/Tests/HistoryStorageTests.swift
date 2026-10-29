import Foundation
import XCTest
@testable import Keldin

final class HistoryStorageTests: XCTestCase {
    private var directory: URL!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinHistoryStorage-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        if let directory { try FileManager.default.removeItem(at: directory) }
    }

    @MainActor
    func testNoncanonicalValidRecordFailsClosedWithoutBeingQuarantinedOrRewritten() throws {
        let valid = record()
        let bytes = try encoded(valid)
        let unexpected = directory.appendingPathComponent("renamed.json")
        try bytes.write(to: unexpected)
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)

        XCTAssertThrowsError(try store.load()) { error in
            XCTAssertEqual(error as? RecentDocumentStoreError, .noncanonicalFileName)
        }

        XCTAssertEqual(try Data(contentsOf: unexpected), bytes)
        XCTAssertFalse(FileManager.default.fileExists(atPath: recordURL(valid).path))
        XCTAssertTrue(store.records.isEmpty)
        XCTAssertEqual(store.quarantinedRecordCount, 0)
        XCTAssertFalse(FileManager.default.fileExists(atPath: directory.appendingPathComponent("Quarantine").path))
    }

    @MainActor
    func testNoncanonicalRunningRecordCannotOverwriteItsCanonicalPeerOrPublishDuplicates() throws {
        let canonical = record()
        let canonicalBytes = try encoded(canonical)
        try canonicalBytes.write(to: recordURL(canonical))
        var writes = 0
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, recordWriter: { data, url in
            writes += 1
            try data.write(to: url, options: .atomic)
        })
        try store.load()
        let prior = store.records
        var duplicate = canonical
        duplicate.state = .running
        let duplicateBytes = try encoded(duplicate)
        let unexpected = directory.appendingPathComponent("copied-record.json")
        try duplicateBytes.write(to: unexpected)

        XCTAssertThrowsError(try store.load()) { error in
            XCTAssertEqual(error as? RecentDocumentStoreError, .noncanonicalFileName)
        }

        XCTAssertEqual(store.records, prior)
        XCTAssertEqual(writes, 0)
        XCTAssertEqual(try Data(contentsOf: recordURL(canonical)), canonicalBytes)
        XCTAssertEqual(try Data(contentsOf: unexpected), duplicateBytes)
        XCTAssertEqual(store.quarantinedRecordCount, 0)
    }

    @MainActor
    func testRunningRecordWriteFailurePreservesValidHistory() throws {
        try assertFailedLoadPreservesRecord(record(state: .running))
    }

    @MainActor
    func testSchemaMigrationWriteFailurePreservesValidHistory() throws {
        try assertFailedLoadPreservesRecord(record(schemaVersion: 0))
    }

    @MainActor
    func testMissingArtifactStateWriteFailurePreservesValidHistory() throws {
        let file = GeneratedFile(role: "question_paper", url: directory.appendingPathComponent("missing.pdf"))
        try assertFailedLoadPreservesRecord(record(artifacts: [file]))
    }

    @MainActor
    func testRelocatedArtifactWriteFailurePreservesValidHistory() throws {
        let oldRoot = directory.appendingPathComponent("legacy", isDirectory: true)
        let newRoot = directory.appendingPathComponent("migrated", isDirectory: true)
        try FileManager.default.createDirectory(at: oldRoot, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: newRoot, withIntermediateDirectories: true)
        let originalPDF = Data("unchanged PDF bytes".utf8)
        try originalPDF.write(to: oldRoot.appendingPathComponent("question.pdf"))
        let newPDF = newRoot.appendingPathComponent("question.pdf")
        try originalPDF.write(to: newPDF)
        let defaults = isolatedDefaults()
        defaults.set(
            [oldRoot.standardizedFileURL.path: newRoot.standardizedFileURL.path],
            forKey: KeldinMigration.artifactMappingsKey
        )
        let file = GeneratedFile(role: "question_paper", url: oldRoot.appendingPathComponent("question.pdf"))

        try assertFailedLoadPreservesRecord(record(artifacts: [file]), defaults: defaults)

        XCTAssertEqual(try Data(contentsOf: newPDF), originalPDF)
    }

    @MainActor
    func testLegacyRunningRecordWithRelocationIsRewrittenOnce() throws {
        let oldRoot = directory.appendingPathComponent("legacy", isDirectory: true)
        let newRoot = directory.appendingPathComponent("migrated", isDirectory: true)
        try FileManager.default.createDirectory(at: oldRoot, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: newRoot, withIntermediateDirectories: true)
        let newPDF = newRoot.appendingPathComponent("question.pdf")
        let pdfBytes = Data("preserved migrated PDF".utf8)
        try pdfBytes.write(to: oldRoot.appendingPathComponent("question.pdf"))
        try pdfBytes.write(to: newPDF)
        let defaults = isolatedDefaults()
        defaults.set(
            [oldRoot.standardizedFileURL.path: newRoot.standardizedFileURL.path],
            forKey: KeldinMigration.artifactMappingsKey
        )
        let artifact = GeneratedFile(
            role: "question_paper", url: oldRoot.appendingPathComponent("question.pdf"),
            createdAt: Date(timeIntervalSince1970: 100)
        )
        let original = record(schemaVersion: 0, state: .running, artifacts: [artifact])
        try encoded(original).write(to: recordURL(original))
        let now = Date(timeIntervalSince1970: 200)
        var rewrites: [GenerationJobRecord] = []
        let store = RecentDocumentStore(
            directory: directory, retentionLimit: 10,
            clock: HistoryStorageClock(now: now), defaults: defaults,
            recordWriter: { data, url in
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                rewrites.append(try decoder.decode(GenerationJobRecord.self, from: data))
                try data.write(to: url, options: [.atomic])
            }
        )

        try store.load()

        XCTAssertEqual(rewrites.count, 1)
        XCTAssertEqual(rewrites, store.records)
        let migrated = try XCTUnwrap(store.records.first)
        XCTAssertEqual(migrated.id, original.id)
        XCTAssertEqual(migrated.schemaVersion, GenerationJobRecord.currentSchemaVersion)
        XCTAssertEqual(migrated.state, .interrupted)
        XCTAssertEqual(migrated.updatedAt, now)
        XCTAssertEqual(migrated.createdAt, original.createdAt)
        XCTAssertEqual(migrated.artifacts.map(\.id), [artifact.id])
        XCTAssertEqual(migrated.artifacts.map(\.url), [newPDF])
        XCTAssertEqual(try Data(contentsOf: newPDF), pdfBytes)
    }

    @MainActor
    func testReadFailureDoesNotQuarantineAHistoryEntry() throws {
        let entry = directory.appendingPathComponent("unreadable.json", isDirectory: true)
        try FileManager.default.createDirectory(at: entry, withIntermediateDirectories: true)
        let child = entry.appendingPathComponent("preserved.json")
        let original = Data("preserve this storage failure".utf8)
        try original.write(to: child)
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)

        XCTAssertThrowsError(try store.load())

        XCTAssertEqual(try? Data(contentsOf: child), original)
        XCTAssertFalse(FileManager.default.fileExists(atPath: directory.appendingPathComponent("Quarantine").path))
        XCTAssertEqual(store.quarantinedRecordCount, 0)
        XCTAssertTrue(store.records.isEmpty)
    }

    @MainActor
    func testCorruptJSONAndUnsupportedSchemaStillQuarantine() throws {
        let valid = record()
        try encoded(valid).write(to: recordURL(valid))
        let unsupported = record(schemaVersion: GenerationJobRecord.currentSchemaVersion + 1)
        let unsupportedBytes = try encoded(unsupported)
        try unsupportedBytes.write(to: recordURL(unsupported))
        let corruptURL = directory.appendingPathComponent("corrupt.json")
        let corruptBytes = Data("{broken JSON".utf8)
        try corruptBytes.write(to: corruptURL)
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10)

        try store.load()

        XCTAssertEqual(store.records, [valid])
        XCTAssertEqual(store.quarantinedRecordCount, 2)
        XCTAssertFalse(FileManager.default.fileExists(atPath: recordURL(unsupported).path))
        XCTAssertFalse(FileManager.default.fileExists(atPath: corruptURL.path))
        let quarantined = try FileManager.default.contentsOfDirectory(
            at: directory.appendingPathComponent("Quarantine"), includingPropertiesForKeys: nil
        )
        XCTAssertEqual(quarantined.count, 2)
        let bytes = try quarantined.map { try Data(contentsOf: $0) }
        XCTAssertTrue(bytes.contains(corruptBytes))
        XCTAssertTrue(bytes.contains(unsupportedBytes))
    }

    @MainActor
    private func assertFailedLoadPreservesRecord(_ failing: GenerationJobRecord, defaults: UserDefaults? = nil) throws {
        let existing = record()
        try encoded(existing).write(to: recordURL(existing))
        var writeAttempts = 0
        let store = RecentDocumentStore(directory: directory, retentionLimit: 10, defaults: defaults ?? isolatedDefaults(), recordWriter: { _, _ in
            writeAttempts += 1
            throw InjectedHistoryFailure.write
        })
        try store.load()
        let previousRecords = store.records
        let original = try encoded(failing)
        let originalURL = recordURL(failing)
        try original.write(to: originalURL)

        XCTAssertThrowsError(try store.load()) { error in
            XCTAssertEqual(error as? InjectedHistoryFailure, .write)
        }

        XCTAssertEqual(writeAttempts, 1)
        XCTAssertEqual(try? Data(contentsOf: originalURL), original)
        XCTAssertEqual(store.records, previousRecords)
        XCTAssertEqual(store.quarantinedRecordCount, 0)
        XCTAssertFalse(FileManager.default.fileExists(atPath: directory.appendingPathComponent("Quarantine").path))
    }

    private func record(
        schemaVersion: Int = GenerationJobRecord.currentSchemaVersion,
        state: GenerationJobState = .completed,
        artifacts: [GeneratedFile] = []
    ) -> GenerationJobRecord {
        let date = Date(timeIntervalSince1970: 100)
        return GenerationJobRecord(
            schemaVersion: schemaVersion,
            configuration: GenerationConfiguration(
                boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 1, dryRun: false
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: state, artifacts: artifacts,
            qualification: QualificationSnapshot(
                engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false
            ),
            createdAt: date, updatedAt: date
        )
    }

    private func recordURL(_ record: GenerationJobRecord) -> URL {
        directory.appendingPathComponent("\(record.id.uuidString).json")
    }

    private func encoded(_ record: GenerationJobRecord) throws -> Data {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return try encoder.encode(record)
    }
}

private enum InjectedHistoryFailure: Error, Equatable {
    case write
}

private struct HistoryStorageClock: AppClock {
    let now: Date
}
