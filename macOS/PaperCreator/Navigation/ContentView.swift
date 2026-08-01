import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        NavigationSplitView {
            Sidebar(selection: $appModel.sidebarSelection)
        } detail: {
            switch appModel.sidebarSelection ?? .board(appModel.selectedBoardID) {
            case let .board(id):
                if let board = ExamCatalog.board(id: id) {
                    GeneratorWorkspace(board: board)
                } else {
                    ContentUnavailableView("Exam board not found", systemImage: "questionmark.folder")
                }
            case .benchmark:
                BenchmarkWorkspace()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .frame(minWidth: 920, minHeight: 640)
        .alert("Generation Error", isPresented: $appModel.showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(appModel.errorMessage)
        }
        .alert("Hosted AI Disclosure", isPresented: $appModel.showHostedAIConsent) {
            Button("Use Hosted AI", action: appModel.acceptHostedAIConsent)
            Button("Cancel", role: .cancel, action: appModel.cancelHostedAIConsent)
        } message: {
            Text("OpenAI and Anthropic generation sends prompts, selected syllabus context, and draft question content to the provider you choose. API keys stay in Keychain. Ollama keeps generation local.")
        }
        .confirmationDialog(
            "Pull \(appModel.modelToPull)?",
            isPresented: $appModel.showPullConfirmation,
            titleVisibility: .visible
        ) {
            Button("Pull Model") {
                appModel.confirmPullModel()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Ollama will download this model and make it available locally.")
        }
        .sheet(isPresented: $appModel.showWelcome) {
            WelcomeSheet()
                .environmentObject(appModel)
        }
        .sheet(isPresented: $appModel.showHelp) {
            HelpSheet()
                .environmentObject(appModel)
        }
        .onAppear(perform: ensureSidebarSelection)
        .onChange(of: appModel.sidebarSelection) { _, newSelection in
            selectBoard(for: newSelection)
        }
        .task {
            if appModel.selectedBoard.usesAI && appModel.aiProvider == .ollama {
                appModel.refreshOllama()
            }
        }
    }

    private func ensureSidebarSelection() {
        guard appModel.sidebarSelection == nil else { return }
        Task { @MainActor in
            appModel.sidebarSelection = .board(appModel.selectedBoardID)
        }
    }

    private func selectBoard(for selection: SidebarItem?) {
        guard case let .board(id) = selection, let board = ExamCatalog.board(id: id) else {
            return
        }
        Task { @MainActor in
            appModel.selectBoard(board)
        }
    }
}

#if DEBUG
private struct ContentViewPreview: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(AppViewModel())
    }
}
#endif
