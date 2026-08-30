# Difficulty Calibration v2 Design

## Purpose

Generated assessments must match the cognitive demand of the relevant official A-level paper while remaining wholly new. Calibration must evaluate what a candidate actually has to do, not merely the declared mark tariff, command word, or blueprint label.

## Safety and truthfulness

- Official papers may be analysed only into copyright-safe aggregate features. No official question prose is stored in prompts, profiles, packages, or generated output.
- Automated calibration is evidence of reference-shaped demand, not psychometric equivalence. The product must continue to state that examiner review and learner trials are required for an equivalence claim.
- Live generation fails closed when an item lacks a passing difficulty review. Preview output may expose incomplete evidence but must not imply that it passed a live AI review.

## Architecture

### Reference profiles

Profile schema version 2 adds mark-weighted demand, response-mode and cognitive-operation distributions, per-metric tolerances, and extraction coverage. The corpus builder pairs marks with nearby command phrases where reliable, applies explicit published MCQ-block rules, records pairing coverage, and stores aggregates only.

### Item targets

Every blueprint item receives a concrete demand contract containing a minimum and maximum reasoning-step range, required cognitive operations, response mode, context and data-transformation requirements, expected-time range, scaffolding ceiling, and shortcut-resistance requirement. These requirements are included in generation and repair prompts.

### Independent calibration

The existing independent solver remains separate from the authoring pass. Its canonical solution trace is supplied to a dedicated difficulty reviewer, which judges actual solution depth, tariff fit, context dependence, cognitive operations, timing, scaffolding, and whether recall or a shortcut can bypass the intended work. A structured `difficulty_evidence` record is attached to accepted generated items.

### Form-level release gate

The assessment package audits mark-weighted demand and item-level review evidence in addition to mark bands and command families. Live packages must have passing evidence for every item; profiles with insufficient extraction coverage cannot support a live release. Reports expose the exact observed/expected distances, review coverage, and failure reasons.

### Specialist generators and product UI

AQA Computer Science and Edexcel Economics use the same target, solver-grounded review, and evidence schema as shared generators. The macOS quality report surfaces calibrated-item coverage, reasoning-range fit, context/shortcut checks, and extraction coverage without claiming empirical equivalence.

## Acceptance criteria

1. All advertised papers have valid schema-v2 profiles derived from the current official corpus.
2. Difficulty targets set both lower and upper bounds and observable operations.
3. Generation and repair prompts explain the item-specific demand contract and prohibit superficial context dressing.
4. Difficulty review receives an independent solution and rejects under-demanded and over-demanded items.
5. Every accepted live item persists a passing evidence record; package revalidation detects tampering or missing evidence.
6. The form audit uses mark weighting and reports all gated distances and evidence coverage.
7. Specialist generators conform to the same review contract.
8. Automated tests, all-family preview qualification, strict macOS build, App Store preflight, repository inventory and Graphify update pass.
