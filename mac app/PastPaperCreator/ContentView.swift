import AppKit
import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var appModel: AppViewModel
    @State private var selection: SidebarItem?

    var body: some View {
        NavigationSplitView {
            Sidebar(selection: $selection)
        } detail: {
            switch selection ?? .board(appModel.selectedBoardID) {
            case let .board(id):
                if let board = ExamCatalog.board(id: id) {
                    GeneratorWorkspace(board: board)
                } else {
                    ContentUnavailableView("Exam board not found", systemImage: "questionmark.folder")
                }
            case .settings:
                SettingsPane()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .frame(minWidth: 1120, minHeight: 740)
        .toolbar {
            ToolbarItemGroup {
                Button(action: appModel.refreshOllama) {
                    Label(appModel.isRefreshingOllama ? "Checking" : "Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(appModel.isRunning || appModel.isRefreshingOllama)
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
        .onAppear {
            if selection == nil {
                DispatchQueue.main.async {
                    selection = .board(appModel.selectedBoardID)
                }
            }
        }
        .onChange(of: selection) { _, newSelection in
            guard case let .board(id) = newSelection, let board = ExamCatalog.board(id: id) else {
                return
            }
            DispatchQueue.main.async {
                appModel.selectBoard(board)
            }
        }
        .task {
            appModel.refreshOllama()
        }
    }
}

private struct WelcomeSheet: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack(spacing: 14) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 30, weight: .semibold))
                    .symbolRenderingMode(.hierarchical)
                    .foregroundStyle(.tint)
                    .frame(width: 58, height: 58)
                    .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

                VStack(alignment: .leading, spacing: 4) {
                    Text("Past Paper Creator")
                        .font(.largeTitle.weight(.semibold))
                    Text("Generate syllabus-bound practice papers from your local subject packs.")
                        .foregroundStyle(.secondary)
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                WelcomeRow(systemImage: "graduationcap", title: "Choose a subject", message: "Economics Edexcel A and Computer Science AQA are ready. Other subjects are placeholders.")
                WelcomeRow(systemImage: "cpu", title: "Pick an AI engine", message: "Use Ollama locally, or configure a hosted provider in Settings.")
                WelcomeRow(systemImage: "folder", title: "Save PDFs", message: "Generated question papers and mark schemes go to your selected output folder.")
            }

            Text("Unofficial practice material. Not affiliated with Pearson, Edexcel, AQA, or any exam board.")
                .font(.callout)
                .foregroundStyle(.secondary)

            HStack {
                SettingsLink {
                    Label("Open Settings", systemImage: "gearshape")
                }
                Spacer()
                Button("Get Started") {
                    appModel.dismissWelcome()
                }
                .keyboardShortcut(.defaultAction)
                .controlSize(.large)
                .nativePrimaryActionStyle()
            }
        }
        .padding(28)
        .frame(width: 620)
        .presentationSizing(.fitted)
    }
}

private struct WelcomeRow: View {
    let systemImage: String
    let title: String
    let message: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: systemImage)
                .font(.title3)
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.secondary)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                Text(message)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

private struct Sidebar: View {
    @Binding var selection: SidebarItem?

    var body: some View {
        List(selection: $selection) {
            Section("A-Levels") {
                ForEach(ExamCatalog.subjects) { subject in
                    DisclosureGroup {
                        ForEach(subject.boards) { board in
                            NavigationLink(value: SidebarItem.board(board.id)) {
                                BoardRow(board: board)
                            }
                        }
                    } label: {
                        Label(subject.title, systemImage: subject.systemImage)
                    }
                }
            }

            Section {
                NavigationLink(value: SidebarItem.settings) {
                    Label("Settings", systemImage: "gearshape")
                }
            }
        }
        .navigationTitle("Past Papers")
    }
}

private struct BoardRow: View {
    let board: ExamBoardOption

    var body: some View {
        HStack {
            Text(board.shortTitle)
            Spacer()
            if board.status == .placeholder {
                Image(systemName: "clock")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .help("Coming soon")
            }
        }
    }
}

private struct GeneratorWorkspace: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HeaderPanel(board: board)

                if board.isReady {
                    ReadinessBanner()

                    HStack(alignment: .top, spacing: 18) {
                        VStack(spacing: 18) {
                            PaperPanel(board: board)
                            OutputPanel()
                            DocumentsPanel()
                        }
                        .frame(maxWidth: .infinity)

                        VStack(spacing: 18) {
                            ModelPanel()
                            ActivityPanel()
                            LivePreviewPanel()
                        }
                        .frame(maxWidth: .infinity)
                    }
                } else {
                    PlaceholderPanel(board: board)
                }
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 24)
            .frame(maxWidth: 1160)
            .frame(maxWidth: .infinity)
        }
        .background(.background)
        .navigationTitle(board.subjectTitle)
    }
}

private struct HeaderPanel: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: board.systemImage)
                .font(.system(size: 26, weight: .semibold))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
                .frame(width: 52, height: 52)
                .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

            VStack(alignment: .leading, spacing: 5) {
                Text(board.subjectTitle)
                    .font(.title.weight(.semibold))
                HStack(spacing: 8) {
                    CapsuleLabel(title: board.title, systemImage: "building.columns")
                    CapsuleLabel(title: appModel.selectedPaperTitle, systemImage: "doc.text")
                    CapsuleLabel(title: board.status.title, systemImage: board.isReady ? "checkmark.circle" : "clock")
                }
            }

            Spacer()
            StatusPill()

            if !board.isReady {
                Label("Coming Soon", systemImage: "clock")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(.thinMaterial, in: Capsule())
            } else if appModel.isRunning {
                Button(role: .cancel, action: appModel.cancelGeneration) {
                    Label("Cancel", systemImage: "xmark.circle")
                }
                .controlSize(.large)
            } else {
                Button(action: appModel.generate) {
                    Label("Generate", systemImage: "play.fill")
                }
                .keyboardShortcut(.return, modifiers: .command)
                .disabled(!appModel.canGenerate)
                .controlSize(.large)
                .nativePrimaryActionStyle()
                .help(generateHelp)
            }
        }
        .nativePanel()
    }

    private var generateHelp: String {
        if !board.isReady { return "This exam board is coming soon." }
        if appModel.aiProvider == .ollama && !appModel.ollamaState.running { return "Refresh Ollama before generating." }
        return "Generate paper"
    }
}

private struct ReadinessBanner: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        if let blocker = appModel.generationBlocker, !appModel.isRunning, !appModel.isRefreshingOllama {
            HStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                VStack(alignment: .leading, spacing: 2) {
                    Text(blocker)
                        .font(.headline)
                    Text(helpText)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if appModel.aiProvider == .ollama {
                    Button("Refresh", action: appModel.refreshOllama)
                    Button("Get Ollama", action: appModel.openOllamaDownload)
                        .disabled(appModel.distributionMode == .appStore)
                }
                SettingsLink {
                    Label("Settings", systemImage: "slider.horizontal.3")
                }
            }
            .padding(14)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .stroke(.orange.opacity(0.28), lineWidth: 1)
            }
        }
    }

    private var helpText: String {
        switch appModel.aiProvider {
        case .ollama:
            "Use Ollama locally, or switch provider in Settings."
        case .openAI, .anthropic:
            "Save provider credentials in Settings before generating."
        }
    }
}

private struct PaperPanel: View {
    @EnvironmentObject private var appModel: AppViewModel
    let board: ExamBoardOption

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Paper", systemImage: "doc.text")

            Picker(
                "Paper",
                selection: Binding(
                    get: { appModel.selectedPaperID },
                    set: { appModel.selectPaperID($0) }
                )
            ) {
                ForEach(board.papers) { paper in
                    Text(paper.title).tag(paper.id)
                }
            }
            .pickerStyle(.segmented)

            Text(appModel.selectedPaperDetail)
                .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}

private struct OutputPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Output", systemImage: "folder")

            HStack {
                Text(appModel.outputFolder.path)
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .foregroundStyle(.secondary)
                Spacer()
                Button(action: appModel.openOutputFolder) {
                    Label("Open", systemImage: "folder")
                }
                .labelStyle(.iconOnly)
                .help("Open output folder")
                Button("Choose...", action: appModel.chooseOutputFolder)
            }

            Text("Generated PDFs are saved here.")
                .font(.callout)
                .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}

private struct ModelPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "AI Engine", systemImage: appModel.aiProvider.systemImage)

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(appModel.aiProvider.title)
                        .font(.headline)
                    Text(appModel.activeModelName.isEmpty ? "No model selected" : appModel.activeModelName)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                Spacer()
                SettingsLink {
                    Label("Settings", systemImage: "slider.horizontal.3")
                }
            }

            Divider()

            HStack {
                if appModel.isRefreshingOllama {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Image(systemName: modelStatusIcon)
                        .foregroundStyle(modelStatusColor)
                }
                Text(modelStatusText)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .nativePanel()
    }

    private var modelStatusIcon: String {
        if appModel.aiProvider == .ollama {
            return appModel.ollamaState.running ? "checkmark.circle.fill" : "exclamationmark.triangle.fill"
        }
        return "checkmark.circle.fill"
    }

    private var modelStatusColor: Color {
        appModel.aiProvider == .ollama && !appModel.ollamaState.running ? .orange : .green
    }

    private var modelStatusText: String {
        appModel.aiProvider == .ollama ? appModel.ollamaState.message : "\(appModel.aiProvider.title) configured in Settings"
    }
}

private struct ActivityPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Activity", systemImage: "waveform.path.ecg")

            if appModel.isRunning, let progress = appModel.generationProgress {
                ProgressView(value: progress) {
                    Text(appModel.status)
                } currentValueLabel: {
                    Text(progress.formatted(.percent.precision(.fractionLength(0))))
                }
                .progressViewStyle(.linear)
            } else if appModel.isRunning {
                ProgressView()
                    .progressViewStyle(.linear)
            }

            ProgressLog(entries: appModel.progressEntries)
        }
        .nativePanel()
    }
}

private struct LivePreviewPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Live Preview", systemImage: "rectangle.stack")

            if appModel.previewPages.isEmpty {
                PanelEmptyState(
                    title: appModel.isRunning ? "Rendering Pages" : "No Preview",
                    message: appModel.isRunning ? "Pages appear as PDFs render." : "Generated pages appear here.",
                    systemImage: appModel.isRunning ? "doc.text.magnifyingglass" : "doc.richtext"
                )
                .frame(maxWidth: .infinity, minHeight: 170)
            } else {
                ScrollView(.horizontal) {
                    LazyHStack(alignment: .top, spacing: 14) {
                        ForEach(appModel.previewPages) { page in
                            PageThumbnail(page: page)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .frame(minHeight: 210)
            }
        }
        .nativePanel()
    }
}

private struct PageThumbnail: View {
    let page: GeneratedPage

    var body: some View {
        VStack(spacing: 8) {
            if let image = NSImage(contentsOf: page.url) {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 120, height: 170)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
                    .shadow(color: .black.opacity(0.16), radius: 8, y: 3)
            } else {
                RoundedRectangle(cornerRadius: 6, style: .continuous)
                    .fill(.quaternary)
                    .frame(width: 120, height: 170)
            }

            Text(page.title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(page.roleTitle)
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
    }
}

private struct DocumentsPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Documents", systemImage: "doc.on.doc")
            GeneratedFilesTable(files: appModel.generatedFiles)
                .frame(minHeight: 170)
        }
        .nativePanel()
    }
}

private struct PlaceholderPanel: View {
    let board: ExamBoardOption

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            PanelHeader(title: "Coming Soon", systemImage: "clock")
            Text("\(board.subjectTitle) \(board.title) is planned for a future release.")
                .foregroundStyle(.secondary)
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                Label("Ready now: Economics Edexcel A and Computer Science AQA.", systemImage: "checkmark.circle")
                Label("More subjects will appear here after their generator profiles are complete.", systemImage: "hourglass")
            }
            .foregroundStyle(.secondary)
        }
        .nativePanel()
    }
}

struct SettingsPane: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        TabView {
            AISettingsTab()
                .tabItem {
                    Label("AI", systemImage: "sparkles")
                }

            OutputSettingsTab()
                .tabItem {
                    Label("Output", systemImage: "folder")
                }

            PrivacySettingsTab()
                .tabItem {
                    Label("Privacy", systemImage: "hand.raised")
                }
        }
        .scenePadding()
        .frame(minWidth: 560, minHeight: 440)
        .navigationTitle("Settings")
    }
}

private struct AISettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Provider") {
                Picker("Provider", selection: $appModel.aiProvider) {
                    ForEach(AIProvider.allCases) { provider in
                        Text(provider.title).tag(provider)
                    }
                }
                .pickerStyle(.segmented)

                Text(appModel.aiProvider.subtitle)
                    .foregroundStyle(.secondary)
            }

            Section("Ollama") {
                Picker("Installed Model", selection: $appModel.selectedModel) {
                    if appModel.availableModels.isEmpty {
                        Text(appModel.selectedModel).tag(appModel.selectedModel)
                    } else {
                        ForEach(appModel.availableModels, id: \.self) { model in
                            Text(model).tag(model)
                        }
                    }
                }

                TextField("Model to pull", text: $appModel.modelToPull)
                    .textFieldStyle(.roundedBorder)

                HStack {
                    Button("Refresh Models", action: appModel.refreshOllama)
                    Button("Pull Model", action: appModel.requestPullModel)
                        .disabled(appModel.modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || appModel.isRunning)
                    Button("Install Ollama", action: appModel.openOllamaDownload)
                        .disabled(appModel.distributionMode == .appStore)
                }

                if let command = appModel.ollamaState.command {
                    LabeledContent("Command", value: command)
                }
            }

            Section("OpenAI") {
                TextField("Model", text: $appModel.openAIModel)
                    .textFieldStyle(.roundedBorder)
                SecureField("API Key", text: $appModel.openAIAPIKey)
                    .textFieldStyle(.roundedBorder)
            }

            Section("Anthropic") {
                TextField("Model", text: $appModel.anthropicModel)
                    .textFieldStyle(.roundedBorder)
                SecureField("API Key", text: $appModel.anthropicAPIKey)
                    .textFieldStyle(.roundedBorder)
            }

            Button("Save AI Settings", action: appModel.saveAISettings)
        }
        .formStyle(.grouped)
    }
}

private struct OutputSettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Folder") {
                LabeledContent("Output") {
                    HStack {
                        Text(appModel.outputFolder.path)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                        Button("Choose...", action: appModel.chooseOutputFolder)
                    }
                }
            }

            Section("Preview Mode") {
                Toggle("Use built-in drafts", isOn: $appModel.dryRun)
                Text("Creates sample PDFs without contacting an AI provider.")
                    .foregroundStyle(.secondary)
            }

            Section("Notifications") {
                Toggle(
                    "Notify when jobs finish",
                    isOn: Binding(
                        get: { appModel.notificationsEnabled },
                        set: { appModel.setNotificationsEnabled($0) }
                    )
                )
                Text("macOS notifications are only used for completed or failed generation jobs.")
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
    }
}

private struct PrivacySettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Privacy") {
                LabeledContent("Distribution", value: appModel.distributionMode.title)
                Link("Privacy Policy", destination: URL(string: "https://github.com/james8464/Past-paper-generation#privacy")!)
                Text("Ollama generation is local. Hosted providers send prompts to the provider you select.")
                    .foregroundStyle(.secondary)
            }

            Section {
                Text("Unofficial practice material. Not affiliated with Pearson, Edexcel, AQA, or any exam board.")
                    .foregroundStyle(.secondary)
            }

            Section("Help") {
                Button("Show Welcome Guide", action: appModel.showWelcomeGuide)
            }
        }
        .formStyle(.grouped)
    }
}

private struct PanelHeader: View {
    let title: String
    let systemImage: String

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.headline)
            .symbolRenderingMode(.hierarchical)
    }
}

private struct CapsuleLabel: View {
    let title: String
    let systemImage: String

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.callout)
            .foregroundStyle(.secondary)
            .lineLimit(1)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(.thinMaterial, in: Capsule())
    }
}

private struct StatusPill: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        HStack(spacing: 7) {
            if appModel.isRunning || appModel.isRefreshingOllama {
                ProgressView()
                    .controlSize(.small)
                    .frame(width: 16, height: 16)
            } else {
                Image(systemName: appModel.status == "Error" ? "exclamationmark.triangle" : "checkmark.circle")
                    .symbolRenderingMode(.hierarchical)
            }
            Text(appModel.status)
        }
            .font(.callout)
            .foregroundStyle(.secondary)
            .lineLimit(1)
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .nativeStatusGlass()
            .frame(maxWidth: 220)
    }
}

private struct ProgressLog: View {
    let entries: [ProgressEntry]

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 8) {
                if entries.isEmpty {
                    PanelEmptyState(title: "Ready", message: "Generation activity appears here.", systemImage: "checkmark.circle")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 24)
                } else {
                    ForEach(entries.suffix(80)) { entry in
                        HStack(alignment: .firstTextBaseline, spacing: 10) {
                            Text(entry.date, style: .time)
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(.tertiary)
                                .frame(width: 64, alignment: .leading)
                            Text(entry.stage ?? "step")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .frame(width: 74, alignment: .leading)
                            Text(entry.message)
                                .textSelection(.enabled)
                        }
                        .font(.callout)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(minHeight: 140, maxHeight: 190)
    }
}

private struct GeneratedFilesTable: View {
    @EnvironmentObject private var appModel: AppViewModel
    let files: [GeneratedFile]

    var body: some View {
        if files.isEmpty {
            PanelEmptyState(title: "No Documents", message: "Generated PDFs will be listed here.", systemImage: "doc")
                .frame(maxWidth: .infinity, minHeight: 150)
        } else {
            Table(files) {
                TableColumn("Document") { file in
                    Text(file.title)
                }
                TableColumn("Location") { file in
                    Text(file.url.path)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .foregroundStyle(.secondary)
                }
                TableColumn("") { file in
                    HStack {
                        Button {
                            appModel.openGeneratedFile(file)
                        } label: {
                            Label("Open", systemImage: "doc")
                        }
                        .labelStyle(.iconOnly)
                        .help("Open")

                        Button {
                            appModel.revealGeneratedFile(file)
                        } label: {
                            Label("Reveal", systemImage: "folder")
                        }
                        .labelStyle(.iconOnly)
                        .help("Reveal in Finder")
                    }
                }
                .width(70)
            }
        }
    }
}

private struct PanelEmptyState: View {
    let title: String
    let message: String
    let systemImage: String

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: systemImage)
                .font(.system(size: 26, weight: .regular))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.secondary)
            Text(title)
                .font(.headline)
            Text(message)
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    ContentView()
        .environmentObject(AppViewModel())
}
