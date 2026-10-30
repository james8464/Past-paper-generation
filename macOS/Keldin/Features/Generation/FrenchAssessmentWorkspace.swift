// Present French NSI generation, reference and teacher-review actions.

import SwiftUI

enum FrenchWorkspaceLayoutPolicy {
    static func contentWidth(for availableWidth: CGFloat) -> CGFloat {
        max(0, min(availableWidth - 32, 720))
    }
}

struct FrenchWorkspacePresentation {
    let hasReferences: Bool
    let isRunning: Bool

    var showsPrepareReferences: Bool { !hasReferences }

    var blocker: String? {
        guard !isRunning else { return nil }
        if !hasReferences { return "Prepare French references first." }
        return nil
    }

    var canGenerate: Bool { !isRunning && blocker == nil }
}

struct FrenchAssessmentWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @State private var largePrint = false
    @State private var showDownloadConsent = false
    @State private var showDeleteReferences = false
    @State private var showTeacherReview = false
    @State private var showMoreOptions = false
    @State private var showReferenceGuidance = false

    var body: some View {
        GeometryReader { geometry in
            form
                .frame(width: FrenchWorkspaceLayoutPolicy.contentWidth(for: geometry.size.width))
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .navigationTitle("Baccalauréat · NSI")
        .focusedSceneValue(\.keldinCreationContext, KeldinCreationContext.french(largePrint: largePrint)
            .presentingModal(showTeacherReview || showDownloadConsent || showDeleteReferences))
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                if application.isRunning {
                    Button("Cancel", role: .cancel, action: application.cancelGeneration)
                } else {
                    Button("Create a draft", systemImage: "doc.badge.plus") {
                        application.generateFrenchPaper(largePrint: largePrint)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canGenerate)
                    .help(createHelp)
                    .accessibilityHint(createHelp)
                }
            }
        }
        .confirmationDialog("Download official references?", isPresented: $showDownloadConsent, titleVisibility: .visible) {
            Button("Download references", action: application.prepareFrenchReferences)
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This contacts French Ministry of Education websites and stores public PDFs on this Mac. No model training is performed and no student data is sent.")
        }
        .confirmationDialog(
            "Delete downloaded French references?",
            isPresented: $showDeleteReferences,
            titleVisibility: .visible
        ) {
            Button("Delete References", role: .destructive, action: application.deleteFrenchReferences)
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("The local reference PDFs and search index will be removed. Generated papers are not affected.")
        }
        .sheet(isPresented: $showTeacherReview) {
            FrenchTeacherReviewSheet()
                .environmentObject(application)
        }
    }

    private var form: some View {
        Form {
            Section {
                Text("NSI written practice")
                    .font(.title2.weight(.semibold))
                Text("Original, non-official practice papers. Review the questions and proposed answers before use.")
                    .foregroundStyle(.secondary)
                Text("The selected AI model writes a new draft from French references. Answers and difficulty still need review.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                LabeledContent("Written exam") {
                    Text("2027 · 3 h 30 · 3 independent exercises")
                }
                // These rows have no input state. Fresh identities refresh the
                // cached accessibility values when the interface language changes.
                .id("written-exam-\(interfaceLanguage)")
                LabeledContent("Indicative credit") {
                    Text("18 technical + 2 French language = 20")
                }
                .id("indicative-credit-\(interfaceLanguage)")
            }
            Section("Create a draft") {
                if presentation.showsPrepareReferences {
                    Label("Prepare French references first.", systemImage: "exclamationmark.circle")
                    Button("Prepare French references") { showDownloadConsent = true }
                        .disabled(application.isRunning)
                } else {
                    Label("Reference files available", systemImage: "checkmark.circle")
                    Text("The reference corpus is incomplete; its presence does not prove topic coverage.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                LabeledContent("AI provider", value: application.aiProvider.title)
                    .id("ai-provider-\(application.aiProvider.rawValue)-\(application.activeModelName)-\(interfaceLanguage)")
                LabeledContent("Model", value: application.activeModelName)
                    .id("ai-model-\(application.aiProvider.rawValue)-\(application.activeModelName)-\(interfaceLanguage)")
                ModelQualityAdviceView(provider: application.aiProvider, model: application.activeModelName)
                Text("Local models run on this Mac. Hosted providers receive the generation prompts only after your consent.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                if let blocker = application.frenchGenerationBlockerResource {
                    Text(blocker).foregroundStyle(.secondary)
                }
                Toggle("Enlarged print", isOn: $largePrint)
                    .disabled(application.isRunning)
                DisclosureGroup("More options", isExpanded: $showMoreOptions) {
                    Picker("Interface language", selection: $interfaceLanguage) {
                        Text("System").tag("system")
                        Text("English").tag("en")
                        Text("Français").tag("fr")
                    }
                    .disabled(application.isRunning)
                    LabeledContent("Save to", value: application.outputFolder.lastPathComponent)
                    Button("Choose output folder…", action: application.chooseOutputFolder)
                        .disabled(application.isRunning)
                }
            }
            Section("Occitanie case study") {
                Text("A separate French activity using 12 public school records from Occitanie. Includes an activity PDF and proposed answers, without an exam mark or official endorsement.")
                    .foregroundStyle(.secondary)
                Button("Create the Occitanie case study", action: application.generateOccitanieActivity)
                    .disabled(application.isRunning || application.benchmarkCoordinator.isRunning)
            }
            Section("Review and guidance") {
                Text("Read both PDFs and the validation record. Check the difficulty and timing before use. Automated checks do not establish classroom suitability.")
                Button("Record a teacher review…") { showTeacherReview = true }
                    .disabled(application.isRunning)
                DisclosureGroup("References and privacy", isExpanded: $showReferenceGuidance) {
                    Text("Official sources are downloaded with your permission. The chosen provider creates the draft; no official approval or calibrated difficulty is implied.")
                    if application.hasFrenchReferences {
                        Button("Delete downloaded French references", role: .destructive) {
                            showDeleteReferences = true
                        }
                        .disabled(application.isRunning)
                    }
                    Link("Official NSI examination rules", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
                        .foregroundStyle(Color("ForegroundAccent"))
                    Button("Open the French NSI help guide") {
                        application.showHelpGuide(topic: .frenchBaccalaureat)
                    }
                }
            }
            if !application.isRunning, !application.progressEntries.isEmpty {
                Section("Status") { Text(application.status) }
            }
            if !application.isRunning, !application.currentGenerationFiles.isEmpty {
                PaperQualitySummarySection(report: application.lastQualityReport, frenchReport: application.lastFrenchDraftQualityReport)
            }
        }
        .formStyle(.grouped)
    }

    private var canGenerate: Bool {
        application.frenchGenerationBlockerResource == nil && KeldinCreationContext.french(largePrint: largePrint).canCreate(
            boardCanGenerate: false,
            hasFrenchReferences: application.hasFrenchReferences,
            isBusy: application.isRunning || application.benchmarkCoordinator.isRunning || application.showWelcome
        )
    }

    private var presentation: FrenchWorkspacePresentation {
        FrenchWorkspacePresentation(
            hasReferences: application.hasFrenchReferences,
            isRunning: application.isRunning
        )
    }

    private var createHelp: String {
        if let blocker = application.frenchGenerationBlockerResource {
            return InterfaceText.resolve(blocker, language: interfaceLanguage)
        }
        return localizedValue(presentation.blocker ?? "Create a non-official practice paper with indicative marking guidance.")
    }

    private func localizedValue(_ key: String) -> String {
        let language = interfaceLanguage == "system"
            ? Locale.current.language.languageCode?.identifier ?? "en"
            : interfaceLanguage
        guard let path = Bundle.main.path(forResource: language, ofType: "lproj"),
              let bundle = Bundle(path: path) else { return key }
        return bundle.localizedString(forKey: key, value: key, table: "Localizable")
    }
}

private struct FrenchTeacherReviewSheet: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @Environment(\.dismiss) private var dismiss
    @State private var reviewer = ""
    @State private var decision = FrenchReviewDecision.revise
    @State private var notes = ""
    @State private var scores = Dictionary(
        uniqueKeysWithValues: FrenchReviewRequest.rubricKeys.map { ($0, 3) }
    )

    var body: some View {
        VStack(spacing: 0) {
            Form {
                Section {
                    Text("Teacher review")
                        .font(.title2.weight(.semibold))
                    Text("This is a self-attested review record, not an official signature or examiner endorsement.")
                        .foregroundStyle(.secondary)
                    TextField("Reviewer name", text: $reviewer)
                    Picker("Decision", selection: $decision) {
                        ForEach(FrenchReviewDecision.allCases) { option in
                            Text(LocalizedStringKey(option.localizationKey)).tag(option)
                        }
                    }
                }
                Section("Rubric · 1 to 4") {
                    ForEach(FrenchReviewRequest.rubricKeys, id: \.self) { key in
                        Picker(LocalizedStringKey(FrenchReviewRubric.localizationKey(for: key)), selection: scoreBinding(for: key)) {
                            ForEach(1 ... 4, id: \.self) { score in
                                Text(score, format: .number).tag(score)
                            }
                        }
                        .pickerStyle(.menu)
                        .accessibilityIdentifier("french-review-\(key)")
                    }
                }
                Section("Review notes") {
                    TextEditor(text: $notes)
                        .frame(minHeight: 110)
                        .accessibilityLabel(Text("Review notes"))
                }
            }
            .formStyle(.grouped)

            Divider()
            HStack {
                Button("Cancel") { dismiss() }
                    .keyboardShortcut(.cancelAction)
                Spacer()
                Button("Save review…") {
                    let outcome = application.recordFrenchReview(
                        reviewer: reviewer,
                        decision: decision,
                        scores: scores,
                        notes: notes
                    )
                    if outcome.closesReviewForm { dismiss() }
                }
                .keyboardShortcut(.defaultAction)
                .buttonStyle(.borderedProminent)
                .disabled(
                    reviewer.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        || notes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                )
            }
            .padding(16)
        }
        .frame(width: 620, height: 690)
    }

    private func scoreBinding(for key: String) -> Binding<Int> {
        Binding(
            get: { scores[key] ?? 1 },
            set: { scores[key] = $0 }
        )
    }
}
