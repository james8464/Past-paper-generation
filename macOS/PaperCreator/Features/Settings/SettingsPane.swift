import AppKit
import SwiftUI

struct SettingsPane: View {
    @AppStorage(AppStorageKey.settingsPane)
    private var selectedPane = SettingsPaneID.ai

    var body: some View {
        TabView(selection: $selectedPane) {
            AISettingsTab()
                .tabItem {
                    Label("AI", systemImage: "sparkles")
                }
                .tag(SettingsPaneID.ai)

            OutputSettingsTab()
                .tabItem {
                    Label("Output", systemImage: "folder")
                }
                .tag(SettingsPaneID.output)

            PrivacySettingsTab()
                .tabItem {
                    Label("Privacy", systemImage: "hand.raised")
                }
                .tag(SettingsPaneID.privacy)
        }
        .scenePadding()
        .frame(minWidth: 620, minHeight: 500)
        .navigationTitle(selectedPane.title)
        .background(SettingsWindowConfiguration(title: selectedPane.title))
    }
}

private enum SettingsPaneID: String {
    case ai
    case output
    case privacy

    var title: String {
        switch self {
        case .ai: "AI Settings"
        case .output: "Output Settings"
        case .privacy: "Privacy Settings"
        }
    }
}

private struct SettingsWindowConfiguration: NSViewRepresentable {
    let title: String

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async { configure(view.window) }
        return view
    }

    func updateNSView(_ view: NSView, context: Context) {
        DispatchQueue.main.async { configure(view.window) }
    }

    private func configure(_ window: NSWindow?) {
        window?.title = title
        window?.standardWindowButton(.miniaturizeButton)?.isEnabled = false
        window?.standardWindowButton(.zoomButton)?.isEnabled = false
    }
}

private struct AISettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Provider") {
                Picker("Provider", selection: Binding(
                    get: { appModel.aiProvider },
                    set: { appModel.selectAIProvider($0) }
                )) {
                    ForEach(AIProvider.allCases) { provider in
                        Text(provider.title).tag(provider)
                    }
                }
                .pickerStyle(.segmented)

                Text(appModel.aiProvider.subtitle)
                    .foregroundStyle(.secondary)

                if appModel.aiProvider.sendsPromptsOffDevice {
                    Label(
                        "Prompts and subject context may be sent to the selected provider.",
                        systemImage: "network"
                    )
                    .foregroundStyle(.secondary)
                }
            }

            providerSettings

        }
        .formStyle(.grouped)
        .disabled(appModel.isRunning)
        .onChange(of: appModel.selectedModel) { _, _ in appModel.saveAISettings() }
        .onChange(of: appModel.openAIModel) { _, _ in appModel.saveAISettings() }
        .onChange(of: appModel.anthropicModel) { _, _ in appModel.saveAISettings() }
        .onChange(of: appModel.appleModel) { _, _ in appModel.saveAISettings() }
        .onChange(of: appModel.openAIAPIKey) { _, _ in appModel.saveAISettings() }
        .onChange(of: appModel.anthropicAPIKey) { _, _ in appModel.saveAISettings() }
    }

    @ViewBuilder
    private var providerSettings: some View {
        switch appModel.aiProvider {
        case .ollama:
            Section("Local model") {
                LabeledContent("Recommended") {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(appModel.ollamaRecommendation.model)
                        Text(appModel.ollamaRecommendation.downloadDescription)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Text(appModel.ollamaRecommendation.detail)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack {
                    if appModel.recommendedModelIsInstalled {
                        Button("Use Recommended Model", action: appModel.useRecommendedOllamaModel)
                            .disabled(appModel.selectedModelIsRecommended)
                    } else if appModel.distributionMode.canManageOllama {
                        Button("Download Recommended Model…", action: appModel.requestRecommendedOllamaModel)
                            .disabled(appModel.isRunning)
                    }

                    Button("Open Model Guide") {
                        appModel.showHelpGuide(topic: .choosingAModel)
                    }
                }

                Divider()

                Picker("Model", selection: $appModel.selectedModel) {
                    ForEach(appModel.ollamaModelOptions, id: \.self) { model in
                        Text(
                            model == appModel.ollamaRecommendation.model
                                ? "\(model) — Recommended"
                                : model
                        )
                        .tag(model)
                    }
                }

                if appModel.selectedModelIsRecommended {
                    Label("Recommended model selected", systemImage: "checkmark.seal.fill")
                        .foregroundStyle(.green)
                } else {
                    Label(
                        OllamaModelGuide.document.otherModelWarning,
                        systemImage: "exclamationmark.triangle.fill"
                    )
                    .foregroundStyle(.orange)
                    .fixedSize(horizontal: false, vertical: true)
                }

                HStack {
                    Button("Check Again", action: appModel.refreshOllama)
                        .disabled(appModel.isRefreshingOllama)
                    Spacer()
                    Text(appModel.ollamaState.message)
                        .foregroundStyle(.secondary)
                }

                if appModel.distributionMode.canManageOllama {
                    LabeledContent("Download model") {
                        HStack {
                            TextField("Model name", text: $appModel.modelToPull)
                                .frame(minWidth: 190)
                            Button("Download", action: appModel.requestPullModel)
                                .disabled(appModel.modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || appModel.isRunning)
                        }
                    }
                } else {
                    Text("Models are managed in Ollama. Once a model is installed, choose Check Again.")
                        .foregroundStyle(.secondary)
                }
            }

        case .openAI:
            Section("OpenAI") {
                TextField("Model", text: $appModel.openAIModel)
                SecureField("API key", text: $appModel.openAIAPIKey)
                Text("Your key is stored in Keychain.")
                    .foregroundStyle(.secondary)
            }

        case .anthropic:
            Section("Anthropic") {
                TextField("Model", text: $appModel.anthropicModel)
                SecureField("API key", text: $appModel.anthropicAPIKey)
                Text("Your key is stored in Keychain.")
                    .foregroundStyle(.secondary)
            }

        case .apple:
            Section("Apple MLX") {
                TextField("Model ID or path", text: $appModel.appleModel)
                Text("Use a Hugging Face model ID or the path to a model already on this Mac. Paper Creator offers guided setup before the first live generation with each model.")
                    .foregroundStyle(.secondary)
            }
        }
    }
}

private struct OutputSettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Folder") {
                LabeledContent("Output") {
                    HStack {
                        Text(appModel.outputFolderDisplayPath)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                        Button("Choose...", action: appModel.chooseOutputFolder)
                    }
                }
            }

            Section("Preview Mode") {
                Toggle(
                    "Create a layout preview",
                    isOn: Binding(
                        get: { appModel.dryRun },
                        set: { appModel.setDryRun($0) }
                    )
                )
                Text(
                    "Creates sample PDFs without contacting an AI provider. "
                    + "Preview questions are placeholders and are not release-ready."
                )
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
                Text("Paper creator only sends notifications about work you start.")
                    .foregroundStyle(.secondary)
            }

            Section("History") {
                Stepper(
                    "Keep \(appModel.settingsStore.historyRetentionLimit) jobs",
                    value: Binding(
                        get: { appModel.settingsStore.historyRetentionLimit },
                        set: { value in
                            appModel.settingsStore.historyRetentionLimit = value
                            appModel.settingsStore.save()
                            appModel.recentDocumentStore.retentionLimit = value
                        }
                    ),
                    in: 10 ... 500,
                    step: 10
                )
                Text("History stores configuration and provenance. Generated PDFs remain in the folder you chose.")
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
        .disabled(appModel.isRunning)
    }
}

private struct PrivacySettingsTab: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        Form {
            Section("Privacy") {
                LabeledContent("Distribution", value: appModel.distributionMode.title)
                LabeledContent("Accounts", value: "Not required")
                LabeledContent("API keys", value: "Keychain")
                LabeledContent("Hosted AI consent", value: appModel.hasHostedAIConsent ? "Accepted" : "Not accepted")
                Link("Privacy Policy", destination: AppLinks.privacyPolicy)
                Text("Ollama generation is local. Hosted providers send prompts to the provider you select.")
                    .foregroundStyle(.secondary)
            }

            Section {
                Text("Unofficial practice material. Not affiliated with Pearson, Edexcel, AQA, or any exam board.")
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
    }
}
