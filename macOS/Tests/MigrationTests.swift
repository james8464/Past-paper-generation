// Exercise file and preference imports with isolated data, never a user's installed app.

import Foundation
import XCTest
@testable import Keldin

final class MigrationTests: XCTestCase {
    @MainActor
    func testStartupImportReturnsWhileCopyWaitsAndFinishesAllRootsBeforeVersioning() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinStartupImport-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let manager = MigrationTestFileManager(root: root)
        let defaults = isolatedDefaults()
        defaults.set(AIProvider.appleIntelligence.rawValue, forKey: AppStorageKey.aiProvider)
        let source = root.appendingPathComponent("Library/Application Support/Paper creator")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        let bytes = Data("original".utf8)
        try bytes.write(to: source.appendingPathComponent("original.pdf"))
        let plan = try XCTUnwrap(KeldinMigration.startupPlan(defaults: defaults, fileManager: manager, distributionMode: .direct, legacyDomainReader: { _, _ in
            [AppStorageKey.ollamaModel: "imported-before-init", "interfaceLanguage": "en"]
        }))
        let gate = ManualImportGate()
        let availability = StartupAvailabilityCounter()
        let application = ApplicationCoordinator(
            defaults: defaults, secrets: ImportHistoryTestSecrets(),
            historyDirectory: plan.destination.appendingPathComponent("JobHistory"),
            backend: ControlledRunBackend(), distributionMode: .direct,
            appleIntelligenceChecker: { _ in
                await availability.record()
                return .unchecked
            },
            startupImportPlan: plan,
            startupCopyFiles: { sources, destination in
                await gate.pause()
                return await PreviousAppDataFileImporter.shared.copyExisting(from: sources, to: destination)
            }
        )
        XCTAssertEqual(application.selectedModel, "imported-before-init")
        XCTAssertTrue(application.isImportingPreviousData)
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        await gate.waitForStart()
        let callsDuringCopy = await availability.calls
        XCTAssertEqual(callsDuringCopy, 0)
        XCTAssertFalse(application.isRefreshingAppleIntelligence)
        await Task { @MainActor in application.showHistory() }.value
        XCTAssertEqual(application.sidebarSelection, .history)
        XCTAssertFalse(application.canGenerate)
        XCTAssertNil(application.beginPreviousAppDataImport(from: source, destination: plan.destination))
        let task = try XCTUnwrap(application.startupImportTask)
        await gate.release()
        await task.value
        XCTAssertFalse(application.isImportingPreviousData)
        XCTAssertFalse(KeldinMigration.needsImport(defaults: defaults))
        XCTAssertFalse(application.showError)
        await application.refreshAppleIntelligenceAvailability()?.value
        let callsAfterCopy = await availability.calls
        XCTAssertGreaterThanOrEqual(callsAfterCopy, 1)
        XCTAssertEqual(try Data(contentsOf: source.appendingPathComponent("original.pdf")), bytes)
        XCTAssertEqual(try Data(contentsOf: plan.destination.appendingPathComponent("original.pdf")), bytes)
    }

    @MainActor
    func testStartupImportFailureKeepsRetryPendingAndStoreNeverReadsLegacyPreferences() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinStartupFailure-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let defaults = isolatedDefaults()
        defaults.set("en", forKey: "interfaceLanguage")
        let plan = try XCTUnwrap(KeldinMigration.startupPlan(defaults: defaults, fileManager: MigrationTestFileManager(root: root), distributionMode: .appStore, legacyDomainReader: { _, _ in
            XCTFail("Store startup must not read another preference domain")
            return nil
        }))
        let application = ApplicationCoordinator(
            defaults: defaults, secrets: ImportHistoryTestSecrets(),
            historyDirectory: plan.destination.appendingPathComponent("JobHistory"),
            backend: ControlledRunBackend(), distributionMode: .appStore,
            startupImportPlan: plan,
            startupCopyFiles: { _, _ in
                KeldinMigration.StartupCopyResult(successfulSources: [], failures: ["fixture failure"])
            }
        )
        let task = try XCTUnwrap(application.startupImportTask)
        await task.value
        XCTAssertTrue(application.showError)
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        XCTAssertFalse(application.isImportingPreviousData)
    }

    @MainActor
    func testStartupBatchCopiesOffMainActorRetainsPartialSuccessAndRetriesMissingFiles() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinStartupBatch-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let first = root.appendingPathComponent("first")
        let second = root.appendingPathComponent("second")
        let destination = root.appendingPathComponent("current")
        for source in [first, second] {
            try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
            try Data(source.lastPathComponent.utf8).write(to: source.appendingPathComponent(source.lastPathComponent + ".pdf"))
        }
        let worker = PreviousAppDataFileImporter { source, target in
            XCTAssertFalse(Thread.isMainThread)
            if source == second { throw CocoaError(.fileReadNoPermission) }
            try KeldinMigration.copyMissingTree(from: source, to: target)
        }
        let result = await worker.copyExisting(from: [first, second], to: destination)
        XCTAssertEqual(result.successfulSources, [first])
        XCTAssertEqual(result.failures.count, 1)
        let defaults = isolatedDefaults()
        XCTAssertFalse(KeldinMigration.finishStartupImport(defaults: defaults, failures: result.failures).isEmpty)
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        try Data("keep current".utf8).write(to: destination.appendingPathComponent("first.pdf"))
        let retry = await PreviousAppDataFileImporter.shared.copyExisting(from: [first, second], to: destination)
        XCTAssertTrue(retry.failures.isEmpty)
        XCTAssertTrue(KeldinMigration.finishStartupImport(defaults: defaults, failures: retry.failures).isEmpty)
        XCTAssertFalse(KeldinMigration.needsImport(defaults: defaults))
        XCTAssertEqual(try String(contentsOf: destination.appendingPathComponent("first.pdf"), encoding: .utf8), "keep current")
        XCTAssertEqual(try String(contentsOf: destination.appendingPathComponent("second.pdf"), encoding: .utf8), "second")
    }

    @MainActor
    func testStartupHistoryLoadFailureDoesNotFinishMigration() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinStartupHistory-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("old")
        let destination = root.appendingPathComponent("current")
        let defaults = isolatedDefaults()
        defaults.set("en", forKey: "interfaceLanguage")
        let gate = ManualImportGate()
        let application = ApplicationCoordinator(
            defaults: defaults, secrets: ImportHistoryTestSecrets(),
            historyDirectory: destination.appendingPathComponent("JobHistory"),
            backend: ControlledRunBackend(), distributionMode: .appStore,
            startupImportPlan: KeldinMigration.StartupPlan(sources: [source], destination: destination),
            startupCopyFiles: { _, _ in
                await gate.pause()
                return KeldinMigration.StartupCopyResult(successfulSources: [], failures: [])
            }
        )
        await gate.waitForStart()
        // A valid record at a noncanonical name must remain an error, not be discarded.
        let history = destination.appendingPathComponent("JobHistory")
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 42, dryRun: true),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        try encoder.encode(record).write(to: history.appendingPathComponent("wrong-name.json"))
        await gate.release()
        let task = try XCTUnwrap(application.startupImportTask)
        await task.value
        XCTAssertTrue(application.errorMessage.contains("Couldn't load generation history."))
        XCTAssertTrue(application.showError)
        XCTAssertEqual(application.status, "Error")
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        XCTAssertFalse(application.isImportingPreviousData)
    }

    @MainActor
    func testManualImportExplainsInvalidFolderChoices() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinImportChoice-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("old")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        let marker = source.appendingPathComponent("preserved")
        let bytes = Data("unchanged".utf8)
        try bytes.write(to: marker)
        XCTAssertThrowsError(try KeldinMigration.copyMissingTree(from: source, to: source)) {
            XCTAssertEqual($0 as? KeldinImportError, .currentDataFolder)
        }
        XCTAssertThrowsError(try KeldinMigration.copyMissingTree(from: source, to: source.appendingPathComponent("nested"))) {
            XCTAssertEqual($0 as? KeldinImportError, .containsCurrentDataFolder)
        }
        for (destination, english, french) in [
            (source, "This is Keldin’s current data folder. Choose the previous app’s folder.", "Ce dossier contient les données actuelles de Keldin. Choisissez le dossier de l’ancienne application."),
            (source.appendingPathComponent("nested"), "Choose the previous app’s own folder. It cannot contain Keldin’s current data folder.", "Choisissez le dossier propre à l’ancienne application. Il ne doit pas contenir le dossier des données actuelles de Keldin."),
        ] {
            for (language, expected) in [("en", english), ("fr", french)] {
                let defaults = isolatedDefaults()
                defaults.set(2, forKey: KeldinMigration.completionKey)
                defaults.set(language, forKey: "interfaceLanguage")
                let application = isolatedApplication(defaults: defaults, distributionMode: .appStore)
                let task = try XCTUnwrap(application.beginPreviousAppDataImport(
                    from: source, destination: destination,
                    startAccess: { _ in false }, stopAccess: { _ in XCTFail("No scope was granted") }
                ))
                await task.value
                XCTAssertEqual(application.errorMessage, expected)
                XCTAssertTrue(application.showError)
                XCTAssertFalse(application.isImportingPreviousData)
                XCTAssertEqual(try Data(contentsOf: marker), bytes)
            }
        }
        XCTAssertFalse(FileManager.default.fileExists(atPath: source.appendingPathComponent("nested").path))
    }

    func testImportPickerExplainsPDFPreservationAndHistoryRetention() {
        let message: LocalizedStringResource = "Choose the previous app's Application Support folder. Existing PDFs will not be replaced. The history limit still applies."
        XCTAssertEqual(InterfaceText.resolve(message, language: "en"), "Choose the previous app's Application Support folder. Existing PDFs will not be replaced. The history limit still applies.")
        XCTAssertEqual(InterfaceText.resolve(message, language: "fr"), "Choisissez le dossier Application Support de l’ancienne application. Les PDF existants ne seront pas remplacés. La limite de l’historique reste applicable.")
    }

    @MainActor
    func testManualImportReportsHistoryReloadFailureWithoutSuccessStatus() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinImportHistoryError-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("old")
        let destination = root.appendingPathComponent("Keldin")
        let defaults = isolatedDefaults()
        defaults.set(2, forKey: KeldinMigration.completionKey)
        defaults.set("en", forKey: "interfaceLanguage")
        let application = ApplicationCoordinator(
            defaults: defaults, secrets: ImportHistoryTestSecrets(),
            historyDirectory: destination.appendingPathComponent("JobHistory"),
            backend: ControlledRunBackend(), distributionMode: .appStore
        )
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 42, dryRun: true),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let relativePath = "JobHistory/not-a-job-id.json"
        let sourceRecord = source.appendingPathComponent(relativePath)
        try FileManager.default.createDirectory(at: sourceRecord.deletingLastPathComponent(), withIntermediateDirectories: true)
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let bytes = try encoder.encode(record)
        try bytes.write(to: sourceRecord)
        var accessEvents: [String] = []
        let task = try XCTUnwrap(application.beginPreviousAppDataImport(
            from: source, destination: destination,
            startAccess: { _ in accessEvents.append("start"); return true },
            stopAccess: { _ in accessEvents.append("stop") }
        ))
        await task.value
        XCTAssertTrue(application.showError)
        XCTAssertTrue(application.errorMessage.contains("Couldn't load generation history."))
        XCTAssertEqual(application.status, "Error")
        XCTAssertFalse(application.isImportingPreviousData)
        XCTAssertTrue(application.canImportPreviousData)
        XCTAssertEqual(accessEvents, ["start", "stop"])
        XCTAssertEqual(try Data(contentsOf: sourceRecord), bytes)
        XCTAssertEqual(try Data(contentsOf: destination.appendingPathComponent(relativePath)), bytes)
    }

    @MainActor
    func testManualImportKeepsNavigationResponsiveAndBlocksConflictingWork() async throws {
        let defaults = isolatedDefaults()
        defaults.set(2, forKey: KeldinMigration.completionKey)
        defaults.set("en", forKey: "interfaceLanguage")
        let backend = ControlledRunBackend()
        let application = isolatedApplication(defaults: defaults, backend: backend, distributionMode: .appStore)
        application.showWelcome = false
        application.setDryRun(true)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinManualImport-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("old")
        let destination = root.appendingPathComponent("new")
        application.outputFolder = root.appendingPathComponent("exports")
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 42, dryRun: true),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        try application.recentDocumentStore.save(record)
        let gate = ManualImportGate()
        var accessEvents: [String] = []
        let task = try XCTUnwrap(application.beginPreviousAppDataImport(
            from: source, destination: destination,
            copyFiles: { actualSource, actualDestination in
                XCTAssertEqual(actualSource, source)
                XCTAssertEqual(actualDestination, destination)
                await gate.pause()
            },
            startAccess: { _ in accessEvents.append("start"); return true },
            stopAccess: { _ in accessEvents.append("stop") }
        ))
        await gate.waitForStart()
        XCTAssertTrue(application.isImportingPreviousData)
        XCTAssertFalse(application.isRunning)
        XCTAssertFalse(application.canImportPreviousData)
        XCTAssertFalse(application.canGenerate)
        XCTAssertEqual(application.generationBlocker, "Previous app data is being imported.")
        XCTAssertEqual(accessEvents, ["start"])
        application.outputFolder = root.appendingPathComponent("different-export")
        XCTAssertNil(application.beginPreviousAppDataImport(from: source, destination: destination))
        application.showHistory()
        XCTAssertEqual(application.sidebarSelection, .history)
        let heartbeat = Task { @MainActor in application.showDocuments() }
        await heartbeat.value
        XCTAssertEqual(application.sidebarSelection, .documents)
        let retention = application.settingsStore.historyRetentionLimit
        application.setHistoryRetentionLimit(retention + 10)
        XCTAssertEqual(application.settingsStore.historyRetentionLimit, retention)
        application.removeHistory(record)
        XCTAssertTrue(application.recentDocumentStore.records.contains { $0.id == record.id })
        application.generate()
        application.generateFrenchFixture(largePrint: false)
        application.generateOccitanieActivity()
        application.prepareFrenchReferences()
        application.requestMLXDownloadInfo()
        application.confirmMLXSetup()
        application.confirmPullModel(ModelDownloadRequest(model: "fixture"))
        application.refreshOllama()
        XCTAssertNil(application.refreshAppleIntelligenceAvailability())
        application.startBenchmark()
        XCTAssertFalse(application.benchmarkCoordinator.isRunning)
        XCTAssertTrue(backend.requests.isEmpty)
        await gate.release()
        await task.value
        XCTAssertFalse(application.isImportingPreviousData)
        XCTAssertTrue(application.canImportPreviousData)
        XCTAssertEqual(accessEvents, ["start", "stop"])
        XCTAssertEqual(defaults.dictionary(forKey: KeldinMigration.artifactMappingsKey) as? [String: String], [source.path: destination.path])
        XCTAssertFalse(application.showError)
    }

    @MainActor
    func testManualImportFailureReleasesScopeAndAllowsAnotherAttempt() async throws {
        for granted in [false, true] {
            let defaults = isolatedDefaults()
            defaults.set(2, forKey: KeldinMigration.completionKey)
            let application = isolatedApplication(defaults: defaults, distributionMode: .appStore)
            let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinManualImportError-\(UUID().uuidString)")
            var stops = 0
            let task = try XCTUnwrap(application.beginPreviousAppDataImport(
                from: root.appendingPathComponent("old"), destination: root.appendingPathComponent("new"),
                copyFiles: { _, _ in throw CocoaError(.fileReadNoPermission) },
                startAccess: { _ in granted }, stopAccess: { _ in stops += 1 }
            ))
            await task.value
            XCTAssertFalse(application.isImportingPreviousData)
            XCTAssertEqual(stops, granted ? 1 : 0)
            XCTAssertTrue(application.showError)
            XCTAssertNil(defaults.dictionary(forKey: KeldinMigration.artifactMappingsKey))
            XCTAssertTrue(application.canImportPreviousData)
        }
    }

    @MainActor
    func testManualImportRefusesAnActiveRunOrBenchmarkBeforeAcquiringScope() {
        let defaults = isolatedDefaults()
        defaults.set(2, forKey: KeldinMigration.completionKey)
        let backend = ControlledRunBackend()
        let application = isolatedApplication(defaults: defaults, backend: backend)
        application.showWelcome = false
        application.setDryRun(true)
        application.outputFolder = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinRefusedImportExports-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: application.outputFolder) }
        application.generate()
        XCTAssertTrue(application.isRunning)
        var accessStarts = 0
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinRefusedImport-\(UUID().uuidString)")
        XCTAssertNil(application.beginPreviousAppDataImport(
            from: root, destination: root.appendingPathComponent("new"), startAccess: { _ in accessStarts += 1; return true }
        ))
        application.cancelGeneration()
        application.benchmarkCoordinator.begin()
        XCTAssertNil(application.beginPreviousAppDataImport(
            from: root, destination: root.appendingPathComponent("new"), startAccess: { _ in accessStarts += 1; return true }
        ))
        XCTAssertEqual(accessStarts, 0)
        application.benchmarkCoordinator.cancel()
    }

    @MainActor
    func testManualFileWorkerCopiesOffMainActorWithoutOverwritingFiles() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinImportWorker-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("old"), destination = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)
        try Data("old".utf8).write(to: source.appendingPathComponent("existing.txt"))
        try Data("current".utf8).write(to: destination.appendingPathComponent("existing.txt"))
        try Data("copied".utf8).write(to: source.appendingPathComponent("new.txt"))
        let worker = PreviousAppDataFileImporter(copyTree: { source, destination in
            XCTAssertFalse(Thread.isMainThread)
            try KeldinMigration.copyMissingTree(from: source, to: destination)
        })
        try await worker.copy(from: source, to: destination)
        XCTAssertEqual(try Data(contentsOf: destination.appendingPathComponent("existing.txt")), Data("current".utf8))
        XCTAssertEqual(try Data(contentsOf: destination.appendingPathComponent("new.txt")), Data("copied".utf8))
    }

    func testStoreMigrationNeverReadsLegacyPreferenceDomainAndStillImportsSelectedFiles() throws {
        for mode in [DistributionMode.appStore, .direct] {
            for manualImport in [false, true] {
                let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationDomain-\(UUID().uuidString)")
                defer { try? FileManager.default.removeItem(at: root) }
                let manager = MigrationTestFileManager(root: root)
                let source = root.appendingPathComponent("selected-old-folder")
                try manager.createDirectory(at: source, withIntermediateDirectories: true)
                let original = Data("retained original PDF".utf8)
                try original.write(to: source.appendingPathComponent("paper.pdf"))
                let defaults = isolatedDefaults()
                defaults.set(AIProvider.apple.rawValue, forKey: AppStorageKey.aiProvider)
                var queriedDomains: [String] = []
                let readLegacy: (UserDefaults, String) -> [String: Any]? = { _, domain in
                    queriedDomains.append(domain)
                    return [AppStorageKey.aiProvider: AIProvider.ollama.rawValue, AppStorageKey.ollamaModel: "legacy-fixture"]
                }
                if manualImport {
                    try KeldinMigration.importData(from: source, defaults: defaults, fileManager: manager, distributionMode: mode, legacyDomainReader: readLegacy)
                    let destination = root.appendingPathComponent("Library/Application Support/Keldin/paper.pdf")
                    XCTAssertEqual(try Data(contentsOf: destination), original)
                    XCTAssertEqual(try Data(contentsOf: source.appendingPathComponent("paper.pdf")), original)
                } else {
                    XCTAssertTrue(KeldinMigration.prepare(defaults: defaults, fileManager: manager, distributionMode: mode, legacyDomainReader: readLegacy).isEmpty)
                }
                XCTAssertEqual(queriedDomains, mode == .direct ? [KeldinMigration.legacyBundleID] : [])
                XCTAssertEqual(defaults.string(forKey: AppStorageKey.aiProvider), AIProvider.apple.rawValue)
                XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), mode == .direct ? "legacy-fixture" : nil)
            }
        }
    }
    func testArtifactCollisionNeverSubstitutesDifferentDestinationBytes() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationCollision-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let original = Data("original assessment".utf8)
        let current = Data("different current assessment".utf8)
        try original.write(to: source)
        try current.write(to: destination)
        try KeldinMigration.copyMissingTree(from: old, to: new)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)

        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)
        XCTAssertEqual(try Data(contentsOf: source), original)
        XCTAssertEqual(try Data(contentsOf: destination), current)
    }

    func testMissingOriginalRequiresVerifiedCopyAndRejectsLaterDestinationChanges() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationProof-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let bytes = Data("verified original assessment".utf8)
        try bytes.write(to: destination)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)

        try bytes.write(to: source)
        let verified = KeldinMigration.relocatedArtifact(artifact, defaults: defaults)
        XCTAssertEqual(verified.url, destination)
        XCTAssertEqual(verified.id, artifact.id)
        try FileManager.default.removeItem(at: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), verified)

        try Data("replacement assessment".utf8).write(to: destination)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)
    }

    func testObservedSourceConflictRevokesProofBeforeTheOriginalDisappears() throws {
        for failure in ["changed bytes", "read denied", "symbolic link"] {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationRevocation-\(UUID().uuidString)")
            defer { try? FileManager.default.removeItem(at: root) }
            let old = root.appendingPathComponent("old")
            let new = root.appendingPathComponent("new")
            try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
            try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
            let source = old.appendingPathComponent("paper.pdf")
            let destination = new.appendingPathComponent("paper.pdf")
            let bytes = Data("assessment A".utf8)
            try bytes.write(to: source)
            try bytes.write(to: destination)
            let defaults = isolatedDefaults()
            defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
            let artifact = GeneratedFile(role: "question_paper", url: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)

            if failure == "changed bytes" {
                try Data("assessment B".utf8).write(to: source)
            } else if failure == "symbolic link" {
                try FileManager.default.removeItem(at: source)
                try FileManager.default.createSymbolicLink(atPath: source.path, withDestinationPath: destination.path)
            }
            let refused = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
                if failure == "read denied", url == source { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            })
            XCTAssertEqual(refused, artifact, failure)

            try FileManager.default.removeItem(at: source)

            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact, failure)
            XCTAssertEqual(try Data(contentsOf: destination), bytes)
            try bytes.write(to: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
            try FileManager.default.removeItem(at: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
        }
    }

    func testRejectedDestinationRevokesProofBeforeTheOriginalDisappears() throws {
        for failure in ["read denied", "symbolic link"] {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationDestination-\(UUID().uuidString)")
            defer { try? FileManager.default.removeItem(at: root) }
            let old = root.appendingPathComponent("old")
            let new = root.appendingPathComponent("new")
            try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
            try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
            let source = old.appendingPathComponent("paper.pdf")
            let destination = new.appendingPathComponent("paper.pdf")
            let bytes = Data("assessment A".utf8)
            try bytes.write(to: source)
            try bytes.write(to: destination)
            let defaults = isolatedDefaults()
            defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
            let artifact = GeneratedFile(role: "question_paper", url: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
            if failure == "symbolic link" {
                try FileManager.default.removeItem(at: destination)
                try FileManager.default.createSymbolicLink(atPath: destination.path, withDestinationPath: source.path)
            }

            let refused = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
                if failure == "read denied", url == destination { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            })
            XCTAssertEqual(refused, artifact, failure)
            try FileManager.default.removeItem(at: source)
            if failure == "symbolic link" { try FileManager.default.removeItem(at: destination) }
            try bytes.write(to: destination)

            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact, failure)
        }
    }

    func testIdentityMigrationRevisitsVersionOneForTheV35FamilyLedger() {
        let defaults = isolatedDefaults()
        defaults.set(1, forKey: KeldinMigration.completionKey)
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        defaults.set(2, forKey: KeldinMigration.completionKey)
        XCTAssertFalse(KeldinMigration.needsImport(defaults: defaults))
    }

    @MainActor
    func testImportRetainsFrenchFamilyUseAfterJobHistoryPruning() throws {
        let defaults = isolatedDefaults()
        let families = FrenchAssessmentRequest.familyIDs
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: families], into: defaults)
        let application = isolatedApplication(defaults: defaults)
        XCTAssertEqual(try application.savedFrenchFamilies(), Array(families.indices))
    }

    @MainActor
    func testImportUnionsFrenchFamilyUseWithoutReplacingCurrentUse() throws {
        let defaults = isolatedDefaults()
        let families = FrenchAssessmentRequest.familyIDs
        defaults.set([families[0]], forKey: AppStorageKey.frenchSavedFamilyIDs)
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: [families[4]]], into: defaults)
        XCTAssertEqual(try isolatedApplication(defaults: defaults).savedFrenchFamilies(), [0, 4])
    }

    @MainActor
    func testCorruptImportedFamilyLedgerBlocksGenerationWithoutDeletingCurrentUse() {
        let defaults = isolatedDefaults()
        let existing = [FrenchAssessmentRequest.familyIDs[0]]
        defaults.set(existing, forKey: AppStorageKey.frenchSavedFamilyIDs)
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: "not an array"], into: defaults)
        XCTAssertEqual(defaults.stringArray(forKey: AppStorageKey.frenchSavedFamilyIDs), existing)
        XCTAssertThrowsError(try isolatedApplication(defaults: defaults).savedFrenchFamilies())
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: [FrenchAssessmentRequest.familyIDs[4]]], into: defaults)
        XCTAssertEqual(try isolatedApplication(defaults: defaults).savedFrenchFamilies(), [0, 4])
    }

    func testImportPreservesCurrentPreferencesAndIgnoresUnknownKeys() {
        let defaults = isolatedDefaults()
        defaults.set("current", forKey: AppStorageKey.ollamaModel)
        KeldinMigration.importPreferences([
            AppStorageKey.ollamaModel: "previous",
            AppStorageKey.selectedBoardID: "economics_aqa",
            "interfaceLanguage": "fr",
            "unrelated": "ignored",
        ], into: defaults)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), "current")
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.selectedBoardID), "economics_aqa")
        XCTAssertEqual(defaults.string(forKey: "interfaceLanguage"), "fr")
        XCTAssertNil(defaults.object(forKey: "unrelated"))
    }

    func testImportMergesHistoryWithoutReplacingCurrentRecords() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old/Job History")
        let new = root.appendingPathComponent("new/Job History")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        try Data("old".utf8).write(to: old.appendingPathComponent("conflict.json"))
        try Data("new".utf8).write(to: new.appendingPathComponent("conflict.json"))
        try Data("accepted".utf8).write(to: old.appendingPathComponent("accepted.json"))
        try KeldinMigration.copyMissingTree(from: root.appendingPathComponent("old"), to: root.appendingPathComponent("new"))
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("conflict.json"), encoding: .utf8), "new")
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("accepted.json"), encoding: .utf8), "accepted")
        XCTAssertEqual(try String(contentsOf: old.appendingPathComponent("conflict.json"), encoding: .utf8), "old")
        XCTAssertThrowsError(try KeldinMigration.copyMissingTree(from: old, to: old.appendingPathComponent("recursive")))
    }

    func testEnvironmentAliasDoesNotOverrideAnExplicitEmptyValue() {
        XCTAssertEqual(KeldinMigration.environmentValue("KELDIN_ROOT", environment: ["PAPER_CREATOR_ROOT": "/old"]), "/old")
        XCTAssertEqual(KeldinMigration.environmentValue("KELDIN_ROOT", environment: ["KELDIN_ROOT": "", "PAPER_CREATOR_ROOT": "/old"]), "")
    }

    func testModelSnapshotLinksAreCopiedWithoutFollowingThem() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try Data("weights".utf8).write(to: old.appendingPathComponent("blob"))
        try FileManager.default.createSymbolicLink(atPath: old.appendingPathComponent("snapshot").path, withDestinationPath: "blob")
        try KeldinMigration.copyMissingTree(from: old, to: new)
        XCTAssertEqual(try FileManager.default.destinationOfSymbolicLink(atPath: new.appendingPathComponent("snapshot").path), "blob")
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("snapshot"), encoding: .utf8), "weights")
    }


    func testImportedHistoryPointsToCopiedArtifactsWithoutChangingTheirIdentity() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let target = new.appendingPathComponent("paper.pdf")
        try Data("saved PDF".utf8).write(to: target)
        try Data("saved PDF".utf8).write(to: old.appendingPathComponent("paper.pdf"))
        let file = GeneratedFile(role: "question_paper", url: old.appendingPathComponent("paper.pdf"))
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let relocated = KeldinMigration.relocatedArtifact(file, defaults: defaults)
        XCTAssertEqual(relocated.id, file.id)
        XCTAssertEqual(relocated.url, target)
        XCTAssertEqual(relocated.createdAt, file.createdAt)
        let external = GeneratedFile(role: "question_paper", url: root.appendingPathComponent("elsewhere.pdf"))
        XCTAssertEqual(KeldinMigration.relocatedArtifact(external, defaults: defaults), external)
    }

    func testUnreadableOriginalCannotUseAnEarlierCopyProof() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationDenied-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let bytes = Data("matching assessment".utf8)
        try bytes.write(to: source)
        try bytes.write(to: destination)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)

        let result = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
            if url == source { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: url)
        })

        XCTAssertEqual(result, artifact)
        XCTAssertEqual(try Data(contentsOf: source), bytes)
        XCTAssertEqual(try Data(contentsOf: destination), bytes)
    }

}

private actor StartupAvailabilityCounter {
    private(set) var calls = 0
    func record() { calls += 1 }
}

private struct ImportHistoryTestSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) { }
}

private actor ManualImportGate {
    private var started = false
    private var startWaiter: CheckedContinuation<Void, Never>?
    private var resumeCopy: CheckedContinuation<Void, Never>?

    func pause() async {
        started = true
        startWaiter?.resume()
        startWaiter = nil
        await withCheckedContinuation { resumeCopy = $0 }
    }

    func waitForStart() async {
        if started { return }
        await withCheckedContinuation { startWaiter = $0 }
    }

    func release() {
        resumeCopy?.resume()
        resumeCopy = nil
    }
}

private final class MigrationTestFileManager: FileManager, @unchecked Sendable {
    private let root: URL

    init(root: URL) {
        self.root = root
        super.init()
    }

    override var homeDirectoryForCurrentUser: URL { root }

    override func homeDirectory(forUser userName: String) -> URL? { root }

    override func urls(for directory: SearchPathDirectory, in domainMask: SearchPathDomainMask) -> [URL] {
        [root.appendingPathComponent("Library/Application Support")]
    }
}
