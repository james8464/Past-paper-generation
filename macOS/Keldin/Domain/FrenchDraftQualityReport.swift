import Foundation

/// Describes the saved evidence, not whether the printed answers are correct.
struct FrenchDraftQualityReport: Equatable {
    struct Finding: Equatable, Identifiable {
        let exerciseID: String
        let questionID: String
        let detail: String
        var id: String { "\(exerciseID)/\(questionID)/\(detail)" }

        var locationResource: LocalizedStringResource {
            if questionID == "exercise" { return "Exercise \(exerciseID)" }
            return "Exercise \(exerciseID), question \(questionID)"
        }
    }

    let questionCount: Int
    let modelReviewedQuestions: Int
    let executableContracts: Int
    let issues: [Finding]
    let warnings: [Finding]
    let notChecked: [Finding]

    static func load(from url: URL) -> Self? {
        guard let data = try? Data(contentsOf: url),
              let package = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let identity = package["identity"] as? [String: Any],
              identity["prompt_version"] as? String == FrenchLLMAssessmentRequest.promptVersion,
              package["generation_origin"] as? String == "model_authored",
              package["model_used"] as? Bool == true,
              let exercises = package["exercises"] as? [[String: Any]] else { return nil }
        let checks = package["checks"] as? [[String: Any]] ?? []
        let reviews = package["reviews"] as? [[String: Any]] ?? []
        var notChecked: [Finding] = []
        var issues: [Finding] = []
        var expected = Set<String>()
        for exercise in exercises {
            guard let exerciseID = exercise["id"] as? String,
                  let questions = exercise["questions"] as? [[String: Any]] else { return nil }
            for question in questions {
                guard let questionID = question["id"] as? String else { return nil }
                expected.insert("\(exerciseID)/\(questionID)")
            }
        }
        var checked = Set<String>()
        var contracts = Set<String>()
        for check in checks {
            guard let exerciseID = check["exercise_id"] as? String,
                  let questionID = check["question_id"] as? String else { continue }
            let key = "\(exerciseID)/\(questionID)"
            guard expected.contains(key), checked.insert(key).inserted else { continue }
            let finding = Finding(exerciseID: exerciseID, questionID: questionID,
                                  detail: check["reason"] as? String ?? check["state"] as? String ?? "")
            if check["passed"] as? Bool == false { issues.append(finding) }
            else if check["passed"] as? Bool == true, check["state"] as? String == "passed",
                    ["sql", "python_trace", "shortest_path"].contains(check["kind"] as? String ?? "") {
                contracts.insert(key)
            } else { notChecked.append(finding) }
        }
        for key in expected.subtracting(checked).sorted() {
            let parts = key.split(separator: "/", maxSplits: 1).map(String.init)
            notChecked.append(Finding(exerciseID: parts[0], questionID: parts[1], detail: ""))
        }
        var reviewed = Set<String>()
        for (exercise, review) in zip(exercises, reviews) {
            guard review["status"] as? String == "model_reviewed_not_proven",
                  let exerciseID = exercise["id"] as? String,
                  let questions = review["question_review"] as? [String: [String: Any]] else { continue }
            for (questionID, questionReview) in questions {
                let key = "\(exerciseID)/\(questionID)"
                guard expected.contains(key) else { continue }
                reviewed.insert(key)
                for field in ["correct", "answer_complete", "rubric_consistent", "curriculum_aligned", "french", "self_contained"]
                    where questionReview[field] as? Bool == false {
                    issues.append(Finding(exerciseID: exerciseID, questionID: questionID, detail: field))
                }
                for detail in questionReview["issues"] as? [String] ?? [] {
                    issues.append(Finding(exerciseID: exerciseID, questionID: questionID, detail: detail))
                }
            }
        }
        let warnings = (package["warnings"] as? [[String: Any]] ?? []).compactMap { warning -> Finding? in
            guard let exerciseID = warning["exercise_id"] as? String,
                  let questionID = warning["question_id"] as? String else { return nil }
            return Finding(exerciseID: exerciseID, questionID: questionID, detail: warning["reason"] as? String ?? "")
        }
        return Self(questionCount: expected.count, modelReviewedQuestions: reviewed.count,
                    executableContracts: contracts.count, issues: unique(issues), warnings: unique(warnings),
                    notChecked: unique(notChecked))
    }

    private static func unique(_ findings: [Finding]) -> [Finding] {
        var seen = Set<String>()
        return findings.filter { seen.insert($0.id).inserted }.sorted { $0.id < $1.id }
    }
}
