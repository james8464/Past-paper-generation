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
make backend-env
make test
make preflight-app-store
```

## Development Reference Corpus

Official A-level PDFs are development references only. They are stored under
`Reference Corpus/`, ignored by Git, and excluded from the app bundle. The profiler
extracts numeric layout data only; it does not copy paper text into shipped resources.

```bash
python3 tools/reference_corpus.py discover-aqa
python3 tools/reference_corpus.py discover-ocr
python3 tools/reference_corpus.py discover-pearson
python3 tools/reference_corpus.py download --workers 6
python3 tools/reference_corpus.py profile --kind question-papers --workers 8
python3 tools/reference_corpus.py summarize
```

Only public, official URLs are downloaded. Secure, gated, non-PDF, and disallowed
resources are skipped and listed in `Reference Corpus/download-errors*.json`.

## CLI

```bash
python bridge.py generate --subject economics --paper 1 --output ~/Downloads --dry-run
python bridge.py generate --subject economics_aqa --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject economics_ocr --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science --paper 2 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science_ocr --paper 2 --output ~/Downloads --dry-run
python bridge.py generate --subject business_aqa --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject accounting_aqa --paper 2 --output ~/Downloads --dry-run
```

## Structure

- `macOS/`: SwiftUI app, Xcode project, tests, and build scripts.
- `Backend/Core/`: JSONL bridge used by the app and CLI.
- `Resources/economics/edexcel-a/`: Economics generator and local resources.
- `Resources/economics/aqa/`: AQA 7136 Papers 1–3, source insert, and calibration evidence.
- `Resources/economics/ocr/`: OCR H460 Papers 1–3 and aggregate calibration evidence.
- `Resources/computer-science/aqa/`: Computer Science generator and local resources.
- `Resources/computer-science/ocr/`: OCR H446 Papers 1–2 and aggregate calibration evidence.
- `Resources/business/aqa/`: AQA 7132 Papers 1–3, source insert, and aggregate calibration evidence.
- `Resources/accounting/aqa/`: AQA 7127 Papers 1–2 and aggregate calibration evidence.
- `tests/`: backend integration tests.

## Privacy

Ollama generation runs locally. Hosted providers are optional and require explicit consent before prompts leave the Mac. API keys are stored in Keychain. Generated PDFs are written to the selected output folder.
