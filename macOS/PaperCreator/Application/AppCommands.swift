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
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @FocusedObject private var documentActions: DocumentActionController?
    @FocusedValue(\.paperCreationContext) private var creationContext

    private var canCreate: Bool {
        creationContext?.canCreate(
            boardCanGenerate: application.canGenerate,
            hasFrenchReferences: application.hasFrenchReferences,
            isBusy: application.isRunning || application.benchmarkCoordinator.isRunning || application.showWelcome || application.showHelp
        ) == true
    }

    private func createPaper() {
        guard canCreate, let creationContext else { return }
        switch creationContext {
        case .board: application.generate()
        case let .french(largePrint): application.generateFrenchPaper(largePrint: largePrint)
        }
    }

    private var canAccessDocument: Bool {
        !application.showWelcome && !application.showHelp
            && documentActions?.canAccessDocument == true
    }

    private var canCopyProvenance: Bool {
        !application.showWelcome && !application.showHelp
            && documentActions?.provenance != nil
    }

    private func localized(_ resource: LocalizedStringResource) -> String {
        InterfaceText.resolve(resource, language: interfaceLanguage)
    }

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button(localized("New Paper"), action: application.showCreationWorkspace)
                .keyboardShortcut("n", modifiers: [.command])

            Button(localized("Create Paper"), action: createPaper)
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(!canCreate)

            Button(localized("Cancel Generation"), action: application.cancelGeneration)
                .keyboardShortcut(".", modifiers: [.command])
                .disabled(!application.isRunning)

            Divider()
        }

        CommandGroup(replacing: .printItem) {
            Button(localized("Print…")) {
                guard canAccessDocument else { return }
                documentActions?.printSelected()
            }
                .keyboardShortcut("p", modifiers: [.command])
                .disabled(!canAccessDocument)
        }

        CommandGroup(after: .saveItem) {
            Button(localized("Export…")) {
                guard canAccessDocument else { return }
                documentActions?.exportSelected()
            }
                .keyboardShortcut("e", modifiers: [.command, .shift])
                .disabled(!canAccessDocument)

            Button(localized("Quick Look")) {
                guard canAccessDocument else { return }
                documentActions?.quickLookSelected()
            }
                .keyboardShortcut("y", modifiers: [.command])
                .disabled(!canAccessDocument)

            Button(localized("Reveal in Finder")) {
                guard canAccessDocument else { return }
                documentActions?.revealSelected()
            }
                .disabled(!canAccessDocument)

            Button(localized("Copy Provenance")) {
                guard canCopyProvenance else { return }
                documentActions?.copyProvenance()
            }
                .disabled(!canCopyProvenance)

            Divider()

            Button(localized("Open Output Folder"), action: application.openOutputFolder)
                .keyboardShortcut("o", modifiers: [.command, .option])

            Divider()

            Button(localized("Open Latest Question Paper")) {
                application.previewGeneratedFile(role: "question_paper")
            }
            .disabled(!application.hasGeneratedFile(role: "question_paper"))

            Button(localized("Open Latest Mark Scheme")) {
                application.previewGeneratedFile(role: "mark_scheme")
            }
            .disabled(!application.hasGeneratedFile(role: "mark_scheme"))

            Button(localized("Reveal Latest Question Paper in Finder")) {
                application.revealGeneratedFile(role: "question_paper")
            }
            .disabled(!application.hasGeneratedFile(role: "question_paper"))
        }

        CommandMenu(localized("Tools")) {
            Button(localized("Show Documents"), action: application.showDocuments)
                .keyboardShortcut("d", modifiers: [.command, .shift])

            Button(localized("Show History"), action: application.showHistory)
                .keyboardShortcut("y", modifiers: [.command, .shift])

            Button(localized("Show Benchmark")) {
                application.showBenchmarkPage()
            }
            .keyboardShortcut("b", modifiers: [.command, .shift])

            Divider()

            Button(localized("Run Benchmark"), action: application.startBenchmark)
                .disabled(application.isRunning || application.benchmarkCoordinator.isRunning)

            Button(localized("Cancel Benchmark"), action: application.cancelBenchmark)
                .disabled(!application.benchmarkCoordinator.isRunning)

            Divider()

            Button(localized("Copy Diagnostic Summary"), action: application.copyDiagnosticSummary)
        }

        CommandGroup(replacing: .help) {
            Button(localized("Keldin Help")) {
                application.showHelpGuide()
            }
            .keyboardShortcut("h", modifiers: [.command, .shift])

            Button(localized("Show Welcome Guide"), action: application.showWelcomeGuide)

            Divider()

            Button(localized("Open User Guide"), action: application.openProjectHelp)
            Button(localized("Privacy Policy"), action: application.openPrivacyPolicy)
            Button(localized("Report an Issue"), action: application.openSupportPage)

            Divider()

            Button(localized("Copy Diagnostic Summary"), action: application.copyDiagnosticSummary)
        }
    }

}
