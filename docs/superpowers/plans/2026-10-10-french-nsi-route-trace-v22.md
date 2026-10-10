# French NSI route-trace V22 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Exercise 1 a staged, original before/after link-outage route investigation with candidate Dijkstra working tables and a causal debug-then-trace sequence.

**Architecture:** Keep V13–V21 contracts and prose immutable. Add a V22-only V5 graph/tree contract and finite French catalogue; then add explicit selection, pipeline, runtime, PDF and benchmark dispatch. Stage the graph, baseline table, faulty code, outage table and tree before the questions that use them. Retain V21 Exercise 2 and V18 Exercise 3.

**Tech Stack:** Python 3, Pydantic, ReportLab, PyMuPDF, pytest, Ruff, Graphify.

**Spec:** `docs/superpowers/specs/2026-10-10-french-nsi-route-trace-v22-design.md`

## Global Constraints

- Written Terminale NSI session 2027 only: three independent exercises, 210 estimated minutes, exactly 18 technical plus a distinct two indicative French-language points; no practical component.
- Exercise 1 has 1a–1j, 70 estimated minutes and exact `Decimal` V20 5.5/6/6.5 point profiles. The re-ordered 1e/1f prompts and every criterion must agree.
- V13–V21 and UK package/state replay remain unchanged. Unknown or mixed V22 identity fails closed.
- French-only eligible references, holdout isolation, no UK fallback or model-executed code, local privacy and non-official PDF labels stay unchanged.
- Fixtures and automated passes are provisional; teacher, learner, rights and accessibility reviews are external gates. Defer the final UK/French matrix while source changes or manual fidelity holds.

## Review Focus

- The V5 closed edge is not the baseline route's first edge or disconnects the graph: test multiple seeds, post-closure reachability, route change and nondecreasing cost.
- Post-closure trace accidentally reuses baseline distances or predecessors: test distinct first fixation and separately derived two-row states for both graphs.
- Dijkstra working cells disclose expected values or appear after dependent prompts: test blank normal/large candidate tables, titles, order and phase/question association.
- The fixed BFS program is requested before the fault is identified, or 1e/1f credits test unstated evidence: test prompt sequence, trusted-code identity, answer/criterion mapping and exact profiles.
- V21/older packages accidentally acquire V22 facts or the correction loses answer/credit attribution: test version-isolated replay, all three exercise totals, subject exclusion and page bounds.

---

### Task 1: Immutable V5 route facts and finite French prose

**Files:** Create `Backend/Core/france/graph_route_trace_contract.py`, `Backend/Core/france/graph_route_trace_prose.py`; test `tests/test_french_graph_route_trace_contract.py`, `tests/test_french_graph_route_trace_prose.py`.

**Interfaces:** `GraphRouteTraceContract.from_dict(data: dict) -> GraphRouteTraceContract`, `build_graph_route_trace_contract(seed: int) -> GraphRouteTraceContract`, `to_dict() -> dict`, `digest: str`; `graph_route_trace_catalogue_digest() -> str`, `graph_route_trace_selection_schema(contract) -> dict`, `validate_graph_route_trace_selection(contract, selection) -> None`, `render_graph_route_trace_candidate(contract, selection, task_specs) -> dict`.

- [ ] Write failing contract tests for the first baseline-route edge closure, two before/after Dijkstra fixation rows, distinct first row, independent shortest route/cost, multiple seeds and canonical rejection of changed graph, edge, trace, answer or seed. Run RED.
- [ ] Implement immutable V5 facts using the existing trusted graph and route algorithms but without changing V4. Run focused tests GREEN and Ruff.
- [ ] Write failing finite-prose tests for 1a–1j, 70-minute sum, all three exact point profiles, native French before/after prompts, corrected 1e→1f dependency, blank phase-labelled tables, and evidence-matched answers/credits. Run RED.
- [ ] Implement the minimal finite catalogue and staged materials. Run focused tests GREEN, review Task 1 and commit only its files.

### Task 2: V22 selection and version-isolated replay

**Files:** Create `Backend/Core/france/graph_route_trace_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_graph_route_trace_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `graph_route_trace_selection_prompt(task, contract, references) -> str`, `author_graph_route_trace_selection(client, task, contract, references, path, *, run_identity) -> tuple[dict, dict]`, `replay_graph_route_trace_selection(task, contract, references, evidence, *, run_identity) -> dict`; `_tasks_for_seed_v22(seed: int) -> list[dict]` retains E2/E3 and the exact paper total.

- [ ] Write failing tests for finite selection IDs, seed/profile identity, three independent exercises, 18+2 points, hash-bound V22 checkpoint/package replay and rejection of altered V5 facts, prose, source index, prompt or reference. Replay representative V13–V21 and UK packages. Run RED.
- [ ] Implement explicit V22-only provider and pipeline branches with no fallback to V21 and no earlier identity changes. Run focused tests GREEN and Ruff; review and commit Task 2.

### Task 3: Runtime, staged PDFs and deterministic gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; test French runtime/PDF/benchmark modules.

**Interfaces:** Runtime advertises V22 only for current French written generation. `validate_graph_route_trace_pdf(...)` binds graph, closure, baseline/outage tables, faulty code, tree, 1a–1j and exact answer/credit to one V22 identity; older validators stay intact.

- [ ] Write failing tests for explicit V22 runtime/benchmark dispatch and V21 replay; missing, filled, swapped or misplaced tables; changed link/title/phase; wrong 1e/1f question order; answer leakage; normal/large bounds; and correction answer/credit grouping. Run RED.
- [ ] Implement minimal V22 staging and fail-closed PDF checks while preserving older paths. Run focused tests GREEN, then full pytest, Ruff, hygiene/compliance and diff checks.
- [ ] Run `graphify update .`, refresh repository inventory, review Task 3 and commit its files.

### Task 4: Visual review, protected merge and measured checkpoint

**Files:** Update English diagnostic and Occitanie evidence only after a pinned live result; never call a fixture live.

- [ ] Render normal and large-print V22 fixture subject/correction PDFs. Inspect every generated page and all official 2026 Métropole pages with the PDF skill; fix material defects test-first, retain any manual depth/working-space hold and do not pad pages.
- [ ] Run full pytest, Ruff, hygiene/compliance, Graphify/inventory and diff checks. Obtain a fresh read-only whole-branch review and fix important findings test-first. Open and attach a protected PR; merge only after Backend/macOS checks pass, then fast-forward clean main.
- [ ] Run exactly one source/model/reference-pinned French live diagnostic after engineering merge. Retain every attempt and artifact hash, inspect every generated page against the official comparator, and publish exact measured English HOLD/PASS evidence and honest Occitanie update through protected checks. Keep the final UK/French matrix deferred until source freezes and manual fidelity passes.
