// Explain setup and supported workflows in the welcome and help views.

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
                WelcomeRow(systemImage: "text.book.closed", title: "Choose a subject", message: "Choose the subject and assessment you want to practise.")
                WelcomeRow(systemImage: "cpu", title: "Use the recommended model", message: "Keldin recommends \(application.ollamaRecommendation.model) for this Mac; other models can produce different results.")
                WelcomeRow(systemImage: "doc.badge.arrow.up", title: "Create both documents", message: "The question paper and mark scheme are saved together.")
                WelcomeRow(systemImage: "doc.richtext", title: "Preview and review", message: "Inspect every generated PDF in Documents and return to any configuration from History.")
            }

            Text("Keldin makes unofficial practice material and is not affiliated with any exam board.")
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
    @Environment(\.locale) private var locale
    let systemImage: String
    let title: LocalizedStringResource
    let message: LocalizedStringResource

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: systemImage)
                .font(.system(size: 18, weight: .medium))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.primary)
                .frame(width: 30, height: 30)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(InterfaceText.localizedResource(title, locale: locale))
                    .font(.headline)
                Text(InterfaceText.localizedResource(message, locale: locale))
                    .foregroundStyle(.secondary)
            }
        }
        .accessibilityElement(children: .combine)
    }
}

struct HelpSheet: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @Environment(\.locale) private var locale

    var body: some View {
        VStack(spacing: 0) {
            NavigationSplitView {
                List(HelpTopic.allCases, selection: $application.helpTopic) { topic in
                    Label {
                        Text(InterfaceText.localizedResource(topic.titleResource, locale: locale))
                    } icon: {
                        Image(systemName: topic.systemImage)
                    }
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
    @Environment(\.locale) private var locale
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
    let topic: HelpTopic

    // Format dynamic values in the selected language, even when macOS uses another locale.
    private var selectedLocale: Locale {
        interfaceLanguage == "system" ? .current : Locale(identifier: interfaceLanguage)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Label {
                    Text(InterfaceText.localizedResource(topic.titleResource, locale: locale))
                } icon: {
                    Image(systemName: topic.systemImage)
                }
                    .font(.largeTitle.weight(.semibold))
                    .symbolRenderingMode(.hierarchical)

                switch topic {
                case .gettingStarted:
                    gettingStarted
                case .choosingAModel:
                    choosingAModel
                case .creatingAPaper:
                    creatingAPaper
                case .frenchBaccalaureat:
                    frenchBaccalaureat
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
            Text("Keldin creates unofficial practice papers and mark schemes. Check the selected subject's generation details before starting. Preview mode checks layout without calling AI. Every paper needs human review.")
                .foregroundStyle(.secondary)

            HelpSteps(
                rows: [
                    ("Choose a generator", "Select a supported subject and exam board in the sidebar."),
                    ("Prepare AI", "For local generation, install Ollama and use the model recommended for this Mac."),
                    ("Configure the paper", "Choose a paper, output folder, and provider. Leave preview mode off for new AI-written questions."),
                    ("Create and review", "Create the paper, then inspect both PDFs and the quality evidence before using them."),
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
            Text("The app chooses a model suggestion from this Mac's unified memory. This is not a ranking of paper quality.")
                .foregroundStyle(.secondary)

            GroupBox("Recommended for this Mac") {
                VStack(alignment: .leading, spacing: 10) {
                    LabeledContent("Model", value: application.ollamaRecommendation.model)
                    LabeledContent("Download size") {
                        Text(application.ollamaRecommendation.downloadResource(locale: selectedLocale, includeContext: false))
                    }
                    LabeledContent("Unified memory") {
                        Text(InterfaceText.localizedResource(currentMemoryResource, locale: selectedLocale))
                    }
                    LabeledContent("Model maximum context", value: application.ollamaRecommendation.contextWindow)
                    LabeledContent("Keldin context", value: application.ollamaRecommendation.appContextWindow)
                    Text(InterfaceText.localizedResource(application.ollamaRecommendation.detailResource, locale: locale))
                        .foregroundStyle(.secondary)
                    Text(InterfaceText.localizedResource(application.ollamaRecommendation.qualityNoteResource, locale: locale))
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 4)
            }

            HelpCallout(
                title: "Results may vary with other models",
                message: OllamaModelGuide.document.otherModelWarningResource,
                systemImage: "exclamationmark.triangle.fill"
            )

            HelpSection(
                title: "Checks and limits",
                rows: [
                    "Keldin checks structured output, marks, command words, topics and assessment objectives. Invalid output can stop generation.",
                    "With the default local Ollama server, prompts and generated content stay on this Mac.",
                    "Difficulty checks compare task features with past papers. Each valid choice of questions is checked separately, as is every printed alternative. Completion times are estimates; no learner timings have been measured.",
                    "Question review, answer checking and difficulty checks use separate prompts and evidence. They may use the same model, so they are not independent model opinions.",
                    "Completed papers are checked for changes in their expected task mix. These limits are engineering rules, not measured confidence intervals. No examiner approval or learner calibration is claimed.",
                ]
            )

            HelpSection(
                title: "Memory guidance",
                rows: [
                    "16 GB or more: gemma4:12b is the configured local suggestion.",
                    "Below 16 GB: qwen2.5:7b is the smaller local suggestion. Memory use still depends on other apps and context.",
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
            Text("New papers may cover familiar topics or include similar questions. Checks still reject duplicate questions within a paper.")
                .foregroundStyle(.secondary)
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
                    "Use Recent Documents to open both PDFs. Quality review reports blueprint, originality, visual, and difficulty evidence separately.",
                    "Difficulty is intended demand until the exact form has enough independently reviewed examiner, learner-response, and timing evidence; the app does not claim psychometric equivalence.",
                ]
            )
        }
    }

    private var frenchBaccalaureat: some View {
        Group {
            Text("Five paper families are available and can be used again for practice.")
                .foregroundStyle(.secondary)
            Text("The French route creates original Terminale NSI written practice for the 2027 rules. It is separate from the UK exam-board generators and does not include the practical component.")
                .foregroundStyle(.secondary)

            HelpSteps(
                rows: [
                    ("Prepare references", "Approve the one-time download from registered French Ministry sources. Holdout material is excluded from generation."),
                    ("Create a draft", "The app builds three independent exercises, 18 technical points and a distinct indicative two-point language component."),
                    ("Inspect the bundle", "Read the subject, proposed correction and validation record. Check every structured table, graph, answer and allocation."),
                    ("Work through the paper", "Check the syllabus content, reasoning steps, calculations and proposed marks against official papers. Automated checks do not establish equal difficulty."),
                    ("Keep the limits visible", "Difficulty and completion time are uncalibrated. An optional teacher-review record can be attached to the exact artifact hashes; the app does not invent one."),
                ]
            )

            HelpCallout(
                title: "Unreviewed and non-official",
                message: "Automated authoring, solving and verification do not constitute Ministry, examiner or teacher approval. Regenerating or editing any artifact invalidates its recorded review.",
                systemImage: "person.badge.shield.checkmark"
            )

            HelpSection(
                title: "Local data and deletion",
                rows: [
                    "French source PDFs and their search index stay in Application Support until you delete them from the French workspace.",
                    "French papers are built locally from a fixed catalogue. No AI model, Ollama installation or cloud service is needed.",
                    "Generated bundles contain questions, corrections, provenance and validation evidence, but no student accounts or submitted answers.",
                ]
            )

            HStack {
                Link("Official 2027 NSI definition", destination: URL(string: "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")!)
                Link("Official language rubric", destination: URL(string: "https://www.education.gouv.fr/sites/default/files/document/annexe-attendus-et-observables-redactionnels-520693.pdf")!)
            }
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
                "Command-Return: Create Paper",
                "Command-Period: Cancel Generation",
                "Option-Command-O: Open Output Folder",
                "Shift-Command-B: Show Benchmark",
                "Shift-Command-D: Show Documents",
                "Shift-Command-Y: Show History",
                "Shift-Command-H: Keldin Help",
                "Command-Comma: Settings",
            ]
        )
    }

    private var currentMemoryResource: LocalizedStringResource {
        let value = Double(ProcessInfo.processInfo.physicalMemory) / 1_073_741_824
        return LocalizedStringResource("\(Int(value.rounded())) GB", locale: selectedLocale)
    }
}

private struct HelpSection: View {
    @Environment(\.locale) private var locale
    let title: LocalizedStringResource
    let rows: [LocalizedStringResource]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(InterfaceText.localizedResource(title, locale: locale))
                .font(.headline)
            ForEach(rows, id: \.key) { row in
                Label {
                    Text(InterfaceText.localizedResource(row, locale: locale))
                } icon: {
                    Image(systemName: "checkmark.circle")
                }
                    .symbolRenderingMode(.hierarchical)
            }
        }
    }
}

private struct HelpSteps: View {
    @Environment(\.locale) private var locale
    let rows: [(LocalizedStringResource, LocalizedStringResource)]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            ForEach(Array(rows.enumerated()), id: \.element.0.key) { index, row in
                HStack(alignment: .top, spacing: 12) {
                    Image(systemName: "\(index + 1).circle.fill")
                        .font(.title3)
                        .symbolRenderingMode(.hierarchical)
                        .accessibilityHidden(true)
                    VStack(alignment: .leading, spacing: 3) {
                        Text(InterfaceText.localizedResource(row.0, locale: locale))
                            .font(.headline)
                        Text(InterfaceText.localizedResource(row.1, locale: locale))
                            .foregroundStyle(.secondary)
                    }
                }
                .accessibilityElement(children: .combine)
            }
        }
    }
}

private struct HelpCallout: View {
    @Environment(\.locale) private var locale
    let title: LocalizedStringResource
    let message: LocalizedStringResource
    let systemImage: String

    var body: some View {
        GroupBox {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: systemImage)
                    .symbolRenderingMode(.hierarchical)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 3) {
                    Text(InterfaceText.localizedResource(title, locale: locale))
                        .font(.headline)
                    Text(InterfaceText.localizedResource(message, locale: locale))
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
