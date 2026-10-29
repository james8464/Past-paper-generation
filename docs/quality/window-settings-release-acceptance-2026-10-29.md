# Window and Settings release acceptance

Status: pending final source freeze, full regression tests, signed builds and
actual computer-control verification. This file reserves the release-evidence
path before identity-bearing model checks. It is not a passing acceptance record.

The scoped native gate passed 129 tests and the Python wiring gate passed seven.
Static review is recorded separately in the native scene boundary audit. Planned
actual checks include Settings-only cancellation, hosted disclosure cancellation
without consent or credentials, Help reopening Main, repeated menu navigation,
correct disabled states and preservation of user data and settings.

The Accounting retained-attempt review and qualification-boundary audit remain
separate. App-owned French trials must not be labelled live AI qualification.
No Store upload, credential change, official equivalence or complete HIG claim
is authorised by this pending record.

The later bookmark follow-up at `7fc9f427` has a failing-before-fix regression and
a 76-test focused pass. It reports persistence failure without changing successful
path/bookmark/security-scope behavior. This count overlaps the earlier native
suite and is not an additional 76 unique tests.

The exact-byte semantic-review ledger has 922 tracked files: 22 explicitly
reviewed, 666 pending and 234 excluded. Full-project semantic review is unfinished.
The AST graph update reports 44 files without nodes, including JSON configuration
files, and uses aggregate rendering above 5,000 nodes. Documentation semantics
were not re-extracted; graph navigation is not complete source coverage.

## Observed interface checks before the final rebuild

The first signed Release candidate ran alone as PID27988 from
`macOS/build/DerivedData/final-window-qualification-direct`. With Main closed,
Settings showed its own model-download confirmation. Cancel left the selected
model at `gemma4:12b` and started no download. Hosted disclosure also appeared in
Settings. Cancel kept consent unaccepted and generation on Ollama, but the
segmented provider control incorrectly retained an OpenAI highlight. This visual
failure was confirmed in both accessibility state and a screenshot.

After `916738ab`, the Debug candidate ran alone as PID29211 from `final-native`.
Repeating Settings-only disclosure and Cancel reset the visible selection to
Ollama (1), OpenAI (0), agreeing with the detail text. No consent was accepted.
The model guide reopened Main on Choosing a Model. Done followed by Documents
and History commands reused `main-AppWindow-1`; the Window menu listed only AI
Settings and one Main window. A document command also reopened the closed Main
window. The control tool retained the open Window menu until its exposed native
Cancel action was invoked; this was not treated as an application routing fault.

Benchmark and Privacy were restored, with Ollama, `gemma4:12b`, Downloads and
unaccepted hosted consent unchanged. Both candidates were normally quit and
process inspection confirmed no Keldin executable remained. No new paper,
benchmark, export, credential, clipboard, download or history deletion was
performed. Existing saved PDFs and old history were left intact. These Debug
checks do not replace verification of the final signed frontend.

## Retained automated checks

The preceding full Python attempt completed with 4,554 passed, one failed and
two skipped in 556.54 seconds. Its failure was the obsolete direct Help-method
spelling assertion after typed routing; the route is now asserted and covered by
native behavior tests. This is not a passing final full-suite result.

The new real-repository review check failed on the stale Settings service hash,
then passed after explicit final-file review and hash refresh. The combined
branding/repository/audit/interface checks passed 55 tests. Future CI now checks
actual tracked review attestations, not just isolated ledger fixtures.

Core `15ad925de29b2efbd10c1b0a7f520fd9aac4c10302d429ac92ac5f762d2b083d`
source and frozen public French trials each passed ten packages, twenty PDFs and
341 pages, all raster-identical to reviewed V35 run 2, with sixth-request refusal
and unchanged existing files. Frozen helper SHA-256 was
`6158ff7cf0fe4c05d2b1b940b66ed1648a855c339427bae17fd35df528cfc25e`.
These trials made no model calls. Recheck the rebuilt helper pin before inheriting
this frozen-artifact result.
