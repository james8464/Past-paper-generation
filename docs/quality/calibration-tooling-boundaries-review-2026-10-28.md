# Calibration tooling boundaries and versioned reports

## Scope

This T8 batch covers the five maintained AQA Accounting, AQA Business, OCR
Economics, OCR Computer Science and AQA Economics calibration tools. It also
repairs specific migration-validator and scaffold boundaries, and states the
release dependency check's actual scope. It does not change Core generation,
native code, subject parsers, syllabus content or qualification records.

## Shared operations and retained byte contracts

`tools/calibration_common.py` supplies typed integer bands and sorted sequence
frequency rows. An empty band retains its ValueError; an empty sequence inventory
retains an empty list. Medians retain their integer or floating-point type.
Document fingerprints still hash each basename followed by its raw content
digest in caller order. No sorting, path-prefix addition or hash migration is
hidden in that extraction. JSON rendering retains two-space indentation,
unescaped Unicode, insertion order and a final newline.

Before extraction, nine characterisation cases passed for the existing helpers.
They remain green afterward. The two remaining unbounded PDF call sites, OCR
Computer Science and AQA Economics, now use the existing 30-second Poppler
boundary. Their six timeout, zero-page and exact-output cases failed before
repair. Subject parsing and reference document selection are unchanged.

## Version 2 content metrics

The former complete-model fingerprints included the seed. A different seed
could therefore count as a different paper even if the assessed content did not
change. The new `public-candidate-content-v2` projection excludes run seeds and
private credit. It includes printed prompts and alternatives, projected public
case inputs, and shared source used by the task. It reuses the Core source-scope
and private-key exclusion rules. Ordinary public credit columns remain inputs.
Unrelated planning titles and extracts do not create artificial variety.
This is a scoped input projection, not an exhaustive printed-page identity.
Private `required_entries` ledger placements and unproven derived
`calculation_variables` are excluded. Selected-response inputs and rows bind the
table operands and diagram geometry used by the Business and Economics renderers;
solved-choice metadata is excluded. Nested public fields named `seed` remain
data, unlike the top-level run seed.

The v2 fields explicitly count candidate-content and public-source fingerprints.
They measure exact projected content differences, not semantic novelty,
difficulty, curriculum equivalence or learner performance. Tests give every
tool identical content with different seeds and require one content fingerprint
and a failed uniqueness check. Other cases change public input values or choices
and require different fingerprints, while changes to private credit have no
effect.

Accounting Paper 1 now hashes its owned public cases instead of the intentionally
empty shared planning stimulus. Its MCQ operation check uses the declared typed
operation fields, not the former literal lowercase `revenue of` count. Paper 1
declares four transforms. Report counts are labelled `declared_transform` and
`other_or_unspecified`, so undeclared Paper 2 operations are not described as
observed conceptual demand. This tooling change does not add missing operation
annotations to Core.

All five new report builders declare schema version 2 and the content policy.
CLI writes and checks use `difficulty-calibration-v2.json`. Atomic publication
uses the existing reviewed JSON writer. A missing v2 report fails before reading
the corpus or generating samples; it cannot fall back to an older PASS. The
legacy `OUTPUT` aliases and all five historical v1 report files remain unchanged.
Registry links still refer to that historical v1 evidence and cannot establish
current-source v2 acceptance. No real v2 corpus report was generated in this
batch.

## Other false-green boundaries

Migration `--all` validation now refuses a missing, malformed, unsupported or
empty advertised registry. Schema versions require exact supported integers;
floats, Boolean values and container values raise the same actionable error.
It cannot turn an empty report tuple into success.
The current seven advertised families still pass the no-preview validator.
Scaffolding rejects invalid Python package identifiers, duplicate paper IDs and
noncanonical or non-string paper IDs before writing files. The generated test
actually calls the fail-closed adapter, requires its refusal and checks that no
output was written. Replacing that adapter with a function returning an empty
mapping makes the generated test fail.

The release report now lists the requirement manifests it checked and explicitly
states that editable-project constraints and transitive resolution were not
checked. Its existing root-manifest upper-bound check is unchanged. No installed
dependency failure or complete dependency-policy audit is claimed. Selecting
upper bounds for every editable project remains a separate dependency-policy
decision.

## Evidence and limits

The initial new-boundary run failed 20 cases and passed nine characterisations.
The remaining-PDF run failed six cases. Five more cases then reproduced missing
v2 checks doing unnecessary corpus/generation work before refusal. Logs are
`tmp/tooling-calibration-boundaries-red.log`,
`tmp/calibration-remaining-pdf-red.log` and
`tmp/calibration-missing-v2-red.log`.

The final bounded gate covers new boundaries, existing PDF helpers, retained
calibration report assertions, release checks and no-preview migration. CLI help
is exercised through direct-script and module entry points with PYTHONPATH
cleared. The expensive existing all-family preview case is excluded from this
targeted run. A further three red projection tests reproduced private-working
inclusion and missing selected-response input/row identity; the nested public
seed characterisation already passed. The registry schema follow-up reproduced
four failures; both Boolean cases already refused. The final run passed 130
tests, with one expensive preview test deselected, in 3.92 seconds. The result is recorded in
`tmp/tooling-calibration-final-green.log`. Ruff and the diff whitespace check
pass. No historical report JSON, live model output, official PDF, native build
or full-suite result is rewritten by this batch. Teacher review and observed
learner timing remain unperformed.
