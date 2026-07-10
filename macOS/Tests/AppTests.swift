import XCTest
@testable import PastPaperCreator

final class PastPaperCreatorTests: XCTestCase {
    func testBackendProgressEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"progress","stage":"render","message":"Rendering question paper","progress":0.88}"#)
        XCTAssertEqual(event, .progress(stage: "render", message: "Rendering question paper", progress: 0.88))
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

    func testAppStoreModeDisablesOllamaManagement() {
        XCTAssertFalse(DistributionMode.appStore.canManageOllama)
        XCTAssertTrue(DistributionMode.direct.canManageOllama)
    }

    func testHostedProvidersAreMarkedOffDevice() {
        XCTAssertFalse(AIProvider.ollama.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.openAI.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.anthropic.sendsPromptsOffDevice)
    }

    func testReviewLinksAreValidHTTPSURLs() {
        XCTAssertEqual(AppLinks.privacyPolicy.scheme, "https")
        XCTAssertEqual(AppLinks.projectHelp.scheme, "https")
        XCTAssertTrue(AppLinks.privacyPolicy.absoluteString.contains("#privacy"))
        XCTAssertTrue(AppLinks.projectHelp.absoluteString.contains("#examforge"))
    }

    func testCatalogReadyBoardsUseCorrectResourceFolders() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        XCTAssertTrue(economics.isReady)
        XCTAssertEqual(economics.resourcePath, "a-levels/economics/edexcel-a")
        XCTAssertEqual(economics.backendSubject, "economics")

        let computerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-aqa"))
        XCTAssertTrue(computerScience.isReady)
        XCTAssertEqual(computerScience.resourcePath, "a-levels/computer-science/aqa")
        XCTAssertEqual(computerScience.backendSubject, "computer_science")

        let placeholder = try XCTUnwrap(ExamCatalog.board(id: "biology-aqa"))
        XCTAssertFalse(placeholder.isReady)
    }
}
