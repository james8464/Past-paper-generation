import Foundation
import XCTest
@testable import Keldin

final class ModelQualityGuidanceTests: XCTestCase {
    func testAppleSystemCalculationEvidenceDoesNotApplyToOtherModelsOrMLX() {
        let advice = ModelQualityAdvice.forModel(provider: .appleIntelligence, model: "apple-system-on-device")
        XCTAssertEqual(advice, .systemCalculationFailed)
        XCTAssertEqual(InterfaceText.resolve(advice.detail, language: "en"), "This Apple on-device model failed an unaided accounting calculation test. Check generated answers and marks; some drafts may be refused.")
        XCTAssertEqual(InterfaceText.resolve(advice.detail, language: "fr"), "Ce modèle Apple sur l’appareil a échoué à un calcul de comptabilité sans aide. Vérifiez les réponses et les barèmes générés ; certains brouillons peuvent être refusés.")
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .appleIntelligence, model: "future-system-model"), .unverified)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "apple-system-on-device"), .unverified)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "mlx-community/Llama-3.2-3B-Instruct-4bit"), .answerChecksFailed)
    }

    func testModelEvidenceIsScopedToExactProviderAndModelNotMemoryOrParameterCount() {
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "mlx-community/Llama-3.2-3B-Instruct-4bit"), .answerChecksFailed)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "gemma4:12b"), .accountingFalseAcceptance)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "qwen3.5:9b"), .nsiProbeFailed)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .apple, model: "qwen3.5:9b"), .unverified)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: "qwen3.5:27b"), .unverified)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .anthropic, model: "claude-sonnet-4-20250514"), .retiredModel)
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .openAI, model: "claude-sonnet-4-20250514"), .unverified)
        XCTAssertEqual(InterfaceText.resolve(ModelQualityAdvice.retiredModel.title, language: "fr"), "Ce modèle a été retiré")
        for (provider, model) in [(AIProvider.ollama, "llama3.2:3b"), (.ollama, "qwen2.5:7b"), (.apple, "/private/model-cache"), (.apple, "other/Model-120B"), (.openAI, "future-model"), (.anthropic, "future-model")] {
            XCTAssertEqual(ModelQualityAdvice.forModel(provider: provider, model: model), .unverified)
        }
        XCTAssertEqual(InterfaceText.resolve(ModelQualityAdvice.unverified.title, language: "fr"), "Qualité des sujets non vérifiée")
        XCTAssertEqual(InterfaceText.resolve(ModelQualityAdvice.answerChecksFailed.title, language: "en"), "Known answer-check failure")
    }

    func testGemmaAccountingFalseAcceptanceEvidenceIsBoundedAndLocalized() {
        let advice = ModelQualityAdvice.forModel(provider: .ollama, model: "gemma4:12b")
        XCTAssertEqual(advice, .accountingFalseAcceptance)
        XCTAssertEqual(InterfaceText.resolve(advice.title, language: "en"), "Known issue in an Accounting test")
        XCTAssertEqual(InterfaceText.resolve(advice.detail, language: "en"), "One tested revision produced an ambiguous Accounting question with an unsupported answer key. Automated checks accepted it.")
        XCTAssertEqual(InterfaceText.resolve(advice.title, language: "fr"), "Problème constaté lors d’un test de comptabilité")
        XCTAssertEqual(InterfaceText.resolve(advice.detail, language: "fr"), "Une version testée a produit une question de comptabilité ambiguë, avec une réponse attendue non justifiée par l’énoncé. Les contrôles automatiques l’ont acceptée.")
        XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: " Gemma4:12B \n"), advice)
        for provider in [AIProvider.apple, .appleIntelligence, .openAI, .anthropic, .deepSeek] {
            XCTAssertEqual(ModelQualityAdvice.forModel(provider: provider, model: "gemma4:12b"), .unverified)
        }
        for model in ["gemma4:27b", "gemma3:12b", "gemma4:12b-q4_K_M", "library/gemma4:12b"] {
            XCTAssertEqual(ModelQualityAdvice.forModel(provider: .ollama, model: model), .unverified)
        }
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
