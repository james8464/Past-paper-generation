import Foundation

enum AppDefaults {
    static let ollamaModel = "qwen2.5:14b"
    static let openAIModel = "gpt-4.1"
    static let anthropicModel = "claude-sonnet-4-20250514"
    static let appleModel = "mlx-community/Llama-3.2-3B-Instruct-4bit"
    static let ollamaURL = "http://localhost:11434"
    static let benchmarkDurationSeconds = 30.0

    static func defaultOutputFolder() -> URL {
        let fileManager = FileManager.default
        let homeDownloads = fileManager.homeDirectoryForCurrentUser.appendingPathComponent("Downloads", isDirectory: true)

        if fileManager.fileExists(atPath: homeDownloads.path), !isSandboxDownloadsPath(homeDownloads.path) {
            return homeDownloads
        }

        if let downloads = fileManager.urls(for: .downloadsDirectory, in: .userDomainMask).first {
            return downloads
        }

        return fileManager.homeDirectoryForCurrentUser
    }

    static func isSandboxDownloadsPath(_ path: String) -> Bool {
        path.contains("/Library/Containers/") && path.contains("/Data/Downloads")
    }
}

enum AppStorageKey {
    static let aiProvider = "aiProvider"
    static let hostedAIConsentAccepted = "hostedAIConsentAccepted"
    static let ollamaModel = "ollamaModel"
    static let openAIModel = "openAIModel"
    static let anthropicModel = "anthropicModel"
    static let appleModel = "appleModel"
    static let notificationsEnabled = "notificationsEnabled"
    static let hasSeenWelcome = "hasSeenWelcome"
    static let outputFolderPath = "outputFolderPath"
    static let selectedBoardID = "selectedBoardID"
    static let selectedPaperID = "selectedPaperID"
}

enum SecretAccount {
    static let openAIAPIKey = "openai-api-key"
    static let anthropicAPIKey = "anthropic-api-key"
}

enum AppLinks {
    static let projectHelp = webURL("https://github.com/james8464/Past-paper-generation#examforge")
    static let privacyPolicy = webURL("https://github.com/james8464/Past-paper-generation#privacy")
    static let support = webURL("https://github.com/james8464/Past-paper-generation/issues")
    static let ollamaDownload = webURL("https://ollama.com/download")

    private static func webURL(_ value: String) -> URL {
        URL(string: value) ?? URL(string: "about:blank")!
    }
}
