import Foundation

struct OllamaModelRecommendation: Identifiable, Hashable, Decodable {
    let id: String
    let minimumMemoryGB: Double
    let maximumMemoryGB: Double?
    let model: String
    let title: String
    let downloadSizeGB: Double
    let contextWindow: String
    let appContextWindow: String
    let validatedForFullMatrix: Bool
    let detail: String
    let qualityNote: String

    private enum CodingKeys: String, CodingKey {
        case id
        case minimumMemoryGB = "minimum_memory_gb"
        case maximumMemoryGB = "maximum_memory_gb"
        case model
        case title
        case downloadSizeGB = "download_size_gb"
        case contextWindow = "context_window"
        case appContextWindow = "app_context_window"
        case validatedForFullMatrix = "validated_for_full_matrix"
        case detail
        case qualityNote = "quality_note"
    }

    func supports(memoryGB: Double) -> Bool {
        memoryGB >= minimumMemoryGB
            && maximumMemoryGB.map { memoryGB < $0 } != false
    }

    func downloadResource(locale: Locale, includeContext: Bool = true) -> LocalizedStringResource {
        let size = downloadSizeGB.formatted(.number.locale(locale).precision(.fractionLength(1)))
        if !includeContext {
            return LocalizedStringResource("About \(size) GB", locale: locale)
        }
        return LocalizedStringResource("About \(size) GB download · \(appContextWindow) app context", locale: locale)
    }

    var detailResource: LocalizedStringResource {
        LocalizedStringResource(stringLiteral: detail)
    }

    var qualityNoteResource: LocalizedStringResource {
        LocalizedStringResource(stringLiteral: qualityNote)
    }
}

struct OllamaModelGuideDocument: Decodable {
    let schemaVersion: Int
    let researchedAt: String
    let defaultModel: String
    let otherModelWarning: String
    let tiers: [OllamaModelRecommendation]
    let sources: [URL]

    var otherModelWarningResource: LocalizedStringResource {
        LocalizedStringResource(stringLiteral: otherModelWarning)
    }

    private enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case researchedAt = "researched_at"
        case defaultModel = "default_model"
        case otherModelWarning = "other_model_warning"
        case tiers
        case sources
    }

    func recommendation(physicalMemoryBytes: UInt64) -> OllamaModelRecommendation {
        let memoryGB = Double(physicalMemoryBytes) / 1_073_741_824
        return tiers.first { $0.supports(memoryGB: memoryGB) }
            ?? tiers.last
            ?? Self.fallback.tiers[0]
    }

    static let fallback = OllamaModelGuideDocument(
        schemaVersion: 1,
        researchedAt: "2026-10-28",
        defaultModel: "gemma4:12b",
        otherModelWarning: "These suggestions concern available memory. The models have not passed a complete paper-quality review. Results may vary with another model or quantisation.",
        tiers: [
            OllamaModelRecommendation(
                id: "memory-compatible",
                minimumMemoryGB: 0,
                maximumMemoryGB: 16,
                model: "qwen2.5:7b",
                title: "Smaller local option",
                downloadSizeGB: 4.7,
                contextWindow: "32K",
                appContextWindow: "16K",
                validatedForFullMatrix: false,
                detail: "A smaller download for Macs with less than 16 GB of unified memory. Memory use also depends on the context and other running apps.",
                qualityNote: "Review the questions and marking guidance before use. Fitting in memory does not establish accuracy."
            ),
            OllamaModelRecommendation(
                id: "quality",
                minimumMemoryGB: 16,
                maximumMemoryGB: nil,
                model: "gemma4:12b",
                title: "Local option for 16 GB or more",
                downloadSizeGB: 8.0,
                contextWindow: "256K",
                appContextWindow: "16K",
                validatedForFullMatrix: false,
                detail: "For Macs with at least 16 GB of unified memory. Close other memory-heavy apps before generating. Paper quality is still under review.",
                qualityNote: "Download size does not include all memory needed during generation."
            ),
        ],
        sources: []
    )
}

enum OllamaModelGuide {
    static let document = (try? load(bundle: .main)) ?? .fallback

    static var currentRecommendation: OllamaModelRecommendation {
        document.recommendation(
            physicalMemoryBytes: ProcessInfo.processInfo.physicalMemory
        )
    }

    static func load(bundle: Bundle) throws -> OllamaModelGuideDocument {
        guard let url = bundle.url(
            forResource: "ollama-model-recommendations",
            withExtension: "json"
        ) else {
            throw OllamaModelGuideError.missingResource
        }
        return try decode(Data(contentsOf: url))
    }

    static func decode(_ data: Data) throws -> OllamaModelGuideDocument {
        let decoder = JSONDecoder()
        let document = try decoder.decode(OllamaModelGuideDocument.self, from: data)
        guard document.schemaVersion == 1, !document.tiers.isEmpty else {
            throw OllamaModelGuideError.unsupportedSchema
        }
        guard document.tiers.contains(where: { $0.model == document.defaultModel }) else {
            throw OllamaModelGuideError.invalidDefault
        }
        return document
    }
}

enum OllamaModelGuideError: LocalizedError {
    case missingResource
    case unsupportedSchema
    case invalidDefault

    var errorDescription: String? {
        switch self {
        case .missingResource:
            "The bundled Ollama model guide is missing."
        case .unsupportedSchema:
            "The bundled Ollama model guide has an unsupported format."
        case .invalidDefault:
            "The default Ollama model is not declared in the model guide."
        }
    }
}
