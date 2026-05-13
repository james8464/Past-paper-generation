# App Store Review Checklist

Sources:

- Apple App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Apple App Sandbox: https://developer.apple.com/documentation/security/app-sandbox
- Apple privacy manifests: https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk
- App Store Connect app information: https://developer.apple.com/help/app-store-connect/reference/app-information/app-information
- Apple user privacy and data use: https://developer.apple.com/app-store/user-privacy-and-data-use/
- Apple notification guidance: https://developer.apple.com/design/human-interface-guidelines/notifications

## Rejection Risks

- App completeness: crashes, broken generation flow, missing backend, missing model/API setup, placeholder features advertised as available.
- Metadata mismatch: screenshots/descriptions showing unavailable subjects, official exam-board affiliation, pricing or claims not present in the app.
- Privacy mismatch: App Privacy answers, privacy policy, and `PrivacyInfo.xcprivacy` disagreeing with actual behavior.
- Third-party AI disclosure: hosted providers sending prompts off-device without an explicit in-app disclosure and consent.
- macOS packaging: no sandbox, third-party installers in App Store build, shared-location installs, login/background agents, or root escalation.
- Downloaded code/resources: App Store build installing Ollama or pulling model executables that materially change reviewed functionality.
- Notification misuse: notifications required for core use, sensitive content in notifications, marketing notifications without opt-in.
- File access: writing outside user-selected folders or relying on unsandboxed Downloads access.
- Intellectual property: using Pearson, Edexcel, AQA, or Apple branding/logos in ways that imply affiliation.

## Guideline Mapping

- 2.1 App Completeness: no crashes, no broken flows, no placeholder text, and reviewers need full access or a complete demo mode.
- 2.3 Accurate Metadata: screenshots, descriptions, privacy answers, ready subjects, and hidden features must match the binary.
- 2.5.2 Self-contained App: App Store builds must not install Ollama, pull model executables, or rely on resources outside the reviewed bundle.
- 5.1.1 Privacy Policy: privacy policy link must be live in App Store Connect and inside the app; it must explain collection, sharing, retention, deletion, and consent.
- 5.1.2 Data Sharing: any prompt or user data sent to third-party AI needs clear disclosure and explicit permission.
- 5.2.1 Intellectual Property: exam-board names are descriptive only; no logos, false official status, or copied branding.

## Current Mitigations

- App Sandbox, hardened runtime, network client, and user-selected read/write file entitlements are explicit.
- `make build-app-store` creates a Release build with `DistributionMode=app-store`.
- App Store mode disables Ollama install/model-pull controls and only detects existing setup.
- Direct mode keeps user-consented Ollama management for website distribution.
- Hosted OpenAI/Anthropic providers require explicit consent before prompts leave the Mac.
- API keys are stored in Keychain with device-only accessibility.
- `PrivacyInfo.xcprivacy` declares no collected data and the required UserDefaults reason.
- Notifications are optional, status-only, and cover start/completion/failure.
- App copy and docs state the app is unofficial and not affiliated with exam boards.
- Coming-soon boards are shown as unavailable and blocked from generation.
- Backend errors are surfaced instead of failing silently.

## Submission Notes

- Provide a working Ollama setup or API key path in App Review notes.
- Explain the direct/App Store difference: website build can manage Ollama; App Store build cannot.
- Keep App Store screenshots focused on ready generators only.
- Privacy policy should say generation is local by default, hosted providers are optional, and no analytics/tracking are included.
- Use `APP_STORE_SUBMISSION_NOTES.md` as the review-note draft.
- If the App Store bundle is submitted later, package the Python backend as a signed, self-contained resource or helper. Do not rely on the developer checkout path.
