import Combine
import Foundation
import XCTest
@testable import Keldin

final class RunIsolationTests: XCTestCase {
    @MainActor
    func testBundledMLXSetupExplanationDescribesChecksAndModelPreparationInSelectedLanguage() {
        for (language, expected) in [
            ("en", "Keldin will check Apple MLX support, then download and prepare fixture/model-3B if needed. Models can use several gigabytes of storage. Generation stays on this Mac."),
            ("fr", "Keldin vérifiera la prise en charge d’Apple MLX, puis téléchargera et préparera fixture/model-3B si nécessaire. Les modèles peuvent occuper plusieurs gigaoctets. La génération reste sur ce Mac."),
        ] {
            let defaults = isolatedDefaults()
            defaults.set(language, forKey: "interfaceLanguage")
            let application = application(backend: ControlledRunBackend(), defaults: defaults)
            application.appleModel = "  fixture/model-3B  "

            // The same truthful explanation is used by bundled direct and
            // Store builds; neither installs a runtime in the running app.
            XCTAssertEqual(application.mlxSetupExplanation, expected)
            XCTAssertFalse(application.mlxSetupExplanation.contains("install"))
            XCTAssertFalse(application.mlxSetupExplanation.contains("Terminal"))
            XCTAssertFalse(application.mlxSetupExplanation.contains("password"))
            XCTAssertFalse(application.isRunning)
        }
    }

    @MainActor
    func testOutputFolderBookmarkFailureIsVisibleInSettings() throws {
        let defaults = isolatedDefaults()
        defaults.set("fr", forKey: "interfaceLanguage")
        let application = application(backend: ControlledRunBackend(), defaults: defaults, outputFolderBookmark: { _ in
            throw CocoaError(.fileWriteUnknown)
        })
        let owner = application.settingsPresentation
        owner.activate()
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent("bookmark-fixture")

        application.setOutputFolder(folder, presentation: owner)

        XCTAssertFalse(application.showError)
        guard case let .error(message) = owner.request?.kind else { return XCTFail("Expected Settings bookmark failure") }
        XCTAssertEqual(message, "Keldin n’a pas pu mémoriser l’accès à ce dossier. Sélectionnez-le à nouveau pour conserver l’accès après le redémarrage.")
        XCTAssertNil(defaults.data(forKey: AppStorageKey.outputFolderBookmark))
    }

    @MainActor
    func testOutputFolderBookmarkSuccessPreservesPathAndBookmark() {
        let defaults = isolatedDefaults()
        var requestedURLs: [URL] = []
        let data = Data("fixture bookmark".utf8)
        let application = application(backend: ControlledRunBackend(), defaults: defaults, outputFolderBookmark: { url in
            requestedURLs.append(url)
            return data
        })
        let owner = application.settingsPresentation
        owner.activate()
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent("bookmark-success")

        application.setOutputFolder(folder, presentation: owner)

        XCTAssertEqual(requestedURLs, [folder])
        XCTAssertEqual(application.outputFolder, folder)
        XCTAssertEqual(application.benchmarkCoordinator.outputFolder, folder)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.outputFolderPath), folder.path)
        XCTAssertEqual(defaults.data(forKey: AppStorageKey.outputFolderBookmark), data)
        XCTAssertNil(owner.request)
    }

    @MainActor
    func testSettingsConsentApprovalUsesCapturedProviderAndRechecksGeneration() throws {
        for busy in [false, true] {
            let backend = ControlledRunBackend()
            let application = application(backend: backend)
            let owner = application.settingsPresentation
            owner.activate()
            application.selectAIProvider(.openAI, presentation: owner)
            let request = try XCTUnwrap(owner.request)
            if busy { application.generateFrenchPaper(largePrint: false) }
            let originalProvider = application.aiProvider
            let originalJob = application.generationCoordinator.activeJob
            guard let approved = owner.consume(id: request.id), case let .hostedConsent(provider) = approved.kind else { return XCTFail("Expected owned consent") }

            application.acceptHostedAIConsent(for: provider, presentation: owner)

            XCTAssertEqual(application.hasHostedAIConsent, !busy)
            XCTAssertEqual(application.aiProvider, busy ? originalProvider : .openAI)
            XCTAssertEqual(application.generationCoordinator.activeJob, originalJob)
            XCTAssertFalse(application.showHostedAIConsent)
            if busy {
                XCTAssertTrue(application.isRunning)
                application.cancelGeneration()
            } else {
                XCTAssertEqual(application.modelCoordinator.provider, .openAI)
                XCTAssertTrue(backend.requests.isEmpty)
            }
        }
    }

    @MainActor
    func testSettingsDownloadFailureDoesNotOverwriteRetainedMainError() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.apply(.error(message: "Retained Main error", code: "fixture"))
        let mainMessage = application.errorMessage
        let owner = application.settingsPresentation
        owner.activate()
        backend.launchError = CocoaError(.executableLoad)

        application.confirmPullModel(ModelDownloadRequest(model: "fixture/model"), presentation: owner)

        XCTAssertTrue(application.showError)
        XCTAssertEqual(application.errorMessage, mainMessage)
        guard case .error = owner.request?.kind else { return XCTFail("Expected Settings error") }
        XCTAssertFalse(application.isRunning)
    }

    @MainActor
    func testLateSettingsRefreshErrorIsRetainedWithoutInvisiblePresentation() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        let owner = application.settingsPresentation
        owner.activate()
        application.refreshOllama(presentation: owner)
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        owner.deactivate()

        backend.resumeNext(.failure(CocoaError(.fileReadUnknown)))
        await waitForRefreshCompletion(application)

        XCTAssertFalse(application.showError)
        XCTAssertFalse(owner.blocksCommands)
        XCTAssertNil(owner.request)
        XCTAssertEqual(application.progressEntries.last?.stage, "error")
        owner.activate()
        guard case .error = owner.request?.kind else { return XCTFail("Expected retained Settings error") }
    }

    @MainActor
    func testMainRefreshFailureDoesNotBecomeSettingsOwnedWhenFocusChanges() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.settingsPresentation.activate()

        backend.resumeNext(.failure(CocoaError(.fileReadUnknown)))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.showError)
        XCTAssertNil(application.settingsPresentation.request)
        XCTAssertFalse(application.settingsPresentation.blocksCommands)
        XCTAssertTrue(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: application.hasCommandBlockingPresentation, mainSceneIsFocused: false))
    }

    @MainActor
    func testSettingsPersistenceErrorStaysWithItsExplicitOwner() {
        let backend = ControlledRunBackend()
        let application = application(backend: backend, secrets: FailingSettingsSecrets())
        let settings = application.settingsPresentation
        settings.activate()
        application.openAIAPIKey = "PRIVATE_TEST_KEY"

        application.saveAISettings(presentation: settings)

        XCTAssertFalse(application.showError)
        XCTAssertTrue(settings.blocksCommands)
        guard case let .error(message) = settings.request?.kind else { return XCTFail("Expected a Settings-owned error") }
        XCTAssertFalse(message.contains("PRIVATE_TEST_KEY"))
        settings.deactivate()
        XCTAssertFalse(settings.blocksCommands)
        settings.activate()
        XCTAssertEqual(settings.request?.kind, .error(message))
    }

    @MainActor
    func testSettingsConsentHasAnExplicitOwnerAndDoesNotPresentOnMain() {
        let application = application(backend: ControlledRunBackend())
        let settings = application.settingsPresentation
        settings.activate()
        let original = application.aiProvider

        application.selectAIProvider(.openAI, presentation: settings)

        XCTAssertFalse(application.showHostedAIConsent)
        XCTAssertEqual(settings.request?.kind, .hostedConsent(.openAI))
        XCTAssertEqual(application.aiProvider, original)
        settings.deactivate()
        XCTAssertFalse(settings.blocksCommands)
        XCTAssertNil(settings.request)
        XCTAssertFalse(application.hasHostedAIConsent)
        settings.activate()
        XCTAssertNil(settings.request)
    }

    @MainActor
    func testDownloadRequestDoesNotBlockAnUnrelatedWindowGlobally() {
        let application = application(backend: ControlledRunBackend())
        application.modelToPull = "fixture/model"

        let request = application.requestPullModel()

        XCTAssertEqual(request?.model, "fixture/model")
        XCTAssertFalse(application.hasCommandBlockingPresentation)
    }

    @MainActor
    func testRecommendedDownloadRequestAndCancelPreserveTheSelectedModel() {
        let defaults = isolatedDefaults()
        defaults.set("fixture/previous-model", forKey: AppStorageKey.ollamaModel)
        let backend = ControlledRunBackend()
        let application = application(backend: backend, defaults: defaults)

        XCTAssertTrue(application.canRequestModelDownload)
        let presentation = ModelDownloadPresentation()
        presentation.present(application.requestRecommendedOllamaModel())

        XCTAssertEqual(application.modelToPull, application.ollamaRecommendation.model)
        XCTAssertTrue(presentation.isPresented)
        XCTAssertEqual(application.selectedModel, "fixture/previous-model")
        XCTAssertEqual(application.settingsStore.ollamaModel, "fixture/previous-model")
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), "fixture/previous-model")
        if let request = presentation.request { presentation.dismiss(id: request.id) }
        XCTAssertFalse(presentation.isPresented)
        XCTAssertEqual(application.selectedModel, "fixture/previous-model")
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), "fixture/previous-model")
        XCTAssertTrue(backend.requests.isEmpty)
    }

    @MainActor
    func testExplicitUseRecommendedModelStillPersistsWithoutDownloading() {
        let defaults = isolatedDefaults()
        defaults.set("fixture/previous-model", forKey: AppStorageKey.ollamaModel)
        let backend = ControlledRunBackend()
        let application = application(backend: backend, defaults: defaults)

        application.useRecommendedOllamaModel()

        XCTAssertEqual(application.selectedModel, application.ollamaRecommendation.model)
        XCTAssertEqual(application.settingsStore.ollamaModel, application.ollamaRecommendation.model)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), application.ollamaRecommendation.model)
        XCTAssertFalse(application.hasCommandBlockingPresentation)
        XCTAssertTrue(backend.requests.isEmpty)
    }

    @MainActor
    func testModelDownloadRequestsDoNotChangeAnythingWhileWorkIsBusy() {
        for benchmark in [false, true] {
            let defaults = isolatedDefaults()
            defaults.set("fixture/previous-model", forKey: AppStorageKey.ollamaModel)
            let backend = ControlledRunBackend()
            let application = application(backend: backend, defaults: defaults)
            if benchmark { application.startBenchmark() }
            else { application.generateFrenchPaper(largePrint: false) }
            application.modelToPull = "fixture/draft-tag"
            XCTAssertFalse(application.canRequestModelDownload)

            XCTAssertNil(application.requestRecommendedOllamaModel())
            XCTAssertNil(application.requestPullModel())
            XCTAssertNil(application.pullSelectedModel())

            XCTAssertFalse(application.hasCommandBlockingPresentation)
            XCTAssertEqual(application.modelToPull, "fixture/draft-tag")
            XCTAssertEqual(application.selectedModel, "fixture/previous-model")
            XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), "fixture/previous-model")
            XCTAssertEqual(backend.requests.count, 1)
            if benchmark { application.cancelBenchmark() }
            else { application.cancelGeneration() }
        }
    }

    @MainActor
    func testRecommendedDownloadSelectsOnlyItsCapturedSuccessfulModel() throws {
        for outcome in ["success", "nonzero", "throw", "error", "cancel"] {
            let defaults = isolatedDefaults()
            defaults.set("fixture/previous-model", forKey: AppStorageKey.ollamaModel)
            let backend = ControlledRunBackend()
            let application = application(backend: backend, defaults: defaults)
            let request = try XCTUnwrap(application.requestRecommendedOllamaModel())
            let requested = request.model
            application.modelToPull = "fixture/changed-before-approval"
            application.confirmPullModel(request)
            let run = try XCTUnwrap(backend.requests.first)
            application.modelToPull = "fixture/later-draft"
            switch outcome {
            case "success": run.onFinish(.success(0))
            case "nonzero": run.onFinish(.success(7))
            case "throw": run.onFinish(.failure(CocoaError(.fileReadUnknown)))
            case "error":
                run.onEvent(.error(message: "Fixture download failure", code: "fixture"))
                run.onFinish(.success(0))
            default:
                application.cancelGeneration()
                run.onFinish(.success(0))
            }
            let expected = outcome == "success" ? requested : "fixture/previous-model"
            XCTAssertEqual(application.selectedModel, expected, outcome)
            XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), expected, outcome)
            XCTAssertFalse(application.isRunning)
        }
    }

    @MainActor
    func testDownloadApprovalIsConsumedOnceAndRechecksBusyOwnership() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let presentation = ModelDownloadPresentation()
        application.modelToPull = "fixture/captured"
        presentation.present(application.requestPullModel())
        let request = try XCTUnwrap(presentation.request)
        if let approved = presentation.consume(id: request.id) { application.confirmPullModel(approved) }
        if let duplicate = presentation.consume(id: request.id) { application.confirmPullModel(duplicate) }
        XCTAssertEqual(backend.requests.count, 1)
        application.cancelGeneration()

        application.modelToPull = "fixture/next"
        presentation.present(application.requestPullModel())
        let next = try XCTUnwrap(presentation.request)
        application.startBenchmark()
        if let approved = presentation.consume(id: next.id) { application.confirmPullModel(approved) }
        XCTAssertEqual(backend.requests.count, 2) // One download, then one benchmark.
        XCTAssertFalse(application.isRunning)
        XCTAssertFalse(presentation.isPresented)
        application.cancelBenchmark()
    }

    @MainActor
    func testMLXSetupContinuesOnlyTheUnchangedLaunchTarget() throws {
        for change in ["none", "board", "paper", "provider", "model", "dryRun", "output"] {
            let backend = ControlledRunBackend()
            let application = application(backend: backend)
            application.duplicateConfiguration(pendingJob(seed: 73))
            let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI && $0.supports(.apple) && $0.papers.count > 1 })
            application.selectBoard(board)
            application.aiProvider = .apple
            application.appleModel = "fixture/model"
            application.ollamaState = OllamaState(installed: true, running: true, command: nil, message: "Fixture")
            let originalPaperID = application.selectedPaperID
            let originalOutput = application.outputFolder
            application.generate()
            XCTAssertTrue(application.showMLXSetupConfirmation)
            application.confirmMLXSetup()
            let setup = try XCTUnwrap(backend.requests.first)
            switch change {
            case "board":
                let other = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.id != board.id })
                application.catalogStore.selectedBoardID = other.id
                application.catalogStore.selectedPaperID = try XCTUnwrap(other.papers.first).id
            case "paper":
                application.catalogStore.selectedPaperID = try XCTUnwrap(board.papers.first { $0.id != originalPaperID }).id
            case "provider": application.aiProvider = .ollama
            case "model": application.appleModel = "fixture/another-model"
            case "dryRun": application.dryRun = true
            case "output": application.outputFolder = originalOutput.appendingPathComponent("different-folder")
            default: break
            }
            let chosenBoard = application.selectedBoardID
            let chosenPaper = application.selectedPaperID
            let chosenProvider = application.aiProvider
            let chosenModel = application.appleModel
            let chosenOutput = application.outputFolder

            setup.onFinish(.success(0))

            if change == "none" {
                XCTAssertEqual(backend.requests.count, 2)
                let job = try XCTUnwrap(application.generationCoordinator.activeJob)
                XCTAssertEqual(job.configuration.boardID, board.id)
                XCTAssertEqual(job.configuration.paperID, originalPaperID)
                XCTAssertEqual(job.configuration.provider, "apple")
                XCTAssertEqual(job.configuration.model, "fixture/model")
                XCTAssertEqual(job.configuration.seed, 73)
                XCTAssertTrue(application.isRunning)
                application.cancelGeneration()
            } else {
                XCTAssertEqual(backend.requests.count, 1, change)
                XCTAssertFalse(application.isRunning, change)
                XCTAssertNil(application.generationCoordinator.activeJob, change)
                XCTAssertFalse(application.showMLXSetupConfirmation, change)
                XCTAssertEqual(application.status, "Apple MLX is ready", change)
            }
            XCTAssertEqual(application.selectedBoardID, chosenBoard)
            XCTAssertEqual(application.selectedPaperID, chosenPaper)
            XCTAssertEqual(application.aiProvider, chosenProvider)
            XCTAssertEqual(application.appleModel, chosenModel)
            XCTAssertEqual(application.outputFolder, chosenOutput)
        }
    }

    @MainActor
    func testGenerationMutationsRequireTheExactOwningJob() throws {
        let historyURL = try temporaryHistoryURL()
        let store = RecentDocumentStore(directory: historyURL, retentionLimit: 10)
        let coordinator = GenerationCoordinator(history: store)
        let old = pendingJob(seed: 1)
        let current = pendingJob(seed: 2)
        try coordinator.begin(old)
        try coordinator.begin(current)
        coordinator.receive(.progress(stage: "current", message: "Current", progress: 0.2), expectedJobID: current.id)
        let recordFile = historyURL.appendingPathComponent("\(current.id.uuidString).json")
        let bytes = try Data(contentsOf: recordFile)
        let entries = coordinator.progressEntries

        coordinator.receive(.file(role: "question_paper", path: "/stale.pdf"), expectedJobID: old.id)
        coordinator.receive(.done(message: "Old result"), expectedJobID: old.id)
        XCTAssertThrowsError(try coordinator.complete(expectedJobID: old.id, artifacts: [GeneratedFile(role: "question_paper", url: URL(fileURLWithPath: "/stale.pdf"))]))
        XCTAssertThrowsError(try coordinator.cancel(expectedJobID: old.id))
        XCTAssertThrowsError(try coordinator.fail(message: "Old failure", expectedJobID: old.id))

        XCTAssertEqual(coordinator.activeJob?.id, current.id)
        XCTAssertEqual(coordinator.progress, 0.2)
        XCTAssertEqual(coordinator.progressEntries, entries)
        XCTAssertTrue(coordinator.generatedFiles.isEmpty)
        XCTAssertEqual(try Data(contentsOf: recordFile), bytes)
        try coordinator.complete(expectedJobID: current.id, artifacts: [])
        XCTAssertNil(coordinator.activeJob)
        XCTAssertEqual(store.records.first(where: { $0.id == current.id })?.state, .completed)
    }

    @MainActor
    func testPaperArtifactsKeepTheirLaunchTargetAfterSelectionChanges() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
        application.selectBoard(board)
        application.setDryRun(true)
        let originalPaper = application.selectedPaper
        application.generate()
        let job = try XCTUnwrap(application.generationCoordinator.activeJob)
        let run = try XCTUnwrap(backend.requests.first)
        let other = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.id != board.id })
        // Exercise the ownership boundary directly; normal UI changes are locked.
        application.catalogStore.selectedBoardID = other.id
        application.catalogStore.selectedPaperID = try XCTUnwrap(other.papers.first).id
        run.onEvent(.file(role: "question_paper", path: "/fixture/current-paper.pdf"))
        run.onFinish(.success(0))

        let file = try XCTUnwrap(application.currentGenerationFiles.first)
        XCTAssertEqual(file.subject, "\(board.subjectTitle) \(board.shortTitle)")
        XCTAssertEqual(file.paper, originalPaper.title)
        XCTAssertEqual(application.recentDocumentStore.records.first(where: { $0.id == job.id })?.artifacts, [file])
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertFalse(application.isRunning)
    }

    @MainActor
    func testFailedPaperBeginCannotFailAnOlderOwnedRecord() throws {
        let backend = ControlledRunBackend()
        let historyURL = try temporaryHistoryURL()
        let application = application(backend: backend, historyDirectory: historyURL)
        let prior = pendingJob(seed: 3)
        try application.generationCoordinator.begin(prior)
        let active = application.generationCoordinator.activeJob
        let backup = historyURL.deletingLastPathComponent().appendingPathComponent("backup")
        try FileManager.default.moveItem(at: historyURL, to: backup)
        try Data("temporary write blocker".utf8).write(to: historyURL)
        application.selectBoard(try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI }))
        application.setDryRun(true)

        application.generate()

        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertEqual(application.generationCoordinator.activeJob, active)
        XCTAssertFalse(application.isRunning)
        XCTAssertNil(application.pendingGenerationSeed)
        XCTAssertNil(application.generationEstimate)
    }

    @MainActor
    func testReferenceMaintenanceNeverMutatesAnUnrelatedPaperJob() throws {
        let outcomes: [Result<Int32, Error>?] = [
            .success(0), .success(1), .failure(CocoaError(.fileReadUnknown)), nil,
        ]
        for (isReview, outcome) in [false, true].flatMap({ review in outcomes.map { (review, $0) } }) {
            let backend = ControlledRunBackend()
            let history = try temporaryHistoryURL()
            let application = application(backend: backend, historyDirectory: history)
            application.selectBoard(try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI }))
            application.setDryRun(true)
            application.generate()
            let job = try XCTUnwrap(application.generationCoordinator.activeJob)
            let backup = history.deletingLastPathComponent().appendingPathComponent("history-backup")
            try FileManager.default.moveItem(at: history, to: backup)
            try Data("temporary write blocker".utf8).write(to: history)
            application.cancelGeneration()
            XCTAssertEqual(application.generationCoordinator.activeJob, job)
            try FileManager.default.removeItem(at: history)
            try FileManager.default.moveItem(at: backup, to: history)
            let originalRecords = application.recentDocumentStore.records
            let recordFile = history.appendingPathComponent("\(job.id.uuidString).json")
            let originalBytes = try Data(contentsOf: recordFile)
            let originalProgress = application.generationCoordinator.progress
            let originalFiles = application.generationCoordinator.generatedFiles

            if !isReview {
                application.prepareFrenchReferences()
            } else {
                let request = FrenchReviewRequest(
                    manifest: URL(fileURLWithPath: "/fixture/manifest.json"), reviewer: "Test fixture",
                    decision: .revise,
                    scores: Dictionary(uniqueKeysWithValues: FrenchReviewRequest.rubricKeys.map { ($0, 1) }),
                    notes: "Test fixture only."
                )
                XCTAssertEqual(application.submitFrenchReview(request), .submitted)
            }
            let maintenance = try XCTUnwrap(backend.requests.last)
            XCTAssertEqual(backend.requests.count, 2)
            maintenance.onEvent(.progress(stage: "references", message: "Reference fixture", progress: 0.8))
            maintenance.onEvent(.file(role: "reference_report", path: "/fixture/reference-report.json"))
            if let outcome {
                maintenance.onFinish(outcome)
            } else {
                application.cancelGeneration()
                maintenance.onFinish(.success(0))
            }

            XCTAssertFalse(application.isRunning)
            XCTAssertEqual(application.generationCoordinator.activeJob, job)
            XCTAssertEqual(application.generationCoordinator.progress, originalProgress)
            XCTAssertEqual(application.generationCoordinator.generatedFiles, originalFiles)
            XCTAssertEqual(application.recentDocumentStore.records, originalRecords)
            XCTAssertEqual(try Data(contentsOf: recordFile), originalBytes)
        }
    }

    @MainActor
    func testMaintenanceLaunchFailureCannotFailAnExistingPaper() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let prior = pendingJob(seed: 9)
        try application.generationCoordinator.begin(prior)
        let active = application.generationCoordinator.activeJob
        let records = application.recentDocumentStore.records
        backend.launchError = CocoaError(.executableLoad)

        application.prepareFrenchReferences()

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob, active)
        XCTAssertEqual(application.recentDocumentStore.records, records)
        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertTrue(application.showError)
    }

    @MainActor
    func testModelManagementDoesNotCollectFilesOrDiscardLastPaperResults() throws {
        for setupMLX in [false, true] {
            let backend = ControlledRunBackend()
            let application = application(backend: backend)
            application.beginDocumentCollection()
            application.apply(.file(role: "question_paper", path: "/fixture/saved-paper.pdf"))
            let files = application.currentGenerationFiles
            application.modelToPull = "fixture-model"
            if setupMLX { application.confirmMLXSetup() }
            else { application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull)) }
            let run = try XCTUnwrap(backend.requests.first)

            run.onEvent(.file(role: "question_paper", path: "/fixture/not-a-paper.pdf"))
            XCTAssertEqual(application.currentGenerationFiles, files)
            application.cancelGeneration()
            run.onFinish(.success(0))

            XCTAssertEqual(application.currentGenerationFiles, files)
            XCTAssertEqual(application.generatedFiles, files)
            XCTAssertTrue(application.recentDocumentStore.records.isEmpty)
            XCTAssertFalse(application.isRunning)
        }
    }

    @MainActor
    func testReplacedJobRefusesCallbacksAndPublicationFromThePreviousRun() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.selectBoard(try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI }))
        application.setDryRun(true)
        application.generate()
        let prior = try XCTUnwrap(backend.requests.first)
        let replacement = pendingJob(seed: 10)
        try application.generationCoordinator.begin(replacement)
        let records = application.recentDocumentStore.records
        let active = application.generationCoordinator.activeJob

        prior.onEvent(.file(role: "question_paper", path: "/fixture/stale.pdf"))
        prior.onEvent(.progress(stage: "stale", message: "Stale", progress: 0.9))
        prior.onFinish(.success(0))

        XCTAssertEqual(application.recentDocumentStore.records, records)
        XCTAssertEqual(application.generationCoordinator.activeJob, active)
        XCTAssertTrue(application.generationCoordinator.generatedFiles.isEmpty)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
        XCTAssertTrue(application.generatedFiles.isEmpty)
        XCTAssertTrue(application.showError)
        XCTAssertFalse(application.isRunning)
    }

    @MainActor
    func testBenchmarkFailureRetainsItsActionableDetailAndCanRetry() throws {
        let backend = ControlledRunBackend()
        let benchmark = BenchmarkCoordinator(backend: backend)
        benchmark.start(generationIsRunning: false)
        let failed = try XCTUnwrap(backend.requests.first)
        failed.onEvent(.error(message: "The diagnostic cannot access its test folder.", code: "benchmark_failed"))
        failed.onFinish(.success(1))

        XCTAssertFalse(benchmark.isRunning)
        XCTAssertEqual(benchmark.errorMessage, "The diagnostic cannot access its test folder.")
        benchmark.start(generationIsRunning: false)
        XCTAssertTrue(benchmark.isRunning)
        XCTAssertNil(benchmark.errorMessage)
        XCTAssertEqual(backend.requests.count, 2)
        benchmark.cancel()
    }

    @MainActor
    func testBenchmarkResultKeepsProcessOwnershipUntilItsExit() throws {
        let backend = ControlledRunBackend()
        let benchmark = BenchmarkCoordinator(backend: backend)
        benchmark.start(generationIsRunning: false)
        let run = try XCTUnwrap(backend.requests.first)
        run.onEvent(.benchmarkDone(BenchmarkVerdict(score: 0.8, verdict: "Ready", detail: "Fixture result")))

        XCTAssertTrue(benchmark.isRunning)
        XCTAssertEqual(benchmark.progress, 1)
        benchmark.start(generationIsRunning: false)
        XCTAssertEqual(backend.requests.count, 1)

        run.onFinish(.success(0))
        XCTAssertFalse(benchmark.isRunning)
        benchmark.start(generationIsRunning: false)
        XCTAssertEqual(backend.requests.count, 2)
        benchmark.cancel()
    }

    @MainActor
    func testModelLaunchConfirmationsCannotInterruptBenchmarkOwnership() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.startBenchmark()
        let status = application.status
        application.modelToPull = "fixture-model"

        application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))
        application.confirmMLXSetup()

        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertTrue(application.benchmarkCoordinator.isRunning)
        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertNil(application.generationCoordinator.activeJob)
        application.cancelBenchmark()
    }

    @MainActor
    func testModelLaunchConfirmationsCannotReplaceGenerationOwnership() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.generateFrenchPaper(largePrint: false)
        let job = try XCTUnwrap(application.generationCoordinator.activeJob)
        let status = application.status
        application.modelToPull = "fixture-model"

        application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))
        application.confirmMLXSetup()

        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.generationCoordinator.activeJob, job)
        XCTAssertTrue(application.isRunning)
        application.cancelGeneration()
    }

    @MainActor
    func testModelPullOutcomesNeverFinalizeAnUnrelatedGenerationHistory() throws {
        let outcomes: [Result<Int32, Error>] = [.success(0), .success(1), .failure(CocoaError(.fileReadUnknown))]
        for outcome in outcomes {
            let backend = ControlledRunBackend()
            let history = try temporaryHistoryURL()
            let application = application(backend: backend, historyDirectory: history)
            let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
            application.selectBoard(board)
            application.setDryRun(true)
            application.generate()
            let job = try XCTUnwrap(application.generationCoordinator.activeJob)
            let backup = history.deletingLastPathComponent().appendingPathComponent("history-backup")
            try FileManager.default.moveItem(at: history, to: backup)
            try Data("temporary write blocker".utf8).write(to: history)
            application.cancelGeneration()
            XCTAssertEqual(application.generationCoordinator.activeJob, job)
            try FileManager.default.removeItem(at: history)
            try FileManager.default.moveItem(at: backup, to: history)
            let originalHistory = application.recentDocumentStore.records
            let historyFile = history.appendingPathComponent("\(job.id.uuidString).json")
            let originalBytes = try Data(contentsOf: historyFile)
            application.modelToPull = "fixture-model"

            application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))
            let pull = try XCTUnwrap(backend.requests.last)
            XCTAssertEqual(backend.requests.count, 2)
            pull.onFinish(outcome)

            XCTAssertFalse(application.isRunning)
            XCTAssertEqual(application.generationCoordinator.activeJob, job)
            XCTAssertEqual(application.recentDocumentStore.records, originalHistory)
            XCTAssertEqual(try Data(contentsOf: historyFile), originalBytes)
        }
    }

    @MainActor
    func testFailedModelDownloadUsesTheSelectedFrenchMessage() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set("fr", forKey: "interfaceLanguage")
        let application = application(backend: backend, defaults: defaults)
        let originalModel = application.selectedModel
        application.modelToPull = "fixture-model"
        application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))
        let pull = try XCTUnwrap(backend.requests.first)

        pull.onFinish(.success(7))

        XCTAssertEqual(application.errorMessage, "Ollama a interrompu le téléchargement du modèle (code de sortie 7). Vérifiez Ollama, puis réessayez.")
        XCTAssertEqual(application.selectedModel, originalModel)
        XCTAssertFalse(application.isRunning)
        XCTAssertTrue(application.recentDocumentStore.records.isEmpty)
    }

    @MainActor
    func testCancellingModelPullDoesNotCancelAnUnrelatedGenerationJob() throws {
        let backend = ControlledRunBackend()
        let history = try temporaryHistoryURL()
        let defaults = isolatedDefaults()
        defaults.set("fr", forKey: "interfaceLanguage")
        let application = application(backend: backend, defaults: defaults, historyDirectory: history)
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
        application.selectBoard(board)
        application.setDryRun(true)
        application.generate()
        let job = try XCTUnwrap(application.generationCoordinator.activeJob)
        let backup = history.deletingLastPathComponent().appendingPathComponent("history-backup")
        try FileManager.default.moveItem(at: history, to: backup)
        try Data("temporary write blocker".utf8).write(to: history)
        application.cancelGeneration()
        try FileManager.default.removeItem(at: history)
        try FileManager.default.moveItem(at: backup, to: history)
        let originalHistory = application.recentDocumentStore.records
        let historyFile = history.appendingPathComponent("\(job.id.uuidString).json")
        let originalBytes = try Data(contentsOf: historyFile)
        application.modelToPull = "fixture-model"
        application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))

        application.cancelGeneration()

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob, job)
        XCTAssertEqual(application.recentDocumentStore.records, originalHistory)
        XCTAssertEqual(try Data(contentsOf: historyFile), originalBytes)
        XCTAssertEqual(application.progressEntries.last?.message, "Téléchargement du modèle annulé.")
    }

    @MainActor
    func testHistoryBeginFailurePreservesThePreviousCoordinatorState() throws {
        for hasActiveJob in [false, true] {
            let historyURL = try temporaryHistoryURL()
            let history = RecentDocumentStore(directory: historyURL, retentionLimit: 10)
            let coordinator = GenerationCoordinator(history: history)
            if hasActiveJob {
                let job = pendingJob(seed: 1)
                try coordinator.begin(job)
                coordinator.receive(.progress(stage: "current", message: "Existing job", progress: 0.4), expectedJobID: job.id)
                coordinator.receive(.file(role: "question_paper", path: "/existing/question.pdf"), expectedJobID: job.id)
                try FileManager.default.moveItem(
                    at: historyURL,
                    to: historyURL.deletingLastPathComponent().appendingPathComponent("preserved-history")
                )
            }
            // A regular file at the directory path fails reliably, including for
            // privileged test runners, without changing filesystem permissions.
            try Data("not a directory".utf8).write(to: historyURL)
            let previousJob = coordinator.activeJob
            let previousStatus = coordinator.status
            let previousProgress = coordinator.progress
            let previousEntries = coordinator.progressEntries
            let previousFiles = coordinator.generatedFiles
            let previousHistory = history.records

            XCTAssertThrowsError(try coordinator.begin(pendingJob(seed: 2)))

            XCTAssertEqual(coordinator.activeJob, previousJob)
            XCTAssertEqual(coordinator.status, previousStatus)
            XCTAssertEqual(coordinator.progress, previousProgress)
            XCTAssertEqual(coordinator.progressEntries, previousEntries)
            XCTAssertEqual(coordinator.generatedFiles, previousFiles)
            XCTAssertEqual(history.records, previousHistory)
        }
    }

    @MainActor
    func testUKGenerationRefusesBackendLaunchWhenHistoryCannotBeSaved() throws {
        let backend = ControlledRunBackend()
        let history = try temporaryHistoryURL()
        try Data("not a directory".utf8).write(to: history)
        let application = application(backend: backend, historyDirectory: history)
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
        application.selectBoard(board)
        application.setDryRun(true)

        application.generate()

        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertFalse(application.isRunning)
        XCTAssertTrue(application.showError)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertTrue(application.recentDocumentStore.records.isEmpty)
        XCTAssertNil(application.pendingGenerationSeed)
        XCTAssertNil(application.generationEstimate)
        application.cancelGeneration()
    }

    @MainActor
    func testFrenchGenerationHistoryFailureLeavesNoPhantomActiveJob() throws {
        let backend = ControlledRunBackend()
        let history = try temporaryHistoryURL()
        try Data("not a directory".utf8).write(to: history)
        let application = application(backend: backend, historyDirectory: history)

        application.generateFrenchPaper(largePrint: false)

        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertFalse(application.isRunning)
        XCTAssertTrue(application.showError)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertNil(application.pendingGenerationSeed)
    }

    @MainActor
    func testCancelledGenerationCannotChangeItsReplacement() throws {
        for french in [false, true] {
            let backend = ControlledRunBackend()
            let application = application(backend: backend)
            if french {
                application.generateFrenchPaper(largePrint: false)
            } else {
                let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI })
                application.selectBoard(board)
                application.setDryRun(true)
                application.generate()
            }
            let cancelled = try XCTUnwrap(backend.requests.first)
            application.cancelGeneration()
            application.generateFrenchPaper(largePrint: true)
            XCTAssertEqual(backend.requests.count, 2)
            let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
            let replacementStatus = application.status

            cancelled.onEvent(.progress(stage: "late", message: "Cancelled progress", progress: 0.9))
            cancelled.onEvent(.file(role: "question_paper", path: "/cancelled/sujet.pdf"))
            cancelled.onEvent(.done(message: "Cancelled completion"))
            cancelled.onEvent(.error(message: "Cancelled error", code: "generation_failed"))
            cancelled.onFinish(.success(1))

            XCTAssertTrue(application.isRunning)
            XCTAssertEqual(application.status, replacementStatus)
            XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
            XCTAssertTrue(application.currentGenerationFiles.isEmpty)
            XCTAssertFalse(application.showError)
            XCTAssertTrue(application.progressEntries.isEmpty)
            backend.requests[1].onEvent(.progress(stage: "current", message: "Current progress", progress: 0.2))
            XCTAssertEqual(application.generationProgress, 0.2)
            application.cancelGeneration()
        }
    }

    @MainActor
    func testCancelledGenerationIgnoresBufferedEventsBeforeAnotherRun() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.generateFrenchPaper(largePrint: false)
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        let status = application.status
        let entries = application.progressEntries

        cancelled.onEvent(.progress(stage: "late", message: "Late progress", progress: 0.8))
        cancelled.onEvent(.file(role: "question_paper", path: "/cancelled/sujet.pdf"))
        cancelled.onEvent(.done(message: "Late completion"))
        cancelled.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
        XCTAssertFalse(application.showError)
    }

    @MainActor
    func testFinishedGenerationIgnoresRepeatedCallbacks() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        application.generateFrenchPaper(largePrint: false)
        let finished = try XCTUnwrap(backend.requests.first)
        finished.onFinish(.success(1))
        let status = application.status
        let entries = application.progressEntries

        finished.onEvent(.file(role: "question_paper", path: "/finished/sujet.pdf"))
        finished.onEvent(.progress(stage: "late", message: "Late progress", progress: 0.8))
        finished.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertTrue(application.currentGenerationFiles.isEmpty)
    }

    @MainActor
    func testCancelledModelPullCannotSelectModelOrFinishReplacement() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let originalModel = application.selectedModel
        application.modelToPull = "cancelled-model"
        application.confirmPullModel(ModelDownloadRequest(model: application.modelToPull))
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        application.generateFrenchPaper(largePrint: false)
        let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)

        cancelled.onFinish(.success(0))

        XCTAssertEqual(application.selectedModel, originalModel)
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testMLXCancellationWaitsForItsOwnExitWithoutRestartingGeneration() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        let application = application(backend: backend, defaults: defaults)
        application.confirmMLXSetup()
        let cancelled = try XCTUnwrap(backend.requests.first)
        application.cancelGeneration()
        XCTAssertTrue(application.isRunning)
        cancelled.onEvent(.error(message: "Cancelled setup", code: "mlx_setup_failed"))
        cancelled.onFinish(.success(0))

        XCTAssertFalse(application.isRunning)
        XCTAssertFalse(application.showError)
        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertNil(defaults.object(forKey: AppStorageKey.preparedMLXModels))
        application.generateFrenchPaper(largePrint: false)
        let replacementID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
        cancelled.onFinish(.success(0))
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, replacementID)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testSuccessfulMLXSetupHandsOwnershipToTheGenerationRun() throws {
        let backend = ControlledRunBackend()
        let application = application(backend: backend)
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI && $0.supports(.apple) })
        application.selectBoard(board)
        application.aiProvider = .apple
        application.confirmMLXSetup()
        let setup = try XCTUnwrap(backend.requests.first)
        setup.onFinish(.success(0))

        XCTAssertEqual(backend.requests.count, 2)
        XCTAssertTrue(application.isRunning)
        let generationID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)
        setup.onEvent(.error(message: "Late setup error", code: "mlx_setup_failed"))
        setup.onFinish(.success(0))
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, generationID)
        XCTAssertTrue(application.isRunning)
        XCTAssertFalse(application.showError)
        XCTAssertEqual(backend.requests.count, 2)
        application.cancelGeneration()
    }

    @MainActor
    func testCancelledBenchmarkCannotChangeItsReplacement() throws {
        let backend = ControlledRunBackend()
        let benchmark = BenchmarkCoordinator(backend: backend)
        benchmark.start(generationIsRunning: false)
        let cancelled = try XCTUnwrap(backend.requests.first)
        benchmark.cancel()
        benchmark.start(generationIsRunning: false)
        XCTAssertEqual(backend.requests.count, 2)

        cancelled.onEvent(.error(message: "Cancelled failure", code: "benchmark_failed"))
        cancelled.onEvent(.benchmarkDone(BenchmarkVerdict(score: 99, verdict: "Old", detail: "Old result")))
        cancelled.onFinish(.success(1))

        XCTAssertTrue(benchmark.isRunning)
        XCTAssertNil(benchmark.errorMessage)
        XCTAssertNil(benchmark.verdict)
        XCTAssertEqual(benchmark.progress, 0)
        backend.requests[1].onEvent(.benchmarkDone(BenchmarkVerdict(score: 0.8, verdict: "Current", detail: "Current result")))
        backend.requests[1].onFinish(.success(0))
        XCTAssertFalse(benchmark.isRunning)
        XCTAssertEqual(benchmark.verdict?.score, 0.8)
        XCTAssertNil(benchmark.errorMessage)
    }

    @MainActor
    func testLateOllamaStatusCannotPoisonModelFreeFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let status = application.status
        let jobID = try XCTUnwrap(application.generationCoordinator.activeJob?.id)

        backend.resumeNext(.success([.error(message: "Stale Ollama status", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, jobID)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
        application.cancelGeneration()
    }

    @MainActor
    func testLateOllamaModelsCannotPoisonFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend(defersModels: true)
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        backend.resumeNext(.success([]))
        await fulfillment(of: [backend.modelsStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: true)
        let status = application.status

        backend.resumeNext(.success([.error(message: "Stale Ollama models", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        application.cancelGeneration()
    }

    @MainActor
    func testLateOllamaCollectionFailureCannotPoisonFrenchGeneration() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let status = application.status

        backend.resumeNext(.failure(CocoaError(.fileReadUnknown)))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertTrue(application.progressEntries.isEmpty)
        application.cancelGeneration()
    }

    @MainActor
    func testRefreshStaysObsoleteAfterTheNewRunFinishes() async throws {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.generateFrenchPaper(largePrint: false)
        let generation = try XCTUnwrap(backend.runs.requests.first)
        generation.onFinish(.success(1))
        XCTAssertFalse(application.isRunning)
        let error = application.errorMessage
        let entries = application.progressEntries

        backend.resumeNext(.success([.error(message: "Stale refresh after completion", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertEqual(application.errorMessage, error)
        XCTAssertEqual(application.progressEntries, entries)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
    }

    @MainActor
    func testLateOllamaRefreshCannotChangeAnActiveBenchmark() async {
        let backend = DeferredRefreshBackend()
        let application = application(backend: backend)
        application.refreshOllama()
        await fulfillment(of: [backend.statusStarted], timeout: 2)
        application.startBenchmark()
        let status = application.status

        backend.resumeNext(.success([.error(message: "Stale refresh during benchmark", code: "ollama_failed")]))
        await waitForRefreshCompletion(application)

        XCTAssertTrue(application.benchmarkCoordinator.isRunning)
        XCTAssertEqual(application.status, status)
        XCTAssertFalse(application.showError)
        XCTAssertNil(application.benchmarkCoordinator.errorMessage)
        XCTAssertEqual(backend.collectionArguments, [["ollama-status"]])
        application.cancelBenchmark()
    }

    @MainActor
    private func waitForRefreshCompletion(_ application: ApplicationCoordinator) async {
        let finished = expectation(description: "Ollama refresh finished")
        let subscription = application.$isRefreshingOllama
            .filter { !$0 }
            .prefix(1)
            .sink { _ in finished.fulfill() }
        await fulfillment(of: [finished], timeout: 2)
        subscription.cancel()
    }

    @MainActor
    private func application(
        backend: any BackendRunning, defaults: UserDefaults? = nil, historyDirectory: URL? = nil,
        secrets: any SecretStoring = RunIsolationSecrets(),
        outputFolderBookmark: @escaping (URL) throws -> Data = { url in
            try url.bookmarkData(options: .withSecurityScope, includingResourceValuesForKeys: nil, relativeTo: nil)
        }
    ) -> ApplicationCoordinator {
        let defaults = defaults ?? isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        let history = historyDirectory ?? FileManager.default.temporaryDirectory.appendingPathComponent("KeldinRunIsolation-\(UUID().uuidString)")
        addTeardownBlock { try? FileManager.default.removeItem(at: history) }
        return ApplicationCoordinator(
            defaults: defaults, secrets: secrets, historyDirectory: history, backend: backend,
            outputFolderBookmark: outputFolderBookmark
        )
    }

    private func temporaryHistoryURL() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinHistoryFailure-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        return root.appendingPathComponent("history")
    }

    private func pendingJob(seed: Int) -> GenerationJobRecord {
        GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: "economics-aqa", paperID: "1", provider: "ollama",
                model: "fixture", seed: seed, dryRun: false
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .pending, artifacts: [],
            qualification: QualificationSnapshot(
                engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false
            )
        )
    }
}

private final class FailingSettingsSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) throws { throw SecretStoreError.unexpected(operation: .write) }
}

// Each instance is driven synchronously by one main-actor test. Captured callbacks
// retain the production main-actor contract without launching a helper or model.
final class ControlledRunBackend: BackendRunning, @unchecked Sendable {
    struct Request {
        let onEvent: @Sendable @MainActor (BackendEvent) -> Void
        let onFinish: @Sendable @MainActor (Result<Int32, Error>) -> Void
    }

    private(set) var requests: [Request] = []
    var launchError: Error?

    func run(
        arguments: [String], environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        if let launchError { throw launchError }
        requests.append(Request(onEvent: onEvent, onFinish: onFinish))
        return ControlledProcess()
    }

    func collect(arguments: [String]) async throws -> [BackendEvent] { [] }
}

private final class ControlledProcess: Process, @unchecked Sendable {
    override func terminate() {}
}

// Continuations may be installed on a background executor. Protect their queue
// while tests drive the public refresh and generation actions on the main actor.
private final class DeferredRefreshBackend: BackendRunning, @unchecked Sendable {
    let runs = ControlledRunBackend()
    let statusStarted = XCTestExpectation(description: "Ollama status collection started")
    let modelsStarted = XCTestExpectation(description: "Ollama models collection started")
    private let lock = NSLock()
    private let defersModels: Bool
    private var arguments: [[String]] = []
    private var continuations: [CheckedContinuation<[BackendEvent], Error>] = []

    init(defersModels: Bool = false) {
        self.defersModels = defersModels
    }

    var collectionArguments: [[String]] { lock.withLock { arguments } }

    func run(
        arguments: [String], environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        try runs.run(arguments: arguments, environment: environment, onEvent: onEvent, onFinish: onFinish)
    }

    func collect(arguments: [String]) async throws -> [BackendEvent] {
        lock.withLock { self.arguments.append(arguments) }
        let isStatus = arguments.first == "ollama-status"
        guard isStatus || defersModels else { return [] }
        return try await withCheckedThrowingContinuation { continuation in
            lock.withLock { continuations.append(continuation) }
            (isStatus ? statusStarted : modelsStarted).fulfill()
        }
    }

    func resumeNext(_ result: Result<[BackendEvent], Error>) {
        let continuation = lock.withLock { continuations.removeFirst() }
        continuation.resume(with: result)
    }
}

private struct RunIsolationSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
