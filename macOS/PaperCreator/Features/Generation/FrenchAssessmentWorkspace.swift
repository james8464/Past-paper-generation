import SwiftUI

struct FrenchAssessmentWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @State private var largePrint = false
    @State private var showDownloadConsent = false

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
                Link("Official NSI examination rules", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
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
    }
}
