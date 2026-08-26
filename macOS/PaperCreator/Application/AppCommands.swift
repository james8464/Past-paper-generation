import SwiftUI

struct AppCommands: Commands {
    @ObservedObject var application: ApplicationCoordinator

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("New Paper", action: application.showCreationWorkspace)
                .keyboardShortcut("n", modifiers: [.command])

            Button("Create Paper", action: application.generate)
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(!application.canGenerate)

            Button("Cancel Generation", action: application.cancelGeneration)
                .keyboardShortcut(".", modifiers: [.command])
                .disabled(!application.isRunning)

            Divider()
        }

        CommandGroup(after: .saveItem) {
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
            Button("Paper creator Help") {
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
