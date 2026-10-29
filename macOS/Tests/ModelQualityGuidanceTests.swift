import Foundation
import XCTest
@testable import Keldin

final class ModelQualityGuidanceTests: XCTestCase {
    func testModelEvidenceIsScopedToExactProviderAndModelNotMemoryOrParameterCount() {
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "mlx-community/Llama-3.2-3B-Instruct-4bit"), .answerChecksFailed)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "gemma4:12b"), .reviewIncomplete)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "qwen3.5:9b"), .nsiProbeFailed)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "qwen3.5:9b"), .unverified)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "qwen3.5:27b"), .unverified)
        for (provider, model) in [(AIProvider.ollama, "llama3.2:3b"), (.ollama, "qwen2.5:7b"), (.apple, "/private/model-cache"), (.apple, "other/Model-120B"), (.openAI, "future-model"), (.anthropic, "future-model")] {
            XCTAssertEqual(ModelQualityAdvice.forModel(provider: provider, model: model), .unverified)
        }
        XCTAssertEqual(InterfaceText.resolve(ModelQualityAdvice.unverified.title, language: "fr"), "Qualité des sujets non vérifiée")
        XCTAssertEqual(InterfaceText.resolve(ModelQualityAdvice.answerChecksFailed.title, language: "en"), "Known answer-check failure")
    }

    func testMissingReportDoesNotBecomeAnAllClear() {
        let summary = GenerationIssueSummary(report: nil)
        XCTAssertTrue(summary.issues.isEmpty)
        XCTAssertEqual(summary.notChecked.map(\.id), ["no-record"])
    }

    func testPreviewAndUncalibratedFieldsRemainVisibleWithoutInventingFailure() throws {
        let summary = GenerationIssueSummary(report: try report(preview: true))
        XCTAssertTrue(summary.issues.isEmpty)
        XCTAssertTrue(summary.warnings.map(\.id).contains("preview"))
        XCTAssertTrue(summary.notChecked.map(\.id).contains("preview-authoring"))
        XCTAssertTrue(summary.notChecked.map(\.id).contains("visual"))
        XCTAssertTrue(summary.notChecked.map(\.id).contains("empirical"))
        XCTAssertTrue(summary.notChecked.map(\.id).contains("engineering"))
    }

    func testExplicitReportFailuresAndGapsStaySeparateFromNotCheckedFields() throws {
        let summary = GenerationIssueSummary(report: try report(
            reference: ["passed": false, "failed_checks": ["q02 check failed", "q02 check failed"], "topic_evidence": ["gaps": ["Missing topic context", "Missing topic context"]]],
            novelty: ["passed": false, "within_paper_passed": false]
        ))
        XCTAssertEqual(Set(summary.issues.map(\.id)), ["reference-checks", "originality", "within-paper"])
        XCTAssertEqual(summary.failureDetails, ["q02 check failed"])
        XCTAssertEqual(summary.warningDetails, ["Missing topic context"])
        XCTAssertTrue(summary.notChecked.map(\.id).contains("empirical"))
    }

    private func report(preview: Bool = false, reference: [String: Any] = [:], novelty: [String: Any] = [:]) throws -> GenerationQualityReport {
        let payload: [String: Any] = [
            "request": ["preview_mode": preview],
            "evidence": [
                "assessment_validation": ["item_count": 1, "reference_demand": reference],
                "novelty_validation": novelty,
                "qualification_levels": ["engineering_validated": false, "visually_calibrated": false, "empirically_calibrated": false],
            ],
            "outputs": [:],
        ]
        let file = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinQualityGuidance-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: file) }
        try JSONSerialization.data(withJSONObject: payload).write(to: file)
        return try XCTUnwrap(GenerationQualityReport.load(from: file))
    }
}
