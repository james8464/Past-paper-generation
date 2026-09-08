import AppKit
import Foundation
import SwiftUI

struct WelcomeSheet: View {
    @EnvironmentObject private var application: ApplicationCoordinator

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
                WelcomeRow(systemImage: "cpu", title: "Use the recommended model", message: "Paper creator recommends \(application.ollamaRecommendation.model) for this Mac; other models can produce different results.")
                WelcomeRow(systemImage: "doc.badge.arrow.up", title: "Create both documents", message: "The question paper and mark scheme are saved together.")
                WelcomeRow(systemImage: "doc.richtext", title: "Preview and review", message: "Inspect every generated PDF in Documents and return to any configuration from History.")
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
                    application.dismissWelcome()
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
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                Text(message)
                    .foregroundStyle(.secondary)
            }
        }
        .accessibilityElement(children: .combine)
    }
}

struct HelpSheet: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        VStack(spacing: 0) {
            NavigationSplitView {
                List(HelpTopic.allCases, selection: $application.helpTopic) { topic in
                    Label(topic.title, systemImage: topic.systemImage)
                        .tag(topic)
                }
                .listStyle(.sidebar)
                .navigationTitle("Help")
                .navigationSplitViewColumnWidth(min: 190, ideal: 220, max: 260)
            } detail: {
                HelpTopicPage(topic: application.helpTopic)
            }
            .navigationSplitViewStyle(.balanced)

            Divider()

            HStack {
                Button("Copy Diagnostics", action: application.copyDiagnosticSummary)
                Button("Report Issue", action: application.openSupportPage)
                Spacer()
                Button("Done", action: application.dismissHelpGuide)
                    .keyboardShortcut(.defaultAction)
                    .nativePrimaryActionStyle()
            }
            .padding(16)
        }
        .frame(width: 920, height: 680)
        .presentationSizing(.fitted)
    }
}

private struct HelpTopicPage: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    let topic: HelpTopic

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Label(topic.title, systemImage: topic.systemImage)
                    .font(.largeTitle.weight(.semibold))
                    .symbolRenderingMode(.hierarchical)

                switch topic {
                case .gettingStarted:
                    gettingStarted
                case .choosingAModel:
                    choosingAModel
                case .creatingAPaper:
                    creatingAPaper
                case .checkingQuality:
                    checkingQuality
                case .privacy:
                    privacy
                case .troubleshooting:
                    troubleshooting
                case .shortcuts:
                    shortcuts
                }
            }
            .frame(maxWidth: 680, alignment: .leading)
            .padding(32)
        }
    }

    private var gettingStarted: some View {
        Group {
            Text("Paper creator builds a new unofficial question paper and mark scheme from a board-specific blueprint. Normal generation asks your selected AI model to write original questions; preview mode checks layout without calling AI.")
                .foregroundStyle(.secondary)

            HelpSteps(
                rows: [
                    ("Choose a generator", "Select a supported subject and exam board in the sidebar."),
                    ("Prepare AI", "For local generation, install Ollama and use the model recommended for this Mac."),
                    ("Configure the paper", "Choose a paper, output folder, and provider. Leave preview mode off for new AI-written questions."),
                    ("Create and review", "Create the paper, then inspect the PDFs and the Quality inspector before using them."),
                ]
            )

            HelpCallout(
                title: "Unofficial practice material",
                message: "Generated work is not affiliated with or endorsed by an exam board. Always review it before giving it to students.",
                systemImage: "info.circle"
            )
        }
    }

    private var choosingAModel: some View {
        Group {
            Text("The recommendation is selected from this Mac’s unified-memory capacity and this project’s paper-generation workload, not from a generic chatbot ranking.")
                .foregroundStyle(.secondary)

            GroupBox("Recommended for this Mac") {
                VStack(alignment: .leading, spacing: 10) {
                    LabeledContent("Model", value: application.ollamaRecommendation.model)
                    LabeledContent("Download", value: application.ollamaRecommendation.downloadDescription)
                    LabeledContent("Unified memory", value: currentMemoryDescription)
                    LabeledContent("Model maximum context", value: application.ollamaRecommendation.contextWindow)
                    LabeledContent("Paper creator context", value: application.ollamaRecommendation.appContextWindow)
                    Text(application.ollamaRecommendation.detail)
                        .foregroundStyle(.secondary)
                    Text(application.ollamaRecommendation.qualityNote)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 4)
            }

            HelpScreenshot(
                name: "TutorialModelSettings",
                caption: "AI Settings identifies the recommendation and warns when another model is selected."
            )

            HelpCallout(
                title: "Results may vary with other models",
                message: OllamaModelGuide.document.otherModelWarning,
                systemImage: "exclamationmark.triangle.fill"
            )

            HelpSection(
                title: "Why this model",
                rows: [
                    "It follows the app’s exact JSON schemas and immutable marks, command words, topics, and assessment-objective totals.",
                    "It has enough reasoning capacity for source-based questions and detailed level-of-response mark schemes while remaining practical on a Mac.",
                    "Ollama keeps prompts and generated content on this Mac.",
                    "Intended cognitive demand is compared with source-derived feature proxies, not measured learner difficulty. Every legal candidate path is checked separately; every printed alternative still needs item review. Times are allocated, not observed.",
                    "Content review, independent solution checking, and difficulty review use separate prompts and evidence. They may use the same selected model, but one check never stands in for another.",
                    "Every completed form is checked again for distribution drift. These engineering tolerances are not empirically learned confidence intervals, and external examiner and learner evidence is still needed for qualification.",
                ]
            )

            HelpSection(
                title: "Memory guidance",
                rows: [
                    "16 GB or more: use gemma4:12b for the intended quality level.",
                    "8 GB: qwen2.5:7b is the memory-compatible option, but expect weaker long-form questions and mark schemes and review every page carefully.",
                    "Keep memory-heavy apps closed during generation. Model download size is not the model’s complete runtime memory requirement.",
                ]
            )

            HStack {
                Link("Ollama model details", destination: AppLinks.gemmaModel)
                Link("Structured-output guide", destination: AppLinks.ollamaStructuredOutputs)
            }
        }
    }

    private var creatingAPaper: some View {
        Group {
            HelpScreenshot(
                name: "TutorialWorkspace",
                caption: "The workspace keeps the paper configuration, create action, recent files, and release gates visible together."
            )

            HelpSteps(
                rows: [
                    ("Select subject and board", "Only implemented generators appear. Their papers come from the canonical generator registry."),
                    ("Choose the assessment", "Select a full paper or, where available, Topic Practice. The blueprint locks marks, command words, syllabus scope, and expected demand."),
                    ("Check the provider", "Ollama must be running and the selected model must be installed. Hosted providers require a key and explicit consent."),
                    ("Choose a folder", "The question paper, mark scheme, assessment evidence, and package manifest are published together only after validation passes."),
                    ("Create the assessment", "Generation can take several minutes. Progress and the estimated time remain visible, and Command-Period cancels safely."),
                    ("Preview and reuse", "Documents opens every generated PDF in the app. History can duplicate a setup or create a new form with a new seed."),
                ]
            )

            HelpCallout(
                title: "Preview mode is not a finished paper",
                message: "Create a layout preview only when checking document geometry. Preview content has no live item-review or originality evidence, and missing saved evidence is reported as unknown rather than passed.",
                systemImage: "doc.text.magnifyingglass"
            )

            HelpCallout(
                title: "Use Topic Practice for focused revision",
                message: "A topic bank is matched to reviewed topic and task-operation records, not full-paper AO percentages. Sparse, mixed or missing source evidence is shown as Insufficient. A bank may be built after structural, correctness, source-content and item-review checks pass while calibration remains insufficient; this is not a calibration pass or external qualification. Data structures, databases, and functional programming are available for AQA Computer Science.",
                systemImage: "square.stack.3d.up"
            )
        }
    }

    private var checkingQuality: some View {
        Group {
            Text("A generated PDF can look convincing and still contain a weak or ambiguous question. Review content and presentation separately.")
                .foregroundStyle(.secondary)

            HelpSection(
                title: "Question and mark-scheme review",
                rows: [
                    "Confirm each command word matches the marks and the expected depth of response.",
                    "Check every fact, calculation, chart label, unit, source reference, distractor, and correct answer.",
                    "Ensure the mark scheme awards every available mark, uses specific creditworthy points, and supports consistent marking.",
                    "For essays, look for accurate knowledge, contextual application, developed analysis, balanced evaluation, and a supported judgement.",
                ]
            )

            HelpSection(
                title: "Layout review",
                rows: [
                    "Check page size, cover hierarchy, fonts, margins, question numbering, mark placement, continuation space, tables, diagrams, and page breaks.",
                    "Use Recent Documents to open both PDFs. The Quality inspector reports blueprint, originality, visual, and difficulty evidence separately.",
                    "Difficulty is intended demand until the exact form has enough independently reviewed examiner, learner-response, and timing evidence; the app does not claim psychometric equivalence.",
                ]
            )
        }
    }

    private var privacy: some View {
        Group {
            HelpSection(
                title: "Local AI",
                rows: [
                    "Ollama generation stays on this Mac and does not require an account.",
                    "The App Store build can detect Ollama but cannot install the app or download models; manage those in Ollama.",
                ]
            )
            HelpSection(
                title: "Hosted AI",
                rows: [
                    "OpenAI and Anthropic receive the generation prompt, relevant syllabus context, and draft assessment data when selected.",
                    "API keys are stored in Keychain. Hosted generation remains blocked until you accept the disclosure.",
                ]
            )
            Link("Read the Privacy Policy", destination: AppLinks.privacyPolicy)
        }
    }

    private var troubleshooting: some View {
        Group {
            HelpSection(
                title: "Ollama is unavailable",
                rows: [
                    "Open Ollama, wait for it to start, then choose AI > Check Ollama Status.",
                    "If a model is missing, download the exact recommended tag shown in AI Settings and check again.",
                    "If generation repeatedly fails, keep enough free memory, stop other model workloads, and copy diagnostics before reporting the issue.",
                ]
            )
            HelpSection(
                title: "A paper fails validation",
                rows: [
                    "No partial package is published. The error identifies the failed provider, content, or PDF gate.",
                    "Retry once with the recommended model. A different seed creates a new form; changing models can materially change quality.",
                    "Use Tools > Show Benchmark to check memory pressure, storage, thermal state, PDF speed, network, and Ollama latency.",
                ]
            )
        }
    }

    private var shortcuts: some View {
        HelpSection(
            title: "Commands",
            rows: [
                "Command-Return — Create Paper",
                "Command-Period — Cancel Generation",
                "Option-Command-O — Open Output Folder",
                "Shift-Command-B — Show Benchmark",
                "Shift-Command-D — Show Documents",
                "Shift-Command-Y — Show History",
                "Shift-Command-H — Paper creator Help",
                "Command-Comma — Settings",
            ]
        )
    }

    private var currentMemoryDescription: String {
        let value = Double(ProcessInfo.processInfo.physicalMemory) / 1_073_741_824
        return "\(Int(value.rounded())) GB"
    }
}

private struct HelpSection: View {
    let title: String
    let rows: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
            ForEach(rows, id: \.self) { row in
                Label(row, systemImage: "checkmark.circle")
                    .symbolRenderingMode(.hierarchical)
            }
        }
    }
}

private struct HelpSteps: View {
    let rows: [(String, String)]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            ForEach(Array(rows.enumerated()), id: \.offset) { index, row in
                HStack(alignment: .top, spacing: 12) {
                    Image(systemName: "\(index + 1).circle.fill")
                        .font(.title3)
                        .symbolRenderingMode(.hierarchical)
                        .accessibilityHidden(true)
                    VStack(alignment: .leading, spacing: 3) {
                        Text(row.0)
                            .font(.headline)
                        Text(row.1)
                            .foregroundStyle(.secondary)
                    }
                }
                .accessibilityElement(children: .combine)
            }
        }
    }
}

private struct HelpCallout: View {
    let title: String
    let message: String
    let systemImage: String

    var body: some View {
        GroupBox {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: systemImage)
                    .symbolRenderingMode(.hierarchical)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.headline)
                    Text(message)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

private struct HelpScreenshot: View {
    let name: String
    let caption: String

    var body: some View {
        if let image = NSImage(named: NSImage.Name(name)) {
            VStack(alignment: .leading, spacing: 8) {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFit()
                    .accessibilityLabel(caption)
                Text(caption)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
