import SwiftUI

struct AppCommands: Commands {
    @ObservedObject var appModel: AppViewModel

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("New Paper", action: appModel.showCreationWorkspace)
                .keyboardShortcut("n", modifiers: [.command])

            Button("Create Paper", action: appModel.generate)
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(!appModel.canGenerate)

            Button("Cancel Generation", action: appModel.cancelGeneration)
                .keyboardShortcut(".", modifiers: [.command])
                .disabled(!appModel.isRunning)

            Divider()
        }

        CommandGroup(after: .saveItem) {
            Button("Open Output Folder", action: appModel.openOutputFolder)
                .keyboardShortcut("o", modifiers: [.command, .option])

            Divider()

            Button("Open Latest Question Paper") {
                appModel.openGeneratedFile(role: "question_paper")
            }
            .disabled(!appModel.hasGeneratedFile(role: "question_paper"))

            Button("Open Latest Mark Scheme") {
                appModel.openGeneratedFile(role: "mark_scheme")
            }
            .disabled(!appModel.hasGeneratedFile(role: "mark_scheme"))

            Button("Reveal Latest Question Paper in Finder") {
                appModel.revealGeneratedFile(role: "question_paper")
            }
            .disabled(!appModel.hasGeneratedFile(role: "question_paper"))
        }

        CommandMenu("Tools") {
            Button("Show Benchmark") {
                appModel.showBenchmarkPage()
            }
            .keyboardShortcut("b", modifiers: [.command, .shift])

            Divider()

            Button("Run Benchmark", action: appModel.startBenchmark)
                .disabled(appModel.isRunning || appModel.isBenchmarkRunning)

            Button("Cancel Benchmark", action: appModel.cancelBenchmark)
                .disabled(!appModel.isBenchmarkRunning)

            Divider()

            Button("Copy Diagnostic Summary", action: appModel.copyDiagnosticSummary)
        }

        CommandGroup(replacing: .help) {
            Button("Paper creator Help", action: appModel.showHelpGuide)
                .keyboardShortcut("/", modifiers: [.command, .shift])

            Button("Show Welcome Guide", action: appModel.showWelcomeGuide)

            Divider()

            Button("Open User Guide", action: appModel.openProjectHelp)
            Button("Privacy Policy", action: appModel.openPrivacyPolicy)
            Button("Report an Issue", action: appModel.openSupportPage)

            Divider()

            Button("Copy Diagnostic Summary", action: appModel.copyDiagnosticSummary)
        }
    }

}
