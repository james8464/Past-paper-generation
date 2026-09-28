import Foundation

struct FrenchAssessmentRequest {
    static let assessmentID = "fr-bac-general-nsi-written-2027"
    let referenceIndex: URL
    let output: URL
    let model: String
    let seed: Int
    let largePrint: Bool

    var arguments: [String] {
        var result = [
            "generate-assessment", "--assessment", Self.assessmentID,
            "--reference-index", referenceIndex.path, "--output", output.path,
            "--model", model, "--provider", "ollama", "--seed", String(seed),
            "--ollama-url", "http://127.0.0.1:11434",
        ]
        if largePrint { result.append("--large-print") }
        return result
    }
}
