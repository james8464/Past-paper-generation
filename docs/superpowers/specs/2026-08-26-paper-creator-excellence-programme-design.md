# Paper Creator Excellence Programme Design

**Date:** 2026-08-26
**Status:** Approved for planning; implementation not yet started

## Purpose

Paper Creator will generate original A-level question papers, supporting materials, and examiner-usable mark schemes. The generated assessment must follow the selected board and specification closely in structure, typography, geometry, demand, mark allocation, assessment-objective coverage, question variety, and marking logic, while remaining clearly unofficial and never copying protected questions or board logos.

This programme brings the existing contract-first generation work, measured rendering work, macOS product experience, empirical assessment calibration, extensibility, and release engineering into one definition of completion.

## Baseline on 26 August 2026

- The registry advertises seven implemented families and 18 papers: AQA Accounting, AQA Business, AQA Computer Science, AQA Economics, OCR Computer Science, OCR Economics, and Pearson Edexcel Economics A.
- The catalogue exposes 23 selectable combinations and 16 coming-soon combinations.
- All 18 implemented papers still have the empirical `difficulty` gate set to `false`.
- AQA Computer Science Paper 2 and all three Pearson Edexcel Economics A papers still have the `visual` gate set to `false`.
- Existing contract, checkpoint, bounded-render, PDF-validation, psychometric, model-recommendation, MLX-setup, coverage, and fidelity foundations are retained.
- Existing detailed plans remain authoritative for their completed or partially completed implementation details:
  - `docs/superpowers/plans/2026-08-23-assessment-reliability-core.md`
  - `docs/superpowers/plans/2026-08-23-rendering-and-mark-scheme-reliability.md`
  - `docs/superpowers/plans/2026-08-23-measured-paper-fidelity.md`

## Product Truth and Readiness Language

The application exposes three independent levels instead of one ambiguous “ready” label:

1. **Engineering validated** — generation, deterministic checks, rendering, packaging, and automated release checks pass.
2. **Visually calibrated** — every document role has passed multi-year, role-matched visual and print validation plus recorded manual review.
3. **Empirically calibrated** — expert review and anonymised student/marker evidence support the targeted demand profile and marking reliability.

The UI may describe an uncalibrated paper as targeting a board demand profile, but must not claim equivalent difficulty, examiner approval, or official status. A paper is fully qualified only when all three levels pass.

## Design Principles

1. AI creates new contexts, questions, reasoning, and indicative content; deterministic code owns marks, AO totals, numeric fixtures, calculations, graph geometry, evidence binding, pagination constraints, and release decisions.
2. Assessment content is renderer-independent. A validated, versioned package can be rerendered without another model call.
3. Board identity is represented through document grammar and measured geometry, not protected logos, copied wording, or implied endorsement.
4. Every claim of quality is backed by a versioned manifest and reproducible evidence.
5. A new subject or board is unavailable until it passes the same gates as existing families.
6. Native macOS behavior takes precedence over decorative novelty. Standard SwiftUI/AppKit controls, materials, commands, focus behavior, and accessibility semantics are used directly.
7. Generated output, caches, local model data, reference PDFs, derived raster pages, and personal calibration data are not committed.

## Target Architecture

```mermaid
flowchart LR
    A[Versioned capability manifest] --> B[Specification and paper blueprint]
    B --> C[Deterministic assessment contract]
    C --> D[AI item transaction]
    D --> E[Independent solution and review]
    E --> F[Validated assessment package]
    F --> G[Board document profile and rendering DSL]
    G --> H[Question paper and mark scheme PDFs]
    H --> I[PDF, visual, print, and accessibility audits]
    I --> J[Qualification manifest]
    J --> K[macOS document history and preview]
    L[Expert, student, and marker evidence] --> J
```

### Shared Core Boundaries

- `Backend/Core/assessment_*` owns content contracts, checkpoints, review, evidence, solutions, and psychometrics.
- `Backend/Core/document_dsl/` owns renderer-neutral page roles and board-profiled PDF components.
- `Backend/Core/qualification/` owns readiness levels, manifests, visual/print/accessibility evidence, and fail-closed gates.
- A family package under `Resources/<subject>/<board>/generator/` contains only syllabus data, paper blueprints, subject validators/calculators, and genuinely exceptional adapters.
- `Resources/generator-registry.json` is the single source of truth for available families, papers, capabilities, schema versions, providers, and qualification state.
- The macOS app consumes registry and job-history protocols; it does not recreate readiness or capability rules.

### macOS State Boundaries

`AppViewModel` becomes a thin composition root over:

- `GenerationCoordinator` for configuration, generation, cancellation, resume, and progress;
- `ModelCoordinator` for providers, Ollama recommendations, benchmark state, and consented MLX setup;
- `SettingsStore` for durable user preferences;
- `RecentDocumentStore` for persisted jobs and artifacts;
- `BenchmarkCoordinator` for performance measurements;
- `CatalogStore` for search, favourites, capability filtering, and registry refresh.

## Visual and Structural Fidelity

### Reference Corpus

- Keep at least three representative official series per family where licensing and local user access permit.
- Store only derived measurements and hashes in the repository.
- Classify pages by semantic role: cover, instructions, question content, source content, answer page, continuation, blank, end page, mark-scheme cover, mark-scheme grid, levels table, and annotation guidance.
- Match generated roles to reference roles using role and content geometry, not page sequence alone.
- Record acceptable ranges across years so legitimate board variation does not become a false regression.

### Measurement

- Raster comparison runs at 300 DPI for CI and 600 DPI for final qualification.
- Text comparison measures font file identity, embedding, glyph bounding boxes, baselines, leading, kerning-sensitive line widths, and fallback use.
- Geometry comparison measures frames, gutters, rules, answer-line rhythm, mark placement, table cells, diagrams, folios, headers, footers, and safe print area.
- Role-specific thresholds replace a single global similarity score.
- Stable furniture receives more weight than intentionally novel question prose.
- Print checks cover 100% scale, common printer non-printable margins, monochrome legibility, colour space, and thin-rule survival.
- PDF checks cover reading order, tags, selectable text, font embedding, clipping, overlap, blank pages, metadata, and declared output roles.

### Deterministic Visual Components

Graphs, tables, accounting statements, logic diagrams, trace tables, scientific apparatus, circuit diagrams, molecules, mathematical plots, maps, timelines, and source panels are generated from typed data. AI may select or describe the intended concept, but cannot emit unvalidated drawing coordinates or raster text.

## Assessment Validity and Mark Schemes

### Question Quality

Every item records command word, topic, subtopic, marks, AO allocation, target demand band, expected completion time, prerequisite knowledge, answer form, misconception targets, evidence references, and originality fingerprint. Deterministic and model-assisted checks cover factual direction, ambiguity, answerability, data sufficiency, syllabus scope, unintended clues, answer leakage, duplication, and cross-paper topic balance.

### Independent Solving

An independent solver receives the question and source material without the draft mark scheme. Its structured solution is reconciled against deterministic calculators and then compared with the mark scheme. Disagreement blocks publication or creates a targeted repair transaction.

### Mark-Scheme Completeness

Each mark-scheme entry contains observable mark points, required working, accepted alternatives, equivalent formulations, partial-credit boundaries, common errors, follow-through rules, evidence links, AO allocation, and correspondence to each subpart. Extended response uses a board-specific level-of-response engine with descriptors, best-fit guidance, indicative content, caps, and exemplar annotations. Weak, average, and excellent synthetic responses are marked before release to expose ambiguous boundaries.

### Empirical Calibration

The evidence model stores anonymised student responses, total scores, completion times, marker decisions, cohort metadata, and consent/provenance. Qualification evaluates facility, discrimination, distractor functioning, reliability, ability-range coverage, completion time, differential item functioning, and inter-rater agreement. Minimum sample and quality thresholds are versioned and cannot be bypassed by model review.

## Subject and Board Expansion

Expansion order is fixed until a release review explicitly changes it:

1. Cambridge International Economics and Computer Science.
2. AQA Mathematics.
3. AQA Biology.
4. AQA Chemistry and Physics.
5. Pearson Edexcel and OCR Mathematics and sciences.
6. Further Mathematics, Psychology, Geography, Sociology, History, and English Literature.

Each family supplies specification data, blueprint distributions, subject validators, deterministic visual primitives, solution rules, mark-scheme policy, multi-year layout evidence, generation-matrix cases, and qualification evidence. Essay-heavy subjects also require source/quotation provenance and level-of-response calibration; mathematics and sciences require symbolic/numeric equivalence and unit/significant-figure rules.

## macOS Product Experience

- Sidebar search filters subjects, boards, papers, favourites, and recent combinations.
- Favourites and recent configurations provide one-click restoration.
- A first-paper flow guides provider setup, model choice, subject selection, save location, progress, preview, and quality interpretation.
- TipKit provides contextual, dismissible education; a searchable tutorial contains annotated current screenshots.
- The recommended Ollama model remains adaptive to Mac memory, clearly labelled, and accompanied by a warning that other models or quantisations may vary in quality.
- Apple MLX setup is a consented in-app transaction with plain-language explanation, progress, cancellation, diagnostics, and retry; users never need to interpret a `pip install` error.
- Native PDFKit preview and Quick Look expose question paper, mark scheme, and supporting files.
- Completion offers “Create another with new questions” and “Duplicate configuration”.
- Persistent history stores seed, provider/model, model digest when available, blueprint version, prompt version, syllabus version, renderer version, qualification manifest, outputs, timestamps, and terminal state.
- Window state and unfinished configurations restore safely after restart.
- Empty and error states give one clear next action.
- Sidebar and inspector adapt or hide at compact widths.
- VoiceOver, Full Keyboard Access, Increase Contrast, Reduce Transparency, Dynamic Type-equivalent macOS text sizing, localisation, right-to-left resilience, and reduced motion are release-tested.
- Toolbars, menus, settings, navigation split views, sheets, alerts, progress, materials, spacing, corner radii, and focus rings use native macOS conventions. No custom imitation of Liquid Glass is introduced.

## Reliability, Privacy, and Distribution

- Checkpoints and job history survive cancellation, process termination, renderer failure, low storage, corrupt cache, offline operation, and app upgrades.
- Writes are atomic; partially rendered files are never published.
- Model secrets remain in Keychain. User papers and calibration data stay local unless the user explicitly exports them.
- App Store and direct builds use separate, least-privilege entitlements and verify bundled helper signing, privacy manifest, hardened runtime, sandbox access, and dependency licences.
- CI runs Python lint/tests, Swift tests/builds, schema migration tests, deterministic matrix smoke tests, App Store preflight, and release artefact validation.
- Release qualification uses a clean machine and a supported low-memory Mac as well as the primary development Mac.

## Repository Organisation

The repository keeps source, durable derived metadata, fixtures, tests, and documentation. It removes obsolete generated output, duplicate scripts, abandoned package copies, editor/system files, stale screenshots, superseded plans, and unused assets only after reference and packaging checks prove they are unreachable. A machine-readable inventory records why exceptional generated or binary assets remain.

## Definition of Done

The programme is complete only when:

1. Every advertised paper generates a complete package from a clean setup with each supported provider path that is claimed in the UI.
2. Every paper passes engineering validation; every visually advertised paper passes 600-DPI role-specific and print/manual review; every empirically advertised paper passes expert/student/marker thresholds.
3. All 18 current papers have no unresolved visual gate; difficulty gates remain false until external evidence actually passes.
4. New families can be registered through the manifest, templates, subject plugins, and migration validator without copying orchestration or board furniture.
5. The macOS workflow passes HIG, accessibility, localisation, persistence, interruption, low-storage, offline, signing, sandbox, and clean-install tests.
6. The full test and release suite passes, Graphify is current, documentation matches behavior, `main` is clean, and no generated/reference/private data is accidentally tracked.

## References

- Apple Human Interface Guidelines: <https://developer.apple.com/design/human-interface-guidelines/>
- Designing for macOS: <https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/>
- Accessibility: <https://developer.apple.com/design/human-interface-guidelines/accessibility/>
- Onboarding: <https://developer.apple.com/design/human-interface-guidelines/onboarding/>
- Sidebars: <https://developer.apple.com/design/human-interface-guidelines/sidebars/>
- Settings: <https://developer.apple.com/design/human-interface-guidelines/settings/>
