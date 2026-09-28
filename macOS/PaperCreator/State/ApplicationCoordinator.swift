import AppKit
import Combine
import Foundation
@preconcurrency import UserNotifications

@MainActor
final class ApplicationCoordinator: ObservableObject {
    let settingsStore: SettingsStore
    let catalogStore: CatalogStore
    let modelCoordinator: ModelCoordinator
    let benchmarkCoordinator: BenchmarkCoordinator
    let recentDocumentStore: RecentDocumentStore
    let generationCoordinator: GenerationCoordinator

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
    @Published var hasLoadedOllamaModels = false
    @Published var modelToPull = AppDefaults.ollamaModel
    @Published var openAIModel = AppDefaults.openAIModel
    @Published var anthropicModel = AppDefaults.anthropicModel
    @Published var appleModel = AppDefaults.appleModel
    @Published var openAIAPIKey = ""
    @Published var anthropicAPIKey = ""
    @Published var showPullConfirmation = false
    @Published var showHostedAIConsent = false
    @Published var showMLXSetupConfirmation = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showWelcome = false
    @Published var showHelp = false
    @Published var helpTopic = HelpTopic.gettingStarted
    @Published var notificationsEnabled = true
    @Published var generationEstimate: GenerationEstimate?
    @Published var lastQualityReport: GenerationQualityReport?
    @Published private(set) var previewedFileID: UUID?

    private(set) var pendingGenerationSeed: Int?

    let distributionMode = DistributionMode.current

    private let backend = BackendClient()
    private let defaults = UserDefaults.standard
    private let notificationCenter = UNUserNotificationCenter.current()
    private var runningProcess: Process?
    private var didReceiveBackendError = false
    private var didCancelRun = false
    private var activeOperation = RunningOperation.none
    private var activeFrameworkID: String?
    private var etaTimer: AnyCancellable?
    private var pendingHostedProvider: AIProvider?
    private var preparedMLXModels: Set<String> = []
    private var mlxRecoveryState = MLXRecoveryState()
    private var securityScopedOutputFolder: URL?

    var selectedBoard: ExamBoardOption {
        catalogStore.selectedBoard
    }

    var selectedPaper: PaperOption {
        catalogStore.selectedPaper
    }

    var selectedBoardID: String { catalogStore.selectedBoardID }
    var selectedPaperID: String { catalogStore.selectedPaperID }
    var sidebarSelection: SidebarItem? {
        get { catalogStore.sidebarSelection }
        set { catalogStore.sidebarSelection = newValue }
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
        if benchmarkCoordinator.isRunning { return "Benchmark is running." }
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
            if hasLoadedOllamaModels && !availableModels.contains(selectedModel) {
                return "Download the selected Ollama model before generating."
            }
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

    var ollamaRecommendation: OllamaModelRecommendation {
        OllamaModelGuide.currentRecommendation
    }

    var selectedModelIsRecommended: Bool {
        selectedModel == ollamaRecommendation.model
    }

    var recommendedModelIsInstalled: Bool {
        availableModels.contains(ollamaRecommendation.model)
    }

    var ollamaModelOptions: [String] {
        var seen: Set<String> = []
        return ([selectedModel, ollamaRecommendation.model] + availableModels)
            .filter { !$0.isEmpty && seen.insert($0).inserted }
    }

    var outputFolderDisplayPath: String {
        AppDefaults.displayPath(outputFolder)
    }

    var mlxSetupExplanation: String {
        let model = appleModel.trimmingCharacters(in: .whitespacesAndNewlines)
        let runtimeDetail = distributionMode == .appStore
            ? "Apple MLX support is included with Paper Creator."
            : "Paper Creator will install Apple MLX into its managed environment if needed."
        return "\(runtimeDetail) It will then download and prepare \(model). "
            + "Models can use several gigabytes of storage. Generation remains on this Mac, "
            + "and setup does not require Terminal or an administrator password."
    }

    init() {
        let settings = SettingsStore()
        let recents = RecentDocumentStore(
            directory: AppDefaults.jobHistoryFolder(),
            retentionLimit: settings.historyRetentionLimit
        )
        settingsStore = settings
        catalogStore = CatalogStore(subjects: ExamCatalog.subjects)
        modelCoordinator = ModelCoordinator()
        benchmarkCoordinator = BenchmarkCoordinator()
        recentDocumentStore = recents
        generationCoordinator = GenerationCoordinator(history: recents)

        let ollamaModel = settings.ollamaModel
        aiProvider = settings.provider
        selectedModel = ollamaModel
        modelCoordinator.provider = settings.provider
        modelCoordinator.selectedModel = ollamaModel
        modelToPull = ollamaModel
        openAIModel = settings.openAIModel
        anthropicModel = settings.anthropicModel
        appleModel = settings.appleModel
        preparedMLXModels = Set(
            defaults.stringArray(forKey: AppStorageKey.preparedMLXModels) ?? []
        )
        dryRun = settings.dryRun
        openAIAPIKey = settings.openAIAPIKey
        anthropicAPIKey = settings.anthropicAPIKey
        notificationCenter.delegate = NotificationPresenter.shared
        notificationsEnabled = settings.notificationsEnabled
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
        restoreRecentDocuments()
        benchmarkCoordinator.outputFolder = outputFolder
    }

    func refreshOllama() {
        guard !isRunning, !benchmarkCoordinator.isRunning, !isRefreshingOllama else { return }
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

    var frenchReferencesFolder: URL {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support")
        return support.appendingPathComponent("Paper Creator/French References", isDirectory: true)
    }

    var hasFrenchReferences: Bool {
        FileManager.default.fileExists(atPath: frenchReferencesFolder.appendingPathComponent("references.sqlite").path)
    }

    func prepareFrenchReferences() {
        startFrenchOperation(arguments: ["prepare-french-references", "--output", frenchReferencesFolder.path], seed: nil)
    }

    func generateFrenchPaper(largePrint: Bool) {
        let seed = pendingGenerationSeed ?? Int.random(in: 1 ... Int(Int32.max))
        pendingGenerationSeed = seed
        let request = FrenchAssessmentRequest(
            referenceIndex: frenchReferencesFolder.appendingPathComponent("references.sqlite"),
            output: distributionMode == .appStore ? AppDefaults.appStoreWorkingFolder() : outputFolder,
            model: selectedModel.trimmingCharacters(in: .whitespacesAndNewlines),
            seed: seed, largePrint: largePrint
        )
        startFrenchOperation(arguments: request.arguments, seed: seed)
    }

    private func startFrenchOperation(arguments: [String], seed: Int?) {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        activeFrameworkID = FrenchAssessmentRequest.assessmentID
        didReceiveBackendError = false
        didCancelRun = false
        progressEntries.removeAll()
        generatedFiles.removeAll()
        lastQualityReport = nil
        isRunning = true
        activeOperation = .generation
        status = String(localized: "Preparing French assessment")
        generationProgress = nil
        do {
            if let seed {
                try generationCoordinator.begin(GenerationJobRecord(
                    configuration: GenerationConfiguration(
                        boardID: "fr-national-nsi", paperID: "written-2027", provider: "ollama",
                        model: selectedModel, seed: seed, dryRun: false,
                        educationSystem: "fr-national", assessmentID: FrenchAssessmentRequest.assessmentID,
                        documentLanguage: "fr-FR"
                    ),
                    provenance: GenerationProvenance(
                        appVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "development",
                        provider: "ollama", model: selectedModel
                    ), state: .pending, artifacts: [],
                    qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
                ))
            }
            runningProcess = try backend.run(arguments: arguments) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                self?.finishGeneration(result)
            }
        } catch {
            finishGeneration(.failure(error))
        }
    }

    func chooseOutputFolder() {
        guard !isRunning else { return }
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
        guard catalogStore.selectBoard(board, isLocked: isRunning) else { return }
        progressEntries.removeAll()
        lastQualityReport = nil
        status = board.isReady ? "Ready" : "Coming Soon"
    }

    func selectPaperID(_ paperID: String) {
        guard catalogStore.selectPaperID(paperID, isLocked: isRunning) else { return }
        progressEntries.removeAll()
        lastQualityReport = nil
    }

    func selectAssessmentKind(_ kind: AssessmentKind) {
        let options = kind == .fullPaper
            ? selectedBoard.fullPapers
            : selectedBoard.questionBanks
        guard let first = options.first else { return }
        selectPaperID(first.id)
    }

    func selectAIProvider(_ provider: AIProvider) {
        guard !isRunning else { return }
        guard provider != aiProvider else { return }
        if provider.sendsPromptsOffDevice && !hasHostedAIConsent {
            pendingHostedProvider = provider
            showHostedAIConsent = true
            return
        }
        aiProvider = provider
        modelCoordinator.provider = provider
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
        catalogStore.show(.benchmark)
    }

    func showCreationWorkspace() {
        catalogStore.show(.board(selectedBoardID))
    }

    func showDocuments() {
        catalogStore.show(.documents)
    }

    func showHistory() {
        catalogStore.show(.history)
    }

    func previewGeneratedFile(_ file: GeneratedFile) {
        previewedFileID = file.id
        catalogStore.show(.documents)
    }

    func previewGeneratedFile(role: String) {
        guard let file = generatedFile(role: role) else { return }
        previewGeneratedFile(file)
    }

    func duplicateConfiguration(_ record: GenerationJobRecord) {
        applyConfiguration(record, seed: record.configuration.seed)
    }

    func createAgainWithNewSeed(_ record: GenerationJobRecord) {
        var seed = Int.random(in: 1 ... Int(Int32.max))
        if seed == record.configuration.seed {
            seed = seed == Int(Int32.max) ? 1 : seed + 1
        }
        applyConfiguration(record, seed: seed)
    }

    private func applyConfiguration(_ record: GenerationJobRecord, seed: Int?) {
        if record.configuration.assessmentID == FrenchAssessmentRequest.assessmentID {
            guard !isRunning, record.configuration.educationSystem == "fr-national",
                  record.configuration.documentLanguage == "fr-FR",
                  record.configuration.provider == "ollama" else { return }
            selectedModel = record.configuration.model
            pendingGenerationSeed = seed
            lastQualityReport = nil
            sidebarSelection = .frenchBaccalaureat
            return
        }
        guard !isRunning,
              let board = ExamCatalog.board(id: record.configuration.boardID),
              board.papers.contains(where: {
                  $0.id == record.configuration.paperID
              }),
              let provider = AIProvider(backendID: record.configuration.provider)
        else { return }
        selectBoard(board)
        selectPaperID(record.configuration.paperID)
        aiProvider = provider
        switch provider {
        case .ollama:
            selectedModel = record.configuration.model
        case .openAI:
            openAIModel = record.configuration.model
        case .anthropic:
            anthropicModel = record.configuration.model
        case .apple:
            appleModel = record.configuration.model
        }
        dryRun = record.configuration.dryRun
        pendingGenerationSeed = seed
        sidebarSelection = .board(board.id)
        persistSettings()
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
        if MLXSetupPolicy.requiresSetup(
            provider: aiProvider,
            model: activeModelName,
            preparedModels: preparedMLXModels,
            usesAI: selectedBoard.usesAI,
            dryRun: dryRun
        ) {
            showMLXSetupConfirmation = true
            status = "Apple MLX setup required"
            return
        }
        persistSettings()

        progressEntries.removeAll()
        lastQualityReport = nil
        didReceiveBackendError = false
        didCancelRun = false
        mlxRecoveryState.beginGeneration()
        isRunning = true
        status = "Starting"
        generationProgress = 0.02
        activeOperation = .generation
        beginGenerationEstimate()
        let generationSeed = pendingGenerationSeed
            ?? Int.random(in: 1 ... Int(Int32.max))
        pendingGenerationSeed = generationSeed
        catalogStore.recordRecentConfiguration(
            boardID: selectedBoard.id,
            paperID: selectedPaper.id
        )
        let readiness = selectedPaper.readiness
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: selectedBoard.id,
                paperID: selectedPaper.id,
                provider: aiProvider.backendID,
                model: activeModelName,
                seed: generationSeed,
                dryRun: dryRun
            ),
            provenance: GenerationProvenance(
                appVersion: Bundle.main.object(
                    forInfoDictionaryKey: "CFBundleShortVersionString"
                ) as? String ?? "development",
                provider: aiProvider.backendID,
                model: activeModelName
            ),
            state: .pending,
            artifacts: [],
            qualification: QualificationSnapshot(
                engineeringValidated: readiness.engineeringValidated,
                visuallyCalibrated: readiness.visuallyCalibrated,
                empiricallyCalibrated: readiness.empiricallyCalibrated
            )
        )
        try? generationCoordinator.begin(record)
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
            "--seed",
            String(generationSeed),
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
        if aiProvider == .apple {
            backendEnvironment["HF_HOME"] = AppDefaults.mlxCacheFolder().path
        }
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

    func confirmMLXSetup() {
        let model = appleModel.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !model.isEmpty else {
            showMLXSetupConfirmation = false
            setError("Choose an Apple MLX model in Settings, then try again.")
            return
        }

        showMLXSetupConfirmation = false
        isRunning = true
        status = "Setting up Apple MLX"
        generationProgress = 0.05
        progressEntries.removeAll()
        didReceiveBackendError = false
        didCancelRun = false
        activeOperation = .mlxSetup
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil

        do {
            runningProcess = try backend.run(
                arguments: ["setup-mlx", "--model", model],
                environment: ["HF_HOME": AppDefaults.mlxCacheFolder().path]
            ) { [weak self] event in
                self?.apply(event)
            } onFinish: { [weak self] result in
                self?.finishMLXSetup(result, model: model)
            }
            notifyStarted(for: .mlxSetup)
        } catch {
            finishMLXSetup(.failure(error), model: model)
        }
    }

    func cancelMLXSetup() {
        showMLXSetupConfirmation = false
        status = "Ready"
    }

    func cancelGeneration() {
        didCancelRun = true
        try? generationCoordinator.cancel()
        mlxRecoveryState.cancel()
        runningProcess?.terminate()
        if activeOperation == .mlxSetup {
            status = "Cancelling Apple MLX setup"
            progressEntries.append(
                ProgressEntry(stage: "cancel", message: "Cancelling Apple MLX setup…")
            )
            return
        }
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

    func showHelpGuide(topic: HelpTopic = .gettingStarted) {
        helpTopic = topic
        showHelp = true
    }

    func dismissHelpGuide() {
        showHelp = false
    }

    func useRecommendedOllamaModel() {
        selectedModel = ollamaRecommendation.model
        modelToPull = ollamaRecommendation.model
        saveAISettings()
    }

    func requestRecommendedOllamaModel() {
        useRecommendedOllamaModel()
        requestPullModel()
    }

    func copyDiagnosticSummary() {
        let generationMode = selectedBoard.usesAI
            ? "\(selectedBoard.contentMode.title), \(aiProvider.title), \(activeModelName)"
            : selectedBoard.contentMode.title
        let summary = ([
            "Paper creator Diagnostics",
            "Distribution: \(distributionMode.title)",
            "Selected board: \(selectedBoard.subjectTitle) \(selectedBoard.title)",
            "Selected paper: \(selectedPaper.title) - \(selectedPaper.detail)",
            "Generation mode: \(generationMode)",
            "Visual profile: \(selectedPaper.readiness.visuallyCalibrated ? "Reviewed" : "Not reviewed")",
            "Empirical calibration: \(selectedPaper.readiness.empiricallyCalibrated ? "Passed" : "Not independently verified")",
            "Hosted AI consent: \(hasHostedAIConsent ? "Accepted" : "Not accepted")",
            "Ollama: \(ollamaState.message)",
            "Output folder: \(outputFolder.path)",
            "Status: \(status)",
            "Latest ETA: \(generationEstimate?.remainingText ?? "None")",
            "Benchmark: \(benchmarkCoordinator.verdict.map { "\($0.verdict) (\(Int($0.score * 100))%)" } ?? "Not run")",
            "Generated files: \(generatedFiles.map { $0.url.lastPathComponent }.joined(separator: ", "))",
        ] + qualityDiagnosticLines).joined(separator: "\n")

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(summary, forType: .string)
        status = "Diagnostics copied"
    }

    var qualityDiagnosticLines: [String] {
        GenerationQualityPolicy.presentation(for: lastQualityReport).diagnosticLines
    }

    func setNotificationsEnabled(_ enabled: Bool) {
        notificationsEnabled = enabled
        settingsStore.notificationsEnabled = enabled
        settingsStore.save()
        if enabled {
            requestNotificationAuthorization()
        }
    }

    func setDryRun(_ enabled: Bool) {
        guard !isRunning else { return }
        dryRun = enabled
        settingsStore.dryRun = enabled
        settingsStore.save()
    }

    func startBenchmark() {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        benchmarkCoordinator.start(generationIsRunning: isRunning)
        status = "Benchmarking"
        sidebarSelection = .benchmark
    }

    func cancelBenchmark() {
        status = "Benchmark cancelled"
        benchmarkCoordinator.cancel()
    }

    private func persistSettings() {
        settingsStore.provider = aiProvider
        settingsStore.ollamaModel = selectedModel
        settingsStore.openAIModel = openAIModel
        settingsStore.anthropicModel = anthropicModel
        settingsStore.appleModel = appleModel
        settingsStore.dryRun = dryRun
        settingsStore.notificationsEnabled = notificationsEnabled
        settingsStore.openAIAPIKey = openAIAPIKey
        settingsStore.anthropicAPIKey = anthropicAPIKey
        settingsStore.save()
        defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
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
        benchmarkCoordinator.outputFolder = url
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

    func apply(_ event: BackendEvent) {
        generationCoordinator.receive(event)
        benchmarkCoordinator.receive(event)
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
                subject: activeFrameworkID == nil ? "\(selectedBoard.subjectTitle) \(selectedBoard.shortTitle)" : "Baccalauréat général · NSI",
                paper: activeFrameworkID == nil ? selectedPaper.title : "Partie écrite · 2027"
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
        case let .error(message, code):
            guard !didCancelRun else { return }
            didReceiveBackendError = true
            if code == "mlx_setup_required", activeOperation == .generation {
                let model = appleModel.trimmingCharacters(in: .whitespacesAndNewlines)
                preparedMLXModels.remove(model)
                defaults.set(preparedMLXModels.sorted(), forKey: AppStorageKey.preparedMLXModels)
                mlxRecoveryState.requestSetup()
                status = "Apple MLX setup required"
                return
            }
            setError(message)
            notifyFailure(for: activeOperation, message: message)
        case let .models(models, message):
            availableModels = models
            modelCoordinator.receiveModels(models)
            hasLoadedOllamaModels = true
            if let message {
                status = message
            }
        case let .ollamaStatus(installed, running, command, message):
            ollamaState = OllamaState(installed: installed, running: running, command: command, message: message ?? "")
            modelCoordinator.receiveOllamaState(ollamaState)
            status = message ?? status
        case .benchmarkMetric, .benchmarkSample, .benchmarkDone:
            break
        }
    }

    func finishGeneration(_ result: Result<Int32, Error>) {
        defer { activeFrameworkID = nil }
        let operation = activeOperation
        activeOperation = .none
        runningProcess = nil
        isRunning = false
        etaTimer?.cancel()
        etaTimer = nil
        if didCancelRun {
            didCancelRun = false
            mlxRecoveryState.cancel()
            status = "Cancelled"
            generationProgress = nil
            generationEstimate = nil
            return
        }
        if mlxRecoveryState.consumeSetupRequest() {
            generationProgress = nil
            generationEstimate = nil
            status = "Apple MLX setup required"
            showMLXSetupConfirmation = true
            return
        }

        switch result {
        case let .success(code):
            if code == 0 && !didReceiveBackendError {
                do {
                    try moveGeneratedFilesToOutputFolderIfNeeded()
                } catch {
                    let message = "The paper was created, but it could not be saved to the selected folder: \(error.localizedDescription)"
                    setError(message)
                    notifyFailure(for: operation, message: message)
                    try? generationCoordinator.fail(message: message)
                    pendingGenerationSeed = nil
                    return
                }
                status = status == "Starting" ? "Done" : status
                generationProgress = 1.0
                generationEstimate = nil
                persistRecentDocuments()
                try? generationCoordinator.complete(artifacts: generatedFiles)
                if let questionPaper = generatedFile(role: "question_paper") {
                    previewedFileID = questionPaper.id
                    sidebarSelection = .documents
                }
                pendingGenerationSeed = nil
                notifySuccess(for: operation)
            } else {
                let message = didReceiveBackendError ? errorMessage
                    : "Generation failed without a backend error message. Refresh Ollama, check the selected model, then try again. Backend exited with code \(code)."
                if !didReceiveBackendError {
                    setError(message)
                    notifyFailure(for: operation, message: message)
                }
                try? generationCoordinator.fail(message: message)
                pendingGenerationSeed = nil
            }
        case let .failure(error):
            setError(error.localizedDescription)
            notifyFailure(for: operation, message: error.localizedDescription)
            try? generationCoordinator.fail(message: error.localizedDescription)
            pendingGenerationSeed = nil
        }
    }

    private func finishMLXSetup(_ result: Result<Int32, Error>, model: String) {
        runningProcess = nil
        isRunning = false
        activeOperation = .none
        generationProgress = nil

        if didCancelRun {
            didCancelRun = false
            status = "Cancelled"
            progressEntries.append(
                ProgressEntry(stage: "cancel", message: "Apple MLX setup cancelled.")
            )
            return
        }

        switch result {
        case let .success(code) where code == 0 && !didReceiveBackendError:
            preparedMLXModels.insert(model)
            defaults.set(preparedMLXModels.sorted(), forKey: AppStorageKey.preparedMLXModels)
            status = "Apple MLX is ready"
            notifySuccess(for: .mlxSetup)
            generate()
        case let .success(code):
            if !didReceiveBackendError {
                let message = "Apple MLX setup could not finish (code \(code)). Check your connection and storage, then try Setup Again."
                setError(message)
                notifyFailure(for: .mlxSetup, message: message)
            }
        case let .failure(error):
            setError(error.localizedDescription)
            notifyFailure(for: .mlxSetup, message: error.localizedDescription)
        }
    }

    private func moveGeneratedFilesToOutputFolderIfNeeded() throws {
        guard distributionMode == .appStore else { return }
        let workingFolder = AppDefaults.appStoreWorkingFolder().standardizedFileURL
        let destinationFolder = outputFolder.standardizedFileURL
        guard workingFolder != destinationFolder else { return }

        if activeFrameworkID == FrenchAssessmentRequest.assessmentID,
           let first = generatedFiles.first {
            let source = first.url.deletingLastPathComponent().standardizedFileURL
            guard source.deletingLastPathComponent() == workingFolder,
                  generatedFiles.allSatisfy({ $0.url.deletingLastPathComponent().standardizedFileURL == source }) else {
                throw CocoaError(.fileReadInvalidFileName)
            }
            let destination = try AssessmentBundleExporter.export(source: source, to: destinationFolder)
            generatedFiles = generatedFiles.map { file in
                GeneratedFile(
                    id: file.id, role: file.role,
                    url: destination.appendingPathComponent(file.url.lastPathComponent),
                    createdAt: file.createdAt, subject: file.subject, paper: file.paper
                )
            }
            return
        }

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
        try? recentDocumentStore.load()
        let jobArtifacts = recentDocumentStore.records.flatMap(\.artifacts)
        if !jobArtifacts.isEmpty {
            generatedFiles = Array(jobArtifacts.prefix(60))
            return
        }
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
            benchmark: benchmarkCoordinator.verdict
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

    private func notifySuccess(for operation: RunningOperation) {
        switch operation {
        case .generation:
            sendNotification(title: "Your paper is ready", body: "The paper and mark scheme are in \(outputFolder.lastPathComponent).")
        case .modelPull:
            sendNotification(title: "Model ready", body: "\(selectedModel) is available in Ollama.")
        case .mlxSetup:
            sendNotification(title: "Apple MLX ready", body: "The selected model is ready for local generation.")
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
        case .mlxSetup:
            sendNotification(title: "Setting up Apple MLX", body: "Paper Creator is preparing the selected local model.")
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
        case .mlxSetup:
            sendNotification(title: "Apple MLX setup needs attention", body: message)
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
    case mlxSetup
}
