// Define Keldin's menu actions and route them through the application coordinator.

import SwiftUI

private struct KeldinCreationContextKey: FocusedValueKey {
    typealias Value = KeldinCreationContext
}

extension FocusedValues {
    var keldinCreationContext: KeldinCreationContext? {
        get { self[KeldinCreationContextKey.self] }
        set { self[KeldinCreationContextKey.self] = newValue }
    }
}

struct AppCommands: Commands {
    @ObservedObject var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @FocusedObject private var documentActions: DocumentActionController?
    @FocusedObject private var modelDownloadPresentation: ModelDownloadPresentation?
    @FocusedValue(\.keldinCreationContext) private var creationContext

    private var canNavigate: Bool {
        KeldinCreationContext.allowsNavigation(
            from: creationContext,
            applicationModal: application.hasCommandBlockingPresentation || modelDownloadPresentation?.blocksCommands == true
        )
    }

    private var canCreate: Bool {
        canNavigate && creationContext?.canCreate(
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
        case .presentingModal: return
        }
    }

    private var canAccessDocument: Bool {
        canNavigate
            && documentActions?.canAccessDocument == true
    }

    private var canCopyProvenance: Bool {
        canNavigate
            && documentActions?.provenance != nil
    }

    private func localized(_ resource: LocalizedStringResource) -> String {
        InterfaceText.resolve(resource, language: interfaceLanguage)
    }

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button(localized("New Paper")) {
                guard canNavigate else { return }
                application.showCreationWorkspace()
            }
                .keyboardShortcut("n", modifiers: [.command])
                .disabled(!canNavigate)

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
                guard canNavigate else { return }
                application.previewGeneratedFile(role: "question_paper")
            }
            .disabled(!canNavigate || !application.hasGeneratedFile(role: "question_paper"))

            Button(localized("Open Latest Mark Scheme")) {
                guard canNavigate else { return }
                application.previewGeneratedFile(role: "mark_scheme")
            }
            .disabled(!canNavigate || !application.hasGeneratedFile(role: "mark_scheme"))

            Button(localized("Reveal Latest Question Paper in Finder")) {
                application.revealGeneratedFile(role: "question_paper")
            }
            .disabled(!application.hasGeneratedFile(role: "question_paper"))
        }

        CommandMenu(localized("Tools")) {
            Button(localized("Show Documents")) {
                guard canNavigate else { return }
                application.showDocuments()
            }
                .keyboardShortcut("d", modifiers: [.command, .shift])
                .disabled(!canNavigate)

            Button(localized("Show History")) {
                guard canNavigate else { return }
                application.showHistory()
            }
                .keyboardShortcut("y", modifiers: [.command, .shift])
                .disabled(!canNavigate)

            Button(localized("Show Benchmark")) {
                guard canNavigate else { return }
                application.showBenchmarkPage()
            }
            .keyboardShortcut("b", modifiers: [.command, .shift])
            .disabled(!canNavigate)

            Divider()

            Button(localized("Run Benchmark")) {
                guard canNavigate else { return }
                application.startBenchmark()
            }
                .disabled(!canNavigate || application.isRunning || application.benchmarkCoordinator.isRunning)

            Button(localized("Cancel Benchmark"), action: application.cancelBenchmark)
                .disabled(!application.benchmarkCoordinator.isRunning)

            Divider()

            Button(localized("Copy Diagnostic Summary"), action: application.copyDiagnosticSummary)
        }

        CommandGroup(replacing: .help) {
            Button(localized("Keldin Help")) {
                guard canNavigate else { return }
                application.showHelpGuide()
            }
            .keyboardShortcut("h", modifiers: [.command, .shift])
            .disabled(!canNavigate)

            Button(localized("Show Welcome Guide")) {
                guard canNavigate else { return }
                application.showWelcomeGuide()
            }
            .disabled(!canNavigate)

            Divider()

            Button(localized("Open User Guide"), action: application.openProjectHelp)
            Button(localized("Privacy Policy"), action: application.openPrivacyPolicy)
            Button(localized("Report an Issue"), action: application.openSupportPage)

            Divider()

            Button(localized("Copy Diagnostic Summary"), action: application.copyDiagnosticSummary)
        }
    }

}
