# Release safety integration acceptance

This integration follows PR116 (`4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`).
It combines the scoped PDF, tooling, Core policy and native safety changes
described in their separate 29 October review records. Their focused tests
do not replace the gates below.

## Required final gates

Freeze maintained source and review-ledger bytes before running identity-bearing
tests. Record the exact Core/runtime pins and commit. Do not relabel retained
earlier attempts as acceptance of the new source.

- Fixed-source complete Python suite, with the declared static checker available.
- Complete native suite and personal-development-signed Store preflight.
- Signed direct Release build, strict bundle verification and exact helper pin.
- Current-source and rebuilt-helper French normal/enlarged catalogue generation,
  complete package/PDF validation, comparison with the previously reviewed pages,
  and unchanged-output refusal after all five finite families are used.
- Separately labelled zero-model-call render regression of the accepted MLX
  Accounting package; preserve the actual installed PR116 live output unchanged.
- Read-only integration review and both latest-head protected checks before merge.
- Squash-tree verification, clean primary main, exact topic cleanup and installation
  of the tested merged bundle without losing user history or documents.

## Fixed-source local results

The production source and review ledger were frozen at
`61d8ce6af0867840f818384aa4f4f6a009728c10`. The subsequent correction only
isolates two SwiftUI test callers to the main actor and updates this report and
derived graph. Core, runtime data, Python tests and production Swift bytes are
unchanged by that correction.

| Identity | SHA-256 |
| --- | --- |
| Core | `08edc0abb2c29afb3da1cca60cbdfb4b354389b5371f737ea39af71a6ee726e0` |
| Runtime | `20d5c507964d8d282fd6582a4fcac49a5759434e050d6c43194597a62cb12536` |
| Signed direct Release frontend | `e9db3e8709de453382131a68bf8d864c75bbcc1538d6d77aca8382322bd2e3d0` |
| Signed direct frozen helper | `02abcb65f893e1ceac065b51196b4bab433b8284a817fdd3210b4a2fe7645088` |

All evidence paths below are retained under the isolated checkout's ignored
`tmp/`. They remain separate from the real installed PR116 live output.

| Gate | Result and evidence |
| --- | --- |
| Full Python | 4,646 passed, two skipped, five third-party warnings in 856.55s; `release-safety-full-python-final.log` |
| Full native | 261 passed before the test annotation correction, then 261 passed afterward; `release-safety-full-native-final.log` and `release-safety-full-native-final2.log` |
| Store preflight | Personal-development-signed Release passed, including sandbox/helper entitlement and strict-signature checks; `release-safety-store-preflight-final.log` |
| Direct Release | Build and strict deep signature verification passed; `release-safety-direct-release-final.log` |
| French current source | Ten packages and 20 PDFs, 341 pages; complete content/order/A4/footer/nonempty/graph checks passed. All 341 full-page 100dpi rasters equal the reviewed V35 run 2; sixth normal/enlarged requests refused without changing existing outputs. `pdfs/release-safety-french-source-20261029/summary.json` |
| French frozen helper | Same ten-package/341-page acceptance and unchanged-output refusals. Full-page rasters equal both current source and reviewed run 2. Frozen/source implementation identities stay distinct, and source validation still rejects the frozen identity. `pdfs/release-safety-french-frozen-20261029/summary.json` |
| Accepted MLX content, offline render regression | Current renderer reproduced all 36 question and 24 scheme pages with identical text and 100dpi pixels; strict scheme/conformance checks passed. No model calls or new visual review. Original live artifacts remain unchanged. `mlx-current-render-regression-20261029/summary.json` |
| Static and repository checks | Ruff lint/format, strict mypy for three leaves, review-ledger validation, Graphify AST update and inventory checks passed. Ledger: 940 files, 110 explicitly reviewed, 589 pending, 241 excluded. |

The Python suite continued progressing through costly French PDF cases during
the longer run; a read-only sample and collection-order check did not establish
a hang or a new performance defect. The completed result is retained. No
unchanged full Python rerun was needed for the Swift-test-only correction.

## Protected CI follow-up

PR117's initial macOS job failed during compilation: the runner's SwiftUI SDK
isolates the view's static label helper to the main actor, while two new test
methods called it from a nonisolated context. Existing hosting tests already ran
on that actor. The two label tests now do too, with all assertions retained and
no unsafe isolation escape or production change. The corrected complete native
suite passes 261 tests. The original job logs and diagnostics are retained at
`release-safety-ci-macos-job.log` and `release-safety-ci-macos-diagnostics/`.
Both updated-head protected checks are still required before merge.

Separate read-only agents reviewed PDF safety and Core policy changes they did
not author; neither found an additional actionable regression within its scope.
The actor-only test correction also received a read-only review. These are
implementation reviews, not teacher review or whole-project clearance.

## Scoped Safari and native interface checks

Apple's [Printing](https://developer.apple.com/design/human-interface-guidelines/printing)
and [Pop-up buttons](https://developer.apple.com/design/human-interface-guidelines/pop-up-buttons)
articles, including macOS considerations, were read in a separate Safari
window. They support contextual File-menu actions, system print options and a
space-efficient mutually exclusive document selector. The candidate selector
fitted 30 PDFs at full and half width. Confirmed selections printed the correct
24/36-page targets, with both panels cancelled. Immediate unacknowledged
accessibility inputs remain an automation-ordering limitation; no physical-event
race closure or every-keyboard/VoiceOver interaction claim is made.

No printer was selected and the system's final Print button was disabled.
Physical printer configurations remain untested. Only the dedicated guideline
window was closed; other Safari tabs, including a newly opened sign-in tab,
were preserved without authentication or consent actions.

## Remaining acceptance

Latest-head protected CI, merge, clean main, exact topic cleanup and final
installed Release acceptance remain pending. The installed PR116 copy is still
preserved. Computer control caches an obsolete identifier for its canonical
path; an exact-path Launch Services registration refresh did not repair that
tool lookup. A temporary symlink attempt was removed after validating its exact
target; no running bundle or user data was moved during that attempt.

Graphify reports 44 source files without extracted nodes, including JSON/data
files. Its structural update is not semantic coverage of those files. The
real installed PR116 MLX sample retains its own fixed-byte acceptance report.
No finalisation or new installed-build acceptance is claimed here yet.

Teacher review and empirical learner calibration remain unperformed. The French
catalogue is finite and explicitly uncalibrated. Distribution credentials,
per-document rights and applicant submission fields remain external. These
engineering gates supply no App Store approval, official-paper equivalence,
whole-HIG certification or repository-wide semantic-review completion.
