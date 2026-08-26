import SwiftUI

struct Sidebar: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage(AppStorageKey.expandedSubjectIDs)
    private var expandedSubjectIDs = ""

    var body: some View {
        CatalogSidebarSections(
            selection: $selection,
            store: application.catalogStore,
            expandedSubjectIDs: $expandedSubjectIDs
        )
        .disabled(application.isRunning)
        .navigationTitle("Paper creator")
        .frame(minWidth: 220)
        .onAppear(perform: expandSelectedSubject)
        .onChange(of: selection) { _, _ in expandSelectedSubject() }
    }

    private var expandedSubjects: Set<String> {
        Set(expandedSubjectIDs.split(separator: ",").map(String.init))
    }

    private func expandSelectedSubject() {
        guard case let .board(boardID) = selection,
              let board = ExamCatalog.board(id: boardID),
              !expandedSubjects.contains(board.subjectID) else {
            return
        }
        var values = expandedSubjects
        values.insert(board.subjectID)
        expandedSubjectIDs = values.sorted().joined(separator: ",")
    }
}

private struct CatalogSidebarSections: View {
    @Binding var selection: SidebarItem?
    @Bindable var store: CatalogStore
    @Binding var expandedSubjectIDs: String

    var body: some View {
        List(selection: $selection) {
            Section("Library") {
                NavigationLink(value: SidebarItem.documents) {
                    Label("Documents", systemImage: "doc.richtext")
                }
                NavigationLink(value: SidebarItem.history) {
                    Label("History", systemImage: "clock.arrow.circlepath")
                }
                NavigationLink(value: SidebarItem.benchmark) {
                    Label("Mac Benchmark", systemImage: "gauge.with.dots.needle.67percent")
                }
            }

            if !store.favoriteIDs.isEmpty {
                Section("Favourites") {
                    ForEach(favouriteBoards) { board in
                        boardLink(board)
                    }
                }
            }

            if !store.recentConfigurationIDs.isEmpty {
                Section("Recent Configurations") {
                    ForEach(recentBoards) { board in
                        boardLink(board)
                    }
                }
            }

            Section("Subjects") {
                ForEach(store.filteredSubjects) { subject in
                    DisclosureGroup(isExpanded: expansionBinding(for: subject.id)) {
                        ForEach(subject.boards) { board in
                            boardLink(board)
                        }
                    } label: {
                        Label(subject.title, systemImage: subject.systemImage)
                    }
                }
            }
        }
        .searchable(text: $store.searchText, placement: .sidebar, prompt: "Subjects and boards")
    }

    private func expansionBinding(for subjectID: String) -> Binding<Bool> {
        Binding(
            get: { expandedSubjects.contains(subjectID) },
            set: { expanded in
                var values = expandedSubjects
                if expanded {
                    values.insert(subjectID)
                } else {
                    values.remove(subjectID)
                }
                expandedSubjectIDs = values.sorted().joined(separator: ",")
            }
        )
    }

    private var expandedSubjects: Set<String> {
        Set(expandedSubjectIDs.split(separator: ",").map(String.init))
    }

    private var favouriteBoards: [ExamBoardOption] {
        ExamCatalog.readyBoards.filter { store.favoriteIDs.contains($0.id) }
    }

    private var recentBoards: [ExamBoardOption] {
        var seen: Set<String> = []
        return store.recentConfigurationIDs.compactMap { value in
            let boardID = value.components(separatedBy: "::").first ?? ""
            guard seen.insert(boardID).inserted else { return nil }
            return ExamCatalog.board(id: boardID)
        }
    }

    private func boardLink(_ board: ExamBoardOption) -> some View {
        NavigationLink(value: SidebarItem.board(board.id)) {
            BoardRow(
                board: board,
                isFavourite: store.favoriteIDs.contains(board.id)
            ) {
                store.toggleFavourite(board.id)
            }
        }
    }
}

private struct BoardRow: View {
    let board: ExamBoardOption
    let isFavourite: Bool
    let toggleFavourite: () -> Void

    var body: some View {
        HStack {
            Text(board.shortTitle)
            Spacer()
            Button(
                isFavourite ? "Remove from Favourites" : "Add to Favourites",
                systemImage: isFavourite ? "star.fill" : "star",
                action: toggleFavourite
            )
            .buttonStyle(.plain)
            .labelStyle(.iconOnly)
            .foregroundStyle(isFavourite ? .primary : .tertiary)
            if board.status == .placeholder {
                Label("Coming soon", systemImage: "clock")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
    }
}
