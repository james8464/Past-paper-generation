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

    var isReady: Bool { status == .ready && backendSubject != nil }
}

struct CatalogSubject: Identifiable, Hashable {
    let id: String
    let title: String
    let systemImage: String
    let boards: [ExamBoardOption]
}

enum ExamCatalog {
    static let subjects: [CatalogSubject] = [
        subject("economics", "Economics", "chart.line.uptrend.xyaxis", [
            placeholderBoard("economics-aqa", "AQA"),
            readyBoard(
                subjectID: "economics",
                subjectTitle: "Economics",
                systemImage: "chart.line.uptrend.xyaxis",
                boardID: "edexcel-a",
                title: "Edexcel A",
                backendSubject: "economics",
                papers: [
                    PaperOption(id: "1", title: "Paper 1", detail: "Markets and business behaviour"),
                    PaperOption(id: "2", title: "Paper 2", detail: "National and global economy"),
                    PaperOption(id: "3", title: "Paper 3", detail: "Microeconomics and macroeconomics"),
                ]
            ),
            placeholderBoard("economics-ocr", "OCR"),
            placeholderBoard("economics-cambridge-international", "Cambridge International"),
        ]),
        subject("computer-science", "Computer Science", "cpu", [
            readyBoard(
                subjectID: "computer-science",
                subjectTitle: "Computer Science",
                systemImage: "cpu",
                boardID: "aqa",
                title: "AQA",
                backendSubject: "computer_science",
                papers: [
                    PaperOption(id: "2", title: "Paper 2", detail: "AQA A-level Computer Science 7517/2"),
                ]
            ),
            placeholderBoard("computer-science-ocr", "OCR"),
            placeholderBoard("computer-science-cambridge-international", "Cambridge International"),
        ]),
        subject("biology", "Biology", "leaf", [
            placeholderBoard("biology-aqa", "AQA", subjectID: "biology", subjectTitle: "Biology", systemImage: "leaf"),
            placeholderBoard("biology-edexcel-a", "Edexcel Biology A (SNAB)", subjectID: "biology", subjectTitle: "Biology", systemImage: "leaf"),
        ]),
        subject("chemistry", "Chemistry", "flask", [
            placeholderBoard("chemistry-aqa", "AQA", subjectID: "chemistry", subjectTitle: "Chemistry", systemImage: "flask"),
            placeholderBoard("chemistry-cambridge-international", "Cambridge International", subjectID: "chemistry", subjectTitle: "Chemistry", systemImage: "flask"),
            placeholderBoard("chemistry-edexcel", "Edexcel", subjectID: "chemistry", subjectTitle: "Chemistry", systemImage: "flask"),
            placeholderBoard("chemistry-ocr-a", "OCR A", subjectID: "chemistry", subjectTitle: "Chemistry", systemImage: "flask"),
        ]),
        placeholderSubject("mathematics", "Mathematics", "x.squareroot", ["AQA", "Edexcel", "OCR A", "Cambridge International"]),
        subject("physics", "Physics", "atom", [
            placeholderBoard("physics-aqa", "AQA", subjectID: "physics", subjectTitle: "Physics", systemImage: "atom"),
            placeholderBoard("physics-cambridge-international", "Cambridge International", subjectID: "physics", subjectTitle: "Physics", systemImage: "atom"),
            placeholderBoard("physics-edexcel", "Edexcel", subjectID: "physics", subjectTitle: "Physics", systemImage: "atom"),
            placeholderBoard("physics-ocr-a", "OCR A", subjectID: "physics", subjectTitle: "Physics", systemImage: "atom"),
        ]),
    ]

    static var readyBoards: [ExamBoardOption] {
        subjects.flatMap(\.boards).filter(\.isReady)
    }

    static var defaultBoard: ExamBoardOption {
        board(id: "economics-edexcel-a") ?? readyBoards[0]
    }

    static func board(id: String) -> ExamBoardOption? {
        subjects.flatMap(\.boards).first { $0.id == id }
    }

    private static func subject(_ id: String, _ title: String, _ systemImage: String, _ boards: [ExamBoardOption]) -> CatalogSubject {
        CatalogSubject(id: id, title: title, systemImage: systemImage, boards: boards)
    }

    private static func placeholderSubject(_ id: String, _ title: String, _ systemImage: String, _ boards: [String]) -> CatalogSubject {
        subject(
            id,
            title,
            systemImage,
            boards.map { placeholderBoard("\(id)-\($0.slugID)", $0, subjectID: id, subjectTitle: title, systemImage: systemImage) }
        )
    }

    private static func readyBoard(
        subjectID: String,
        subjectTitle: String,
        systemImage: String,
        boardID: String,
        title: String,
        backendSubject: String,
        papers: [PaperOption]
    ) -> ExamBoardOption {
        return ExamBoardOption(
            id: "\(subjectID)-\(boardID)",
            subjectID: subjectID,
            subjectTitle: subjectTitle,
            title: title,
            shortTitle: title,
            systemImage: systemImage,
            status: .ready,
            backendSubject: backendSubject,
            papers: papers,
            resourcePath: "a-levels/\(subjectID)/\(boardID)"
        )
    }

    private static func placeholderBoard(
        _ id: String,
        _ title: String,
        subjectID: String? = nil,
        subjectTitle: String? = nil,
        systemImage: String? = nil
    ) -> ExamBoardOption {
        let resolvedSubjectID = subjectID ?? id.components(separatedBy: "-").dropLast().joined(separator: "-")
        let boardSlug = String(id.dropFirst("\(resolvedSubjectID)-".count))
        return ExamBoardOption(
            id: id,
            subjectID: resolvedSubjectID,
            subjectTitle: subjectTitle ?? resolvedSubjectID.replacingOccurrences(of: "-", with: " ").capitalized,
            title: title,
            shortTitle: title,
            systemImage: systemImage ?? "doc.text",
            status: .placeholder,
            backendSubject: nil,
            papers: [
                PaperOption(id: "coming-soon", title: "Coming Soon", detail: "Generator support will be added later."),
            ],
            resourcePath: "a-levels/\(resolvedSubjectID)/\(boardSlug)"
        )
    }
}

private extension String {
    var slugID: String {
        lowercased()
            .replacingOccurrences(of: "&", with: "and")
            .replacingOccurrences(of: " ", with: "-")
            .replacingOccurrences(of: ".", with: "")
    }
}

enum SidebarItem: Hashable {
    case board(String)
    case settings
}

enum AIProvider: String, CaseIterable, Identifiable {
    case ollama
    case openAI
    case anthropic

    var id: String { rawValue }

    var title: String {
        switch self {
        case .ollama: "Ollama"
        case .openAI: "OpenAI"
        case .anthropic: "Anthropic"
        }
    }

    var subtitle: String {
        switch self {
        case .ollama: "Runs locally"
        case .openAI: "Uses an API key"
        case .anthropic: "Uses an API key"
        }
    }

    var systemImage: String {
        switch self {
        case .ollama: "desktopcomputer"
        case .openAI: "sparkles"
        case .anthropic: "text.bubble"
        }
    }

    var backendID: String {
        switch self {
        case .ollama: "ollama"
        case .openAI: "openai"
        case .anthropic: "anthropic"
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

struct GeneratedFile: Identifiable, Equatable {
    let id = UUID()
    let role: String
    let url: URL

    var title: String {
        switch role {
        case "question_paper": "Question Paper"
        case "source_booklet": "Source Booklet"
        case "mark_scheme": "Mark Scheme"
        default: role.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
}

enum BackendEvent: Equatable {
    case progress(stage: String?, message: String, progress: Double?)
    case file(role: String, path: String)
    case done(message: String)
    case error(message: String)
    case models([String], message: String?)
    case ollamaStatus(installed: Bool, running: Bool, command: String?, message: String?)

    init(jsonLine: String) throws {
        let data = Data(jsonLine.utf8)
        let payload = try JSONDecoder().decode(BackendEventPayload.self, from: data)

        switch payload.type {
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
        default:
            self = .progress(stage: payload.type, message: payload.message ?? payload.type, progress: payload.progress)
        }
    }
}

private struct BackendEventPayload: Decodable {
    let type: String
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

    enum CodingKeys: String, CodingKey {
        case type
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
    }
}
