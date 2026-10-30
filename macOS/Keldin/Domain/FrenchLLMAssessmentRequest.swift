import CryptoKit
import Foundation

/// A model-authored draft. The older catalogue request remains available for saved-package replay.
struct FrenchLLMAssessmentRequest {
    static let promptVersion = "fr-nsi-written-2027-v36-llm"
    static let printPolicy = "fr-nsi-v36-model-review-v2"
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
            guard artifact.url.isFileURL else { throw CocoaError(.fileReadInvalidFileName) }
            let attributes = try FileManager.default.attributesOfItem(atPath: artifact.url.path)
            guard attributes[.type] as? FileAttributeType == .typeRegular,
                  let size = attributes[.size] as? NSNumber, size.int64Value > 0 else {
                throw CocoaError(.fileReadCorruptFile)
            }
        }
        try validatePublication(at: manifest.url, configuration: configuration)
        let manifestData = try Data(contentsOf: manifest.url)
        let decoder = JSONDecoder()
        let metadata = try decoder.decode(ArtifactManifest.self, from: manifestData)
        let recordedRoles = required.subtracting(["package_manifest"])
        guard Set(metadata.artifacts.keys) == recordedRoles,
              Set(metadata.artifacts.values.map(\.file)).count == recordedRoles.count else {
            throw CocoaError(.fileReadCorruptFile)
        }
        for artifact in artifacts where artifact.role != "package_manifest" {
            guard let record = metadata.artifacts[artifact.role],
                  !record.file.isEmpty, ![".", ".."].contains(record.file),
                  !record.file.contains("/"), !record.file.contains("\\"),
                  record.file == artifact.url.lastPathComponent,
                  record.sha256.count == 64,
                  record.sha256.allSatisfy({ "0123456789abcdef".contains($0) }) else {
                throw CocoaError(.fileReadCorruptFile)
            }
            let data = try Data(contentsOf: artifact.url)
            let hash = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
            guard hash == record.sha256 else { throw CocoaError(.fileReadCorruptFile) }
            if artifact.role == "assessment_package" {
                guard artifact.url.deletingLastPathComponent().standardizedFileURL == manifest.url.deletingLastPathComponent().standardizedFileURL,
                      let package = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let publication = try JSONSerialization.jsonObject(with: manifestData) as? [String: Any],
                      let packageIdentity = package["identity"] as? [String: Any],
                      let manifestIdentity = publication["identity"] as? [String: Any],
                      try JSONSerialization.data(withJSONObject: packageIdentity, options: [.sortedKeys]) == JSONSerialization.data(withJSONObject: manifestIdentity, options: [.sortedKeys]) else {
                    throw CocoaError(.fileReadCorruptFile)
                }
            }
        }
    }

    private struct ArtifactManifest: Decodable {
        let artifacts: [String: Artifact]
        struct Artifact: Decodable { let file: String; let sha256: String }
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
