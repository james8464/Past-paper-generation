# Past Paper Creator

A tool for generating practice exam papers using LLMs. It supports local generation via Ollama or hosted providers like OpenAI and Anthropic.

The project is split into a native macOS application and a Python-based bridge that handles the generation logic.

## Getting Started

### macOS App (Recommended)
The SwiftUI app is the primary way to use the tool. It handles model management and provides a clean interface for paper generation.

1. Clone the repo.
2. Open `macOS/PastPaperCreator.xcodeproj` in Xcode.
3. Build and run the `PastPaperCreator` scheme.

*Note: You'll need [Ollama](https://ollama.com) installed for local generation, otherwise you can use API keys in the app settings.*

### Python CLI
For terminal usage or headless generation:

1. Setup a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e "Backend/Core[dev]"
   ```
2. Run the bridge script:
   ```bash
   python bridge.py generate --subject economics --paper 1 --output ~/Downloads --dry-run
   ```

## Project Structure

- `macOS/`: SwiftUI application.
- `Backend/Core/`: Python package for generation, rendering, and benchmarking.
- `Resources/`: Subject data and prompt templates.
- `Tests/`: Integration tests for the bridge.
- `bridge.py`: Entry point used by the app and CLI.

## Privacy
By default, everything runs locally using Ollama. If you choose to use a hosted provider, your data is only sent to the provider you select. API keys are stored securely in the macOS Keychain.

## Contributing
Feel free to open a PR if you want to add support for more subjects or improve the UI. New subjects should be added to the `Resources/` directory.
