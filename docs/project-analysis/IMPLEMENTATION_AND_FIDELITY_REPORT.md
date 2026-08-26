# Implementation and fidelity report

Date: 26 August 2026

## Release outcome

Paper Creator now has one modular generation path for all seven advertised
subject/board families and 18 papers. AI writes new questions inside immutable
paper blueprints; deterministic validators and a separate model-review pass
check marks, assessment objectives, command words, source use, numerical
consistency, originality, mark-scheme traceability, and PDF safety before a
package is published atomically.

The product is deliberately described as an **unofficial practice-paper
generator**. It reproduces measured document conventions but does not ship
official papers, protected logos, copied questions, or a claim of exam-board
endorsement.

## Implemented architecture

- `Resources/generator-registry.json` is the canonical list of generators,
  papers, entry points, required resources, providers, outputs, and evidence
  gates. The app catalogue, backend dispatch, packaging, and matrix tests all
  consume or validate this registry.
- Every generator receives a frozen blueprint. AI may author approved content
  fields but cannot change numbering, sections, marks, AO allocation, or page
  roles.
- Mark-scheme enrichment now distinguishes high-mark calculations from
  evaluative responses: calculations keep method/accuracy points, while
  genuinely extended responses retain levels descriptors and indicative
  content.
- JSON-schema constrained generation, bounded repair/retry, an independent
  review pass, subject-specific deterministic checks, and a typed mark-scheme
  DSL fail closed on invalid work.
- Generation uses a hidden transaction directory. The complete question
  paper, mark scheme, any inserts/supporting files, assessment package, and
  provenance manifest are moved to the selected folder only after all gates
  pass.
- Board-specific composition masters define page boxes, cover hierarchy,
  candidate fields, answer grids, tables, diagrams, mark positions, page-role
  sequences, and footer anchors. Protected branding is replaced with neutral
  Paper Creator branding.
- Swift sources are divided into Application, Components, Domain, Features,
  Navigation, Services, and State. Adding a conforming registry family does not
  require a new backend dispatch branch or matrix entry.

## Model guidance

The shared recommendation registry selects `gemma4:12b` for Macs with at least
16 GB unified memory. It selects `qwen2.5:7b` as the 8 GB compatibility option
and presents a stronger review warning. The app explains download size, the
model's maximum context, Paper Creator's fixed 16K context, and why results may
vary with another model or quantisation. The same record drives the Swift UI,
backend defaults, standalone CLIs, tests, and in-app guide.

## Automated and visual evidence

- Python regression suite: **521 passed, 2 skipped**. The five warnings are
  upstream PyMuPDF SWIG deprecations.
- Complete deterministic layout matrix: **18/18 papers passed**, producing all
  43 declared PDFs plus assessment packages and provenance manifests.
- Strict macOS suite: **20/20 tests passed** with warnings-as-errors and complete
  Swift concurrency checking.
- The standalone helper inside the final Debug app passed the same **18/18**
  paper matrix without importing source-tree modules.
- App Store preflight passed: privacy and entitlement plists are valid, the
  sandboxed Release app builds, app and inherited helper signatures verify,
  hardened runtime is present, and no reference-corpus file is bundled.
- Registered/masked schema-v3 fidelity audit: **68.9% aggregate** across all 36
  primary question-paper and mark-scheme roles.
- The complete live Ollama matrix passed **18/18 papers** with `gemma4:12b`.
  Every question paper, mark scheme, supporting file, assessment package and
  provenance manifest passed its release contracts. Interrupted runs resumed
  from independently validated item checkpoints.
- All six overview sheets were inspected after the final OCR Economics Paper 3
  pagination work. Page roles, response grids, charts, marks, answer-space
  rhythm, and footer geometry align with the chosen official references.
- A live Accounting review exposed an incomplete company-statement source. The
  replacement `IncomeStatementCase` is now the single source of truth for the
  printed case, AI task contract, arithmetic answers and 14-mark scheme; every
  adjustment is supplied and the scheme is kept intact on one page.
- The same adversarial review exposed incomplete partnership retirement data.
  `PartnershipCase` now drives both Question 15 source panels, the authoring
  contracts, goodwill/appropriation arithmetic, answer grids and mark-scheme
  tables. The retirement and two-period appropriation tasks are therefore
  self-contained and independently reproducible.
- Manual inspection of the first passing live package then found a semantic
  relationship the model reviewer had missed. Authoring contracts now support
  forbidden prompt/scheme relationships and mandatory marking content; the
  partnership scheme must cover both periods and cannot write goodwill off
  against the retiring partner.
- The final representative live Accounting Paper 1 run passed in 1,115 seconds
  with `gemma4:12b`: 15 open-ended items were authored and adversarially
  reviewed by Ollama, while six typed calculation items retained their verified
  prompt and mark-scheme contracts. The resulting 36-page question paper and
  26-page mark scheme were rendered and inspected at page level.
- OCR Economics Paper 3 now starts Section B on page 16 and preserves the
  reference-like extract/question/continuation sequence through page 25.
- OCR Computer Science marking tables now use a release-tested 9.5-point body
  scale instead of 7.1 points. This raised live mark-scheme similarity from
  65.4%/66.6% to 67.7%/68.1% without overlapping the densest preview seed.
- Edexcel continuation rules now match the reference's measured solid rule
  darkness and thickness; the old lightly dashed lines disappeared when
  rasterised at normal viewing resolution.
- The largest systematic raster difference is intentional neutral branding.
  Remaining variation is concentrated in independently authored text density,
  question-specific diagrams, and font-metric differences.

The reproducible development evidence is ignored by Git and lives under
`tmp/pdfs/live-full-matrix-final-2026-08-23/`. Its `matrix-report.json`,
`fidelity-report.json`, and `visual-review/` directory contain the detailed
results and side-by-side sheets.

## Live-model evidence boundary

The local `gemma4:12b` benchmark passed the full 18-paper qualification matrix,
not only focused or preview generation. The exact evidence package is under
`tmp/pdfs/live-full-matrix-final-2026-08-23/`; it records the provider, model,
seed, duration, required roles and outcome for each paper. A failed run is
recorded as failed; preview/layout evidence is never relabelled as live-model
success.

Live output still requires human subject review. Software can establish
intended demand, AO allocation, mark distribution, timing, internal
answerability, and scheme consistency. It cannot establish experienced
difficulty or fairness. Those claims require representative student-response
data, trained-marker agreement, item analysis, equating, and subject-expert
sign-off. Accordingly, every `difficultyVerified` gate remains false.

## Publication boundary

The local publication gate has passed: strict Swift compilation, Swift tests,
an App Store-mode Release build, privacy/entitlement validation, nested-helper
code-signature checks, and confirmation that the reference corpus is absent
from the bundle. App Store Connect metadata, Apple Distribution credentials,
notarisation/submission, legal review, and Apple's review decision remain
external release-owner steps.
