import SwiftUI

enum FrenchWorkspaceLayoutPolicy {
    static func contentWidth(for availableWidth: CGFloat) -> CGFloat {
        max(0, min(availableWidth - 32, 720))
    }
}

struct FrenchWorkspacePresentation {
    let hasReferences: Bool
    let model: String
    let isRunning: Bool
    let ollamaState: OllamaState
    let availableModels: [String]
    let hasLoadedModels: Bool

    var showsPrepareReferences: Bool { !hasReferences }

    var blocker: String? {
        guard !isRunning else { return nil }
        if !hasReferences { return "Prepare French references first." }
        let selectedModel = model.trimmingCharacters(in: .whitespacesAndNewlines)
        if selectedModel.isEmpty {
            return "Choose a local Ollama model first."
        }
        if ollamaState.message == "Not checked" { return "Check Ollama before creating a draft." }
        if !ollamaState.installed { return "Install Ollama before creating a draft." }
        if !ollamaState.running { return "Start Ollama before creating a draft." }
        if hasLoadedModels && !availableModels.contains(selectedModel) {
            return "Install the selected Ollama model before creating a draft."
        }
        return nil
    }

    var canGenerate: Bool { !isRunning && blocker == nil }

    var showsOllamaRecheck: Bool {
        guard let blocker else { return false }
        return [
            "Check Ollama before creating a draft.",
            "Install Ollama before creating a draft.",
            "Start Ollama before creating a draft.",
            "Install the selected Ollama model before creating a draft."
        ].contains(blocker)
    }
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
                Text("Original, non-official drafts for teachers to review before classroom use.")
                    .foregroundStyle(.secondary)
                Text("V32 uses three app-authored case families, not model-generated questions. New drafts may repeat a family.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                LabeledContent("Written exam") {
                    Text(localizedValue("2027 · 3 h 30 · 3 independent exercises"))
                }
                LabeledContent("Indicative credit") {
                    Text(localizedValue("18 technical + 2 French language = 20"))
                }
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
                TextField("Local Ollama model", text: $application.selectedModel)
                    .disabled(application.isRunning)
                Text("Ollama is currently checked for the run record, but the selected model does not write V32 papers. This does not qualify the model.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
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
                    Button("Choose output folder", action: application.chooseOutputFolder)
                        .disabled(application.isRunning)
                }
                if let blocker = presentation.blocker,
                   !presentation.showsPrepareReferences {
                    Text(localizedValue(blocker))
                        .font(.callout)
                        .foregroundStyle(.secondary)
                    if blocker == "Install Ollama before creating a draft." {
                        Button("Get Ollama", action: application.openOllamaDownload)
                    } else if blocker == "Install the selected Ollama model before creating a draft.",
                              application.distributionMode.canManageOllama {
                        Button("Download selected model", action: application.pullSelectedModel)
                    } else if blocker == "Install the selected Ollama model before creating a draft." {
                        Text("Install this model in Ollama, then check again.")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    if presentation.showsOllamaRecheck {
                        Button("Check Ollama", action: application.refreshOllama)
                    }
                }
            }
            Section("Review and guidance") {
                Text("Check both PDFs, the validation record, difficulty and timing. Automated checks do not replace an NSI teacher.")
                Button("Record a teacher review") { showTeacherReview = true }
                    .disabled(application.isRunning)
                DisclosureGroup("References and privacy", isExpanded: $showReferenceGuidance) {
                    Text("Official sources are downloaded with your permission. V32 builds papers on this Mac without model prompts or cloud generation.")
                    if application.hasFrenchReferences {
                        Button("Delete downloaded French references", role: .destructive) {
                            showDeleteReferences = true
                        }
                        .disabled(application.isRunning)
                    }
                    Link("Official NSI examination rules", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
                    Button("Open the French NSI help guide") {
                        application.showHelpGuide(topic: .frenchBaccalaureat)
                    }
                }
            }
            if application.isRunning {
                Section {
                    ProgressView()
                    Text(application.status)
                        .accessibilityLabel(Text("Generation status"))
                }
            } else if !application.progressEntries.isEmpty {
                Section("Status") { Text(application.status) }
            }
        }
        .formStyle(.grouped)
    }

    private var canGenerate: Bool {
        presentation.canGenerate
    }

    private var presentation: FrenchWorkspacePresentation {
        FrenchWorkspacePresentation(
            hasReferences: application.hasFrenchReferences,
            model: application.selectedModel,
            isRunning: application.isRunning,
            ollamaState: application.ollamaState,
            availableModels: application.availableModels,
            hasLoadedModels: application.hasLoadedOllamaModels
        )
    }

    private var createHelp: String {
        localizedValue(presentation.blocker ?? "Create a non-official draft for teacher review.")
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
                        Stepper(value: scoreBinding(for: key), in: 1 ... 4) {
                            LabeledContent(
                                LocalizedStringKey(FrenchReviewRubric.localizationKey(for: key)),
                                value: String(scores[key] ?? 1)
                            )
                        }
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
                Button("Choose Reviewed Bundle and Record") {
                    application.recordFrenchReview(
                        reviewer: reviewer,
                        decision: decision,
                        scores: scores,
                        notes: notes
                    )
                    dismiss()
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
