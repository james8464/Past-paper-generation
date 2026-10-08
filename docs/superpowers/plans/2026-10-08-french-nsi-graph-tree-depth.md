# French NSI graph/tree depth implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the current original French graph/BST exercise ten deterministic, multi-step questions without changing saved V16 and earlier papers.

**Architecture:** V17 keeps the seeded graph and tree facts but binds them to a new immutable depth contract and finite French prose catalogue. Explicit version dispatch changes only Exercise 1; V16 Exercise 2 and V15 Exercise 3 remain pinned. A new verifier checks printed V17 facts and credits, while older handlers retain their old identities.

**Tech Stack:** Python 3, Pydantic, ReportLab, PyMuPDF, pytest, Ruff, Graphify; protected Backend and macOS CI.

**Spec:** `docs/superpowers/specs/2026-10-08-french-nsi-graph-tree-depth-design.md`

## Global constraints

- Terminale NSI session 2027 written component only; three independent exercises and 210 estimated minutes.
- Exact 18 technical points plus distinct two-point indicative language component; E1 totals 5.5, 6 or 6.5 by existing allocation.
- V16 and earlier French contracts, prompt identities, packages and replay remain readable; all UK routes/state/packages unchanged.
- French-only scoped sources; no UK/cloud fallback, no model-authored executable code, no holdout leakage.
- Native French, original exercise content, non-official subject and proposed-correction labels.
- Preserve all previous live/failure artifacts and hashes. Do not start the expensive final matrix while source changes.
- Automated results do not imply teacher, examiner, learner, rights or accessibility approval.

## Review focus

- A seeded graph yields a tied shortest route: record the deterministic tie rule, and test derived trace/path consistency over a seed range.
- A code-typo question exposes the correction in candidate context: test that only fixed faulty code is printed and the subject contains no solution fragment.
- A ten-question selection is missing/reordered/duplicated: reject it before any candidate publication.
- V17 package validation silently dispatches to V16 six-question code: require exact version/digest and fail closed on mismatches, while replaying a saved V16 fixture unchanged.
- A long Dijkstra/BFS rubric creates clipped text or a mostly blank page: measure PDF bounds and inspect normal/large-print output; reject or adjust only an observed defect.

---

### Task 1: Immutable depth contract and expected results

**Files:** Create `Backend/Core/france/graph_tree_depth_contract.py`; test `tests/test_french_graph_tree_depth_contract.py`.

**Interfaces:** `GraphTreeDepthContract.from_dict(data: dict) -> GraphTreeDepthContract`, `build_graph_tree_depth_contract(seed: int) -> GraphTreeDepthContract`, `to_dict() -> dict`, `digest -> str`. The canonical JSON has `version: 3`, `seed`, `exercise_id: "1"`, `task_ids: [1a…1j]`, base graph/tree and fixed faulty BFS/BST-search code, and deterministic `expected` keyed by all ten IDs. `from_dict` recomputes from seed and rejects changed content.

- [ ] Write failing tests for seed determinism, ten IDs, hand-checked A–C–E–F detour sum, Dijkstra first two settled rows/predecessors, BFS first two queue states, typo and insertion/inorder/search correction, and tampered content/seed rejection.
- [ ] Run focused tests RED.
- [ ] Implement the V3 constructor using only fixed app-owned snippets and algorithms; leave the V2 contract untouched.
- [ ] Run focused tests GREEN and existing V2 tests; review and commit Task 1.

### Task 2: Finite French ten-question selection and rendering

**Files:** Create `Backend/Core/france/graph_tree_depth_prose.py`, `Backend/Core/france/graph_tree_depth_authoring.py`; update `Backend/Core/france/provider.py`; test `tests/test_french_graph_tree_depth_authoring.py`.

**Interfaces:** `graph_tree_depth_selection_schema(contract) -> dict`, `validate_graph_tree_depth_selection(contract, selection) -> dict`, `render_graph_tree_depth_candidate(contract, selection, task_specs) -> dict`, `author_graph_tree_depth_selection(...) -> tuple[dict, dict]`, `replay_graph_tree_depth_selection(...) -> dict`. Only finite scene/form IDs cross the model boundary; the catalogue digest binds exact question/answer/rubric text.

**Locked blueprint:** 1a–1j minute estimates `(6,6,8,7,8,7,7,7,7,7)` sum to 70. Every question has 0.5 point; 1c gets +0.5 for all allocations, 1e gets +0.5 at 6 or 6.5, and 1j gets +0.5 at 6.5. Parts are `AAAABBBCCC`; all rubric criteria are exact quarter-point units.

- [ ] Write failing tests for ten stable labels, three parts, exact 5.5/6/6.5 sums and 70-minute total, native French prompts, expected answers, quarter-point rubrics, invalid form IDs, wrong claims, evidence hashes and replay.
- [ ] Run focused tests RED.
- [ ] Implement finite original prose/selection/replay and explicit fixture-provider schema dispatch for V17; never fall back to an older schema.
- [ ] Run focused tests GREEN, Ruff and review/commit Task 2.

### Task 3: V17 route, verifier, package identity and compatibility

**Files:** Modify `Backend/Core/france/pipeline.py`, `Backend/Core/france/runtime.py`, `Backend/Core/france/verification.py`, `Backend/Core/france/graph_tree_binding.py` only if a shared helper is necessary; test `tests/test_nsi_pipeline.py`, `tests/test_french_runtime.py`, `tests/test_french_benchmark_runner.py`.

**Interfaces:** `_tasks_for_seed_v17(seed: int) -> list[dict]` replaces only E1's blueprint; `generate_assessment(..., contract_authoring_version="v17")` is explicit internally; current French written runtime selects V17. `validate_graph_tree_depth_contract_pdf(...)` verifies all printed V17 facts, answer values and per-question credit without V2 fallback. V17 package identity binds the new contract/catalogue digests; old package validation remains version-specific.

- [ ] Write failing tests for V17 three-exercise generation, ten E1 questions, 18+2 exact credit, wrong/missing printed facts and answer leakage, mixed identity rejection, V16 saved-package replay and UK route preservation.
- [ ] Run focused tests RED.
- [ ] Add explicit V17 dispatch, identity and verifier; do not alter V16's task builder or existing package artifacts.
- [ ] Run focused tests GREEN; review/commit Task 3.

### Task 4: PDF inspection, full verification and protected integration

**Files:** Touch `Backend/Core/france/rendering.py` only for observed V17 layout defects; update `Resources/repository-inventory.json` and `graphify-out/` after source changes; add measured English evidence only when available.

- [ ] Render normal and large-print fixture subjects and corrections, inspect every page with the PDF skill against the official 2026 Métropole comparator, and measure page bounds/density. Fix any observed clipping, orphan or leakage test-first; preserve prior evidence.
- [ ] Run full pytest, Ruff, repository hygiene and `git diff --check`; run `graphify update .` and include the graph/inventory changes.
- [ ] Obtain read-only code review, address important findings and make small reviewed commits.
- [ ] Open and attach a PR; merge only after protected Backend/macOS checks pass, then fast-forward clean main.
- [ ] After source freezes, run one pinned V17 live diagnostic, retain every attempt/hash, inspect every PDF page against the official reference and record an honest pass/hold. Teacher review, learner calibration, rights and accessibility remain external gates.
