// Define Keldin's menu actions and route them through the application coordinator.

import SwiftUI

private struct KeldinCreationContextKey: FocusedValueKey {
    typealias Value = KeldinCreationContext
}

private struct KeldinMainWindowIdentityKey: FocusedValueKey {
    typealias Value = MainWindowIdentity
}

extension FocusedValues {
    var keldinMainWindowIdentity: MainWindowIdentity? {
        get { self[KeldinMainWindowIdentityKey.self] }
        set { self[KeldinMainWindowIdentityKey.self] = newValue }
    }
    var keldinCreationContext: KeldinCreationContext? {
        get { self[KeldinCreationContextKey.self] }
        set { self[KeldinCreationContextKey.self] = newValue }
    }
}

struct AppCommands: Commands {
    @Environment(\.openWindow) private var openWindow
    @ObservedObject var application: ApplicationCoordinator
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    @FocusedObject private var documentActions: DocumentActionController?
    @FocusedObject private var modelDownloadPresentation: ModelDownloadPresentation?
    @FocusedObject private var settingsPresentation: SettingsActionPresentation?
    @FocusedValue(\.keldinMainWindowIdentity) private var mainWindowIdentity
    @FocusedValue(\.keldinCreationContext) private var creationContext

    private var canNavigate: Bool {
        KeldinCreationContext.allowsNavigation(
            from: creationContext,
            applicationModal: application.hasCommandBlockingPresentation,
            mainSceneIsFocused: mainWindowIdentity != nil,
            settingsModal: modelDownloadPresentation?.blocksCommands == true || settingsPresentation?.blocksCommands == true
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

    private func navigate(_ route: MainWindowRoute) {
        guard canNavigate else { return }
        MainWindowRouting.navigate(route, application: application) {
            openWindow(id: MainWindowRouting.sceneID, value: $0)
        }
    }

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button(localized("New Paper")) {
                guard canNavigate else { return }
                navigate(.creation)
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
                navigate(.latestPreview(role: "question_paper"))
            }
            .disabled(!canNavigate || !application.hasGeneratedFile(role: "question_paper"))

            Button(localized("Open Latest Mark Scheme")) {
                guard canNavigate else { return }
                navigate(.latestPreview(role: "mark_scheme"))
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
                navigate(.documents)
            }
                .keyboardShortcut("d", modifiers: [.command, .shift])
                .disabled(!canNavigate)

            Button(localized("Show History")) {
                guard canNavigate else { return }
                navigate(.history)
            }
                .keyboardShortcut("y", modifiers: [.command, .shift])
                .disabled(!canNavigate)

            Button(localized("Show Benchmark")) {
                guard canNavigate else { return }
                navigate(.benchmark)
            }
            .keyboardShortcut("b", modifiers: [.command, .shift])
            .disabled(!canNavigate)

            Divider()

            Button(localized("Run Benchmark")) {
                guard canNavigate else { return }
                navigate(.runBenchmark)
            }
                .disabled(!canNavigate || application.hasCommandBlockingPresentation || application.isRunning || application.benchmarkCoordinator.isRunning)

            Button(localized("Cancel Benchmark"), action: application.cancelBenchmark)
                .disabled(!application.benchmarkCoordinator.isRunning)

            Divider()

            Button(localized("Copy Diagnostic Summary"), action: application.copyDiagnosticSummary)
        }

        CommandGroup(replacing: .help) {
            Button(localized("Keldin Help")) {
                guard canNavigate else { return }
                navigate(.help(.gettingStarted))
            }
            .keyboardShortcut("h", modifiers: [.command, .shift])
            .disabled(!canNavigate)

            Button(localized("Show Welcome Guide")) {
                guard canNavigate else { return }
                navigate(.welcome)
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
