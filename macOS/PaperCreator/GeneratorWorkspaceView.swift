import SwiftUI

struct GeneratorWorkspace: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HeaderPanel(board: board)

                if board.isReady {
                    ReadinessBanner()
                    OutputDestinationPanel()
                    if appModel.isRunning {
                        ActivityPanel()
                    }
                    DocumentsPanel()
                } else {
                    PlaceholderPanel(board: board)
                }
            }
            .padding(.horizontal, 40)
            .padding(.vertical, 32)
            .frame(maxWidth: 1080)
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
        .padding(.bottom, 4)
    }

    private var horizontalHeader: some View {
        HStack(spacing: 14) {
            titleBlock
            Spacer()
            primaryAction
        }
    }

    private var verticalHeader: some View {
        VStack(alignment: .leading, spacing: 14) {
            titleBlock
            HStack {
                Spacer()
                primaryAction
            }
        }
    }

    private var titleBlock: some View {
        HStack(alignment: .top, spacing: 14) {
            Image(systemName: board.systemImage)
                .font(.system(size: 24, weight: .semibold))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.primary)
                .frame(width: 42, height: 42)

            VStack(alignment: .leading, spacing: 5) {
                Text(board.subjectTitle)
                    .font(.title.weight(.semibold))
                Text(board.title)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)

                if board.isReady {
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
                    .labelsHidden()
                    .frame(maxWidth: 440)
                    .padding(.top, 8)

                    Text(appModel.selectedPaperDetail)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)

                    HStack(spacing: 8) {
                        Label(board.contentMode.title, systemImage: board.contentMode.systemImage)
                            .foregroundStyle(.secondary)
                        evidenceLabel(
                            appModel.selectedPaper.readiness.visuallyCalibrated
                                ? "Visual profile reviewed"
                                : "Visual review pending",
                            passed: appModel.selectedPaper.readiness.visuallyCalibrated
                        )
                        evidenceLabel(
                            appModel.selectedPaper.readiness.difficultyVerified
                                ? "Difficulty independently verified"
                                : "Difficulty not independently verified",
                            passed: appModel.selectedPaper.readiness.difficultyVerified
                        )
                    }
                    .font(.caption)
                    .padding(.top, 2)
                }
            }
        }
    }

    private func evidenceLabel(_ title: String, passed: Bool) -> some View {
        Label(title, systemImage: passed ? "checkmark.seal.fill" : "exclamationmark.triangle")
            .foregroundStyle(passed ? Color.green : Color.orange)
            .help(title)
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
            Label("Creating Paper", systemImage: "progress.indicator")
                .foregroundStyle(.secondary)
        } else {
            Button(action: appModel.generate) {
                Label("Create Paper", systemImage: "doc.badge.plus")
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
        if let blocker = appModel.generationBlocker { return blocker }
        return "Create the question paper and mark scheme"
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
            .padding(16)
            .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
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
            if appModel.selectedBoard.usesAI && appModel.aiProvider == .ollama {
                Button("Check Again", action: appModel.refreshOllama)
                if appModel.distributionMode.canManageOllama {
                    Button("Get Ollama", action: appModel.openOllamaDownload)
                }
            }
            SettingsLink {
                Label("Settings", systemImage: "slider.horizontal.3")
            }
        }
    }

    private var helpText: String {
        guard appModel.selectedBoard.usesAI else {
            return "This paper uses the built-in constrained generator and does not contact an AI provider."
        }
        return switch appModel.aiProvider {
        case .ollama:
            "Use Ollama locally, or switch provider in Settings."
        case .apple:
            "Using Apple MLX local inference. Configure model in Settings."
        case .openAI, .anthropic:
            "Save provider credentials in Settings before generating."
        }
    }
}

private struct ActivityPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Creating paper", systemImage: "doc.badge.plus")

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
        }
        .nativePanel()
    }
}

private struct DocumentsPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Recent papers", systemImage: "doc.on.doc")
            GeneratedFilesTable(files: appModel.generatedFiles)
                .frame(minHeight: 110)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct OutputDestinationPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(spacing: 12) {
            if appModel.selectedBoard.usesAI {
                HStack(spacing: 12) {
                    Label("AI provider", systemImage: "sparkles")
                        .font(.headline)
                    Picker(
                        "AI provider",
                        selection: Binding(
                            get: { appModel.aiProvider },
                            set: { appModel.selectAIProvider($0) }
                        )
                    ) {
                        ForEach(
                            appModel.selectedBoard.supportedProviders
                        ) { provider in
                            Text(provider.title).tag(provider)
                        }
                    }
                    .labelsHidden()
                    .pickerStyle(.menu)
                    Text(appModel.activeModelName)
                        .lineLimit(1)
                        .foregroundStyle(.secondary)
                    Spacer()
                    SettingsLink {
                        Label("Configure", systemImage: "gear")
                    }
                }
                Divider()
            }

            HStack(spacing: 12) {
                Label("Save to", systemImage: "folder")
                    .font(.headline)
                Text(appModel.outputFolder.path)
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .foregroundStyle(.secondary)
                Spacer()
                Button("Choose…", action: appModel.chooseOutputFolder)
            }
        }
        .padding(14)
        .background(
            Color(nsColor: .controlBackgroundColor),
            in: RoundedRectangle(cornerRadius: 10, style: .continuous)
        )
    }
}

private struct PlaceholderPanel: View {
    let board: ExamBoardOption

    var body: some View {
        ContentUnavailableView {
            Label("Coming soon", systemImage: "clock")
        } description: {
            Text("\(board.subjectTitle) for \(board.title) is not available yet.")
        }
        .frame(maxWidth: .infinity, minHeight: 320)
    }
}
