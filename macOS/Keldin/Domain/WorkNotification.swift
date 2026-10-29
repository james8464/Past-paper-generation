import Foundation

struct WorkNotificationContent: Equatable {
    let title: String
    let body: String
}

enum WorkNotification {
    case paperStarted(subject: String, paper: String)
    case paperReady(folder: String)
    case paperFailed(detail: String)
    case modelStarted(model: String)
    case modelReady(model: String)
    case modelFailed(detail: String)
    case mlxStarted
    case mlxReady
    case mlxFailed(detail: String)

    func content(language: String) -> WorkNotificationContent {
        func text(_ resource: LocalizedStringResource) -> String {
            InterfaceText.resolve(resource, language: language)
        }
        switch self {
        case let .paperStarted(subject, paper):
            return WorkNotificationContent(title: text("Creating your paper"), body: "\(subject) · \(paper)")
        case let .paperReady(folder):
            return WorkNotificationContent(title: text("Your paper is ready"), body: text("The paper and mark scheme are in \(folder)."))
        case let .paperFailed(detail):
            return WorkNotificationContent(title: text("Couldn’t create the paper"), body: detail)
        case let .modelStarted(model):
            return WorkNotificationContent(title: text("Downloading model"), body: text("Ollama is downloading \(model)."))
        case let .modelReady(model):
            return WorkNotificationContent(title: text("Model ready"), body: text("\(model) is available in Ollama."))
        case let .modelFailed(detail):
            return WorkNotificationContent(title: text("Couldn’t download the model"), body: detail)
        case .mlxStarted:
            return WorkNotificationContent(title: text("Setting up Apple MLX"), body: text("Keldin is preparing the selected local model."))
        case .mlxReady:
            return WorkNotificationContent(title: text("Apple MLX ready"), body: text("The selected model is ready for local generation."))
        case let .mlxFailed(detail):
            return WorkNotificationContent(title: text("Apple MLX setup needs attention"), body: detail)
        }
    }
}
