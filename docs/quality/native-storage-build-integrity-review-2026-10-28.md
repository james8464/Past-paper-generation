# Native history and build evidence integrity

## History start

UK generation suppressed failure to save its initial history record and still
launched the helper. `GenerationCoordinator.begin` also changed active state
before saving. Three regression tests produced 15 assertion failures against that
behaviour (`tmp/native-history-start-red.log`).

The coordinator now saves first. UK generation handles a save failure before
launching the helper. French operations use the same state-preserving begin path.
A first green run exposed a remaining estimate after failure; the terminal handler
now clears that estimate with its timer. The resulting 131-test native suite
passed (`tmp/native-history-start-final-green.log`). Test faults use a regular
file in place of a test-owned history directory, not unreliable permission bits
or real user storage.

## Valid records and quarantine

The old loader caught decoding, reading and migration-write errors together.
A valid record whose migration could not be written entered quarantine. Six
tests reproduced 20 assertion failures in a 137-test suite, with the prior
131 tests still passing (`tmp/native-history-quarantine-red.log`).

Only decoding failures and the explicit unsupported-schema case now quarantine
records. Reading/access and migration-write errors propagate without moving valid
history. An injected writer preserves the default atomic file replacement and
lets tests force failures reliably. Explicit defaults keep relocation tests away
from real application preferences and ensure each application instance uses its
own mapping source.

A combined legacy-schema, running-state and relocation case also revealed three
intermediate writes. Its regression failed two assertions
(`tmp/native-history-single-write-red.log`). The loader now prepares the final
record, then writes once. Tests check final identity, timestamps, state, relocated
pointer and unchanged PDF bytes.

The final native suite passes 138 tests without failures
(`tmp/native-storage-final-green.log`). This is per-record migration handling,
not a whole-directory transaction: earlier successful migrations can persist
before a later record fails. Retention and removal policies are unchanged and
remain separate audit work.

## Helper cache and build logs

The helper cache fingerprint now includes sorted, normalised installed
distribution names and versions. Requirement ranges can resolve to new versions
without changing requirement-file bytes. Unchanged or reordered metadata keeps
the same fingerprint; a dependency version change invalidates it.

An early test fixture needed a path-with-spaces correction. Its first failure
log is retained but is not the acceptance red. The corrected fixture produced
three failures and four passes (`tmp/build-script-integrity-fixture-fixed-red.log`).
Second-pass review then caught a Bash command-substitution difference: the test
called the function directly, while production captures its output. The exact
production form reproduced a masked metadata failure
(`tmp/build-script-command-substitution-red.log`). An explicit return now
propagates that failure through the fingerprint pipeline. The final focused
suite passes seven cases (`tmp/build-script-integrity-final-green.log`).

The build wrapper also checks log capture's exit status. A failed log writer
cannot produce a successful evidence-bearing build. An original Xcode failure
keeps priority; failure of the optional display filter still remains a warning.
Both changed scripts pass Bash syntax checks. No dependencies were installed,
signing restrictions changed or runtime model-install policy weakened.

## Release checks

Personal-development-signed direct Release and Store-mode preflight builds pass
against the final source. Logs are
`tmp/native-storage-build-final-direct.log` and
`tmp/native-storage-build-final-store.log`. These signatures and preflight checks
are not Apple Distribution signing, an upload or Store approval. Protected
latest-head checks and merge remain required before installation as a release.

Computer control launched the final direct Release, opened History and confirmed
the existing completed, failed and cancelled records remained visible. It returned
to the French workspace and closed the candidate. Before/after hashes of all
58 existing history files match exactly, including the file inventory. No paper,
history record or preference was edited during this check. Hash lists remain in
`tmp/native-storage-history-{before,after}.sha256`.
