# Atomic live-matrix JSON publication

Implementation audit package T3 replaces direct writes of resumable matrix
results, the JSON summary and the run manifest with one small shared writer.
It serializes before touching the destination, writes a uniquely named sibling,
flushes and fsyncs that file, then atomically replaces the destination. Each
writer cleans up only its own temporary file. Existing JSON formatting options
and trailing newlines are preserved at each call site.

The helper does not merge concurrent updates, serialize multiple writers or
make the whole matrix a transaction. Overlapping publications are last-writer
wins, with each destination containing one complete document. Directory metadata
is not fsynced, so this is not a claim of power-loss directory durability.

The initial helper tests could not import the absent module. After introducing
it, the existing run-manifest integration reproduced one failing interruption
test while the three helper tests passed. Routing that boundary through the
helper turned the suite green. Additional tests inject flush failure and overlap
two publications at a barrier. The combined helper and live-matrix suites pass
26 tests. Retained evidence:

- `tmp/final-validation-20261028/atomic-json-red.log`
- `tmp/final-validation-20261028/atomic-json-integration-red.log`
- `tmp/final-validation-20261028/atomic-json-green.log`

Read-only second-pass review found no actionable issue. Ruff passes for the
changed tool and tests. Existing strict resume identities, artifact hashes,
qualification gates and event/stdout/stderr log handling are unchanged. This
work does not qualify any paper or revise old retained live-run evidence.
