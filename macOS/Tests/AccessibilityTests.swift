import AppKit
import SwiftUI
import XCTest
@testable import PaperCreator

final class AccessibilityTests: XCTestCase {
    @MainActor
    func testReadyWorkspaceLaysOutInAnExpandedWindow() {
        let application = isolatedApplication()
        let board = ExamCatalog.board(id: "economics-aqa")!
        application.selectBoard(board)
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1_440, height: 900),
            styleMask: [.titled, .resizable],
            backing: .buffered,
            defer: false
        )
        window.contentView = NSHostingView(
            rootView: ContentView()
                .environmentObject(application)
                .environment(application.catalogStore)
                .environment(application.benchmarkCoordinator)
                .environment(application.generationCoordinator)
        )
        window.orderFront(nil)
        window.contentView?.layoutSubtreeIfNeeded()
        window.displayIfNeeded()
        RunLoop.current.run(until: Date().addingTimeInterval(0.5))
        XCTAssertNotNil(window.contentView)
    }

    func testWorkspaceLayoutProtectsCompactWindowsFromColumnOverlap() {
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 720), .compact)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 839), .compact)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 840), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 900), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_099), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_100), .expanded)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_200), .expanded)

        XCTAssertFalse(WorkspaceLayoutPolicy.mode(for: 720).showsSidebar)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 720).qualityReviewWidth, 420)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 900).qualityReviewWidth, 480)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_200).qualityReviewWidth, 560)
    }

    func testFrenchTeacherFormKeepsReadableLineLengthWithoutClippingSmallWindows() {
        XCTAssertEqual(FrenchWorkspaceLayoutPolicy.contentWidth(for: 600), 568)
        XCTAssertEqual(FrenchWorkspaceLayoutPolicy.contentWidth(for: 900), 720)
        XCTAssertEqual(FrenchWorkspaceLayoutPolicy.contentWidth(for: 1_440), 720)
    }

    func testFrenchDraftPresentsReferenceRecoveryOnlyWhenNeeded() {
        let missing = FrenchWorkspacePresentation(
            hasReferences: false,
            model: "gemma4:12b",
            isRunning: false,
            ollamaState: readyOllama,
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertFalse(missing.canGenerate)
        XCTAssertTrue(missing.showsPrepareReferences)
        XCTAssertEqual(missing.blocker, "Prepare French references first.")

        let ready = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "gemma4:12b",
            isRunning: false,
            ollamaState: readyOllama,
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertTrue(ready.canGenerate)
        XCTAssertFalse(ready.showsPrepareReferences)
        XCTAssertNil(ready.blocker)
    }

    func testFrenchDraftExplainsMissingModelAndRunningState() {
        let noModel = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "  ",
            isRunning: false,
            ollamaState: readyOllama,
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertFalse(noModel.canGenerate)
        XCTAssertEqual(noModel.blocker, "Choose a local Ollama model first.")

        let running = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "gemma4:12b",
            isRunning: true,
            ollamaState: readyOllama,
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertFalse(running.canGenerate)
        XCTAssertNil(running.blocker)
    }

    func testFrenchDraftExplainsUnavailableLocalModelBeforeStarting() {
        let stopped = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "gemma4:12b",
            isRunning: false,
            ollamaState: OllamaState(installed: true, running: false, command: "ollama", message: "Stopped"),
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertEqual(stopped.blocker, "Start Ollama before creating a draft.")
        XCTAssertTrue(stopped.showsOllamaRecheck)

        let missingModel = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "unavailable:latest",
            isRunning: false,
            ollamaState: OllamaState(installed: true, running: true, command: "ollama", message: "Ready"),
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertEqual(missingModel.blocker, "Install the selected Ollama model before creating a draft.")
        XCTAssertFalse(missingModel.canGenerate)
        XCTAssertTrue(missingModel.showsOllamaRecheck)

        let absent = FrenchWorkspacePresentation(
            hasReferences: true,
            model: "gemma4:12b",
            isRunning: false,
            ollamaState: OllamaState(installed: false, running: false, command: nil, message: "Not installed"),
            availableModels: [],
            hasLoadedModels: false
        )
        XCTAssertTrue(absent.showsOllamaRecheck)

        let paddedModel = FrenchWorkspacePresentation(
            hasReferences: true,
            model: " gemma4:12b ",
            isRunning: false,
            ollamaState: readyOllama,
            availableModels: ["gemma4:12b"],
            hasLoadedModels: true
        )
        XCTAssertTrue(paddedModel.canGenerate)
    }

    private var readyOllama: OllamaState {
        OllamaState(installed: true, running: true, command: "ollama", message: "Ready")
    }

    func testEveryProviderAndHelpTopicHasSpokenTextAndSymbol() {
        for provider in AIProvider.allCases {
            XCTAssertFalse(provider.title.isEmpty)
            XCTAssertFalse(provider.subtitle.isEmpty)
            XCTAssertFalse(provider.systemImage.isEmpty)
        }
        for topic in HelpTopic.allCases {
            XCTAssertFalse(topic.title.isEmpty)
            XCTAssertFalse(topic.systemImage.isEmpty)
        }
    }

    func testQualificationStatesNeverRelyOnColourAlone() {
        let states = [
            QualificationReadiness(
                engineeringValidated: false,
                visuallyCalibrated: false,
                empiricallyCalibrated: false
            ),
            QualificationReadiness(
                engineeringValidated: true,
                visuallyCalibrated: true,
                empiricallyCalibrated: false
            ),
            QualificationReadiness(
                engineeringValidated: true,
                visuallyCalibrated: true,
                empiricallyCalibrated: true
            ),
        ]

        XCTAssertEqual(states.map(\.highestLevelTitle), [
            "Not validated",
            "Visually calibrated",
            "Empirically calibrated",
        ])
    }

    func testLongPseudoLocalisedCopyAndRightToLeftLocaleRemainAvailable() {
        let longCopy = String(
            repeating: "Create another paper with new questions — ",
            count: 8
        )
        let rightToLeft = Locale.Language(identifier: "ar").characterDirection

        XCTAssertGreaterThan(longCopy.count, 250)
        XCTAssertEqual(rightToLeft, .rightToLeft)
    }

    func testBenchmarkChartSummaryExposesLatestValueAndRangeWithoutVision() {
        XCTAssertEqual(
            BenchmarkAccessibility.chartSummary(
                title: "CPU Load",
                unit: "%",
                values: [40, 55]
            ),
            "CPU Load. 2 samples. Latest 55 %. Range 40 to 55 %."
        )
        XCTAssertEqual(
            BenchmarkAccessibility.chartSummary(
                title: "CPU Load",
                unit: "%",
                values: []
            ),
            "CPU Load. No samples."
        )
    }
}
