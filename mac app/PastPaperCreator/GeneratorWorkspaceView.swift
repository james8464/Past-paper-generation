import SwiftUI

struct GeneratorWorkspace: View {
    let board: ExamBoardOption

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HeaderPanel(board: board)

                if board.isReady {
                    ReadinessBanner()

                    ResponsiveColumns {
                        VStack(spacing: 18) {
                            PaperPanel(board: board)
                            OutputPanel()
                            DocumentsPanel()
                        }
                    } trailing: {
                        VStack(spacing: 18) {
                            ModelPanel()
                            ActivityPanel()
                        }
                    }
                } else {
                    PlaceholderPanel(board: board)
                }
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 24)
            .frame(maxWidth: 1160)
            .frame(maxWidth: .infinity)
        }
        .background(.background)
        .navigationTitle(board.subjectTitle)
    }
}

private struct HeaderPanel: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        ViewThatFits(in: .horizontal) {
            horizontalHeader
            verticalHeader
        }
        .nativePanel()
    }

    private var horizontalHeader: some View {
        HStack(spacing: 14) {
            titleBlock
            Spacer()
            StatusPill()
            primaryAction
        }
    }

    private var verticalHeader: some View {
        VStack(alignment: .leading, spacing: 14) {
            titleBlock
            HStack {
                StatusPill()
                Spacer()
                primaryAction
            }
        }
    }

    private var titleBlock: some View {
        HStack(spacing: 14) {
            Image(systemName: board.systemImage)
                .font(.system(size: 26, weight: .semibold))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
                .frame(width: 52, height: 52)
                .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

            VStack(alignment: .leading, spacing: 5) {
                Text(board.subjectTitle)
                    .font(.title.weight(.semibold))
                HStack(spacing: 8) {
                    CapsuleLabel(title: board.title, systemImage: "building.columns")
                    CapsuleLabel(title: appModel.selectedPaperTitle, systemImage: "doc.text")
                    CapsuleLabel(title: board.status.title, systemImage: board.isReady ? "checkmark.circle" : "clock")
                }
            }
        }
    }

    @ViewBuilder
    private var primaryAction: some View {
        if !board.isReady {
            Label("Coming Soon", systemImage: "clock")
                .font(.headline)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(.thinMaterial, in: Capsule())
        } else if appModel.isRunning {
            Button(role: .cancel, action: appModel.cancelGeneration) {
                Label("Cancel", systemImage: "xmark.circle")
            }
            .controlSize(.large)
        } else {
            Button(action: appModel.generate) {
                Label("Generate", systemImage: "play.fill")
            }
            .keyboardShortcut(.return, modifiers: .command)
            .disabled(!appModel.canGenerate)
            .controlSize(.large)
            .nativePrimaryActionStyle()
            .help(generateHelp)
            .accessibilityHint(generateHelp)
        }
    }

    private var generateHelp: String {
        if !board.isReady { return "This exam board is coming soon." }
        if appModel.aiProvider == .ollama && !appModel.ollamaState.running { return "Refresh Ollama before generating." }
        return "Generate paper"
    }
}

private struct ReadinessBanner: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        if appModel.generationBlocker != nil, !appModel.isRunning, !appModel.isRefreshingOllama {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 12) {
                    message
                    Spacer()
                    actions
                }

                VStack(alignment: .leading, spacing: 12) {
                    message
                    actions
                }
            }
            .padding(14)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .stroke(.orange.opacity(0.28), lineWidth: 1)
            }
        }
    }

    private var message: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
            VStack(alignment: .leading, spacing: 2) {
                Text(appModel.generationBlocker ?? "")
                    .font(.headline)
                Text(helpText)
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var actions: some View {
        HStack(spacing: 8) {
            if appModel.aiProvider == .ollama {
                Button("Refresh", action: appModel.refreshOllama)
                Button("Get Ollama", action: appModel.openOllamaDownload)
                    .disabled(appModel.distributionMode == .appStore)
            }
            SettingsLink {
                Label("Settings", systemImage: "slider.horizontal.3")
            }
        }
    }

    private var helpText: String {
        switch appModel.aiProvider {
        case .ollama:
            "Use Ollama locally, or switch provider in Settings."
        case .openAI, .anthropic:
            "Save provider credentials in Settings before generating."
        }
    }
}

private struct PaperPanel: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Paper", systemImage: "doc.text")

            Picker(
                "Paper",
                selection: Binding(
                    get: { appModel.selectedPaperID },
                    set: { appModel.selectPaperID($0) }
                )
            ) {
                ForEach(board.papers) { paper in
                    Text(paper.title).tag(paper.id)
                }
            }
            .pickerStyle(.segmented)

            Text(appModel.selectedPaperDetail)
                .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}

private struct OutputPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Output", systemImage: "folder")

            HStack {
                Text(appModel.outputFolder.path)
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .foregroundStyle(.secondary)
                Spacer()
                Button(action: appModel.openOutputFolder) {
                    Label("Open", systemImage: "folder")
                }
                .labelStyle(.iconOnly)
                .help("Open output folder")
                Button("Choose...", action: appModel.chooseOutputFolder)
            }

            Text("Generated PDFs are saved here.")
                .font(.callout)
                .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}

private struct ModelPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "AI Engine", systemImage: appModel.aiProvider.systemImage)

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(appModel.aiProvider.title)
                        .font(.headline)
                    Text(appModel.activeModelName.isEmpty ? "No model selected" : appModel.activeModelName)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                Spacer()
                SettingsLink {
                    Label("Settings", systemImage: "slider.horizontal.3")
                }
            }

            Divider()

            HStack {
                if appModel.isRefreshingOllama {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Image(systemName: modelStatusIcon)
                        .foregroundStyle(modelStatusColor)
                }
                Text(modelStatusText)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .nativePanel()
    }

    private var modelStatusIcon: String {
        if appModel.aiProvider == .ollama {
            return appModel.ollamaState.running ? "checkmark.circle.fill" : "exclamationmark.triangle.fill"
        }
        return "checkmark.circle.fill"
    }

    private var modelStatusColor: Color {
        appModel.aiProvider == .ollama && !appModel.ollamaState.running ? .orange : .green
    }

    private var modelStatusText: String {
        appModel.aiProvider == .ollama ? appModel.ollamaState.message : "\(appModel.aiProvider.title) configured in Settings"
    }
}

private struct ActivityPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Activity", systemImage: "waveform.path.ecg")

            if appModel.isRunning, let progress = appModel.generationProgress {
                ProgressView(value: progress) {
                    HStack {
                        Text(appModel.status)
                        Spacer()
                        if let estimate = appModel.generationEstimate {
                            Text("ETA \(estimate.remainingText)")
                                .foregroundStyle(.secondary)
                        }
                    }
                } currentValueLabel: {
                    Text(progress.formatted(.percent.precision(.fractionLength(0))))
                }
                .progressViewStyle(.linear)
            } else if appModel.isRunning {
                ProgressView()
                    .progressViewStyle(.linear)
            }

            if let estimate = appModel.generationEstimate {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Label("Estimated finish", systemImage: "clock")
                            .font(.headline)
                        Spacer()
                        Text(estimate.etaDate, style: .time)
                            .foregroundStyle(.secondary)
                    }
                    HStack(spacing: 10) {
                        Text("Confidence")
                            .foregroundStyle(.secondary)
                        ProgressView(value: estimate.confidence)
                            .progressViewStyle(.linear)
                        Text(estimate.confidence.formatted(.percent.precision(.fractionLength(0))))
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                    .font(.callout)

                    ForEach(estimate.factors.prefix(3)) { factor in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(factor.title)
                                    .font(.caption.weight(.semibold))
                                Text(factor.detail)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer()
                            Text(factor.impact.formatted(.number.precision(.fractionLength(2))) + "x")
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(factor.impact > 1.05 ? .orange : .secondary)
                        }
                    }
                }
                .padding(12)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            }

            ProgressLog(entries: appModel.progressEntries)
        }
        .nativePanel()
    }
}

private struct DocumentsPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Documents", systemImage: "doc.on.doc")
            GeneratedFilesTable(files: appModel.generatedFiles)
                .frame(minHeight: 170)
        }
        .nativePanel()
    }
}

private struct PlaceholderPanel: View {
    let board: ExamBoardOption

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            PanelHeader(title: "Coming Soon", systemImage: "clock")
            Text("\(board.subjectTitle) \(board.title) is planned for a future release.")
                .foregroundStyle(.secondary)
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                Label("Ready now: Economics Edexcel A and Computer Science AQA.", systemImage: "checkmark.circle")
                Label("More subjects will appear here after their generator profiles are complete.", systemImage: "hourglass")
            }
            .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}
