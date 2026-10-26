import Foundation

struct FrenchAssessmentRequest {
    static let assessmentID = "fr-bac-general-nsi-written-2027"
    let referenceIndex: URL
    let output: URL
    let seed: Int
    let largePrint: Bool

    var arguments: [String] {
        var result = [
            "generate-assessment", "--assessment", Self.assessmentID,
            "--reference-index", referenceIndex.path, "--output", output.path,
            "--provider", "application-owned", "--seed", String(seed),
        ]
        if largePrint { result.append("--large-print") }
        return result
    }
}
