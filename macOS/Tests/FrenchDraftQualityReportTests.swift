import Foundation
import XCTest
@testable import Keldin

final class FrenchDraftQualityReportTests: XCTestCase {
    func testHumanAndMissingChecksRemainNotCheckedDespiteModelReview() throws {
        let report = try load(checks: [
            ["exercise_id": "1", "question_id": "1a", "kind": "human", "state": "not_checked", "reason": "No executable proof"],
        ], warnings: [["exercise_id": "1", "question_id": "1a", "reason": "No executable proof"]])
        XCTAssertEqual(report.questionCount, 2)
        XCTAssertEqual(report.modelReviewedQuestions, 2)
        XCTAssertEqual(report.executableContracts, 0)
        XCTAssertEqual(report.notChecked.map(\.questionID), ["1a", "1b"])
        XCTAssertEqual(report.warnings.first?.detail, "No executable proof")
        XCTAssertTrue(report.issues.isEmpty)
    }

    func testOnlyKnownPassingContractsCountAndExplicitFailuresStayVisible() throws {
        let report = try load(checks: [
            ["exercise_id": "1", "question_id": "1a", "kind": "sql", "state": "passed", "passed": true],
            ["exercise_id": "1", "question_id": "1b", "kind": "python_trace", "state": "failed", "passed": false, "reason": "Mismatch"],
        ])
        XCTAssertEqual(report.executableContracts, 1)
        XCTAssertEqual(report.issues.first?.detail, "Mismatch")
        XCTAssertTrue(report.notChecked.isEmpty)
        XCTAssertEqual(InterfaceText.resolve("Model review is not proof. Executable contract checks do not certify the printed answers.", language: "fr"),
            "L’avis d’un modèle n’est pas une preuve. Les contrôles de contrats exécutables ne certifient pas les réponses imprimées.")
    }

    private func load(checks: [[String: Any]], warnings: [[String: Any]] = []) throws -> FrenchDraftQualityReport {
        let payload: [String: Any] = [
            "identity": ["prompt_version": FrenchLLMAssessmentRequest.promptVersion],
            "generation_origin": "model_authored", "model_used": true,
            "exercises": [["id": "1", "questions": [["id": "1a"], ["id": "1b"]]]],
            "reviews": [["status": "model_reviewed_not_proven", "question_review": ["1a": ["issues": []], "1b": ["issues": []]]]],
            "checks": checks, "warnings": warnings,
        ]
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("FrenchDraftReview-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: url) }
        try JSONSerialization.data(withJSONObject: payload).write(to: url)
        return try XCTUnwrap(FrenchDraftQualityReport.load(from: url))
    }
}
