import AppKit
import Combine
import Foundation
import UserNotifications

@MainActor
final class AppViewModel: ObservableObject {
    @Published var selectedBoardID = ExamCatalog.defaultBoard.id
    @Published var selectedPaperID = ExamCatalog.defaultBoard.papers[0].id
    @Published var selectedModel = "qwen2.5:14b"
    @Published var aiProvider: AIProvider = .ollama
    @Published var ollamaURL = "http://localhost:11434"
    @Published var outputFolder = AppViewModel.defaultOutputFolder()
    @Published var dryRun = false
    @Published var isRunning = false
    @Published var status = "Ready"
    @Published var generationProgress: Double?
    @Published var progressEntries: [ProgressEntry] = []
    @Published var generatedFiles: [GeneratedFile] = []
    @Published var previewPages: [GeneratedPage] = []
    @Published var isRefreshingOllama = false
    @Published var ollamaState = OllamaState()
    @Published var availableModels: [String] = []
    @Published var modelToPull = "qwen2.5:14b"
    @Published var openAIModel = "gpt-4.1"
    @Published var anthropicModel = "claude-sonnet-4-20250514"
    @Published var openAIAPIKey = ""
    @Published var anthropicAPIKey = ""
    @Published var showPullConfirmation = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showWelcome = false
    @Published var notificationsEnabled = true

    let distributionMode = DistributionMode.current

    private let backend = BackendClient()
    private let defaults = UserDefaults.standard
    private var runningProcess: Process?
    private var didReceiveBackendError = false
    private var didCancelRun = false
    private var activeOperation = RunningOperation.none

    var selectedBoard: ExamBoardOption {
        ExamCatalog.board(id: selectedBoardID) ?? ExamCatalog.defaultBoard
    }

    var selectedPaper: PaperOption {
        selectedBoard.papers.first { $0.id == selectedPaperID } ?? selectedBoard.papers[0]
    }

    var selectedPaperTitle: String {
        selectedPaper.title
    }

    var selectedPaperDetail: String {
        selectedPaper.detail
    }

    var canGenerate: Bool {
        generationBlocker == nil
    }

    var generationBlocker: String? {
        if isRunning { return "Generation is already running." }
        if !selectedBoard.isReady { return "\(selectedBoard.subjectTitle) \(selectedBoard.title) is coming soon." }
        if dryRun { return nil }
        if activeModelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return "Choose a model before generating."
        }
        switch aiProvider {
        case .ollama:
            if ollamaState.message == "Not checked" { return "Check Ollama before generating." }
            if !ollamaState.installed { return "Ollama is not installed." }
            if !ollamaState.running { return "Ollama is not running." }
            return nil
        case .openAI:
            return openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "Enter an OpenAI API key in Settings." : nil
        case .anthropic:
            return anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "Enter an Anthropic API key in Settings." : nil
        }
    }

    var activeModelName: String {
        switch aiProvider {
        case .ollama: selectedModel
        case .openAI: openAIModel
        case .anthropic: anthropicModel
        }
    }

    init() {
        let ollamaModel = defaults.string(forKey: "ollamaModel") ?? "qwen2.5:14b"
        aiProvider = AIProvider(rawValue: defaults.string(forKey: "aiProvider") ?? "") ?? .ollama
        selectedModel = ollamaModel
        modelToPull = ollamaModel
        openAIModel = defaults.string(forKey: "openAIModel") ?? "gpt-4.1"
        anthropicModel = defaults.string(forKey: "anthropicModel") ?? "claude-sonnet-4-20250514"
        openAIAPIKey = SecretStore.read("openai-api-key")
        anthropicAPIKey = SecretStore.read("anthropic-api-key")
        if defaults.object(forKey: "notificationsEnabled") != nil {
            notificationsEnabled = defaults.bool(forKey: "notificationsEnabled")
        }
        showWelcome = !defaults.bool(forKey: "hasSeenWelcome")
        if let savedOutput = defaults.string(forKey: "outputFolderPath"), !savedOutput.isEmpty {
            if Self.isSandboxDownloadsPath(savedOutput) {
                defaults.set(outputFolder.path, forKey: "outputFolderPath")
            } else {
                outputFolder = URL(fileURLWithPath: savedOutput)
            }
        }
        selectedBoardID = defaults.string(forKey: "selectedBoardID") ?? ExamCatalog.defaultBoard.id
        selectedPaperID = defaults.string(forKey: "selectedPaperID") ?? selectedBoard.papers[0].id
    }

    private static func defaultOutputFolder() -> URL {
        let fallback = URL(fileURLWithPath: "/Users/\(NSUserName())/Downloads")
        if FileManager.default.fileExists(atPath: fallback.path) {
            return fallback
        }
        if let realHome = NSHomeDirectoryForUser(NSUserName()) {
            let downloads = URL(fileURLWithPath: realHome).appendingPathComponent("Downloads")
            if FileManager.default.fileExists(atPath: downloads.path), !isSandboxDownloadsPath(downloads.path) {
                return downloads
            }
        }
        return FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first ?? fallback
    }

    private static func isSandboxDownloadsPath(_ path: String) -> Bool {
        path.contains("/Library/Containers/") && path.contains("/Data/Downloads")
    }

    func refreshOllama() {
        guard !isRunning, !isRefreshingOllama else { return }
        isRefreshingOllama = true
        status = "Checking Ollama"
        Task {
            defer { isRefreshingOllama = false }
            do {
                let statusEvents = try await backend.collect(arguments: ["ollama-status"])
                statusEvents.forEach(apply)
                let modelEvents = try await backend.collect(arguments: ["list-models"])
                modelEvents.forEach(apply)
            } catch {
                setError(error.localizedDescription)
            }
        }
    }

    func chooseOutputFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.directoryURL = outputFolder

        if panel.runModal() == .OK, let url = panel.url {
            outputFolder = url
            defaults.set(url.path, forKey: "outputFolderPath")
        }
    }

    func openOutputFolder() {
        NSWorkspace.shared.open(outputFolder)
    }

    func selectBoard(_ board: ExamBoardOption) {
        guard selectedBoardID != board.id || !board.papers.contains(where: { $0.id == selectedPaperID }) else {
            return
        }
        selectedBoardID = board.id
        selectedPaperID = board.papers[0].id
        defaults.set(board.id, forKey: "selectedBoardID")
        defaults.set(selectedPaperID, forKey: "selectedPaperID")
        generatedFiles.removeAll()
        previewPages.removeAll()
        progressEntries.removeAll()
        status = board.isReady ? "Ready" : "Coming Soon"
    }

    func selectPaperID(_ paperID: String) {
        guard selectedPaperID != paperID else {
            defaults.set(paperID, forKey: "selectedPaperID")
            return
        }
        selectedPaperID = paperID
        defaults.set(paperID, forKey: "selectedPaperID")
    }

    func generate() {
        guard canGenerate else { return }
        guard let backendSubject = selectedBoard.backendSubject else {
            setError("This exam board is coming soon.")
            return
        }
        persistSettings()

        generatedFiles.removeAll()
        previewPages.removeAll()
        progressEntries.removeAll()
        didReceiveBackendError = false
        didCancelRun = false
        isRunning = true
        status = "Starting"
        generationProgress = 0.02
        activeOperation = .generation

        var arguments = [
            "generate",
            "--subject",
            backendSubject,
            "--paper",
            selectedPaper.id,
            "--output",
            outputFolder.path,
            "--provider",
            aiProvider.backendID,
            "--model",
            activeModelName,
            "--ollama-url",
            ollamaURL,
        ]

        switch aiProvider {
        case .ollama:
            break
        case .openAI:
            arguments.append(contentsOf: ["--api-key", openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)])
        case .anthropic:
            arguments.append(contentsOf: ["--api-key", anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)])
        }

        if dryRun {
            arguments.append("--dry-run")
        }

        do {
            runningProcess = try backend.run(arguments: arguments) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                self?.finishGeneration(result)
            }
        } catch {
            finishGeneration(.failure(error))
        }
    }

    func cancelGeneration() {
        didCancelRun = true
        runningProcess?.terminate()
        runningProcess = nil
        isRunning = false
        status = "Cancelled"
        generationProgress = nil
        activeOperation = .none
        progressEntries.append(ProgressEntry(stage: "cancel", message: "Generation cancelled."))
    }

    func pullSelectedModel() {
        modelToPull = selectedModel
        showPullConfirmation = true
    }

    func requestPullModel() {
        guard !modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        showPullConfirmation = true
    }

    func confirmPullModel() {
        guard distributionMode.canManageOllama else {
            setError("The App Store build can detect Ollama, but cannot install or pull models.")
            return
        }

        let model = modelToPull.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !model.isEmpty else { return }
        isRunning = true
        status = "Pulling model"
        generationProgress = 0.05
        progressEntries.removeAll()
        didReceiveBackendError = false
        didCancelRun = false
        activeOperation = .modelPull

        do {
            runningProcess = try backend.run(arguments: ["pull-model", "--model", model]) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                if case .success(0) = result {
                    self?.selectedModel = model
                    self?.defaults.set(model, forKey: "ollamaModel")
                }
                self?.finishGeneration(result)
                self?.refreshOllama()
            }
        } catch {
            finishGeneration(.failure(error))
        }
    }

    func openOllamaDownload() {
        guard let url = URL(string: "https://ollama.com/download") else { return }
        NSWorkspace.shared.open(url)
    }

    func openGeneratedFile(_ file: GeneratedFile) {
        guard FileManager.default.fileExists(atPath: file.url.path) else {
            setError("This file no longer exists.")
            return
        }
        NSWorkspace.shared.open(file.url)
    }

    func revealGeneratedFile(_ file: GeneratedFile) {
        guard FileManager.default.fileExists(atPath: file.url.path) else {
            setError("This file no longer exists.")
            return
        }
        NSWorkspace.shared.activateFileViewerSelecting([file.url])
    }

    func saveAISettings() {
        persistSettings()
        status = "Settings saved"
    }

    func dismissWelcome() {
        defaults.set(true, forKey: "hasSeenWelcome")
        showWelcome = false
    }

    func showWelcomeGuide() {
        showWelcome = true
    }

    func setNotificationsEnabled(_ enabled: Bool) {
        notificationsEnabled = enabled
        defaults.set(enabled, forKey: "notificationsEnabled")
        if enabled {
            requestNotificationAuthorization()
        }
    }

    private func persistSettings() {
        defaults.set(aiProvider.rawValue, forKey: "aiProvider")
        defaults.set(selectedModel, forKey: "ollamaModel")
        defaults.set(openAIModel, forKey: "openAIModel")
        defaults.set(anthropicModel, forKey: "anthropicModel")
        defaults.set(outputFolder.path, forKey: "outputFolderPath")
        SecretStore.save(openAIAPIKey, account: "openai-api-key")
        SecretStore.save(anthropicAPIKey, account: "anthropic-api-key")
    }

    private func apply(_ event: BackendEvent) {
        switch event {
        case let .progress(stage, message, progress):
            status = message
            generationProgress = progress ?? generationProgress
            progressEntries.append(ProgressEntry(stage: stage, message: message))
        case let .file(role, path):
            let file = GeneratedFile(role: role, url: URL(fileURLWithPath: path))
            if !generatedFiles.contains(where: { $0.url == file.url }) {
                generatedFiles.append(file)
            }
        case let .previewPage(role, page, path, sourcePDF):
            guard page > 0 else { return }
            let generatedPage = GeneratedPage(
                role: role,
                pageNumber: page,
                url: URL(fileURLWithPath: path),
                sourcePDF: URL(fileURLWithPath: sourcePDF)
            )
            if !previewPages.contains(where: { $0.role == role && $0.pageNumber == page && $0.sourcePDF == generatedPage.sourcePDF }) {
                previewPages.append(generatedPage)
                previewPages.sort { $0.sortKey < $1.sortKey }
            }
        case let .done(message):
            status = message
            generationProgress = 1.0
            progressEntries.append(ProgressEntry(stage: "done", message: message))
        case let .error(message):
            didReceiveBackendError = true
            setError(message)
            notifyFailure(for: activeOperation, message: message)
        case let .models(models, message):
            availableModels = models
            if !models.isEmpty, !models.contains(selectedModel) {
                if models.contains("qwen2.5:14b") {
                    selectedModel = "qwen2.5:14b"
                } else {
                    selectedModel = models[0]
                }
                defaults.set(selectedModel, forKey: "ollamaModel")
            }
            if let message {
                status = message
            }
        case let .ollamaStatus(installed, running, command, message):
            ollamaState = OllamaState(installed: installed, running: running, command: command, message: message ?? "")
            status = message ?? status
        }
    }

    private func finishGeneration(_ result: Result<Int32, Error>) {
        let operation = activeOperation
        activeOperation = .none
        runningProcess = nil
        isRunning = false
        if didCancelRun {
            didCancelRun = false
            status = "Cancelled"
            generationProgress = nil
            return
        }

        switch result {
        case let .success(code):
            if code == 0 {
                status = status == "Starting" ? "Done" : status
                generationProgress = 1.0
                notifySuccess(for: operation)
            } else if !didReceiveBackendError {
                let message = "Generation failed without a backend error message. Refresh Ollama, check the selected model, then try again. Backend exited with code \(code)."
                setError(message)
                notifyFailure(for: operation, message: message)
            }
        case let .failure(error):
            setError(error.localizedDescription)
            notifyFailure(for: operation, message: error.localizedDescription)
        }
    }

    private func setError(_ message: String) {
        errorMessage = message
        showError = true
        status = "Error"
        generationProgress = nil
        progressEntries.append(ProgressEntry(stage: "error", message: message))
    }

    private func notifySuccess(for operation: RunningOperation) {
        switch operation {
        case .generation:
            sendNotification(title: "Paper ready", body: "The generated PDFs have been saved to \(outputFolder.lastPathComponent).")
        case .modelPull:
            sendNotification(title: "Model ready", body: "\(selectedModel) is available in Ollama.")
        case .none:
            break
        }
    }

    private func notifyFailure(for operation: RunningOperation, message: String) {
        switch operation {
        case .generation:
            sendNotification(title: "Generation failed", body: message)
        case .modelPull:
            sendNotification(title: "Model pull failed", body: message)
        case .none:
            break
        }
    }

    private func requestNotificationAuthorization() {
        Task {
            _ = try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])
        }
    }

    private func sendNotification(title: String, body: String) {
        guard notificationsEnabled else { return }
        Task {
            let center = UNUserNotificationCenter.current()
            let settings = await center.notificationSettings()
            let allowed: Bool
            switch settings.authorizationStatus {
            case .authorized, .provisional, .ephemeral:
                allowed = true
            case .notDetermined:
                allowed = (try? await center.requestAuthorization(options: [.alert, .sound])) ?? false
            default:
                allowed = false
            }
            guard allowed else { return }

            let content = UNMutableNotificationContent()
            content.title = title
            content.body = body
            content.sound = .default
            let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
            try? await center.add(request)
        }
    }
}

private enum RunningOperation {
    case none
    case generation
    case modelPull
}
