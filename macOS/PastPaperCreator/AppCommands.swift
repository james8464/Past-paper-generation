import SwiftUI

struct AppCommands: Commands {
    @ObservedObject var appModel: AppViewModel
    @Environment(\.openWindow) private var openWindow

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("New Window") {
                openWindow(id: "main")
            }
            .keyboardShortcut("n", modifiers: [.command])

            Divider()

            Button("Generate Paper", action: appModel.generate)
                .keyboardShortcut("g", modifiers: [.command])
                .disabled(!appModel.canGenerate)

            Button("Cancel Generation", action: appModel.cancelGeneration)
                .keyboardShortcut(".", modifiers: [.command])
                .disabled(!appModel.isRunning)

            Divider()
        }

        CommandGroup(after: .saveItem) {
            Button("Choose Output Folder...", action: appModel.chooseOutputFolder)
                .keyboardShortcut("o", modifiers: [.command, .shift])

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

        CommandMenu("Paper") {
            Section("Generator") {
                ForEach(ExamCatalog.readyBoards) { board in
                    Button {
                        appModel.selectBoard(board)
                    } label: {
                        menuLabel(
                            "\(board.subjectTitle) - \(board.title)",
                            isSelected: appModel.selectedBoardID == board.id
                        )
                    }
                }
            }

            Divider()

            Section("Paper") {
                ForEach(appModel.selectedBoard.papers) { paper in
                    Button {
                        appModel.selectPaperID(paper.id)
                    } label: {
                        menuLabel(paper.title, isSelected: appModel.selectedPaperID == paper.id)
                    }
                }
            }
        }

        CommandMenu("AI") {
            Section("Provider") {
                ForEach(AIProvider.allCases) { provider in
                    Button {
                        appModel.selectAIProvider(provider)
                    } label: {
                        menuLabel(provider.title, isSelected: appModel.aiProvider == provider)
                    }
                }
            }

            Divider()

            if appModel.aiProvider == .ollama {
                Button("Check Ollama Status", action: appModel.refreshOllama)
                    .disabled(appModel.isRunning || appModel.isBenchmarkRunning || appModel.isRefreshingOllama)

                Button("Open Ollama Download Page", action: appModel.openOllamaDownload)
                    .disabled(appModel.distributionMode == .appStore)
            }
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
            Button("ExamForge Help", action: appModel.showHelpGuide)
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

    @ViewBuilder
    private func menuLabel(_ title: String, isSelected: Bool) -> some View {
        if isSelected {
            Label(title, systemImage: "checkmark")
        } else {
            Text(title)
        }
    }
}
