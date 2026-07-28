import SwiftUI

struct PanelHeader: View {
    let title: String
    let systemImage: String

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.headline)
            .symbolRenderingMode(.hierarchical)
    }
}

struct GeneratedFilesTable: View {
    @EnvironmentObject private var appModel: AppViewModel
    let files: [GeneratedFile]

    var body: some View {
        if files.isEmpty {
            PanelEmptyState(title: "No papers yet", message: "Your question paper and mark scheme will appear here.", systemImage: "doc")
                .frame(maxWidth: .infinity, minHeight: 90)
        } else {
            Table(files) {
                TableColumn("Document") { file in
                    Text(file.title)
                }
                TableColumn("Location") { file in
                    Text(file.url.path)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .foregroundStyle(.secondary)
                }
                TableColumn("") { file in
                    HStack {
                        Button {
                            appModel.openGeneratedFile(file)
                        } label: {
                            Label("Open", systemImage: "doc")
                        }
                        .labelStyle(.iconOnly)
                        .help("Open")

                        Button {
                            appModel.revealGeneratedFile(file)
                        } label: {
                            Label("Reveal", systemImage: "folder")
                        }
                        .labelStyle(.iconOnly)
                        .help("Reveal in Finder")
                    }
                }
                .width(70)
            }
        }
    }
}

struct PanelEmptyState: View {
    let title: String
    let message: String
    let systemImage: String

    var body: some View {
        ContentUnavailableView {
            Label(title, systemImage: systemImage)
                .symbolRenderingMode(.hierarchical)
        } description: {
            Text(message)
        }
        .frame(maxWidth: .infinity)
    }
}
