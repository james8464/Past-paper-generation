import Foundation

enum FrenchReviewDecision: String, CaseIterable, Identifiable {
    case approved
    case revise
    case rejected

    var id: String { rawValue }

    var localizationKey: String {
        switch self {
        case .approved: "Approved for classroom practice"
        case .revise: "Revisions required"
        case .rejected: "Rejected"
        }
    }
}

enum FrenchReviewRubric {
    private static let localizationKeys = [
        "correctness": "Correctness",
        "curriculum": "Curriculum alignment",
        "language": "Quality of French",
        "difficulty": "Difficulty",
        "timing": "Timing",
        "marking": "Marking guidance",
        "layout": "Layout",
        "originality": "Originality",
    ]

    static func localizationKey(for key: String) -> String {
        localizationKeys[key] ?? key
    }
}

struct FrenchReviewRequest {
    static let rubricKeys = [
        "correctness", "curriculum", "language", "difficulty",
        "timing", "marking", "layout", "originality",
    ]

    let manifest: URL
    let reviewer: String
    let decision: FrenchReviewDecision
    let scores: [String: Int]
    let notes: String

    var arguments: [String] {
        let data = try? JSONSerialization.data(withJSONObject: scores, options: [.sortedKeys])
        let scoresJSON = data.flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
        return [
            "review-french-assessment",
            "--manifest", manifest.path,
            "--reviewer", reviewer,
            "--decision", decision.rawValue,
            "--scores-json", scoresJSON,
            "--notes", notes,
        ]
    }

    var isComplete: Bool {
        !reviewer.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !notes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && Set(scores.keys) == Set(Self.rubricKeys)
            && scores.values.allSatisfy { 1 ... 4 ~= $0 }
    }
}
