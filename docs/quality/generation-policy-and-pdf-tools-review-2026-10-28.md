# Generation-policy and PDF-tool boundaries

## P3: generation policy

GenerationPolicy now checks counts at construction: batch size, attempts and
worker count must be positive non-Boolean integers. Similarity limits must be
finite numeric values in the existing closed range 0–1. Zero remains maximally
strict; one still rejects exact duplication because the comparison is inclusive.
No arbitrary count cap or unrelated review-flag change was introduced.

The regression suite failed 44 invalid-input cases against the previous policy,
with nine valid cases already passing. The subsequent combined policy, AI,
checkpoint and MCQ suite passed 154 tests after the separate formatted-option
repair. Logs: `generation-policy-validation-{red,green}.log` and
`mcq-formatted-options-{red,green}.log` under `tmp/final-validation-20261028`.

## T4: bounded PDF subprocesses

Accounting, Business and OCR Economics calibration tools share a small PDF
inspection helper. Both pdfinfo and pdftotext have a 30-second deadline.
Timeout, missing executable, failed command and invalid page count errors name
the affected tool and document. Successful extracted text is returned unchanged;
subject-specific parsing, report fields and fingerprints are not consolidated.
The existing private helper names remain aliases, including direct-script use
from an unrelated working directory.

The boundary regressions failed 33 cases against the old implementation, with
three cases already passing. The focused helper and existing report suites now
pass 48 tests; Ruff passes. Logs: `pdf-process-{red,green}.log` under the same
evidence folder. No PDFs were rewritten and no live generation was run for
these tests. Broader calibration refactoring remains package T8, not completed
by this bounded-process change.
