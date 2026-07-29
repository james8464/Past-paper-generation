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

struct PaperOption: Identifiable, Hashable {
    let id: String
    let title: String
    let detail: String
    let readiness: PaperReadiness
}

struct PaperReadiness: Hashable {
    let difficultyVerified: Bool
    let visuallyCalibrated: Bool
    let releaseReady: Bool
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
        let subjects = try catalog.subjects.compactMap { subject -> CatalogSubject? in
            let boards = try subject.boards.compactMap { board -> ExamBoardOption? in
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
                                readiness: PaperReadiness(
                                    difficultyVerified: $0.gates["difficulty"] ?? false,
                                    visuallyCalibrated: $0.gates["visual"] ?? false,
                                    releaseReady: $0.gates["release"] ?? false
                                )
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
                return nil
            }
            guard !boards.isEmpty else { return nil }
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
    let gates: [String: Bool]
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

enum BackendEvent: Equatable {
    case hello(protocolVersion: Int, backendVersion: String, capabilities: [String])
    case progress(stage: String?, message: String, progress: Double?)
    case file(role: String, path: String)
    case done(message: String)
    case error(message: String)
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
            self = .error(message: payload.message ?? "Unknown backend error")
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
