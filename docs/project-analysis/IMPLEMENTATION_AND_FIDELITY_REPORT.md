# Implementation and fidelity report

Date: 29 July 2026

## Outcome

This pass converts the main architectural recommendations into working code and
tests, then validates the result across every advertised paper. The product is
now more truthful about which generators use AI, fails closed before publishing
bad PDFs, produces an auditable package manifest, and uses shared board-shaped
cover and typography primitives for the deterministic families.

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
| Protocol | JSONL protocol v2 adds a hello handshake, event IDs, UTC timestamps, job IDs, backend version, and explicit capabilities. |
| Publication safety | Every generation runs in a hidden transaction directory. Files are validated and atomically moved into the selected folder only after the whole package passes. |
| Provenance | Each package includes a JSON manifest with commit, generator/app/backend versions, seed, content mode, provider/model where applicable, evidence gates, input hashes, output hashes, and PDF inspection results. |
| PDF release checks | Output fails closed on missing title metadata, invalid page boxes, annotations, empty pages, uncontrolled font substitutions, or images below 150 DPI. |
| Assessment schema | Questions now carry syllabus outcomes, AO marks, intended demand, expected time, provenance, source references, scheme mode, and a typed mark-scheme DSL. |
| Mark-scheme validation | Every mark must trace to a structured scheme element; duplicate points and inconsistent multiple-choice keys fail validation. |
| Provider resilience | Hosted calls have bounded retries, capped `Retry-After`, response-size limits, JSON-envelope checks, and redacted/bounded error details. |
| Layout composition | AQA/OCR deterministic families share measured cover primitives, controlled table fonts, candidate fields, examiner tables, board-shaped title hierarchy, and deterministic barcodes. |
| Page sequence | OCR Economics Papers 1 and 2 now start Section B on page 9 and Section C on page 13, matching the inspected official page roles. |
| Fidelity tooling | Audit schema v2 adds per-page scores, compact reports, worst-page ranking, side-by-side reference/generated/difference sheets, overview sheets, and HTML review output. |
| macOS product truth | Deterministic families no longer require or pretend to use an AI provider. AI families expose only supported providers and explain exact blockers. |
| macOS workflow | Settings save immediately, `⌘N` starts a new paper, `⌘↩` creates, `⌘.` cancels, output selection stays in the task, recent files persist, and missing files can be removed from history. |

## Full-matrix validation

The reference corpus contains 5,545 PDFs (about 6.2 GB). The post-change matrix
generated all 18 advertised papers:

- seven subject/board families;
- 18 question-paper forms;
- 43 PDFs across question papers, mark schemes, source material, and
  computer-science support documents;
- 18 package manifests;
- zero partial packages or release-validation failures.

The audit compares the 36 primary question-paper and mark-scheme roles. It
profiles page count, word count, printed mark sequence, margins, fonts, physical
page boxes, raster placement, text placement, drawing placement, image
placement, and content envelope.

| Measurement | Baseline | Post-change |
| --- | ---: | ---: |
| Comparable families | 18 | 18 |
| Primary roles | 36 | 36 |
| Aggregate structural/visual score | 63.9% | 64.3% |

The aggregate gain is modest because variable independently authored question
text is deliberately not pixel-identical to copyrighted reference text and the
current metric does not mask those regions. The human-visible improvement to
shared covers is much larger than the aggregate delta: typography, candidate
fields, examiner tables, title hierarchy, section spacing, mark-scheme covers,
and page roles now occupy substantially closer coordinates and scale.

The reproducible reports are:

- `output/pdf/fidelity-baseline-2026-07-29/fidelity-v2.md`
- `output/pdf/fidelity-improved-2026-07-29/fidelity-v2.md`
- `output/pdf/fidelity-improved-2026-07-29/visual-review/index.html`

These output artifacts are intentionally ignored by Git because they contain
hundreds of large raster comparisons.

## Manual PDF review

The review did not rely only on the aggregate score. The following evidence was
opened and inspected at readable resolution:

1. all six overview sheets covering the 36 primary roles;
2. AQA Accounting Paper 1 pages 1–8 before and after the shared-cover change;
3. OCR Economics Paper 1 pages 1–8 after the shared-cover change;
4. OCR Economics Paper 2 pages 9–16, specifically the Section B/Section C
   transition;
5. all three Edexcel Economics question-paper and mark-scheme covers;
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
- Edexcel question-paper covers remain the closest family: physical boxes,
  header grid, paper code, mark field, crop marks, and footer composition are
  already strongly aligned.

Remaining visible differences:

- protected AQA/OCR/Pearson wordmarks are deliberately replaced by
  `PAPER CREATOR`;
- question wording and source data are independently authored and therefore
  create large red difference regions;
- some page interiors still have lower information density than official
  papers, especially dense mark-scheme guidance pages;
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

## Highest-value next engineering work

1. Add variable-content masks and page registration to the visual audit so
   question wording does not dominate layout scores.
2. Model full composition masters for continuation/source/blank/end pages,
   rather than only physical page boxes and shared cover primitives.
3. Add executable checking for calculations, accounting statements, algorithms,
   and data tables.
4. Store reviewed items in a versioned bank with semantic-duplicate and exposure
   controls.
5. Build the external pilot/calibration workflow before changing the difficulty
   evidence gate.
