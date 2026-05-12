import AppKit
import Charts
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
        .sheet(isPresented: $appModel.showHelp) {
            HelpSheet()
                .environmentObject(appModel)
        }
        .onAppear {
            if appModel.sidebarSelection == nil {
                DispatchQueue.main.async {
                    appModel.sidebarSelection = .board(appModel.selectedBoardID)
                }
            }
        }
        .onChange(of: appModel.sidebarSelection) { _, newSelection in
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

private struct HelpSheet: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 14) {
                Image(systemName: "questionmark.circle")
                    .font(.system(size: 28, weight: .semibold))
                    .symbolRenderingMode(.hierarchical)
                    .foregroundStyle(.tint)
                    .frame(width: 54, height: 54)
                    .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

                VStack(alignment: .leading, spacing: 4) {
                    Text("Past Paper Creator Help")
                        .font(.title.weight(.semibold))
                    Text("Quick reference for generating, saving, and troubleshooting papers.")
                        .foregroundStyle(.secondary)
                }

                Spacer()
            }
            .padding(.horizontal, 26)
            .padding(.top, 24)
            .padding(.bottom, 18)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HelpSection(
                        title: "Generate",
                        rows: [
                            HelpRow("Choose a ready generator in the sidebar: Economics Edexcel A or Computer Science AQA."),
                            HelpRow("Choose the paper, confirm the AI engine is ready, then use Generate Paper."),
                            HelpRow("Generation continues in the background; optional notifications report start, finish, or failure."),
                        ]
                    )

                    HelpSection(
                        title: "AI Setup",
                        rows: [
                            HelpRow("Ollama runs locally. Use AI > Check Ollama Status if generation is blocked."),
                            HelpRow("OpenAI and Anthropic require API keys in Settings."),
                            HelpRow("The App Store build can detect Ollama, but cannot install Ollama or pull models."),
                        ]
                    )

                    HelpSection(
                        title: "Files",
                        rows: [
                            HelpRow("Generated PDFs are saved to the selected output folder."),
                            HelpRow("Use File > Open Latest Question Paper or File > Open Latest Mark Scheme after a run."),
                            HelpRow("Use File > Choose Output Folder to change where papers are saved."),
                        ]
                    )

                    HelpSection(
                        title: "Benchmark",
                        rows: [
                            HelpRow("Use Tools > Show Benchmark to run a 30-second device diagnostic."),
                            HelpRow("The ETA uses paper length, provider, model size, CPU cores, memory, thermal state and the latest benchmark score."),
                            HelpRow("Benchmark results never include API keys or paper content."),
                        ]
                    )

                    HelpSection(
                        title: "Shortcuts",
                        rows: [
                            HelpRow("Command-G: Generate Paper"),
                            HelpRow("Command-Period: Cancel Generation"),
                            HelpRow("Shift-Command-O: Choose Output Folder"),
                            HelpRow("Option-Command-O: Open Output Folder"),
                            HelpRow("Shift-Command-B: Benchmark"),
                            HelpRow("Shift-Command-/: Help"),
                        ]
                    )
                }
                .padding(26)
            }

            Divider()

            HStack {
                Button("Copy Diagnostics", action: appModel.copyDiagnosticSummary)
                Button("Report Issue", action: appModel.openSupportPage)
                Spacer()
                Button("Done", action: appModel.dismissHelpGuide)
                    .keyboardShortcut(.defaultAction)
                    .nativePrimaryActionStyle()
            }
            .padding(20)
        }
        .frame(width: 680, height: 620)
        .presentationSizing(.fitted)
    }
}

private struct HelpSection: View {
    let title: String
    let rows: [HelpRow]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
            VStack(alignment: .leading, spacing: 8) {
                ForEach(rows) { row in
                    Label(row.text, systemImage: "checkmark.circle")
                        .symbolRenderingMode(.hierarchical)
                        .foregroundStyle(.primary, .secondary)
                }
            }
            .font(.callout)
        }
    }
}

private struct HelpRow: Identifiable {
    let id = UUID()
    let text: String

    init(_ text: String) {
        self.text = text
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
                NavigationLink(value: SidebarItem.benchmark) {
                    Label("Benchmark", systemImage: "speedometer")
                }
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
                    HStack {
                        Text(appModel.status)
                        Spacer()
                        if let estimate = appModel.generationEstimate {
                            Text("ETA \(estimate.remainingText)")
                                .foregroundStyle(.secondary)
                        }
                    }
                } currentValueLabel: {
                    Text(progress.formatted(.percent.precision(.fractionLength(0))))
                }
                .progressViewStyle(.linear)
            } else if appModel.isRunning {
                ProgressView()
                    .progressViewStyle(.linear)
            }

            if let estimate = appModel.generationEstimate {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Label("Estimated finish", systemImage: "clock")
                            .font(.headline)
                        Spacer()
                        Text(estimate.etaDate, style: .time)
                            .foregroundStyle(.secondary)
                    }
                    HStack(spacing: 10) {
                        Text("Confidence")
                            .foregroundStyle(.secondary)
                        ProgressView(value: estimate.confidence)
                            .progressViewStyle(.linear)
                        Text(estimate.confidence.formatted(.percent.precision(.fractionLength(0))))
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                    .font(.callout)

                    ForEach(estimate.factors.prefix(3)) { factor in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(factor.title)
                                    .font(.caption.weight(.semibold))
                                Text(factor.detail)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer()
                            Text(factor.impact.formatted(.number.precision(.fractionLength(2))) + "x")
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(factor.impact > 1.05 ? .orange : .secondary)
                        }
                    }
                }
                .padding(12)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            }

            ProgressLog(entries: appModel.progressEntries)
        }
        .nativePanel()
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

private struct BenchmarkWorkspace: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(spacing: 14) {
                    Image(systemName: "speedometer")
                        .font(.system(size: 26, weight: .semibold))
                        .symbolRenderingMode(.hierarchical)
                        .foregroundStyle(.tint)
                        .frame(width: 52, height: 52)
                        .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

                    VStack(alignment: .leading, spacing: 5) {
                        Text("Benchmark")
                            .font(.title.weight(.semibold))
                        Text("Measure generation-critical performance for this Mac.")
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    if appModel.isBenchmarkRunning {
                        Button(role: .cancel, action: appModel.cancelBenchmark) {
                            Label("Cancel", systemImage: "xmark.circle")
                        }
                        .controlSize(.large)
                    } else {
                        Button(action: appModel.startBenchmark) {
                            Label("Run 30 Second Test", systemImage: "play.fill")
                        }
                        .disabled(appModel.isRunning)
                        .controlSize(.large)
                        .nativePrimaryActionStyle()
                    }
                }
                .nativePanel()

                BenchmarkOverviewPanel()
                BenchmarkLiveCharts()
                BenchmarkMetricGrid()
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 24)
            .frame(maxWidth: 1160)
            .frame(maxWidth: .infinity)
        }
        .background(.background)
        .navigationTitle("Benchmark")
    }
}

private struct BenchmarkOverviewPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Diagnostic", systemImage: "gauge.with.dots.needle.67percent")

            if appModel.isBenchmarkRunning {
                ProgressView(value: appModel.benchmarkProgress ?? 0) {
                    Text("Running CPU, memory, disk and network checks")
                } currentValueLabel: {
                    Text(((appModel.benchmarkProgress ?? 0).formatted(.percent.precision(.fractionLength(0)))))
                }
                .progressViewStyle(.linear)
            } else if let verdict = appModel.benchmarkVerdict {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: verdict.score >= 0.72 ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                        .font(.title2)
                        .foregroundStyle(verdict.score >= 0.72 ? .green : .orange)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(verdict.verdict)
                            .font(.headline)
                        Text(verdict.detail)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text(verdict.score.formatted(.percent.precision(.fractionLength(0))))
                        .font(.title2.monospacedDigit().weight(.semibold))
                }
            } else {
                Text("Run the benchmark to calibrate ETA and check whether this Mac is ready for local generation.")
                    .foregroundStyle(.secondary)
            }
        }
        .nativePanel()
    }
}

private struct BenchmarkLiveCharts: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Grid(alignment: .topLeading, horizontalSpacing: 18, verticalSpacing: 18) {
            GridRow {
                BenchmarkChart(
                    title: "CPU Load",
                    unit: "%",
                    samples: appModel.benchmarkSamples,
                    value: \.cpuLoad
                )
                BenchmarkChart(
                    title: "Free Memory",
                    unit: "GB",
                    samples: appModel.benchmarkSamples,
                    value: \.memoryAvailableGB
                )
            }
            GridRow {
                BenchmarkChart(
                    title: "Disk Write",
                    unit: "MB/s",
                    samples: appModel.benchmarkSamples,
                    value: \.diskWriteMBs
                )
                BenchmarkChart(
                    title: "Disk Read",
                    unit: "MB/s",
                    samples: appModel.benchmarkSamples,
                    value: \.diskReadMBs
                )
            }
        }
    }
}

private struct BenchmarkChart: View {
    let title: String
    let unit: String
    let samples: [BenchmarkSample]
    let value: KeyPath<BenchmarkSample, Double>

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.headline)
                Spacer()
                if let latest = samples.last {
                    Text(latest[keyPath: value].formatted(.number.precision(.fractionLength(0...1))) + " \(unit)")
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                }
            }

            if samples.isEmpty {
                PanelEmptyState(title: "No Samples", message: "Start the benchmark to populate this chart.", systemImage: "chart.xyaxis.line")
                    .frame(height: 150)
            } else {
                Chart(samples) { sample in
                    LineMark(
                        x: .value("Seconds", sample.elapsed),
                        y: .value(unit, sample[keyPath: value])
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(.tint)
                    AreaMark(
                        x: .value("Seconds", sample.elapsed),
                        y: .value(unit, sample[keyPath: value])
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(.tint.opacity(0.12))
                }
                .chartXAxisLabel("seconds")
                .chartYAxisLabel(unit)
                .frame(height: 150)
            }
        }
        .nativePanel()
    }
}

private struct BenchmarkMetricGrid: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Results", systemImage: "list.bullet.rectangle")

            if appModel.benchmarkMetrics.isEmpty {
                PanelEmptyState(title: "No Results", message: "Metric results appear as the diagnostic runs.", systemImage: "speedometer")
                    .frame(maxWidth: .infinity, minHeight: 130)
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 230), spacing: 12)], spacing: 12) {
                    ForEach(appModel.benchmarkMetrics) { metric in
                        BenchmarkMetricTile(metric: metric)
                    }
                }
            }
        }
        .nativePanel()
    }
}

private struct BenchmarkMetricTile: View {
    let metric: BenchmarkMetric

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text(metric.name)
                    .font(.headline)
                Spacer()
                if let score = metric.score {
                    Text(score.formatted(.percent.precision(.fractionLength(0))))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(score >= 0.7 ? .green : .orange)
                }
            }
            Text(metric.displayValue)
                .font(.title3.monospacedDigit().weight(.semibold))
            if let detail = metric.detail, !detail.isEmpty {
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(12)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
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
                        .disabled(appModel.modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || appModel.isRunning || !appModel.distributionMode.canManageOllama)
                    Button("Install Ollama", action: appModel.openOllamaDownload)
                        .disabled(appModel.distributionMode == .appStore)
                }

                if appModel.distributionMode == .appStore {
                    Text("The App Store build can detect an existing Ollama installation, but cannot install Ollama or download models.")
                        .foregroundStyle(.secondary)
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
                    "Notify when generation starts and finishes",
                    isOn: Binding(
                        get: { appModel.notificationsEnabled },
                        set: { appModel.setNotificationsEnabled($0) }
                    )
                )
                Text("macOS notifications are optional and only used for generation/model-download status.")
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

            Section("App Store Readiness") {
                LabeledContent("Sandbox", value: "Enabled")
                LabeledContent("Tracking", value: "None")
                LabeledContent("Analytics", value: "None")
                LabeledContent("External installers", value: appModel.distributionMode == .appStore ? "Disabled" : "Direct build only")
                Text("Exam-board names are used only to identify specifications. Generated practice materials remain unofficial.")
                    .foregroundStyle(.secondary)
            }

            Section {
                Text("Unofficial practice material. Not affiliated with Pearson, Edexcel, AQA, or any exam board.")
                    .foregroundStyle(.secondary)
            }

            Section("Help") {
                Button("Past Paper Creator Help", action: appModel.showHelpGuide)
                Button("Show Welcome Guide", action: appModel.showWelcomeGuide)
                Button("Show Benchmark") {
                    appModel.showBenchmarkPage()
                }
                Button("Copy Diagnostic Summary", action: appModel.copyDiagnosticSummary)
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
