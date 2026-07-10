import SwiftUI

struct Sidebar: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(spacing: 0) {
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

            Divider()

            statusBar
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
        }
        .frame(minWidth: 200)
    }

    @ViewBuilder
    private var statusBar: some View {
        if appModel.isRunning || appModel.isBenchmarkRunning {
            HStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 12, height: 12)

                VStack(alignment: .leading, spacing: 1) {
                    Text(appModel.status)
                        .font(.caption)
                        .lineLimit(1)

                    if let progress = appModel.generationProgress ?? appModel.benchmarkProgress {
                        Text(Int(progress * 100).formatted() + "%")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer(minLength: 0)
            }
            .foregroundStyle(.secondary)
        } else if appModel.isRefreshingOllama {
            HStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 12, height: 12)

                Text("Checking Ollama...")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer(minLength: 0)
            }
        } else if !appModel.generatedFiles.isEmpty {
            HStack(spacing: 8) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.caption)
                    .foregroundStyle(.green)

                Text("Papers ready")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer(minLength: 0)
            }
        } else {
            HStack(spacing: 8) {
                Circle()
                    .fill(.secondary)
                    .frame(width: 6, height: 6)

                Text("Ready")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer(minLength: 0)
            }
        }
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
