import Foundation
import Observation

@MainActor
@Observable
final class CatalogStore {
    var searchText = ""
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
