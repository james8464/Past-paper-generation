import SwiftUI

private struct PaperCreationContextKey: FocusedValueKey {
    typealias Value = PaperCreationContext
}

extension FocusedValues {
    var paperCreationContext: PaperCreationContext? {
        get { self[PaperCreationContextKey.self] }
        set { self[PaperCreationContextKey.self] = newValue }
    }
}

struct AppCommands: Commands {
    @ObservedObject var application: ApplicationCoordinator
    @FocusedObject private var documentActions: DocumentActionController?
    @FocusedValue(\.paperCreationContext) private var creationContext

    private var canCreate: Bool {
        creationContext?.canCreate(
            boardCanGenerate: application.canGenerate,
            hasFrenchReferences: application.hasFrenchReferences,
            isBusy: application.isRunning || application.benchmarkCoordinator.isRunning || application.showWelcome
        ) == true
    }

    private func createPaper() {
        guard canCreate, let creationContext else { return }
        switch creationContext {
        case .board: application.generate()
        case let .french(largePrint): application.generateFrenchPaper(largePrint: largePrint)
        }
    }

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("New Paper", action: application.showCreationWorkspace)
                .keyboardShortcut("n", modifiers: [.command])

            Button("Create Paper", action: createPaper)
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(!canCreate)

            Button("Cancel Generation", action: application.cancelGeneration)
                .keyboardShortcut(".", modifiers: [.command])
                .disabled(!application.isRunning)

            Divider()
        }

        CommandGroup(replacing: .printItem) {
            Button("Print…") { documentActions?.printSelected() }
                .keyboardShortcut("p", modifiers: [.command])
                .disabled(documentActions?.canAccessDocument != true)
        }

        CommandGroup(after: .saveItem) {
            Button("Export…") { documentActions?.exportSelected() }
                .keyboardShortcut("e", modifiers: [.command, .shift])
                .disabled(documentActions?.canAccessDocument != true)

            Button("Quick Look") { documentActions?.quickLookSelected() }
                .keyboardShortcut("y", modifiers: [.command])
                .disabled(documentActions?.canAccessDocument != true)

            Button("Reveal in Finder") { documentActions?.revealSelected() }
                .disabled(documentActions?.canAccessDocument != true)

            Button("Copy Provenance") { documentActions?.copyProvenance() }
                .disabled(documentActions?.provenance == nil)

            Divider()

            Button("Open Output Folder", action: application.openOutputFolder)
                .keyboardShortcut("o", modifiers: [.command, .option])

            Divider()

            Button("Open Latest Question Paper") {
                application.previewGeneratedFile(role: "question_paper")
            }
            .disabled(!application.hasGeneratedFile(role: "question_paper"))

            Button("Open Latest Mark Scheme") {
                application.previewGeneratedFile(role: "mark_scheme")
            }
            .disabled(!application.hasGeneratedFile(role: "mark_scheme"))

            Button("Reveal Latest Question Paper in Finder") {
                application.revealGeneratedFile(role: "question_paper")
            }
            .disabled(!application.hasGeneratedFile(role: "question_paper"))
        }

        CommandMenu("Tools") {
            Button("Show Documents", action: application.showDocuments)
                .keyboardShortcut("d", modifiers: [.command, .shift])

            Button("Show History", action: application.showHistory)
                .keyboardShortcut("y", modifiers: [.command, .shift])

            Button("Show Benchmark") {
                application.showBenchmarkPage()
            }
            .keyboardShortcut("b", modifiers: [.command, .shift])

            Divider()

            Button("Run Benchmark", action: application.startBenchmark)
                .disabled(application.isRunning || application.benchmarkCoordinator.isRunning)

            Button("Cancel Benchmark", action: application.cancelBenchmark)
                .disabled(!application.benchmarkCoordinator.isRunning)

            Divider()

            Button("Copy Diagnostic Summary", action: application.copyDiagnosticSummary)
        }

        CommandGroup(replacing: .help) {
            Button("Keldin Help") {
                application.showHelpGuide()
            }
            .keyboardShortcut("h", modifiers: [.command, .shift])

            Button("Show Welcome Guide", action: application.showWelcomeGuide)

            Divider()

            Button("Open User Guide", action: application.openProjectHelp)
            Button("Privacy Policy", action: application.openPrivacyPolicy)
            Button("Report an Issue", action: application.openSupportPage)

            Divider()

            Button("Copy Diagnostic Summary", action: application.copyDiagnosticSummary)
        }
    }

}
