# Native history, credentials and publication integrity

Implementation audit packages N5, N6 and N7 address three different persistence
boundaries. This branch starts from protected main PR109. It does not change
French exercise content or claim paper qualification.

## N5: history deletion and retention

Explicit removal treats an already absent record as success. Other deletion
errors keep the record visible and reach the application alert. Generated PDFs
are not deleted. Retention attempts obsolete records individually and keeps
failed deletions visible with retryable maintenance warnings. A cleanup failure
cannot make an already committed new job look like a failed initial save.
Lowering the retention limit applies cleanup immediately; saving or reopening
retries retained failures. Startup load failures are surfaced before attempting
legacy fallback.

The red run also reproduced a production crash: the observable retention-limit
setter assigned itself inside didSet. The captured crash stack repeats that
setter. Retention is now private-set with explicit clamping in its update method.
This was not a fixture-indexing failure. The diagnostic reference and stack
excerpt are retained in ignored `tmp/native-retention-recursion-evidence.md`.

## N6: Keychain results and credential state

An injectable Security adapter distinguishes absent items from denied access or
malformed data. Read, add, update and delete errors propagate as typed messages
that contain no key or account value. Legacy imports require a confirmed current
write and keep their old entry for recoverable older installs.

Explicit clear first writes an empty current marker. It deletes legacy and
current entries only in that order, retaining the marker on a partial failure so
legacy fallback cannot resurrect the key. Failed reads do not become empty-key
writes. Settings compare known snapshots and save changed credentials only.
Preference-only saves and local/preview generation do not retry pending hosted
keys. Hosted generation refuses before helper launch when its required key
cannot be saved.

Tests use fake Keychain/backend adapters, not real credentials. Security calls
remain synchronous; this work does not claim an off-main-thread performance
improvement. That concern belongs with the remaining service-boundary audit.

## N7: UK artifact publication

Native Store-mode UK publication preflights the current run's files, refuses
duplicate names/IDs, symlinks and mixed source roots, then copies into one hidden
same-volume staging directory. One rename commits a new unique visible job
folder. Existing papers and earlier runs are never replaced. Current document
URLs and completed history change only after that commit. Artifact bytes and
relative manifest filenames/hashes remain intact. French publication is unchanged.

Failed cleanup may leave only this transaction's hidden staging directory;
cleanup is best effort and does not replace an original copy/commit error.
There is no claim of cross-process checkpoint locking, hardware power-loss
testing or atomic rollback of the separate history directory.

## Regression evidence

The first combined red attempt stopped at two strict compiler warnings about
old unlabeled trailing closures. Those calls were labelled explicitly without
changing their injected faults. The second attempt reached actual deletion,
Keychain and publication assertion failures and the retention recursion crash.
Xcode restarted test processes, so its final 110-test/52-failure launch total is
not misreported as one complete uninterrupted run.

The implemented combined gate passed 173 native tests. A further local/preview
credential-retry test produced two real failures, then 19 targeted Keychain
tests passed after the caller fix. Eight French catalogue entries and explicit
selected-language resolution were added without changing authentication logic.
Four localisation cases first failed 11 assertions; all 32 localisation/history/
Keychain targeted cases then passed.

The final combined native run passed all 178 tests with zero failures. The
personal-development-signed Store Release preflight also passed its build and
strict signature checks. These results cover the frozen N5/N6/N7 source,
including the local/preview credential save guard and translated storage errors.
They do not establish App Store approval or complete user-interaction coverage.

Retained primary logs:

- `tmp/native-storage-transactions-red.log`
- `tmp/native-storage-transactions-red-2.log`
- `tmp/native-storage-transactions-green.log`
- `tmp/native-secret-local-preview-{red,green}.log`
- `tmp/storage-localization-{red,green}.log`
- `tmp/native-storage-transactions-final.log`
- `tmp/native-storage-transactions-store-preflight.log`

## Native Store publication check

The signed Store candidate completed one internal-folder layout preview first.
That run did not exercise external publication. The reviewer then selected
`tmp/native-uk-store-publication-iFalAO` through the native folder chooser and
completed another Accounting Paper 1 layout preview. It published four artifacts
in the unique directory `Keldin-B8A95456-EC1C-4E71-A251-12F22E5D74C5`.
Documents opened the subject automatically. Cmd-P showed All 36 Pages; the
reviewer cancelled without printing.

The published assessment JSON and both PDFs match all three relative filenames,
SHA-256 hashes and byte counts in the published package manifest. The manifest
itself has SHA-256
`0c78ce70a9a53e17145d3d7e8a02180740cc6e6aacae701ebdd82512e46d34d1`.
No transaction staging directory remained. Full output hashes and byte counts
are retained in `tmp/native-storage-transactions-publication-summary.json`.

The preview preference was restored to off and the output preference was
restored through the chooser to the exact original container-internal Generated
papers folder. The candidate was closed and no Keldin process remained. This
preview uses the primary branch's pre-V11 Accounting content. It is publication
and native interaction evidence, not a live AI run or an every-page content
review. The isolated V11 source and its separate acceptance work are unaffected.

Read-only second passes found no actionable N5/N7 correctness issue. Protected
publication remains pending. A separate access problem affecting older saved
PDFs is under investigation and is not claimed as fixed by these storage
changes. No App Store submission or whole-HIG certification is claimed.
