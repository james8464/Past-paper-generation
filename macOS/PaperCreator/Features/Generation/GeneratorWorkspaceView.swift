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
                    detail: qualificationDetail(
                        saved: application.lastQualityReport?.engineeringValidated,
                        current: application.selectedPaper.readiness.engineeringValidated,
                        passed: "Generation, validation, rendering, and packaging checks pass.",
                        pending: "Engineering validation is incomplete for this paper."
                    ),
                    state: qualificationState(
                        saved: application.lastQualityReport?.engineeringValidated,
                        current: application.selectedPaper.readiness.engineeringValidated
                    )
                )
                qualityRow(
                    "Originality",
                    detail: originalityDetail,
                    state: originalityState
                )
                qualityRow(
                    "Visual profile",
                    detail: qualificationDetail(
                        saved: application.lastQualityReport?.visuallyCalibrated,
                        current: application.selectedPaper.readiness.visuallyCalibrated,
                        passed: "Reference geometry has been reviewed.",
                        pending: "This paper still needs a completed visual calibration."
                    ),
                    state: qualificationState(
                        saved: application.lastQualityReport?.visuallyCalibrated,
                        current: application.selectedPaper.readiness.visuallyCalibrated
                    )
                )
                qualityRow(
                    "Reference demand",
                    detail: referenceDemandDetail,
                    state: referenceDemandState
                )
                qualityRow(
                    "Empirical demand",
                    detail: qualificationDetail(
                        saved: application.lastQualityReport?.empiricallyCalibrated,
                        current: application.selectedPaper.readiness.empiricallyCalibrated,
                        passed: "Independent student and marker calibration is complete.",
                        pending: "The paper targets the board demand profile; equivalent difficulty is not claimed."
                    ),
                    state: qualificationState(
                        saved: application.lastQualityReport?.empiricallyCalibrated,
                        current: application.selectedPaper.readiness.empiricallyCalibrated
                    )
                )
                qualityRow(
                    "Candidate paths",
                    detail: presentation.pathEvidenceDetail,
                    state: presentation.pathEvidenceState
                )
            }

            if let report = application.lastQualityReport {
                Section("Latest package") {
                    LabeledContent("Items", value: "\(report.itemCount)")
                    LabeledContent("Saved mode", value: report.savedMode.rawValue)
                    if let subject = report.identity.subject,
                       let paper = report.identity.paper {
                        LabeledContent("Saved target", value: "\(subject) · \(paper)")
                    }
                    if let seed = report.identity.seed {
                        LabeledContent("Saved seed", value: "\(seed)")
                    }
                    if let jobID = report.identity.jobID {
                        LabeledContent("Saved job", value: jobID)
                    }
                    if let formID = report.identity.formID {
                        LabeledContent("Saved form", value: formID)
                    }
                    if let generatorID = report.identity.generatorID {
                        let value = [generatorID, report.identity.generatorVersion]
                            .compactMap { $0 }
                            .joined(separator: " · ")
                        LabeledContent("Saved generator", value: value)
                    }
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
                            value: fitCount(
                                report.difficultyReasoningFitItems,
                                reviewed: report.difficultyReviewedItems,
                                suffix: "fit"
                            )
                        )
                        LabeledContent(
                            "Context use",
                            value: fitCount(
                                report.difficultyContextFitItems,
                                reviewed: report.difficultyReviewedItems,
                                suffix: "fit"
                            )
                        )
                        LabeledContent(
                            "Shortcut resistance",
                            value: fitCount(
                                report.difficultyShortcutFitItems,
                                reviewed: report.difficultyReviewedItems,
                                suffix: "pass"
                            )
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
        state: GenerationQualityState
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

    private var presentation: GenerationQualityPresentation {
        GenerationQualityPolicy.presentation(for: application.lastQualityReport)
    }

    private var originalityState: GenerationQualityState {
        presentation.originalityState
    }

    private var originalityDetail: String {
        presentation.originalityDetail
    }

    private var referenceDemandState: GenerationQualityState {
        presentation.referenceDemandState
    }

    private var referenceDemandDetail: String {
        presentation.referenceDemandDetail
    }

    private func fitCount(_ count: Int?, reviewed: Int, suffix: String) -> String {
        count.map { "\($0) of \(reviewed) \(suffix)" } ?? "Unknown"
    }

    private func qualificationState(
        saved: Bool?,
        current: Bool
    ) -> GenerationQualityState {
        if application.lastQualityReport != nil {
            return saved.map { $0 ? .passed : .pending } ?? .unknown
        }
        return current ? .passed : .pending
    }

    private func qualificationDetail(
        saved: Bool?,
        current: Bool,
        passed: String,
        pending: String
    ) -> String {
        if application.lastQualityReport != nil, saved == nil {
            return "This evidence is not recorded in the saved package."
        }
        return (saved ?? current) ? passed : pending
    }
}

private extension GenerationQualityState {
    var systemImage: String {
        switch self {
        case .passed: "checkmark.circle.fill"
        case .pending: "clock"
        case .preview: "eye"
        case .atCreation: "checkmark.shield"
        case .unknown: "questionmark.circle"
        }
    }

    var color: Color {
        switch self {
        case .passed: .green
        case .pending: .orange
        case .preview: .secondary
        case .atCreation: .secondary
        case .unknown: .secondary
        }
    }
}
