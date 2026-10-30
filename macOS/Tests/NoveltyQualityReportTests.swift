import Foundation
import XCTest
@testable import Keldin

final class NoveltyQualityReportTests: XCTestCase {
    func testSkippedHistoryRemainsUnknownInQualityPresentation() throws {
        for policy in ["strict-cross-generation-v1", "repeat-practice-v1"] {
            let manifest = """
            {"request":{"preview_mode":false},"evidence":{"assessment_validation":{"item_count":1},"novelty_validation":{"passed":null,"cross_generation_policy":"\(policy)","within_paper_passed":true,"historical_overlap":false,"history_complete":false,"skipped_history_packages":1}},"outputs":{}}
            """
            let url = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension("json")
            defer { try? FileManager.default.removeItem(at: url) }
            try Data(manifest.utf8).write(to: url)
            let report = try XCTUnwrap(GenerationQualityReport.load(from: url))
            XCTAssertNil(report.noveltyPassed)
            XCTAssertEqual(GenerationQualityPolicy.presentation(for: report).originalityState, .unknown)
            XCTAssertTrue(GenerationIssueSummary(report: report).notChecked.contains { $0.id == "originality-review" })
        }
    }
}
