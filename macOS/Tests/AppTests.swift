import AppKit
import XCTest
@testable import PaperCreator

final class PaperCreatorTests: XCTestCase {
    func testQualificationReadinessKeepsThreeEvidenceLevelsIndependent() {
        let readiness = QualificationReadiness(
            engineeringValidated: true,
            visuallyCalibrated: true,
            empiricallyCalibrated: false
        )

        XCTAssertTrue(readiness.engineeringValidated)
        XCTAssertTrue(readiness.visuallyCalibrated)
        XCTAssertFalse(readiness.empiricallyCalibrated)
        XCTAssertEqual(readiness.highestLevelTitle, "Visually calibrated")
    }

    func testLegacyRegistryGatesMigrateWithoutFalseEmpiricalCalibration() throws {
        let catalog = Data(
            #"{"qualification":"A-Level","subjects":[{"id":"economics","title":"Economics","system_image":"chart.line.uptrend.xyaxis","boards":[{"id":"aqa","title":"AQA"}]}]}"#.utf8
        )
        let registry = Data(
            #"{"schema_version":2,"qualification":"a-level","families":[{"app_subject":"economics","app_board":"aqa","backend_subject":"economics_aqa","resource_path":"economics/aqa","content_mode":"ai-assisted","supported_providers":["ollama"],"advertised":true,"papers":[{"id":"1","title":"Paper 1","detail":"Markets","gates":{"release":true,"visual":true,"difficulty":false}}]}]}"#.utf8
        )

        let subjects = try CatalogLoader.load(catalogData: catalog, registryData: registry)
        let readiness = try XCTUnwrap(subjects.first?.boards.first?.papers.first?.readiness)

        XCTAssertTrue(readiness.engineeringValidated)
        XCTAssertTrue(readiness.visuallyCalibrated)
        XCTAssertFalse(readiness.empiricallyCalibrated)
    }

    func testBackendHandshakeDecodesProtocolCapabilities() throws {
        let event = try BackendEvent(
            jsonLine: #"{"protocol":2,"type":"hello","event_id":1,"timestamp":"2026-07-29T12:00:00Z","job_id":"job","backend_version":"2.0.0","capabilities":["manifest"]}"#
        )
        XCTAssertEqual(
            event,
            .hello(
                protocolVersion: 2,
                backendVersion: "2.0.0",
                capabilities: ["manifest"]
            )
        )
    }

    func testBackendProgressEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"progress","stage":"render","message":"Rendering question paper","progress":0.88}"#)
        XCTAssertEqual(event, .progress(stage: "render", message: "Rendering question paper", progress: 0.88))
    }

    func testBackendMLXCacheMissPreservesRecoveryCode() throws {
        let event = try BackendEvent(
            jsonLine: #"{"type":"error","message":"Approve setup again.","code":"mlx_setup_required"}"#
        )
        XCTAssertEqual(
            event,
            .error(message: "Approve setup again.", code: "mlx_setup_required")
        )
    }

    func testBackendFileEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"file","role":"mark_scheme","path":"/tmp/ms.pdf"}"#)
        XCTAssertEqual(event, .file(role: "mark_scheme", path: "/tmp/ms.pdf"))
    }

    func testBackendClientLaunchesBridge() async throws {
        let events = try await BackendClient().collect(arguments: ["ollama-status"])
        XCTAssertTrue(events.contains { event in
            if case .ollamaStatus = event {
                return true
            }
            return false
        })
    }

    func testBuiltAppContainsStandaloneBackend() throws {
        let bundle = Bundle(for: ApplicationCoordinator.self).bundleURL
        let executable = bundle
            .appendingPathComponent("Contents/Resources/PaperCreatorBackend/PaperCreatorBackend")
        XCTAssertTrue(FileManager.default.isExecutableFile(atPath: executable.path))
        let calibrationSchema = bundle.appendingPathComponent(
            "Contents/Resources/PaperCreatorBackend/_internal/Resources/empirical-calibration.schema.json"
        )
        XCTAssertTrue(FileManager.default.fileExists(atPath: calibrationSchema.path))
    }

    func testBenchmarkSampleEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"benchmark_sample","elapsed":2,"cpu_load":18.5,"cpu_mb_s":720,"memory_available_gb":9.25,"memory_pressure_percent":42,"swap_used_gb":0.5,"disk_write_mb_s":420,"disk_read_mb_s":900,"disk_free_gb":128,"small_file_ms":3.2,"network_latency_ms":42,"network_download_mb_s":34,"ollama_latency_ms":12,"thermal_speed_limit_percent":100,"pdf_pages_per_s":22}"#)
        if case let .benchmarkSample(sample) = event {
            XCTAssertEqual(sample.elapsed, 2)
            XCTAssertEqual(sample.cpuLoad, 18.5)
            XCTAssertEqual(sample.cpuThroughputMBs, 720)
            XCTAssertEqual(sample.memoryAvailableGB, 9.25)
            XCTAssertEqual(sample.memoryPressurePercent, 42)
            XCTAssertEqual(sample.swapUsedGB, 0.5)
            XCTAssertEqual(sample.diskWriteMBs, 420)
            XCTAssertEqual(sample.diskReadMBs, 900)
            XCTAssertEqual(sample.diskFreeGB, 128)
            XCTAssertEqual(sample.smallFileMS, 3.2)
            XCTAssertEqual(sample.networkLatencyMS, 42)
            XCTAssertEqual(sample.networkDownloadMBs, 34)
            XCTAssertEqual(sample.ollamaLatencyMS, 12)
            XCTAssertEqual(sample.thermalSpeedLimitPercent, 100)
            XCTAssertEqual(sample.pdfPagesPerSecond, 22)
        } else {
            XCTFail("Expected benchmark sample")
        }
    }

    func testGenerationEstimateUsesModelSize() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(economics.papers.first)
        let small = GenerationEstimator.initialEstimate(
            board: economics,
            paper: paper,
            provider: .ollama,
            model: "qwen2.5:7b",
            dryRun: false,
            benchmark: nil
        )
        let large = GenerationEstimator.initialEstimate(
            board: economics,
            paper: paper,
            provider: .ollama,
            model: "qwen2.5:32b",
            dryRun: false,
            benchmark: nil
        )
        XCTAssertGreaterThan(large.totalSeconds, small.totalSeconds)
    }

    func testOllamaGuideSelectsAMemoryAppropriateModel() throws {
        let guide = try OllamaModelGuide.load(bundle: .main)
        let eightGB = guide.recommendation(physicalMemoryBytes: 8 * 1_073_741_824)
        let sixteenGB = guide.recommendation(physicalMemoryBytes: 16 * 1_073_741_824)

        XCTAssertEqual(eightGB.model, "qwen2.5:7b")
        XCTAssertEqual(sixteenGB.model, "gemma4:12b")
        XCTAssertEqual(sixteenGB.contextWindow, "256K")
        XCTAssertEqual(sixteenGB.appContextWindow, "16K")
        XCTAssertEqual(
            AppDefaults.ollamaModel,
            OllamaModelGuide.currentRecommendation.model
        )
        XCTAssertTrue(guide.otherModelWarning.localizedCaseInsensitiveContains("results may vary"))
        XCTAssertTrue(guide.sources.allSatisfy { $0.scheme == "https" })
    }

    func testTutorialScreenshotsAreBundled() {
        XCTAssertNotNil(NSImage(named: NSImage.Name("TutorialWorkspace")))
        XCTAssertNotNil(NSImage(named: NSImage.Name("TutorialModelSettings")))
    }

    func testDisplayPathAbbreviatesOnlyTheHomeFolder() {
        let home = FileManager.default.homeDirectoryForCurrentUser
        XCTAssertEqual(AppDefaults.displayPath(home), "~")
        XCTAssertEqual(
            AppDefaults.displayPath(home.appendingPathComponent("Downloads")),
            "~/Downloads"
        )
        XCTAssertEqual(
            AppDefaults.displayPath(URL(fileURLWithPath: "/Users/Shared/Papers")),
            "/Users/Shared/Papers"
        )
    }

    func testAppStoreModeDisablesOllamaManagement() {
        XCTAssertFalse(DistributionMode.appStore.canManageOllama)
        XCTAssertTrue(DistributionMode.direct.canManageOllama)
    }

    func testAppStoreWorkspaceIsPrivateAndNotDownloads() {
        let path = AppDefaults.appStoreWorkingFolder().path
        XCTAssertTrue(path.contains("/Library/Containers/"))
        XCTAssertTrue(path.hasSuffix("/Data/Library/Application Support/Paper creator/Generated papers"))
        XCTAssertFalse(path.contains("/Data/Downloads"))
    }

    @MainActor
    func testPreviewModePreferencePersists() {
        let defaults = UserDefaults.standard
        let previous = defaults.object(forKey: AppStorageKey.dryRun)
        defer {
            if let previous {
                defaults.set(previous, forKey: AppStorageKey.dryRun)
            } else {
                defaults.removeObject(forKey: AppStorageKey.dryRun)
            }
        }

        defaults.set(true, forKey: AppStorageKey.dryRun)
        let application = ApplicationCoordinator()
        XCTAssertTrue(application.dryRun)

        application.setDryRun(false)
        XCTAssertFalse(defaults.bool(forKey: AppStorageKey.dryRun))
    }

    func testHostedProvidersAreMarkedOffDevice() {
        XCTAssertFalse(AIProvider.ollama.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.openAI.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.anthropic.sendsPromptsOffDevice)
    }

    func testAppleMLXSetupPolicyRequestsConsentOnlyForUnpreparedLiveModels() {
        let model = "mlx-community/test-model"

        XCTAssertTrue(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: false
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [model],
                usesAI: true,
                dryRun: false
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: true
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .ollama,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: false
            )
        )
    }

    func testCancelledMLXCacheRecoveryDoesNotLeakIntoSuccessfulRetry() {
        var recovery = MLXRecoveryState()

        recovery.beginGeneration()
        recovery.requestSetup()
        recovery.cancel()
        recovery.beginGeneration()

        XCTAssertFalse(recovery.consumeSetupRequest())
    }

    func testReviewLinksAreValidHTTPSURLs() {
        XCTAssertEqual(AppLinks.privacyPolicy.scheme, "https")
        XCTAssertEqual(AppLinks.projectHelp.scheme, "https")
        XCTAssertTrue(AppLinks.privacyPolicy.absoluteString.contains("#privacy"))
        XCTAssertEqual(
            AppLinks.projectHelp.absoluteString,
            "https://github.com/james8464/Past-paper-generation"
        )
    }

    func testCatalogReadyBoardsUseCorrectResourceFolders() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        XCTAssertTrue(economics.isReady)
        XCTAssertEqual(economics.resourcePath, "economics/edexcel-a")
        XCTAssertEqual(economics.backendSubject, "economics")
        XCTAssertEqual(economics.papers.map(\.id), ["1", "2", "3"])

        let aqaEconomics = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))
        XCTAssertTrue(aqaEconomics.isReady)
        XCTAssertEqual(aqaEconomics.resourcePath, "economics/aqa")
        XCTAssertEqual(aqaEconomics.backendSubject, "economics_aqa")
        XCTAssertEqual(aqaEconomics.papers.map(\.id), ["1", "2", "3"])

        let ocrEconomics = try XCTUnwrap(ExamCatalog.board(id: "economics-ocr"))
        XCTAssertTrue(ocrEconomics.isReady)
        XCTAssertEqual(ocrEconomics.resourcePath, "economics/ocr")
        XCTAssertEqual(ocrEconomics.backendSubject, "economics_ocr")
        XCTAssertEqual(ocrEconomics.papers.map(\.id), ["1", "2", "3"])

        let computerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-aqa"))
        XCTAssertTrue(computerScience.isReady)
        XCTAssertEqual(computerScience.resourcePath, "computer-science/aqa")
        XCTAssertEqual(computerScience.backendSubject, "computer_science")
        XCTAssertEqual(computerScience.papers.map(\.id), ["1", "2"])

        let ocrComputerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-ocr"))
        XCTAssertTrue(ocrComputerScience.isReady)
        XCTAssertEqual(ocrComputerScience.resourcePath, "computer-science/ocr")
        XCTAssertEqual(ocrComputerScience.backendSubject, "computer_science_ocr")
        XCTAssertEqual(ocrComputerScience.papers.map(\.id), ["1", "2"])

        let aqaBusiness = try XCTUnwrap(ExamCatalog.board(id: "business-aqa"))
        XCTAssertTrue(aqaBusiness.isReady)
        XCTAssertEqual(aqaBusiness.resourcePath, "business/aqa")
        XCTAssertEqual(aqaBusiness.backendSubject, "business_aqa")
        XCTAssertEqual(aqaBusiness.papers.map(\.id), ["1", "2", "3"])

        let aqaAccounting = try XCTUnwrap(ExamCatalog.board(id: "accounting-aqa"))
        XCTAssertTrue(aqaAccounting.isReady)
        XCTAssertEqual(aqaAccounting.resourcePath, "accounting/aqa")
        XCTAssertEqual(aqaAccounting.backendSubject, "accounting_aqa")
        XCTAssertEqual(aqaAccounting.papers.map(\.id), ["1", "2"])

        XCTAssertNil(ExamCatalog.board(id: "biology-aqa"))
    }

    func testBundledCatalogLoadsFromCanonicalResources() throws {
        let subjects = try CatalogLoader.load(bundle: .main)
        XCTAssertEqual(subjects.count, 4)
        XCTAssertEqual(subjects.flatMap(\.boards).filter(\.isReady).count, 7)
    }

    func testCatalogExposesAIForEveryGenerator() throws {
        let edexcel = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let aqa = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))

        XCTAssertTrue(edexcel.usesAI)
        XCTAssertEqual(Set(edexcel.supportedProviders), Set(AIProvider.allCases))
        XCTAssertTrue(aqa.usesAI)
        XCTAssertEqual(Set(aqa.supportedProviders), Set(AIProvider.allCases))
        XCTAssertTrue(aqa.papers.allSatisfy { !$0.readiness.empiricallyCalibrated })
    }

    @MainActor
    func testAIGeneratorRequiresOllamaCheck() throws {
        let defaults = UserDefaults.standard
        let previousWelcome = defaults.object(forKey: AppStorageKey.hasSeenWelcome)
        defer {
            if let previousWelcome {
                defaults.set(previousWelcome, forKey: AppStorageKey.hasSeenWelcome)
            } else {
                defaults.removeObject(forKey: AppStorageKey.hasSeenWelcome)
            }
        }
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let application = ApplicationCoordinator()
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))
        application.selectBoard(board)
        application.aiProvider = .ollama
        application.selectedModel = AppDefaults.ollamaModel
        application.ollamaState = OllamaState()
        application.setDryRun(false)
        XCTAssertEqual(application.generationBlocker, "Check Ollama before generating.")
    }

    func testRecentDocumentMetadataRoundTrips() throws {
        let document = GeneratedFile(
            role: "question_paper",
            url: URL(fileURLWithPath: "/tmp/practice.pdf"),
            subject: "Economics AQA",
            paper: "Paper 1"
        )
        let data = try JSONEncoder().encode([document])
        let restored = try JSONDecoder().decode([GeneratedFile].self, from: data)
        XCTAssertEqual(restored, [document])
    }
}
