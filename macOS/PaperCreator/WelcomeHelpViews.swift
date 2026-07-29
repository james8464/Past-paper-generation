import AppKit
import SwiftUI

struct WelcomeSheet: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 28) {
            VStack(alignment: .leading, spacing: 14) {
                Image(nsImage: NSApplication.shared.applicationIconImage)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 72, height: 72)

                Text("Create a practice paper")
                    .font(.largeTitle.weight(.semibold))

                Text("Choose the subject and paper. AI-assisted families also let you choose a model; constrained families run without one.")
                    .font(.title3)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            VStack(alignment: .leading, spacing: 18) {
                WelcomeRow(systemImage: "text.book.closed", title: "Choose a subject", message: "Each paper follows its exam board’s specification and structure.")
                WelcomeRow(systemImage: "cpu", title: "Choose a model", message: "Work locally with Ollama, or connect a hosted provider.")
                WelcomeRow(systemImage: "doc.badge.arrow.up", title: "Create both documents", message: "The question paper and mark scheme are saved together.")
            }

            Text("Paper creator makes unofficial practice material and is not affiliated with any exam board.")
                .font(.callout)
                .foregroundStyle(.secondary)

            HStack {
                SettingsLink {
                    Text("Settings…")
                }
                Spacer()
                Button("Continue") {
                    appModel.dismissWelcome()
                }
                .keyboardShortcut(.defaultAction)
                .controlSize(.large)
                .nativePrimaryActionStyle()
            }
        }
        .padding(36)
        .frame(width: 600)
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
                .font(.system(size: 18, weight: .medium))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.primary)
                .frame(width: 30, height: 30)
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 7, style: .continuous))
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
                    Text("Paper creator Help")
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
