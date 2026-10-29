// Coordinate user actions across catalogue, model, generation and document state.

import AppKit
import Combine
import Foundation
import UniformTypeIdentifiers
@preconcurrency import UserNotifications

@MainActor
final class ApplicationCoordinator: ObservableObject {
    let settingsStore: SettingsStore
    let catalogStore: CatalogStore
    let modelCoordinator: ModelCoordinator
    let benchmarkCoordinator: BenchmarkCoordinator
    let recentDocumentStore: RecentDocumentStore
    let generationCoordinator: GenerationCoordinator
    let settingsPresentation = SettingsActionPresentation()

    @Published var selectedModel = AppDefaults.ollamaModel
    @Published var aiProvider: AIProvider = .ollama
    @Published var ollamaURL = AppDefaults.ollamaURL
    @Published var outputFolder = AppDefaults.defaultOutputFolder()
    @Published var dryRun = false
    @Published private var activeRun: BackendRun?
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

    private let backend: any BackendRunning
    private let defaults: UserDefaults
    private let outputFolderBookmark: (URL) throws -> Data
    private let notificationCenter = UNUserNotificationCenter.current()
    private var ollamaRefreshRevision = UUID()
    private var etaTimer: AnyCancellable?
    private var pendingHostedProvider: AIProvider?
    private var preparedMLXModels: Set<String> = []
    private var mlxRecoveryState = MLXRecoveryState()
    private var securityScopedOutputFolder: URL?
    // Finished artifacts outlive their process so Documents can keep showing
    // the last result. During a run, its collection is the only mutable owner.
    private var completedDocuments = RunDocuments()

    var isRunning: Bool { activeRun != nil }

    var hasCommandBlockingPresentation: Bool {
        showWelcome || showHelp || showError || showHostedAIConsent
            || showMLXSetupConfirmation
    }

    private var activeOperation: RunningOperation { activeRun?.intent.operation ?? .none }

    private var currentGenerationFileIDs: Set<UUID> {
        get { activeRun?.documents.fileIDs ?? completedDocuments.fileIDs }
        set {
            if activeRun != nil { activeRun?.documents.fileIDs = newValue }
            else { completedDocuments.fileIDs = newValue }
        }
    }

    private var generationRetryTarget: GenerationRetryTarget {
        GenerationRetryTarget(
            boardID: selectedBoardID, paperID: selectedPaperID, provider: aiProvider,
            model: activeModelName, dryRun: dryRun, output: outputFolder.standardizedFileURL,
            seed: pendingGenerationSeed
        )
    }

    private var presentationLanguage: String {
        defaults.string(forKey: "interfaceLanguage") ?? "system"
    }

    var currentGenerationFiles: [GeneratedFile] {
        generatedFiles.filter { currentGenerationFileIDs.contains($0.id) }
    }

    func beginDocumentCollection() {
        guard activeRun == nil else { return }
        completedDocuments = RunDocuments(
            subject: "\(selectedBoard.subjectTitle) \(selectedBoard.shortTitle)",
            paper: selectedPaper.title
        )
    }

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
        generationBlockerResource.map { InterfaceText.resolve($0, language: presentationLanguage) }
    }

    var generationBlockerResource: LocalizedStringResource? {
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
            if openAIAPIKey.isEmpty, let error = settingsStore.credentialFailure(for: SecretAccount.openAIAPIKey) { return "\(error.message(language: presentationLanguage))" }
            return openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "Enter an OpenAI API key in Settings." : nil
        case .anthropic:
            if !hasHostedAIConsent { return "Review and accept the hosted AI disclosure in Settings." }
            if anthropicAPIKey.isEmpty, let error = settingsStore.credentialFailure(for: SecretAccount.anthropicAPIKey) { return "\(error.message(language: presentationLanguage))" }
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
            ? "Apple MLX support is included with Keldin."
            : "Keldin will install Apple MLX into its managed environment if needed."
        return "\(runtimeDetail) It will then download and prepare \(model). "
            + "Models can use several gigabytes of storage. Generation remains on this Mac, "
            + "and setup does not require Terminal or an administrator password."
    }

    init(
        defaults: UserDefaults = .standard,
        secrets: SecretStoring = KeychainSecretStore(),
        historyDirectory: URL? = nil,
        backend: any BackendRunning = BackendClient(),
        outputFolderBookmark: @escaping (URL) throws -> Data = { url in
            try url.bookmarkData(options: .withSecurityScope, includingResourceValuesForKeys: nil, relativeTo: nil)
        },
        historyRecordRemover: @escaping (URL) throws -> Void = { url in
            try FileManager.default.removeItem(at: url)
        }
    ) {
        self.defaults = defaults
        self.backend = backend
        self.outputFolderBookmark = outputFolderBookmark
        let settings = SettingsStore(defaults: defaults, secrets: secrets)
        let recents = RecentDocumentStore(
            directory: historyDirectory ?? AppDefaults.jobHistoryFolder(),
            retentionLimit: settings.historyRetentionLimit,
            defaults: defaults,
            recordRemover: historyRecordRemover
        )
        settingsStore = settings
        catalogStore = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        modelCoordinator = ModelCoordinator()
        benchmarkCoordinator = BenchmarkCoordinator(backend: backend)
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
        // Invalid saved usage stays untouched; the creation action reports it.
        _ = try? savedFrenchFamilies()
        benchmarkCoordinator.outputFolder = outputFolder
        if !showError, let message = settings.secretFailureMessage(language: presentationLanguage) { setError(message) }
    }

    func refreshOllama(presentation: SettingsActionPresentation? = nil) {
        guard !isRunning, !benchmarkCoordinator.isRunning, !isRefreshingOllama else { return }
        isRefreshingOllama = true
        status = "Checking Ollama"
        let revision = ollamaRefreshRevision
        Task {
            defer { isRefreshingOllama = false }
            guard ollamaRefreshRevision == revision else { return }
            do {
                let statusEvents = try await backend.collect(arguments: ["ollama-status"])
                guard ollamaRefreshRevision == revision else { return }
                statusEvents.forEach { apply($0, errorPresentation: presentation) }
                let modelEvents = try await backend.collect(arguments: ["list-models"])
                guard ollamaRefreshRevision == revision else { return }
                modelEvents.forEach { apply($0, errorPresentation: presentation) }
            } catch {
                guard ollamaRefreshRevision == revision else { return }
                setError(error.localizedDescription, presentation: presentation)
            }
        }
    }

    func importPreviousAppData(presentation: SettingsActionPresentation? = nil) {
        guard !isRunning else { return }
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.message = String(localized: "Choose the previous app's folder inside Library/Application Support. Existing Keldin files will be kept.")
        guard panel.runModal() == .OK, let source = panel.url else { return }
        let scoped = source.startAccessingSecurityScopedResource()
        defer { if scoped { source.stopAccessingSecurityScopedResource() } }
        do {
            try KeldinMigration.importData(from: source, defaults: defaults)
            restoreRecentDocuments(presentation: presentation)
            status = String(localized: "Previous app data imported. Restart Keldin to load imported settings.")
        } catch {
            setError(error.localizedDescription, presentation: presentation)
        }
    }

    var frenchReferencesFolder: URL {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support")
        return support.appendingPathComponent("Keldin/French References", isDirectory: true)
    }

    var hasFrenchReferences: Bool {
        FileManager.default.fileExists(atPath: frenchReferencesFolder.appendingPathComponent("references.sqlite").path)
    }

    func prepareFrenchReferences() {
        startFrenchOperation(
            arguments: ["prepare-french-references", "--output", frenchReferencesFolder.path],
            seed: nil,
            statusMessage: String(localized: "Preparing French references")
        )
    }

    func deleteFrenchReferences() {
        guard !isRunning else { return }
        do {
            if FileManager.default.fileExists(atPath: frenchReferencesFolder.path) {
                try FileManager.default.removeItem(at: frenchReferencesFolder)
            }
            status = String(localized: "French references deleted")
        } catch {
            setError(error.localizedDescription)
        }
    }

    func generateFrenchPaper(largePrint: Bool) {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        let excludedFamilies: [Int]
        do {
            excludedFamilies = try savedFrenchFamilies()
        } catch {
            setError(error.localizedDescription)
            return
        }
        guard excludedFamilies.count < 5 else {
            pendingGenerationSeed = nil
            setError("Les cinq familles disponibles sont trop proches des sujets précédents. Aucun nouveau sujet n'a été créé.")
            return
        }
        let seed = pendingGenerationSeed ?? Int.random(in: 1 ... Int(Int32.max))
        pendingGenerationSeed = seed
        let request = FrenchAssessmentRequest(
            referenceIndex: frenchReferencesFolder.appendingPathComponent("references.sqlite"),
            output: distributionMode == .appStore ? AppDefaults.appStoreWorkingFolder() : outputFolder,
            seed: seed, largePrint: largePrint, excludedFamilies: excludedFamilies
        )
        startFrenchOperation(arguments: request.arguments, seed: seed)
    }

    /// Catalogue use survives the configurable job-history limit and output moves.
    func savedFrenchFamilies() throws -> [Int] {
        guard !defaults.bool(forKey: KeldinMigration.frenchFamilyImportFailedKey) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        let ids = FrenchAssessmentRequest.familyIDs
        var remembered: [Int] = []
        if let raw = defaults.object(forKey: AppStorageKey.frenchSavedFamilyIDs) {
            guard let values = raw as? [String], values.count <= ids.count else {
                throw CocoaError(.fileReadCorruptFile)
            }
            remembered = values.compactMap { ids.firstIndex(of: $0) }
            guard remembered.count == values.count else { throw CocoaError(.fileReadCorruptFile) }
        }
        let observed = try FrenchAssessmentRequest.savedFamilies(in: recentDocumentStore.records)
        let families = Set(remembered + observed).sorted()
        defaults.set(families.map { ids[$0] }, forKey: AppStorageKey.frenchSavedFamilyIDs)
        return families
    }

    func recordFrenchReview(
        reviewer: String,
        decision: FrenchReviewDecision,
        scores: [String: Int],
        notes: String
    ) -> FrenchReviewSubmissionOutcome {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return .cancelled }
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedContentTypes = [.json]
        panel.message = String(localized: "Choose the manifest.json file from the reviewed assessment bundle.")
        guard panel.runModal() == .OK, let manifest = panel.url else { return .cancelled }
        guard manifest.lastPathComponent == "manifest.json" else {
            setError(String(localized: "Choose the bundle's manifest.json file."))
            return .rejected
        }
        let request = FrenchReviewRequest(
            manifest: manifest,
            reviewer: reviewer,
            decision: decision,
            scores: scores,
            notes: notes
        )
        return submitFrenchReview(request)
    }

    func submitFrenchReview(_ request: FrenchReviewRequest) -> FrenchReviewSubmissionOutcome {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return .cancelled }
        guard request.manifest.lastPathComponent == "manifest.json" else {
            setError(String(localized: "Choose the bundle's manifest.json file."))
            return .rejected
        }
        guard request.isComplete else {
            setError(String(localized: "Complete every review score and add review notes."))
            return .rejected
        }
        startFrenchOperation(
            arguments: request.arguments,
            seed: nil,
            intent: .reviewRecord,
            statusMessage: String(localized: "Recording teacher review")
        )
        return isRunning ? .submitted : .rejected
    }

    private func startFrenchOperation(
        arguments: [String],
        seed: Int?,
        intent: BackendRunIntent = .referencePreparation,
        statusMessage: String = String(localized: "Preparing French assessment")
    ) {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        progressEntries.removeAll()
        lastQualityReport = nil
        status = statusMessage
        generationProgress = nil
        let session = beginRunSession(
            intent: seed == nil ? intent : .paper,
            documents: RunDocuments(
                frameworkID: FrenchAssessmentRequest.assessmentID,
                subject: "Baccalauréat général · NSI", paper: "Partie écrite · 2027"
            ),
            model: FrenchAssessmentRequest.modelID
        )
        do {
            if let seed {
                let job = GenerationJobRecord(
                    configuration: GenerationConfiguration(
                        boardID: "fr-national-nsi", paperID: "written-2027", provider: "application-owned",
                        model: FrenchAssessmentRequest.modelID, seed: seed, dryRun: false,
                        educationSystem: "fr-national", assessmentID: FrenchAssessmentRequest.assessmentID,
                        documentLanguage: "fr-FR"
                    ),
                    provenance: GenerationProvenance(
                        appVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "development",
                        provider: "application-owned", model: FrenchAssessmentRequest.modelID
                    ), state: .pending, artifacts: [],
                    qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
                )
                try generationCoordinator.begin(job)
                activeRun?.ownedJobID = job.id
            }
            let process = try backend.run(arguments: arguments, environment: [:]) { [weak self] event in
                self?.apply(event, from: session)
            } onFinish: { [weak self] result in
                self?.finishRun(result, from: session)
            }
            if activeRun?.id == session { activeRun?.process = process }
        } catch {
            finishRun(.failure(error), from: session)
        }
    }

    func chooseOutputFolder() { chooseOutputFolder(presentation: nil) }

    func chooseOutputFolder(presentation: SettingsActionPresentation?) {
        guard !isRunning else { return }
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.directoryURL = outputFolder

        if panel.runModal() == .OK, let url = panel.url {
            setOutputFolder(url, presentation: presentation)
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

    func selectAIProvider(_ provider: AIProvider, presentation: SettingsActionPresentation? = nil) {
        guard !isRunning else { return }
        guard provider != aiProvider else { return }
        if provider.sendsPromptsOffDevice && !hasHostedAIConsent {
            if let presentation {
                presentation.requestConsent(for: provider)
                return
            }
            pendingHostedProvider = provider
            showHostedAIConsent = true
            return
        }
        aiProvider = provider
        modelCoordinator.provider = provider
        persistSettings(presentation: presentation)
    }

    func acceptHostedAIConsent() {
        guard !isRunning else { return }
        defaults.set(true, forKey: AppStorageKey.hostedAIConsentAccepted)
        if let provider = pendingHostedProvider {
            aiProvider = provider
            modelCoordinator.provider = provider
        }
        pendingHostedProvider = nil
        showHostedAIConsent = false
        persistSettings()
    }

    func acceptHostedAIConsent(for provider: AIProvider, presentation: SettingsActionPresentation) {
        guard !isRunning else {
            presentation.reportError(InterfaceText.resolve("Generation is already running.", language: presentationLanguage))
            return
        }
        defaults.set(true, forKey: AppStorageKey.hostedAIConsentAccepted)
        aiProvider = provider
        modelCoordinator.provider = provider
        persistSettings(presentation: presentation)
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
                  ["ollama", "application-owned"].contains(record.configuration.provider) else { return }
            if record.configuration.provider == "ollama" {
                selectedModel = record.configuration.model
            }
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
        let settingsSaved = persistSettings(
            includeCredentials: !dryRun && selectedBoard.usesAI && aiProvider.sendsPromptsOffDevice
        )
        if !settingsSaved, !dryRun, selectedBoard.usesAI,
           let account = activeSecretAccount,
           settingsStore.credentialFailure(for: account) != nil { return }

        progressEntries.removeAll()
        lastQualityReport = nil
        mlxRecoveryState.beginGeneration()
        status = "Starting"
        generationProgress = 0.02
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
            "KELDIN_GENERATED_ON": Self.generationDateFormatter.string(from: Date()),
            "KELDIN_JOB_ID": UUID().uuidString,
            "KELDIN_APP_VERSION": Bundle.main.object(
                forInfoDictionaryKey: "CFBundleShortVersionString"
            ) as? String ?? "development",
            "KELDIN_APP_BUILD": Bundle.main.object(
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
            backendEnvironment["KELDIN_API_KEY"] = openAIAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)
        case .anthropic:
            backendEnvironment["KELDIN_API_KEY"] = anthropicAPIKey.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        if dryRun {
            arguments.append("--dry-run")
        }

        let session = beginRunSession(
            intent: .paper,
            documents: RunDocuments(
                subject: "\(selectedBoard.subjectTitle) \(selectedBoard.shortTitle)", paper: selectedPaper.title
            ),
            model: activeModelName
        )
        do {
            try generationCoordinator.begin(record)
            activeRun?.ownedJobID = record.id
            let process = try backend.run(arguments: arguments, environment: backendEnvironment) { [weak self] event in
                self?.apply(event, from: session)
            } onFinish: { [weak self] result in
                self?.finishRun(result, from: session)
            }
            if activeRun?.id == session { activeRun?.process = process }
            notifyStarted(for: .generation)
        } catch {
            finishRun(.failure(error), from: session)
        }
    }

    func confirmMLXSetup() {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        let model = appleModel.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !model.isEmpty else {
            showMLXSetupConfirmation = false
            setError("Choose an Apple MLX model in Settings, then try again.")
            return
        }

        showMLXSetupConfirmation = false
        status = "Setting up Apple MLX"
        generationProgress = 0.05
        progressEntries.removeAll()
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil

        let session = beginRunSession(intent: .mlxSetup, model: model, retryTarget: generationRetryTarget)
        do {
            let process = try backend.run(
                arguments: ["setup-mlx", "--model", model],
                environment: ["HF_HOME": AppDefaults.mlxCacheFolder().path]
            ) { [weak self] event in
                self?.apply(event, from: session)
            } onFinish: { [weak self] result in
                self?.finishRun(result, from: session)
            }
            if activeRun?.id == session { activeRun?.process = process }
            notifyStarted(for: .mlxSetup)
        } catch {
            finishRun(.failure(error), from: session)
        }
    }

    func cancelMLXSetup() {
        showMLXSetupConfirmation = false
        status = "Ready"
    }

    func cancelGeneration() {
        guard var run = activeRun else { return }
        ollamaRefreshRevision = UUID()
        run.phase = .cancelling
        let operation = run.intent.operation
        if let jobID = run.ownedJobID { try? generationCoordinator.cancel(expectedJobID: jobID) }
        mlxRecoveryState.cancel()
        // MLX setup keeps ownership until its helper exits. Other operations can
        // release the UI immediately, but their queued callbacks no longer own it.
        if run.intent == .mlxSetup { activeRun = run }
        else {
            completedDocuments = run.documents
            activeRun = nil
        }
        run.process?.terminate()
        if run.intent == .mlxSetup {
            status = "Cancelling Apple MLX setup"
            progressEntries.append(
                ProgressEntry(stage: "cancel", message: "Cancelling Apple MLX setup…")
            )
            return
        }
        status = operation == .modelPull
            ? InterfaceText.resolve("Model download cancelled.", language: presentationLanguage)
            : "Cancelled"
        generationProgress = nil
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil
        let message: String
        switch operation {
        case .modelPull:
            message = InterfaceText.resolve("Model download cancelled.", language: presentationLanguage)
        case .generation:
            message = "Generation cancelled."
        case .none, .mlxSetup:
            message = InterfaceText.resolve("Cancelled", language: presentationLanguage)
        }
        progressEntries.append(ProgressEntry(stage: "cancel", message: message))
    }

    func pullSelectedModel() -> ModelDownloadRequest? {
        guard canRequestModelDownload else { return nil }
        modelToPull = selectedModel
        return requestPullModel()
    }

    func requestPullModel() -> ModelDownloadRequest? {
        guard canRequestModelDownload,
              !modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
        return ModelDownloadRequest(model: modelToPull.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    func confirmPullModel(_ request: ModelDownloadRequest, presentation: SettingsActionPresentation? = nil) {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        guard distributionMode.canManageOllama else {
            setError("The App Store build can detect Ollama, but cannot install or pull models.", presentation: presentation)
            return
        }

        let model = request.model.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !model.isEmpty else { return }
        status = "Pulling model"
        generationProgress = 0.05
        progressEntries.removeAll()
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil

        let session = beginRunSession(intent: .modelPull, model: model, errorPresentation: presentation)
        do {
            let process = try backend.run(arguments: ["pull-model", "--model", model], environment: [:]) { [weak self] event in
                self?.apply(event, from: session)
            } onFinish: { [weak self] result in
                self?.finishRun(result, from: session)
            }
            if activeRun?.id == session { activeRun?.process = process }
            notifyStarted(for: .modelPull, model: model)
        } catch {
            finishRun(.failure(error), from: session)
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

    func saveAISettings(presentation: SettingsActionPresentation? = nil) {
        persistSettings(presentation: presentation)
    }

    func removeGeneratedFile(_ file: GeneratedFile) {
        let path = file.url.standardizedFileURL.path
        var hidden = hiddenRecentPaths
        hidden.insert(path)
        defaults.set(hidden.sorted(), forKey: AppStorageKey.hiddenRecentDocumentPaths)
        generatedFiles.removeAll { $0.url.standardizedFileURL.path == path }
        persistRecentDocuments()
    }

    func removeHistory(_ record: GenerationJobRecord) {
        do {
            try recentDocumentStore.remove(record)
        } catch {
            setError(InterfaceText.resolve("Couldn't remove this history item. \(error.localizedDescription)", language: presentationLanguage))
        }
    }

    func setHistoryRetentionLimit(_ value: Int, presentation: SettingsActionPresentation? = nil) {
        settingsStore.historyRetentionLimit = max(1, value)
        _ = saveSettingsAndReportSecretFailure(presentation: presentation)
        recentDocumentStore.updateRetentionLimit(value)
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

    func useRecommendedOllamaModel(presentation: SettingsActionPresentation? = nil) {
        selectedModel = ollamaRecommendation.model
        modelToPull = ollamaRecommendation.model
        saveAISettings(presentation: presentation)
    }

    var canRequestModelDownload: Bool {
        distributionMode.canManageOllama && !isRunning && !benchmarkCoordinator.isRunning
    }

    func requestRecommendedOllamaModel() -> ModelDownloadRequest? {
        guard canRequestModelDownload else { return nil }
        modelToPull = ollamaRecommendation.model
        return requestPullModel()
    }

    func copyDiagnosticSummary() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(diagnosticSummary, forType: .string)
        status = "Diagnostics copied"
    }

    var diagnosticSummary: String {
        let generationMode = selectedBoard.usesAI
            ? "\(selectedBoard.contentMode.title), \(aiProvider.title), \(activeModelName)"
            : selectedBoard.contentMode.title
        return ([
            "Keldin Diagnostics",
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
        ] + qualityDiagnosticLines + progressEntries.suffix(6).map {
            "\($0.stage ?? "activity"): \($0.message)"
        }).joined(separator: "\n")
    }

    var qualityDiagnosticLines: [String] {
        GenerationQualityPolicy.presentation(for: lastQualityReport).diagnosticLines
    }

    func setNotificationsEnabled(_ enabled: Bool, presentation: SettingsActionPresentation? = nil) {
        notificationsEnabled = enabled
        settingsStore.notificationsEnabled = enabled
        saveSettingsAndReportSecretFailure(presentation: presentation)
        if enabled {
            requestNotificationAuthorization()
        }
    }

    func setDryRun(_ enabled: Bool, presentation: SettingsActionPresentation? = nil) {
        guard !isRunning else { return }
        dryRun = enabled
        settingsStore.dryRun = enabled
        saveSettingsAndReportSecretFailure(presentation: presentation)
    }

    func startBenchmark() {
        guard !isRunning, !benchmarkCoordinator.isRunning else { return }
        ollamaRefreshRevision = UUID()
        benchmarkCoordinator.start(generationIsRunning: isRunning)
        status = "Benchmarking"
        sidebarSelection = .benchmark
    }

    func cancelBenchmark() {
        ollamaRefreshRevision = UUID()
        status = "Benchmark cancelled"
        benchmarkCoordinator.cancel()
    }

    @discardableResult
    private func persistSettings(includeCredentials: Bool = true, presentation: SettingsActionPresentation? = nil) -> Bool {
        settingsStore.provider = aiProvider
        settingsStore.ollamaModel = selectedModel
        settingsStore.openAIModel = openAIModel
        settingsStore.anthropicModel = anthropicModel
        settingsStore.appleModel = appleModel
        settingsStore.dryRun = dryRun
        settingsStore.notificationsEnabled = notificationsEnabled
        settingsStore.openAIAPIKey = openAIAPIKey
        settingsStore.anthropicAPIKey = anthropicAPIKey
        let saved = saveSettingsAndReportSecretFailure(includeCredentials: includeCredentials, presentation: presentation)
        defaults.set(outputFolder.path, forKey: AppStorageKey.outputFolderPath)
        return saved
    }

    @discardableResult
    func saveSettingsAndReportSecretFailure(includeCredentials: Bool = false, presentation: SettingsActionPresentation? = nil) -> Bool {
        let saved = settingsStore.save(includeCredentials: includeCredentials)
        if !saved, let message = settingsStore.secretFailureMessage(language: presentationLanguage) { setError(message, presentation: presentation) }
        return saved
    }

    private var activeSecretAccount: String? {
        switch aiProvider {
        case .openAI: SecretAccount.openAIAPIKey
        case .anthropic: SecretAccount.anthropicAPIKey
        case .ollama, .apple: nil
        }
    }

    private static let generationDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    func setOutputFolder(_ url: URL, presentation: SettingsActionPresentation? = nil) {
        benchmarkCoordinator.outputFolder = url
        securityScopedOutputFolder?.stopAccessingSecurityScopedResource()
        securityScopedOutputFolder = url.startAccessingSecurityScopedResource() ? url : nil
        outputFolder = url
        defaults.set(url.path, forKey: AppStorageKey.outputFolderPath)
        do {
            let bookmark = try outputFolderBookmark(url)
            defaults.set(bookmark, forKey: AppStorageKey.outputFolderBookmark)
        } catch {
            defaults.removeObject(forKey: AppStorageKey.outputFolderBookmark)
            setError(
                InterfaceText.resolve("Keldin couldn't save access to this folder. Choose it again to keep access after restarting.", language: presentationLanguage),
                presentation: presentation
            )
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
        generatedFiles.first { $0.role == role }
    }

    private func beginRunSession(
        intent: BackendRunIntent, documents: RunDocuments? = nil, model: String,
        retryTarget: GenerationRetryTarget? = nil, errorPresentation: SettingsActionPresentation? = nil
    ) -> UUID {
        // A discovery request started before this operation must remain obsolete
        // even if the operation finishes before that request returns.
        ollamaRefreshRevision = UUID()
        let run = BackendRun(
            intent: intent, documents: documents ?? completedDocuments, model: model, retryTarget: retryTarget,
            errorPresentation: errorPresentation
        )
        activeRun = run
        return run.id
    }

    private func apply(_ event: BackendEvent, from session: UUID) {
        guard activeRun?.id == session, activeRun?.phase == .running else { return }
        apply(event)
    }

    func apply(_ event: BackendEvent, errorPresentation: SettingsActionPresentation? = nil) {
        if let jobID = activeRun?.ownedJobID {
            guard generationCoordinator.activeJob?.id == jobID else { return }
            generationCoordinator.receive(event, expectedJobID: jobID)
        }
        switch event {
        case let .hello(protocolVersion, _, _):
            if protocolVersion != 2 {
                setError("The generation service uses an unsupported protocol version.", presentation: activeRun?.errorPresentation ?? errorPresentation)
            }
        case let .progress(stage, message, progress):
            status = GenerationPresentation.progress(message, language: presentationLanguage)
            generationProgress = progress ?? generationProgress
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: stage, message: message))
        case let .file(role, path):
            // Setup and model-management output cannot become paper artifacts.
            if let intent = activeRun?.intent, intent == .mlxSetup || intent == .modelPull { return }
            var hidden = hiddenRecentPaths
            hidden.remove(URL(fileURLWithPath: path).standardizedFileURL.path)
            defaults.set(hidden.sorted(), forKey: AppStorageKey.hiddenRecentDocumentPaths)
            let file = GeneratedFile(
                role: role,
                url: URL(fileURLWithPath: path),
                subject: activeRun?.documents.subject ?? completedDocuments.subject
                    ?? "\(selectedBoard.subjectTitle) \(selectedBoard.shortTitle)",
                paper: activeRun?.documents.paper ?? completedDocuments.paper ?? selectedPaper.title
            )
            // UK exports can replace an existing filename. Give each new
            // revision a fresh identity so previews reload the actual output.
            generatedFiles.removeAll { $0.url == file.url }
            generatedFiles.insert(file, at: 0)
            generatedFiles = Array(generatedFiles.prefix(60))
            currentGenerationFileIDs.insert(file.id)
            if role == "package_manifest" {
                lastQualityReport = GenerationQualityReport.load(from: file.url)
            }
        case let .done(message):
            status = GenerationPresentation.completion(message, language: presentationLanguage)
            generationProgress = 1.0
            updateGenerationEstimate()
            progressEntries.append(ProgressEntry(stage: "done", message: message))
        case let .error(message, code):
            guard activeRun?.phase != .cancelling else { return }
            activeRun?.backendErrorMessage = message
            if code == "mlx_setup_required", activeRun?.intent == .paper {
                let model = activeRun?.model ?? ""
                preparedMLXModels.remove(model)
                defaults.set(preparedMLXModels.sorted(), forKey: AppStorageKey.preparedMLXModels)
                mlxRecoveryState.requestSetup()
                status = "Apple MLX setup required"
                return
            }
            setError(message, presentation: activeRun?.errorPresentation ?? errorPresentation)
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

    private func finishRun(_ result: Result<Int32, Error>, from session: UUID) {
        guard let run = activeRun, run.id == session else { return }
        completedDocuments = run.documents
        activeRun = nil
        etaTimer?.cancel()
        etaTimer = nil
        generationEstimate = nil
        switch run.intent {
        case .paper:
            finishGeneration(result, run: run)
        case .referencePreparation, .reviewRecord:
            finishMaintenance(result, run: run)
        case .modelPull:
            finishModelPull(result, run: run)
        case .mlxSetup:
            finishMLXSetup(result, run: run)
        }
    }

    private func finishMaintenance(_ result: Result<Int32, Error>, run: BackendRun) {
        switch result {
        case .success(0) where run.backendErrorMessage == nil:
            generationProgress = 1
            persistRecentDocuments()
        case let .success(code):
            if run.backendErrorMessage == nil {
                setError(InterfaceText.resolve("The operation stopped (exit code \(String(code))). Try again.", language: presentationLanguage))
            }
        case let .failure(error):
            setError(error.localizedDescription)
        }
    }

    private func finishGeneration(_ result: Result<Int32, Error>, run: BackendRun) {
        let operation = run.intent.operation
        if mlxRecoveryState.consumeSetupRequest() {
            generationProgress = nil
            generationEstimate = nil
            status = "Apple MLX setup required"
            showMLXSetupConfirmation = true
            return
        }

        switch result {
        case let .success(code):
            if code == 0 && run.backendErrorMessage == nil {
                guard let jobID = run.ownedJobID else { return }
                guard generationCoordinator.activeJob?.id == jobID else {
                    setError(String(localized: "The paper was created, but its history could not be saved or verified."))
                    pendingGenerationSeed = nil
                    return
                }
                do {
                    try moveGeneratedFilesToOutputFolderIfNeeded(frameworkID: run.documents.frameworkID)
                } catch {
                    let message = "The paper was created, but it could not be saved to the selected folder: \(error.localizedDescription)"
                    setError(message)
                    notifyFailure(for: operation, message: message)
                    try? generationCoordinator.fail(message: message, expectedJobID: jobID)
                    pendingGenerationSeed = nil
                    return
                }
                status = status == "Starting" ? "Done" : status
                generationProgress = 1.0
                generationEstimate = nil
                do {
                    try generationCoordinator.complete(expectedJobID: jobID, artifacts: currentGenerationFiles)
                    if run.documents.frameworkID == FrenchAssessmentRequest.assessmentID {
                        _ = try savedFrenchFamilies()
                    }
                } catch {
                    let message = String(localized: "The paper was created, but its history could not be saved or verified.")
                    setError(message)
                    notifyFailure(for: operation, message: message)
                    try? generationCoordinator.fail(message: message, expectedJobID: jobID)
                    pendingGenerationSeed = nil
                    return
                }
                persistRecentDocuments()
                if let questionPaper = currentGenerationFiles.first(where: { $0.role == "question_paper" }) {
                    previewedFileID = questionPaper.id
                    sidebarSelection = .documents
                }
                pendingGenerationSeed = nil
                notifySuccess(for: operation)
            } else {
                let message = run.backendErrorMessage.map {
                    GenerationPresentation.error($0, language: presentationLanguage)
                } ?? "Generation failed without a backend error message. Refresh Ollama, check the selected model, then try again. Backend exited with code \(code)."
                if run.backendErrorMessage == nil {
                    setError(message)
                    notifyFailure(for: operation, message: message)
                }
                if let jobID = run.ownedJobID {
                    try? generationCoordinator.fail(message: message, expectedJobID: jobID)
                }
                pendingGenerationSeed = nil
            }
        case let .failure(error):
            setError(error.localizedDescription)
            notifyFailure(for: operation, message: error.localizedDescription)
            if let jobID = run.ownedJobID {
                try? generationCoordinator.fail(message: error.localizedDescription, expectedJobID: jobID)
            }
            pendingGenerationSeed = nil
        }
    }

    private func finishModelPull(_ result: Result<Int32, Error>, run: BackendRun) {
        let model = run.model
        generationProgress = nil
        generationEstimate = nil
        etaTimer?.cancel()
        etaTimer = nil
        // A model download owns no generation job, even when an earlier job's
        // cancellation could not be written to history.
        switch result {
        case .success(0) where run.backendErrorMessage == nil:
            selectedModel = model
            defaults.set(model, forKey: AppStorageKey.ollamaModel)
            status = InterfaceText.resolve("Done", language: presentationLanguage)
            generationProgress = 1
            notifySuccess(for: .modelPull)
            refreshOllama(presentation: run.errorPresentation)
        case let .success(code):
            if run.backendErrorMessage == nil {
                let message = InterfaceText.resolve("Ollama stopped the model download (exit code \(String(code))). Check Ollama, then try again.", language: presentationLanguage)
                setError(message, presentation: run.errorPresentation)
                notifyFailure(for: .modelPull, message: message)
            }
        case let .failure(error):
            setError(error.localizedDescription, presentation: run.errorPresentation)
            notifyFailure(for: .modelPull, message: error.localizedDescription)
        }
    }

    private func finishMLXSetup(_ result: Result<Int32, Error>, run: BackendRun) {
        let model = run.model
        generationProgress = nil

        if run.phase == .cancelling {
            status = "Cancelled"
            progressEntries.append(
                ProgressEntry(stage: "cancel", message: "Apple MLX setup cancelled.")
            )
            return
        }

        switch result {
        case let .success(code) where code == 0 && run.backendErrorMessage == nil:
            preparedMLXModels.insert(model)
            defaults.set(preparedMLXModels.sorted(), forKey: AppStorageKey.preparedMLXModels)
            status = "Apple MLX is ready"
            notifySuccess(for: .mlxSetup)
            // Never turn a finished setup into a request for a different target.
            // A later selection stays intact and can be generated explicitly.
            if let target = run.retryTarget, target == generationRetryTarget { generate() }
        case let .success(code):
            if run.backendErrorMessage == nil {
                let message = "Apple MLX setup could not finish (code \(code)). Check your connection and storage, then try Setup Again."
                setError(message)
                notifyFailure(for: .mlxSetup, message: message)
            }
        case let .failure(error):
            setError(error.localizedDescription)
            notifyFailure(for: .mlxSetup, message: error.localizedDescription)
        }
    }

    private func moveGeneratedFilesToOutputFolderIfNeeded(frameworkID: String?) throws {
        guard distributionMode == .appStore else { return }
        // Save review records beside the user-selected manifest so they stay
        // with that assessment instead of the app's temporary working files.
        guard currentGenerationFiles.contains(where: { $0.role != "teacher_review" }) else { return }
        let workingFolder = AppDefaults.appStoreWorkingFolder().standardizedFileURL
        let destinationFolder = outputFolder.standardizedFileURL
        guard workingFolder != destinationFolder else { return }

        if frameworkID == FrenchAssessmentRequest.assessmentID,
           let first = currentGenerationFiles.first {
            let source = first.url.deletingLastPathComponent().standardizedFileURL
            guard source.deletingLastPathComponent() == workingFolder,
                  currentGenerationFiles.allSatisfy({ $0.url.deletingLastPathComponent().standardizedFileURL == source }) else {
                throw CocoaError(.fileReadInvalidFileName)
            }
            let destination = try AssessmentBundleExporter.export(source: source, to: destinationFolder)
            generatedFiles = generatedFiles.map { file in
                guard currentGenerationFileIDs.contains(file.id) else { return file }
                return GeneratedFile(
                    id: file.id, role: file.role,
                    url: destination.appendingPathComponent(file.url.lastPathComponent),
                    createdAt: file.createdAt, subject: file.subject, paper: file.paper
                )
            }
            return
        }

        try publishUKGeneratedFiles(from: workingFolder, to: destinationFolder)
    }

    func publishUKGeneratedFiles(
        from workingFolder: URL,
        to destinationFolder: URL,
        publisher: UKArtifactPublisher = UKArtifactPublisher()
    ) throws {
        let files = currentGenerationFiles
        guard !files.isEmpty else { return }
        guard files.allSatisfy({
            $0.url.deletingLastPathComponent().standardizedFileURL == workingFolder.standardizedFileURL
        }) else {
            throw CocoaError(.fileReadInvalidFileName)
        }
        let published = try publisher.publish(files, to: destinationFolder)
        let byID = Dictionary(uniqueKeysWithValues: published.map { ($0.id, $0) })
        generatedFiles = generatedFiles.map { file in
            byID[file.id] ?? file
        }
    }

    private func restoreRecentDocuments(presentation: SettingsActionPresentation? = nil) {
        do {
            try recentDocumentStore.load()
        } catch {
            setError(InterfaceText.resolve("Couldn't load generation history. \(error.localizedDescription)", language: presentationLanguage), presentation: presentation)
            return
        }
        let jobArtifacts = recentDocumentStore.records.flatMap(\.artifacts)
        if !jobArtifacts.isEmpty {
            generatedFiles = latestDocumentVersions(jobArtifacts)
            return
        }
        guard let data = defaults.data(forKey: AppStorageKey.recentDocuments),
              let documents = try? JSONDecoder().decode(
                [GeneratedFile].self,
                from: data
              ) else {
            return
        }
        generatedFiles = latestDocumentVersions(documents.map { KeldinMigration.relocatedArtifact($0, defaults: defaults) })
    }

    private func latestDocumentVersions(_ documents: [GeneratedFile]) -> [GeneratedFile] {
        var seen = Set<URL>()
        let hidden = hiddenRecentPaths
        return Array(documents.filter {
            !hidden.contains($0.url.standardizedFileURL.path)
                && seen.insert($0.url.standardizedFileURL).inserted
        }.prefix(60))
    }

    private var hiddenRecentPaths: Set<String> {
        Set(defaults.stringArray(forKey: AppStorageKey.hiddenRecentDocumentPaths) ?? [])
    }

    private func persistRecentDocuments() {
        guard let data = try? JSONEncoder().encode(generatedFiles) else { return }
        defaults.set(data, forKey: AppStorageKey.recentDocuments)
    }

    private func setError(_ message: String, presentation: SettingsActionPresentation? = nil) {
        let displayMessage = GenerationPresentation.error(message, language: presentationLanguage)
        if let presentation { presentation.reportError(displayMessage) }
        else {
            errorMessage = displayMessage
            showError = true
        }
        status = InterfaceText.resolve("Error", language: presentationLanguage)
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
            sendNotification(.paperReady(folder: outputFolder.lastPathComponent))
        case .modelPull:
            sendNotification(.modelReady(model: selectedModel))
        case .mlxSetup:
            sendNotification(.mlxReady)
        case .none:
            break
        }
    }

    private func notifyStarted(for operation: RunningOperation, model: String? = nil) {
        switch operation {
        case .generation:
            sendNotification(.paperStarted(subject: selectedBoard.subjectTitle, paper: selectedPaper.title))
        case .modelPull:
            sendNotification(.modelStarted(model: model ?? modelToPull))
        case .mlxSetup:
            sendNotification(.mlxStarted)
        case .none:
            break
        }
    }

    private func notifyFailure(for operation: RunningOperation, message: String) {
        switch operation {
        case .generation:
            sendNotification(.paperFailed(detail: message))
        case .modelPull:
            sendNotification(.modelFailed(detail: message))
        case .mlxSetup:
            sendNotification(.mlxFailed(detail: message))
        case .none:
            break
        }
    }

    private func requestNotificationAuthorization() {
        Task {
            _ = try? await notificationCenter.requestAuthorization(options: [.alert, .sound])
        }
    }

    private func sendNotification(_ event: WorkNotification) {
        let copy = event.content(language: presentationLanguage)
        sendNotification(title: copy.title, body: copy.body)
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

private enum BackendRunIntent {
    case paper, referencePreparation, reviewRecord, modelPull, mlxSetup

    var operation: RunningOperation {
        switch self {
        case .paper: .generation
        case .referencePreparation, .reviewRecord: .none
        case .modelPull: .modelPull
        case .mlxSetup: .mlxSetup
        }
    }
}

private struct RunDocuments {
    let frameworkID: String?
    let subject: String?
    let paper: String?
    var fileIDs = Set<UUID>()

    init(frameworkID: String? = nil, subject: String? = nil, paper: String? = nil) {
        self.frameworkID = frameworkID
        self.subject = subject
        self.paper = paper
    }
}

private struct BackendRun {
    let id = UUID()
    let intent: BackendRunIntent
    var documents: RunDocuments
    let model: String
    let retryTarget: GenerationRetryTarget?
    let errorPresentation: SettingsActionPresentation?
    var ownedJobID: UUID?
    var process: Process?
    var phase = BackendRunPhase.running
    var backendErrorMessage: String?
}

private struct GenerationRetryTarget: Equatable {
    let boardID: String
    let paperID: String
    let provider: AIProvider
    let model: String
    let dryRun: Bool
    let output: URL
    let seed: Int?
}

private enum BackendRunPhase {
    case running, cancelling
}
