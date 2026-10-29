// Edit generation preferences, provider settings and output-folder access.

import AppKit
import SwiftUI

struct SettingsPane: View {
    @AppStorage("interfaceLanguage") private var interfaceLanguage = "system"
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
        .navigationTitle(InterfaceText.resolve(selectedPane.title, language: interfaceLanguage))
        .background(SettingsWindowConfiguration(title: InterfaceText.resolve(selectedPane.title, language: interfaceLanguage)))
        .environment(\.locale, interfaceLanguage == "system" ? .current : Locale(identifier: interfaceLanguage))
    }
}

private enum SettingsPaneID: String {
    case ai
    case output
    case privacy

    var title: LocalizedStringResource {
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
    @Environment(\.locale) private var locale
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        Form {
            Section("Provider") {
                Picker("Provider", selection: Binding(
                    get: { application.aiProvider },
                    set: { application.selectAIProvider($0) }
                )) {
                    ForEach(AIProvider.allCases) { provider in
                        Text(provider.title).tag(provider)
                    }
                }
                .pickerStyle(.segmented)

                Text(InterfaceText.localizedResource(application.aiProvider.subtitleResource, locale: locale))
                    .foregroundStyle(.secondary)

                if application.aiProvider.sendsPromptsOffDevice {
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
        .disabled(application.isRunning)
        .onChange(of: application.selectedModel) { _, _ in application.saveAISettings() }
        .onChange(of: application.openAIModel) { _, _ in application.saveAISettings() }
        .onChange(of: application.anthropicModel) { _, _ in application.saveAISettings() }
        .onChange(of: application.appleModel) { _, _ in application.saveAISettings() }
        .onChange(of: application.openAIAPIKey) { _, _ in application.saveAISettings() }
        .onChange(of: application.anthropicAPIKey) { _, _ in application.saveAISettings() }
    }

    @ViewBuilder
    private var providerSettings: some View {
        switch application.aiProvider {
        case .ollama:
            Section("Local model") {
                LabeledContent("Recommended") {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(application.ollamaRecommendation.model)
                        Text(application.ollamaRecommendation.downloadResource(locale: locale))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Text(InterfaceText.localizedResource(application.ollamaRecommendation.detailResource, locale: locale))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack {
                    if application.recommendedModelIsInstalled {
                        Button("Use Recommended Model", action: application.useRecommendedOllamaModel)
                            .disabled(application.selectedModelIsRecommended)
                    } else if application.distributionMode.canManageOllama {
                        Button("Download Recommended Model…", action: application.requestRecommendedOllamaModel)
                            .disabled(!application.canRequestModelDownload)
                    }

                    Button("Open Model Guide") {
                        application.showHelpGuide(topic: .choosingAModel)
                    }
                }

                Divider()

                Picker("Model", selection: $application.selectedModel) {
                    ForEach(application.ollamaModelOptions, id: \.self) { model in
                        if model == application.ollamaRecommendation.model {
                            Text("\(model) (recommended)").tag(model)
                        } else {
                            Text(model).tag(model)
                        }
                    }
                }

                if application.selectedModelIsRecommended {
                    Label("Recommended model selected", systemImage: "checkmark.seal.fill")
                        .foregroundStyle(.primary)
                } else {
                    Label {
                        Text(InterfaceText.localizedResource(OllamaModelGuide.document.otherModelWarningResource, locale: locale))
                    } icon: {
                        Image(systemName: "exclamationmark.triangle.fill")
                    }
                    .foregroundStyle(.primary)
                    .fixedSize(horizontal: false, vertical: true)
                }

                HStack {
                    Button("Check Again", action: application.refreshOllama)
                        .disabled(application.isRefreshingOllama)
                    Spacer()
                    Text(InterfaceText.localizedResource(application.ollamaState.messageResource, locale: locale))
                        .foregroundStyle(.secondary)
                }

                if application.distributionMode.canManageOllama {
                    LabeledContent("Download model") {
                        HStack {
                            TextField("Model name", text: $application.modelToPull)
                                .frame(minWidth: 190)
                            Button("Download", action: application.requestPullModel)
                                .disabled(application.modelToPull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !application.canRequestModelDownload)
                        }
                    }
                } else {
                    Text("Models are managed in Ollama. Once a model is installed, choose Check Again.")
                        .foregroundStyle(.secondary)
                }
            }

        case .openAI:
            Section("OpenAI") {
                TextField("Model", text: $application.openAIModel)
                SecureField("API key", text: $application.openAIAPIKey)
                Text("Your key is stored in Keychain.")
                    .foregroundStyle(.secondary)
            }

        case .anthropic:
            Section("Anthropic") {
                TextField("Model", text: $application.anthropicModel)
                SecureField("API key", text: $application.anthropicAPIKey)
                Text("Your key is stored in Keychain.")
                    .foregroundStyle(.secondary)
            }

        case .apple:
            Section("Apple MLX") {
                TextField("Model ID or path", text: $application.appleModel)
                Text("Use a Hugging Face model ID or the path to a model already on this Mac. Keldin offers guided setup before the first live generation with each model.")
                    .foregroundStyle(.secondary)
                Text("Setup checks that a model can run, not paper quality. Generation stops if the model changes source data or fails answer and marking checks.")
                    .foregroundStyle(.secondary)
            }
        }
    }
}

private struct OutputSettingsTab: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        Form {
            Section("Folder") {
                LabeledContent("Output") {
                    HStack {
                        Text(application.outputFolderDisplayPath)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                        Button("Choose…", action: application.chooseOutputFolder)
                    }
                }
            }

            Section("Previous app data") {
                Button("Import previous app data…", action: application.importPreviousAppData)
                    .disabled(application.isRunning)
                Text("Use this if your earlier papers or history were not imported automatically. Choose the former app's Application Support folder. You may need to choose your output folder again or re-enter API keys.")
                    .foregroundStyle(.secondary)
            }

            Section("Preview Mode") {
                Toggle(
                    "Create a layout preview",
                    isOn: Binding(
                        get: { application.dryRun },
                        set: { application.setDryRun($0) }
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
                        get: { application.notificationsEnabled },
                        set: { application.setNotificationsEnabled($0) }
                    )
                )
                Text("Keldin only sends notifications about work you start.")
                    .foregroundStyle(.secondary)
            }

            Section("History") {
                Stepper(
                    "Keep \(application.settingsStore.historyRetentionLimit) jobs",
                    value: Binding(
                        get: { application.settingsStore.historyRetentionLimit },
                        set: { application.setHistoryRetentionLimit($0) }
                    ),
                    in: 10 ... 500,
                    step: 10
                )
                Text("History stores configuration and provenance. Generated PDFs remain in the folder you chose.")
                    .foregroundStyle(.secondary)
                if !application.recentDocumentStore.retentionFailureIDs.isEmpty {
                    Label("Some older history items couldn't be removed. They remain listed in History until cleanup succeeds.", systemImage: "exclamationmark.triangle")
                }
            }
        }
        .formStyle(.grouped)
        .disabled(application.isRunning)
    }
}

private struct PrivacySettingsTab: View {
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        Form {
            Section("Privacy") {
                LabeledContent("Distribution", value: application.distributionMode.title)
                LabeledContent("Accounts", value: "Not required")
                LabeledContent("API keys", value: "Keychain")
                LabeledContent("Hosted AI consent", value: application.hasHostedAIConsent ? "Accepted" : "Not accepted")
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
