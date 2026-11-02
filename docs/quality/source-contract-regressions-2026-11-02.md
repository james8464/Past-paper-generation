# Public-source contract repairs, 2 November 2026

These repairs address reproducible implementation defects found against main
`67fb28fb`. No model calls or downloaded models were needed to reproduce them.
They do not qualify a model, calibrate difficulty or clear a live-paper hold.

## Accounting Paper 2

The writer and review stages received two generic extracts and a chart for
questions 11, 12.2 and 15.2. The rendered paper printed only the first extract.
Reviews could therefore assess material unavailable to candidates.

Those tasks now own an explicit source projection containing the printed first
extract. The existing independent cases for questions 16 and 17 are unchanged.
Projection metadata remains in the internal package rather than appearing as
technical prose in the correction appendix. The Accounting prompt identity moves
from v11 to v12; old checkpoints are not relabelled or deleted.

Writer, blind-solver, reviewer and difficulty-review regressions cover the source
boundary. Across both components and four seeds, blueprint data is unchanged
apart from the declared projection. All 124 pages of the seed-270101 subjects
and corrections are raster-identical at 72 dpi to the pre-fix render.

## Economics opportunity cost

A candidate could swap which product increased and which fell while retaining
all numbers and both labels. The deterministic solver and checkpoint validator
accepted the altered question but retained choices for the original task.

The calculation now binds each product to its before/after values, direction,
requested total quantity and answer unit. Validation consumes the complete
supported fact-and-task composition; extra assumptions cannot hide after a
recognised fragment. Existing shared-neutral-verb wording remains supported.

The writer receives the same public grammar, source fields and unsolved examples
used by validation. It receives no solved sacrifice, keyed choice or private
credit through this disclosure. Other operations receive no new field or
instruction. Shared source checks run before both disclosure and solving.

This is a bounded grammar, not a general natural-language interpreter.
Unsupported valid phrasing may be refused. Tests cover current generated stems,
supported paraphrases, existing compatibility fixtures, malformed source data,
role reversals and contradictory tails at parser, solver and checkpoint boundaries.
The existing independent-solver question with a preposed verb is unchanged.
A dispatch-only generic placeholder now supplies its case's public facts; its
expected solutions and mutation checks are unchanged.

## Business financial data

A balanced statement could still contain negative assets, non-finite values or
an undefined ratio. A zero-liability source caused division by zero; a balanced
zero-capital source made the stated ROCE undefined.

The existing Business adapter validation hook now checks these domains before
publication. Assets and liabilities must be finite and non-negative. Negative
finite equity remains valid. Positive current liabilities are required only for
current-ratio tasks; nonzero capital is required only for ROCE tasks. Tests cover
the actual adapter path and preserve normal generated calculations, including
the original issue's seed. No ordinary seed was shown to generate malformed data.

## Benchmark wording

Normal native testing verified start, cancel, restart and a completed 30-sample
diagnostic. Its old result promised comfortable generation with the selected
model even though the benchmark receives no model or provider identity.

The result now says the hardware check passed and explains that model speed and
paper quality were not measured. Scores and thresholds are unchanged. English
and French resources retain historical result labels for compatibility.

## Saved PDF access

Store-mode testing found that a generated PDF needed permission again after the
output folder changed and the app relaunched. The file still existed. Choosing
the exact file through the recovery control worked, including after another
relaunch. The missing step was remembering access when files were first saved
or opened successfully.

The app now records read-only bookmarks for every published PDF while the chosen
folder grant is active. Successful first loads also remember access. Recording
another document does not acquire or release the active reader's lease. Invalid
or unreadable PDFs are not recorded. A bookmark failure leaves saved files intact
and adds a nonfatal activity message. It does not turn a successful publication
into a failed job.

This uses the existing sandbox and already selected files. No entitlement or
library-validation setting changes. The approach follows Apple's guidance on
[persisting file access with read-only security-scoped bookmarks](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox).
Tests cover both published PDFs, private JSON exclusion, folder changes, a fresh
access controller, balanced leases and failure preservation. Runtime acceptance
of the final Store build is recorded separately in the pull request.

## Release boundary

Focused regressions preceded each fix. Independent review found the residual
Economics prose and zero-capital cases before integration; both were repaired.
Full release-suite and protected-check outcomes belong to the associated pull
request. Accessibility testing is excluded at the user's request. Existing
French manual holds, live subject/provider acceptance, rights and production
Store signing remain separate work.
