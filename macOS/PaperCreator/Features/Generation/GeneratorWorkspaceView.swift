import SwiftUI

struct GeneratorWorkspace: View {
    @EnvironmentObject private var appModel: AppViewModel
    @AppStorage(AppStorageKey.qualityInspectorVisible)
    private var showsQualityInspector = true
    let board: ExamBoardOption

    var body: some View {
        Group {
            if board.isReady {
                workspace
            } else {
                ContentUnavailableView {
                    Label("Coming soon", systemImage: "clock")
                } description: {
                    Text("\(board.subjectTitle) for \(board.title) is not available yet.")
                }
            }
        }
        .navigationTitle("\(board.subjectTitle) — \(board.shortTitle)")
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button {
                    showsQualityInspector.toggle()
                } label: {
                    Label(
                        showsQualityInspector ? "Hide Quality Inspector" : "Show Quality Inspector",
                        systemImage: "checklist"
                    )
                }
                .help(showsQualityInspector ? "Hide Quality Inspector" : "Show Quality Inspector")

                if appModel.isRunning {
                    Button(role: .cancel, action: appModel.cancelGeneration) {
                        Label("Cancel", systemImage: "xmark.circle")
                    }
                    .help("Cancel paper creation")
                } else {
                    Button(action: appModel.generate) {
                        Label("Create Paper", systemImage: "doc.badge.plus")
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!appModel.canGenerate)
                    .help(generateHelp)
                    .accessibilityHint(generateHelp)
                }
            }
        }
        .inspector(isPresented: $showsQualityInspector) {
            QualityInspector()
                .inspectorColumnWidth(min: 250, ideal: 290, max: 360)
        }
    }

    private var workspace: some View {
        VStack(spacing: 0) {
            PaperConfiguration(board: board)
                .frame(maxHeight: 390)

            Divider()

            RecentDocuments()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private var generateHelp: String {
        appModel.generationBlocker ?? "Create a new question paper, mark scheme, and validation package."
    }
}

private struct PaperConfiguration: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        Form {
            Section("Paper") {
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

                LabeledContent("Assessment") {
                    Text(appModel.selectedPaperDetail)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.trailing)
                }
            }

            Section("Generation") {
                Picker(
                    "AI provider",
                    selection: Binding(
                        get: { appModel.aiProvider },
                        set: { appModel.selectAIProvider($0) }
                    )
                ) {
                    ForEach(board.supportedProviders) { provider in
                        Label(provider.title, systemImage: provider.systemImage)
                            .tag(provider)
                    }
                }
                .pickerStyle(.menu)

                LabeledContent("Model") {
                    Text(appModel.activeModelName)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .help(appModel.activeModelName)
                }

                LabeledContent("Save to") {
                    HStack(spacing: 8) {
                        Text(appModel.outputFolder.path)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .help(appModel.outputFolder.path)
                        Button("Choose…", action: appModel.chooseOutputFolder)
                    }
                }

                Toggle(
                    "Create a layout preview",
                    isOn: Binding(
                        get: { appModel.dryRun },
                        set: { appModel.setDryRun($0) }
                    )
                )
                .help("Preview layout without contacting an AI provider. Preview questions are not release output.")
            }

            if appModel.isRunning {
                Section("Progress") {
                    GenerationProgress()
                }
            } else if let blocker = appModel.generationBlocker {
                Section("Action required") {
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                            .accessibilityHidden(true)
                        Text(blocker)
                        Spacer()
                        SettingsLink {
                            Text("Open Settings…")
                        }
                    }
                    .accessibilityElement(children: .combine)
                }
            }
        }
        .formStyle(.grouped)
    }
}

private struct GenerationProgress: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            if let progress = appModel.generationProgress {
                ProgressView(value: progress) {
                    HStack {
                        Text(appModel.status)
                        Spacer()
                        if let estimate = appModel.generationEstimate {
                            Text(estimate.remainingText)
                                .foregroundStyle(.secondary)
                        }
                    }
                } currentValueLabel: {
                    Text(progress.formatted(.percent.precision(.fractionLength(0))))
                }
            } else {
                ProgressView(appModel.status)
            }
        }
        .accessibilityElement(children: .contain)
    }
}

private struct RecentDocuments: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Recent Documents")
                    .font(.headline)
                if !appModel.generatedFiles.isEmpty {
                    Text(appModel.generatedFiles.count, format: .number)
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("\(appModel.generatedFiles.count) documents")
                }
                Spacer()
                Button("Open Output Folder", action: appModel.openOutputFolder)
            }
            .padding(.horizontal, 20)
            .padding(.top, 14)

            GeneratedFilesTable(files: appModel.generatedFiles)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .padding(.bottom, 12)
    }
}

private struct QualityInspector: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Release gates") {
                qualityRow(
                    "Blueprint",
                    detail: "Structure, marks, AO allocation, and command words are locked.",
                    state: .passed
                )
                qualityRow(
                    "Originality",
                    detail: originalityDetail,
                    state: originalityState
                )
                qualityRow(
                    "Visual profile",
                    detail: appModel.selectedPaper.readiness.visuallyCalibrated
                        ? "Reference geometry has been reviewed."
                        : "This paper still needs a completed visual calibration.",
                    state: appModel.selectedPaper.readiness.visuallyCalibrated ? .passed : .pending
                )
                qualityRow(
                    "Difficulty",
                    detail: appModel.selectedPaper.readiness.difficultyVerified
                        ? "Independent response-data calibration is complete."
                        : "Intended demand is checked; psychometric equivalence is not claimed.",
                    state: appModel.selectedPaper.readiness.difficultyVerified ? .passed : .pending
                )
            }

            if let report = appModel.lastQualityReport {
                Section("Latest package") {
                    LabeledContent("Items", value: "\(report.itemCount)")
                    LabeledContent(
                        "Fingerprints",
                        value: report.fingerprintsVerified ? "Verified" : "Failed"
                    )
                    LabeledContent(
                        "History checks",
                        value: "\(report.historicComparisons)"
                    )
                    if let nearest = report.nearestSimilarity {
                        LabeledContent(
                            "Nearest match",
                            value: nearest.formatted(.percent.precision(.fractionLength(1)))
                        )
                    }
                    LabeledContent("Validated PDFs", value: "\(report.pdfCount)")
                }
            }

            if appModel.isRunning || !appModel.progressEntries.isEmpty {
                Section("Activity") {
                    ForEach(appModel.progressEntries.suffix(6)) { entry in
                        Text(entry.message)
                            .lineLimit(3)
                    }
                }
            }

            Section {
                Text("Unofficial practice material. The app reproduces measured document conventions, not copyrighted paper content.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Quality")
    }

    private func qualityRow(
        _ title: String,
        detail: String,
        state: QualityState
    ) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: state.systemImage)
                .foregroundStyle(state.color)
                .frame(width: 16)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(title)
                    Spacer()
                    Text(state.title)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .accessibilityElement(children: .combine)
    }

    private var originalityState: QualityState {
        if appModel.dryRun {
            return .preview
        }
        return appModel.lastQualityReport == nil ? .atCreation : .passed
    }

    private var originalityDetail: String {
        if appModel.dryRun {
            return "History comparison is skipped for preview drafts."
        }
        if appModel.lastQualityReport == nil {
            return "Draft and history similarity are checked before files are published."
        }
        return "Draft and historic-item similarity passed the release threshold."
    }
}

private enum QualityState {
    case passed
    case pending
    case preview
    case atCreation

    var title: String {
        switch self {
        case .passed: "Passed"
        case .pending: "Pending"
        case .preview: "Preview"
        case .atCreation: "At creation"
        }
    }

    var systemImage: String {
        switch self {
        case .passed: "checkmark.circle.fill"
        case .pending: "clock"
        case .preview: "eye"
        case .atCreation: "checkmark.shield"
        }
    }

    var color: Color {
        switch self {
        case .passed: .green
        case .pending: .orange
        case .preview: .secondary
        case .atCreation: .secondary
        }
    }
}
