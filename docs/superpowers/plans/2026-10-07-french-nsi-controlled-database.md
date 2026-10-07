# French NSI controlled database exercise Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Exercise 2 an original, deterministic, app-owned database and debugging exercise whose printed facts and marking cannot be changed by model prose.

**Architecture:** A seeded immutable contract owns relational data, faulty and corrected operations, and expected results. A finite French catalogue renders six blueprint questions from that contract; the model selects only bounded IDs. The v13 pipeline checkpoints and replays contract, selection and catalogue identities, while older French and UK readers stay unchanged.

**Tech Stack:** Python 3, Pydantic assessment models, pytest, existing French PDF renderer and runtime.

**Spec:** `docs/superpowers/specs/2026-10-07-french-nsi-controlled-database-design.md`

## Global Constraints

- Exercise 2 is independent of Exercises 1 and 3, has six task IDs `2a`–`2f`, and fits the existing 70-minute, 6.5-point blueprint allocation.
- The paper remains three written exercises, 18 technical points plus a distinct two-point indicative French-language component. No practical component claim.
- No model-authored fact, SQL, code, answer, credit or arbitrary text reaches the PDF. Reject unknown or inconsistent selections and preserve failures.
- Existing UK route IDs and French v10–v12 package readers remain stable; no silent cloud or UK reference fallback.
- No official annale text or holdout content is bundled. PDF outputs remain non-official and require teacher and learner gates.

## Review Focus

- Accidental primary-key/foreign-key collision across seeds: contract test must enumerate multiple seeds and recompute joins.
- Incorrect SQL result hidden by coincidentally equal IDs: contract test must show faulty and corrected JOIN differ.
- A model selection with a free-text or extra field: catalogue test must reject it without copying any bytes into rendered work.
- Resume against a changed catalogue or contract: pipeline test must reject and preserve the prior checkpoint.
- A structurally valid but visually unreadable table/code block: runtime PDF test and page-by-page manual render inspection must catch it.

---

### Task 1: Seeded relational fact contract

**Files:**
- Create: `Backend/Core/france/database_contract.py`
- Create: `tests/test_french_database_contract.py`

**Interfaces:**
- Produces: `DatabaseContract.from_dict(data: dict) -> DatabaseContract`, `.to_dict() -> dict`, `.digest -> str`, `build_database_contract(seed: int, exercise_id: str = "2") -> DatabaseContract`.

- [ ] Write failing tests for identical-seed identity, cross-seed variation, three table schemas and four incidents, duplicate/broken keys, changed JOIN results, bounded UPDATE result, unequal faulty/corrected Python counts, and tamper rejection.
- [ ] Run `pytest -q tests/test_french_database_contract.py`; expected failure is missing contract module.
- [ ] Implement canonical JSON, strict field/row validation and recomputation of expected results from data, using only fixed application-owned SQL/code snippets.
- [ ] Run `pytest -q tests/test_french_database_contract.py`; expected all pass.
- [ ] Commit contract and tests.

### Task 2: Finite French catalogue and structured binding

**Files:**
- Create: `Backend/Core/france/database_prose.py`
- Create: `Backend/Core/france/database_binding.py`
- Create: `tests/test_french_database_prose.py`

**Interfaces:**
- Consumes: Task 1 contract and its expected results.
- Produces: `database_selection_schema(contract: DatabaseContract) -> dict`, `validate_database_selection(contract: DatabaseContract, selection: dict) -> dict`, `render_database_candidate(contract: DatabaseContract, selection: dict, task_specs: list) -> dict`, and catalogue version/digest.

- [ ] Write failing tests for every advertised ID, exact six tasks/credit, printed relational materials and fixed SQL/code, unknown/extra/free-text IDs, and computed answer/rubric agreement.
- [ ] Run `pytest -q tests/test_french_database_prose.py`; expected missing module or function failure.
- [ ] Implement finite scene/question/rubric templates and strict validation; bind only contract values and existing blueprint credit.
- [ ] Run focused tests; expected all pass.
- [ ] Commit renderer, binder and tests.

### Task 3: Checkpointed v13 generation and replay

**Files:**
- Create: `Backend/Core/france/database_authoring.py`
- Modify: `Backend/Core/france/pipeline.py`
- Modify: `tests/test_nsi_pipeline.py`
- Create: `tests/test_french_database_authoring.py`

**Interfaces:**
- Consumes: Task 1 contract and Task 2 schema/renderer.
- Produces: explicit v13 generation mode with hash-bound selection, replay and old-version compatibility.

- [ ] Write failing tests for one bounded model selection, rejected attempts retained, changed contract/catalogue resume rejection, v13 replay tamper rejection and v10–v12/UK unchanged behavior.
- [ ] Run focused tests; expected assertions fail on missing v13 support.
- [ ] Implement v13 opt-in and checkpoint identities without modifying historical E1 or older readers.
- [ ] Run focused tests; expected all pass.
- [ ] Commit authoring, pipeline and tests.

### Task 4: PDF integrity, qualification and release

**Files:**
- Modify: `Backend/Core/france/runtime.py`
- Modify: `tests/test_french_runtime.py`
- Modify: `docs/quality/french-nsi-v13-live-diagnostic-2026-10-07.md`
- Modify: `docs/occitanie-project.md`
- Modify: relevant inventory/ledger files.

**Interfaces:**
- Consumes: v13 bound Exercise 2 and rendered standard/large-print PDFs.
- Produces: extraction gate for printed tables, code, prompts, answers and credit, plus a new pinned live diagnostic.

- [ ] Write failing PDF-mutation tests for a missing row, faulty SQL/code, question or mark; test both sizes.
- [ ] Run focused tests; expected integrity failures are initially missed.
- [ ] Implement v13 extraction checks; retain E1 checks and explicit non-official labels.
- [ ] Run focused tests and full suite; expected pass.
- [ ] Run a pinned local live diagnostic only for the changed French route; preserve all failed attempts and inspect every output page against the official visual comparator. Do not start the final shared-source matrix while Exercise 3 changes.
- [ ] Update Graphify, inventory and honest evidence docs; request fresh whole-branch review, then protected PR checks before merge.
