# Task Intent Draft

## Requested outcome

Ship a macOS App Store-ready A-level practice-paper generator whose supported
subject/exam-board/paper combinations produce unique, syllabus-specific papers
with measured parity for structure, question types, timing, mark distribution,
difficulty, and independently recreated page geometry.

## Scope

- A-level only.
- AQA, OCR, and Pearson Edexcel families for which official public reference
  metadata has been lawfully collected.
- Other boards only after their public resources can be acquired without
  bypassing robots, authentication, access controls, or licensing restrictions.
- Question papers, source/insert booklets where required, and mark schemes.
- Native macOS runtime, offline/hosted model paths, packaging, sandboxing,
  privacy, signing readiness, and App Store review readiness.

## Non-goals

- Shipping official papers, specifications, logos, trademarks, or copied text.
- Claiming affiliation, endorsement, or official-paper status.
- Bypassing gated resources or automated-access restrictions.
- Pixel-copying protected branding or trade dress.
- Marking a family ready from a shared generic prompt or an unvalidated layout.

## Goal and stop conditions

The goal is complete only when every in-scope family has an explicit paper
blueprint and every advertised paper passes schema, syllabus, marks, difficulty,
uniqueness, PDF, runtime, visual, and release gates.

Valid stops are:

- `done`: every advertised combination passes all gates and external release
  requirements are either supplied or explicitly handed off.
- `blocked`: a repeated legal/access/credential dependency prevents further
  safe progress.
- `needs-verification`: implementation exists but evidence is incomplete.
- `scope-exceeded`: a newly requested board or qualification is outside the
  A-level/public-reference boundary.

## Compatibility boundary

- Existing Economics Edexcel A Papers 1–3 and AQA Computer Science Paper 2
  commands remain supported.
- Existing local Ollama and optional hosted-provider behavior remains supported.
- `Reference Corpus/` remains development-only, ignored by Git, and excluded
  from every app bundle.
- Shipped profiles contain numeric/structural derived data only.
- A family may be shown as ready only when all declared paper variants pass the
  readiness gates.

## Retirement boundary

- Retire hard-coded Swift subject lists after the checked-in catalog becomes
  the canonical source.
- Retire binary `ready` labels that lack per-paper evidence.
- Retire generator dispatch based solely on two subject names after the
  registry contract is implemented.
- Never reintroduce official branding or copied reference text.

## Baseline read set hint

Required:

- `README.md`
- `Resources/catalog.json`
- `Resources/layout-profiles.json`
- `Backend/Core/generation.py`
- `Backend/Core/cli.py`
- `macOS/PaperCreator/AppModels.swift`
- `macOS/PaperCreator/AppViewModel.swift`
- generator tests under both current resource packs
- App Store build/preflight scripts and entitlements
- current Git worktree status

Acknowledged before this plan:

- README, catalog, layout-profile schema, backend dispatch/CLI, and worktree.
- Prior verified Python, Swift, standalone-helper, PDF, and App Store build
  evidence retained in `90-evidence.md`.

Missing:

- Per-paper structural blueprints for the remaining profiled families.
- Licensing/access path for WJEC, CCEA, and Cambridge International corpora.
- Apple Distribution credentials and final App Store Connect metadata.

Decision: proceed with the public AQA/OCR/Pearson-derived numeric corpus and
keep unlicensed/unavailable boards outside advertised readiness.

## Impact statement draft

This work changes the product catalog, generator registry, generation contracts,
content validation, PDF renderers, test matrix, and release evidence. The
development corpus remains outside the shipped product. Any new ready status is
a public product claim and therefore requires complete evidence.

## Execution Readiness View

- Intent lock: authentic, unique, syllabus-specific unofficial practice papers.
- Scope fence: A-level; public lawful references; macOS App Store.
- Baseline lock: preserve current ready generators and verified release path.
- Owner constraints: app catalog owns advertised support; generator registry
  owns dispatch; each resource pack owns syllabus and paper blueprints.
- Compatibility: existing CLI examples and Swift generation flow keep working.
- Retirement: remove hard-coded coverage only after registry/catalog tests pass.
- Task batches: coverage schema; registry; per-family vertical slices; full
  matrix; release gate.
- Tests: schema, deterministic dry-run, multi-seed uniqueness, mark totals,
  PDF integrity, visual metrics, runtime, sandboxed release build.
- Review gates: no protected assets/text in bundle; no unsupported ready claim;
  no family-specific fallback to generic content.
- Drift rule: stop a slice if it introduces copied reference content, claims
  unsupported readiness, or weakens an existing verified combination.
- Completion evidence: every advertised paper has a passing machine-readable
  evidence record plus final release preflight.
