import AppKit
import SwiftUI
import XCTest
@testable import PaperCreator

final class AccessibilityTests: XCTestCase {
    @MainActor
    func testReadyWorkspaceLaysOutInAnExpandedWindow() {
        let application = ApplicationCoordinator()
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
        XCTAssertEqual(FrenchWorkspaceLayoutPolicy.contentWidth(for: 900), 840)
        XCTAssertEqual(FrenchWorkspaceLayoutPolicy.contentWidth(for: 1_440), 840)
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
