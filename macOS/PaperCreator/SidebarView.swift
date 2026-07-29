import SwiftUI

struct Sidebar: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var appModel: AppViewModel
    @AppStorage(AppStorageKey.expandedSubjectIDs)
    private var expandedSubjectIDs = ""

    var body: some View {
        List(selection: $selection) {
            Section("A level") {
                ForEach(ExamCatalog.subjects) { subject in
                    DisclosureGroup(isExpanded: expansionBinding(for: subject.id)) {
                        ForEach(subject.boards) { board in
                            NavigationLink(value: SidebarItem.board(board.id)) {
                                BoardRow(board: board)
                            }
                        }
                    } label: {
                        Label(subject.title, systemImage: subject.systemImage)
                    }
                }
            }
        }
        .navigationTitle("Paper creator")
        .frame(minWidth: 220)
        .onAppear(perform: expandSelectedSubject)
        .onChange(of: selection) { _, _ in expandSelectedSubject() }
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

private struct BoardRow: View {
    let board: ExamBoardOption

    var body: some View {
        HStack {
            Text(board.shortTitle)
            Spacer()
            if board.status == .placeholder {
                Image(systemName: "clock")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .help("Coming soon")
            }
        }
    }
}
