# French NSI network exercise depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current short third exercise in new French written papers with a deeper, original, app-owned network case while keeping old packages replayable.

**Architecture:** Keep the v14 network contract, prose catalogue, and replay path immutable. Add a separate v15 contract and finite prose/selection path with a five-node, seven-link network, an independently recomputed route trace, and a concrete process/security sequence. Dispatch by prompt version at generation, verification, PDF validation, benchmark, and package replay. The v15 blueprint changes only Exercise 3's point split; it preserves 70 minutes, six numbered questions, three independent exercises, and 18 + 2 exact points.

**Tech Stack:** Python 3, Pydantic, ReportLab, PyMuPDF, pytest; existing local Ollama selection interface.

**Spec:** `docs/quality/french-nsi-v15-live-diagnostic-2026-10-07.md`, under the approved constraints of `docs/superpowers/plans/2026-09-28-french-baccalaureat.md`.

## Global Constraints

- Written Terminale NSI session 2027 only; training paper and proposed correction remain explicitly non-official.
- Three independent 70-minute exercises; 18 technical points and a separate two-point indicative French-language component.
- App-owned premises, deterministic answers, finite model selection, French-only references, no UK fallback or silent cloud use.
- Old v14/v12/v13 French packages and all UK routes, saved state and packages remain readable and unchanged.
- Never promote automated checks to teacher, examiner, learner, accessibility or prize approval; preserve failed and accepted evidence.
- TDD, reviewed small commits, Graphify/inventory, protected PR checks and merge, clean Git. No final live matrix until source freeze.

## Review Focus

- A seeded graph with tied best routes must fail closed: test unique initial and changed routes across the full finite profile set.
- A forged shortest-path trace or omitted printed edge must fail deterministic replay: tamper both contract and PDF tests.
- A saved v14 package must still validate after v15 becomes the runtime default: keep a recorded fixture and replay test.
- A resume checkpoint from v14 must not be silently reused by v15: assert identity mismatch and retained failed-attempt file.
- A model response containing free text, a new route cost, or an unknown selection ID must be rejected without publication.

---

### Task 1: Versioned app-owned network case

**Files:** Create `Backend/Core/france/network_depth_contract.py`; test `tests/test_french_network_depth_contract.py`.

**Interfaces:** `build_network_depth_contract(seed: int) -> NetworkDepthContract`; `NetworkDepthContract.from_dict(data: dict)` re-derives all facts and expected results. Contract version is `2`. The finite profile is a common integer offset 0–3 over seven positive bidirectional links: Central–R1 2, Central–R2 5, R1–R3 3, R1–R2 4, R2–R3 2, R2–Station 10, R3–Station 4. R1–R3 changes to 12 plus offset. The originally planned R2–Station cost 8 created tied changed routes at offset 2; 10 preserves a unique best route for all four profiles (Task 1 ruling). A fresh Dijkstra implementation supplies settled order, tentative-distance trace, unique route and cost before/after; no stored answer is trusted. Fixed process and security premises are printed and validated.

- [ ] Write tests for all four profiles, independent shortest-path oracle, unique route change, and tampering of each premise/trace; run RED.
- [ ] Implement the contract and run focused tests GREEN; commit the independently testable contract.

### Task 2: Deep finite prose, exact credits and selection replay

**Files:** Create `Backend/Core/france/network_depth_prose.py` and `network_depth_authoring.py`; modify `Backend/Core/france/pipeline.py`, `Backend/Core/france/verification.py`, and the fail-closed selection response policy in `Backend/Core/france/provider.py`; test `tests/test_french_network_depth_prose.py`, `tests/test_french_network_depth_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `render_network_depth_candidate(contract, selection, task_specs) -> dict`; `author_network_depth_selection(...) -> tuple[dict, dict]`; `replay_network_depth_selection(...) -> dict`. New prompt version `fr-nsi-written-2027-v15` selects only finite scene/question/rubric IDs. Its Exercise 3 point profiles for totals 5.5/6/6.5 are `(0.5,1.5,0.5,1,1,1)`, `(0.5,1.5,0.5,1,1,1.5)`, `(0.5,1.5,1,1,1,1.5)`. Questions 3a–3b use the printed seven-link graph and Dijkstra trace; 3c–3d use a concrete resource state and recovery/prevention sequence; 3e–3f distinguish a session-key protocol from sender authentication and other limits. Credit criteria split wherever multiple independently assessable steps are requested. Keep the v14 code path and catalogue digest unchanged.

- [ ] Write RED tests for finite selection, all 18 exact technical points, premise-linked multi-step answers, tamper/replay, v14 fixture validation and v14 checkpoint mismatch.
- [ ] Implement v15-only blueprint/authoring/replay dispatch and independent deterministic verification; run focused tests GREEN; commit.

### Task 3: PDF, runtime and benchmark dispatch

**Files:** Modify `Backend/Core/france/runtime.py`, `tools/french_nsi_benchmark.py`; test `tests/test_french_runtime.py`, `tests/test_french_benchmark_runner.py`, `tests/test_french_framework.py`.

**Interfaces:** Runtime defaults to v15. `validate_network_depth_contract_pdf(...)` checks every app-owned edge, change, process/security premise, question/credit label and role-specific rubric; v14 validator remains available. Benchmark pins v15 contract, prose, model, source and artifact identities, while accepting preserved v14 records as historical evidence, never as a v15 pass.

- [ ] Write RED tests for runtime dispatch, actual normal/large-print PDF text and bounds, no leaked rubric, benchmark identity and old package replay.
- [ ] Implement dispatch and checks; run focused tests GREEN, full pytest, Python lint, macOS build/tests where affected; visually inspect every generated test PDF with the PDF skill; commit.

### Task 4: Review and live fidelity gate

**Files:** Update `Resources/repository-inventory.json`, Graphify output, `docs/quality/reference-live-fidelity-2026-09-28.md`, and the English Occitanie evidence only after measured results.

- [ ] Run `graphify update .`, inventory check, `git diff --check`, full tests and read-only source review; address findings in small commits.
- [ ] Push a protected PR, wait for Backend/macOS checks, then merge and fast-forward clean main.
- [ ] Run one pinned French live diagnostic, preserving all failed attempts. Render and inspect each subject/correction page against official 2026 NSI references; record exact hashes, page/question depth and remaining hold. Do not start the final shared-source UK/French matrix unless this gate passes and source freezes.
