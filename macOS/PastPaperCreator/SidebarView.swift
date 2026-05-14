import SwiftUI

struct Sidebar: View {
    @Binding var selection: SidebarItem?

    var body: some View {
        List(selection: $selection) {
            Section("A-Levels") {
                ForEach(ExamCatalog.subjects) { subject in
                    DisclosureGroup {
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

            Section {
                NavigationLink(value: SidebarItem.benchmark) {
                    Label("Benchmark", systemImage: "speedometer")
                }
                NavigationLink(value: SidebarItem.settings) {
                    Label("Settings", systemImage: "gearshape")
                }
            }
        }
        .navigationTitle("Past Papers")
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
