import Foundation

enum ModelQualityAdvice: Equatable {
    case answerChecksFailed, systemCalculationFailed, nsiProbeFailed, retiredModel, reviewIncomplete, unverified

    static func forModel(provider: AIProvider, model: String) -> Self {
        let model = model.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if provider == .appleIntelligence, model == "apple-system-on-device" {
            return .systemCalculationFailed
        }
        if provider == .apple, model == "mlx-community/llama-3.2-3b-instruct-4bit" {
            return .answerChecksFailed
        }
        if provider == .ollama, model == "gemma4:12b" { return .reviewIncomplete }
        if provider == .ollama, model == "qwen3.5:9b" { return .nsiProbeFailed }
        if provider == .anthropic, model == "claude-sonnet-4-20250514" { return .retiredModel }
        return .unverified
    }

    var title: LocalizedStringResource {
        switch self {
        case .answerChecksFailed, .systemCalculationFailed: "Known answer-check failure"
        case .nsiProbeFailed: "Wrong answers in an NSI probe"
        case .retiredModel: "This model has been retired"
        case .reviewIncomplete: "Paper-quality review incomplete"
        case .unverified: "Paper quality unverified"
        }
    }

    var detail: LocalizedStringResource {
        switch self {
        case .answerChecksFailed:
            "This Apple MLX model failed answer checks in an Accounting test. Memory fit does not establish paper quality."
        case .systemCalculationFailed:
            "This Apple on-device model failed an unaided accounting calculation test. Check generated answers and marks; some drafts may be refused."
        case .nsiProbeFailed:
            "A tested revision returned wrong answers in a small NSI reasoning probe with reasoning off. Full-paper quality remains unverified."
        case .retiredModel:
            "Anthropic retired claude-sonnet-4-20250514. Choose an active model in Settings. Your saved choice has not been changed."
        case .reviewIncomplete:
            "Paper-quality evidence for this model is incomplete. A memory-fit suggestion does not mean its papers passed."
        case .unverified:
            "Paper quality is unverified for this provider and model. Smaller models may fail multi-step questions; model size alone does not establish accuracy."
        }
    }
}

struct QualityCheckNotice: Identifiable {
    let id: String
    let message: LocalizedStringResource
}

struct GenerationIssueSummary {
    var issues: [QualityCheckNotice] = []
    var warnings: [QualityCheckNotice] = []
    var notChecked: [QualityCheckNotice] = []
    var failureDetails: [String] = []
    var warningDetails: [String] = []

    init(report: GenerationQualityReport?) {
        guard let report else {
            notChecked = [.init(id: "no-record", message: "No quality record is available for this result.")]
            return
        }
        failureDetails = Array(Set(report.referenceDemandFailedChecks ?? [])).sorted()
        warningDetails = Array(Set(report.evidenceGaps)).sorted()
        if !failureDetails.isEmpty || (report.referenceDemandPassed == false && report.referenceEvidenceState != "insufficient") {
            issues.append(.init(id: "reference-checks", message: "The record reports reference-demand checks that did not pass."))
        }
        if report.candidatePathEvidencePassed == false, report.pathEvidenceState != "insufficient" {
            issues.append(.init(id: "candidate-paths", message: "Candidate-path checks did not pass."))
        }
        if report.withinPaperPassed == false {
            issues.append(.init(id: "within-paper", message: "Duplicate checks within this paper did not pass."))
        }
        if report.savedMode == .live, report.noveltyPassed == false,
           report.crossGenerationPolicy != "repeat-practice-v1" {
            issues.append(.init(id: "originality", message: "Saved-paper similarity checks did not pass."))
        }
        if report.savedMode == .preview {
            warnings.append(.init(id: "preview", message: "This is a layout preview, not a finished paper."))
            notChecked.append(.init(id: "preview-authoring", message: "This preview does not evaluate AI question or marking quality."))
        } else if report.savedMode == .unknown {
            notChecked.append(.init(id: "mode", message: "The record does not identify whether this was a preview or live generation."))
        }
        if !warningDetails.isEmpty {
            warnings.append(.init(id: "coverage-gaps", message: "The record lists gaps in reference coverage."))
        }
        if report.referenceEvidenceState == "insufficient" || report.pathEvidenceState == "insufficient" {
            warnings.append(.init(id: "insufficient", message: "Reference evidence is insufficient to establish paper qualification."))
        }
        if report.crossGenerationPolicy == "repeat-practice-v1" {
            warnings.append(.init(id: "repeat-practice", message: "This result may overlap with earlier practice papers."))
        }
        if report.engineeringValidated != true {
            notChecked.append(.init(id: "engineering", message: "Engineering qualification is incomplete or not recorded."))
        }
        if report.visuallyCalibrated != true {
            notChecked.append(.init(id: "visual", message: "Visual calibration is incomplete or not recorded."))
        }
        if report.empiricallyCalibrated != true {
            notChecked.append(.init(id: "empirical", message: "Difficulty and timing have not been calibrated with learners."))
        }
        if report.referenceDemandPassed == nil {
            notChecked.append(.init(id: "reference-review", message: "Reference-demand review is not recorded."))
        }
        if report.candidatePathEvidencePassed == nil {
            notChecked.append(.init(id: "path-review", message: "Candidate-path evidence is not recorded."))
        }
        if report.noveltyPassed == nil {
            notChecked.append(.init(id: "originality-review", message: "Saved-paper similarity review is not recorded."))
        }
        switch report.authoringProvenance.kind {
        case .reviewedFixedOnly:
            warnings.append(.init(id: "fixed-items", message: "This result contains fixed items and does not establish AI authoring quality."))
        case .mixed:
            warnings.append(.init(id: "mixed-items", message: "This result combines fixed items and AI-authored items."))
        case .unreviewed, .unknown:
            notChecked.append(.init(id: "authoring", message: "Item authoring and review evidence is incomplete or not recorded."))
        case .aiAuthoredOnly:
            break
        }
    }
}
