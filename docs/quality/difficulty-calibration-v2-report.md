# Difficulty Calibration v2 Qualification Report

Date: 30 August 2026

## Outcome

Difficulty Calibration v2 is implemented across all advertised assessment routes. It replaces tariff-only calibration with copyright-safe reference features and an item-level, independently solved difficulty gate.

## Implemented evidence

- Reference profiles are schema version 2 and cover all 21 advertised assessments.
- Each profile includes paired tariff/command aggregates, mark-weighted demand, response mode, cognitive operation, extraction coverage and per-metric tolerances.
- Every item target declares a lower and upper reasoning-step bound, required cognitive operations, context/data requirements, timing range, scaffolding ceiling and shortcut-resistance rule.
- Shared generators pass their canonical independent solution to a distinct difficulty reviewer and persist the result on the accepted item.
- AQA Computer Science and Pearson Edexcel Economics use the same solver-grounded review and persisted evidence contract.
- Live assessment packages fail closed if any item lacks passing difficulty evidence. Preview packages expose evidence coverage without implying that an AI review occurred.
- The macOS Quality inspector reports item-review coverage, reasoning-range fit, context fit, shortcut resistance, extraction coverage and maximum form drift.

## Verification

- Python: 775 passed, 2 skipped. The skips are pre-existing environment-dependent checks.
- Advertised preview matrix: 21 of 21 packages generated and passed the schema-v2 reference-demand audit.
- Maximum gated distribution distance across that matrix: 0.782174 (within the focused question-bank tolerance of 0.8).
- Minimum official-corpus extraction coverage: 0.793103.
- The corpus profile freshness check passed and retained no official question prose or corpus paths.

## Interpretation

The result supports a claim that generated items and forms are shaped to the observable demand of relevant official papers. It does not establish psychometric equivalence. That remains dependent on independent examiner review, student response data and marker agreement under the empirical-calibration policy.
