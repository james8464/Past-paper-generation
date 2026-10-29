// Build the backend arguments for a French assessment request.

import Foundation

struct FrenchAssessmentRequest {
    enum PracticePolicy { case strict, repeatPractice }
    static let assessmentID = "fr-bac-general-nsi-written-2027"
    static let modelID = "app-owned-v35"
    static let familyIDs = [
        "rank-sensors-routing", "expression-bookings-locks",
        "prefix-stock-delivery", "postfix-loans-scheduling",
        "directories-eligibility-channel",
    ]
    let referenceIndex: URL
    let output: URL
    let seed: Int
    let largePrint: Bool
    var excludedFamilies: [Int] = []

    static func savedFamilies(in records: [GenerationJobRecord]) throws -> [Int] {
        var families = Set<Int>()
        for record in records {
            let configuration = record.configuration
            guard [.completed, .missingArtifacts].contains(record.state),
                  !configuration.dryRun,
                  configuration.assessmentID == assessmentID,
                  configuration.provider == "application-owned" else { continue }
            let count: Int
            switch configuration.model {
            case "app-owned-v34": count = 4
            case modelID: count = 5
            default: continue
            }
            guard let seed = configuration.seed else { throw CocoaError(.fileReadCorruptFile) }
            families.insert((seed % count + count) % count)
        }
        return families.sorted()
    }

    var arguments: [String] {
        var result = [
            "generate-assessment", "--assessment", Self.assessmentID,
            "--reference-index", referenceIndex.path, "--output", output.path,
            "--provider", "application-owned", "--seed", String(seed),
            "--repeat-practice",
        ]
        if largePrint { result.append("--large-print") }
        for family in excludedFamilies { result += ["--exclude-family", String(family)] }
        return result
    }

    static func publishedSeed(from manifest: URL, expectedPolicy: PracticePolicy = .strict) throws -> Int {
        let data = try Data(contentsOf: manifest)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let publication = try decoder.decode(Publication.self, from: data)
        switch expectedPolicy {
        case .strict:
            guard publication.practicePolicy == nil, publication.crossHistoryComparison == nil else { throw CocoaError(.fileReadCorruptFile) }
        case .repeatPractice:
            guard publication.practicePolicy == "repeat-practice-v1", publication.crossHistoryComparison == "not_performed" else { throw CocoaError(.fileReadCorruptFile) }
        }
        guard publication.schemaVersion == 1,
              publication.assessment == assessmentID,
              publication.status == "unreviewed_draft",
              publication.generationOrigin == "application_owned",
              !publication.modelUsed,
              publication.teacherReview == "not_run",
              publication.empiricalCalibration == "not_run",
              publication.identity.provider == "application-owned",
              publication.identity.model == modelID,
              publication.identity.promptVersion == "fr-nsi-written-2027-v35",
              publication.identity.printPolicy == "fr-nsi-v35-internal-review-v1" else {
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
        let practicePolicy: String?
        let crossHistoryComparison: String?

        struct Identity: Decodable {
            let provider: String
            let model: String
            let seed: Int
            let promptVersion: String
            let printPolicy: String
        }
    }
}
