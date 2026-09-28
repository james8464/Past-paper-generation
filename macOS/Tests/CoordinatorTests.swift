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

    private func qualityReport() throws -> GenerationQualityReport {
        let url = temporaryDirectory.appendingPathComponent("quality.json")
        let manifest = #"{"request":{"subject":"economics_aqa","paper":"1","seed":42,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"form","item_count":1,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":1,"counts":{"reviewed-fixed":1},"reviewed_fixed_items":1,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":1,"failed_checks":[],"item_review_evidence":{"reviewed_items":1,"approved_items":1,"coverage":1.0,"reasoning_range_fit":1,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":1}},"outputs":{}}"#
        try Data(manifest.utf8).write(to: url)
        return try XCTUnwrap(GenerationQualityReport.load(from: url))
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
    func testCompletionRecordsExportedArtifactLocations() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        let coordinator = GenerationCoordinator(history: store)
        let record = GenerationJobRecord.fixture(state: .pending)
        try coordinator.begin(record)
        coordinator.receive(.file(role: "question_paper", path: "/private/working/sujet.pdf"))
        let exported = GeneratedFile(role: "question_paper", url: temporaryDirectory.appendingPathComponent("sujet.pdf"))
        try Data("PDF fixture".utf8).write(to: exported.url)
        try coordinator.complete(artifacts: [exported])
        XCTAssertEqual(store.records.first?.artifacts.map(\.url), [exported.url])
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
    func testCatalogStoreRestoresNonBoardNavigationDestination() throws {
        let suite = "PaperCreatorCatalogNavigationTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }

        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        store.show(.history)

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.sidebarSelection, .history)
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
    func testApplicationCoordinatorOwnsFocusedCoordinators() {
        let model = ApplicationCoordinator()

        XCTAssertEqual(model.settingsStore.provider, model.aiProvider)
        XCTAssertEqual(model.catalogStore.subjects, ExamCatalog.subjects)
        XCTAssertTrue(model.modelCoordinator.isModelListStale)
        XCTAssertFalse(model.benchmarkCoordinator.isRunning)
        XCTAssertGreaterThan(model.recentDocumentStore.retentionLimit, 0)
        XCTAssertNil(model.generationCoordinator.activeJob)
    }

    @MainActor
    func testSavedReportClearsOnlyForAcceptedTargetChanges() throws {
        let model = ApplicationCoordinator()
        let board = try XCTUnwrap(
            ExamCatalog.readyBoards.first { $0.papers.count > 1 }
        )
        model.selectBoard(board)
        let original = model.selectedPaperID
        let changed = try XCTUnwrap(board.papers.first { $0.id != original })
        let report = try qualityReport()

        model.lastQualityReport = report
        model.selectPaperID(original)
        XCTAssertEqual(model.lastQualityReport, report)
        model.selectPaperID("not-a-paper")
        XCTAssertEqual(model.lastQualityReport, report)
        model.isRunning = true
        model.selectPaperID(changed.id)
        XCTAssertEqual(model.lastQualityReport, report)
        model.isRunning = false
        model.selectPaperID(changed.id)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testModeToggleAndArtifactOnlyRelaunchDoNotInventOrChangeSavedFacts() throws {
        let model = ApplicationCoordinator()
        let report = try qualityReport()
        model.lastQualityReport = report

        model.setDryRun(!model.dryRun)

        XCTAssertEqual(model.lastQualityReport, report)
        XCTAssertEqual(model.lastQualityReport?.savedMode, .live)
        XCTAssertEqual(
            model.qualityDiagnosticLines,
            GenerationQualityPolicy.presentation(for: report).diagnosticLines
        )
        XCTAssertNil(ApplicationCoordinator().lastQualityReport)
    }

    @MainActor
    func testAssessmentKindChangeClearsSavedReportOnAcceptedNewTarget() throws {
        let model = ApplicationCoordinator()
        let board = try XCTUnwrap(
            ExamCatalog.readyBoards.first {
                !$0.fullPapers.isEmpty && !$0.questionBanks.isEmpty
            }
        )
        model.selectBoard(board)
        model.lastQualityReport = try qualityReport()

        model.selectAssessmentKind(.questionBank)

        XCTAssertEqual(model.selectedPaper.assessmentKind, .questionBank)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testDuplicateConfigurationRestoresSelectionsAndSeed() throws {
        let model = ApplicationCoordinator()
        let record = GenerationJobRecord.fixture(state: .completed)

        model.duplicateConfiguration(record)

        XCTAssertEqual(model.selectedBoardID, record.configuration.boardID)
        XCTAssertEqual(model.selectedPaperID, record.configuration.paperID)
        XCTAssertEqual(model.aiProvider.backendID, record.configuration.provider)
        XCTAssertEqual(model.pendingGenerationSeed, record.configuration.seed)
        XCTAssertEqual(model.sidebarSelection, .board(record.configuration.boardID))
    }

    @MainActor
    func testReportedBackendFailureFinalizesHistoryAndReleasesSeed() throws {
        let model = ApplicationCoordinator()
        let record = GenerationJobRecord.fixture(state: .pending)
        model.duplicateConfiguration(record)
        try model.generationCoordinator.begin(record)
        model.apply(.error(message: "Checkpoint identity changed", code: "french_generation_failed"))
        model.finishGeneration(.success(1))
        XCTAssertNil(model.pendingGenerationSeed)
        XCTAssertNil(model.generationCoordinator.activeJob)
        XCTAssertEqual(model.recentDocumentStore.records.first(where: { $0.id == record.id })?.state, .failed)
    }

    @MainActor
    func testFrenchHistoryPreservesContextWithoutUKBoardLookup() throws {
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: "fr-national-nsi", paperID: "written-2027", provider: "ollama",
                model: "fixture", seed: 55, dryRun: false, educationSystem: "fr-national",
                assessmentID: FrenchAssessmentRequest.assessmentID, documentLanguage: "fr-FR"
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 2)
        XCTAssertEqual(store.duplicateConfiguration(of: record).configuration, record.configuration)
        let model = ApplicationCoordinator()
        model.duplicateConfiguration(record)
        XCTAssertEqual(model.sidebarSelection, .frenchBaccalaureat)
        XCTAssertEqual(model.pendingGenerationSeed, 55)
        XCTAssertEqual(model.selectedModel, "fixture")
    }

    @MainActor
    func testInvalidConfigurationDoesNotClearSavedReportOrChangeTarget() throws {
        let model = ApplicationCoordinator()
        let report = try qualityReport()
        model.lastQualityReport = report
        let originalBoard = model.selectedBoardID
        let originalPaper = model.selectedPaperID
        let differentBoard = try XCTUnwrap(
            ExamCatalog.readyBoards.first { $0.id != originalBoard }
        )
        let fixture = GenerationJobRecord.fixture(state: .completed)
        let invalid = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: differentBoard.id,
                paperID: "not-a-paper",
                provider: fixture.configuration.provider,
                model: fixture.configuration.model,
                seed: fixture.configuration.seed,
                dryRun: fixture.configuration.dryRun
            ),
            provenance: fixture.provenance,
            state: fixture.state,
            artifacts: fixture.artifacts,
            qualification: fixture.qualification
        )

        model.duplicateConfiguration(invalid)

        XCTAssertEqual(model.selectedBoardID, originalBoard)
        XCTAssertEqual(model.selectedPaperID, originalPaper)
        XCTAssertEqual(model.lastQualityReport, report)
    }

    @MainActor
    func testApplyingHistoryConfigurationUsesAcceptedTargetChangePolicy() throws {
        let model = ApplicationCoordinator()
        let fixture = GenerationJobRecord.fixture(state: .completed)
        let board = try XCTUnwrap(ExamCatalog.board(id: fixture.configuration.boardID))
        model.selectBoard(board)
        model.selectPaperID(fixture.configuration.paperID)
        let report = try qualityReport()
        model.lastQualityReport = report

        model.duplicateConfiguration(fixture)
        XCTAssertEqual(model.lastQualityReport, report)

        let otherPaper = try XCTUnwrap(
            board.papers.first { $0.id != fixture.configuration.paperID }
        )
        let changed = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: board.id,
                paperID: otherPaper.id,
                provider: fixture.configuration.provider,
                model: fixture.configuration.model,
                seed: fixture.configuration.seed,
                dryRun: fixture.configuration.dryRun
            ),
            provenance: fixture.provenance,
            state: fixture.state,
            artifacts: fixture.artifacts,
            qualification: fixture.qualification
        )
        model.duplicateConfiguration(changed)

        XCTAssertEqual(model.selectedPaperID, otherPaper.id)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testCreateAgainUsesDifferentSeedAndPreviewOpensDocuments() throws {
        let model = ApplicationCoordinator()
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
