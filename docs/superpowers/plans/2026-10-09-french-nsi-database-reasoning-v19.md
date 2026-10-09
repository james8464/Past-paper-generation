# French NSI database reasoning V19 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the existing original database case a deeper ten-question integrity, query and debugging progression without changing old paper packages.

**Architecture:** Keep the immutable six-incident V2 data contract, but add a V19-only finite French prose and answer/rubric catalogue. Select and replay its IDs through a separately hashed authoring adapter. Explicit pipeline/runtime/PDF dispatch protects V13–V18 and UK behaviour.

**Tech Stack:** Python 3, Pydantic, SQLite, ReportLab, PyMuPDF, pytest, Ruff, Graphify.

**Spec:** `docs/superpowers/specs/2026-10-09-french-nsi-database-reasoning-v19-design.md`

## Global constraints

- Written Terminale NSI session 2027 only: three independent exercises, 210 minutes, exact 18 technical points plus distinct two-point indicative French-language component.
- Exercise 2 remains ten questions, 70 estimated minutes and 5.5, 6 or 6.5 exact-decimal technical points; all prompts, answers and criteria are finite, app-owned French.
- The immutable V2 six-incident data contract and V13–V18/UK saved-package readability remain unchanged; unknown/mixed identity fails closed.
- French-only sources, holdout isolation, no UK fallback, no model-authored SQL/Python execution, non-official PDF labels, local privacy and preserved failed attempts remain unchanged.
- Fixture or automated live success cannot establish teacher, learner, examiner, rights or accessibility approval; final UK/French matrix stays deferred until fidelity passes.

## Review focus

- A hypothetical empty category is printed as if it already exists: subject must state the hypothetical separately, and answer must distinguish observed counts from the hypothetical zero.
- A more elaborate prompt asks for two results but grants or verifies credit for only one: require exact quarter-point criteria for each requested step at every allocation.
- A V18 checkpoint or package is reinterpreted with V19 wording: reject mismatched catalogue, prompt, response and candidate hashes while retaining old replay.
- A V19 subject omits one locked SQL/Python fact or leaks an expected answer: the version-specific PDF gate must reject it in both normal and large print.
- Additional prose creates a clipped or orphaned phase/question, or hides a correction rubric: test physical bounds and inspect every page.

---

### Task 1: Finite V19 question, answer and credit catalogue

**Files:** Create `Backend/Core/france/database_reasoning_prose.py`; test `tests/test_french_database_reasoning_prose.py`.

**Interfaces:** `DATABASE_REASONING_PROSE_VERSION = "fr-nsi-database-prose-v3"`; `database_reasoning_catalogue_digest() -> str`; `database_reasoning_selection_schema(contract: DatabaseDepthContract) -> dict`; `validate_database_reasoning_selection(contract, selection: dict) -> None`; `render_database_reasoning_candidate(contract, selection: dict, task_specs: list[dict]) -> dict`.

- [ ] Write failing tests for ten ordered native-French IDs, three phase labels adjacent to 2a/2e/2g, the two-row join trace, a clearly hypothetical empty category, initial/post-update Python returns, and every prompt-to-answer-to-credit match. Test all 5.5/6/6.5 allocations and multiple seeds, including a wrong category label.
- [ ] Run focused tests RED; verify missing V19 interfaces or expected derivations cause the failures.
- [ ] Implement only finite V19 variants and deterministic answers from `DatabaseDepthContract.to_dict()`. Recompute hypothetical zero by running the existing left-join SQL against a private copy with a new empty category, never modifying the locked V2 contract or running model SQL. Use exact `Decimal` quarter-point criteria.
- [ ] Run focused tests GREEN and Ruff. Review and commit Task 1; do not alter V16–V18 prose.

### Task 2: Explicit V19 selection, pipeline identity and replay

**Files:** Create `Backend/Core/france/database_reasoning_authoring.py`; modify `Backend/Core/france/provider.py` and `Backend/Core/france/pipeline.py`; test `tests/test_nsi_pipeline.py`, `tests/test_french_database_reasoning_authoring.py`.

**Interfaces:** `database_reasoning_selection_prompt(task, contract, references) -> str`; `author_database_reasoning_selection(client, task, contract, references, path, *, run_identity) -> tuple[dict, dict]`; `replay_database_reasoning_selection(task, contract, references, evidence, *, run_identity) -> dict`; `_tasks_for_seed_v19(seed: int) -> list[dict]` derives from V18 and preserves all allocations/other exercises.

- [ ] Write failing tests for V19 generation, exact 18+2 totals, three independent exercises and 70-minute E2; reject extra/unknown/reordered IDs and changed hashes or failed-attempt evidence. Replay an existing V18 package and a UK route in the same test scope.
- [ ] Run focused tests RED, then implement prompt/schema dispatch and hash-bound checkpoint saving/replay with no default to V18. Add the V19 prompt version only to explicit pipeline branches and identity field sets; keep V13–V18 branches unchanged.
- [ ] Run focused tests GREEN and Ruff. Review and commit Task 2.

### Task 3: Publication and PDF gates

**Files:** Modify `Backend/Core/france/runtime.py` and `Backend/Core/france/rendering.py` only if V19 phase flow needs layout treatment; test `tests/test_french_runtime.py` and `tests/test_french_pdf_layout.py`.

**Interfaces:** Runtime publishes V19 for the current French written route; `database_pdf_contract_version("fr-nsi-written-2027-v19")` dispatches to the V2 facts plus V19 prose gate. Existing `validate_database_depth_contract_pdf(...)` continues validating V2 table/source facts; add `validate_database_reasoning_pdf(...)` for phase labels, V19 prompt/answer/credit identity and hypothetical status if needed rather than weakening old checks.

- [ ] Write failing runtime/PDF tests for explicit V19 dispatch, exact printed V2 facts, all ten prompts, no leaked answers/criteria, three phase labels, normal/large-print bounds, and rejection of missing/interchanged explanations or a correction rubric separated from its answer.
- [ ] Run focused tests RED; implement only the V19-specific dispatch/checks and minimal page-flow repair proven necessary by those tests.
- [ ] Run focused tests GREEN, then full pytest, Ruff, repository hygiene and `git diff --check`; update Graphify and repository inventory. Review and commit Task 3.

### Task 4: Visual and protected qualification checkpoint

**Files:** Update English evidence and Occitanie claims only for measured results; no fixture may be called live.

- [ ] Render normal and large-print V19 fixture subjects and corrections, inspect every page with the PDF skill against the official 2026 Métropole paper, and fix any material defect test-first. Record remaining density/depth gaps honestly.
- [ ] Run full pytest, Ruff, hygiene, compliance, Graphify/inventory and diff checks. Obtain one fresh read-only whole-branch review, resolve important findings test-first, then open/attach a protected PR. Merge only after Backend and macOS checks pass; fast-forward clean main.
- [ ] Only after merge, run one source/model/reference-pinned French live diagnostic, retain all attempts/artifact hashes, inspect every PDF page against the official comparator and record a measured HOLD/PASS. Do not run the expensive final shared-route matrix unless the French paper passes manual fidelity and shared source is frozen.
