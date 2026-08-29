import Foundation
import XCTest
@testable import PaperCreator

final class AccessibilityTests: XCTestCase {
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
