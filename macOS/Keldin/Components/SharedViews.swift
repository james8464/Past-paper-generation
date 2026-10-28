// Reusable controls and status views for the workspace and settings.

import SwiftUI

struct GeneratedFilesTable: View {
    @Environment(\.locale) private var locale
    @EnvironmentObject private var application: ApplicationCoordinator
    let files: [GeneratedFile]

    var body: some View {
        if files.isEmpty {
            PanelEmptyState(title: "No papers yet", message: "Your question paper and mark scheme will appear here.", systemImage: "doc")
                .frame(maxWidth: .infinity, minHeight: 90)
        } else {
            Table(files) {
                TableColumn("Document") { file in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(InterfaceText.localizedResource(file.titleResource, locale: locale))
                        if !file.paperDescription.isEmpty {
                            Text(file.paperDescription)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .foregroundStyle(file.exists ? .primary : .secondary)
                    .draggable(file.url)
                }
                TableColumn("Created") { file in
                    Text(file.createdAt, format: .dateTime.day().month().hour().minute())
                        .foregroundStyle(.secondary)
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
                            application.previewGeneratedFile(file)
                        } label: {
                            Label("Preview", systemImage: "eye")
                        }
                        .labelStyle(.iconOnly)
                        .help("Preview")

                        Button {
                            application.revealGeneratedFile(file)
                        } label: {
                            Label("Reveal", systemImage: "folder")
                        }
                        .labelStyle(.iconOnly)
                        .help("Reveal in Finder")
                        .disabled(!file.exists)
                    }
                }
                .width(70)
            }
            .contextMenu(forSelectionType: GeneratedFile.ID.self) { selection in
                if let id = selection.first,
                   let file = files.first(where: { $0.id == id }) {
                    Button("Remove from Recents") {
                        application.removeGeneratedFile(file)
                    }
                }
            }
        }
    }
}

struct PanelEmptyState: View {
    @Environment(\.locale) private var locale
    let title: LocalizedStringResource
    let message: LocalizedStringResource
    let systemImage: String

    var body: some View {
        ContentUnavailableView {
            Label { Text(InterfaceText.localizedResource(title, locale: locale)) } icon: { Image(systemName: systemImage) }
                .symbolRenderingMode(.hierarchical)
        } description: {
            Text(InterfaceText.localizedResource(message, locale: locale))
        }
        .frame(maxWidth: .infinity)
    }
}
