import SwiftUI

struct FrenchAssessmentWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @State private var largePrint = false
    @State private var showDownloadConsent = false
    @State private var showDeleteReferences = false
    @State private var showTeacherReview = false

    var body: some View {
        Form {
            Section {
                Text("French written-paper prototype").font(.title2).fontWeight(.semibold)
                Text("Original practice papers in French. Teacher review is required before classroom assessment.")
                    .foregroundStyle(.secondary)
                LabeledContent("Qualification", value: "Baccalauréat général")
                LabeledContent("Stage", value: "Terminale")
                LabeledContent("Speciality", value: "Numérique et sciences informatiques")
                LabeledContent("Assessment", value: "Partie écrite · 2027 · 3 h 30 · /20")
                Text("Three independent exercises: 18 technical points, plus 2 points for French. The practical component is not included.")
            }
            Section("References and privacy") {
                Text("Official sources are downloaded only with your permission. Generation uses Ollama on this Mac; no student answers are collected.")
                Button("Prepare French references") { showDownloadConsent = true }
                    .disabled(application.isRunning)
                if application.hasFrenchReferences {
                    Button("Delete downloaded French references", role: .destructive) {
                        showDeleteReferences = true
                    }
                    .disabled(application.isRunning)
                }
                Text("The initial corpus is incomplete. Its existence does not mean that every topic or exam session is covered.")
                    .font(.callout).foregroundStyle(.secondary)
            }
            Section("Model and document") {
                TextField("Local Ollama model", text: $application.selectedModel)
                Text("Gemma 4 12B is the comparison baseline, not a validated French recommendation. Results with all models require review.")
                    .font(.callout).foregroundStyle(.secondary)
                Toggle("Enlarged print", isOn: $largePrint)
                Picker("Interface language", selection: $interfaceLanguage) {
                    Text("System").tag("system")
                    Text("English").tag("en")
                    Text("Français").tag("fr")
                }
                Text("Changing the interface language does not change the curriculum or the French language of the paper.")
                    .font(.callout).foregroundStyle(.secondary)
                LabeledContent("Save to", value: application.outputFolder.lastPathComponent)
                Button("Choose output folder", action: application.chooseOutputFolder)
                Button("Create an unreviewed draft") { application.generateFrenchPaper(largePrint: largePrint) }
                    .buttonStyle(.borderedProminent)
                    .disabled(application.isRunning || !application.hasFrenchReferences || application.selectedModel.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            Section("Review checklist") {
                Text("Check every answer, allocation of credit, diagram, code listing and page. Compare difficulty and timing with authentic papers. Automated checks cannot replace a French NSI teacher.")
                Button("Record a teacher review") { showTeacherReview = true }
                    .disabled(application.isRunning)
                Link("Official NSI examination rules", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
            }
            Section("How this route works") {
                LabeledContent("1", value: "Prepare the official French references")
                LabeledContent("2", value: "Create an original, unreviewed draft")
                LabeledContent("3", value: "Inspect both PDFs and the validation record")
                LabeledContent("4", value: "Record an independent teacher decision")
                Text("A recorded review is bound to the exact document hashes. Editing or regenerating any file makes that review stale.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                Button("Open the French NSI help guide") {
                    application.showHelpGuide(topic: .frenchBaccalaureat)
                }
            }
            if application.isRunning {
                Section {
                    ProgressView()
                    Text(application.status)
                        .accessibilityLabel(Text("Generation status"))
                    Button("Cancel", role: .cancel, action: application.cancelGeneration)
                }
            } else if !application.progressEntries.isEmpty {
                Section("Status") { Text(application.status) }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Baccalauréat · NSI")
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
