import Foundation
import Observation

@MainActor
@Observable
final class CatalogStore {
    var searchText = ""
    var selectedBoardID: String
    var selectedPaperID: String
    var sidebarSelection: SidebarItem? {
        didSet { persistNavigation() }
    }
    private(set) var favoriteIDs: Set<String>
    private(set) var recentConfigurationIDs: [String]
    let subjects: [CatalogSubject]

    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored private let maximumRecents: Int

    init(
        subjects: [CatalogSubject],
        defaults: UserDefaults = .standard,
        maximumRecents: Int = 8
    ) {
        self.subjects = subjects
        self.defaults = defaults
        self.maximumRecents = max(1, maximumRecents)
        favoriteIDs = Set(defaults.stringArray(forKey: AppStorageKey.favoriteBoardIDs) ?? [])
        recentConfigurationIDs = defaults.stringArray(
            forKey: AppStorageKey.recentConfigurationIDs
        ) ?? []
        let requestedBoardID = defaults.string(forKey: AppStorageKey.selectedBoardID)
        let board = requestedBoardID.flatMap(ExamCatalog.board(id:)) ?? ExamCatalog.defaultBoard
        let requestedPaperID = defaults.string(forKey: AppStorageKey.selectedPaperID)
        selectedBoardID = board.id
        selectedPaperID = board.papers.contains { $0.id == requestedPaperID }
            ? requestedPaperID ?? board.papers.first?.id ?? "unknown"
            : board.papers.first?.id ?? "unknown"
        sidebarSelection = Self.restoredNavigation(
            defaults.string(forKey: AppStorageKey.sidebarSelection),
            fallbackBoardID: board.id
        )
    }

    var filteredSubjects: [CatalogSubject] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return subjects }
        return subjects.compactMap { subject in
            let subjectMatches = subject.title.localizedCaseInsensitiveContains(query)
            let boards = subject.boards.filter {
                subjectMatches
                    || $0.title.localizedCaseInsensitiveContains(query)
                    || $0.shortTitle.localizedCaseInsensitiveContains(query)
                    || $0.subjectTitle.localizedCaseInsensitiveContains(query)
            }
            guard !boards.isEmpty else { return nil }
            return CatalogSubject(
                id: subject.id,
                title: subject.title,
                systemImage: subject.systemImage,
                boards: boards
            )
        }
    }

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
                readiness: QualificationReadiness(
                    engineeringValidated: false,
                    visuallyCalibrated: false,
                    empiricallyCalibrated: false
                )
            )
    }

    @discardableResult
    func selectBoard(_ board: ExamBoardOption, isLocked: Bool) -> Bool {
        guard !isLocked else { return false }
        let currentPaperIsValid = board.papers.contains { $0.id == selectedPaperID }
        guard selectedBoardID != board.id || !currentPaperIsValid else { return false }
        selectedBoardID = board.id
        selectedPaperID = board.papers.first?.id ?? "unknown"
        sidebarSelection = .board(board.id)
        persistSelection()
        return true
    }

    @discardableResult
    func selectPaperID(_ paperID: String, isLocked: Bool) -> Bool {
        guard !isLocked, selectedBoard.papers.contains(where: { $0.id == paperID }) else {
            return false
        }
        guard selectedPaperID != paperID else {
            defaults.set(paperID, forKey: AppStorageKey.selectedPaperID)
            return false
        }
        selectedPaperID = paperID
        defaults.set(paperID, forKey: AppStorageKey.selectedPaperID)
        return true
    }

    func show(_ item: SidebarItem) {
        sidebarSelection = item
    }

    private func persistNavigation() {
        let value: String
        switch sidebarSelection {
        case let .board(id): value = "board:\(id)"
        case .benchmark: value = "benchmark"
        case .documents: value = "documents"
        case .history: value = "history"
        case nil: value = ""
        }
        defaults.set(value, forKey: AppStorageKey.sidebarSelection)
    }

    private static func restoredNavigation(
        _ value: String?,
        fallbackBoardID: String
    ) -> SidebarItem {
        switch value {
        case "benchmark": return .benchmark
        case "documents": return .documents
        case "history": return .history
        case let value? where value.hasPrefix("board:"):
            let id = String(value.dropFirst("board:".count))
            return ExamCatalog.board(id: id).map { .board($0.id) }
                ?? .board(fallbackBoardID)
        default:
            return .board(fallbackBoardID)
        }
    }

    private func persistSelection() {
        defaults.set(selectedBoardID, forKey: AppStorageKey.selectedBoardID)
        defaults.set(selectedPaperID, forKey: AppStorageKey.selectedPaperID)
    }

    func toggleFavourite(_ boardID: String) {
        if !favoriteIDs.insert(boardID).inserted {
            favoriteIDs.remove(boardID)
        }
        defaults.set(favoriteIDs.sorted(), forKey: AppStorageKey.favoriteBoardIDs)
    }

    func recordRecentConfiguration(boardID: String, paperID: String) {
        let id = "\(boardID)::\(paperID)"
        recentConfigurationIDs.removeAll { $0 == id }
        recentConfigurationIDs.insert(id, at: 0)
        recentConfigurationIDs = Array(recentConfigurationIDs.prefix(maximumRecents))
        defaults.set(
            recentConfigurationIDs,
            forKey: AppStorageKey.recentConfigurationIDs
        )
    }
}
