import Foundation

/// A model-authored draft. The older catalogue request remains available for saved-package replay.
struct FrenchLLMAssessmentRequest {
    static let promptVersion = "fr-nsi-written-2027-v36-llm"
    static let printPolicy = "fr-nsi-v36-model-review-v1"
    let referenceIndex: URL
    let output: URL
    let seed: Int
    let largePrint: Bool
    let provider: AIProvider
    let model: String

    var arguments: [String] {
        var result = [
            "generate-assessment", "--assessment", FrenchAssessmentRequest.assessmentID,
            "--reference-index", referenceIndex.path, "--output", output.path,
            "--seed", String(seed), "--provider", provider.backendID,
            "--model", model, "--authoring-version", "v36",
        ]
        if largePrint { result.append("--large-print") }
        return result
    }

    static func validatePublication(at url: URL, configuration: GenerationConfiguration) throws {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let publication = try decoder.decode(Publication.self, from: Data(contentsOf: url))
        guard publication.schemaVersion == 1,
              publication.assessment == FrenchAssessmentRequest.assessmentID,
              publication.status == "unreviewed_draft",
              publication.generationOrigin == "model_authored", publication.modelUsed,
              publication.teacherReview == "not_run", publication.empiricalCalibration == "not_run",
              publication.identity.provider == configuration.provider,
              publication.identity.model == configuration.model,
              publication.identity.seed == configuration.seed,
              publication.identity.promptVersion == promptVersion,
              publication.identity.printPolicy == printPolicy else {
            throw CocoaError(.fileReadCorruptFile)
        }
    }

    static func validatePublication(artifacts: [GeneratedFile], configuration: GenerationConfiguration) throws {
        let required: Set<String> = ["assessment_package", "package_manifest", "question_paper", "mark_scheme"]
        guard artifacts.count == required.count,
              Set(artifacts.map(\.role)) == required,
              Set(artifacts.map { $0.url.standardizedFileURL }).count == required.count,
              let manifest = artifacts.first(where: { $0.role == "package_manifest" }) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        for artifact in artifacts {
            let attributes = try FileManager.default.attributesOfItem(atPath: artifact.url.path)
            guard attributes[.type] as? FileAttributeType == .typeRegular,
                  let size = attributes[.size] as? NSNumber, size.int64Value > 0 else {
                throw CocoaError(.fileReadCorruptFile)
            }
        }
        try validatePublication(at: manifest.url, configuration: configuration)
    }

    private struct Publication: Decodable {
        let schemaVersion: Int
        let assessment: String
        let status: String
        let generationOrigin: String
        let modelUsed: Bool
        let teacherReview: String
        let empiricalCalibration: String
        let identity: Identity

        struct Identity: Decodable {
            let provider: String
            let model: String
            let seed: Int
            let promptVersion: String
            let printPolicy: String
        }
    }
}
