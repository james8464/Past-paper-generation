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

struct CapsuleLabel: View {
    let title: String
    let systemImage: String

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.callout)
            .foregroundStyle(.secondary)
            .lineLimit(1)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(.thinMaterial, in: Capsule())
    }
}

struct StatusPill: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        HStack(spacing: 7) {
            if appModel.isRunning || appModel.isBenchmarkRunning || appModel.isRefreshingOllama {
                ProgressView()
                    .controlSize(.small)
                    .frame(width: 16, height: 16)
            } else {
                Image(systemName: appModel.status == "Error" ? "exclamationmark.triangle" : "checkmark.circle")
                    .symbolRenderingMode(.hierarchical)
            }
            Text(appModel.status)
        }
        .font(.callout)
        .foregroundStyle(.secondary)
        .lineLimit(1)
        .padding(.horizontal, 12)
        .padding(.vertical, 7)
        .nativeStatusGlass()
        .frame(maxWidth: 220)
    }
}

struct ProgressLog: View {
    let entries: [ProgressEntry]

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 8) {
                if entries.isEmpty {
                    PanelEmptyState(title: "Ready", message: "Generation activity appears here.", systemImage: "checkmark.circle")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 24)
                } else {
                    ForEach(entries.suffix(80)) { entry in
                        HStack(alignment: .firstTextBaseline, spacing: 10) {
                            Text(entry.date, style: .time)
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(.tertiary)
                                .frame(width: 64, alignment: .leading)
                            Text(entry.stage ?? "step")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .frame(width: 74, alignment: .leading)
                            Text(entry.message)
                                .textSelection(.enabled)
                        }
                        .font(.callout)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(minHeight: 140, maxHeight: 190)
    }
}

struct GeneratedFilesTable: View {
    @EnvironmentObject private var appModel: AppViewModel
    let files: [GeneratedFile]

    var body: some View {
        if files.isEmpty {
            PanelEmptyState(title: "No Documents", message: "Generated PDFs will be listed here.", systemImage: "doc")
                .frame(maxWidth: .infinity, minHeight: 150)
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
        VStack(spacing: 8) {
            Image(systemName: systemImage)
                .font(.system(size: 26, weight: .regular))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.secondary)
            Text(title)
                .font(.headline)
            Text(message)
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
    }
}
