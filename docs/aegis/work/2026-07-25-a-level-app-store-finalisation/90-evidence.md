# Evidence Bundle Draft

## Fixed-layout finalisation pass — 27 July 2026

- Coordinate-preserving layout masters were built for all 18 supported papers
  and their mark schemes. The shipped registry contains numeric page boxes only;
  reference text, artwork, logos and PDFs remain excluded.
- Every supported question paper matches its current reference page count and
  page-box sequence.
- OCR mark schemes preserve the two-page portrait introduction followed by
  landscape tables.
- OCR H446/01 now has the current ten top-level questions. H446/01 and H446/02
  match every current top-level question start page; their generated mark
  schemes match the current 36/27-page counts.
- Edexcel Papers 2 and 3 render to 36 pages. Paper 3 ends with three labelled
  blank pages.
- AQA Accounting, Business and Economics mark-scheme question content starts
  on the same front-matter page as the current reference families.
- Full Python suite: 239 passed, 2 skipped.
- Swift suite: 11 passed.
- Sandboxed App Store Release preflight passed with warnings-as-errors and
  strict concurrency.
- Release bundle: 120 MB; sandbox, user-selected read/write and outbound network
  entitlements only.
- The Release bundle contains the 610 KB numeric layout registry and no reference
  corpus or official paper.
- The packaged Release backend generated all 18 variants successfully: 18/18
  completion events and 43 PDFs.
- The strict 18-paper structural/visual audit is retained under ignored
  development output. Its aggregate score is 66.1%; exact visual identity is not
  claimed. Independent subject review, psychometric equivalence and App Store
  upload review remain outstanding.

## Retained verified evidence

- Python suite: 206 passed, 2 skipped.
- Swift tests: 11 passed.
- App Store preflight:
  `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer make preflight-app-store`
  succeeded.
- Release app:
  `macOS/build/DerivedData/CODEX/Build/Products/Release/PaperCreator.app`.
- Local code-signature verification passed.
- App and bundled helper are arm64.
- Bundled helper generated Economics and Computer Science packages in dry-run.
- Release bundle contains no `Reference Corpus/` path and no official reference
  PDFs.
- Development corpus manifest: 7,716 documents.
- Numeric profiles: 2,629 question-paper PDFs aggregated into 105
  board/subject families.

## Coverage slice evidence

- `python3 tools/coverage_matrix.py --write`: passed.
- `python3 tools/coverage_matrix.py --check`: passed.
- `pytest -q tests/test_coverage_matrix.py`: 9 passed.
- Matrix summary: 105 families, 3 boards, 103 reference-profiled, 1 partial,
  1 implemented, 0 verified.
- `git diff --check`: passed.

## Current slice evidence

- `pytest -q ../tests/test_coverage_matrix.py`: 10 passed.
- XcodeGen project regeneration: passed.
- Swift test suite: 11 passed.
- Bundled `catalog.json` byte comparison: passed.
- Bundled `generator-registry.json` byte comparison: passed.
- Built-app official-PDF exclusion check: passed.
- `git diff --check`: passed.

## Paper 1 slice evidence

- Focused Paper 1/registry/backend tests: 24 passed before fillable-form upgrade.
- Final focused Paper 1 tests: 7 passed.
- Full Python suite: 179 passed, 2 skipped.
- Paper 1 invariant: 12 questions, 100 marks, 2h30, on-screen delivery.
- Multi-seed scenario, question, skeleton, data, and PDF differences: passed.
- Skeleton Python compilation and generated data filename match: passed.
- PDF pages: question paper 13; preliminary material 2; answer document 13;
  mark scheme 17.
- Fillable PDF: 12 canonical fields, 12 widgets, 12 appearance streams,
  multiline flags present.
- PNG inspection: cover, first/last questions, preliminary pages, answer
  document, mark-scheme cover/table; no clipping or overlap.
- Swift tests after catalog registry integration: 11 passed.
- App Store release preflight: passed with sandboxing, strict concurrency and
  warnings-as-errors.
- Release helper Paper 1 generation: six roles passed; Skeleton Program compiled;
  fillable document contained 12 fields.
- Release code-signature verification: passed.
- Release app and helper architectures: arm64.
- Release bundle official-PDF and `Reference Corpus` exclusion: passed.

## Evidence limits

- Existing tests prove only the currently implemented generator paths.
- Numeric layout profiles do not prove syllabus or difficulty fidelity.
- Local signing does not prove App Store upload acceptance.
- No remaining family may be described as ready without additional per-paper
  evidence.

## Shared blueprint and AQA Economics slice

- Shared rule/generated-paper validators: 4 focused tests passed.
- AQA Economics adapter: 5 focused tests passed.
- Full Python suite: 194 passed, 2 skipped, 5 third-party deprecation warnings.
- AQA 7136 Paper 1/2 candidate structure: 2 contexts, answer 1, 40 marks each;
  3 essays, answer 1, 40 marks each.
- AQA 7136 Paper 3 candidate structure: 30 one-mark MCQs plus one 50-mark case
  split 10/15/25.
- All three paper rules total exactly 80 candidate marks in 120 minutes.
- Same seed is deterministic; different seeds change questions, scenarios,
  figures, extracts, charts, and mark-scheme application.
- Papers 1–2 render to eight A4 pages. Paper 3 renders to 40 A4 pages with
  in-paper response space and a separate eight-page source insert.
- Sampled covers, context pages, charts, questions, MCQs, case-study answer
  pages, source insert and last pages were visually inspected with no clipping
  or overlap.
- Backend bridge generated Papers 1–3 with two output roles each.
- Swift catalog tests: 11 passed; AQA Economics exposes Papers 1–3.
- App Store preflight passed after XcodeGen regeneration with sandboxing,
  strict concurrency, and warnings-as-errors.
- Frozen release helper generated Papers 1–3; Paper 3 produced question paper,
  source insert and mark scheme roles with 40/8-page geometry.
- A frozen-helper path regression was found and fixed: relative outputs now
  remain under the caller's working directory rather than the signed bundle.
- Final release code-signature verification passed after helper generation.
- App and helper are arm64; official-paper/reference-corpus bundle exclusion
  and bundled canonical JSON comparisons passed.
- Matrix summary: 105 families, 3 advertised, 102 reference-profiled,
  3 implemented, 0 partial, 0 verified.

## Difficulty calibration evidence

- `python3 tools/difficulty_calibration.py --write`: passed.
- `python3 tools/difficulty_calibration.py --check`: passed.
- Aggregate reference set: 18 AQA Economics question papers/inserts; only
  counts, ranges, fingerprints and mark sequences retained.
- Reference paper page bands: Paper 1 = 8; Paper 2 = 8; Paper 3 = 36–44,
  median 40.
- Reference Paper 3 insert band: 4–8 pages; 993–1276 words.
- Generated geometry: 8, 8 and 40 pages; Paper 3 insert = 8 pages/1107 words.
- Printed marks match every reference: Papers 1/2 use
  `2,4,9,25` twice and `15,25` three times; Paper 3 uses 30 one-mark items and
  `10,15,25`.
- Twenty seeds per paper produced 20 unique prompt fingerprints and complete
  allowed-topic coverage.
- Paper 3 MCQ demand mix: 24 conceptual, 6 quantitative.
- Automated structural-demand gate: passed.
- Independent subject review, student trial, psychometric equivalence and final
  difficulty gates: false.

## OCR Economics H460 slice

- Current paper structures derived from 12 official OCR question papers:
  four each for H460/01, H460/02 and H460/03; correction notices excluded.
- H460/01 current Section A marks: `2,4,2,2,8,12`; Sections B/C each offer two
  25-mark essays, answer one.
- H460/02 current Section A marks: `2,1,3,4,8,12`; Sections B/C each offer two
  25-mark essays, answer one.
- H460/03: 30 one-mark MCQs followed by `2,3,15,3,2,15,2,8`.
- Generated question-paper geometry: 20, 20 and 28 pages. Generated mark-scheme
  geometry: 5, 5 and 7 pages.
- Twenty seeds per paper produced unique paper and stimulus fingerprints,
  complete allowed-topic coverage and exact current printed mark sequences.
- Paper 3 demand mix: 24 conceptual and 6 quantitative MCQs; every choice set
  contains four distinct answers.
- PDF bounds scan found no text outside any page; sampled covers, dense extracts,
  figures, MCQs, essay-choice pages, mark-scheme tables and final pages passed
  visual inspection.
- Focused OCR/calibration/coverage tests: 21 passed.
- Full Python suite: 206 passed, 2 skipped.
- Swift suite after XcodeGen regeneration: 11 passed.
- App Store plist/privacy/entitlement lint and sandboxed Release build passed
  with strict concurrency and warnings-as-errors.
- Frozen Release helper generated all three papers at 20/20/28 pages and emitted
  successful JSONL completion events.
- Release app code-signature verification, sandbox entitlement inspection,
  official-paper exclusion and bundled catalog byte comparison passed.
- Automated structural-demand calibration passed. Independent subject review,
  student trial, psychometric equivalence and difficulty verification remain
  false.
- Matrix summary: 105 families, 4 advertised, 101 reference-profiled,
  4 implemented, 0 partial, 0 verified.

## OCR Computer Science H446 slice

- Reference structure: eight official question papers, four each for H446/01
  and H446/02; aggregate counts, bands, sequence inventories and hashes only.
- Current H446/01: 41 subquestions, 140 marks, 2h30, 28 pages.
- Current H446/02: 40 subquestions, 140 marks, 2h30, 32 pages, Section A plus a
  Section B programming scenario.
- Current printed mark sequences match exactly; question-type maps distinguish
  short answers, analysis, traces, calculations, diagrams, tables,
  programming and level-based extended responses.
- Twenty seeds per paper produced 20 unique paper fingerprints and 20 unique
  stimulus/code/data fingerprints with complete component topic coverage.
- Generated question-paper geometry: 28/32 pages; mark schemes: 12/11 pages.
- All 83 sampled generated PDF pages contained text and had no out-of-bounds
  text blocks. Covers, pseudocode, answer lines, sparse continuations, Section B,
  trace data, mark-scheme tables and final pages passed visual inspection.
- OCR H446/calibration tests: 8 passed; backend/registry focused suite: 26 passed.
- Full Python suite: 215 passed, 2 skipped.
- XcodeGen regeneration and Swift suite: 11 passed.
- App Store plist/privacy/entitlement lint and sandboxed Release build passed
  with warnings-as-errors and strict concurrency.
- Frozen Release helper generated both papers with 28/32-page geometry and
  successful JSONL completion events.
- Release code-signature, bundled canonical JSON equality and official-paper
  exclusion checks passed.
- Automated structural-demand calibration passed. Subject review, student
  trials, psychometric equivalence and final difficulty verification remain
  false.
- Matrix summary: 105 families, 5 advertised, 100 reference-profiled,
  5 implemented, 0 partial, 0 verified.

## AQA Business 7132 slice

- Reference set: 18 official question papers and six Paper 3 inserts; the
  shipped calibration retains aggregate bands, inventories and hashes only.
- Current structures match exactly: Paper 1 has 15 one-mark MCQs,
  `4,4,9,9,9`, two 25-mark Section C choices and two 25-mark Section D choices;
  Paper 2 uses `3,4,9,16,3,6,9,16,9,9,16`; Paper 3 uses
  `12,12,16,16,20,24`.
- Generated question-paper geometry is 32/24/28 pages; Paper 3 source booklet
  is eight pages. Mark schemes are 6/4/3 pages.
- Twenty seeds per paper produced 20 unique paper fingerprints and 20 unique
  stimulus fingerprints with full 3.1–3.10 syllabus coverage.
- Paper 1 contains 12 conceptual and three quantitative MCQs; every option set
  contains four distinct choices.
- Case extracts now use coherent market, finance, operations, strategy,
  external-change, stakeholder and scenario-analysis roles rather than
  repeated generic prose. Source tables and charts use the same values.
- All generated PDFs passed page-count, non-empty-page and bounds checks;
  sampled MCQ, case, essay-choice, source and mark-scheme pages passed visual
  inspection.
- Full Python suite: 224 passed, 2 skipped. Swift suite: 11 passed.
- App Store plist/privacy/entitlement lint and sandboxed arm64 Release build
  passed with warnings-as-errors and strict concurrency.
- Frozen Release helper generated all three papers with 32/24/28-page geometry
  and an eight-page Paper 3 source booklet.
- Release code-signature, canonical bundled JSON equality and official-paper
  exclusion checks passed.
- Automated structural-demand calibration passed. Subject review, student
  trials, psychometric equivalence and final difficulty verification remain
  false.
- Matrix summary: 105 families, 6 advertised, 99 reference-profiled,
  6 implemented, 0 partial, 0 verified.

## AQA Accounting 7127 slice

- Reference structure derived from 12 official question papers, six per paper;
  only aggregate bands, sequence inventories and hashes are retained.
- Current Paper 1 sequence is ten one-mark MCQs followed by
  `6,7,5,2,14,6,6,8,6,25,25`.
- Current Paper 2 sequence is ten one-mark MCQs followed by
  `3,6,3,8,4,8,2,6,8,1,5,6,25,25`.
- Both generated papers are 120 marks, three hours and 36 pages. Section starts
  match the current geometry: Paper 1 at pages 2/12/22 and Paper 2 at 2/12/20.
- Twenty seeds per paper produced unique paper and stimulus fingerprints with
  complete coverage of all 18 specification domains.
- PDF non-empty/bounds scans and sampled MCQ, financial-statement,
  management-accounting and 25-mark decision pages passed.
- Full Python suite: 233 passed, 2 skipped. Swift suite: 11 passed.
- Sandboxed arm64 App Store Release build, frozen-helper 36/36-page generation,
  canonical resource equality and strict code-signature checks passed.
- Automated structural-demand calibration passed; independent review, student
  trials, psychometric equivalence and final difficulty verification remain
  false.
- Matrix summary: 105 families, 7 advertised, 98 reference-profiled,
  7 implemented, 0 partial, 0 verified.
