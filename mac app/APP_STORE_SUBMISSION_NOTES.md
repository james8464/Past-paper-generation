# App Store Submission Notes

Use this as the App Review notes source of truth before submitting.

## Reviewer Access

- No account is required.
- Ready generators: Economics Edexcel A and Computer Science AQA.
- Coming-soon subjects and boards are visible but blocked from generation.
- If App Review cannot use Ollama or a hosted provider, enable **Settings > Output > Use built-in drafts** to test the generation flow without an AI request.
- Generated PDFs are written only to the user-selected output folder.

## AI And Privacy

- Ollama keeps generation local.
- OpenAI and Anthropic are optional. The app asks for explicit consent before sending prompts, syllabus context, or draft paper content to a hosted provider.
- API keys are stored in Keychain with device-only accessibility.
- No analytics, tracking, advertising SDKs, accounts, or telemetry are included.
- Notifications are optional and status-only.

## App Store Build Limits

- `make build-app-store` sets `DistributionMode=app-store`.
- App Store mode disables Ollama installation and model pulls.
- App Store mode must not download, install, or execute extra code after review.
- The bundle must be self-contained before submission. If the Python backend is packaged later, it must be included in the signed app bundle or as a signed helper tool.

## Metadata Guardrails

- Do not use Pearson, Edexcel, AQA, or other exam-board logos.
- Do not imply official endorsement.
- Screenshots should show only ready generators.
- The privacy policy URL must stay live and match App Store Connect privacy answers.
- The support URL must stay live.

## Review Checklist

- Build and launch the App Store configuration.
- Run `make preflight-app-store`.
- Generate at least one Economics paper and one Computer Science paper.
- Confirm no installer or model-pull UI is available in App Store mode.
- Confirm hosted-AI consent appears before selecting OpenAI or Anthropic.
- Confirm notification permission is optional.
- Confirm sandboxed output goes to the selected folder.
