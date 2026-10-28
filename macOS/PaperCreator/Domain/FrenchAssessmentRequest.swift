import Foundation

struct FrenchAssessmentRequest {
    static let assessmentID = "fr-bac-general-nsi-written-2027"
    static let modelID = "app-owned-v34"
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

    static func publishedSeed(from manifest: URL) throws -> Int {
        let data = try Data(contentsOf: manifest)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let publication = try decoder.decode(Publication.self, from: data)
        guard publication.schemaVersion == 1,
              publication.assessment == assessmentID,
              publication.status == "unreviewed_draft",
              publication.generationOrigin == "application_owned",
              !publication.modelUsed,
              publication.teacherReview == "not_run",
              publication.empiricalCalibration == "not_run",
              publication.identity.provider == "application-owned",
              publication.identity.model == modelID,
              publication.identity.promptVersion == "fr-nsi-written-2027-v34",
              publication.identity.printPolicy == "fr-nsi-v34-internal-review-v1" else {
            throw CocoaError(.fileReadCorruptFile)
        }
        return publication.identity.seed
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
