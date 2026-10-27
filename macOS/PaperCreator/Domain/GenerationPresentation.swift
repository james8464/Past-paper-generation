import Foundation

/// Short status text belongs in the workspace; original messages stay in diagnostics.
enum GenerationPresentation {
    static func progress(_ message: String) -> String {
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
        return String(localized: "Rechecking question \(number)")
    }

    static func error(_ message: String) -> String {
        guard message.hasPrefix("AI could not produce a valid, second-pass reviewed item for question ") else {
            return message
        }
        return String(localized: "This model couldn't create a paper that passed the quality checks. No new paper was published. Try another model. You can copy diagnostics from Tools.")
    }
}
