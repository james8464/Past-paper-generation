# OCR Computer Science Paper 2 preview uniqueness

This is a deterministic construction repair and offline publication check, not
live-model, examiner or educational qualification.

## Reproduction and repair

The actual public CLI at seed 270100 refused publication because questions 7(b)
and 9(b) repeated the same two-mark functions/procedures/recursion task and
credit. The original failure remains in the capacity worktree under
`tmp/nov2-output-integrity-public-cli/computer_science_ocr-paper-2/`.
The original matrix remains 20/21 successful publications; its failed attempt
has not been replaced with the repaired result.

Source commit `e1e1328c0b7890821b8e6b5f734dcdb8411840e7` reserves the original
assessed syllabus points before allocating unused same-topic points to colliding
generic short-answer tasks. Only Paper 2 uses this allocation. Calibrated tasks,
random draws, identifiers, marks, source data and publication gates are unchanged.
The finite pool fails closed when exhausted. Prompt and credit are constructed
together before normal marking enrichment.

Tests captured four expected failures before repair, including actual CLI
publication. Eight fixed Paper 2 seeds now pass the unchanged duplicate guard.
Both complete seed-123 blueprints retain their pre-repair canonical hashes.
At seed 270100 every model field outside 9(b) is unchanged; seed 2 similarly
preserves every field outside its colliding 7(a), including the later original
7(b) task. Renaming a duplicated item still fails the gate.

The focused OCR, calibration, shared-source and app-backend group passed 80 tests.
Ruff, formatting and the existing scoped mypy gate passed. No full suite or
native build was run for this change.

## Frozen-source public output and manual check

The unchanged public command with `--dry-run --seed 270100 --provider ollama
--model unused-offline` completed at the source commit above. Output, events,
manifest and hashes are retained in the identifiers worktree at
`tmp/nov2-ocr-preview-uniqueness/frozen-e1e1328c/`.

- Subject: 32 pages; SHA-256
  `f0bc976b9c254838cc243307ddede51a93f11eb66f56cdf6602e620fa33fd6f3`.
- Mark scheme: 27 pages; SHA-256
  `a3f9702593b4a04a92ec8e05b5f1786ecd303aa7dcc63341f0a4b159ca53733d`.

Both files retain the first-page preview notice and match their final manifest
hashes. Subject page 23 and scheme page 19 were read in full and inspected at
1,100 pixels wide. Question 9(b) now asks for two features of object-oriented
programming with reference to maintainability; its printed two-mark AO1 credit
is explicitly about object-oriented programming. This is a different assessed
concept from the unchanged functions/procedures/recursion task in 7(b), within
the same `algorithms-2` syllabus topic. Encapsulation and modular class interfaces
are relevant examples; no new numeric premise or pseudocode dependency is added.

The complete stored question/credit pairs were also read. No stale recursion
credit remains in 9(b), and no clipping was seen on the two inspected pages.
The marking remains indicative rather than a fully developed examiner scheme.
This targeted check does not claim manual review of the entire paper, measured
learner timing, live generation or model quality.
