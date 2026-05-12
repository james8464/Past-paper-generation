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
            case .settings:
                SettingsPane()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .frame(minWidth: 1120, minHeight: 740)
        .toolbar {
            ToolbarItemGroup {
                Button(action: appModel.refreshOllama) {
                    if appModel.isRefreshingOllama {
                        Label {
                            Text("Checking")
                        } icon: {
                            ProgressView()
                                .controlSize(.small)
                        }
                    } else {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                }
                .disabled(appModel.isRunning || appModel.isBenchmarkRunning || appModel.isRefreshingOllama)
                .help("Refresh models")

                if appModel.isRunning {
                    Button(role: .cancel, action: appModel.cancelGeneration) {
                        Label("Cancel", systemImage: "xmark.circle")
                    }
                    .help("Cancel")
                }
            }
        }
        .alert("Generation Error", isPresented: $appModel.showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(appModel.errorMessage)
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
            appModel.refreshOllama()
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

#Preview {
    ContentView()
        .environmentObject(AppViewModel())
}
