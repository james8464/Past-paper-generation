# French NSI database depth implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned, ten-question original database reasoning sequence to the French NSI written route without invalidating previous packages.

**Architecture:** V16 selects from an app-owned, immutable SQLite-backed database contract and a finite French prose catalogue. Legacy V13–V15 dispatch continues to use V1. A version-specific adapter builds and verifies V16 Exercise 2, while the shared pipeline retains three independent exercises and exact overall scoring.

**Tech Stack:** Python 3, Pydantic, SQLite, ReportLab, PyMuPDF, pytest, Ruff, Graphify; protected Backend and macOS CI.

**Spec:** `docs/superpowers/specs/2026-10-08-french-nsi-database-depth-design.md`

## Global constraints

- Written Terminale NSI session 2027 only; three independent exercises and 210 minutes.
- 18 exact-decimal technical points plus a separate two-point indicative language component; E2 totals 5.5, 6 or 6.5 by existing allocation.
- V13–V15 contracts/catalogues and package replay stay readable; UK route IDs/state/packages are unchanged.
- French-only scoped official-source retrieval, no UK fallback, no model-authored executable SQL/Python, no holdout leakage.
- Subject and correction retain non-official/proposed labels. No automated result is teacher, learner, examiner or accessibility approval.
- Preserve failed attempts and their hashes; do not run the final UK/French live matrix until shared source freezes.

## Review focus

- A seeded case accidentally makes the wrong and correct join identical: test multiple seeds and reject ambiguous cases in the constructor.
- The wrong Python count equals the correct count: assert unequal values for every valid contract.
- A malformed or reordered ten-question selection sneaks through: reject missing, extra, duplicate or unknown IDs.
- A V16 checkpoint replays with V15 prose/blueprint identity: require versioned contract/catalogue/digest equality.
- A large-print table/question or correction rubric clips or leaks answers into the subject: render and inspect both PDFs, and validate physical bounds and page order.

---

### Task 1: Immutable V2 case and deterministic facts

**Files:** Create `Backend/Core/france/database_depth_contract.py`; test `tests/test_french_database_depth_contract.py`.

**Interfaces:** `DatabaseDepthContract.from_dict(data: dict) -> DatabaseDepthContract`; `build_database_depth_contract(seed: int) -> DatabaseDepthContract`. `to_dict()` returns canonical JSON including `version: 2`, `task_ids: [2a…2j]`, six incidents, fixed SQL/Python source and SQLite-recomputed `expected`; `digest` binds all fields.

- [ ] Write failing tests for seed determinism, six valid rows, hand-checked join/group/update/count results, all ten IDs, malformed rows/keys/source code, and alternate-seed fault observability.
- [ ] Run focused tests to observe expected failures.
- [ ] Implement the V2 constructor and SQLite-backed expected results without changing V1.
- [ ] Run focused tests and a V1 compatibility test; review/commit Task 1.

### Task 2: Finite ten-question French authoring

**Files:** Create `Backend/Core/france/database_depth_prose.py`, `Backend/Core/france/database_depth_authoring.py`; modify `Backend/Core/france/provider.py`; test `tests/test_french_database_depth_authoring.py`.

**Interfaces:** `database_depth_selection_schema(contract)`, `validate_database_depth_selection(contract, selection)`, `render_database_depth_candidate(contract, selection, task_specs) -> dict`, `author_database_depth_selection(...) -> tuple[dict, dict]`, `replay_database_depth_selection(...) -> dict`. Version and catalogue digest are immutable identity fields. Only finite IDs cross the model boundary.

**Locked blueprint values:** `2a`–`2j` have minute credits `(6,6,7,7,8,8,7,7,7,7)`. Every question receives at least `0.5` technical point. `2e` receives a further `0.5` at all allocations; `2f` receives a further `0.5` at allocations 6 and 6.5; `2i` receives a further `0.5` at allocation 6.5. Thus E2 totals exactly 5.5, 6 or 6.5.

- [ ] Write failing tests for ten stable question labels, native French, correct answer/rubric alignment, exact E2 credit profiles and 70-minute total, schema rejection, hash-bound replay, and saved failed attempts.
- [ ] Run focused tests RED.
- [ ] Implement original 2a–2j prose and evidence-bound selection/replay; update fixture provider dispatch explicitly for V16, never as an implicit fallback.
- [ ] Run focused tests GREEN, Ruff and review/commit Task 2.

### Task 3: V16 pipeline, verification and backward compatibility

**Files:** Modify `Backend/Core/france/pipeline.py`, `Backend/Core/france/runtime.py`, `Backend/Core/france/verification.py`, `Backend/Core/france/nsi.py` only if schema demands it; test `tests/test_nsi_pipeline.py`, `tests/test_french_runtime.py`, `tests/test_french_benchmark_runner.py`.

**Interfaces:** `generate_assessment(..., contract_authoring_version="v16")` is explicit opt-in internally; runtime selects V16 for the current written route. `_tasks_for_seed_v16(seed)` creates the ten-question E2 blueprint and preserves E1/E3 contracts. `validate_database_depth_contract_pdf(...)` checks printed V2 facts, labels, answers and rubric credits without V1 fallback.

- [ ] Write failing route/replay tests: V16 generation and exact paper credit, V15 saved-package validation, UK registry/state stability, identity mismatch refusal, missing printed E2 fact and subject answer leakage.
- [ ] Run focused tests RED.
- [ ] Add explicit V16 dispatch/identity and V2 deterministic verification; keep V13–V15 branches untouched and fail closed on unknown versions.
- [ ] Run focused tests GREEN; review/commit Task 3.

### Task 4: PDF fidelity, evidence and protected integration

**Files:** Modify renderer only for V16-specific page flow if generated PDFs expose a defect; update `Resources/repository-inventory.json` if tracked file counts change, Graphify output, and English evidence only for measured results.

- [ ] Render fixture V16 normal and large-print subject/correction; inspect every page using the PDF skill and compare structure/density with the official 2026 Métropole reference. Fix observed defects test-first.
- [ ] Run full pytest, Ruff lint/format, repository hygiene, `git diff --check`, and `graphify update .`; preserve old live/failure artifacts.
- [ ] Obtain read-only code review, address important findings, commit and push in small units.
- [ ] Open and attach a PR, wait for protected Backend/macOS success, merge, fast-forward clean main.
- [ ] Only after source freeze, run one pinned French live diagnostic and page-by-page manual comparison; record artifact/model/source hashes and an honest HOLD/PASS decision. Do not start the full matrix if fidelity remains on hold.
