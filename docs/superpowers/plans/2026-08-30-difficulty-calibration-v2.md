# Difficulty Calibration v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make every generated assessment match the relevant official paper's observable cognitive demand through reference-derived targets, independent solver-grounded review, and fail-closed release evidence.

**Architecture:** Upgrade the copyright-safe reference profiles and item contracts, reuse the existing independent solution as objective evidence for a richer second AI judge, persist that judgment on each item, and aggregate it in assessment-package and macOS quality reports. Shared and specialist generators use one contract so future subjects inherit the same calibration automatically.

**Tech Stack:** Python 3.12, Pydantic 2, pytest, Swift 6/SwiftUI, JSON Schema, Graphify.

**Spec:** `docs/superpowers/specs/2026-08-30-difficulty-calibration-v2-design.md`

## Global Constraints

- Retain no official question prose; store and prompt only aggregate reference features.
- Do not claim psychometric equivalence without external examiner and learner evidence.
- Live generation fails closed; preview generation remains clearly labelled as unreviewed where applicable.
- Keep all work on `main`, commit locally, do not push.
- Preserve compatibility with the current macOS deployment target and App Store sandbox.

## Continued qualification — 31 August

The checked foundation tasks below record implementation, not proof that all
generated papers are correctly calibrated. Fresh live, adversarial and manual
checks found the following integration defects. Their bounded implementation
and review are tracked in the Excellence Programme's Task 7, using its existing
SDD ledger rather than restarting completed work:

- [x] Candidate-visible Accounting shareholder source and exact worked credit (7.A).
- [x] Accounting AO1–AO3 meanings, actual 30/42/48 paper allocation and stale-policy rejection (7.B).
- [x] Exhaustive finite CS answers, retained private keys and candidate/source parity (7.C).
- [x] Shared closed-numeric verification without draft-answer substitution; role/value/unit checks and explicit deterministic coverage (7.G, reviewed through `7ea51fa`; remaining OCR/Edexcel contracts tracked below).
- [x] AQA/OCR CS actual task demand, objective meanings, answerable trace sources, consistent operations and component-specific timing (7.E, scoped independent review clean through `31cc94c`; outstanding live/layout qualification below).
- [ ] Edexcel item-specific marking and complete explicit shared content-review responses (7.F).
- [ ] Reject reproduced non-SQL/unknown-field solver answers using candidate-grounded, explicitly bounded SQL validation; preserve dialect distinctions and rerun the actual SQL transaction (7.I).
- [ ] All permitted candidate paths and remaining Economics/Business application/analysis demand, including MCQs (7.H).
- [ ] Once-only general marking instructions with all case-specific credit retained (7.D).
- [ ] Fresh all-route verification and live/manual evidence after these corrections.

Reference facts: `docs/quality/assessment-objective-reference.md`. Current
failures and verification limits: `docs/quality/difficulty-calibration-v2-report.md`.
External examiner and learner evidence remains a separate, unpassed gate.

---

### Task 1: Reference profile schema v2

**Files:**
- Modify: `Backend/Core/reference_demand.py`
- Modify: `Resources/reference-demand-profile.schema.json`
- Modify: `tools/reference_demand_profiles.py`
- Modify: `Resources/reference-demand-profiles.json`
- Test: `tests/test_reference_demand.py`

**Interfaces:**
- Produces: `ReferenceDemandProfile` v2 distributions, `metric_tolerances`, `extraction_coverage`, and paired aggregate extraction.
- Consumes: official PDF text through the existing local corpus builder.

- [x] Add failing tests for copyright-safe paired item features, mark-weighted distributions, per-metric tolerances, and coverage validation.
- [x] Run the focused tests and confirm failures are caused by missing v2 fields/behavior.
- [x] Implement local command/mark pairing, response-mode and operation inference, weighting, and profile validation.
- [x] Rebuild the committed profiles and JSON Schema; verify no source prose or paths are retained.
- [x] Run `pytest tests/test_reference_demand.py -q` and commit the passing profile upgrade.

### Task 2: Observable item demand contracts

**Files:**
- Modify: `Backend/Core/reference_demand.py`
- Modify: `tests/test_reference_demand.py`

**Interfaces:**
- Produces: `ItemDemandTarget` with `maximum_reasoning_steps`, `required_cognitive_operations`, `expected_minutes_min/max`, `maximum_scaffolding`, and `requires_shortcut_resistance`.
- Consumes: schema-v2 reference profile and a serialisable assessment item.

- [x] Add failing tests for recall, multi-stage calculations, contextual analysis, extended judgement, and over-demand ceilings.
- [x] Run each test and observe the expected missing-field failure.
- [x] Implement deterministic target construction using marks, AO allocation, command family, response mode, and reference archetypes.
- [x] Run focused tests and commit the demand-contract change.

### Task 3: Solver-grounded difficulty judge

**Files:**
- Modify: `Backend/Core/model_review.py`
- Modify: `Backend/Core/ai_assessment.py`
- Modify: `tests/test_model_review.py`
- Modify: `tests/test_ai_assessment.py`

**Interfaces:**
- Produces: `DifficultyReviewResult`/`DifficultyEvidence` containing reasoning range, observed operations, context dependence, shortcut resistance, timing and scaffolding checks.
- Consumes: `CanonicalSolution` returned by `_independently_validate_candidate(...)`.

- [x] Add failing tests showing the judge receives the canonical solution, rejects too few or too many steps, and requires every boolean gate.
- [x] Run focused tests and verify the new assertions fail.
- [x] Return the canonical solution from reconciliation and pass it to the difficulty review.
- [x] Strengthen the reviewer prompt/schema and attach the validated evidence under `authoring_context.difficulty_evidence`.
- [x] Include the demand contract and precise previous failures in generation/repair prompts.
- [x] Run focused tests and commit the shared-pipeline gate.

### Task 4: Specialist generator parity

**Files:**
- Modify: `Resources/computer-science/aqa/generator/cspapergen/models.py`
- Modify: `Resources/computer-science/aqa/generator/cspapergen/ollama_client.py`
- Modify: `Resources/economics/edexcel-a/generator/pastpapergen/models.py`
- Modify: `Resources/economics/edexcel-a/generator/pastpapergen/ollama_client.py`
- Test: specialist generator test suites.

**Interfaces:**
- Produces: specialist blueprints with the same persisted `difficulty_evidence` payload.
- Consumes: shared `build_item_demand_target`, `IndependentSolver`, and `require_difficulty_review` interfaces.

- [x] Add failing specialist tests for solver-grounded reviewer inputs and persisted evidence.
- [x] Run the tests and confirm missing evidence failures.
- [x] Implement immutable part/question evidence fields and return updated reviewed blueprints.
- [x] Run both specialist suites and commit parity changes.

### Task 5: Form-level evidence and release gate

**Files:**
- Modify: `Backend/Core/assessment_package.py`
- Modify: `Backend/Core/reference_demand.py`
- Modify: `Backend/Core/generation.py`
- Test: `tests/test_assessment_package.py`
- Test: `tests/test_reference_demand.py`
- Test: `tests/test_generation_entrypoint.py`

**Interfaces:**
- Produces: schema-v2 `reference_demand` report with mark-weighted drift, review coverage, reasoning/context/shortcut pass rates and extraction coverage.
- Consumes: persisted item-level difficulty evidence extracted from all blueprint shapes.

- [x] Add failing tests for mark weighting, missing/tampered live evidence, preview disclosure, and report fields.
- [x] Run focused tests and verify correct failures.
- [x] Preserve evidence during item extraction and implement the new audit and fail-closed live validation.
- [x] Propagate concise metrics and truthful limitations to generation manifests.
- [x] Run focused tests and commit the package gate.

### Task 6: macOS evidence presentation and guidance

**Files:**
- Modify: `macOS/PaperCreator/Domain/AppModels.swift`
- Modify: `macOS/PaperCreator/Features/Generation/GeneratorWorkspaceView.swift`
- Modify: relevant Swift tests and help content.

**Interfaces:**
- Produces: accessible quality rows for item review coverage, reasoning fit, context/shortcut fit, extraction coverage, and maximum gated drift.
- Consumes: assessment JSON `reference_demand` schema v2.

- [x] Add failing Swift parsing/presentation tests for the new metrics and non-equivalence copy.
- [x] Run the focused Swift suite and observe failures.
- [x] Implement resilient decoding and compact native presentation with accessibility labels.
- [x] Run Swift tests and strict build; commit the UI/report update.

### Task 7: Whole-project qualification

**Files:**
- Modify: `docs/quality/difficulty-calibration-v2-report.md`
- Modify: `Resources/repository-inventory.json` if tracked files changed.
- Update: `graphify-out/`

**Interfaces:**
- Produces: reproducible qualification evidence for all advertised assessment IDs.
- Consumes: all preceding tasks.

- [x] Run the complete Python and Swift test suites.
- [x] Rebuild every advertised preview assessment and validate its package/PDF outputs.
- [x] Run available live-model smoke calibration without converting unavailable external services into a false pass.
- [x] Run strict macOS build, App Store preflight, inventory validation, and repository hygiene checks.
- [x] Record exact results and limitations, update Graphify, verify a clean tree, and commit all remaining evidence.

### Task 8: Live-validation hardening

The live accounting run and final matrix audit exposed issues beyond the initial
implementation. These are part of this delivery, not deferred quality work.

- [x] Require locked numerical contracts to pass independent content and difficulty review.
- [x] Make accounting schemes solver-complete, including exact finals and intermediate working.
- [x] Recompute six closed accounting contracts independently from their source data; remove draft-answer leakage from model solver prompts.
- [x] Correct implicit depreciation rounding, declare whole-pound company rounding, and conserve partnership allocations exactly across seeds.
- [x] Scale calculation reasoning ceilings with tariff and required operations; clarify minutes and operation tokens in reviewer prompts.
- [x] Resume complete verified guidance without applying unrelated AI-authoring entry caps.
- [x] Strictly revalidate saved difficulty evidence at release and on shared-generator resume.
- [x] Add a sustained four-mark data-structures comparison within the existing 30-mark bank.
- [x] Make the matrix qualification tool fail on a missing or failed reference-demand audit, even when preview rendering succeeds.
- [x] Run focused live company/partnership reviews and visually check changed question pages.
- [x] Complete the fresh full live accounting paper and record its actual outcome.
- [x] Record final multi-seed matrix, backend/macOS/App Store results and commit the updated evidence.

### Task 9: Independent review corrections

- [x] Reject raw model responses that omit any required difficulty check or completion-time estimate.
- [x] Keep generation and exported-package targets identical across all specialist routes, including legacy AO labels, inherited styles and empty context.
- [x] Classify the `mcq` command as selected-response retrieval instead of requiring an explanation.
- [x] Supply candidate-visible options, chart values, table headers and diagram structure to specialist solvers without leaking hidden classification labels or keyed answers.
- [x] Reconcile specialist canonical answers before difficulty review, including explicit keyed-option agreement.
- [x] Accept combined legacy objective labels as their individual declared objectives without losing release validation.
- [x] Obtain a bounded follow-up review and rerun regression tests and all 21 advertised routes across three seeds.

### Task 10: Supported-decision command calibration

The full live run accepted 20 parts, then rejected question 17 three times because
`Advise` incorrectly fell through to an `explain` requirement. AQA defines this
command as recommending an appropriate choice or course of action.

- [x] Reproduce the missing command recognition and unsupported explanation requirement with four failing regression cases.
- [x] Recognise `Advise` in corpus extraction and align advice, recommendation and justification with analysis and judgement in item targets and form audits.
- [x] Obtain a focused read-only review of the correction.
- [x] Rebuild the reference profiles, resume the saved live paper and rerun final qualification without weakening any acceptance gate.

### Task 11: Visual review correction

- [x] Reproduce incorrect positional assessment-objective labels in Accounting indicative-content tables.
- [x] Preserve explicit objective labels and show an em dash for unassigned points in all three affected table builders.
- [x] Rerender the accepted live blueprint through normal package finalisation, inspect the corrected PDF, obtain a focused review and run regression tests and three-seed Accounting previews.
