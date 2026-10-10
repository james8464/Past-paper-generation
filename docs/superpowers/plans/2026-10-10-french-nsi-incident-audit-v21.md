# French NSI incident audit V21 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Exercise 2 a sustained, original incident-audit case with eight locked rows, two observable state changes and traceable SQL/Python reasoning.

**Architecture:** Keep V13–V20 contracts and prose immutable. Add a V21-only V3 database contract and finite French catalogue, then explicit selection, pipeline, runtime, PDF and benchmark dispatch. Stage candidate working tables near dependent prompts; retain V20 Exercise 1 and V18 Exercise 3.

**Tech Stack:** Python 3, SQLite, Pydantic, ReportLab, PyMuPDF, pytest, Ruff, Graphify.

**Spec:** `docs/superpowers/specs/2026-10-10-french-nsi-incident-audit-v21-design.md`

## Global Constraints

- Written Terminale NSI session 2027 only: three independent exercises, 210 estimated minutes, exactly 18 technical plus a distinct two indicative French-language points; no practical component.
- Exercise 2 has 2a–2j, 70 estimated minutes and exact `Decimal` 5.5/6/6.5 allocations in the spec; no rubric credits unstated work.
- V13–V20 and UK package/state replay stay unchanged. Unknown or mixed V21 identity fails closed.
- French-only eligible references, holdout isolation, no UK fallback or model-executed code, local privacy and non-official PDF labels stay unchanged.
- Fixtures and automated passes are provisional; teacher, learner, rights and accessibility review are external gates. Defer the final UK/French matrix while source changes or manual fidelity is on hold.

## Review Focus

- A proposed insert with agent 999 is accidentally treated as an initial row: test row counts and S0/S1/S2 isolation in the V3 contract and PDF.
- Wrong join and true join happen to produce the same displayed label for one row: test all four comparison rows and require at least the specified counterexamples.
- A one-row update silently changes another incident or a grouped count: test SQLite row counts and before/after states, not hand-entered answers.
- The Python trace derives from a status sequence other than the printed incident table: test 5/4/3 and 3/4/5 across S0/S1/S2, plus the empty input.
- A V20 package or a normal/large-print subject acquires V21 data or answers: test version-isolated replay, staged material association, answer exclusion and bounds.

---

### Task 1: Immutable V3 database facts and finite V21 prose

**Files:** Create `Backend/Core/france/database_audit_contract.py`, `Backend/Core/france/database_audit_prose.py`; test `tests/test_french_database_audit_contract.py`, `tests/test_french_database_audit_prose.py`.

**Interfaces:** `DatabaseAuditContract.from_dict(data: dict) -> DatabaseAuditContract`, `build_database_audit_contract(seed: int, exercise_id: str = "2") -> DatabaseAuditContract`, `to_dict() -> dict`, `digest: str`; `database_audit_catalogue_digest() -> str`, `database_audit_selection_schema(contract) -> dict`, `validate_database_audit_selection(contract, selection) -> None`, `render_database_audit_candidate(contract, selection, task_specs) -> dict`.

- [ ] Write failing tests that pin all eight incident rows, four agents/categories, valid foreign keys, wrong/correct join, grouped counts 2/3/2/1, hypothetical fifth-category zero, two single-row updates, SQLite counts 3/4/5, faulty/corrected Python traces 5/4/3 and 3/4/5, and canonical digest rejection for mutated facts/source/seed. Run focused tests RED.
- [ ] Implement V3 immutable data and SQLite derivation without editing V2; run contract tests GREEN and Ruff.
- [ ] Write failing prose tests for 2a–2j, three staged working tables with blank outcomes, two finite French variants, 70-minute sum and all three exact point profiles. Require each answer/rubric claim to match a prompt and locked value; run RED.
- [ ] Implement minimal finite catalogue, material binding and deterministic answers/credits; run focused tests GREEN. Review Task 1 and commit only its files.

### Task 2: V21 selection, source identity and replay isolation

**Files:** Create `Backend/Core/france/database_audit_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_database_audit_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `database_audit_selection_prompt(task, contract, references) -> str`, `author_database_audit_selection(client, task, contract, references, path, *, run_identity) -> tuple[dict, dict]`, `replay_database_audit_selection(task, contract, references, evidence, *, run_identity) -> dict`; `_tasks_for_seed_v21(seed: int) -> list[dict]` preserves E1/E3 and the paper total.

- [ ] Write failing tests for finite IDs, seed/profile selection, three independent exercises, exact 18+2, hash-bound V21 checkpoint/package replay, and rejection of altered V3 rows, prose, prompt, source index, reference or version. Replay representative V13–V20 and UK packages. Run RED.
- [ ] Implement explicit V21 provider and pipeline branches; never silently fall back to V20, and never change earlier identity fields. Run focused tests GREEN and Ruff; review and commit Task 2.

### Task 3: Runtime, staged PDF and benchmark gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; test existing French runtime/PDF/benchmark modules.

**Interfaces:** Runtime advertises V21 only for current French written generation. `validate_database_audit_pdf(...)` binds printed V3 initial rows, join/state/trace tables, faulty source, 2a–2j and exact answer/credit to the same V21 identity; old V20 validators remain intact.

- [ ] Write failing tests for explicit V21 runtime and benchmark dispatch, V20 replay, missing/interchanged initial, join, state and trace material, wrong phase/question association, answer leakage, normal/large-print bounds, and correction answer-credit grouping. Run RED.
- [ ] Implement minimal V21-only staging and fail-closed PDF checks, preserving old paths. Run focused tests GREEN, then full pytest, Ruff, hygiene/compliance and diff checks.
- [ ] Run `graphify update .`, refresh repository inventory, review Task 3 and commit its files.

### Task 4: Visual review, protected merge and measured checkpoint

**Files:** Update English diagnostic and Occitanie evidence only after a pinned live result; never call a fixture live.

- [ ] Render normal and large-print V21 fixture subject/correction PDFs. Inspect every generated page and all official 2026 Métropole pages with the PDF skill; fix material defects test-first and retain any manual depth/working-space hold. Do not pad merely to approach 16 pages.
- [ ] Run full pytest, Ruff, hygiene/compliance, Graphify/inventory and diff checks. Obtain a fresh read-only whole-branch review and fix important findings test-first. Open and attach a protected PR; merge only after Backend and macOS checks pass, then fast-forward clean main.
- [ ] Run exactly one source/model/reference-pinned French live diagnostic after engineering merge. Retain every attempt and artifact hash, inspect every generated page against the official comparator, and publish exact measured English HOLD/PASS evidence and an honest Occitanie update through protected checks. Keep the final UK/French matrix deferred until source freezes and manual fidelity passes.
