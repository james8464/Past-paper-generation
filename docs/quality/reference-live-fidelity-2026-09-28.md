# Reference support, live qualification and PDF repairs

## Qualification boundary

This work separates three claims: a generated task has comparable source
evidence; its actual live AI output passes the generation/review pipeline; and
its PDF preserves the content in a measured board-style layout. None implies
empirical difficulty equivalence, examiner approval, or pixel identity.

Topic-bank support is documented in
[topic-reference-support-2026-09-28.md](topic-reference-support-2026-09-28.md).
Every generated item now has reviewed same-topic/task-family evidence. The
whole-topic and empirical qualification flags remain false.

## Renderer repairs

- AQA cover coordinates no longer inherit unintended frame padding. The
  on-screen CS Paper 1 cover omits handwritten candidate/signature boxes and
  paper-only instructions; Paper 2 retains its candidate form.
- AQA cover titles embed licensed Open Sans Medium/SemiBold, with measured
  per-paper sizes and casing rather than substituting body-font bold. The
  official-font provenance and deterministic Medium build are recorded in
  `Backend/Core/fonts/opensans/README.md`; body fonts are unchanged. The written
  CS cover barcode caption sits below the bars rather than crossing them.
- CS Paper 1 body pages also use the measured on-screen header rule, without
  written-paper borders, examiner boxes or footer barcodes. Blank leaves retain
  one visible footer, and turn-over instructions occur only on non-blank rectos.
- AQA marking covers restore the heavy title rule and thin session rule, with
  source baselines rather than mistaken text-bounding-box coordinates. Economics
  booklets retain their separate title-case cover grid, footer and answer-booklet
  instructions.
- OCR covers use the OCR candidate panel, not the AQA signature form. Measured
  subject/code/materials/identity anchors replace the previous generic cover.
  The actual paper's calculator restriction is printed.
- AQA additional pages use black ruling and measured heading typography. Blank
  end-page diagonals retain their source-shaped bounds even with a legal notice.
- Accounting's first MCQ page now includes the response/correction instruction
  panel that was previously missing, with source-shaped rounded corners.
- OCR answer rulings use the source's dark 11-point dot glyphs and 26-point pitch;
  faint vector dashes no longer substitute for them. Actual end-of-question
  pages do not print a misleading turn-over instruction. See
  [OCR measurements](ocr-question-chrome-2026-09-28.md).
- OCR Economics schemes use 11-point body text and the measured four-column
  grid. The renderer no longer cycles guidance to reach a fixed page count or
  drops credit to fit that count. Tables continue naturally, with visible
  question identifiers. Levels descriptors span the content columns.

OCR seed 123 schemes contain 39, 38 and 31 pages. The content gate verifies all
301, 297 and 202 required credit statements respectively. These page counts are
not claims of matching the length of a different real paper. A 120-statement
stress case verifies natural overflow. Mixed-orientation conformance preserves
the two portrait opening pages, landscape guidance/body and portrait colophon.

The gate excludes question prompts and tariff-only cells from answer evidence,
requires numeric alternatives under their correct labels, rejects missing or
wrong-question credit, duplicate pages and unassessed padding, and checks the
assessment package identity. It is a content-preservation check, not an
independent semantic examiner.
Distinct Accept/Allow/Do not accept/Ignore labels are preserved even when their
wording is identical; deduplication cannot erase a different marking rule.

Original branding, question wording, session date and publisher/legal pages
intentionally differ. Representative Edexcel scheme geometry already matched
the measured body font/table anchors; no arbitrary change was made there.
The stored dominant-font profile is body-weighted and does not list Open Sans.
Its family-overlap check therefore records 50% for Arial plus Open Sans, not
100%. Genuine Open Sans static/weight names now normalize to one Open Sans
family (never Arial); thresholds are unchanged, and unrelated/condensed fonts
remain distinct. Cover-specific PDF tests verify the separately measured faces.
Deterministic OCR preview blueprints still contain some generic AO-labelled
credit. Preserving that assessed content is not evidence of editorial quality;
live item review remains a separate requirement.

## Live matrix integrity

The first live Accounting Paper 1 attempt exposed a genuine source-scope defect
at question 14.2. The independent solver received a generic option extract
containing staff turnover of 19%, while that page's specialist renderer printed
the company-statement case instead. Writer/reviewer context therefore disagreed
with the solver's input. The repair shares the candidate-visible source
projection across writing, review, blind solving and difficulty review. Mere
authoring metadata must not hide a relevant case, and explicit source records
cannot be silently replaced by a same-ID parent extract. The review version is
advanced so old reviewed checkpoints cannot bypass the new boundary. The
numeric-profit/AO2 checks remain unchanged; only a successful fresh live run
can demonstrate the repaired route passes.
Independent rereview also verified plural extract/chart references against
actual Economics blueprints and fail-closed handling of conflicting visible
source identifiers. The source-scope focused suite passed 204 tests.

The runner streams progress to disk and records per-backend peak resident
memory. That memory figure explicitly excludes the separate model server/GPU.
Timeout, interruption and termination clean up the owned process group.

Resume requires the same route, seed, preview/live mode, provider, endpoint
identity, model digest, runtime source and executable, plus hashes of every
required artifact and event log. Unknown Ollama model identity cannot qualify.
Starting a retry invalidates previous success before logs are replaced. The
aggregate rechecks earlier successes against final source/model/artifact state
and records whether all advertised routes have completed.

The full live run uses `gemma4:12b`, base seed `26092840`, all 21 advertised
routes and no preview mode. Local progress is retained under
`tmp/pdfs/qualification-20260928-live/`; copyrighted references, generated
papers, model output and contact sheets remain outside Git. Its final result
must be read from `matrix-report.json`, not inferred from preview success or
individual accepted items. A source-changing development run is not final-code
qualification; the stable runner must rerun/revalidate it.

## Verification record

- Baseline: 1,958 backend tests passed, 2 skipped.
- Independent review exposed unsafe resume, interrupted stale evidence,
  model/source drift, subprocess cleanup, prompt-as-answer and labelled numeric
  alternative cases. Each was reproduced and corrected with regression tests.
- Native macOS tests: 61 passed, no failures, including the final-source refresh.
- Renderer integration: 2,040 backend tests passed, 2 skipped; all 21 preview
  routes passed; local release build and signature/sandbox preflight passed.
  These precede the later source-scope and cover-font repairs and do not certify
  their final integration.
- Final source integration: 2,078 backend tests passed, 2 skipped (five existing
  SWIG deprecation warnings); all 21 preview routes passed. Local release build,
  signature/sandbox preflight, lint and release-compliance checks passed.
- The stable full live matrix restarted with the repaired source context and
  cover fonts. Previous failed/interrupted attempt records were preserved.
  Final live results and their manual PDF comparison remain pending; no complete
  qualification claim yet.

Contact sheets and measured renderer findings are retained locally in
`tmp/pdfs/renderer-20260928/`. The final preview comparison uses
`tmp/pdfs/qualification-20260928-preview-final/`. Comparisons of newly authored content
must not be presented as a literal percentage of question correctness.

Graphify's structural refresh indexes 6,827 nodes and 19,155 edges. Its AST-only
pass reports 37 data/configuration sources with no extracted nodes; these are
not represented as complete semantic coverage. Large-graph HTML uses the
271-community overview. The repository inventory classifies 504 tracked files
with no forbidden or unclassified artifacts.

## 6 October French v12 source-fidelity checkpoint

The earlier UK matrix and its failures are retained as historical evidence; its
identity does not qualify the changed shared source. The French graph/tree slice
now uses a versioned finite French catalogue, with selection-only authoring,
hash-bound replay and extracted-PDF comparison. This narrows one observed
false-positive authoring class without claiming general NSI correctness.
Deterministic fixtures passed; no v12 live complete paper has yet been accepted.
The [page-level comparison](french-nsi-v12-pdf-verification-2026-10-06.md)
keeps the official 2026 reference separate from the non-official fixture.

Do not launch the final shared-source UK-plus-French live matrix while this
branch is changing. After protected integration and source freeze, pin the
implementation, model digests, reference index and artifact hashes, preserve
every failed attempt, and inspect every resulting PDF. Human teacher review,
learner calibration and accessibility are independent gates; issues #4 and #8
remain open until actual qualification.
