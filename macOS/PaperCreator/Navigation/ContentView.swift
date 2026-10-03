import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @Environment(CatalogStore.self) private var catalog
    @AppStorage(AppStorageKey.navigationColumnVisibility)
    private var navigationColumnVisibility = "all"
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"

    var body: some View {
        @Bindable var catalog = catalog
        GeometryReader { geometry in
            let layoutMode = WorkspaceLayoutPolicy.mode(for: geometry.size.width)

            NavigationSplitView(columnVisibility: columnVisibility(for: layoutMode)) {
                Sidebar(selection: $catalog.sidebarSelection)
            } detail: {
                switch catalog.sidebarSelection ?? .board(catalog.selectedBoardID) {
                case let .board(id):
                    if let board = ExamCatalog.board(id: id) {
                        GeneratorWorkspace(board: board, layoutMode: layoutMode)
                    } else {
                        ContentUnavailableView("Exam board not found", systemImage: "questionmark.folder")
                    }
                case .benchmark:
                    BenchmarkWorkspace()
                case .frenchBaccalaureat:
                    FrenchAssessmentWorkspace()
                case .documents:
                    DocumentPreviewView(
                        files: application.generatedFiles,
                        selectedID: application.previewedFileID
                    )
                case .history:
                    JobHistoryView(store: application.recentDocumentStore)
                }
            }
            .navigationSplitViewStyle(.balanced)
        }
        .frame(minWidth: 720, minHeight: 560)
        .environment(\.locale, interfaceLanguage == "system" ? .current : Locale(identifier: interfaceLanguage))
        .alert("Generation Error", isPresented: $application.showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(application.errorMessage)
        }
        .alert("Hosted AI Disclosure", isPresented: $application.showHostedAIConsent) {
            Button("Use Hosted AI", action: application.acceptHostedAIConsent)
            Button("Cancel", role: .cancel, action: application.cancelHostedAIConsent)
        } message: {
            Text("OpenAI and Anthropic generation sends prompts, selected syllabus context, and draft question content to the provider you choose. API keys stay in Keychain. Ollama keeps generation local.")
        }
        .confirmationDialog(
            "Set Up Apple MLX?",
            isPresented: $application.showMLXSetupConfirmation,
            titleVisibility: .visible
        ) {
            Button("Set Up and Continue", action: application.confirmMLXSetup)
            Button("Cancel", role: .cancel, action: application.cancelMLXSetup)
        } message: {
            Text(application.mlxSetupExplanation)
        }
        .confirmationDialog(
            "Pull \(application.modelToPull)?",
            isPresented: $application.showPullConfirmation,
            titleVisibility: .visible
        ) {
            Button("Pull Model") {
                application.confirmPullModel()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Ollama will download this model and make it available locally.")
        }
        .sheet(isPresented: $application.showWelcome) {
            WelcomeSheet()
                .environmentObject(application)
        }
        .sheet(isPresented: $application.showHelp) {
            HelpSheet()
                .environmentObject(application)
        }
        .onAppear(perform: ensureSidebarSelection)
        .onChange(of: catalog.sidebarSelection) { _, newSelection in
            selectBoard(for: newSelection)
        }
        .task {
            if application.selectedBoard.usesAI && application.aiProvider == .ollama {
                application.refreshOllama()
            }
        }
    }

    private func columnVisibility(
        for layoutMode: WorkspaceLayoutMode
    ) -> Binding<NavigationSplitViewVisibility> {
        Binding(
            get: { () -> NavigationSplitViewVisibility in
                guard layoutMode.showsSidebar else { return .detailOnly }
                switch navigationColumnVisibility {
                case "detail": return .detailOnly
                case "double": return .doubleColumn
                default: return .all
                }
            },
            set: { value in
                guard layoutMode.showsSidebar else { return }
                switch value {
                case .detailOnly: navigationColumnVisibility = "detail"
                case .doubleColumn: navigationColumnVisibility = "double"
                default: navigationColumnVisibility = "all"
                }
            }
        )
    }

    private func ensureSidebarSelection() {
        guard catalog.sidebarSelection == nil else { return }
        Task { @MainActor in
            catalog.sidebarSelection = .board(catalog.selectedBoardID)
        }
    }

    private func selectBoard(for selection: SidebarItem?) {
        guard case let .board(id) = selection, let board = ExamCatalog.board(id: id) else {
            return
        }
        Task { @MainActor in
            application.selectBoard(board)
        }
    }
}

#if DEBUG
private struct ContentViewPreview: PreviewProvider {
    static var previews: some View {
        let model = ApplicationCoordinator()
        ContentView()
            .environmentObject(model)
            .environment(model.catalogStore)
            .environment(model.benchmarkCoordinator)
            .environment(model.generationCoordinator)
    }
}
#endif
