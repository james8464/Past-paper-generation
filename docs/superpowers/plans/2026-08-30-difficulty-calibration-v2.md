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
