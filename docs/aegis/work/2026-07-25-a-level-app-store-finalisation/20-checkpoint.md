# Todo Checkpoint Draft

## Current todo

1. Create durable long-task records. **Complete.**
2. Generate a canonical 105-family coverage/readiness matrix. **Complete.**
3. Validate catalog claims against generator artifacts and evidence. **Complete.**
4. Make the app consume canonical readiness data. **Complete.**
5. Implement remaining families as complete vertical slices. **Active: 5/105.**
6. Run full matrix and App Store release gates.

## Completed

- Official public AQA/OCR/Pearson development corpus discovered and downloaded.
- Numeric layout profiles produced for 105 board/subject families.
- Reference corpus ignored by Git and excluded from release bundles.
- Economics Edexcel A Papers 1–3 generation and pagination refined.
- AQA Computer Science Paper 2 generation implemented.
- Native app runtime, sandbox bookmarks, privacy manifest, standalone backend,
  arm64 packaging, and App Store build preflight repaired.
- Current Python, Swift, bundled-helper, and release-build checks passed.
- Durable intent/checkpoint/evidence/drift trail created.
- `generator-registry.json` now defines implementations and per-paper gates.
- `coverage-matrix.json` deterministically covers all 105 profiled families.
- Coverage validation rejects missing resources, unknown families, missing
  gates, duplicate declarations, and false verified states.
- Swift catalog availability and paper lists now load from the bundled canonical
  generator registry.
- The catalog contains display taxonomy only; it no longer contains duplicated
  ready/status declarations.
- Built-app resource inspection confirmed both canonical JSON files and no
  official PDFs.
- AQA Computer Science Paper 1 now generates a coordinated on-screen package:
  question paper, preliminary material, fillable Electronic Answer Document,
  Python 3 Skeleton Program, unique data file, and mark scheme.
- AQA Computer Science now has both declared papers implemented.
- Unimplemented board controls are hidden from the shipping UI.
- Shared declarative exam contracts now validate selection rules, candidate
  marks, syllabus scope, generated-question shape, and uniqueness.
- AQA Economics 7136 Papers 1–3 are implemented and selectable.
- AQA Economics Papers 1–2 implement two 40-mark data-response choices and
  three 40-mark essay choices; Paper 3 implements 30 MCQs and a 50-mark case.
- All three AQA Economics question papers render to the eight-page standard
  Paper 1/2 layout; Paper 3 renders to the 40-page in-paper response format and
  adds a separate eight-page source insert.
- Frozen-backend relative output no longer resolves inside the signed app
  bundle; a regression test protects the code-signature seal.
- AQA Economics difficulty calibration derives aggregate bands from 18 local
  official references without retaining text or corpus paths.
- The automated structural-demand gate passes across 20 seeds per paper:
  marks, pages, syllabus coverage, uniqueness, MCQ mix and insert word demand.
- Difficulty remains unverified pending subject review, student trials and
  psychometric equivalence evidence.
- OCR Economics H460 Papers 1–3 are implemented and selectable.
- OCR current-paper structures are exact: Papers 1–2 are 80 marks/2 hours with
  30-mark data response and two 25-mark essay sections; Paper 3 is 30 MCQs plus
  a 50-mark extended data response.
- OCR question papers render to 20, 20 and 28 pages with independently written
  fictional sources, figures, syllabus-linked questions and level-based mark
  schemes.
- OCR aggregate calibration covers 12 official question-paper structures and
  20 generated seeds per paper without retaining source text or local paths.
- OCR Computer Science H446 Papers 1–2 are implemented and selectable.
- H446/01 and H446/02 reproduce the current 41- and 40-subquestion mark
  sequences, 140 marks, 2h30 duration, 28/32-page geometry and Paper 2
  Section A/Section B scenario split.
- OCR Computer Science uses H446-specific processor, software, data exchange,
  representation, Boolean, legal, computational-thinking, programming,
  algorithm and data-structure domains.
- Generated demand includes pseudocode, traces, conversions, comparison tables,
  diagrams and extended responses with level descriptors.

## Completed slices

Slice Card:

- Goal: create an enforceable, machine-readable coverage/readiness matrix.
- Parent plan/spec: `10-intent.md`.
- Files: `Resources/`, `tools/`, `tests/`, this checkpoint.
- Boundary: derived structural metadata only; no paper text; no readiness
  promotion without implemented artifacts.
- Verification: focused pytest, JSON validation, then full Python suite.
- Stop: achieved; matrix exactly covers 105 families and rejects false claims.
Slice Card:

- Goal: make advertised app support derive from the canonical registry.
- Parent plan/spec: `10-intent.md`.
- Files: `Resources/catalog.json`, Swift catalog models/tests, build resources.
- Boundary: preserve the two currently usable generator routes and paper lists.
- Verification: Swift tests, backend CLI tests, resource-bundle inspection.
- Stop: achieved; no independently maintained ready-generator list remains.

## Completed vertical slice

Slice Card:

- Goal: complete the AQA Computer Science family by implementing Paper 1.
- Parent plan/spec: `10-intent.md`.
- Files: Computer Science generator/data/tests, backend dispatch, registry,
  catalog-facing tests.
- Boundary: independently authored content and neutral practice branding; no
  official question text, logos, or paper assets.
- Verification: blueprint/marks tests, multi-seed uniqueness, PDF generation,
  bundled-helper runtime, Swift paper list.
- Stop: achieved; Papers 1 and 2 are selectable and valid, and the family moved
  from partial to implemented. Difficulty calibration remains unverified.

## Completed calibration slice

Slice Card:

- Goal: calibrate objective difficulty gates from generated-paper measurements
  and derived reference metadata.
- Parent plan/spec: `10-intent.md`.
- Files: calibration tooling, per-family fixtures, registry evidence, tests.
- Boundary: difficulty remains false until repeatable measurements exist; do
  not infer difficulty from marks, page count, or prose claims.
- Verification: multi-seed batches, command-word/reading/quantitative demand
  metrics, reference bands, deterministic reports, regression thresholds.
- Stop: achieved for automated structural demand; the overall difficulty gate
  correctly remains false because the human/psychometric sub-gates are absent.

## Completed OCR Economics vertical slice

Slice Card:

- Goal: implement OCR Economics H460 as a complete family using the shared
  contract and its own syllabus, rules, renderer and calibration path.
- Parent plan/spec: `10-intent.md`.
- Files: selected resource pack, backend route, registry, app tests.
- Boundary: complete every declared paper before advertising; no generic
  fallback and no protected paper assets.
- Verification: official public structure, syllabus map, invariants,
  multi-seed uniqueness, PDF visual/runtime/release checks.
- Stop: achieved; all three OCR H460 papers pass backend, visual, frozen-helper,
  sandboxed Release build and code-signature checks. Difficulty stays false
  pending external validation.

## Completed OCR Computer Science vertical slice

Slice Card:

- Goal: implement OCR Computer Science H446 as a complete family.
- Parent plan/spec: `10-intent.md`.
- Boundary: complete every declared paper before advertising; independently
  authored content only; no generic fallback or protected paper assets.
- Verification: structure/syllabus evidence, invariants, multi-seed uniqueness,
  PDF visual/runtime/release checks.
- Stop: achieved; both papers pass exact-sequence calibration, multi-seed
  uniqueness, PDF bounds/visual checks, frozen helper, sandboxed Release build
  and code-signature verification.

## Completed AQA Business vertical slice

Slice Card:

- Goal: implement AQA Business 7132 as a complete family.
- Parent plan/spec: `10-intent.md`.
- Boundary: complete every declared paper before advertising; independently
  authored content only; no generic fallback or protected paper assets.
- Verification: structure/syllabus evidence, invariants, multi-seed uniqueness,
  PDF visual/runtime/release checks.
- Stop: achieved; all three papers pass current-sequence calibration, PDF
  bounds/visual checks, frozen-helper generation, sandboxed Release build and
  code-signature verification.

## Completed AQA Accounting vertical slice

Slice Card:

- Goal: implement AQA Accounting 7127 as a complete family.
- Parent plan/spec: `10-intent.md`.
- Boundary: complete every declared paper before advertising; independently
  authored content only; no generic fallback or protected paper assets.
- Verification: structure/syllabus evidence, invariants, multi-seed uniqueness,
  PDF visual/runtime/release checks.
- Stop: achieved; both papers pass current-sequence calibration, PDF
  bounds/visual checks, frozen-helper generation, sandboxed Release build and
  code-signature verification.

## Active slice

Slice Card:

- Goal: implement AQA Biology 7402 Papers 1–3 as the next complete family.
- Parent plan/spec: `10-intent.md`.
- Boundary: complete every declared paper before advertising; independently
  authored content only; no generic fallback or protected paper assets.
- Verification: structure/syllabus evidence, invariants, multi-seed uniqueness,
  PDF visual/runtime/release checks.
- Current evidence: latest Paper 1/2 are 36 pages; Paper 3 is 40 pages and
  ends with two 25-mark essays. Exact latest printed mark sequences and the
  eight specification domains have been extracted.
- Stop: all three papers pass structure, calibration, visual, runtime and
  release gates and are selectable.

## Evidence refs

- `Resources/layout-profiles.json`
- `Resources/catalog.json`
- `Reference Corpus/manifest.json` (development-only)
- `90-evidence.md`

## Blocked on

- WJEC automated access disallowed by robots.
- CCEA archive protected by Cloudflare.
- Cambridge International corpus/licensing not established.
- Apple Distribution identity and App Store Connect assets are external.

These do not block work on the current AQA/OCR/Pearson matrix.

## Resume state hint

Read `10-intent.md`, this file, `90-evidence.md`, and `95-drift.md`; compare
`git status --short`; then run the next pending verification command. Do not
infer support from `layout-profiles.json`: profiled is not implemented.

## Next

Select the next AQA/OCR/Pearson family with complete public structure metadata
and implement its entire paper inventory.
