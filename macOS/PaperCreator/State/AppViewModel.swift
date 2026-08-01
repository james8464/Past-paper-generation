import AppKit
import Combine
import Foundation
@preconcurrency import UserNotifications

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
    @Published var lastQualityReport: GenerationQualityReport?

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
        selectedBoard.papers.first { $0.id == selectedPaperID }
            ?? selectedBoard.papers.first
            ?? PaperOption(
                id: "unknown",
                title: "Unknown",
                detail: "",
                readiness: PaperReadiness(
                    difficultyVerified: false,
                    visuallyCalibrated: false,
                    releaseReady: false
                )
            )
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
        if showWelcome { return "Finish the welcome guide before creating a paper." }
        if !selectedBoard.isReady { return "\(selectedBoard.subjectTitle) \(selectedBoard.title) is coming soon." }
        if dryRun { return nil }
        if !selectedBoard.usesAI { return nil }
        if !selectedBoard.supports(aiProvider) {
            return "\(aiProvider.title) is not supported by this generator."
        }
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
        dryRun = defaults.bool(forKey: AppStorageKey.dryRun)
        openAIAPIKey = SecretStore.read(SecretAccount.openAIAPIKey)
        anthropicAPIKey = SecretStore.read(SecretAccount.anthropicAPIKey)
        notificationCenter.delegate = NotificationPresenter.shared
        if defaults.object(forKey: AppStorageKey.notificationsEnabled) != nil {
            notificationsEnabled = defaults.bool(forKey: AppStorageKey.notificationsEnabled)
        }
        showWelcome = !defaults.bool(forKey: AppStorageKey.hasSeenWelcome)
        if let bookmark = defaults.data(forKey: AppStorageKey.outputFolderBookmark) {
            restoreOutputFolder(from: bookmark)
        } else if distributionMode == .direct,
                  let savedOutput = defaults.string(forKey: AppStorageKey.outputFolderPath),
                  !savedOutput.isEmpty {
            if AppDefaults.isSandboxDownloadsPath(savedOutput) {
                defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
            } else {
                outputFolder = URL(fileURLWithPath: savedOutput)
            }
        } else {
            defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
        }
        selectedBoardID = defaults.string(forKey: AppStorageKey.selectedBoardID) ?? ExamCatalog.defaultBoard.id
        selectedPaperID = defaults.string(forKey: AppStorageKey.selectedPaperID) ?? selectedBoard.papers.first?.id ?? "unknown"
        restoreRecentDocuments()
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
        progressEntries.removeAll()
        lastQualityReport = nil
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

    func showCreationWorkspace() {
        sidebarSelection = .board(selectedBoardID)
    }

    func generate() {
        guard canGenerate else { return }
        guard let backendSubject = selectedBoard.backendSubject else {
            setError("This exam board is coming soon.")
            return
        }
        if selectedBoard.usesAI && aiProvider.sendsPromptsOffDevice && !hasHostedAIConsent {
            pendingHostedProvider = aiProvider
            showHostedAIConsent = true
            return
        }
        persistSettings()

        progressEntries.removeAll()
        lastQualityReport = nil
        didReceiveBackendError = false
        didCancelRun = false
        isRunning = true
        status = "Starting"
        generationProgress = 0.02
        activeOperation = .generation
        beginGenerationEstimate()
        let processOutputFolder = distributionMode == .appStore
            ? AppDefaults.appStoreWorkingFolder()
            : outputFolder

        var arguments = [
            "generate",
            "--subject",
            backendSubject,
            "--paper",
            selectedPaper.id,
            "--output",
            processOutputFolder.path,
            "--provider",
            aiProvider.backendID,
            "--model",
            activeModelName,
            "--ollama-url",
            ollamaURL,
        ]

        var backendEnvironment = [
            "PAPER_CREATOR_GENERATED_ON": Self.generationDateFormatter.string(from: Date()),
            "PAPER_CREATOR_JOB_ID": UUID().uuidString,
            "PAPER_CREATOR_APP_VERSION": Bundle.main.object(
                forInfoDictionaryKey: "CFBundleShortVersionString"
            ) as? String ?? "development",
            "PAPER_CREATOR_APP_BUILD": Bundle.main.object(
                forInfoDictionaryKey: "CFBundleVersion"
            ) as? String ?? "development",
        ]
        switch selectedBoard.usesAI ? aiProvider : .ollama {
        case .ollama, .apple:
            break
        case .openAI:
            backendEnvironment["PAPER_CREATOR_API_KEY"] = openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)
        case .anthropic:
            backendEnvironment["PAPER_CREATOR_API_KEY"] = anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)
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
    }

    func removeGeneratedFile(_ file: GeneratedFile) {
        generatedFiles.removeAll { $0.id == file.id }
        persistRecentDocuments()
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
        let generationMode = selectedBoard.usesAI
            ? "\(selectedBoard.contentMode.title), \(aiProvider.title), \(activeModelName)"
            : selectedBoard.contentMode.title
        let summary = [
            "Paper creator Diagnostics",
            "Distribution: \(distributionMode.title)",
            "Selected board: \(selectedBoard.subjectTitle) \(selectedBoard.title)",
            "Selected paper: \(selectedPaper.title) - \(selectedPaper.detail)",
            "Generation mode: \(generationMode)",
            "Visual profile: \(selectedPaper.readiness.visuallyCalibrated ? "Reviewed" : "Not reviewed")",
            "Difficulty verification: \(selectedPaper.readiness.difficultyVerified ? "Passed" : "Not independently verified")",
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

    func setDryRun(_ enabled: Bool) {
        dryRun = enabled
        defaults.set(enabled, forKey: AppStorageKey.dryRun)
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
        defaults.set(dryRun, forKey: AppStorageKey.dryRun)
        defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
        SecretStore.save(openAIAPIKey, account: SecretAccount.openAIAPIKey)
        SecretStore.save(anthropicAPIKey, account: SecretAccount.anthropicAPIKey)
    }

    private static let generationDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

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
            guard url.startAccessingSecurityScopedResource() else {
                defaults.removeObject(forKey: AppStorageKey.outputFolderBookmark)
                outputFolder = AppDefaults.defaultOutputFolder()
                defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
                return
            }
            securityScopedOutputFolder = url
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
        case let .hello(protocolVersion, _, _):
            if protocolVersion != 2 {
                setError("The generation service uses an unsupported protocol version.")
            }
        case let .progress(stage, message, progress):
            status = message
            generationProgress = progress ?? generationProgress
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: stage, message: message))
        case let .file(role, path):
            let file = GeneratedFile(
                role: role,
                url: URL(fileURLWithPath: path),
                subject: "\(selectedBoard.subjectTitle) \(selectedBoard.shortTitle)",
                paper: selectedPaper.title
            )
            if !generatedFiles.contains(where: { $0.url == file.url }) {
                generatedFiles.insert(file, at: 0)
                generatedFiles = Array(generatedFiles.prefix(60))
            }
            if role == "package_manifest" {
                lastQualityReport = GenerationQualityReport.load(from: file.url)
            }
        case let .done(message):
            status = message
            generationProgress = 1.0
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: "done", message: message))
        case let .error(message):
            guard !didCancelRun else { return }
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
                do {
                    try moveGeneratedFilesToOutputFolderIfNeeded()
                } catch {
                    let message = "The paper was created, but it could not be saved to the selected folder: \(error.localizedDescription)"
                    setError(message)
                    notifyFailure(for: operation, message: message)
                    return
                }
                status = status == "Starting" ? "Done" : status
                generationProgress = 1.0
                generationEstimate = nil
                persistRecentDocuments()
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

    private func moveGeneratedFilesToOutputFolderIfNeeded() throws {
        guard distributionMode == .appStore else { return }
        let workingFolder = AppDefaults.appStoreWorkingFolder().standardizedFileURL
        let destinationFolder = outputFolder.standardizedFileURL
        guard workingFolder != destinationFolder else { return }

        try FileManager.default.createDirectory(
            at: destinationFolder,
            withIntermediateDirectories: true
        )
        generatedFiles = try generatedFiles.map { file in
            guard file.url.deletingLastPathComponent().standardizedFileURL == workingFolder else {
                return file
            }
            let destination = destinationFolder.appendingPathComponent(file.url.lastPathComponent)
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.copyItem(at: file.url, to: destination)
            return GeneratedFile(
                id: file.id,
                role: file.role,
                url: destination,
                createdAt: file.createdAt,
                subject: file.subject,
                paper: file.paper
            )
        }
    }

    private func restoreRecentDocuments() {
        guard let data = defaults.data(forKey: AppStorageKey.recentDocuments),
              let documents = try? JSONDecoder().decode(
                [GeneratedFile].self,
                from: data
              ) else {
            return
        }
        generatedFiles = Array(documents.prefix(60))
    }

    private func persistRecentDocuments() {
        guard let data = try? JSONEncoder().encode(generatedFiles) else { return }
        defaults.set(data, forKey: AppStorageKey.recentDocuments)
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
            sendNotification(title: "Your paper is ready", body: "The paper and mark scheme are in \(outputFolder.lastPathComponent).")
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
                title: "Creating your paper",
                body: "\(selectedBoard.subjectTitle) · \(selectedPaper.title)"
            )
        case .modelPull:
            sendNotification(title: "Downloading model", body: "Ollama is downloading \(modelToPull).")
        case .none:
            break
        }
    }

    private func notifyFailure(for operation: RunningOperation, message: String) {
        switch operation {
        case .generation:
            sendNotification(title: "Couldn’t create the paper", body: message)
        case .modelPull:
            sendNotification(title: "Couldn’t download the model", body: message)
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
