import AppKit
import Combine
import Foundation
import UserNotifications

@MainActor
final class AppViewModel: ObservableObject {
    @Published var selectedBoardID = ExamCatalog.defaultBoard.id
    @Published var selectedPaperID = ExamCatalog.defaultBoard.papers.first?.id ?? "unknown"
    @Published var selectedModel = AppDefaults.ollamaModel
    @Published var aiProvider: AIProvider = .ollama
    @Published var ollamaURL = AppDefaults.ollamaURL
    @Published var outputFolder = AppDefaults.defaultOutputFolder()
    @Published var dryRun = false
    @Published var isRunning = false
    @Published var status = "Ready"
    @Published var generationProgress: Double?
    @Published var progressEntries: [ProgressEntry] = []
    @Published var generatedFiles: [GeneratedFile] = []
    @Published var isRefreshingOllama = false
    @Published var ollamaState = OllamaState()
    @Published var availableModels: [String] = []
    @Published var modelToPull = AppDefaults.ollamaModel
    @Published var openAIModel = AppDefaults.openAIModel
    @Published var anthropicModel = AppDefaults.anthropicModel
    @Published var appleModel = AppDefaults.appleModel
    @Published var openAIAPIKey = ""
    @Published var anthropicAPIKey = ""
    @Published var showPullConfirmation = false
    @Published var showHostedAIConsent = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showWelcome = false
    @Published var showHelp = false
    @Published var notificationsEnabled = true
    @Published var sidebarSelection: SidebarItem?
    @Published var generationEstimate: GenerationEstimate?
    @Published var isBenchmarkRunning = false
    @Published var benchmarkProgress: Double?
    @Published var benchmarkSamples: [BenchmarkSample] = []
    @Published var benchmarkMetrics: [BenchmarkMetric] = []
    @Published var benchmarkVerdict: BenchmarkVerdict?

    let distributionMode = DistributionMode.current

    private let backend = BackendClient()
    private let defaults = UserDefaults.standard
    private let notificationCenter = UNUserNotificationCenter.current()
    private var runningProcess: Process?
    private var benchmarkProcess: Process?
    private var didReceiveBackendError = false
    private var didCancelRun = false
    private var activeOperation = RunningOperation.none
    private var etaTimer: AnyCancellable?
    private var pendingHostedProvider: AIProvider?
    private var securityScopedOutputFolder: URL?

    var selectedBoard: ExamBoardOption {
        ExamCatalog.board(id: selectedBoardID) ?? ExamCatalog.defaultBoard
    }

    var selectedPaper: PaperOption {
        selectedBoard.papers.first { $0.id == selectedPaperID } ?? selectedBoard.papers.first ?? PaperOption(id: "unknown", title: "Unknown", detail: "")
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
        if isBenchmarkRunning { return "Benchmark is running." }
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
            if !hasHostedAIConsent { return "Review and accept the hosted AI disclosure in Settings." }
            return openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "Enter an OpenAI API key in Settings." : nil
        case .anthropic:
            if !hasHostedAIConsent { return "Review and accept the hosted AI disclosure in Settings." }
            return anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "Enter an Anthropic API key in Settings." : nil
        case .apple:
            return nil
        }
    }

    var hasHostedAIConsent: Bool {
        defaults.bool(forKey: AppStorageKey.hostedAIConsentAccepted)
    }

    var activeModelName: String {
        switch aiProvider {
        case .ollama: selectedModel
        case .openAI: openAIModel
        case .anthropic: anthropicModel
        case .apple: appleModel
        }
    }

    init() {
        let ollamaModel = defaults.string(forKey: AppStorageKey.ollamaModel) ?? AppDefaults.ollamaModel
        aiProvider = AIProvider(rawValue: defaults.string(forKey: AppStorageKey.aiProvider) ?? "") ?? .ollama
        selectedModel = ollamaModel
        modelToPull = ollamaModel
        openAIModel = defaults.string(forKey: AppStorageKey.openAIModel) ?? AppDefaults.openAIModel
        anthropicModel = defaults.string(forKey: AppStorageKey.anthropicModel) ?? AppDefaults.anthropicModel
        appleModel = defaults.string(forKey: AppStorageKey.appleModel) ?? AppDefaults.appleModel
        openAIAPIKey = SecretStore.read(SecretAccount.openAIAPIKey)
        anthropicAPIKey = SecretStore.read(SecretAccount.anthropicAPIKey)
        notificationCenter.delegate = NotificationPresenter.shared
        if defaults.object(forKey: AppStorageKey.notificationsEnabled) != nil {
            notificationsEnabled = defaults.bool(forKey: AppStorageKey.notificationsEnabled)
        }
        showWelcome = !defaults.bool(forKey: AppStorageKey.hasSeenWelcome)
        if let bookmark = defaults.data(forKey: AppStorageKey.outputFolderBookmark) {
            restoreOutputFolder(from: bookmark)
        } else if let savedOutput = defaults.string(forKey: AppStorageKey.outputFolderPath), !savedOutput.isEmpty {
            if AppDefaults.isSandboxDownloadsPath(savedOutput) {
                defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
            } else {
                outputFolder = URL(fileURLWithPath: savedOutput)
            }
        }
        selectedBoardID = defaults.string(forKey: AppStorageKey.selectedBoardID) ?? ExamCatalog.defaultBoard.id
        selectedPaperID = defaults.string(forKey: AppStorageKey.selectedPaperID) ?? selectedBoard.papers.first?.id ?? "unknown"
        sidebarSelection = .board(selectedBoardID)
    }

    func refreshOllama() {
        guard !isRunning, !isBenchmarkRunning, !isRefreshingOllama else { return }
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
            setOutputFolder(url)
        }
    }

    func openOutputFolder() {
        NSWorkspace.shared.open(outputFolder)
    }

    func openProjectHelp() {
        NSWorkspace.shared.open(AppLinks.projectHelp)
    }

    func openPrivacyPolicy() {
        NSWorkspace.shared.open(AppLinks.privacyPolicy)
    }

    func openSupportPage() {
        NSWorkspace.shared.open(AppLinks.support)
    }

    func selectBoard(_ board: ExamBoardOption) {
        guard selectedBoardID != board.id || !board.papers.contains(where: { $0.id == selectedPaperID }) else {
            return
        }
        selectedBoardID = board.id
        selectedPaperID = board.papers.first?.id ?? "unknown"
        defaults.set(board.id, forKey: AppStorageKey.selectedBoardID)
        defaults.set(selectedPaperID, forKey: AppStorageKey.selectedPaperID)
        generatedFiles.removeAll()
        progressEntries.removeAll()
        status = board.isReady ? "Ready" : "Coming Soon"
    }

    func selectPaperID(_ paperID: String) {
        guard selectedPaperID != paperID else {
            defaults.set(paperID, forKey: AppStorageKey.selectedPaperID)
            return
        }
        selectedPaperID = paperID
        defaults.set(paperID, forKey: AppStorageKey.selectedPaperID)
    }

    func selectAIProvider(_ provider: AIProvider) {
        guard provider != aiProvider else { return }
        if provider.sendsPromptsOffDevice && !hasHostedAIConsent {
            pendingHostedProvider = provider
            showHostedAIConsent = true
            return
        }
        aiProvider = provider
        persistSettings()
    }

    func acceptHostedAIConsent() {
        defaults.set(true, forKey: AppStorageKey.hostedAIConsentAccepted)
        if let provider = pendingHostedProvider {
            aiProvider = provider
        }
        pendingHostedProvider = nil
        showHostedAIConsent = false
        persistSettings()
    }

    func cancelHostedAIConsent() {
        pendingHostedProvider = nil
        showHostedAIConsent = false
    }

    func showBenchmarkPage() {
        sidebarSelection = .benchmark
    }

    func generate() {
        guard canGenerate else { return }
        guard let backendSubject = selectedBoard.backendSubject else {
            setError("This exam board is coming soon.")
            return
        }
        if aiProvider.sendsPromptsOffDevice && !hasHostedAIConsent {
            pendingHostedProvider = aiProvider
            showHostedAIConsent = true
            return
        }
        persistSettings()

        generatedFiles.removeAll()
        progressEntries.removeAll()
        didReceiveBackendError = false
        didCancelRun = false
        isRunning = true
        status = "Starting"
        generationProgress = 0.02
        activeOperation = .generation
        beginGenerationEstimate()

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

        let backendEnvironment: [String: String]
        switch aiProvider {
        case .ollama, .apple:
            backendEnvironment = [:]
        case .openAI:
            backendEnvironment = ["PAPER_CREATOR_API_KEY": openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)]
        case .anthropic:
            backendEnvironment = ["PAPER_CREATOR_API_KEY": anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)]
        }

        if dryRun {
            arguments.append("--dry-run")
        }

        do {
            runningProcess = try backend.run(arguments: arguments, environment: backendEnvironment) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                self?.finishGeneration(result)
            }
            notifyStarted(for: .generation)
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
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil
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
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil

        do {
            runningProcess = try backend.run(arguments: ["pull-model", "--model", model]) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                if case .success(0) = result {
                    self?.selectedModel = model
                    self?.defaults.set(model, forKey: AppStorageKey.ollamaModel)
                }
                self?.finishGeneration(result)
                self?.refreshOllama()
            }
            notifyStarted(for: .modelPull)
        } catch {
            finishGeneration(.failure(error))
        }
    }

    func openOllamaDownload() {
        NSWorkspace.shared.open(AppLinks.ollamaDownload)
    }

    func openGeneratedFile(_ file: GeneratedFile) {
        guard FileManager.default.fileExists(atPath: file.url.path) else {
            setError("This file no longer exists.")
            return
        }
        NSWorkspace.shared.open(file.url)
    }

    func hasGeneratedFile(role: String) -> Bool {
        generatedFile(role: role) != nil
    }

    func openGeneratedFile(role: String) {
        guard let file = generatedFile(role: role) else {
            setError("Generate a paper first.")
            return
        }
        openGeneratedFile(file)
    }

    func revealGeneratedFile(_ file: GeneratedFile) {
        guard FileManager.default.fileExists(atPath: file.url.path) else {
            setError("This file no longer exists.")
            return
        }
        NSWorkspace.shared.activateFileViewerSelecting([file.url])
    }

    func revealGeneratedFile(role: String) {
        guard let file = generatedFile(role: role) else {
            setError("Generate a paper first.")
            return
        }
        revealGeneratedFile(file)
    }

    func saveAISettings() {
        persistSettings()
        status = "Settings saved"
    }

    func dismissWelcome() {
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        showWelcome = false
    }

    func showWelcomeGuide() {
        showWelcome = true
    }

    func showHelpGuide() {
        showHelp = true
    }

    func dismissHelpGuide() {
        showHelp = false
    }

    func copyDiagnosticSummary() {
        let summary = [
            "ExamForge Diagnostics",
            "Distribution: \(distributionMode.title)",
            "Selected board: \(selectedBoard.subjectTitle) \(selectedBoard.title)",
            "Selected paper: \(selectedPaper.title) - \(selectedPaper.detail)",
            "AI provider: \(aiProvider.title)",
            "Model: \(activeModelName)",
            "Hosted AI consent: \(hasHostedAIConsent ? "Accepted" : "Not accepted")",
            "Ollama: \(ollamaState.message)",
            "Output folder: \(outputFolder.path)",
            "Status: \(status)",
            "Latest ETA: \(generationEstimate?.remainingText ?? "None")",
            "Benchmark: \(benchmarkVerdict.map { "\($0.verdict) (\(Int($0.score * 100))%)" } ?? "Not run")",
            "Generated files: \(generatedFiles.map { $0.url.lastPathComponent }.joined(separator: ", "))",
        ].joined(separator: "\n")

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(summary, forType: .string)
        status = "Diagnostics copied"
    }

    func setNotificationsEnabled(_ enabled: Bool) {
        notificationsEnabled = enabled
        defaults.set(enabled, forKey: AppStorageKey.notificationsEnabled)
        if enabled {
            requestNotificationAuthorization()
        }
    }

    func startBenchmark() {
        guard !isRunning, !isBenchmarkRunning else { return }
        benchmarkSamples.removeAll()
        benchmarkMetrics.removeAll()
        benchmarkVerdict = nil
        benchmarkProgress = 0
        isBenchmarkRunning = true
        status = "Benchmarking"
        sidebarSelection = .benchmark

        do {
            benchmarkProcess = try backend.run(arguments: [
                "benchmark",
                "--duration",
                String(Int(AppDefaults.benchmarkDurationSeconds)),
                "--output",
                outputFolder.path,
            ]) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                self?.finishBenchmark(result)
            }
        } catch {
            finishBenchmark(.failure(error))
        }
    }

    func cancelBenchmark() {
        benchmarkProcess?.terminate()
        benchmarkProcess = nil
        isBenchmarkRunning = false
        benchmarkProgress = nil
        status = "Benchmark cancelled"
    }

    private func persistSettings() {
        defaults.set(aiProvider.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set(selectedModel, forKey: AppStorageKey.ollamaModel)
        defaults.set(openAIModel, forKey: AppStorageKey.openAIModel)
        defaults.set(anthropicModel, forKey: AppStorageKey.anthropicModel)
        defaults.set(appleModel, forKey: AppStorageKey.appleModel)
        defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
        SecretStore.save(openAIAPIKey, account: SecretAccount.openAIAPIKey)
        SecretStore.save(anthropicAPIKey, account: SecretAccount.anthropicAPIKey)
    }

    private func setOutputFolder(_ url: URL) {
        securityScopedOutputFolder?.stopAccessingSecurityScopedResource()
        securityScopedOutputFolder = url.startAccessingSecurityScopedResource() ? url : nil
        outputFolder = url
        defaults.set(url.path, forKey: AppStorageKey.outputFolderPath)
        do {
            let bookmark = try url.bookmarkData(
                options: .withSecurityScope,
                includingResourceValuesForKeys: nil,
                relativeTo: nil
            )
            defaults.set(bookmark, forKey: AppStorageKey.outputFolderBookmark)
        } catch {
            defaults.removeObject(forKey: AppStorageKey.outputFolderBookmark)
        }
    }

    private func restoreOutputFolder(from bookmark: Data) {
        var isStale = false
        do {
            let url = try URL(
                resolvingBookmarkData: bookmark,
                options: .withSecurityScope,
                relativeTo: nil,
                bookmarkDataIsStale: &isStale
            )
            securityScopedOutputFolder = url.startAccessingSecurityScopedResource() ? url : nil
            outputFolder = url
            defaults.set(url.path, forKey: AppStorageKey.outputFolderPath)
            if isStale {
                setOutputFolder(url)
            }
        } catch {
            defaults.removeObject(forKey: AppStorageKey.outputFolderBookmark)
        }
    }

    private func generatedFile(role: String) -> GeneratedFile? {
        generatedFiles.reversed().first { $0.role == role }
    }

    private func apply(_ event: BackendEvent) {
        switch event {
        case let .progress(stage, message, progress):
            status = message
            generationProgress = progress ?? generationProgress
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: stage, message: message))
        case let .file(role, path):
            let file = GeneratedFile(role: role, url: URL(fileURLWithPath: path))
            if !generatedFiles.contains(where: { $0.url == file.url }) {
                generatedFiles.append(file)
            }
        case let .done(message):
            status = message
            generationProgress = 1.0
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: "done", message: message))
        case let .error(message):
            didReceiveBackendError = true
            setError(message)
            notifyFailure(for: activeOperation, message: message)
        case let .models(models, message):
            availableModels = models
            if !models.isEmpty, !models.contains(selectedModel) {
                if models.contains(AppDefaults.ollamaModel) {
                    selectedModel = AppDefaults.ollamaModel
                } else {
                    selectedModel = models[0]
                }
                defaults.set(selectedModel, forKey: AppStorageKey.ollamaModel)
            }
            if let message {
                status = message
            }
        case let .ollamaStatus(installed, running, command, message):
            ollamaState = OllamaState(installed: installed, running: running, command: command, message: message ?? "")
            status = message ?? status
        case let .benchmarkMetric(metric):
            benchmarkMetrics.append(metric)
        case let .benchmarkSample(sample):
            benchmarkSamples.append(sample)
            benchmarkProgress = min(1.0, sample.elapsed / AppDefaults.benchmarkDurationSeconds)
        case let .benchmarkDone(verdict):
            benchmarkVerdict = verdict
            benchmarkProgress = 1.0
            status = verdict.verdict
        }
    }

    private func finishGeneration(_ result: Result<Int32, Error>) {
        let operation = activeOperation
        activeOperation = .none
        runningProcess = nil
        isRunning = false
        etaTimer?.cancel()
        etaTimer = nil
        if didCancelRun {
            didCancelRun = false
            status = "Cancelled"
            generationProgress = nil
            generationEstimate = nil
            return
        }

        switch result {
        case let .success(code):
            if code == 0 {
                status = status == "Starting" ? "Done" : status
                generationProgress = 1.0
                generationEstimate = nil
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
        if activeOperation == .generation {
            generationEstimate = nil
            etaTimer?.cancel()
            etaTimer = nil
        }
        progressEntries.append(ProgressEntry(stage: "error", message: message))
    }

    private func beginGenerationEstimate() {
        generationEstimate = GenerationEstimator.initialEstimate(
            board: selectedBoard,
            paper: selectedPaper,
            provider: aiProvider,
            model: activeModelName,
            dryRun: dryRun,
            benchmark: benchmarkVerdict
        )
        etaTimer?.cancel()
        etaTimer = Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.updateGenerationEstimate()
            }
    }

    private func updateGenerationEstimate() {
        guard let estimate = generationEstimate else { return }
        generationEstimate = GenerationEstimator.update(estimate: estimate, progress: generationProgress)
    }

    private func finishBenchmark(_ result: Result<Int32, Error>) {
        benchmarkProcess = nil
        isBenchmarkRunning = false
        if benchmarkVerdict != nil {
            benchmarkProgress = 1.0
        } else {
            benchmarkProgress = nil
        }

        switch result {
        case let .success(code):
            if code != 0 {
                setError("Benchmark exited with code \(code).")
            }
        case let .failure(error):
            setError(error.localizedDescription)
        }
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

    private func notifyStarted(for operation: RunningOperation) {
        switch operation {
        case .generation:
            sendNotification(
                title: "Paper generation started",
                body: "ExamForge is generating \(selectedBoard.subjectTitle) \(selectedPaper.title) in the background. You will be notified when it finishes."
            )
        case .modelPull:
            sendNotification(title: "Model download started", body: "Ollama is downloading \(modelToPull). You will be notified when it finishes.")
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
            _ = try? await notificationCenter.requestAuthorization(options: [.alert, .sound])
        }
    }

    private func sendNotification(title: String, body: String) {
        guard notificationsEnabled else { return }
        Task {
            let settings = await notificationCenter.notificationSettings()
            let allowed: Bool
            switch settings.authorizationStatus {
            case .authorized, .provisional, .ephemeral:
                allowed = true
            case .notDetermined:
                allowed = (try? await notificationCenter.requestAuthorization(options: [.alert, .sound])) ?? false
            default:
                allowed = false
            }
            guard allowed else { return }

            let content = UNMutableNotificationContent()
            content.title = title
            content.body = body
            content.sound = .default
            let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
            try? await notificationCenter.add(request)
        }
    }
}

@MainActor
final class NotificationPresenter: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationPresenter()

    private override init() {
        super.init()
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .sound]
    }
}

private enum RunningOperation {
    case none
    case generation
    case modelPull
}
