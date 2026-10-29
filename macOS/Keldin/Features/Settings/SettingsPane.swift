// Edit generation preferences, provider settings and output-folder access.

import AppKit
import SwiftUI

struct SettingsPane: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @StateObject private var downloadPresentation = ModelDownloadPresentation()
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
        .environmentObject(downloadPresentation)
        .focusedSceneObject(downloadPresentation)
        .modifier(SettingsActionHost(presentation: application.settingsPresentation, download: downloadPresentation))
        .confirmationDialog(
            "Pull \(downloadPresentation.request?.model ?? "")?",
            isPresented: downloadConfirmationBinding,
            titleVisibility: .visible,
            presenting: downloadPresentation.request
        ) { request in
            Button("Pull Model") {
                guard let approved = downloadPresentation.consume(id: request.id) else { return }
                application.confirmPullModel(approved, presentation: application.settingsPresentation)
            }
            Button("Cancel", role: .cancel) { downloadPresentation.dismiss(id: request.id) }
        } message: { _ in
            Text("Ollama will download this model and make it available locally.")
        }
        .onDisappear {
            if let request = downloadPresentation.request { downloadPresentation.dismiss(id: request.id) }
        }
    }

    private var downloadConfirmationBinding: Binding<Bool> {
        let requestID = downloadPresentation.request?.id
        return Binding(
            get: { downloadPresentation.isPresented && downloadPresentation.request?.id == requestID },
            set: { visible in
                if !visible, let requestID { downloadPresentation.presentationDidDismiss(id: requestID) }
            }
        )
    }
}

private struct SettingsActionHost: ViewModifier {
    @EnvironmentObject private var application: ApplicationCoordinator
    @ObservedObject var presentation: SettingsActionPresentation
    @ObservedObject var download: ModelDownloadPresentation
    @State private var isAttached = false

    func body(content: Content) -> some View {
        content
            .focusedSceneObject(presentation)
            .alert(title, isPresented: presentedBinding, presenting: presentation.request) { request in
                switch request.kind {
                case let .hostedConsent(provider):
                    Button("Use Hosted AI") {
                        guard presentation.consume(id: request.id) != nil else { return }
                        application.acceptHostedAIConsent(for: provider, presentation: presentation)
                    }
                    Button("Cancel", role: .cancel) { presentation.dismiss(id: request.id) }
                case .error:
                    Button("OK", role: .cancel) { presentation.dismiss(id: request.id) }
                }
            } message: { request in
                switch request.kind {
                case .hostedConsent:
                    Text("OpenAI and Anthropic generation sends prompts, selected syllabus context, and draft question content to the provider you choose. API keys stay in Keychain. Ollama keeps generation local.")
                case let .error(message): Text(message)
                }
            }
            .onAppear {
                isAttached = true
                updateAvailability()
            }
            .onDisappear {
                isAttached = false
                presentation.deactivate()
            }
            .onChange(of: download.blocksCommands) { _, _ in updateAvailability() }
    }

    private var title: LocalizedStringKey {
        if case .hostedConsent = presentation.request?.kind { return "Hosted AI Disclosure" }
        return "Couldn't complete the action"
    }

    private var presentedBinding: Binding<Bool> {
        let id = presentation.request?.id
        return Binding(
            get: { presentation.blocksCommands && presentation.request?.id == id },
            set: { visible in
                if !visible, let id { presentation.presentationDidDismiss(id: id) }
            }
        )
    }

    private func updateAvailability() {
        if isAttached && !download.blocksCommands { presentation.activate() }
        else { presentation.deactivate() }
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
    @Environment(\.openWindow) private var openWindow
    @Environment(\.locale) private var locale
    @EnvironmentObject private var application: ApplicationCoordinator
    @EnvironmentObject private var downloadPresentation: ModelDownloadPresentation

    var body: some View {
        Form {
            Section("Provider") {
                Picker("Provider", selection: Binding(
                    get: { application.aiProvider },
                    set: { application.selectAIProvider($0, presentation: application.settingsPresentation) }
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
        .onChange(of: application.selectedModel) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
        .onChange(of: application.openAIModel) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
        .onChange(of: application.anthropicModel) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
        .onChange(of: application.appleModel) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
        .onChange(of: application.openAIAPIKey) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
        .onChange(of: application.anthropicAPIKey) { _, _ in application.saveAISettings(presentation: application.settingsPresentation) }
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
                        Button("Use Recommended Model") {
                            application.useRecommendedOllamaModel(presentation: application.settingsPresentation)
                        }
                            .disabled(application.selectedModelIsRecommended)
                    } else if application.distributionMode.canManageOllama {
                        Button("Download Recommended Model…") {
                            downloadPresentation.present(application.requestRecommendedOllamaModel())
                        }
                            .disabled(!application.canRequestModelDownload)
                    }

                    Button("Open Model Guide") {
                        MainWindowRouting.navigate(.help(.choosingAModel), application: application) {
                            openWindow(id: MainWindowRouting.sceneID, value: $0)
                        }
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
                    Button("Check Again") {
                        application.refreshOllama(presentation: application.settingsPresentation)
                    }
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
                            Button("Download") {
                                downloadPresentation.present(application.requestPullModel())
                            }
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
                        Button("Choose…") { application.chooseOutputFolder(presentation: application.settingsPresentation) }
                    }
                }
            }

            Section("Previous app data") {
                Button("Import previous app data…") {
                    application.importPreviousAppData(presentation: application.settingsPresentation)
                }
                    .disabled(application.isRunning)
                Text("Use this if your earlier papers or history were not imported automatically. Choose the former app's Application Support folder. You may need to choose your output folder again or re-enter API keys.")
                    .foregroundStyle(.secondary)
            }

            Section("Preview Mode") {
                Toggle(
                    "Create a layout preview",
                    isOn: Binding(
                        get: { application.dryRun },
                        set: { application.setDryRun($0, presentation: application.settingsPresentation) }
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
                        set: { application.setNotificationsEnabled($0, presentation: application.settingsPresentation) }
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
                        set: { application.setHistoryRetentionLimit($0, presentation: application.settingsPresentation) }
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
