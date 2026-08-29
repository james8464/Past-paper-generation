# Reference-Demand Calibration Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Calibrate every advertised assessment against aggregate features from the relevant real-paper corpus, enforce item and form demand independently from content review, and expose honest evidence in the app.

**Architecture:** Add a shared, copyright-safe demand-profile layer consumed by all generators and package validation. Keep deterministic structural checks separate from a dedicated AI difficulty judge and from empirical student-response calibration. Store only aggregate corpus evidence and fingerprints.

**Tech Stack:** Python 3.12, Pydantic, pytest, Swift 6/SwiftUI, JSON Schema, bundled PDF extraction tooling, Graphify.

---

### Task 1: Specify and validate the profile contract

**Files:**
- Create: `Backend/Core/reference_demand.py`
- Create: `Resources/reference-demand-profile.schema.json`
- Create: `tests/test_reference_demand.py`

1. Write failing tests proving malformed profiles, missing advertised papers and retained source text are rejected.
2. Run `pytest tests/test_reference_demand.py` and confirm failures describe the absent loader/models.
3. Implement typed profile, demand-target and profile-store models with cached loading and advertised-registry coverage checks.
4. Re-run the focused tests until green.

### Task 2: Derive compact profiles from real papers

**Files:**
- Create: `tools/reference_demand_profiles.py`
- Create: `Resources/reference-demand-profiles.json`
- Modify: `requirements-test.txt` only if the existing bounded PDF dependency is insufficient.
- Modify: `tests/test_reference_demand.py`

1. Add failing fixture-based extraction tests for mark tariffs, command words, demand bands and copyright-safe output.
2. Implement board-aware corpus discovery and aggregate extraction for all advertised full papers, with parent-paper inheritance for AQA Computer Science topic banks.
3. Run the tool against the bundled corpus, write the resource, then run it in `--check` mode.
4. Verify every advertised paper resolves to a non-empty, fingerprinted profile and no source path or question prose is retained.

### Task 3: Add deterministic item and form demand audits

**Files:**
- Modify: `Backend/Core/reference_demand.py`
- Modify: `Backend/Core/assessment_package.py`
- Modify: `tests/test_reference_demand.py`
- Modify: `tests/test_assessment_package.py`

1. Add failing literal tests for low, standard, high, calculation, contextual AO2, analytical AO3 and evaluative AO4 targets.
2. Add failing package tests showing missing context/application, shallow high-tariff demand and distribution drift are reported or rejected.
3. Implement target derivation and a form audit comparing mark bands, command words and demand proportions within explicit tolerances.
4. Include the audit and profile fingerprint in assessment-package validation output; require a pass for live packages.

### Task 4: Separate content review from difficulty review in the shared pipeline

**Files:**
- Modify: `Backend/Core/model_review.py`
- Modify: `Backend/Core/ai_assessment.py`
- Modify: `Backend/Core/providers.py`
- Modify: `Backend/Core/family_adapter.py`
- Modify: `tests/test_model_review.py`
- Modify: `tests/test_ai_assessment.py`
- Modify: `tests/test_family_adapter.py`

1. Add failing tests proving a content-approved but under-demanded item is rejected by a second, dedicated call.
2. Add failing prompt tests proving generation, difficulty review and repair carry the exact target/profile basis.
3. Implement a structured `DifficultyReviewResult`, dedicated prompt/parser and provider response schema.
4. Resolve the profile in the family adapter, pass it through shared generation and emit a visible “checking reference demand” progress stage.
5. Re-run focused tests and refactor duplicated serialization only after green.

### Task 5: Integrate custom AQA Computer Science and Edexcel pipelines

**Files:**
- Modify: `Resources/computer-science/aqa/generator/cspapergen/ollama_client.py`
- Modify: `Resources/computer-science/aqa/generator/tests/test_ollama_client.py`
- Modify: `Resources/economics/edexcel-a/generator/pastpapergen/ollama_client.py`
- Modify: `Resources/economics/edexcel-a/generator/tests/test_ollama_client.py`

1. Add failing tests showing both custom pipelines include a concrete demand target and require the separate judge for generated, review-only and fallback items.
2. Integrate shared target construction and difficulty review without changing immutable answers or marking guidance.
3. Ensure checkpoint identities/prompt versions invalidate pre-calibration cached items.
4. Run both generator test suites.

### Task 6: Record evidence in registry, manifests and app UI

**Files:**
- Modify: `Resources/generator-registry.json`
- Modify: `Resources/generator-capability.schema.json`
- Modify: `Backend/Core/generator_registry.py`
- Modify: `Backend/Core/generation.py`
- Modify: `macOS/PaperCreator/Domain/AppModels.swift`
- Modify: `macOS/PaperCreator/Features/Generation/GeneratorWorkspaceView.swift`
- Modify: `macOS/PaperCreator/Features/Onboarding/WelcomeHelpViews.swift`
- Modify: relevant Python and Swift tests.

1. Add failing registry and Swift tests for a required `reference_demand_profile` declaration and decoded package audit.
2. Link every advertised family to the shared resource and record its fingerprint/audit in package manifests.
3. Add a Reference demand row and latest-package metrics to Quality; retain Empirical demand as a distinct, conservative status.
4. Expand Help with the three evidence layers and what the automated comparison can and cannot prove.
5. Run focused Python and Swift tests.

### Task 7: Verify all supported outputs and finish cleanly

**Files:**
- Modify: `docs/ASSESSMENT_QUALITY.md`
- Modify: generated Graphify output.

1. Run `tools/reference_demand_profiles.py --check`, all Python tests, generator-specific suites and static compilation.
2. Run the supported-assessment preview matrix and validate each generated assessment package/PDF.
3. Run macOS unit/UI tests, release compliance, repository hygiene and App Store archive checks available locally.
4. Review representative real/generated PDF pages using the PDF visual workflow where calibration changes affect output.
5. Update assessment-quality documentation with exact guarantees and limitations.
6. Run `graphify update .`, inspect `git diff --check`, commit on `main`, and verify the working tree is clean.
