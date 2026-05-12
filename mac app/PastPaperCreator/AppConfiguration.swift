import Foundation

enum AppDefaults {
    static let ollamaModel = "qwen2.5:14b"
    static let openAIModel = "gpt-4.1"
    static let anthropicModel = "claude-sonnet-4-20250514"
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
    static let ollamaModel = "ollamaModel"
    static let openAIModel = "openAIModel"
    static let anthropicModel = "anthropicModel"
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
    static let projectHelp = webURL("https://github.com/james8464/Past-paper-generation#past-paper-creation")
    static let privacyPolicy = webURL("https://github.com/james8464/Past-paper-generation#privacy")
    static let support = webURL("https://github.com/james8464/Past-paper-generation/issues")
    static let ollamaDownload = webURL("https://ollama.com/download")

    private static func webURL(_ value: String) -> URL {
        guard let url = URL(string: value) else {
            preconditionFailure("Invalid app link: \(value)")
        }
        return url
    }
}
