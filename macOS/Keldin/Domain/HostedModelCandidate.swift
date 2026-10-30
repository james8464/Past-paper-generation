import Foundation

/// Vendor catalogue choices, not evidence that a generated paper is correct.
struct HostedModelCandidate: Identifiable {
    let model: String
    let role: LocalizedStringResource
    var id: String { model }

    static func forProvider(_ provider: AIProvider) -> [Self] {
        switch provider {
        case .openAI:
            [Self(model: AppDefaults.openAIModel, role: "Balanced candidate"),
             Self(model: "gpt-6-astra", role: "Higher-capability candidate")]
        case .anthropic:
            [Self(model: AppDefaults.anthropicModel, role: "Balanced candidate"),
             Self(model: "claude-opus-5-5", role: "Higher-capability candidate")]
        case .deepSeek:
            [Self(model: AppDefaults.deepSeekModel, role: "Lower-cost candidate"),
             Self(model: "deepseek-v4-pro", role: "Pro candidate, not yet qualified")]
        case .ollama, .apple: []
        }
    }
}
