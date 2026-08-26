import Foundation
import XCTest
@testable import PaperCreator

final class CoordinatorTests: XCTestCase {
    private var temporaryDirectory: URL!

    override func setUpWithError() throws {
        temporaryDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("PaperCreatorCoordinatorTests-(UUID().uuidString)")
        try FileManager.default.createDirectory(
            at: temporaryDirectory,
            withIntermediateDirectories: true
        )
    }

    override func tearDownWithError() throws {
        if let temporaryDirectory {
            try? FileManager.default.removeItem(at: temporaryDirectory)
        }
    }

    @MainActor
    func testHistoryPersistsVersionedJobAndRestoresAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        let record = GenerationJobRecord.fixture(state: .completed)
        try original.save(record)

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records, [record])
        XCTAssertEqual(relaunched.records.first?.schemaVersion, GenerationJobRecord.currentSchemaVersion)
    }

    @MainActor
    func testRunningJobBecomesInterruptedAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try original.save(.fixture(state: .running))

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records.first?.state, .interrupted)
    }

    @MainActor
    func testSchemaZeroHistoryMigratesWithoutLosingConfiguration() throws {
        let record = GenerationJobRecord.fixture(state: .completed)
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(record)
        var payload = try XCTUnwrap(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )
        payload.removeValue(forKey: "schemaVersion")
        let legacyData = try JSONSerialization.data(withJSONObject: payload)
        try legacyData.write(
            to: temporaryDirectory.appendingPathComponent("\(record.id.uuidString).json")
        )

        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.load()

        XCTAssertEqual(store.records.first?.schemaVersion, 1)
        XCTAssertEqual(store.records.first?.configuration, record.configuration)
        XCTAssertEqual(store.quarantinedRecordCount, 0)
    }

    @MainActor
    func testCancelledJobRemainsCancelledAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try original.save(.fixture(state: .cancelled))

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records.first?.state, .cancelled)
    }

    @MainActor
    func testCorruptHistoryIsQuarantinedWithoutDiscardingValidJobs() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.save(.fixture(state: .completed))
        try Data("not json".utf8).write(to: temporaryDirectory.appendingPathComponent("broken.json"))

        try store.load()

        XCTAssertEqual(store.records.count, 1)
        XCTAssertEqual(store.quarantinedRecordCount, 1)
        let quarantine = temporaryDirectory.appendingPathComponent("Quarantine", isDirectory: true)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: quarantine.path).count, 1)
    }

    @MainActor
    func testCompletedJobWithMissingArtifactIsMarkedActionably() throws {
        let missing = GeneratedFile(
            role: "question_paper",
            url: temporaryDirectory.appendingPathComponent("missing.pdf")
        )
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.save(.fixture(state: .completed, artifacts: [missing]))

        try store.load()

        XCTAssertEqual(store.records.first?.state, .missingArtifacts)
        XCTAssertEqual(store.records.first?.missingArtifactCount, 1)
    }

    @MainActor
    func testRetentionIsBoundedAndDuplicateConfigurationGetsNewIdentity() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 2)
        let first = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 1)
        )
        let second = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 2)
        )
        let third = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 3)
        )
        try store.save(first)
        try store.save(second)
        try store.save(third)

        XCTAssertEqual(store.records.map(\.id), [third.id, second.id])
        let duplicate = store.duplicateConfiguration(of: third, newSeed: 99)
        XCTAssertNotEqual(duplicate.id, third.id)
        XCTAssertEqual(duplicate.configuration.seed, 99)
        XCTAssertEqual(duplicate.state, .pending)
        XCTAssertTrue(duplicate.artifacts.isEmpty)
    }

    @MainActor
    func testModelCoordinatorExpiresStaleModelList() {
        let clock = TestClock(now: Date(timeIntervalSince1970: 1_000))
        let coordinator = ModelCoordinator(clock: clock, staleAfter: 60)
        coordinator.receiveModels(["gemma4:12b"], at: clock.now)
        XCTAssertFalse(coordinator.isModelListStale)

        clock.now = Date(timeIntervalSince1970: 1_061)
        XCTAssertTrue(coordinator.isModelListStale)
    }

    @MainActor
    func testCatalogStoreFiltersAndPersistsFavouritesAndRecentConfigurations() throws {
        let suite = "PaperCreatorCatalogTests-(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        store.searchText = "computer"

        XCTAssertTrue(store.filteredSubjects.allSatisfy { subject in
            subject.title.localizedCaseInsensitiveContains("computer")
                || subject.boards.contains {
                    $0.title.localizedCaseInsensitiveContains("computer")
                        || $0.subjectTitle.localizedCaseInsensitiveContains("computer")
                }
        })
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first)
        store.toggleFavourite(board.id)
        store.recordRecentConfiguration(boardID: board.id, paperID: board.papers[0].id)

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.favoriteIDs, [board.id])
        XCTAssertEqual(restored.recentConfigurationIDs.first, "\(board.id)::\(board.papers[0].id)")
    }

    @MainActor
    func testCatalogStoreOwnsAndRestoresValidSelection() throws {
        let suite = "PaperCreatorCatalogSelectionTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let board = try XCTUnwrap(ExamCatalog.readyBoards.last)
        let paper = try XCTUnwrap(board.papers.last)

        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertTrue(store.selectBoard(board, isLocked: false))
        XCTAssertTrue(store.selectPaperID(paper.id, isLocked: false))

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.selectedBoardID, board.id)
        XCTAssertEqual(restored.selectedPaperID, paper.id)
        XCTAssertEqual(restored.sidebarSelection, .board(board.id))
        XCTAssertFalse(restored.selectPaperID("not-a-paper", isLocked: false))
    }

    @MainActor
    func testSettingsStorePersistsPreferencesAndDelegatesSecrets() throws {
        let suite = "PaperCreatorSettingsTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let secrets = MemorySecrets()
        let settings = SettingsStore(defaults: defaults, secrets: secrets)
        settings.provider = .apple
        settings.appleModel = "mlx-community/test"
        settings.historyRetentionLimit = 0
        settings.openAIAPIKey = "private-test-value"
        settings.save()

        let restored = SettingsStore(defaults: defaults, secrets: secrets)
        XCTAssertEqual(restored.provider, .apple)
        XCTAssertEqual(restored.appleModel, "mlx-community/test")
        XCTAssertEqual(restored.historyRetentionLimit, 1)
        XCTAssertEqual(restored.openAIAPIKey, "private-test-value")
    }

    @MainActor
    func testAppViewModelOwnsFocusedCoordinatorsDuringCompatibilityMigration() {
        let model = AppViewModel()

        XCTAssertEqual(model.settingsStore.provider, model.aiProvider)
        XCTAssertEqual(model.catalogStore.subjects, ExamCatalog.subjects)
        XCTAssertTrue(model.modelCoordinator.isModelListStale)
        XCTAssertFalse(model.benchmarkCoordinator.isRunning)
        XCTAssertGreaterThan(model.recentDocumentStore.retentionLimit, 0)
        XCTAssertNil(model.generationCoordinator.activeJob)
    }

    @MainActor
    func testDuplicateConfigurationRestoresSelectionsAndSeed() throws {
        let model = AppViewModel()
        let record = GenerationJobRecord.fixture(state: .completed)

        model.duplicateConfiguration(record)

        XCTAssertEqual(model.selectedBoardID, record.configuration.boardID)
        XCTAssertEqual(model.selectedPaperID, record.configuration.paperID)
        XCTAssertEqual(model.aiProvider.backendID, record.configuration.provider)
        XCTAssertEqual(model.pendingGenerationSeed, record.configuration.seed)
        XCTAssertEqual(model.sidebarSelection, .board(record.configuration.boardID))
    }

    @MainActor
    func testCreateAgainUsesDifferentSeedAndPreviewOpensDocuments() throws {
        let model = AppViewModel()
        let record = GenerationJobRecord.fixture(state: .completed)
        let file = GeneratedFile(
            role: "question_paper",
            url: temporaryDirectory.appendingPathComponent("paper.pdf")
        )

        model.createAgainWithNewSeed(record)
        model.previewGeneratedFile(file)

        XCTAssertNotEqual(model.pendingGenerationSeed, record.configuration.seed)
        XCTAssertEqual(model.previewedFileID, file.id)
        XCTAssertEqual(model.sidebarSelection, .documents)
    }

    func testCopiedProvenanceIdentifiesConfigurationAndQualification() {
        let record = GenerationJobRecord.fixture(state: .completed)

        let summary = record.provenanceSummary

        XCTAssertTrue(summary.contains("economics-aqa · Paper 1"))
        XCTAssertTrue(summary.contains("Ollama · gemma4:12b · Seed 42"))
        XCTAssertTrue(summary.contains("Engineering: passed"))
        XCTAssertTrue(summary.contains("Visual: pending"))
        XCTAssertTrue(summary.contains("Empirical: pending"))
    }
}

private extension GenerationJobRecord {
    static func fixture(
        state: GenerationJobState,
        createdAt: Date = Date(timeIntervalSince1970: 10),
        artifacts: [GeneratedFile] = []
    ) -> GenerationJobRecord {
        GenerationJobRecord(
            id: UUID(),
            configuration: GenerationConfiguration(
                boardID: "economics-aqa",
                paperID: "1",
                provider: "ollama",
                model: "gemma4:12b",
                seed: 42,
                dryRun: false
            ),
            provenance: GenerationProvenance(
                appVersion: "test",
                provider: "ollama",
                model: "gemma4:12b"
            ),
            state: state,
            artifacts: artifacts,
            qualification: QualificationSnapshot(
                engineeringValidated: true,
                visuallyCalibrated: false,
                empiricallyCalibrated: false
            ),
            createdAt: createdAt,
            updatedAt: createdAt
        )
    }
}

private final class TestClock: AppClock {
    var now: Date

    init(now: Date) {
        self.now = now
    }
}

private final class MemorySecrets: SecretStoring {
    private var values: [String: String] = [:]

    func read(_ account: String) -> String {
        values[account] ?? ""
    }

    func save(_ value: String, account: String) {
        values[account] = value
    }
}
