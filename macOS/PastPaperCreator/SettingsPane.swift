import SwiftUI

struct SettingsPane: View {
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
                LabeledContent("Accounts", value: "Not required")
                LabeledContent("API keys", value: "Keychain")
                LabeledContent("Hosted AI consent", value: appModel.hasHostedAIConsent ? "Accepted" : "Not accepted")
                Link("Privacy Policy", destination: AppLinks.privacyPolicy)
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
                Button("ExamForge Help", action: appModel.showHelpGuide)
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
