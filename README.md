# ExamForge

Native macOS app and Python backend for generating unofficial A-level practice papers.

## Run

```bash
cd macOS
make build-and-run
```

If Xcode command-line tools are selected instead of Xcode:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## Build Checks

```bash
cd macOS
make test
make preflight-app-store
```

## CLI

```bash
python bridge.py generate --subject economics --paper 1 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science --paper 2 --output ~/Downloads --dry-run
```

## Structure

- `macOS/`: SwiftUI app, Xcode project, tests, and build scripts.
- `Backend/Core/`: JSONL bridge used by the app and CLI.
- `Resources/economics/edexcel-a/`: Economics generator and local resources.
- `Resources/computer-science/aqa/`: Computer Science generator and local resources.
- `tests/`: backend integration tests.

## Privacy

Ollama generation runs locally. Hosted providers are optional and require explicit consent before prompts leave the Mac. API keys are stored in Keychain. Generated PDFs are written to the selected output folder.
