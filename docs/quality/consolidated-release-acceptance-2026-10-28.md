# Consolidated release acceptance

This is a release-work record, not a declaration that Keldin is finished or
approved for the App Store. Pending checks remain explicitly pending.

## Frozen engineering checkpoint

At `a93ecb86f472387b34e1e03b5ecf09670a2b53d1`, the full Python suite passed
4,484 tests with two skips and five third-party PyMuPDF warnings in 530.61 seconds.
Both skips concern an unpopulated optional local Computer Science notes folder;
the two cases were separately rerun with skip reasons. The native suite passed
215 tests. Personal-development-signed direct Release and Store-mode preflight
builds passed. This is not Apple Distribution signing or upload approval.

Core/France implementation identity before and after the full suite was exactly
`1d373ab671e45844de0bfa076d3effea6d2c0c807d20e3cdea3b927d4ecc21d9`.
Retained logs are `tmp/consolidated-audit-full-suite.log`,
`tmp/consolidated-audit-full-native.log`,
`tmp/consolidated-audit-{direct-release,store-preflight}.log` and
`tmp/consolidated-audit-optional-notes-skips.log`.

## Current-source French public route

Ten real application-owned runs generated all five families in normal and
enlarged print. Repeated preferred seed 270100 selected 270100 through 270104 in
each output root. Both sixth requests refused without changing any existing
output or checkpoint bytes. No history was cleared.

All 20 PDFs, 341 pages, passed complete source/order, graph, A4, footer and
nonempty-body checks. Every full-page raster at 100 dpi is identical to retained,
previously reviewed V35 run 2. Fresh review covered the fifth family's nine
normal subject pages and five correction tails; other visual coverage is exact
raster inheritance, not a claim that all 341 pages were freshly viewed again.
Question/key chains were reread and marks independently summed: three six-point
technical exercises and two separate indicative language points.

The official 2026 Métropole day-1 comparator was reread, and all 16 pages were
rendered and viewed. Its SHA-256 remains
`275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`.
No new correctness or layout blocker was found. The five-family catalogue is
finite. Difficulty and duration remain uncalibrated; question/page counts alone
do not establish equivalence. No teacher review or learner timing was invented.

Evidence is retained under
`tmp/pdfs/french-v35-current-source-20261028-a93ecb86/`: summary.json,
internal-review.json, source-freeze.json and both sixth-refusal reports. All
artifact hashes are in summary.json. This is public catalogue acceptance, not
live AI qualification. Frozen-helper and final native checks are still pending.

## Final native follow-up

The a93ecb86 direct Release exposed enabled New Paper/Create Paper menu entries
while Quality Review and the optional French Review sheets were open. No
creation command was invoked. Empty-review Save was disabled; Cancel worked.
The original visible workspace/expansion state was restored before quitting.
No review record was fabricated. The native-only fix at `19e8827` uses the
existing presentation flags and a scene-focused modal context. No duplicate
global sheet state was introduced. The full native suite passed 219 tests;
personal-development-signed direct Release and Store preflight builds passed.
Logs are `tmp/consolidated-final-full-native.log`,
`tmp/consolidated-final-direct-release.log` and
`tmp/consolidated-final-store-preflight.log`.

Computer control reopened that direct Release. New Paper, Create Paper,
document actions and latest-document preview commands were disabled in both
Quality Review and the empty French Review sheet. Dismissing each sheet restored
the creation commands. Save review remained disabled, no fields were filled and
no review was saved. No generation, export or clipboard action was invoked.
The original Benchmark selection and collapsed Accounting section were restored,
and the candidate was closed. Output-folder/reveal menu entries remain available;
this observation does not claim every menu action is blocked by every sheet.

The source-level document-command regression now follows the shared navigation
guard instead of requiring the old duplicated welcome/help checks. All 52
targeted interface, branding and inventory tests pass. Native behaviour tests
independently exercise all six existing global presentation flags and local
modal restoration, including the French enlarged-print choice.

Selected-language notification copy has English/French unit coverage. Its delivery
cannot be claimed without OS authorization and an actual delivered notification.
No new permission or credential access is authorized by this record.

## Live model and publication gates

The final frozen helper probe exposed a missing acceptance check: its healthy
result covered only the three historical French families. The fix at `6ced2de`
retains those legacy render/catalogue checks and also validates all five current
V35 source families, typed exercises and their catalogue. The diagnostic reports
the current prompt version and family count. Five regressions failed before the
fix; seven probe tests and 55 related registry/pipeline tests pass. Evidence:
`tmp/bundle-public-family-{red,green,related-green}.log`.
No immutable French exercise source was changed. This CLI edit changes the Core
implementation identity, so the a93ecb86 source acceptance above remains a
historical checkpoint rather than acceptance of the new final identity.

The new Core identity is
`babc3dec7917ce725217d83c0146098c312ff14562497a247052216aac4033cc`.
Its repeated current-source acceptance also passed all ten packages and 341 PDF
pages, including both unchanged-output sixth refusals. All page rasters remain
identical to reviewed V35 run 2. Evidence now also exists under
`tmp/pdfs/french-v35-current-source-20261028-final/`; summary.json has SHA-256
`005ce9f5b66e0888cbea1156825b3b30a6b13a5f2ba13d8bb4a420c3424bf30a`.
This rerun inherits the earlier exact-raster visual coverage; it is not another
claim that every page was freshly viewed.

Separate frozen-helper acceptance then passed the same ten packages and 341
pages. Every raster matches both the final source and reviewed V35 run 2. Both
sixth refusals preserved all existing output/checkpoint bytes. The exact direct
Release helper SHA-256 remained
`7857708915a9cc8180fbc79fe5b7c0876f59cd1e36e630492f3fb0b591960c58`.
Its implementation identity is
`01573f02623a8508549a02ad561b215c2b2dce7717f36a15a65e5218e5e64c4a`.
Production source validation still rejects these actual frozen identities, as
intended. Independent content comparison excludes only implementation identity
and its dependent evidence digest; it does not rewrite packages or loosen
validation. Evidence: `tmp/pdfs/french-v35-frozen-final-20261028/summary.json`,
SHA-256 `7f2ced233ba49dda42b700becca976457f6a630bcf18146d80216004a7b1aa5a`.

A fresh pinned V11 Accounting Ollama run is RUNNING, not accepted, under
`tmp/final-v11-accounting-live-20261028/`. Complete-paper MLX acceptance is NOT
RUN. Earlier V10 Accounting automation success remains a historical manual HOLD
and is not relabelled as V11 acceptance. Final installed-app interaction,
latest-head protected checks and publication remain required.

The next Python gate was deliberately interrupted before later fixes:
`tmp/consolidated-release-final-full-suite.log` records 2,050 passes and a
KeyboardInterrupt after 357.16 seconds, not a full-suite pass. Subsequent source
review reproduced a post-spawn process-cleanup gap. `8d5c675` moves deadline
initialisation into the existing cleanup guard. The failing fake-clock test then
passed with 32 related cases, including real timeout, termination and descendant
cleanup tests. Logs: `tmp/post-spawn-cleanup-{red,green}.log`. The Core and live
runtime identities remain unchanged; the already-started Accounting child was
not stopped or altered by this tooling-only fix.

`d52024e` fixes two further native discovery findings. Collected output now uses
the same strict complete-byte-line decoder as streaming output, reports malformed
events and silent nonzero exits, and preserves explicit backend errors. The old
String split also mishandled CRLF event boundaries. Implicit direct-development
root discovery now walks the source ancestors instead of stopping one directory
too early. Store builds still refuse all repository fallbacks. Fake processes
and a controlled real refresh caller reproduced six failing assertions across
eight tests; 94 focused native tests then passed without skips. Evidence:
`tmp/backend-discovery-{red,green}.log`. Existing invalid UTF-8-in-JSON tests remain
green; the strict buffer itself was already correct and was not changed.

The final full Python/native and signed packaging gates are being repeated after
these actual fixes. Earlier successful builds remain historical evidence, not
acceptance of this later frontend. Core/French and live runtime identities remain
the two exact hashes recorded above, so the current paper run was not restarted.

The canonical local app currently contains protected PR112, matching its tested
direct Release frontend/helper bytes and strict signature. Its predecessor is
recoverable as `Keldin-before-PR112-20261028.app` in Trash; user data is retained.
The current audit branch is not yet that installed release. Personal Distribution
identity, third-party rights and applicant information remain external. No
whole-HIG, whole-project semantic-review or official-exam-equivalence claim is made.
