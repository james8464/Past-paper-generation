import Foundation

/// Short status text belongs in the workspace; original messages stay in diagnostics.
enum GenerationPresentation {
    static func estimatedTime(_ estimate: GenerationEstimate, locale: Locale) -> String {
        let resource: LocalizedStringResource
        if estimate.remainingSeconds <= 0 {
            resource = "Taking longer than estimated"
        } else if estimate.lastUpdatedAt != nil, estimate.remainingSeconds < 5,
                  (estimate.lastObservedProgress ?? 0) < 0.9 {
            resource = "Updating time estimate…"
        } else {
            resource = "Estimated time left: \(estimate.remainingText)"
        }
        return String(localized: InterfaceText.localizedResource(resource, locale: locale))
    }

    static func progress(_ message: String, language: String = "system") -> String {
        switch message {
        case "Préparation de l'extrait public d'Occitanie", "Préparation de l’extrait public d’Occitanie":
            return localized("Preparing the Occitanie case study", language: language)
        case "Création de l'activité annulée", "Création de l’activité annulée":
            return localized("Occitanie case study cancelled.", language: language)
        case "Apple MLX is decoding two tasks together.":
            return localized("Apple MLX is working on two tasks.", language: language)
        case "Apple MLX is using serial decoding for this model or prompt pair.":
            return localized("Apple MLX is working on one task at a time for this model or these prompts.", language: language)
        default:
            break
        }
        if let range = message.range(of: #"^Accepted [0-9]+ of [0-9]+ AI (items|questions)$"#, options: .regularExpression),
           range == (message.startIndex..<message.endIndex) {
            let words = message.split(separator: " ")
            if let completed = Int(words[1]), let total = Int(words[3]),
               total > 0, completed <= total {
                return words[5] == "questions"
                    ? localized("Questions checked: \(completed) of \(total)", language: language)
                    : localized("Items checked: \(completed) of \(total)", language: language)
            }
        }
        if message == "Construction des exercices vérifiés, sans appel à un modèle." {
            return localized("Preparing the practice paper.", language: language)
        }
        for prefix in ["Calibrating difficulty ", "Checking reference demand "] where message.hasPrefix(prefix) {
            let counts = message.dropFirst(prefix.count)
                .prefix(while: { $0 != ":" }).split(separator: "/")
            guard counts.count == 2, let index = Int(counts[0]), let total = Int(counts[1]),
                  1 <= index, index <= total else { return message }
            return localized("Reviewing question \(index) of \(total)", language: language)
        }
        let prefix = "Refining AI item "
        let separator = " after an automated quality check:"
        guard message.hasPrefix(prefix),
              let end = message.range(of: separator),
              end.lowerBound >= message.index(message.startIndex, offsetBy: prefix.count) else {
            return message
        }
        let number = String(message[message.index(message.startIndex, offsetBy: prefix.count)..<end.lowerBound])
        guard number.range(of: #"^[0-9][0-9A-Za-z().]{0,23}$"#, options: .regularExpression) != nil else {
            return message
        }
        return localized("Rechecking question \(number)", language: language)
    }

    static func error(_ message: String, code: String? = nil, language: String = "system") -> String {
        if message.hasPrefix("Les cinq familles disponibles sont trop proches des sujets précédents.") {
            return localized("None of the five paper families is sufficiently different from your saved papers. No new paper was created.", language: language)
        }
        if message.hasPrefix("Les quatre familles disponibles sont trop proches des sujets précédents.") {
            return localized("None of the four paper families is sufficiently different from your saved papers. No new paper was created.", language: language)
        }
        guard isGenerationQualityFailure(message, code: code) else {
            return message
        }
        return localized("The model's work did not pass the paper quality checks. Try again or choose a stronger model in Settings. You can copy diagnostics from Tools.", language: language)
    }

    private static func isGenerationQualityFailure(_ message: String, code: String?) -> Bool {
        guard code == "generation_failed" else { return false }
        // Only the actual failure line classifies the error, never a path or
        // diagnostic body that happens to mention an assessment check.
        let line = String(message.prefix(while: { $0 != "\n" && $0 != "\r" }))
        let identifier = #"(?:question |question-|verified contract )?[0-9][0-9A-Za-z()./_-]{0,63}"#
        let failures = #"(?:failed independent solution reconciliation:|failed reference-demand review:|failed second-pass assessment review:|failed assessment review:|independent answer disagrees with the keyed option(?:$|:))"#
        return line.range(of: "^\(identifier) \(failures)", options: .regularExpression) != nil
            || line.range(of: #"^AI could not produce a valid, second-pass reviewed item for question [0-9][0-9A-Za-z()./_-]{0,63}:"#, options: .regularExpression) != nil
    }

    static func completion(_ message: String, language: String = "system") -> String {
        if [
            "Activité Occitanie créée. Document indépendant, sans note d'examen.",
            "Activité Occitanie créée. Document indépendant, sans note d’examen.",
        ].contains(message) {
            return localized("Occitanie case study created. Separate activity, without an exam mark.", language: language)
        }
        guard message == "Sujet d'entraînement créé. Barème indicatif, difficulté et durée non calibrées." else {
            return message
        }
        return localized("Practice paper created. Marking guidance is indicative; difficulty and timing are uncalibrated.", language: language)
    }

    private static func localized(_ resource: LocalizedStringResource, language: String) -> String {
        var resource = resource
        if language != "system" {
            resource.locale = Locale(identifier: language)
        }
        return String(localized: resource)
    }
}
