# Paper creator

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

## Recommended Ollama model

The app chooses a recommendation from the Mac's unified-memory capacity. For
the intended paper-quality workflow, use `gemma4:12b` on a Mac with at least
16 GB unified memory. On an 8 GB Mac, `qwen2.5:7b` is the memory-compatible
choice, but its long-form questions and mark schemes need especially careful
human review. Results may vary with any other model or quantisation.

The recommendation, download sizes, explanation, warning, and source links are
owned by `Resources/ollama-model-recommendations.json`; the macOS app, backend
CLI, standalone generator CLIs, tests, and packaged helper consume that record.

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
python3 -m tools.build_supported_layout_masters
```

Only public, official URLs are downloaded. Secure, gated, non-PDF, and disallowed
resources are skipped and listed in `Reference Corpus/download-errors*.json`.
The generated runtime registry contains page boxes and numeric coordinates only.
Full development masters remain ignored with the reference corpus.

To compare generated papers with all supported references:

```bash
python3 -m tools.paper_fidelity_audit \
  --generated-root output/pdf/perfection-audit-2026-07-27 \
  --json output/pdf/perfection-audit-2026-07-27/fidelity-report.json \
  --markdown output/pdf/perfection-audit-2026-07-27/fidelity-report.md
```

To generate every advertised paper through the same backend used by the app,
with resumable per-paper evidence:

```bash
python3 -m tools.live_generation_matrix \
  --output tmp/pdfs/live-matrix \
  --model gemma4:12b \
  --provider ollama \
  --resume
```

The job list is derived from `generator-registry.json`; adding a conforming
subject or exam board automatically adds its papers to this matrix.

## CLI

```bash
python bridge.py generate --subject economics --paper 1 --output ~/Downloads --dry-run
python bridge.py generate --subject economics_aqa --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject economics_ocr --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science --paper 2 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science --paper bank-4.2 --output ~/Downloads --dry-run
python bridge.py generate --subject computer_science_ocr --paper 2 --output ~/Downloads --dry-run
python bridge.py generate --subject business_aqa --paper 3 --output ~/Downloads --dry-run
python bridge.py generate --subject accounting_aqa --paper 2 --output ~/Downloads --dry-run
```

## Structure

- `macOS/`: SwiftUI app, Xcode project, tests, and build scripts.
- `Backend/Core/`: shared AI, assessment, validation, JSONL, and publication core.
- `Resources/economics/edexcel-a/`: Economics generator and local resources.
- `Resources/economics/aqa/`: AQA 7136 Papers 1–3, source insert, and calibration evidence.
- `Resources/economics/ocr/`: OCR H460 Papers 1–3 and aggregate calibration evidence.
- `Resources/computer-science/aqa/`: Computer Science Papers 1–2 plus data
  structures, database, and functional-programming topic banks.
- `Resources/computer-science/ocr/`: OCR H446 Papers 1–2 and aggregate calibration evidence.
- `Resources/business/aqa/`: AQA 7132 Papers 1–3, source insert, and aggregate calibration evidence.
- `Resources/accounting/aqa/`: AQA 7127 Papers 1–2 and aggregate calibration evidence.
- `Resources/ollama-model-recommendations.json`: hardware-aware local-model guidance.
- `tests/`: backend integration tests.

## Architecture and quality analysis

- [`docs/project-analysis/PROJECT_ANALYSIS.md`](docs/project-analysis/PROJECT_ANALYSIS.md):
  end-to-end architecture, current evidence, fidelity limits, and macOS HIG audit.
- [`docs/project-analysis/IMPLEMENTATION_AND_FIDELITY_REPORT.md`](docs/project-analysis/IMPLEMENTATION_AND_FIDELITY_REPORT.md):
  implemented release architecture, full-matrix evidence, visual findings, and
  the remaining human-evidence boundary.
- [`docs/project-analysis/UI_AUDIT.md`](docs/project-analysis/UI_AUDIT.md):
  current native macOS UI evidence and hands-on release checks.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): current runtime and repository
  boundaries.
- [`docs/ASSESSMENT_QUALITY.md`](docs/ASSESSMENT_QUALITY.md): AI, mark-scheme,
  originality, and response-calibration invariants.
- [`docs/HIG_COMPLIANCE.md`](docs/HIG_COMPLIANCE.md): native macOS interaction,
  geometry, and accessibility decisions.
- [`graphify-out/GRAPH_REPORT.md`](graphify-out/GRAPH_REPORT.md): token-efficient
  code communities and architectural hubs.
- [`graphify-out/graph.html`](graphify-out/graph.html): interactive code graph.

Run `graphify query "<question>"` before broad source inspection, and
`graphify update .` after code changes.

## Privacy

Ollama generation runs locally. Hosted providers are optional and require explicit consent before prompts leave the Mac. API keys are stored in Keychain. Generated PDFs are written to the selected output folder.
