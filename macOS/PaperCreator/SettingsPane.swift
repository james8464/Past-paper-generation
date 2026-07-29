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

                if !appModel.selectedBoard.usesAI {
                    Label(
                        "\(appModel.selectedBoard.subjectTitle) \(appModel.selectedBoard.shortTitle) uses a built-in constrained generator. These settings only affect AI-assisted papers.",
                        systemImage: "info.circle"
                    )
                    .foregroundStyle(.secondary)
                }

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
                Picker("Model", selection: $appModel.selectedModel) {
                    if appModel.availableModels.isEmpty {
                        Text(appModel.selectedModel).tag(appModel.selectedModel)
                    } else {
                        ForEach(appModel.availableModels, id: \.self) { model in
                            Text(model).tag(model)
                        }
                    }
                }

                HStack {
                    Button("Check Again", action: appModel.refreshOllama)
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
                Text("Use a Hugging Face model ID or the path to a model already on this Mac.")
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
                        Text(appModel.outputFolder.path)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                        Button("Choose...", action: appModel.chooseOutputFolder)
                    }
                }
            }

            Section("Preview Mode") {
                Toggle(
                    "Use built-in drafts",
                    isOn: Binding(
                        get: { appModel.dryRun },
                        set: { appModel.setDryRun($0) }
                    )
                )
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
                Text("Paper creator only sends notifications about work you start.")
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
