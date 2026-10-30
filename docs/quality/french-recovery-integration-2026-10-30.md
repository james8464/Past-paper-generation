# Private recovery integration

The private candidate combines the two-round generation and replay path with
the evidence store. Main and the installed PR136 build are unchanged. This is
not release acceptance or a live-model quality result.

Only a fully validated semantic refusal enters a second whole-exercise cycle.
Accepted earlier exercises stay fixed. Returned author, blind-solver and
reviewer objects are retained with their hashes. Replay reconstructs requests,
admission checks, refusals and final links. Signed phase-seed edge tests caught
overflow before the fix; both author and reviewer seeds now wrap correctly.

Completed rounds invoke a defensive-copy recording callback before another
model call. A storage error stops generation rather than silently losing the
record. Terminal refused snapshots include the refusal fields required by the
replay validator. A new regression caught their omission before that fix.
The callback does not turn storage into approval; teacher review and learner
calibration remain `not_run`.

The runtime writes snapshots in its private job output, without emitting user
document events for them. Native generation already supplies an Application
Support job directory and exports only user-facing documents. Developer CLI
callers must also choose a private working directory; the store does not infer
privacy from an arbitrary `--output` argument.

Native completion now requires the exact string
`fr-nsi-v36-whole-exercise-redraft-v1`. A small Swift/Foundation harness compiled
the production validator and passed six publication-boundary cases after the
red run. The XCTest source parses, but the full native application suite and
signed builds have not run for this candidate.

The generation/replay change passed 399 focused tests before the seed follow-up;
149 focused tests passed after that follow-up. Those scopes overlap. The first
integrated scope passed 193 tests. Recording tests were red before wiring; the
wired scope passed 187 tests. The terminal-snapshot replay regression then
failed and its corrected scope passed 110 tests. These are separate scopes,
not numbers to add or a whole-suite result. Logs remain in
`tmp/final-validation-20261030/recovery-*` and the contributing worktrees.

Release work remains: retention, total elapsed-time and spending controls,
honest capture of partial nonsemantic failures, full native and packaged CLI
acceptance, a frozen-source full regression run, protected checks and a fresh
live French paper review. The 24-attempt bound concerns current sequential
typed inference clients, not ancillary HTTP requests, wall-clock duration or
remote billing after cancellation. No model calls were made for this change.
