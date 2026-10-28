import Foundation

/// Short status text belongs in the workspace; original messages stay in diagnostics.
enum GenerationPresentation {
    static func progress(_ message: String, language: String = "system") -> String {
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

    static func error(_ message: String, language: String = "system") -> String {
        if message.hasPrefix("Les quatre familles disponibles sont trop proches des sujets précédents.") {
            return localized("None of the four paper families is sufficiently different from your saved papers. No new paper was created.", language: language)
        }
        guard message.hasPrefix("AI could not produce a valid, second-pass reviewed item for question ") else {
            return message
        }
        return localized("This model couldn't create a paper that passed the quality checks. No new paper was published. Try another model. You can copy diagnostics from Tools.", language: language)
    }

    static func completion(_ message: String, language: String = "system") -> String {
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
