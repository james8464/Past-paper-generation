import SwiftUI

struct JobHistoryView: View {
    @EnvironmentObject private var appModel: AppViewModel
    @Bindable var store: RecentDocumentStore
    @State private var selection: GenerationJobRecord.ID?

    var body: some View {
        Group {
            if store.records.isEmpty {
                ContentUnavailableView {
                    Label("No generation history", systemImage: "clock.arrow.circlepath")
                } description: {
                    Text("Completed, cancelled, and interrupted jobs will appear here.")
                }
            } else {
                Table(store.records, selection: $selection) {
                    TableColumn("Paper") { record in
                        VStack(alignment: .leading) {
                            Text(boardTitle(record.configuration.boardID))
                            Text("Paper \(record.configuration.paperID)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    TableColumn("State") { record in
                        Label(record.state.title, systemImage: record.state.systemImage)
                    }
                    TableColumn("Created") { record in
                        Text(record.createdAt, format: .dateTime.day().month().hour().minute())
                    }
                    TableColumn("Model") { record in
                        Text(record.configuration.model)
                            .lineLimit(1)
                            .truncationMode(.middle)
                    }
                }
                .contextMenu(forSelectionType: GenerationJobRecord.ID.self) { selected in
                    if let record = selectedRecord(from: selected) {
                        Button("Duplicate Configuration") {
                            appModel.duplicateConfiguration(record)
                        }
                        Button("Create Again with New Questions") {
                            appModel.createAgainWithNewSeed(record)
                        }
                        Divider()
                        Button("Remove from History", role: .destructive) {
                            try? store.remove(record)
                        }
                    }
                }
            }
        }
        .navigationTitle("History")
        .toolbar {
            ToolbarItemGroup {
                Button("Duplicate Configuration", systemImage: "doc.on.doc") {
                    if let record = selectedRecord {
                        appModel.duplicateConfiguration(record)
                    }
                }
                .disabled(selectedRecord == nil)

                Button("Create Again with New Questions", systemImage: "arrow.clockwise") {
                    if let record = selectedRecord {
                        appModel.createAgainWithNewSeed(record)
                    }
                }
                .disabled(selectedRecord == nil)
            }
        }
    }

    private var selectedRecord: GenerationJobRecord? {
        store.records.first { $0.id == selection }
    }

    private func selectedRecord(
        from selection: Set<GenerationJobRecord.ID>
    ) -> GenerationJobRecord? {
        guard let id = selection.first else { return nil }
        return store.records.first { $0.id == id }
    }

    private func boardTitle(_ id: String) -> String {
        guard let board = ExamCatalog.board(id: id) else { return id }
        return "\(board.subjectTitle) — \(board.shortTitle)"
    }
}

private extension GenerationJobState {
    var title: String {
        switch self {
        case .pending: "Pending"
        case .running: "Creating"
        case .completed: "Completed"
        case .cancelled: "Cancelled"
        case .failed: "Failed"
        case .interrupted: "Interrupted"
        case .missingArtifacts: "Files Missing"
        }
    }

    var systemImage: String {
        switch self {
        case .pending: "clock"
        case .running: "progress.indicator"
        case .completed: "checkmark.circle"
        case .cancelled: "xmark.circle"
        case .failed: "exclamationmark.triangle"
        case .interrupted: "pause.circle"
        case .missingArtifacts: "doc.badge.ellipsis"
        }
    }
}
