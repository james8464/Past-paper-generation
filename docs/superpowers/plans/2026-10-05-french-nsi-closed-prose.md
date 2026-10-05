# French NSI Closed-Prose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the session-2027 graph/tree exercise's printable French text exclusively app-rendered from immutable, versioned facts and bounded model selections, while retaining exact replay of older packages.

**Architecture:** Introduce a pure controlled-language catalogue/renderer, then route only new graph/tree A/B/C authoring and targeted repair through selection-only JSON. Bind and replay the rendered candidate with a new prompt/prose version and template digest; leave v10/v11 readers and every other route on their existing path. Verify both package evidence and extracted PDFs against the same rendered contract.

**Tech Stack:** Python 3, Pydantic, pytest, PyMuPDF/Poppler PDF checks, existing Ollama JSON transport, Graphify, GitHub protected PR checks.

**Spec:** `docs/superpowers/specs/2026-10-05-french-nsi-closed-prose-design.md`

## Global Constraints

- Work in the existing `french-nsi-integrity` managed worktree and draft PR #33. Preserve user changes, failed attempts, old packages and UK route IDs. Use `apply_patch`, TDD, small reviewed commits, and `graphify update .` after code changes.
- `CONTRACT_PROMPT_VERSION` v11 remains a historical reader. Name a distinct v12 generation version and `prose_contract_version`; do not silently migrate any v10/v11 artifact. Version/digest mismatches fail closed.
- Do not allow model text to become a title, context, question, answer, criterion, printed code, or PDF metadata that looks like subject content. Rejected raw JSON, its hash, prompt hash and run identity remain recoverable. Do not silently sanitize it into acceptance.
- All credits use exact decimal arithmetic and retain the six locked question totals and 18+2 full-paper policy. The controlled slice remains written-only, provisional and non-official.
- Do not run the expensive final UK/French model matrix while shared French source changes. The first source-pinned live diagnostic is a later gate; teacher review, learner calibration, accessibility assessment and prize outcome are not automatable claims.

## Review Focus

| Adversarial input | Owning task and required test |
| --- | --- |
| False A–F adjacency in title, scene, instruction, or criterion | Task 1 renderer contains no model prose, Task 2 response rejects every free-text field |
| False graph generalisation or invented tree key | Task 1 renders only contract-derived facts; Task 3 compares exact rendered candidate |
| Unknown choice ID, unsupported scene/slot pairing, or extra key | Task 2 schema plus direct validator rejects before rendering and retains raw failure |
| Altered rubric credit or canonical answer | Task 1 exact-decimal rubric tests; Task 3 binding/replay rejects altered candidate |
| Changed catalogue/version, failed-attempt hash, or old package | Task 2 checkpoint and Task 3 package replay/legacy fixtures |

---

### Task 1: Pure versioned French renderer and deterministic rubric

**Files:** Add `Backend/Core/france/graph_tree_prose.py`; add `tests/test_french_graph_tree_prose.py`; read `Backend/Core/france/graph_tree_contract.py`, `graph_tree_binding.py`, `archetypes.py`, `nsi.py` for the existing exact facts and field names.

**Interfaces:** Export `PROSE_CONTRACT_VERSION`, `prose_catalogue_digest()`, `selection_schema(part)`, `validate_selection(part, selection, task, contract)`, and `render_graph_tree_candidate(task, contract, selections) -> dict`. Define typed, finite IDs for scene frame/slots, each task's question form and rubric form. The renderer owns title, context, six question prompts, canonical answers, verification, materials references and criterion text; choices cannot carry printable strings.

- [ ] Add RED tests for at least two valid scene/wording combinations, all six task IDs and varied seeds. Assert printed words contain only catalogue text and contract-derived values; no model-provided factual prose reaches candidate fields. Include all four false A–F adjacency locations, false generic graph property and invented tree key as rejected selection payloads.
- [ ] Add RED tests for each task's locked points and exact `Decimal` rubric sums, with separately checkable clauses for 1b, 1c, 1e and 1f. Assert 1a–1f answers and code/API values derive from the contract, not selection data.
- [ ] Run `pytest -q tests/test_french_graph_tree_prose.py` and record the expected RED failures.
- [ ] Implement the finite catalogue as immutable data and deterministic render functions; canonicalise its data for a stable SHA-256 digest. Keep questions imperative/interrogative and avoid new factual premises. Do not reuse the current unrestricted `title/context/prompt/marking` model fields.
- [ ] Run the focused tests GREEN, then `graphify update .`; inspect the diff and commit renderer/tests as one small commit.

### Task 2: Selection-only A/B/C authoring, checkpoint and repair

**Files:** `Backend/Core/france/graph_tree_authoring.py`, `provider.py`, `question_review.py`; `tests/test_french_graph_tree_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** Add new v12-specific `part_selection_schema(part)` and `part_selection_prompt(...)` alongside the existing v11 functions. A accepted part stores only exact task IDs/results and finite choices; part A additionally stores scene/slot choices. Add `author_closed_prose_parts(...)` and `replay_closed_prose_parts(...)` returning the same candidate/evidence shape expected by the pipeline, with `prose_contract_version` and `prose_catalogue_sha256` in checkpoint identity. Add targeted `apply_closed_prose_repair(...)` that changes only the rejected task's selections and preserves peers/scene. Keep v11 functions intact for replay.

- [ ] Add RED transport tests: extra printable string in every response location, unknown IDs, wrong locked claim, changed point, malformed slot pair and incomplete two-question part all fail closed. Confirm the exact raw failed response/hash, prompt hash and run identity survive retry or cancellation.
- [ ] Add RED resume/replay tests: accepted A survives failed B; a retry adds rather than erases failure; tampered accepted/failed hash, prompt, model digest, template digest or version rejects; A/B/C rebuild identical rendered candidate. Include a targeted repair test proving untouched questions and scene are byte-identical.
- [ ] Run focused tests to observe RED. Implement separate v12 schema/prompt/checkpoint/repair paths; wire the provider's JSON format selection by requested version without changing v11 format or legacy routes. Keep the alignment reviewer diagnostic untrusted and require an exact choice-only repair response.
- [ ] Run focused tests GREEN, `graphify update .`, inspect diff and commit.

### Task 3: Bind, package and replay v12 evidence without legacy migration

**Files:** `Backend/Core/france/graph_tree_binding.py`, `pipeline.py`, `source_identity.py` if identity helpers require it, `runtime.py`; `tests/test_nsi_pipeline.py`, `tests/test_french_graph_tree_contract.py`, `tests/test_french_runtime.py`.

**Interfaces:** Introduce an explicit v12 dispatch constant (do not reassign the meaning of v11). `generate_assessment(..., contract_graph_tree=True)` uses v12 selection authoring and stores prompt/prose/catalogue identities in package manifest, binding and exercise evidence. `validate_package` dispatches v12 to selection replay and exact re-render/hash comparison, v11 to existing `replay_graph_tree_evidence`, and v10/other legacy versions to their present readers.

- [ ] Add RED tests for altered title/context/prompt/answer/criterion/credit, false graph or tree facts, changed template digest/version, corrupted targeted repair, and missing provenance. Verify each fails package validation even if top-level hashes are recomputed by the adversary.
- [ ] Add RED compatibility fixtures/tests for one existing v11 graph/tree package, one v10 French package and representative UK route IDs/saved state; they must read under their original version without a new prose identity. Test a new v12 package has all required identities and no route ID changes.
- [ ] Run focused RED tests. Implement v12 dispatch, binding and evidence replay; compare every rendered field and exact `Decimal` rubric credit, not merely a result hash. Do not weaken v11 verification or silently accept a v12 claim in v11 format.
- [ ] Run focused tests GREEN and broader `pytest -q tests/test_nsi_pipeline.py tests/test_french_runtime.py`; update Graphify, inspect diff and commit.

### Task 4: Extracted-PDF content, visual layout and reference comparison

**Files:** `Backend/Core/france/runtime.py`, relevant French PDF renderer under `Backend/Core/france/`, `tests/test_french_runtime.py`, PDF QA notes under `docs/quality/`. Use the `pdf:pdf` skill before inspecting or editing PDFs.

**Interfaces:** Extend `validate_contract_pdf(...)` or a v12-specific wrapper with the rendered exercise and document kind. For both standard and large print, require every graph endpoint/weight, tree cell, code/API, question instruction, answer only in correction, and exact rubric clause/credit to be extractable. Missing or ambiguous extraction is failure, not a pass.

- [ ] Add RED tests that mutate or omit a graph weight, tree key, question instruction, answer location or rubric credit in the extracted PDF; assert publication blocks. Test standard and large-print subject/correction pairs separately.
- [ ] Run RED. Implement exact text/fact checks and fix any proven layout defect in the existing generator without changing official/non-official labels. Keep source/correction separation and accessible text order.
- [ ] Run tests GREEN. Render every generated page, inspect visually with the PDF skill against current relevant official NSI references, and record page-level observations plus remaining limitations. Compare typography, hierarchy, spacing, contrast, page breaks and answer leakage; do not claim official endorsement.
- [ ] Update Graphify after code changes, inspect diff and commit.

### Task 5: Qualification, evidence and protected integration

**Files:** `tests/test_french_benchmark_runner.py`, existing benchmark harness if changed, `docs/quality/french-nsi-prototype-verification-2026-09-28.md`, reference/live-fidelity ledger, `docs/occitanie-project.md`, `Resources/repository-inventory.json`; only modify files needed by demonstrated evidence.

- [ ] Exercise the selection authoring path under pinned seed/model/source identities in fast fixtures first, including originality against eligible references and previous generated work; preserve all rejected attempts and accepted checkpoints. Do not relabel previews as live generations.
- [ ] Run the full local suite and exact repository inventory; run `graphify update .` after the last code change. Inspect working tree, package replay, UK compatibility and all French routes. Obtain independent code review and repair concrete findings with new RED tests before claiming source freeze.
- [ ] Update the English application/report and quality ledger with honest measured evidence, current prototype limitations, official-source/corpus rights and holdout gaps, and explicit teacher/learner/accessibility/personal-detail gates. Keep “Sujet d’entraînement — non officiel” and “Corrigé proposé et barème indicatif”; do not claim practical-exam support, reviewers, partnerships, Apple approval or prize certainty.
- [ ] Commit in reviewable increments, push to draft PR #33, wait for protected backend/macOS checks and review. Merge only under normal protected workflow; verify main and clean worktree. Keep issues #4 and #8 open until actual qualification.
- [ ] Only after source freeze and protected acceptance, run one pinned live graph/tree diagnostic, inspect every PDF with the PDF skill, and record a go/no-go decision. If the slice is stable and other French source is frozen, run the previously approved shared UK-plus-French live matrix with pinned source/model/artifact identities. Human gates remain outstanding even if automation passes.

## Plan Self-Review

The tasks cover each design boundary: finite render choices, raw rejection evidence, versioned checkpoint/binding/package replay, extracted and visual PDF checks, historical compatibility, and qualification gates. Their interfaces keep v11 readers separate from v12 generation. Each mutation begins with a failing test and ends with focused verification, Graphify update and a reviewable commit. The plan intentionally stops short of calling a live model result, teacher validation, accessibility approval or prize submission complete.
