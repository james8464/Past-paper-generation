# French NSI network reasoning depth implementation plan

> **For agentic workers:** Use superpowers:executing-plans task by task. Start each source task with Graphify, write a failing test before implementation, review small commits, and update Graphify after code edits.

**Goal:** Give the original written Exercise 3 a substantive twelve-question reasoning sequence without changing old French packages or UK routes.

**Spec:** `docs/superpowers/specs/2026-10-08-french-nsi-network-reasoning-design.md`.

**Baseline:** Protected PR #49 merged at `b4a229c` after Backend/macOS checks and read-only review. The pinned V17 live evidence is `docs/quality/french-nsi-v17-graph-tree-depth-live-diagnostic-2026-10-08.md` and remains a manual fidelity hold. Preserve all earlier live/failure artifacts and hashes. The source is not frozen.

## Task 1: Version-three immutable case and exact working

Create `Backend/Core/france/network_reasoning_contract.py` and contract tests. Fix the seven-link graph, cost-change rule, process state/schedule and security message/threat facts. Derive initial and changed Dijkstra traces and predecessors, wait-for edges and recovery states. Canonical seed/digest validation must reject tampering, ties or missing states. Keep V2 byte-for-byte behavior.

- [ ] Test a hand-computed seed, a seed range, all twelve IDs, intermediate states and changed-route uniqueness; prove tampered/extra facts fail.
- [ ] Watch the focused suite fail, implement the contract, then run contract and V2 compatibility suites green; review and commit.

## Task 2: Native French finite prose and exact blueprint

Create a V18-only finite catalogue/authoring path and provider schema. Use twelve connected questions in parts AAAABBBBCCCC; only finite scene/question/rubric IDs may cross the model boundary. Derive answers and quarter-point criteria from the contract. Lock three allocation profiles (5.5/6/6.5) and a 70-minute estimate; never use time estimates as measured learner evidence.

- [ ] Test schema rejection, twelve original prompts, requested working, canonical answers, exact credit/part/time sums and replay hashes before code.
- [ ] Watch RED, implement, run focused/older-version suites green, review and commit.

## Task 3: Explicit V18 pipeline, package and PDF gates

Dispatch V18 only for new generation and benchmarks. Keep V13–V17 identities and packages on their original code paths. Verify all subject materials, task IDs, answer/rubric presence, non-leakage, exact credit and role labels in PDFs. Preserve French-only retrieval and no UK fallback.

- [ ] Test V18 full-paper 18+2 scoring, malicious mixed identity, missing/interchanged printed facts, V17 saved-package replay, UK route compatibility and normal/large-print bounds first.
- [ ] Watch RED, implement, run focused suites green, review and commit.

## Task 4: Page-by-page review and protected integration

- [ ] Render normal and large-print fixture subject/correction; inspect every page against the official 2026 Métropole reference with the PDF skill. Fix observed layout defects test-first, never by padding to a target count.
- [ ] Run full pytest, Ruff, inventory and diff checks; update Graphify, obtain a read-only review and address concrete findings.
- [ ] Open and attach a PR; merge only after Backend/macOS protected checks; fast-forward clean main.
- [ ] Run exactly one pinned local-model French live diagnostic before any expensive shared-source matrix. Retain attempt and artifact hashes, inspect every generated page, record an honest English fidelity decision and update the Occitanie evidence. External teacher, learner, rights and accessibility gates stay open; issues #4/#8 stay open.
