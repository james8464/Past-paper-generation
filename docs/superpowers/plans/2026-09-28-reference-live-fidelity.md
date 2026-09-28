# Reference evidence, live validation and PDF fidelity implementation plan

> **For agentic workers:** Use the executing-plans workflow for the validation runner and dispatching-parallel-agents for the independent reference and renderer repairs. Steps use checkbox syntax for tracking.

**Goal:** Resolve the three outstanding engineering gaps using genuine reference evidence, complete live generation, and measured PDF comparisons.

**Architecture:** Preserve the existing generation/review pipeline. Reference evidence supports the actual generated bank items, without implying whole-syllabus or empirical calibration. Renderer fixes use measured board geometry without reproducing official branding. Live qualification binds results to inputs and records failures rather than substituting previews.

**Tech stack:** Python, ReportLab/PyMuPDF, Ollama, pytest, native macOS tests, GitHub Actions.

**Spec:** User request of 28 September and `docs/quality/teacher-feedback-review-2026-09-27.md`; this plan's constraints define the scoped completion criteria.

## Global constraints

- AI-authored questions remain original; never copy reference question prose into shipped content.
- Do not weaken review, content, layout or evidence checks to make a run pass.
- Source records need document hashes, page/item provenance and defensible task matching.
- Preview success is not live success; bank-item support is not whole-topic/student calibration.
- Keep copyrighted references, model output and temporary renders outside Git.
- Normal protected PR/check flow; leave only main after merge.

## Review focus

- A resumed preview, different seed/model, changed runtime or modified artifact must not count as a current live pass.
- Interrupted generation must preserve progress/failure evidence and stop its child process.
- Unsupported/misclassified topic tasks must fail even if nearby topic keywords match.
- New geometry must preserve content, writing space, diagrams and page bounds for varied seeds.
- A failed model review must remain visible and cannot be converted into a qualified result.

### Task 1: Source-backed topic-bank evidence

**Files:** `Backend/Core/topic_reference_evidence.py`, bank branch of `reference_demand.py`, `tools/reference_demand_profiles.py`, reviewed profile JSON and focused topic tests.
**Interface:** `audit_topic_bank(items, topic, records)` returns evidence/coverage and an explicitly scoped reference-support result; no empirical claim.

- [x] Audit missing task forms against original question papers and mark schemes.
- [x] Add failing tests for supported complete banks and false matches/sparse sources.
- [x] Add reviewed feature records and a sufficient-evidence rule that requires actual coverage.
- [x] Regenerate profiles and verify all three bank seeds, negative tests and the full suite.

### Task 2: Reliable live-matrix evidence and execution

**Files:** `tools/live_generation_matrix.py`, optional focused process-runner module, `tests/test_live_generation_matrix.py`.
**Interface:** Existing `run_matrix` retains its arguments and report fields, adding request/artifact identity, progress and explicitly scoped resource evidence.

- [x] Reproduce unsafe resume across changed model/seed/preview/artifacts in failing tests.
- [x] Bind resume to request/runtime identity and file digests; never backfill proof from bare success flags.
- [x] Test real subprocess streaming, timeout cleanup and peak backend memory reporting, then implement.
- [ ] Run every advertised route through the app backend without preview. Diagnose each failure, add regression coverage and retry without weakening review.
- [ ] Persist complete per-route and aggregate evidence with exact model, seed and source identity.

### Task 3: Measured visual repairs

**Files:** Board/shared renderers, layout tests and relevant runtime geometry resources.
**Interface:** Existing PDF output contracts and content/layout gates remain intact.

- [x] Inspect real/generated cover, answer, end and scheme pages to identify actual recurring differences.
- [x] Add failing geometry/content-preservation tests for each repair.
- [x] Apply measured typography/spacing/layout changes; inspect rerenders at readable scale.
- [ ] Generate all preview routes and compare using fixed seeds/settings; retain contact sheets locally.

### Integration and publication

- [ ] Revalidate final-code live artifacts, topic support and PDF fidelity; record precise results and any genuine external limits.
- [x] Run complete backend/native tests, lint, release preflight and fresh independent code review.
- [ ] Refresh Graphify and inventory; commit, publish PR, pass required checks, merge and verify clean main.

## Execution notes

- Work in the existing checkout as previously requested, on a temporary review branch. Git cannot create `main/...` while a branch named `main` exists, so use `qualification-completion`.
- User explicitly requested implementation without repeated approval prompts; proceed with these bounded existing-pipeline repairs.
