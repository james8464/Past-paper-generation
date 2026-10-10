# French NSI graph resilience V20 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Exercise 1 a staged, original graph-resilience and tree-reasoning case without changing earlier French or UK packages.

**Architecture:** Freeze V17–V19 graph/tree facts and prose; add a V20-only immutable resilience contract and finite French question catalogue. Versioned selection, pipeline, runtime and PDF gates bind those facts to candidate material at the point of use. Exercises 2 and 3 retain V19 behaviour.

**Tech Stack:** Python 3, Pydantic, ReportLab, PyMuPDF, pytest, Ruff, Graphify.

**Spec:** `docs/superpowers/specs/2026-10-10-french-nsi-graph-resilience-v20-design.md`

## Global Constraints

- Written Terminale NSI session 2027 only: three independent exercises, 210 estimated minutes, exactly 18 technical plus a distinct two indicative French-language points; no practical component.
- Exercise 1 has 1a–1j, 70 estimated minutes and exact `Decimal` 5.5/6/6.5 allocations from the spec; prompts and criteria must match the evidence asked.
- V13–V19 and UK package/state replay remain unchanged; unknown or mixed V20 identity fails closed.
- French-only cleared references, holdout isolation, no UK fallback or model-executed code, local privacy and non-official PDF labels remain unchanged.
- Fixtures and automated passes are provisional; teacher, learner, rights and accessibility review are external gates. Final UK/French matrix stays deferred while source changes or manual fidelity is on hold.

## Review Focus

- A closed edge lies on a different or tied route: test the selected canonical edge against the recomputed path, including equal before/after weights and no remaining closed edge.
- A question asks for more graph or BFS facts than its quarter-point criteria award: test each prompt against exact 5.5/6/6.5 credit evidence.
- A V19 package is silently replayed with V20 facts or text: assert old content/hash identity remains unchanged and mixed V20 evidence fails closed.
- Tree/search material appears before 1a or after its dependent question: test staged association and missing/interchanged source rejection in normal and large print.
- Added material leaks an answer or strands a correction rubric: test subject exclusion, PDF bounds and answer-credit grouping, then visually inspect all pages.

---

### Task 1: Immutable V4 graph-resilience facts and finite prose

**Files:** Create `Backend/Core/france/graph_resilience_contract.py`, `Backend/Core/france/graph_resilience_prose.py`; test `tests/test_french_graph_resilience_contract.py`, `tests/test_french_graph_resilience_prose.py`.

**Interfaces:** `GraphResilienceContract` derives immutable V3 data for a seed and exposes canonical `to_dict()`, `digest`, `closed_edge`, `route_before`, `route_after`, `cost_before`, `cost_after` and BFS states. `graph_resilience_catalogue_digest() -> str`, `graph_resilience_selection_schema(contract) -> dict`, `validate_graph_resilience_selection(contract, selection) -> None`, `render_graph_resilience_candidate(contract, selection, task_specs) -> dict` expose only finite app-owned French scenes and exact answers/credits.

- [ ] Write failing seed-sweep tests: choose the middle edge of the canonical A–F shortest route, remove only that edge, recompute shortest routes by the V3 tie rule, require connectivity and changed route, and cover equal as well as unequal total costs. Assert canonical digest changes on any altered seed, edge, route, predecessor, BFS or tree fact.
- [ ] Run focused tests RED and confirm missing V4 interfaces/facts cause the failures.
- [ ] Implement V4 derivation without changing V3; do not execute model-provided code or adopt model facts. Run focused contract tests GREEN and Ruff.
- [ ] Write failing prose tests for all ten question IDs, native-French stage copy, exact spec credit profiles and 70-minute sum. Pin 1a degree-only, 1b detour-only, 1e BFS evidence consistent with its credit, and four quarter-point 1g criteria including honest equal-cost comparison.
- [ ] Run prose tests RED, implement the finite catalogue and deterministic answer/rubric derivation, then run GREEN. Review and commit Task 1.

### Task 2: V20 selection, identity and old-package isolation

**Files:** Create `Backend/Core/france/graph_resilience_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_graph_resilience_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `graph_resilience_selection_prompt(task, contract, references) -> str`, `author_graph_resilience_selection(client, task, contract, references, path, *, run_identity) -> tuple[dict, dict]`, `replay_graph_resilience_selection(task, contract, references, evidence, *, run_identity) -> dict`; `_tasks_for_seed_v20(seed: int) -> list[dict]` preserves E2/E3, time and exact total.

- [ ] Write failing tests for V20 generation, 18+2 scoring, three independent exercises, E1 70 minutes, finite scene/wording IDs and hash-bound selection/checkpoint replay. Reject extra IDs, wrong order, tampered V4 facts, changed catalogue/prompt/reference hashes and mismatched version; replay representative V13–V19 and UK packages.
- [ ] Run focused tests RED; implement explicit V20 provider/schema and pipeline branches with no fallback to V19. Keep earlier version fields and identity untouched.
- [ ] Run focused tests GREEN and Ruff; review and commit Task 2.

### Task 3: Runtime and staged PDF publication gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; add focused runtime/PDF/benchmark tests to existing French test modules.

**Interfaces:** Runtime advertises V20 only for current French written generation. `validate_graph_resilience_pdf(...)` checks V4 printed facts, all 1a–1j prompts, stage/material association, subject answer exclusion and correction answer/credit identity; existing V3 PDF gate continues to validate V17–V19 unchanged.

- [ ] Write failing tests for explicit runtime and benchmark V20 dispatch, old V19 replay, missing/interchanged candidate graph/BFS/outage/tree/search sources, phase adjacency, 1a–1j presence, normal/large-print bounds and no answer leakage. Require the answer and rubric for each question to stay attributable together.
- [ ] Run focused tests RED; implement minimal V20-only staged material rendering and strict PDF gate. Do not add blank pages or weaken earlier validators.
- [ ] Run focused tests GREEN, then full pytest, Ruff, hygiene/compliance and diff checks. Run `graphify update .`, refresh repository inventory and review/commit Task 3.

### Task 4: Visual review and protected qualification checkpoint

**Files:** Update measured English evidence and Occitanie claims only after an actual pinned live result; no fixture is called live.

- [ ] Render normal and large-print V20 fixture subjects/corrections. With the PDF skill inspect every generated page against all official 2026 Métropole pages; fix material defects test-first and record remaining depth/page-flow gaps without treating page count as the sole goal.
- [ ] Run full pytest, Ruff, hygiene/compliance, Graphify/inventory and diff checks. Obtain fresh read-only whole-branch review; resolve important findings test-first. Open and attach a protected PR; merge only after Backend and macOS checks pass, then fast-forward clean main.
- [ ] Run one pinned French live diagnostic only after engineering merge. Preserve attempts and model/source/reference/artifact hashes; inspect every subject/correction page with the PDF skill and publish an exact measured HOLD/PASS in English. Do not start the expensive UK/French matrix until French source is frozen and manual fidelity passes.
