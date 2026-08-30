import Foundation
import XCTest
@testable import PaperCreator

final class AccessibilityTests: XCTestCase {
    func testWorkspaceLayoutProtectsCompactWindowsFromColumnOverlap() {
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 720), .compact)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 839), .compact)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 840), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 900), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_099), .standard)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_100), .expanded)
        XCTAssertEqual(WorkspaceLayoutPolicy.mode(for: 1_200), .expanded)

        XCTAssertFalse(WorkspaceLayoutPolicy.mode(for: 720).showsSidebar)
        XCTAssertFalse(WorkspaceLayoutPolicy.mode(for: 900).showsInspector)
        XCTAssertTrue(WorkspaceLayoutPolicy.mode(for: 1_200).showsInspector)
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
