# French NSI prototype verification — 2026-09-28

**PROTOTYPE, not educational qualification.** Tracks
[issue #16](https://github.com/james8464/Past-paper-generation/issues/16).
The approved plan remains incomplete. No French live inference, teacher review,
learner pilot or App Store approval is represented by this record.

## Engineering checks

- Baseline: 2,078 Python tests passed, two optional skips.
- Education/reference foundation: 2,094 passed, two optional skips.
- Integrated prototype: 2,122 passed, two optional skips.
- Inference redirect protection: 2,123 passed, two optional skips; five existing
  PyMuPDF/SWIG deprecation warnings. A subsequent reviewer-name whitespace regression
  was reproduced and repaired; focused tests passed. Final consolidated run:
  **2,124 passed, two optional skips, five existing warnings** (142.42 seconds).
- Native build/tests passed, including reproduced export, history and failure
  lifecycle regressions. Final packaging/native run: **66 passed, zero failures,
  zero skips**, arm64 MacBook Pro, macOS 26.6.2. This is not Intel or App Store testing.
- Local App Store build preflight passed at commit `05553ad`: Release build,
  signing verification and sandbox/hardened-runtime checks. This does not establish
  distribution signing, Apple review or App Store acceptance.
- Initial GitHub backend run found a Python-build portability defect: SQLite's
  extension-loading API can be absent. Reproduced it with a connection lacking that
  API, then repaired feature detection while retaining the SQL authorizer's denial
  of extension loading and external databases. All eight NSI assessment tests pass.
  Full local requalification: **2,125 passed, two optional skips, five existing
  warnings** (107.49 seconds). Independent review found no Important issue.
  The initial GitHub native release/tests job passed; GitHub requalification of
  the repair is separate from these local totals.

Independent review identified four repaired issues: nested French bundles bypassing
App Store export; code wrapping changing Python semantics; unsupported qualification
claims being accepted; and failed jobs retaining unusable checkpoint seeds/history.
Exported artifact locations are now used in persistent history as well.

Tests cover French response schemas/budgets/seeds; source/model/reference checkpoint
identities; package-reader dispatch; complete-or-absent publication; rendering failure;
cancellation; scoped retrieval; exact points; and bounded technical contracts.
These are deterministic tests, not evidence of a language model's NSI accuracy.

## References

Four pinned seed PDFs are acquired/indexed locally; one is holdout-only. The macOS
system-trust programme download was exercised: 201,097 bytes, SHA-256
`10ce34666edd722a3d8d86642a9f1ac205c7a9d128d6142a17effcba2fb85e69`.
TLS verification remains enabled; the fallback rejects redirects/non-approved hosts.
No official PDFs are committed or bundled. At this dated checkpoint, archive
completeness remained false; the 30 September addendum below supersedes that status.

The official interactive archive's NSI filter was traversed across all eight pages:
79 rows, 122 distinct linked documents (114 PDFs, eight Braille ZIP archives).
The [discovery snapshot](french-nsi-archive-discovery-2026-09-28.json) records every
link and normalized session/centre/variant metadata; its transcription checksum
matched the browser-extracted rows. This reconciles the visible index count only:
content hashes, duplicate-content checks, availability, per-document rights and
stratified holdouts remain pending. Discovery entries are not retrieval-eligible.

## Manual PDF inspection

Rendered the 2026 Métropole reference cover/first exercise using Poppler. Inspected
all four question-paper pages and eight correction pages of an engineering fixture,
then the three changed correction pages after repair. The correction now has five
pages including unchanged cover/guidance. Fixed short corrections spilling onto
almost-empty continuation pages; credit headings identify exercise and question.

The fixture contains deliberately trivial repeated calculations. It is **not** a
live-generated paper, realistic NSI assessment or accepted evaluation specimen.
It establishes neither difficulty, timing, originality nor authentic paper length.

Remaining visual differences/work:

- Cover grouping, vertical rhythm, heading weight, exercise headings and footers
  differ from the historical reference. Compatible fonts are not pixel identity.
- Real papers use extended contextual exercises, diagrams and code. Structured
  vector diagrams/tables and complete code-layout qualification remain unfinished.
- Overwide code fails instead of silently changing it. Large-print bounds tests
  exist; full manual large-print/accessibility/VoiceOver/reading-order audits do not.
- Independent non-official branding is intentional; 2026 references cannot establish
  an official 2027 template. Keep visual calibration `not_run`.

## Isolation

Manual native UI smoke: opened the built app, selected the French workspace,
verified that UK qualification controls disappear, switched System → Français
and observed translated controls/consent text with unchanged 2027 NSI context.
Opened and cancelled reference-download consent; no generation was started.
Restored the original language and board selection. This is a smoke check, not a
complete keyboard, contrast, VoiceOver or window-size accessibility audit.

Changes remain in `french-baccalaureat`. Main's UK controller was verified active;
no duplicate inference was started. Do not merge into its source baseline during
that run. Issues #4/#8 remain open independently; a prototype does not close #16.

## 30 September reconciliation and fidelity addendum

The archive gate above is now complete locally. All 79 canonical 2021–2026 paper
links downloaded successfully, alongside the two foundational documents, and all
81 registered files have pinned SHA-256 hashes. Thirteen papers are frozen as
holdouts. Forty-three enlarged-print/braille links remain recorded as non-retrieval
representations of canonical papers. Two byte-identical 2022 Nouvelle-Calédonie
normal/replacement pairs were found; one identity from each pair is excluded from
the SQLite index so duplicates cannot alter ranking. Neither pair crosses the
holdout boundary. The current index has 79 unique sources: 66 reference and 13
holdout. Rights remain reference-only and no source PDF is bundled.

The renderer was remeasured against the official Métropole 2026 paper. It now uses
the measured A4 cover rhythm, 20/14/11-point hierarchy, 14-point centred exercise
titles, italic scope line, question indents, unmodified 12-point code and independent
non-official branding. Correction guidance appears once, followed by compact answer
and indicative-credit blocks. All generated fixture pages were manually inspected;
the fixture still does not establish educational quality.

The French-focused regression suite passes **57 tests** after archive reconciliation,
originality, difficulty, rendering, runtime, review and benchmark-runner changes.
The complete backend suite passes **2,189 tests** with two optional skips and five
existing PyMuPDF/SWIG deprecation warnings. Native compilation succeeds and 69 of
70 tests pass; the sole failure is the deliberately missing real `TutorialFrenchNSI`
screenshot. The Mac session is locked, so neither that truthful UI asset nor the
real demonstration video can be captured yet. A mock image is not accepted as a pass.

A resumable candidate-model runner now preserves first-pass/repaired status, logs,
checkpoints, timing, RSS, hardware, Ollama version and exact model/source/code identity.
The live matrix remains not run. The exact `ministral-3:8b` and `qwen3:8b` candidates
must be installed and the source committed before qualification begins.
