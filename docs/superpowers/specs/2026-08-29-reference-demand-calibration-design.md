# Reference-Demand Calibration Design

## Purpose

Improve every advertised generator so that new AI-authored questions match the structural and cognitive demand of the relevant real papers more reliably, while retaining original wording and never claiming psychometric equivalence without student-response evidence.

## Current Problem

The project already freezes marks, command words, assessment objectives and broad `low`/`standard`/`high` demand bands. It also runs a second-pass editorial review. However, difficulty is currently only a short instruction inside a review covering many unrelated concerns. The model is not given an auditable description of what the requested demand means, the final package does not report how closely its demand distribution matches the relevant corpus, and AQA Computer Science and Edexcel Economics do not have the same reusable calibration metadata as the other advertised families.

## Design

### 1. Copyright-safe reference-demand profiles

A development tool derives aggregate fingerprints from the bundled official question-paper corpus for every advertised family and paper. Profiles retain counts, hashes, mark bands, command-word distributions and derived demand proportions only. They do not retain question prose, source paths or excerpts. Topic-bank profiles inherit the aggregate AQA Computer Science paper distribution but identify themselves as focused-practice derivatives rather than full-paper equivalents.

The committed resource is the runtime source of truth. A schema and registry validation ensure that every advertised paper has exactly one valid profile and that stale or partial coverage cannot ship unnoticed.

### 2. Item-level demand contracts

Each immutable blueprint item is converted into a compact demand target using its marks, command word, kind, AO allocation, expected time and the relevant reference profile. The target states:

- the intended demand band;
- a minimum reasoning-step range;
- whether explicit use of context/evidence is required;
- whether multiple concepts, data transformations, causal chains, comparison or judgement are required;
- the expected response mode and tariff fit;
- the aggregate real-paper comparison basis.

These targets are authoring constraints, not model-generated labels. They are injected into generation and repair prompts, making “harder” precise enough for a model to act on without exposing past-question text.

### 3. Separate difficulty review

Content correctness and difficulty calibration are reviewed in separate model calls. The existing editorial pass continues to check facts, answers, sources, ambiguity and marking. A dedicated difficulty judge then estimates reasoning steps and checks tariff, command-word depth, AO demand, contextual application, misconception resistance and fit to the reference profile. It must return structured findings and rejects both under-demanded and over-demanded items.

The judge receives the immutable target, specification scope, source context and candidate item. It does not receive historic question prose. Repairs include findings from both reviewers. Seeded or immutable items must also pass the difficulty judge before live publication.

### 4. Deterministic form-level demand audit

Assessment-package validation computes an auditable report from the final item set. It compares mark-band, command-word and intended-demand distributions with the reference profile, verifies every item has a complete target, and checks item-level structural signals such as AO2 context binding and high-demand analysis/evaluation requirements. Live output fails closed when the form is outside the reference tolerances. Preview output reports the comparison but remains explicitly non-release material.

The package manifest records the profile fingerprint and audit result so a generated form can be traced to the exact aggregate evidence used.

### 5. App experience and evidence wording

The Quality inspector adds a separate “Reference demand” result with profile coverage, distribution fit and the number of checked items. “Empirical demand” remains separate and pending unless student-response calibration has actually passed. Help explains the three layers clearly:

1. reference-shaped authoring and automated review;
2. independent subject-specialist review;
3. empirical student-response calibration.

This gives users useful assurance without presenting AI review as psychometric evidence.

## Supported Scope

All 21 advertised assessments are covered:

- AQA Accounting Papers 1–2;
- AQA Business Papers 1–3;
- AQA Economics Papers 1–3;
- AQA Computer Science Papers 1–2 and three topic banks;
- OCR Computer Science Papers 1–2;
- OCR Economics Papers 1–3;
- Pearson Edexcel Economics A Papers 1–3.

Unadvertised Cambridge foundations remain excluded until their official reference corpus and full generation paths are release-qualified.

## Failure Handling

- Missing or malformed profile: generation/package validation fails with a user-readable configuration error.
- Difficulty judge rejects an item: the item is regenerated with bounded findings; it is never silently accepted.
- Difficulty judge returns malformed JSON: normal bounded retry handling applies.
- Form-level distribution misses tolerance: publication stops before files leave the staging transaction.
- Student evidence is absent: the empirical flag remains false regardless of reference-demand success.

## Testing Strategy

Tests first cover profile completeness and validation, literal demand-target expectations, separate reviewer rejection/acceptance, prompt payloads, custom AQA Computer Science and Edexcel integrations, assessment-package audit output, manifest evidence, and Swift decoding. Full verification then generates every supported assessment in preview mode, validates all packages and PDFs, builds/tests the macOS app, runs repository/release hygiene, and refreshes Graphify.

