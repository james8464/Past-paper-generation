# Accounting Paper 2: explicit budget assumptions

Source commit: `27fc56d786aa264b22a40ed947a9429cba7cf62b`.

Question 13 supplied cash receipts/payments but asked for profit without stating
their relationship to period revenue/expenses. Its arithmetic was correct under
an unstated assumption; the printed facts did not exclude prepayments, accruals,
inventory movements or non-cash charges. This was an owned static-task premise
gap, not a model-answer or rendering repair.

The shared public statement now reads:

> Assume sales receipts equal revenue earned in this budget period, and variable-
> and fixed-cost payments equal expenses incurred in it. There are no inventory
> changes, accruals, prepayments or non-cash charges. The capital payment purchases
> a non-current asset; there are no other transactions.

The same unsolved statement appears in the candidate prompt and existing public,
protected `independent_solver_instructions`. No solved amount or calculation
method was added to those givens. The blind projection retains the statement and
removes private answer keys. Current immutable-prompt/context bindings reject an
author or checkpoint that drops, changes or removes the declaration. The solver
also refuses declared assumptions inconsistent with the printed prompt.

Historical budget records without this declaration retain their original numeric
reading and rendering. No assumption is injected into old packages, and no old
identity or PDF is retagged. Strict `source_data` fields, numeric contracts,
arithmetic, eight marks and existing credit remain unchanged. Tests also retain
the complete prior non-budget content and numeric contracts for both components.

## Regression and frozen-source CLI evidence

The initial run had six expected failures and two passing legacy/numeric controls.
All nine new premise/binding/privacy/compatibility cases now pass. The focused
Accounting, independent-solver, AI-assessment and shared-source group passed
133 tests. Ruff, formatting and the existing scoped mypy gate passed.

A frozen-source CLI preview at seed 270100 completed public finalization:

- Subject: 36 pages; SHA-256
  `081bffc1cfb823f86af5be977371a6bb7206308dbb82dc2a6a58e90584e41424`.
- Mark scheme: 12 pages; SHA-256
  `e78d3ef5b040a86a0afd3758a30daeef850b10964888b15790ce674a302b0b94`.

Both hashes match the final manifest. The new-assumption pages, subject 10 and
scheme 5, were read in full and visually inspected at 1,100 pixels wide. The
statement, unchanged cash figures and eight credit rows are legible; no clipping
was seen. Root's complete baseline/new raster comparison identifies exactly
three changed pages: subject 10 and scheme 4–5; the other 45 pages are unchanged.
Root inspected all three changed pages at 1,100 pixels wide: the complete Q13
table retains all eight awards, the sparse scheme page 4 is legitimate, and no
clipping or overlap was seen. That comparison and its images are retained in the
capacity worktree at `tmp/pdfs/nov2-budget-assumption-root-review/`.

Retained pre-repair objects were separately rerendered: all 48 legacy
pages have identical text geometry and raster bytes, and the original PDF/JSON
files remain unchanged.

Logs, baseline/new output, legacy-render comparison, `qa.json` and page images are
retained in the identifiers worktree at
`tmp/nov2-accounting-budget-assumptions/`.

This ran the repository's source CLI, not a newly built PyInstaller executable
or installed application binary. No live model calls, native build, full suite,
learner timing or examiner/teacher qualification is claimed by this evidence.

## Historical baseline follow-up

The first integrated full suite found one obsolete comparison: its 102-seed
content digest predates the new printed premise. That run returned 6,427 passes,
one failure and two skips; it was not accepted as a release pass.

The historical projection now removes only one exact, declared budget-premise
addition, after asserting its public declaration and printed occurrence. The
original expected hash is unchanged. Mutation canaries for budget and nonbudget
questions prove that other prompt changes still alter that hash. Dedicated
premise tests continue to require the current printed and public forms. A shared
digest helper lets the canaries check that property without calling another test.
All 63 focused historical, premise, projection and private-credit checks passed.
A separate read-only review found no scoped issue in this test-only follow-up.

Application, backend, runtime resources and build tools remain byte-identical to
the integrated `ac99602e` acceptance source. Its 401 native tests (one skipped,
no failures), direct/Store-mode release checks, complete 21-component source and
packaged preview trials, and two successful native preview operations apply to
those unchanged production files. Original manifests retain their actual source
identities. The revised test head still needs a fresh full Python pass and both
latest protected checks before merge.
