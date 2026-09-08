import Foundation

enum BoardStatus: String, Equatable {
    case ready
    case placeholder

    var title: String {
        switch self {
        case .ready: "Ready"
        case .placeholder: "Coming Soon"
        }
    }
}

enum AssessmentKind: String, Codable, Hashable {
    case fullPaper = "full-paper"
    case questionBank = "question-bank"

    var title: String {
        switch self {
        case .fullPaper: "Full Paper"
        case .questionBank: "Topic Practice"
        }
    }
}

struct PaperOption: Identifiable, Hashable {
    let id: String
    let title: String
    let detail: String
    let readiness: QualificationReadiness
    let assessmentKind: AssessmentKind
    let topicID: String?

    init(
        id: String,
        title: String,
        detail: String,
        readiness: QualificationReadiness,
        assessmentKind: AssessmentKind = .fullPaper,
        topicID: String? = nil
    ) {
        self.id = id
        self.title = title
        self.detail = detail
        self.readiness = readiness
        self.assessmentKind = assessmentKind
        self.topicID = topicID
    }
}

struct QualificationReadiness: Hashable {
    let engineeringValidated: Bool
    let visuallyCalibrated: Bool
    let empiricallyCalibrated: Bool

    var highestLevelTitle: String {
        if empiricallyCalibrated {
            return "Empirically calibrated"
        }
        if visuallyCalibrated {
            return "Visually calibrated"
        }
        if engineeringValidated {
            return "Engineering validated"
        }
        return "Not validated"
    }
}

enum GeneratorContentMode: String, Hashable, Codable {
    case deterministic
    case aiAssisted = "ai-assisted"

    var usesAI: Bool { self == .aiAssisted }

    var title: String {
        switch self {
        case .deterministic: "Built-in constrained generator"
        case .aiAssisted: "AI-assisted generator"
        }
    }

    var systemImage: String {
        switch self {
        case .deterministic: "checklist"
        case .aiAssisted: "sparkles"
        }
    }
}

struct ExamBoardOption: Identifiable, Hashable {
    let id: String
    let subjectID: String
    let subjectTitle: String
    let title: String
    let shortTitle: String
    let systemImage: String
    let status: BoardStatus
    let backendSubject: String?
    let papers: [PaperOption]
    let resourcePath: String
    let contentMode: GeneratorContentMode
    let supportedProviders: [AIProvider]

    var isReady: Bool { status == .ready && backendSubject != nil }
    var usesAI: Bool { contentMode.usesAI }
    var fullPapers: [PaperOption] {
        papers.filter { $0.assessmentKind == .fullPaper }
    }
    var questionBanks: [PaperOption] {
        papers.filter { $0.assessmentKind == .questionBank }
    }

    func supports(_ provider: AIProvider) -> Bool {
        supportedProviders.contains(provider)
    }
}

struct CatalogSubject: Identifiable, Hashable {
    let id: String
    let title: String
    let systemImage: String
    let boards: [ExamBoardOption]
}

enum ExamCatalog {
    static let subjects = (try? CatalogLoader.load(bundle: .main)) ?? []

    static var readyBoards: [ExamBoardOption] {
        subjects.flatMap(\.boards).filter(\.isReady)
    }

    static var defaultBoard: ExamBoardOption {
        board(id: "economics-edexcel-a") ?? readyBoards.first ?? ExamBoardOption(
            id: "unknown", subjectID: "unknown", subjectTitle: "Unknown", title: "Unknown",
            shortTitle: "Unknown", systemImage: "doc.text", status: .placeholder,
            backendSubject: nil, papers: [], resourcePath: "",
            contentMode: .deterministic, supportedProviders: []
        )
    }

    static func board(id: String) -> ExamBoardOption? {
        subjects.flatMap(\.boards).first { $0.id == id }
    }
}

enum CatalogLoader {
    static func load(bundle: Bundle) throws -> [CatalogSubject] {
        guard let catalogURL = bundle.url(forResource: "catalog", withExtension: "json") else {
            throw CatalogLoadError.missingResource("catalog.json")
        }
        guard let registryURL = bundle.url(forResource: "generator-registry", withExtension: "json") else {
            throw CatalogLoadError.missingResource("generator-registry.json")
        }
        return try load(
            catalogData: Data(contentsOf: catalogURL),
            registryData: Data(contentsOf: registryURL)
        )
    }

    static func load(catalogData: Data, registryData: Data) throws -> [CatalogSubject] {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let catalog = try decoder.decode(CatalogDocument.self, from: catalogData)
        let registry = try decoder.decode(GeneratorRegistryDocument.self, from: registryData)
        guard catalog.qualification == "A-Level", registry.qualification == "a-level" else {
            throw CatalogLoadError.qualificationMismatch
        }

        var implementations: [String: GeneratorFamilyDocument] = [:]
        for family in registry.families where family.advertised {
            let key = implementationKey(subject: family.appSubject, board: family.appBoard)
            guard implementations[key] == nil else {
                throw CatalogLoadError.duplicateImplementation(key)
            }
            guard !family.papers.isEmpty else {
                throw CatalogLoadError.emptyImplementation(key)
            }
            implementations[key] = family
        }

        var seenBoards: Set<String> = []
        let subjects = try catalog.subjects.map { subject -> CatalogSubject in
            let boards = try subject.boards.map { board -> ExamBoardOption in
                let key = implementationKey(subject: subject.id, board: board.id)
                guard seenBoards.insert(key).inserted else {
                    throw CatalogLoadError.duplicateBoard(key)
                }
                if let implementation = implementations.removeValue(forKey: key) {
                    return ExamBoardOption(
                        id: key,
                        subjectID: subject.id,
                        subjectTitle: subject.title,
                        title: board.title,
                        shortTitle: board.shortTitle ?? board.title,
                        systemImage: subject.systemImage,
                        status: .ready,
                        backendSubject: implementation.backendSubject,
                        papers: implementation.papers.map {
                            PaperOption(
                                id: $0.id,
                                title: $0.title,
                                detail: $0.detail,
                                readiness: $0.readiness,
                                assessmentKind: $0.assessmentKind,
                                topicID: $0.topicId
                            )
                        },
                        resourcePath: implementation.resourcePath,
                        contentMode: implementation.contentMode,
                        supportedProviders: try implementation.supportedProviders.map {
                            guard let provider = AIProvider(backendID: $0) else {
                                throw CatalogLoadError.unknownProvider($0)
                            }
                            return provider
                        }
                    )
                }
                return ExamBoardOption(
                    id: key,
                    subjectID: subject.id,
                    subjectTitle: subject.title,
                    title: board.title,
                    shortTitle: board.shortTitle ?? board.title,
                    systemImage: subject.systemImage,
                    status: .placeholder,
                    backendSubject: nil,
                    papers: [],
                    resourcePath: "",
                    contentMode: .deterministic,
                    supportedProviders: []
                )
            }
            return CatalogSubject(
                id: subject.id,
                title: subject.title,
                systemImage: subject.systemImage,
                boards: boards
            )
        }
        if let unmatched = implementations.keys.sorted().first {
            throw CatalogLoadError.implementationMissingFromCatalog(unmatched)
        }
        return subjects
    }

    private static func implementationKey(subject: String, board: String) -> String {
        "\(subject)-\(board)"
    }
}

private struct CatalogDocument: Decodable {
    let qualification: String
    let subjects: [CatalogSubjectDocument]
}

private struct CatalogSubjectDocument: Decodable {
    let id: String
    let title: String
    let systemImage: String
    let boards: [CatalogBoardDocument]
}

private struct CatalogBoardDocument: Decodable {
    let id: String
    let title: String
    let shortTitle: String?
}

private struct GeneratorRegistryDocument: Decodable {
    let qualification: String
    let families: [GeneratorFamilyDocument]
}

private struct GeneratorFamilyDocument: Decodable {
    let appSubject: String
    let appBoard: String
    let backendSubject: String
    let resourcePath: String
    let contentMode: GeneratorContentMode
    let supportedProviders: [String]
    let advertised: Bool
    let papers: [GeneratorPaperDocument]
}

private struct GeneratorPaperDocument: Decodable {
    let id: String
    let title: String
    let detail: String
    let checks: [String: Bool]
    let qualification: [String: QualificationLevelDocument]?
    let legacyGates: [String: Bool]
    let assessmentKind: AssessmentKind
    let topicId: String?

    var readiness: QualificationReadiness {
        if let qualification {
            return QualificationReadiness(
                engineeringValidated: qualification["engineering"]?.isPassed ?? false,
                visuallyCalibrated: qualification["visual"]?.isPassed ?? false,
                empiricallyCalibrated: qualification["empirical"]?.isPassed ?? false
            )
        }
        return QualificationReadiness(
            engineeringValidated: legacyGates["release"] ?? false,
            visuallyCalibrated: legacyGates["visual"] ?? false,
            empiricallyCalibrated: legacyGates["difficulty"] ?? false
        )
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case title
        case detail
        case checks
        case qualification
        case gates
        case assessmentKind
        case topicId
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        id = try values.decode(String.self, forKey: .id)
        title = try values.decode(String.self, forKey: .title)
        detail = try values.decode(String.self, forKey: .detail)
        checks = try values.decodeIfPresent([String: Bool].self, forKey: .checks) ?? [:]
        qualification = try values.decodeIfPresent(
            [String: QualificationLevelDocument].self,
            forKey: .qualification
        )
        legacyGates = try values.decodeIfPresent(
            [String: Bool].self,
            forKey: .gates
        ) ?? [:]
        assessmentKind = try values.decodeIfPresent(
            AssessmentKind.self,
            forKey: .assessmentKind
        ) ?? .fullPaper
        topicId = try values.decodeIfPresent(String.self, forKey: .topicId)
    }
}

private struct QualificationLevelDocument: Decodable {
    let state: String
    let evidence: [String]

    var isPassed: Bool {
        state == "passed" || state == "not_applicable"
    }
}

enum CatalogLoadError: LocalizedError {
    case missingResource(String)
    case qualificationMismatch
    case duplicateImplementation(String)
    case emptyImplementation(String)
    case duplicateBoard(String)
    case implementationMissingFromCatalog(String)
    case unknownProvider(String)

    var errorDescription: String? {
        switch self {
        case let .missingResource(name): "Missing bundled catalog resource: \(name)"
        case .qualificationMismatch: "Catalog and generator registry qualifications do not match."
        case let .duplicateImplementation(id): "Duplicate generator implementation: \(id)"
        case let .emptyImplementation(id): "Advertised generator has no papers: \(id)"
        case let .duplicateBoard(id): "Duplicate catalog board: \(id)"
        case let .implementationMissingFromCatalog(id): "Generator is missing from the app catalog: \(id)"
        case let .unknownProvider(id): "Generator registry has an unknown AI provider: \(id)"
        }
    }
}

enum SidebarItem: Hashable {
    case board(String)
    case benchmark
    case documents
    case history
}

enum HelpTopic: String, CaseIterable, Identifiable {
    case gettingStarted
    case choosingAModel
    case creatingAPaper
    case checkingQuality
    case privacy
    case troubleshooting
    case shortcuts

    var id: String { rawValue }

    var title: String {
        switch self {
        case .gettingStarted: "Getting Started"
        case .choosingAModel: "Choosing a Model"
        case .creatingAPaper: "Creating a Paper"
        case .checkingQuality: "Checking Quality"
        case .privacy: "Privacy"
        case .troubleshooting: "Troubleshooting"
        case .shortcuts: "Keyboard Shortcuts"
        }
    }

    var systemImage: String {
        switch self {
        case .gettingStarted: "hand.wave"
        case .choosingAModel: "cpu"
        case .creatingAPaper: "doc.badge.plus"
        case .checkingQuality: "checklist"
        case .privacy: "hand.raised"
        case .troubleshooting: "wrench.and.screwdriver"
        case .shortcuts: "keyboard"
        }
    }
}

enum AIProvider: String, CaseIterable, Identifiable {
    case ollama
    case openAI
    case anthropic
    case apple

    var id: String { rawValue }

    var title: String {
        switch self {
        case .ollama: "Ollama"
        case .openAI: "OpenAI"
        case .anthropic: "Anthropic"
        case .apple: "Apple MLX"
        }
    }

    var subtitle: String {
        switch self {
        case .ollama: "Runs locally via Ollama"
        case .openAI: "Uses an API key"
        case .anthropic: "Uses an API key"
        case .apple: "Runs locally on Apple Silicon"
        }
    }

    var sendsPromptsOffDevice: Bool {
        self == .openAI || self == .anthropic
    }

    var systemImage: String {
        switch self {
        case .ollama: "desktopcomputer"
        case .openAI: "sparkles"
        case .anthropic: "text.bubble"
        case .apple: "applelogo"
        }
    }

    var backendID: String {
        switch self {
        case .ollama: "ollama"
        case .openAI: "openai"
        case .anthropic: "anthropic"
        case .apple: "apple"
        }
    }

    init?(backendID: String) {
        switch backendID {
        case "ollama": self = .ollama
        case "openai": self = .openAI
        case "anthropic": self = .anthropic
        case "apple": self = .apple
        default: return nil
        }
    }
}

enum DistributionMode: String {
    case direct
    case appStore

    static var current: DistributionMode {
        let rawValue = Bundle.main.object(forInfoDictionaryKey: "DistributionMode") as? String
        return rawValue == "app-store" ? .appStore : .direct
    }

    var title: String {
        switch self {
        case .direct: "Direct Download"
        case .appStore: "App Store"
        }
    }

    var canManageOllama: Bool { self == .direct }
}

struct OllamaState: Equatable {
    var installed = false
    var running = false
    var command: String?
    var message = "Not checked"
}

struct ProgressEntry: Identifiable, Equatable {
    let id = UUID()
    let date = Date()
    let stage: String?
    let message: String
}

struct EstimateFactor: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let detail: String
    let impact: Double
}

struct GenerationEstimate: Equatable {
    let startedAt: Date
    var totalSeconds: TimeInterval
    var remainingSeconds: TimeInterval
    var confidence: Double
    var factors: [EstimateFactor]

    var etaDate: Date {
        Date().addingTimeInterval(max(0, remainingSeconds))
    }

    var remainingText: String {
        Self.formatDuration(remainingSeconds)
    }

    static func formatDuration(_ seconds: TimeInterval) -> String {
        let clamped = max(0, Int(seconds.rounded()))
        if clamped < 60 {
            return "\(clamped)s"
        }
        let minutes = clamped / 60
        let remainder = clamped % 60
        return remainder == 0 ? "\(minutes)m" : "\(minutes)m \(remainder)s"
    }
}

struct BenchmarkSample: Identifiable, Equatable {
    let id = UUID()
    let elapsed: Double
    let cpuLoad: Double
    let cpuThroughputMBs: Double
    let memoryAvailableGB: Double
    let memoryPressurePercent: Double
    let swapUsedGB: Double
    let diskWriteMBs: Double
    let diskReadMBs: Double
    let diskFreeGB: Double
    let smallFileMS: Double
    let networkLatencyMS: Double?
    let networkDownloadMBs: Double?
    let ollamaLatencyMS: Double?
    let thermalSpeedLimitPercent: Double?
    let pdfPagesPerSecond: Double

    var networkLatencyDisplayMS: Double {
        networkLatencyMS ?? 0
    }

    var thermalSpeedLimitDisplayPercent: Double {
        thermalSpeedLimitPercent ?? 100
    }
}

struct BenchmarkMetric: Identifiable, Equatable {
    let id = UUID()
    let name: String
    let value: Double?
    let unit: String?
    let detail: String?
    let score: Double?

    var displayValue: String {
        if let value {
            let formatted = value.formatted(.number.precision(.fractionLength(0...2)))
            if let unit, !unit.isEmpty {
                return "\(formatted) \(unit)"
            }
            return formatted
        }
        return detail ?? "Unknown"
    }
}

struct BenchmarkVerdict: Equatable {
    let score: Double
    let verdict: String
    let detail: String
}

struct GeneratedFile: Identifiable, Codable, Equatable {
    let id: UUID
    let role: String
    let url: URL
    let createdAt: Date
    let subject: String
    let paper: String

    init(
        id: UUID = UUID(),
        role: String,
        url: URL,
        createdAt: Date = Date(),
        subject: String = "",
        paper: String = ""
    ) {
        self.id = id
        self.role = role
        self.url = url
        self.createdAt = createdAt
        self.subject = subject
        self.paper = paper
    }

    var exists: Bool {
        FileManager.default.fileExists(atPath: url.path)
    }

    var title: String {
        switch role {
        case "question_paper": "Question Paper"
        case "source_booklet": "Source Booklet"
        case "mark_scheme": "Mark Scheme"
        case "assessment_package": "Assessment Package"
        case "package_manifest": "Package Manifest"
        case "preliminary_material": "Preliminary Material"
        case "electronic_answer_document": "Electronic Answer Document"
        case "skeleton_program": "Skeleton Program"
        case "data_file": "Practice Data"
        default: role.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    var paperDescription: String {
        [subject, paper].filter { !$0.isEmpty }.joined(separator: " · ")
    }
}

enum SavedGenerationMode: String, Equatable {
    case preview = "Preview"
    case live = "Live"
    case unknown = "Unknown"
}

struct SavedPackageIdentity: Equatable {
    let subject: String?
    let paper: String?
    let seed: Int?
    let jobID: String?
    let generatorID: String?
    let generatorVersion: String?
    let formID: String?
}

enum AuthoringProvenanceKind: Equatable {
    case reviewedFixedOnly
    case aiAuthoredOnly
    case mixed
    case unreviewed
    case unknown
}

struct AuthoringProvenanceSummary: Equatable {
    let kind: AuthoringProvenanceKind
    let reviewedFixedItems: Int?
    let aiAuthoredItems: Int?
    let aiAuthoredStemItems: Int?
    let unreviewedItems: Int?
    let unknownItems: Int?

    static let unknown = AuthoringProvenanceSummary(
        kind: .unknown,
        reviewedFixedItems: nil,
        aiAuthoredItems: nil,
        aiAuthoredStemItems: nil,
        unreviewedItems: nil,
        unknownItems: nil
    )
}

enum GenerationQualityState: Equatable {
    case passed
    case pending
    case preview
    case atCreation
    case unknown

    var title: String {
        switch self {
        case .passed: "Passed"
        case .pending: "Pending"
        case .preview: "Preview"
        case .atCreation: "At creation"
        case .unknown: "Unknown"
        }
    }
}

struct GenerationQualityPresentation: Equatable {
    let originalityState: GenerationQualityState
    let originalityDetail: String
    let referenceDemandState: GenerationQualityState
    let referenceDemandDetail: String
    let pathEvidenceState: GenerationQualityState
    let pathEvidenceDetail: String
    let diagnosticLines: [String]
}

struct GenerationQualityReport: Equatable {
    let identity: SavedPackageIdentity
    let savedMode: SavedGenerationMode
    let itemCount: Int
    let fingerprintsVerified: Bool
    let historicComparisons: Int
    let noveltyPassed: Bool?
    let nearestSimilarity: Double?
    let pdfCount: Int
    let engineeringValidated: Bool?
    let visuallyCalibrated: Bool?
    let empiricallyCalibrated: Bool?
    let referenceDemandPassed: Bool?
    let referenceDemandItems: Int
    let referenceDemandDocuments: Int
    let referenceDemandMaxDistance: Double?
    let referenceDemandExtractionCoverage: Double?
    let referenceDemandFailedChecks: [String]?
    let difficultyReviewedItems: Int
    let difficultyApprovedItems: Int?
    let difficultyReviewCoverage: Double?
    let difficultyReasoningFitItems: Int?
    let difficultyContextFitItems: Int?
    let difficultyShortcutFitItems: Int?
    let candidatePathEvidencePassed: Bool?
    let authoringProvenance: AuthoringProvenanceSummary

    static func load(from url: URL) -> GenerationQualityReport? {
        guard let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let evidence = root["evidence"] as? [String: Any],
              let assessment = evidence["assessment_validation"] as? [String: Any],
              let novelty = evidence["novelty_validation"] as? [String: Any],
              let outputs = root["outputs"] as? [String: Any] else {
            return nil
        }
        let nearest = novelty["nearest_match"] as? [String: Any]
        let request = root["request"] as? [String: Any]
        let generator = root["generator"] as? [String: Any]
        let qualification = evidence["qualification_levels"] as? [String: Any]
        let referenceDemand = assessment["reference_demand"] as? [String: Any]
        let distances = referenceDemand?["gated_distances"] as? [String: Double]
        let itemReview = referenceDemand?["item_review_evidence"] as? [String: Any]
        let pathEvidence = assessment["path_evidence"] as? [String: Any]
        let assessmentItemCount = assessment["item_count"] as? Int ?? 0
        let mode: SavedGenerationMode
        if let preview = request?["preview_mode"] as? Bool {
            mode = preview ? .preview : .live
        } else {
            mode = .unknown
        }
        let pdfCount = outputs.values.compactMap { value -> [String: Any]? in
            value as? [String: Any]
        }.filter { $0["pdf_validation"] is [String: Any] }.count
        return GenerationQualityReport(
            identity: SavedPackageIdentity(
                subject: Self.nonEmpty(request?["subject"] as? String),
                paper: Self.nonEmpty(request?["paper"] as? String),
                seed: request?["seed"] as? Int,
                jobID: Self.nonEmpty(root["job_id"] as? String),
                generatorID: Self.nonEmpty(generator?["id"] as? String),
                generatorVersion: Self.nonEmpty(generator?["version"] as? String),
                formID: Self.nonEmpty(assessment["form_id"] as? String)
            ),
            savedMode: mode,
            itemCount: assessmentItemCount,
            fingerprintsVerified: assessment["fingerprints_verified"] as? Bool ?? false,
            historicComparisons: novelty["historic_comparisons"] as? Int ?? 0,
            noveltyPassed: novelty["passed"] as? Bool,
            nearestSimilarity: nearest?["similarity"] as? Double,
            pdfCount: pdfCount,
            engineeringValidated: qualification?["engineering_validated"] as? Bool,
            visuallyCalibrated: qualification?["visually_calibrated"] as? Bool,
            empiricallyCalibrated: qualification?["empirically_calibrated"] as? Bool,
            referenceDemandPassed: referenceDemand?["passed"] as? Bool,
            referenceDemandItems: referenceDemand?["items_checked"] as? Int ?? 0,
            referenceDemandDocuments: referenceDemand?["source_document_count"] as? Int ?? 0,
            referenceDemandMaxDistance: distances?.values.max(),
            referenceDemandExtractionCoverage: referenceDemand?["extraction_coverage"] as? Double,
            referenceDemandFailedChecks: referenceDemand?["failed_checks"] as? [String],
            difficultyReviewedItems: itemReview?["reviewed_items"] as? Int ?? 0,
            difficultyApprovedItems: itemReview?["approved_items"] as? Int,
            difficultyReviewCoverage: itemReview?["coverage"] as? Double,
            difficultyReasoningFitItems: itemReview?["reasoning_range_fit"] as? Int,
            difficultyContextFitItems: itemReview?["context_fit"] as? Int,
            difficultyShortcutFitItems: itemReview?["shortcut_resistant"] as? Int,
            candidatePathEvidencePassed: pathEvidence?["passed"] as? Bool,
            authoringProvenance: Self.decodeAuthoringProvenance(
                assessment["authoring_provenance"] as? [String: Any],
                expectedItems: assessmentItemCount
            )
        )
    }

    private static func decodeAuthoringProvenance(
        _ value: [String: Any]?,
        expectedItems: Int
    ) -> AuthoringProvenanceSummary {
        guard let value,
              value["schema_version"] as? Int == 1,
              let items = value["items"] as? Int,
              let fixed = value["reviewed_fixed_items"] as? Int,
              let authored = value["ai_authored_items"] as? Int,
              let stems = value["ai_authored_stem_items"] as? Int,
              let unreviewed = value["unreviewed_or_builtin_items"] as? Int,
              let unknown = value["unknown_items"] as? Int,
              items >= 0,
              items == expectedItems,
              [fixed, authored, stems, unreviewed, unknown].allSatisfy({ $0 >= 0 }),
              fixed + authored + stems + unreviewed + unknown == items
        else { return .unknown }
        let kind: AuthoringProvenanceKind
        if unknown > 0 {
            kind = .unknown
        } else if fixed == items {
            kind = .reviewedFixedOnly
        } else if authored + stems == items {
            kind = .aiAuthoredOnly
        } else if unreviewed == items {
            kind = .unreviewed
        } else {
            kind = .mixed
        }
        return AuthoringProvenanceSummary(
            kind: kind,
            reviewedFixedItems: fixed,
            aiAuthoredItems: authored,
            aiAuthoredStemItems: stems,
            unreviewedItems: unreviewed,
            unknownItems: unknown
        )
    }

    private static func nonEmpty(_ value: String?) -> String? {
        guard let value = value?.trimmingCharacters(in: .whitespacesAndNewlines),
              !value.isEmpty else { return nil }
        return value
    }
}

enum GenerationQualityPolicy {
    static func presentation(
        for report: GenerationQualityReport?
    ) -> GenerationQualityPresentation {
        guard let report else {
            return GenerationQualityPresentation(
                originalityState: .atCreation,
                originalityDetail: "Originality evidence is created with a saved package.",
                referenceDemandState: .atCreation,
                referenceDemandDetail: "Reference-demand evidence is created with a saved package.",
                pathEvidenceState: .unknown,
                pathEvidenceDetail: "Candidate-path evidence is not available.",
                diagnosticLines: ["Saved package evidence: None"]
            )
        }
        let originalityState: GenerationQualityState
        let originalityDetail: String
        switch report.savedMode {
        case .preview:
            originalityState = .preview
            originalityDetail = "Preview history comparison is skipped; authorship and originality are not reviewed."
        case .live where report.noveltyPassed == true:
            originalityState = switch report.authoringProvenance.kind {
            case .unreviewed, .unknown: .unknown
            case .reviewedFixedOnly, .aiAuthoredOnly, .mixed: .passed
            }
            originalityDetail = "Saved-package similarity checks passed. " + provenanceDetail(report)
        case .live where report.noveltyPassed == false:
            originalityState = .pending
            originalityDetail = "Saved-package similarity checks did not pass. " + provenanceDetail(report)
        case .live, .unknown:
            originalityState = .unknown
            originalityDetail = "Saved-package originality evidence is incomplete. " + provenanceDetail(report)
        }

        let coverageText = report.difficultyReviewCoverage.map {
            "\(report.difficultyReviewedItems) of \(report.referenceDemandItems) items (\($0.formatted(.percent.precision(.fractionLength(0)))))"
        } ?? "unknown item coverage"
        let validItemReview = validatedItemReview(report)
        let completeLiveReview = report.savedMode == .live
            && validItemReview
            && report.referenceDemandPassed == true
            && report.difficultyReviewCoverage == 1.0
            && report.difficultyApprovedItems == report.referenceDemandItems
            && report.difficultyReasoningFitItems == report.difficultyReviewedItems
            && report.difficultyContextFitItems == report.difficultyReviewedItems
            && report.difficultyShortcutFitItems == report.difficultyReviewedItems
            && report.referenceDemandFailedChecks?.isEmpty == true
        let referenceState: GenerationQualityState
        let referenceDetail: String
        if report.savedMode == .preview {
            referenceState = .preview
            referenceDetail = "Aggregate profile fit is preview-only; validated item depth covers \(coverageText)."
        } else if completeLiveReview {
            referenceState = .passed
            referenceDetail = "Aggregate profile fit passed and validated item depth covers \(coverageText)."
        } else if report.savedMode == .unknown
                    || report.referenceDemandPassed == nil
                    || !validItemReview {
            referenceState = .unknown
            referenceDetail = "Saved profile or item-review coverage is missing; item depth is unknown."
        } else {
            referenceState = .pending
            referenceDetail = "Profile fit or validated item coverage is incomplete: \(coverageText)."
        }
        let pathState: GenerationQualityState = switch report.candidatePathEvidencePassed {
        case true: .passed
        case false: .pending
        case nil: .unknown
        }
        let pathDetail = report.candidatePathEvidencePassed.map {
            $0 ? "Candidate-path evidence passed." : "Candidate-path evidence needs review."
        } ?? "Candidate-path and focused-bank evidence is not present in this package."
        let identity = [report.identity.subject, report.identity.paper]
            .compactMap { $0 }
            .joined(separator: " / ")
        return GenerationQualityPresentation(
            originalityState: originalityState,
            originalityDetail: originalityDetail,
            referenceDemandState: referenceState,
            referenceDemandDetail: referenceDetail,
            pathEvidenceState: pathState,
            pathEvidenceDetail: pathDetail,
            diagnosticLines: [
                "Saved package: \(identity.isEmpty ? "Unknown" : identity)",
                "Saved seed: \(report.identity.seed.map(String.init) ?? "Unknown")",
                "Saved job: \(report.identity.jobID ?? "Unknown")",
                "Saved mode: \(report.savedMode.rawValue)",
                "Saved form: \(report.identity.formID ?? "Unknown")",
                "Saved generator: \(report.identity.generatorID ?? "Unknown") \(report.identity.generatorVersion ?? "")".trimmingCharacters(in: .whitespaces),
                "Originality (\(originalityState.title)): \(originalityDetail)",
                "Reference demand: \(referenceDetail)",
                "Candidate paths: \(pathDetail)",
            ]
        )
    }

    private static func provenanceDetail(_ report: GenerationQualityReport) -> String {
        let provenance = report.authoringProvenance
        switch provenance.kind {
        case .reviewedFixedOnly:
            return "All content follows reviewed fixed contracts; no AI-authored wording is recorded."
        case .aiAuthoredOnly:
            return "The package records AI-authored content; review coverage remains a separate check."
        case .mixed:
            if let stems = provenance.aiAuthoredStemItems, stems > 0 {
                return "Mixed provenance includes \(stems) stem edit(s) and reviewed fixed contracts; a stem edit is not full-question authorship."
            }
            return "The package records mixed authored and reviewed fixed content."
        case .unreviewed:
            return "The package records built-in or unreviewed content, not reviewed originality."
        case .unknown:
            return "Authoring provenance is unknown."
        }
    }

    private static func validatedItemReview(_ report: GenerationQualityReport) -> Bool {
        guard report.itemCount > 0,
              report.referenceDemandItems == report.itemCount,
              let approved = report.difficultyApprovedItems,
              let coverage = report.difficultyReviewCoverage,
              report.referenceDemandFailedChecks != nil,
              report.difficultyReviewedItems >= 0,
              approved >= 0,
              approved <= report.difficultyReviewedItems,
              report.difficultyReviewedItems <= report.referenceDemandItems,
              (0.0 ... 1.0).contains(coverage),
              let reasoningFit = report.difficultyReasoningFitItems,
              reasoningFit >= 0,
              reasoningFit <= report.difficultyReviewedItems,
              let contextFit = report.difficultyContextFitItems,
              contextFit >= 0,
              contextFit <= report.difficultyReviewedItems,
              let shortcutFit = report.difficultyShortcutFitItems,
              shortcutFit >= 0,
              shortcutFit <= report.difficultyReviewedItems
        else { return false }
        let expectedCoverage = Double(report.difficultyReviewedItems)
            / Double(report.referenceDemandItems)
        return abs(coverage - expectedCoverage) < 0.000_001
    }
}

enum BackendEvent: Equatable {
    case hello(protocolVersion: Int, backendVersion: String, capabilities: [String])
    case progress(stage: String?, message: String, progress: Double?)
    case file(role: String, path: String)
    case done(message: String)
    case error(message: String, code: String? = nil)
    case models([String], message: String?)
    case ollamaStatus(installed: Bool, running: Bool, command: String?, message: String?)
    case benchmarkMetric(BenchmarkMetric)
    case benchmarkSample(BenchmarkSample)
    case benchmarkDone(BenchmarkVerdict)

    init(jsonLine: String) throws {
        let data = Data(jsonLine.utf8)
        let payload = try JSONDecoder().decode(BackendEventPayload.self, from: data)

        switch payload.type {
        case "hello":
            self = .hello(
                protocolVersion: payload.protocolVersion ?? 0,
                backendVersion: payload.backendVersion ?? "Unknown",
                capabilities: payload.capabilities ?? []
            )
        case "progress":
            self = .progress(stage: payload.stage, message: payload.message ?? "", progress: payload.progress)
        case "file":
            self = .file(role: payload.role ?? "file", path: payload.path ?? "")
        case "done":
            self = .done(message: payload.message ?? "Done")
        case "error":
            self = .error(
                message: payload.message ?? "Unknown backend error",
                code: payload.code
            )
        case "models":
            self = .models(payload.models ?? [], message: payload.message)
        case "ollama_status":
            self = .ollamaStatus(
                installed: payload.installed ?? false,
                running: payload.running ?? false,
                command: payload.command,
                message: payload.message
            )
        case "benchmark_metric":
            self = .benchmarkMetric(
                BenchmarkMetric(
                    name: payload.name ?? "Metric",
                    value: payload.value,
                    unit: payload.unit,
                    detail: payload.detail ?? payload.message,
                    score: payload.score
                )
            )
        case "benchmark_sample":
            self = .benchmarkSample(
                BenchmarkSample(
                    elapsed: payload.elapsed ?? 0,
                    cpuLoad: payload.cpuLoad ?? 0,
                    cpuThroughputMBs: payload.cpuMBs ?? 0,
                    memoryAvailableGB: payload.memoryAvailableGB ?? 0,
                    memoryPressurePercent: payload.memoryPressurePercent ?? 0,
                    swapUsedGB: payload.swapUsedGB ?? 0,
                    diskWriteMBs: payload.diskWriteMBs ?? 0,
                    diskReadMBs: payload.diskReadMBs ?? 0,
                    diskFreeGB: payload.diskFreeGB ?? 0,
                    smallFileMS: payload.smallFileMS ?? 0,
                    networkLatencyMS: payload.networkLatencyMS,
                    networkDownloadMBs: payload.networkDownloadMBs,
                    ollamaLatencyMS: payload.ollamaLatencyMS,
                    thermalSpeedLimitPercent: payload.thermalSpeedLimitPercent,
                    pdfPagesPerSecond: payload.pdfPagesPerSecond ?? 0
                )
            )
        case "benchmark_done":
            self = .benchmarkDone(
                BenchmarkVerdict(
                    score: payload.score ?? 0,
                    verdict: payload.verdict ?? "Unknown",
                    detail: payload.detail ?? payload.message ?? ""
                )
            )
        default:
            self = .progress(stage: payload.type, message: payload.message ?? payload.type, progress: payload.progress)
        }
    }
}

enum MLXSetupPolicy {
    static func requiresSetup(
        provider: AIProvider,
        model: String,
        preparedModels: Set<String>,
        usesAI: Bool,
        dryRun: Bool
    ) -> Bool {
        guard provider == .apple, usesAI, !dryRun else { return false }
        let model = model.trimmingCharacters(in: .whitespacesAndNewlines)
        return !model.isEmpty && !preparedModels.contains(model)
    }
}

struct MLXRecoveryState {
    private(set) var needsSetupAfterGeneration = false

    mutating func beginGeneration() {
        needsSetupAfterGeneration = false
    }

    mutating func requestSetup() {
        needsSetupAfterGeneration = true
    }

    mutating func cancel() {
        needsSetupAfterGeneration = false
    }

    mutating func consumeSetupRequest() -> Bool {
        defer { needsSetupAfterGeneration = false }
        return needsSetupAfterGeneration
    }
}

private struct BackendEventPayload: Decodable {
    let protocolVersion: Int?
    let type: String
    let eventID: Int?
    let timestamp: String?
    let jobID: String?
    let backendVersion: String?
    let capabilities: [String]?
    let stage: String?
    let message: String?
    let code: String?
    let role: String?
    let path: String?
    let page: Int?
    let sourcePDF: String?
    let progress: Double?
    let models: [String]?
    let installed: Bool?
    let running: Bool?
    let command: String?
    let name: String?
    let value: Double?
    let unit: String?
    let detail: String?
    let score: Double?
    let elapsed: Double?
    let cpuLoad: Double?
    let cpuMBs: Double?
    let memoryAvailableGB: Double?
    let memoryPressurePercent: Double?
    let swapUsedGB: Double?
    let diskWriteMBs: Double?
    let diskReadMBs: Double?
    let diskFreeGB: Double?
    let smallFileMS: Double?
    let networkLatencyMS: Double?
    let networkDownloadMBs: Double?
    let ollamaLatencyMS: Double?
    let thermalSpeedLimitPercent: Double?
    let pdfPagesPerSecond: Double?
    let verdict: String?

    enum CodingKeys: String, CodingKey {
        case protocolVersion = "protocol"
        case type
        case eventID = "event_id"
        case timestamp
        case jobID = "job_id"
        case backendVersion = "backend_version"
        case capabilities
        case stage
        case message
        case code
        case role
        case path
        case page
        case sourcePDF = "source_pdf"
        case progress
        case models
        case installed
        case running
        case command
        case name
        case value
        case unit
        case detail
        case score
        case elapsed
        case cpuLoad = "cpu_load"
        case cpuMBs = "cpu_mb_s"
        case memoryAvailableGB = "memory_available_gb"
        case memoryPressurePercent = "memory_pressure_percent"
        case swapUsedGB = "swap_used_gb"
        case diskWriteMBs = "disk_write_mb_s"
        case diskReadMBs = "disk_read_mb_s"
        case diskFreeGB = "disk_free_gb"
        case smallFileMS = "small_file_ms"
        case networkLatencyMS = "network_latency_ms"
        case networkDownloadMBs = "network_download_mb_s"
        case ollamaLatencyMS = "ollama_latency_ms"
        case thermalSpeedLimitPercent = "thermal_speed_limit_percent"
        case pdfPagesPerSecond = "pdf_pages_per_s"
        case verdict
    }
}
