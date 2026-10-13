# French NSI V23 network incident — implementation plan

**Goal:** Replace only new French E3 packages with an immutable, sustained causal network incident and useful candidate working-space flow while preserving historical replay.

**Architecture:** New versioned contract/catalogue/authoring module; explicit V23 dispatch through existing provider, pipeline, runtime PDF and benchmark boundaries. V22 and earlier code paths remain immutable.

**Tech Stack:** Python, pytest, ReportLab, Graphify, repository inventory, protected GitHub PR.

**Spec:** `docs/superpowers/specs/2026-10-13-french-nsi-network-incident-v23-design.md`.

**Global Constraints:** Three independent Terminale written exercises; 18 technical + distinct 2 indicative language points; French-only references/no holdout or UK fallback; non-official PDF labels; V13–V22 and UK package/state replay; no page-count padding or final expensive model matrix before a manual fidelity pass. Preserve pinned evidence.

**Review Focus:** Independent oracle and causal consistency; fail-closed source/version identity; material-question association; exact credit; normal/large-print legibility; old-package and UK compatibility.

## Task 1 — Immutable incident facts and finite prose

**Files:** Create `Backend/Core/france/network_incident_contract.py`, `Backend/Core/france/network_incident_prose.py`; test `tests/test_french_network_incident_contract.py`, `tests/test_french_network_incident_prose.py`.

**Interfaces:** `NetworkIncidentContract.from_dict(data)`, `build_network_incident_contract(seed)`, `to_dict()`, `digest`; `network_incident_catalogue_digest()`, `network_incident_selection_schema(contract)`, `validate_network_incident_selection(contract, selection)`, `render_network_incident_candidate(contract, selection, task_specs)`.

- [ ] Query Graphify for E3 contract/prose/tests, then write RED tests for independent route, deadline, queue, recovery and security outcomes, roundtrip/tamper, 12 IDs, 70 minutes and 5.5/6/6.5 point profiles.
- [ ] Add separate V23 contract and finite French catalogue/prose. Keep V18 E3 modules unchanged.
- [ ] Run focused tests, Ruff, Graphify update and inventory. Expected: all focused tests and lint pass; inspect diff, then commit only Task 1 files.

## Task 2 — Selection and package identity

**Files:** Create `Backend/Core/france/network_incident_authoring.py`; modify `Backend/Core/france/provider.py`, `Backend/Core/france/pipeline.py`; test `tests/test_french_network_incident_authoring.py`, `tests/test_nsi_pipeline.py`.

**Interfaces:** `network_incident_selection_prompt(...)`, `author_network_incident_selection(...)`, `replay_network_incident_selection(...)`; `_tasks_for_seed_v23(seed)` keeps E1/E2 contracts unchanged.

- [ ] Write RED tests for hash-bound finite selection, explicit provider/pipeline V23 dispatch, mixed-version rejection and V13–V22/UK replay.
- [ ] Implement the least V23-only dispatch and strict package identity; retain prior routes unchanged.
- [ ] Run focused tests, Ruff, Graphify/inventory. Expected: focused suite and lint pass, old-package/UK replay evidence is green; inspect diff and commit Task 2 files.

## Task 3 — Runtime PDF and benchmark gates

**Files:** Modify `Backend/Core/france/runtime.py`, `Backend/Core/france/rendering.py`, `Backend/Core/france/verification.py`, `tools/french_nsi_benchmark.py`; test relevant French runtime/PDF/benchmark modules.

**Interfaces:** current French generation advertises V23; `validate_network_incident_pdf(...)` binds all three stages, question/answer/credit and digest to V23 only; older validators remain unchanged.

- [ ] Write RED tests for missing/interchanged incident facts, answer leakage, phase/credit mismatches, evidence-question association, normal/large bounds and benchmark routing.
- [ ] Implement V23 PDF/runtime/benchmark checks and staged materials with usable writing space; do not manipulate old saved packages.
- [ ] Run focused and full suites, Ruff/hygiene/compliance, Graphify/inventory. Expected: all tests/checks pass, no historical replay change; inspect diff and commit Task 3 files.

## Task 4 — Visual and integration review

**Files:** New exact English quality diagnostic and corresponding Occitanie report/claims only after a live run; ignored fixture/live outputs remain ignored.

- [ ] Render NOT-LIVE normal/large-print V23 subject and correction fixtures; inspect every generated page and all 16 official 2026 Métropole pages with PDF skill. Repair material defects test-first.
- [ ] Run full verification, fresh read-only whole-branch review, protected Backend/macOS PR/check/merge, then fast-forward clean primary main. Expected: both required checks pass and main is clean.
- [ ] Run exactly one pinned seed-270100 French live diagnostic against locked French reference index; retain all attempts/artifact hashes; inspect every subject/correction page against official. Record exact English evidence and refresh honest Occitanie report via protected PR. If manual fidelity is still HOLD, do not choose a French model or run the final UK/French matrix. Expected: evidence names the exact automated and manual status, with hashes and page log.
