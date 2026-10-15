# French NSI V25 two-outage E1 — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace only new French E1 packages with a connected two-outage graph case and useful route-working space, without changing earlier packages.

**Architecture:** A separate immutable V25 E1 contract derives and independently verifies the second outage. A finite French prose catalogue, explicit V25 authoring/package dispatch and PDF gate bind every printed edge, answer and credit; existing V24 E2 and V23 E3 stay unchanged.

**Tech Stack:** Python, pytest, ReportLab, Ruff, Graphify, protected GitHub PR.

**Spec:** `docs/superpowers/specs/2026-10-15-french-nsi-two-outage-e1-v25-design.md`

## Global Constraints

- Three independent Terminale NSI written exercises, 210 estimated minutes; E1 remains 70 minutes and 5.5/6/6.5 technical points by seed.
- Exactly 18 technical points plus a distinct 2-point indicative French-language component.
- V25 E1 keeps IDs `1a`–`1j`: old 1g route task becomes 1f (1 point), old 1f BFS trace is replaced by new 1g two-outage task (0.5 point), and 1h–1j retain tree work.
- E1 minutes for `1a`–`1j` are `(3,3,10,8,8,10,11,6,5,6)` and sum to 70; these are provisional until learner calibration.
- The second closed edge is the final edge of the first-outage minimum route; it is distinct from the first edge and not incident to A. A surviving A-to-F route must be proved by independent path enumeration.
- Strict French-only references, holdouts excluded, no UK fallback; non-official PDF labels.
- V13–V24 French and UK package/checkpoint replay unchanged. Never mutate V22 E1 contract or catalogue facts.
- No page-count padding or final UK/French matrix while manual French fidelity is HOLD. Preserve ignored evidence; no official PDF bundled.

## Review Focus

- A seed where the second closure leaves an equal-cost optimum must credit equality, not falsely require a higher cost; add a literal-seed test.
- A repeated or A-incident second edge, an unreachable survivor or a Dijkstra/simple-path disagreement must fail contract construction; add tamper and oracle tests.
- V25/V24 mixed identity, selection hashes or checkpoint evidence must fail closed; add replay tests.
- The second closure caption and blank working surface must precede only 1g, never leak the route or correction; add PDF tests.
- Normal and large-print E1 pages must keep each table with its dependent question and avoid clipping or orphaned credit; add PDF bounds tests and visual review.

---

### Task 1: Immutable second-outage facts and finite French wording

**Files:** Create `Backend/Core/france/graph_two_outage_contract.py`, `Backend/Core/france/graph_two_outage_prose.py`; test `tests/test_french_graph_two_outage_contract.py`, `tests/test_french_graph_two_outage_prose.py`.

**Interfaces:** `GraphTwoOutageContract.from_dict(data: dict)`, `build_graph_two_outage_contract(seed: int)`, `to_dict()`, `digest`; `graph_two_outage_catalogue_digest()`, `graph_two_outage_selection_schema(contract)`, `validate_graph_two_outage_selection(contract, selection)`, `render_graph_two_outage_candidate(contract, selection, task_specs)`.

- [ ] Write a RED contract test with hand-checked seed 270100: first closure `A–B`, first-outage route `A–C–D–E–F` at cost 26, second closure `E–F`, and surviving route `A–C–D–F` at cost 30; add seed-diversity, equal-cost and edited-edge rejection cases. Run focused pytest and confirm the expected missing-interface failure.
- [ ] Implement the smallest V25 contract using the existing V22 seeded graph only as input, with separate simple-path enumeration as oracle. Run focused tests green and Ruff.
- [ ] Write RED prose tests for `1a`–`1j`, first-closure work at 1f, second closure/cost/comparison at 1g, no BFS queue-trace task, exact credit totals and staged subject/correction surfaces. Confirm focused RED.
- [ ] Implement finite V25 wording, answer and quarter-point criteria; run focused tests green. Inspect diff, update Graphify/inventory and commit Task 1.

### Task 2: Selection and version-isolated generation

**Files:** Create `Backend/Core/france/graph_two_outage_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_graph_two_outage_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `author_graph_two_outage_selection(...)`, `replay_graph_two_outage_selection(...)`; `_tasks_for_seed_v25(seed: int)` returns V24 E2/V23 E3 unchanged and the V25 E1 blueprint.

- [ ] Write RED tests for finite provider response, contract/catalogue digest binding, exact `fr-nsi-written-2027-v25` identity, 70-minute E1 blueprint, 18+2 paper credit, mixed-version rejection and V13–V24/UK replay. Confirm focused RED.
- [ ] Add explicit V25 provider/pipeline/replay branches without changing old branches. Run focused tests and Ruff; inspect diff, update Graphify/inventory and commit Task 2.

### Task 3: Runtime, PDF and benchmark gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; test `tests/test_french_runtime.py`, `tests/test_french_benchmark_runner.py`, `tests/test_french_graph_two_outage_pdf.py`.

**Interfaces:** V25 runtime dispatch only for new packages; `validate_graph_two_outage_pdf(...)` binds the two closures, 1f/1g materials, answer/credit and digest to the rendered PDF.

- [ ] Write RED tests for omitted/swapped second closure, wrong route/cost/comparison, answer leakage, wrong material order, score drift, normal/large-print page bounds and V24 replay. Confirm focused RED.
- [ ] Implement fail-closed runtime/rendering/verification/benchmark routing and a candidate route-working surface associated with 1g. Run focused and full pytest, Ruff, hygiene, Graphify update and inventory; inspect diff and commit Task 3.

### Task 4: Visual qualification and protected publication

**Files:** Add measured English evidence only after a pinned live run; preserve fixture and live artifacts in ignored paths.

**Interfaces:** Existing PDF renderer; pinned `gemma4:12b` seed 270100 and locked French reference index.

- [ ] Render normal/large fixture subject and correction, visually inspect every page using the PDF skill and compare with every official 2026 Métropole page. Repair demonstrated defects test-first without blank-page padding.
- [ ] Run full suite, Ruff/hygiene/compliance, Graphify/inventory and independent read-only whole-branch review. Open a protected PR; merge only after Backend and macOS checks pass, then fast-forward clean primary main.
- [ ] Run exactly one fresh pinned V25 live diagnostic; preserve every attempt/checkpoint/artifact/hash and inspect each page. Record an honest manual HOLD/PASS in English through a separate protected evidence PR. Do not select a model or launch the final matrix while fidelity holds.
