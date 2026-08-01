# Implementation and fidelity report

Date: 1 August 2026

## Outcome

This pass converts the main architectural recommendations into working code and
tests, then validates the result across every advertised paper. Every normal
generation path now uses AI to create new questions inside an immutable
board/subject blueprint, fails closed instead of substituting a planning draft,
and publishes auditable assessment and package artifacts only after content and
PDF validation.

The intended product boundary remains important:

> Paper Creator produces independently authored, unofficial practice material.
> Layout similarity is a quality target, not a claim of exam-board authorship,
> endorsement, trademark identity, or empirically equivalent difficulty.

## Implemented changes

| Area | Implemented result |
| --- | --- |
| Generator capabilities | One validated schema-v2 registry now owns entry points, resources, paper IDs, providers, content mode, outputs, and evidence gates. |
| Runtime dispatch | Generation dynamically imports the declared entry point; adding a family no longer requires a hard-coded subject branch. |
| Packaging | The standalone-backend build derives hidden imports, package paths, and syllabus resources from the same registry. |
| Bundle integrity | PyInstaller receives an explicit registry-derived module manifest, and every Xcode build imports all seven dynamic entry points plus their syllabus assets before the helper is copied into the app. |
| AI coverage | All seven advertised families and all 18 papers use the selected local or hosted provider in normal mode; deterministic content exists only for explicitly labelled layout previews. |
| AI quality control | Shared batched generation preserves marks, AO allocations, topics, command words, and numeric invariants, with bounded retries and a separate independent assessment-review call. |
| Originality | Planning-draft, within-paper, and prior-output comparisons reject paraphrases; fingerprints and nearest-history evidence are stored in a renderer-independent assessment package. |
| Protocol | JSONL protocol v2 adds a hello handshake, event IDs, UTC timestamps, job IDs, backend version, and explicit capabilities. |
| Publication safety | Every generation runs in a hidden transaction directory. Files are validated and atomically moved into the selected folder only after the whole package passes. |
| Provenance | Each package includes a JSON manifest with commit, generator/app/backend versions, seed, content mode, provider/model where applicable, evidence gates, input hashes, output hashes, and PDF inspection results. |
| PDF release checks | Output fails closed on missing production metadata, invalid page boxes, annotations, empty pages, missing glyphs, text below 5 pt, off-page text, uncontrolled font substitutions, low-resolution images, or out-of-profile question-paper typography. |
| Assessment schema | Questions now carry syllabus outcomes, AO marks, intended demand, expected time, provenance, source references, scheme mode, and a typed mark-scheme DSL. |
| Mark-scheme validation | Every mark must trace to a structured scheme element; duplicate points and inconsistent multiple-choice keys fail validation. |
| Provider resilience | Hosted calls have bounded retries, capped `Retry-After`, response-size limits, JSON-envelope checks, and redacted/bounded error details. Ollama uses schema-constrained `/api/chat`, deterministic seeds, demand-aware batches, one format repair, and adaptive split retries. |
| Layout composition | AQA/OCR deterministic families share measured cover primitives, controlled table fonts, candidate fields, examiner tables, board-shaped title hierarchy, and deterministic barcodes. |
| Page sequence | OCR Economics Papers 1 and 2 now start Section B on page 9 and Section C on page 13, matching the inspected official page roles. |
| Fidelity tooling | Audit schema v3 registers pages before comparison, masks independently authored text, measures the remaining stable artwork and text-block geometry, and retains per-page scores, worst-page ranking, side-by-side sheets, and HTML review output. |
| Difficulty evidence | A fingerprinted response-calibration tool computes facility, discrimination, timing, reliability, marker agreement, and group screening for one exact form; it cannot promote the gate without minimum samples and independent review. |
| macOS product truth | Every family presents only its supported AI providers; preview mode is explicitly non-release output and difficulty remains pending until exact-form response evidence exists. |
| macOS workflow | The app now uses a native three-column sidebar/task/inspector geometry, grouped forms and tables, standard toolbar actions, immediate Settings, keyboard commands, persistent recent files, Finder drag/reveal, and exact blockers. |
| Repository structure | Swift sources are grouped into Application, Components, Domain, Features, Navigation, Services, and State; backend AI, quality, package, review, PDF, and psychometric responsibilities are separate modules. |

## Full-matrix validation

The reference corpus contains 5,545 PDFs (about 6.2 GB). The post-change matrix
generated all 18 advertised papers:

- seven subject/board families;
- 18 question-paper forms;
- 43 PDFs across question papers, mark schemes, source material, and
  computer-science support documents;
- 18 renderer-independent assessment packages;
- 18 package manifests;
- 81 emitted file events/artifacts across the matrix run;
- zero partial packages or release-validation failures.

The audit compares the 36 primary question-paper and mark-scheme roles. It
profiles page count, word count, printed mark sequence, margins, fonts, physical
page boxes, raster placement, text placement, drawing placement, image
placement, and content envelope.

| Measurement | Legacy baseline | Registered/masked audit |
| --- | ---: | ---: |
| Comparable families | 18 | 18 |
| Primary roles | 36 | 36 |
| Aggregate structural/visual score | 63.9% (schema v2) | 67.4% (schema v3) |

The two figures are not a like-for-like release regression because the audit
schema changed. Schema v3 deliberately excludes variable independently authored
question text from the raster signal after page registration, while retaining
stable boilerplate, rules, boxes, graphics, and text-block geometry. Across the
36 primary documents the stable registered artwork score is typically
0.94–0.96; remaining score loss is concentrated in interior text density,
question-specific diagrams, font metrics, and mark-scheme text geometry.

The reproducible reports are:

- `output/pdf/fidelity-baseline-2026-07-29/fidelity-v2.md`
- `output/pdf/fidelity-improved-2026-07-29/fidelity-v2.md`
- `output/pdf/fidelity-improved-2026-07-29/visual-review/index.html`
- `tmp/final-fidelity/report.md` and `tmp/final-fidelity/report.json` for the
  final schema-v3 development audit.

These output artifacts are intentionally ignored by Git because they contain
hundreds of large raster comparisons.

## Final verification evidence

- Python regression suite: **297 passed, 2 skipped**. The only warnings are
  upstream PyMuPDF SWIG deprecations.
- Complete dry-run generation matrix: **18/18 papers passed**, producing 43
  PDFs, 18 assessment packages, 18 manifests, and two declared support files.
- macOS build: `xcodebuild` completed successfully with code signing disabled
  for local verification.
- Bundled-helper health: all seven generator families and their entry points
  imported from the built `.app` without reaching back into source files.
- Bundled-helper creation: the built app generated and release-validated an AQA
  Accounting Paper 1 preview containing its question paper, mark scheme,
  assessment package, and provenance manifest.

One external evidence boundary remains. A normal-mode Ollama generation item
completed successfully earlier in the review and exposed several prompt/schema
edge cases that are now covered by regression tests. The final six-item live
smoke could not be repeated because the user's local Ollama service was stopped
and this sandbox cannot start or bind that user process. This is an environment
limitation, not evidence that the six-item run passed; normal-mode publication
continues to fail closed when the provider is unavailable or returns invalid
content.

## Manual PDF review

The review did not rely only on the aggregate score. The following evidence was
opened and inspected at readable resolution:

1. all six overview sheets covering the 36 primary roles;
2. AQA Accounting Paper 1 question-paper and mark-scheme pages 1–8, including a
   second comparison after increasing front-matter guidance density;
3. AQA Computer Science Paper 2 question-paper pages 1–8;
4. OCR Economics Paper 1 pages 1–8 and Paper 2 pages 9–16, specifically the
   Section B/Section C transition;
5. Edexcel Economics Paper 1 question-paper pages 1–8 and all three Edexcel
   question-paper and mark-scheme covers;
6. representative AQA and OCR mark-scheme covers;
7. the detailed worst-page lists produced for every role.

Confirmed improvements:

- AQA cover titles now use the measured 27/27/16-point hierarchy instead of the
  previous compressed 15/19/10-point hierarchy.
- AQA candidate forms now include centre/candidate boxes, surname, forenames,
  signature, and declaration rows at reference-like vertical positions.
- AQA Accounting and Business covers now include section/mark examiner tables.
- Shared instruction text uses reference-like 11-point body type and line
  rhythm.
- OCR candidate and instruction regions now occupy the same broad vertical
  bands as the official covers.
- Shared mark-scheme covers now use reference-like hierarchy and month/year
  series labels.
- AQA common mark-scheme guidance now occupies reference-like multi-page bands
  rather than leaving the opening guidance pages visibly sparse. The focused
  Accounting Paper 1 mark-scheme score rose from 61.2% to 62.7% under schema v3
  while preserving the exact 26-page reference length.
- Edexcel question-paper covers remain the closest family: physical boxes,
  header grid, paper code, mark field, crop marks, and footer composition are
  already strongly aligned.

Remaining visible differences:

- protected AQA/OCR/Pearson wordmarks are deliberately replaced by
  `PAPER CREATOR`;
- question wording and source data are independently authored and therefore
  retain different text-block geometry even though those words are excluded
  from the registered raster signal;
- some interior item and mark-scheme pages still have lower information density
  than official papers;
- generic AQA/OCR backgrounds do not reproduce protected decorative artwork;
- several continuation pages match physical grids better than semantic line
  density;
- source pagination can still drift when generated prose is unusually long.

## What code cannot honestly prove

The new schema verifies intended demand, AO allocation, marks, timing, structure,
and scheme traceability. It does **not** prove that a generated paper has the
same experienced difficulty as a live examination.

Those remaining gates require external evidence:

1. subject-expert review and Angoff/bookmark estimates;
2. cognitive labs for interpretation and timing;
3. representative student pilots;
4. facility and discrimination analysis;
5. Rasch/IRT or partial-credit modelling where appropriate;
6. differential item-functioning checks;
7. equating against secure anchor items;
8. trained-marker inter-rater agreement for mark schemes.

Until those steps are completed, the registry correctly leaves every
`difficulty` gate false and the app says “Difficulty not independently
verified.”

## Repository cleanup

The implementation pass also removed the abandoned legacy Xcode project,
duplicated nested Graphify output, an unused agent folder, empty IDE-assistant
metadata, stale Python caches, obsolete package metadata, a broken virtual
environment, and reproducible build products. More than 7 GB of redundant
local data was moved to the macOS Trash so it remains recoverable.

The following large directories are retained intentionally:

- `Reference Corpus/` is the measured source of truth for layout profiling and
  regression comparison;
- `output/` contains user-created papers and audit evidence;
- `.venv/` is the active local test and tooling environment;
- `.idea/` contains user-owned IDE configuration.

## Remaining evidence work

The engineering workflow for exact-form response calibration is implemented,
but no software change can manufacture valid student evidence. Before any
`difficulty` gate can become true, one exact generated form still needs
independent subject review, double marking, a representative pilot, and the
minimum response sample documented in `docs/ASSESSMENT_QUALITY.md`.
