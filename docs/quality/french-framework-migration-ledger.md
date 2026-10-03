# French framework migration ledger

Snapshot: 30 September 2026, branch `french-baccalaureat`, through commit
`f78b18b`. This ledger records the complete repository matches for the boundary
symbols used to audit UK assumptions. A legacy name is not renamed merely for
symmetry: compatibility and policy separation matter more than vocabulary.

## Disposition rules

- **UK-specific, retained:** board profiles, assessment objectives, paper IDs,
  family adapters and saved UK keys keep their existing names and meaning.
- **Shared, neutral boundary:** registry dispatch, education context, provider,
  event, history and publication services accept an explicit framework/context.
- **French-separated:** prompts, scoring, retrieval, validation and rendering live
  under the French policy path and cannot fall back to UK AO rules.

## Complete symbol inventory

The paths below are the sorted results of repository-wide `rg -l` checks over
`Backend`, `Resources`, `macOS`, `tests`, `tools` and `bridge.py`, excluding build
outputs. Re-run those checks whenever a boundary symbol is added.

### `ExamBoardOption` - six files - UK-specific, retained

- `macOS/PaperCreator/Domain/AppModels.swift`
- `macOS/PaperCreator/Domain/GenerationEstimator.swift`
- `macOS/PaperCreator/Features/Generation/GeneratorWorkspaceView.swift`
- `macOS/PaperCreator/Navigation/SidebarView.swift`
- `macOS/PaperCreator/State/ApplicationCoordinator.swift`
- `macOS/PaperCreator/State/CatalogStore.swift`

These symbols represent the existing UK catalogue only. France is a distinct
`SidebarItem.frenchBaccalaureat` and never constructs a fictitious exam board.

### `selectedBoard` / `selectedBoardID` - five files - compatibility key, retained

- `macOS/PaperCreator/Application/AppConfiguration.swift`
- `macOS/PaperCreator/Navigation/ContentView.swift`
- `macOS/PaperCreator/State/ApplicationCoordinator.swift`
- `macOS/PaperCreator/State/CatalogStore.swift`
- `macOS/Tests/CoordinatorTests.swift`

The stored UK board/paper selection remains readable. Framework navigation is
stored independently as `france:nsi`, so opening France does not rewrite a user's
last UK selection.

### `assessment_frameworks` - two files - neutral boundary, added

- `Backend/Core/generator_registry.py`
- `Resources/generator-registry.json`

The registry reads the additive framework collection alongside legacy `families`.
Unknown or incomplete framework policies fail closed.

### `generate-assessment` - five files - French-separated dispatch

- `Backend/Core/cli.py`
- `macOS/PaperCreator/Domain/FrenchAssessmentRequest.swift`
- `macOS/Tests/AppTests.swift`
- `tests/test_french_framework.py`
- `tools/french_nsi_benchmark.py`

This route bypasses `run_family_adapter`; it supplies the explicit assessment ID,
French reference index, model identity, seed and output profile.

### `objective_policy_for` - fifteen files - UK-specific, retained

- `Backend/Core/ai_assessment.py`
- `Backend/Core/assessment_objectives.py`
- `Backend/Core/assessment_package.py`
- `Backend/Core/computer_science_audit.py`
- `Backend/Core/exam_blueprints.py`
- `Backend/Core/independent_solver.py`
- `Backend/Core/mark_scheme_enrichment.py`
- `Backend/Core/model_review.py`
- `Backend/Core/reference_demand.py`
- `Resources/accounting/aqa/generator/aqaaccountgen/render_pdf.py`
- `Resources/computer-science/aqa/generator/cspapergen/objective_calibration.py`
- `Resources/computer-science/aqa/generator/cspapergen/ollama_client.py`
- `Resources/computer-science/aqa/generator/cspapergen/validation.py`
- `tests/test_computer_science_objectives.py`
- `tools/reference_demand_profiles.py`

These remain UK AO consumers. The shared package reader dispatches French schema 2
to French validation before any UK objective policy is requested.

### `run_family_adapter` - eleven files - UK-specific, retained

- `Backend/Core/family_adapter.py`
- `Resources/accounting/aqa/generator/aqaaccountgen/cli.py`
- `Resources/business/aqa/generator/aqabizgen/cli.py`
- `Resources/computer-science/aqa/generator/cspapergen/cli.py`
- `Resources/computer-science/ocr/generator/ocrcsgen/cli.py`
- `Resources/configured-generators/generator/configuredgen/cli.py`
- `Resources/economics/aqa/generator/aqaecongen/cli.py`
- `Resources/economics/edexcel-a/generator/pastpapergen/cli.py`
- `Resources/economics/ocr/generator/ocregen/cli.py`
- `tests/test_generator_render_transactions.py`
- `tests/test_shared_numeric_integrity.py`

France reuses lower-level providers, events and atomic rendering, not this adapter's
UK blueprint/AO assumptions.

### `document_language` - four files - neutral boundary, added

- `Backend/Core/education_context.py`
- `Backend/Core/france/corpus.py`
- `Resources/france/nsi/source-register.json`
- `Resources/generator-registry.json`

`fr-FR` is part of source scope and output policy. Interface language remains a
separate user preference and cannot silently change the paper language.

## French-owned policy surface

`Backend/Core/france/` owns the French corpus, model transport, exercise schema,
generation pipeline, deterministic verification, originality screen, rendering,
runtime and teacher-review record. `Resources/france/` owns dated programme,
assessment, curriculum and source records. `FrenchAssessmentWorkspace.swift` owns
the native teacher workflow. None of these are aliases for a UK family.

## Compatibility result

Existing UK route IDs, favourites, recent documents, command-line family entry
points and package validators are unchanged in meaning. Older history records omit
the new optional framework/language fields and remain readable. Historical outputs
are never rewritten. Tests cover legacy registry loading, UK route preservation,
French/UK package dispatch and saved navigation restoration.
