import SwiftUI
import TipKit

struct GeneratorWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage(AppStorageKey.qualityInspectorVisible)
    private var showsQualityInspector = true
    @State private var showsCompactQualityInspector = false
    let board: ExamBoardOption
    let layoutMode: WorkspaceLayoutMode

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
                if board.isReady {
                    Button {
                        if layoutMode.showsInspector {
                            showsQualityInspector.toggle()
                        } else {
                            showsCompactQualityInspector = true
                        }
                    } label: {
                        Label(
                            qualityButtonTitle,
                            systemImage: "checklist"
                        )
                    }
                    .help(qualityButtonTitle)

                    if application.isRunning {
                        Button(role: .cancel, action: application.cancelGeneration) {
                            Label("Cancel", systemImage: "xmark.circle")
                        }
                        .help("Cancel paper creation")
                    } else {
                        Button(action: application.generate) {
                            Label(createButtonTitle, systemImage: "doc.badge.plus")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!application.canGenerate)
                        .help(generateHelp)
                        .accessibilityHint(generateHelp)
                    }
                }
            }
        }
        .inspector(isPresented: inspectorPresentation) {
            QualityInspector()
                .inspectorColumnWidth(min: 250, ideal: 290, max: 360)
        }
        .sheet(isPresented: $showsCompactQualityInspector) {
            NavigationStack {
                QualityInspector()
                    .frame(minWidth: 480, minHeight: 520)
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") {
                                showsCompactQualityInspector = false
                            }
                        }
                    }
            }
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
        application.generationBlocker
            ?? "Create a new assessment, mark scheme, and validation package."
    }

    private var createButtonTitle: String {
        application.selectedPaper.assessmentKind == .questionBank
            ? "Create Practice Set"
            : "Create Paper"
    }

    private var qualityButtonTitle: String {
        if !layoutMode.showsInspector {
            return "Show Quality Inspector"
        }
        return showsQualityInspector
            ? "Hide Quality Inspector"
            : "Show Quality Inspector"
    }

    private var inspectorPresentation: Binding<Bool> {
        Binding(
            get: {
                board.isReady
                    && layoutMode.showsInspector
                    && showsQualityInspector
            },
            set: { isPresented in
                guard board.isReady, layoutMode.showsInspector else { return }
                showsQualityInspector = isPresented
            }
        )
    }
}

private struct PaperConfiguration: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    let board: ExamBoardOption

    var body: some View {
        Form {
            if board.usesAI,
               application.aiProvider == .ollama,
               !application.selectedModelIsRecommended {
                TipView(PaperCreationTips.modelRecommendation)
            } else if application.generatedFiles.isEmpty {
                TipView(PaperCreationTips.preview)
            }

            Section("Assessment") {
                if !board.fullPapers.isEmpty, !board.questionBanks.isEmpty {
                    Picker(
                        "Type",
                        selection: Binding(
                            get: { application.selectedPaper.assessmentKind },
                            set: { application.selectAssessmentKind($0) }
                        )
                    ) {
                        ForEach([AssessmentKind.fullPaper, .questionBank], id: \.self) { kind in
                            Text(kind.title).tag(kind)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                Picker(
                    application.selectedPaper.assessmentKind == .questionBank
                        ? "Topic"
                        : "Paper",
                    selection: Binding(
                        get: { application.selectedPaperID },
                        set: { application.selectPaperID($0) }
                    )
                ) {
                    ForEach(visibleAssessments) { paper in
                        Text(paper.title).tag(paper.id)
                    }
                }
                .pickerStyle(.segmented)

                LabeledContent("Assessment") {
                    Text(application.selectedPaperDetail)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.trailing)
                }
            }

            Section("Generation") {
                Picker(
                    "AI provider",
                    selection: Binding(
                        get: { application.aiProvider },
                        set: { application.selectAIProvider($0) }
                    )
                ) {
                    ForEach(board.supportedProviders) { provider in
                        Label(provider.title, systemImage: provider.systemImage)
                            .tag(provider)
                    }
                }
                .pickerStyle(.menu)

                LabeledContent("Model") {
                    HStack(spacing: 8) {
                        Text(application.activeModelName)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .help(application.activeModelName)
                        if application.aiProvider == .ollama && application.selectedModelIsRecommended {
                            Text("Recommended")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                if application.aiProvider == .ollama && !application.selectedModelIsRecommended {
                    Label(
                        "Results may vary with other Ollama models. Use the recommendation in Settings for the checked workflow.",
                        systemImage: "exclamationmark.triangle.fill"
                    )
                    .font(.caption)
                    .foregroundStyle(.orange)
                    .fixedSize(horizontal: false, vertical: true)
                }

                LabeledContent("Save to") {
                    HStack(spacing: 8) {
                        Text(application.outputFolderDisplayPath)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .help(application.outputFolderDisplayPath)
                        Button("Choose…", action: application.chooseOutputFolder)
                    }
                }

                Toggle(
                    "Create a layout preview",
                    isOn: Binding(
                        get: { application.dryRun },
                        set: { application.setDryRun($0) }
                    )
                )
                .help("Preview layout without contacting an AI provider. Preview questions are not release output.")
            }

            if application.isRunning {
                Section("Progress") {
                    GenerationProgress()
                }
            } else if let blocker = application.generationBlocker {
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
        .disabled(application.isRunning)
        .focusSection()
    }

    private var visibleAssessments: [PaperOption] {
        application.selectedPaper.assessmentKind == .questionBank
            ? board.questionBanks
            : board.fullPapers
    }
}

private struct GenerationProgress: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            if let progress = application.generationProgress {
                ProgressView(value: progress) {
                    HStack {
                        Text(application.status)
                        Spacer()
                        if let estimate = application.generationEstimate {
                            Text(estimate.remainingText)
                                .foregroundStyle(.secondary)
                        }
                    }
                } currentValueLabel: {
                    Text(progress.formatted(.percent.precision(.fractionLength(0))))
                }
            } else {
                ProgressView(application.status)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Paper creation progress")
        .accessibilityValue(accessibilityValue)
        .accessibilityAddTraits(.updatesFrequently)
    }

    private var accessibilityValue: String {
        var parts = [application.status]
        if let progress = application.generationProgress {
            parts.append(progress.formatted(.percent.precision(.fractionLength(0))))
        }
        if let estimate = application.generationEstimate {
            parts.append(estimate.remainingText)
        }
        return parts.joined(separator: ", ")
    }
}

private struct RecentDocuments: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Recent Documents")
                    .font(.headline)
                if !application.generatedFiles.isEmpty {
                    Text(application.generatedFiles.count, format: .number)
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("\(application.generatedFiles.count) documents")
                }
                Spacer()
                Button("Open Output Folder", action: application.openOutputFolder)
            }
            .padding(.horizontal, 20)
            .padding(.top, 14)

            if !application.generatedFiles.isEmpty {
                TipView(PaperCreationTips.quality)
                    .padding(.horizontal, 20)
            }

            GeneratedFilesTable(files: application.generatedFiles)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .padding(.bottom, 12)
        .focusSection()
    }
}

private struct QualityInspector: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        Form {
            Section("Qualification") {
                qualityRow(
                    "Engineering",
                    detail: application.selectedPaper.readiness.engineeringValidated
                        ? "Generation, validation, rendering, and packaging checks pass."
                        : "Engineering validation is incomplete for this paper.",
                    state: application.selectedPaper.readiness.engineeringValidated ? .passed : .pending
                )
                qualityRow(
                    "Originality",
                    detail: originalityDetail,
                    state: originalityState
                )
                qualityRow(
                    "Visual profile",
                    detail: application.selectedPaper.readiness.visuallyCalibrated
                        ? "Reference geometry has been reviewed."
                        : "This paper still needs a completed visual calibration.",
                    state: application.selectedPaper.readiness.visuallyCalibrated ? .passed : .pending
                )
                qualityRow(
                    "Reference demand",
                    detail: referenceDemandDetail,
                    state: referenceDemandState
                )
                qualityRow(
                    "Empirical demand",
                    detail: application.selectedPaper.readiness.empiricallyCalibrated
                        ? "Independent student and marker calibration is complete."
                        : "The paper targets the board demand profile; equivalent difficulty is not claimed.",
                    state: application.selectedPaper.readiness.empiricallyCalibrated ? .passed : .pending
                )
            }

            if let report = application.lastQualityReport {
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
                    LabeledContent(
                        "Demand profile",
                        value: report.referenceDemandPassed == true ? "Passed" : "Review needed"
                    )
                    if report.referenceDemandItems > 0 {
                        LabeledContent(
                            "Demand evidence",
                            value: "\(report.referenceDemandItems) items · \(report.referenceDemandDocuments) reference papers"
                        )
                    }
                    if let distance = report.referenceDemandMaxDistance {
                        LabeledContent(
                            "Maximum demand drift",
                            value: distance.formatted(.number.precision(.fractionLength(2)))
                        )
                    }
                    if report.difficultyReviewedItems > 0 {
                        LabeledContent(
                            "Independent item reviews",
                            value: "\(report.difficultyReviewedItems) of \(report.referenceDemandItems)"
                        )
                        LabeledContent(
                            "Reasoning range",
                            value: "\(report.difficultyReasoningFitItems) of \(report.difficultyReviewedItems) fit"
                        )
                        LabeledContent(
                            "Context use",
                            value: "\(report.difficultyContextFitItems) of \(report.difficultyReviewedItems) fit"
                        )
                        LabeledContent(
                            "Shortcut resistance",
                            value: "\(report.difficultyShortcutFitItems) of \(report.difficultyReviewedItems) pass"
                        )
                    }
                    if let coverage = report.referenceDemandExtractionCoverage {
                        LabeledContent(
                            "Reference extraction",
                            value: coverage.formatted(.percent.precision(.fractionLength(0)))
                        )
                    }
                }
            }

            if application.isRunning || !application.progressEntries.isEmpty {
                Section("Activity") {
                    ForEach(application.progressEntries.suffix(6)) { entry in
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
        if application.dryRun {
            return .preview
        }
        return application.lastQualityReport == nil ? .atCreation : .passed
    }

    private var originalityDetail: String {
        if application.dryRun {
            return "History comparison is skipped for preview drafts."
        }
        if application.lastQualityReport == nil {
            return "Draft and history similarity are checked before files are published."
        }
        return "Draft and historic-item similarity passed the release threshold."
    }

    private var referenceDemandState: QualityState {
        guard let report = application.lastQualityReport else { return .atCreation }
        return report.referenceDemandPassed == true ? .passed : .pending
    }

    private var referenceDemandDetail: String {
        guard let report = application.lastQualityReport else {
            return "Every generated item and the complete form are checked against aggregate patterns from relevant papers."
        }
        if report.referenceDemandPassed == true {
            return "Item depth and whole-paper mark, command-word, and demand distributions match the configured reference envelope."
        }
        return "The latest package moved outside its reference-demand envelope and needs review."
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
