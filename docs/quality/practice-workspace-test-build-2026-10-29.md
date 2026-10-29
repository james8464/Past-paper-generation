# Practice workspace test build

Date: 29 October 2026

The user asked to simplify repetition controls, make generation progress visible,
and reduce the space used by Recent Documents. With 10% usage remaining, the
immediate target is a usable signed testing build. Whole-repository audit and
release qualification are still incomplete.

## Interface changes

One shared progress bar now sits outside the disabled settings form, at the
bottom of the main window. It remains visible when navigating to History or
Documents. It uses actual backend progress and status, shows the existing time
estimate when available, and offers Cancel. Unknown progress remains
indeterminate; the interface does not invent a percentage or completion time.

Independent review now advances through the existing 78% to 82% review stage as
each preceding question finishes. It does not count the question still being
reviewed as complete or imply a time estimate. Invalid counts leave progress
unchanged. Legacy status messages no longer move the indicator backwards.
English/French status copy says which question is being reviewed; the original
backend message remains available in diagnostics.

Recent Documents starts collapsed. Expanding it reveals a 160-point table
instead of occupying the lower half of the window. Existing document preview,
Finder actions and output-folder access remain available. Configuration receives
the remaining space and can scroll rather than being capped at 390 points.

Three source-structure regression tests failed before implementation, then passed.
An additional regression for the shared main-window progress location failed
before that relocation and passed afterward. The related layout/copy/contrast
selection passed 14 tests. These are structural checks, not a replacement for
native visual acceptance.

Final combined focused Python checks passed 275 tests, with five third-party
deprecation warnings. Repository inventory/audit-ledger/layout checks passed
42 tests. The focused native gate passed 147 tests with no failures; the earlier
migration/history boundary gate passed 72. The first native attempt failed to
compile a test that tried to set a private seed. Its fixture was corrected to
capture the real requested seed; no production setter was exposed. That failed
log is retained and is not passing evidence.

The reviewer read the complete generation workspace, shared progress component,
French workspace, main navigation view and new layout test. Help and catalogue
changes were reviewed as scoped copy changes. Existing translations and saved
user catalogue entries are retained; four English/French entries describe the
new repetition policy without claiming originality.

## Repetition policy

UK generation permits overlap with earlier papers under `repeat-practice-v1`.
Answer correctness, source fidelity, within-paper duplicate rejection and item
review checks remain. Historical overlap is reported without blocking publication
or being presented as an originality pass. Strict comparison remains available
to historical and diagnostic callers.

French practice still uses five app-owned families. The app prefers unused
families, then permits their reuse. The explicit practice policy does not clear
saved history or change retained V35 source/package reconstruction. References,
answers, marks and duplicates within the current paper remain checked. An exact
request that collides with an existing destination still refuses to overwrite it.
The normal app flow creates a fresh random seed for each request.

## Acceptance boundary

The first protected Backend run completed with 4,722 passes, two skips and one
failure: a test still required the old French repeat-blocking sentence. Its
expectation now matches the requested repeat-practice wording while retaining
the bilingual/non-AI provenance assertions. The failure was reproduced locally
and retained in `tmp/french-repeat-ui-copy-red.log`.

The progress follow-up reproduced three failures before implementation and then
passed 41 related Python tests. The English/French review-status test first
failed its four expected text assertions; the final complete native suite passed
272 tests. This follow-up changes progress presentation, not paper content,
provider requests, quality thresholds or the stored original diagnostic message.
Latest-head protected checks remain a separate merge gate.

The currently running user Xcode Debug app was observed creating an Economics
paper. Its old progress control was inside the disabled form. That generation
was not cancelled, replaced or counted as acceptance of the changed interface.

The signed Release build is a separate delivery gate. A successful build
does not establish full HIG compliance, complete interaction coverage, paper
difficulty equivalence or Store approval. Existing French/UK quality limits and
the missing Distribution identity remain recorded separately.
