# Verifiable French NSI Exercises Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the French `graph-and-tree` exercise authorable from immutable, reproducible task data rather than asking a model to invent unverifiable graph/tree facts.

**Architecture:** A pure seeded contract supplies student-visible materials, node API, operations and canonical results. The model writes original French context and question prose around this contract; the pipeline assembles locked facts and verifies every bound question before AI review. Failed candidates and repairs remain hash-recorded. This is a first vertical slice, not a claim of whole-paper qualification.

**Tech Stack:** Python 3, Pydantic, pytest, existing Ollama bridge and PDF renderer.

**Spec:** `docs/superpowers/specs/2026-10-05-french-nsi-verifiable-exercises.md`

## Global Constraints

- French Terminale NSI written 2027 remains three independent exercises, 210 minutes, 18 technical points and a separate indicative two-point language component; no practical component.
- Preserve UK route IDs, packages, saved state, AO policy and active qualification evidence. Old French packages and failed checkpoints remain readable, not rewritten.
- No unsupported claim or unresolved deterministic check becomes a pass. Do not execute arbitrary generated Python or fall back to UK references/cloud inference.
- Keep original question wording, non-official branding, exact decimal points, French-only rights-filtered retrieval, holdout isolation and hash-bound provenance.
- No final model matrix while source changes. Protected PR checks, Graphify and inventory must be current before merge.

## Review Focus

1. A graph question mentions an edge not in the locked figure: the candidate must fail even if an AI reviewer approves it (Task 2 test).
2. A solution calls `Noeud(...)` without the constructor being printed for students: fail before solver/review (Task 2 test).
3. A tree key or traversal answer contradicts the locked tree: fail, not silently replace the model's answer (Task 2 test).
4. An interruption after one accepted exercise: resume only at the identical source/contract/model/reference identity (Task 3 test).
5. A contract change after PDF export: package replay and artifact hashes must reject the stale document (Task 4 test).

---

### Task 1: Seeded graph/tree contract

**Files:**
- Create: `Backend/Core/france/graph_tree_contract.py`
- Test: `tests/test_french_graph_tree_contract.py`

**Interfaces:**
- Produce `build_graph_tree_contract(seed: int, exercise_id: str) -> GraphTreeContract` with a stable `to_dict()` representation and SHA-256 digest.
- Contract owns `reseau` (weighted graph), `arbre` (`cle`, `gauche`, `droite` table), a student-visible `Noeud` API, six task IDs and canonical graph/tree results. It does not own prose or marking. Tie-breaking is alphabetical.

- [ ] Write failing tests for repeatability, seed variation, connected graph, BST ordering, deterministic shortest path, alphabetically ordered BFS and tree insertion/search trace. Include a tampered-edge and duplicate-key rejection test.
- [ ] Run `.venv/bin/python -m pytest tests/test_french_graph_tree_contract.py -q`; confirm the new tests fail for the missing interface.
- [ ] Implement the pure contract with bounded dataset sizes, explicit tie-breaking and no generated-code execution. Serialize only JSON-compatible primitives; derive results from those primitives.
- [ ] Run the focused tests and Ruff; commit this independently testable unit.

### Task 2: Locked materials and semantic binding

**Files:**
- Modify: `Backend/Core/france/pipeline.py`
- Modify: `Backend/Core/france/nsi.py` only if a new structured tree material is required; prefer the existing table material when it can print every parent/child relation unambiguously.
- Test: `tests/test_nsi_pipeline.py`

**Interfaces:**
- Consume `GraphTreeContract.to_dict()` from Task 1 at `_tasks_for_seed(seed)` and `_prepare_candidate(...)`.
- Produce `contract_binding` evidence containing contract digest, task IDs, locked material hashes, model `claimed_result` and canonical result hashes; package replay verifies it. Raw `contract_task_id` and `claimed_result` are stripped only for assembly into the legacy `NSIQuestion` schema, never from evidence.

- [ ] Add failing fixtures from the three preserved Gemma attempts: undefined `Noeud`, a claimed graph edge absent from the figure, and incorrect BFS order. Add a positive fixture with the exact printed constructor and correct route/tree values.
- [ ] Run the named focused tests RED. Establish that the current pipeline either accepts a false claim or lacks contract binding.
- [ ] Assemble the `reseau` graph and `arbre` table from the contract, never model-supplied vertices/weights/keys. Put the `Noeud` API in student-visible context. Require each of the six question IDs to bind to its planned contract task and exact structured `claimed_result`. Reject mismatched claims and verification values; compose the canonical final result separately and preserve the raw answer/marking for audit.
- [ ] Re-run the full affected exercise checks after every repair. Assert old package versions still validate under their pinned identities. Run focused tests GREEN, then commit.

### Task 3: Model-facing part authoring and resumable evidence

**Files:**
- Modify: `Backend/Core/france/pipeline.py`
- Modify: `Backend/Core/france/question_review.py`
- Modify: `Backend/Core/france/runtime.py` only if the existing provider response schema cannot express the part/repair prompt.
- Test: `tests/test_nsi_pipeline.py`
- Test: `tests/test_french_runtime.py`

**Interfaces:**
- Consume immutable contract tasks from Tasks 1–2. Keep `generate_assessment(...)` return and French package schema compatible.
- Produce hash-linked raw part candidates, bounded repairs, assembled exercise and explicit failed-attempt records.

- [ ] Add a fake-client RED test proving a one-question repair cannot alter locked data, plan metadata, other questions or the contract; cancellation preserves the draft and does not publish.
- [ ] Split the model's graph/tree authoring into coherent A/B/C part prompts, each including only the locked task facts it needs. A response that invents facts is rejected. Keep no canned-question fallback.
- [ ] Verify exact provider transport for every new prompt type. Re-run structural, contract, originality, independent-solver and review gates on the assembled exercise; keep failed evidence. Run focused tests GREEN and commit.

### Task 4: Replay, PDF and end-to-end qualification gate

**Files:**
- Modify: `Backend/Core/france/pipeline.py`
- Modify: `Backend/Core/france/rendering.py` only if the locked node API/tree cannot be read clearly in the existing renderer.
- Test: `tests/test_nsi_pipeline.py`
- Test: `tests/test_french_rendering.py`
- Update: `docs/quality/french-nsi-evaluation.md`
- Update: `docs/quality/french-nsi-manual-comparison-2026-10-04.md` only after a complete new PDF exists.

**Interfaces:**
- Checkpoint/package identity adds the contract version and digest; a saved package re-derives all canonical facts and rejects tampering.
- Preserve the existing `unreviewed_draft` and hash-bound teacher-review states.

- [ ] Add RED tests for changed contract digest, changed printed tree/graph, stale checkpoint, false canonical answer and broken artifact hash; assert no partial PDF publication.
- [ ] Implement fail-closed replay, PDF extraction checks for all printed graph/tree facts and node API, and explicit unresolved states for claims outside deterministic coverage.
- [ ] Run focused suite, full Python suite, Ruff, macOS build/release checks if rendering or app resources changed, Graphify update and inventory. Commit and request independent review.
- [ ] Merge only after exact-head protected checks pass. Then run one new pinned live diagnostic (not a preview); preserve failures. If it produces a complete PDF, inspect every page and every question/solution/credit against the official historical paper using the PDF skill. Record exact result and remaining human gates before expanding to database/network contracts or the full matrix.
