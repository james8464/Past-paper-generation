import SwiftUI

enum FrenchWorkspaceLayoutPolicy {
    static func contentWidth(for availableWidth: CGFloat) -> CGFloat {
        max(0, min(availableWidth - 32, 840))
    }
}

struct FrenchAssessmentWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @State private var largePrint = false
    @State private var showDownloadConsent = false
    @State private var showDeleteReferences = false
    @State private var showTeacherReview = false

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
                LabeledContent("Programme", value: "Baccalauréat général · Terminale · NSI")
                LabeledContent("Written exam") {
                    Text(localizedValue("2027 · 3 h 30 · 3 independent exercises"))
                }
                LabeledContent("Indicative credit") {
                    Text(localizedValue("18 technical + 2 French language = 20"))
                }
            }
            Section("References and privacy") {
                Text("Official sources are downloaded with your permission. French generation uses Ollama on this Mac, with no cloud fallback.")
                Button("Prepare French references") { showDownloadConsent = true }
                    .disabled(application.isRunning)
                if application.hasFrenchReferences {
                    Button("Delete downloaded French references", role: .destructive) {
                        showDeleteReferences = true
                    }
                    .disabled(application.isRunning)
                }
                Text("The reference corpus is incomplete; its presence does not prove topic coverage.")
                    .font(.callout).foregroundStyle(.secondary)
            }
            Section("Create a draft") {
                TextField("Local Ollama model", text: $application.selectedModel)
                Text("No French model is yet qualified. Gemma 4 12B is a comparison baseline, not a recommendation.")
                    .font(.callout).foregroundStyle(.secondary)
                Toggle("Enlarged print", isOn: $largePrint)
                Picker("Interface language", selection: $interfaceLanguage) {
                    Text("System").tag("system")
                    Text("English").tag("en")
                    Text("Français").tag("fr")
                }
                LabeledContent("Save to", value: application.outputFolder.lastPathComponent)
                Button("Choose output folder", action: application.chooseOutputFolder)
            }
            Section("Review and guidance") {
                Text("Check both PDFs, the validation record, difficulty and timing. Automated checks do not replace an NSI teacher.")
                Button("Record a teacher review") { showTeacherReview = true }
                    .disabled(application.isRunning)
                Link("Official NSI examination rules", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
                Button("Open the French NSI help guide") {
                    application.showHelpGuide(topic: .frenchBaccalaureat)
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
        !application.isRunning
            && application.hasFrenchReferences
            && !application.selectedModel.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private var createHelp: String {
        if !application.hasFrenchReferences {
            return localizedValue("Prepare French references first.")
        }
        if application.selectedModel.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return localizedValue("Choose a local Ollama model first.")
        }
        return localizedValue("Create a non-official draft for teacher review.")
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
