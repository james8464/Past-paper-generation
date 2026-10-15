# French NSI V24 incident reconciliation — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace only new French Exercise 2 packages with a sustained, deterministic database-to-algorithm reconciliation case and useful working space.

**Architecture:** A new immutable V4 E2 contract and finite French catalogue own every source fact, oracle and answer. Explicit V24 selection/package/PDF/benchmark dispatch leaves V13–V23 and UK replay untouched.

**Tech Stack:** Python, SQLite, pytest, ReportLab, Ruff, Graphify, protected GitHub PR.

**Spec:** `docs/superpowers/specs/2026-10-13-french-nsi-incident-reconciliation-v24-design.md`

## Global Constraints

- Three independent Terminale NSI written exercises; 210 estimated minutes.
- Exactly 18 technical points plus a distinct 2-point indicative French-language component; E2 profiles 5.5/6/6.5 and 70 minutes.
- For `2a`–`2l`, quarter-point profiles are exactly `5.5: (1,2,2,2,2,3,2,2,2,2,1,1)`, `6: (1,2,3,2,2,4,2,2,2,2,1,1)`, `6.5: (1,2,3,2,2,4,3,2,2,3,1,1)`; minutes `(4,5,8,6,7,8,6,6,6,6,4,4)`.
- French-only references, holdouts excluded, no UK fallback; non-official PDF labels.
- V13–V23 French and UK package/state replay unchanged. Never mutate V21 E2 source facts.
- No page-count padding or final expensive UK/French model matrix while source is changing or manual French fidelity is HOLD.
- Preserve all pinned evidence and ignored artifacts; no official paper is bundled.

## Review Focus

- Two matching labels in a faulty join must not hide six incorrect rows: test all eight rows and mismatch IDs.
- Category-2 faulty/correct counts diverge at S0/S1 but agree at S2: test the full trace and the explanatory rubric.
- An invalid agent reference must not alter S0; an empty fifth category must appear with count zero only in its separate hypothesis.
- Mixed V23/V24 contracts, catalogues or selection hashes must fail closed rather than silently falling back.
- Normal/large-print comparison, query and state materials must remain legible beside dependent tasks; answers and technical credit must stay together in correction.

---

### Task 1: Immutable V4 facts and finite twelve-question prose

**Files:** Create `Backend/Core/france/database_reconciliation_contract.py`, `Backend/Core/france/database_reconciliation_prose.py`; test `tests/test_french_database_reconciliation_contract.py`, `tests/test_french_database_reconciliation_prose.py`.

**Interfaces:** `DatabaseReconciliationContract.from_dict(data: dict)`, `build_database_reconciliation_contract(seed: int, exercise_id: str = "2")`, `to_dict()`, `digest`; `database_reconciliation_catalogue_digest()`, `database_reconciliation_selection_schema(contract)`, `validate_database_reconciliation_selection(contract, selection)`, `render_database_reconciliation_candidate(contract, selection, task_specs)`.

- [ ] Write RED contract tests for the eight exact rows, two matching/six mismatching labels, category counts `[2,2,2,2]`, category-2 traces faulty `[2,2,2]` versus corrected `[0,1,2]`, SQLite/Python oracle parity, invalid insert, empty fifth category and edited/missing/mixed fields. Run `pytest tests/test_french_database_reconciliation_contract.py -q`; expect failures for missing V4 interfaces.
- [ ] Implement the smallest standalone V4 contract and independent oracles; run the contract tests to green. Keep V3 untouched.
- [ ] Write RED prose tests for IDs `2a`–`2l`, 70 minutes, exact quarter-point criteria for 5.5/6/6.5, finite selection, all eight comparison rows, staged materials and answer/credit parity; run focused tests and confirm RED.
- [ ] Implement V24-only French prose and candidate materials; run focused tests and Ruff. Inspect diff, update Graphify/inventory and commit Task 1 files.

### Task 2: Hash-bound selection and version-isolated packages

**Files:** Create `Backend/Core/france/database_reconciliation_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_database_reconciliation_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `database_reconciliation_selection_prompt(...)`, `author_database_reconciliation_selection(...)`, `replay_database_reconciliation_selection(...)`; `_tasks_for_seed_v24(seed: int)` returns V23 E1/E3 and V24 E2 blueprints only.

- [ ] Query Graphify for current E2 dispatch. Write RED tests for catalogue/contract hash binding, finite provider response, exact `fr-nsi-written-2027-v24` identity, mixed-version rejection and V13–V23/UK replay; run focused tests and confirm RED.
- [ ] Add explicit V24 provider/pipeline/replay routing without changing older version branches. Run focused tests and Ruff; inspect diff, update Graphify/inventory and commit Task 2 files.

### Task 3: Runtime, PDF and benchmark gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; test `tests/test_french_runtime.py`, `tests/test_french_benchmark_runner.py` and a new `tests/test_french_database_reconciliation_pdf.py`.

**Interfaces:** V24 runtime dispatch uses V24 only for E2; `validate_database_reconciliation_pdf(...)` binds V4 materials, all `2a`–`2l` prompts, answers, exact credits and digest to the displayed PDF.

- [ ] Write RED tests for omitted/swapped rows, wrong state trace, leaked answers, missing/interchanged materials, answer/credit mismatch, normal/large page bounds, benchmark identity and UK/old-version compatibility; run focused tests and confirm RED.
- [ ] Implement the V24 runtime/rendering/verification/benchmark routes with fail-closed checks; run focused and full pytest, Ruff, hygiene/compliance, Graphify update and inventory. Inspect diff and commit Task 3 files.

### Task 4: Page-level review, protected integration and one live diagnostic

**Files:** Add exact English quality evidence and update Occitanie claims/report builder only after a live run; retain fixture and live artifacts in ignored paths.

**Interfaces:** Existing normal/large PDF renderers; pinned `gemma4:12b` seed 270100 and locked French reference index.

- [ ] Use the PDF skill to render and inspect every normal/large subject/correction fixture page and all 16 official 2026 Métropole pages. Record page-level material association, legibility and remaining fidelity gaps; repair defects test-first without padding.
- [ ] Run full tests, Ruff/hygiene/compliance, Graphify/inventory and fresh read-only whole-branch review. Open a protected PR; merge only after Backend and macOS checks pass, then fast-forward clean primary main.
- [ ] Run exactly one pinned V24 French live diagnostic; retain every attempt/checkpoint/artifact/hash and inspect every generated PDF page against the official comparator using the PDF skill. Publish exact English evidence and honest Occitanie claims through a separate protected PR. If manual fidelity remains HOLD, select no French model and do not launch the final matrix.
