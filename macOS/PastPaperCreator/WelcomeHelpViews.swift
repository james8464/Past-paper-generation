import SwiftUI

struct WelcomeSheet: View {
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
                    Text("ExamForge")
                        .font(.largeTitle.weight(.semibold))
                    Text("Generate syllabus-bound practice papers from your local subject packs.")
                        .foregroundStyle(.secondary)
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                WelcomeRow(systemImage: "graduationcap", title: "Choose a subject", message: "Choose from generators that have complete local resource packs.")
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

struct HelpSheet: View {
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
                    Text("ExamForge Help")
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
                            HelpRow("Choose an available generator in the sidebar."),
                            HelpRow("Choose the paper, confirm the AI engine is ready, then use Generate Paper."),
                            HelpRow("Generation continues in the background; optional notifications report start, finish, or failure."),
                        ]
                    )

                    HelpSection(
                        title: "AI Setup",
                        rows: [
                            HelpRow("Ollama runs locally. Use AI > Check Ollama Status if generation is blocked."),
                            HelpRow("OpenAI and Anthropic require API keys in Settings and explicit hosted-AI consent before prompts leave the Mac."),
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
                            HelpRow("Use Tools > Show Benchmark to run a \(Int(AppDefaults.benchmarkDurationSeconds))-second device diagnostic."),
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
