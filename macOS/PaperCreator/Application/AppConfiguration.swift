import Foundation

enum AppDefaults {
    static let ollamaModel = OllamaModelGuide.currentRecommendation.model
    static let openAIModel = "gpt-4.1"
    static let anthropicModel = "claude-sonnet-4-20250514"
    static let appleModel = "mlx-community/Llama-3.2-3B-Instruct-4bit"
    static let ollamaURL = "http://localhost:11434"
    static let benchmarkDurationSeconds = 30.0

    static func defaultOutputFolder() -> URL {
        let fileManager = FileManager.default
        if DistributionMode.current == .appStore {
            return appStoreWorkingFolder()
        }

        let homeDownloads = fileManager.homeDirectoryForCurrentUser.appendingPathComponent("Downloads", isDirectory: true)

        if fileManager.fileExists(atPath: homeDownloads.path), !isSandboxDownloadsPath(homeDownloads.path) {
            return homeDownloads
        }

        if let downloads = fileManager.urls(for: .downloadsDirectory, in: .userDomainMask).first {
            return downloads
        }

        return fileManager.homeDirectoryForCurrentUser
    }

    static func appStoreWorkingFolder() -> URL {
        let fileManager = FileManager.default
        let home = fileManager.homeDirectoryForCurrentUser
        if home.path.contains("/Library/Containers/"), home.path.hasSuffix("/Data") {
            return home
                .appendingPathComponent("Library/Application Support", isDirectory: true)
                .appendingPathComponent("Paper creator/Generated papers", isDirectory: true)
        }
        let bundleID = Bundle.main.bundleIdentifier ?? "com.jamesdurup.PaperCreator"
        return home
            .appendingPathComponent("Library/Containers", isDirectory: true)
            .appendingPathComponent(bundleID, isDirectory: true)
            .appendingPathComponent("Data/Library/Application Support", isDirectory: true)
            .appendingPathComponent("Paper creator/Generated papers", isDirectory: true)
    }

    static func mlxCacheFolder() -> URL {
        let fileManager = FileManager.default
        let applicationSupport = fileManager.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first ?? fileManager.homeDirectoryForCurrentUser
        return applicationSupport
            .appendingPathComponent("Paper creator", isDirectory: true)
            .appendingPathComponent("MLX Models", isDirectory: true)
    }

    static func jobHistoryFolder() -> URL {
        let fileManager = FileManager.default
        let applicationSupport = fileManager.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first ?? fileManager.homeDirectoryForCurrentUser
        return applicationSupport
            .appendingPathComponent("Paper creator", isDirectory: true)
            .appendingPathComponent("Job History", isDirectory: true)
    }

    static func isSandboxDownloadsPath(_ path: String) -> Bool {
        path.contains("/Library/Containers/") && path.contains("/Data/Downloads")
    }

    static func displayPath(_ url: URL) -> String {
        let path = url.path
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        if path == home {
            return "~"
        }
        if path.hasPrefix(home + "/") {
            return "~" + path.dropFirst(home.count)
        }
        return path
    }
}

enum AppStorageKey {
    static let aiProvider = "aiProvider"
    static let hostedAIConsentAccepted = "hostedAIConsentAccepted"
    static let ollamaModel = "ollamaModel"
    static let openAIModel = "openAIModel"
    static let anthropicModel = "anthropicModel"
    static let appleModel = "appleModel"
    static let preparedMLXModels = "preparedMLXModels"
    static let dryRun = "dryRun"
    static let notificationsEnabled = "notificationsEnabled"
    static let hasSeenWelcome = "hasSeenWelcome"
    static let outputFolderPath = "outputFolderPath"
    static let outputFolderBookmark = "outputFolderBookmark"
    static let recentDocuments = "recentDocuments"
    static let expandedSubjectIDs = "expandedSubjectIDs"
    static let settingsPane = "settingsPane"
    static let selectedBoardID = "selectedBoardID"
    static let selectedPaperID = "selectedPaperID"
    static let qualityInspectorVisible = "qualityInspectorVisible"
    static let favoriteBoardIDs = "favoriteBoardIDs"
    static let recentConfigurationIDs = "recentConfigurationIDs"
    static let historyRetentionLimit = "historyRetentionLimit"
}

enum SecretAccount {
    static let openAIAPIKey = "openai-api-key"
    static let anthropicAPIKey = "anthropic-api-key"
}

enum AppLinks {
    static let projectHelp = webURL("https://github.com/james8464/Past-paper-generation")
    static let privacyPolicy = webURL("https://github.com/james8464/Past-paper-generation#privacy")
    static let support = webURL("https://github.com/james8464/Past-paper-generation/issues")
    static let ollamaDownload = webURL("https://ollama.com/download")
    static let gemmaModel = webURL("https://ollama.com/library/gemma4/tags")
    static let ollamaStructuredOutputs = webURL("https://docs.ollama.com/capabilities/structured-outputs")

    private static func webURL(_ value: String) -> URL {
        URL(string: value) ?? URL(string: "about:blank")!
    }
}
