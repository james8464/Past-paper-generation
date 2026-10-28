# Checkpoint seed input integrity

Implementation audit package P1 now rejects coercible seeds before hashing and
when decoding a stored identity. Python considers `bool` a subtype of `int`, so
the previous blueprint boundary accepted `True`; Pydantic also converted stored
Boolean, numeric-string and whole-float seeds into integers.

The boundary now requires an actual integer and the saved model uses a strict
integer field. No new numeric range is imposed: signed seeds, zero and historical
unsigned 64-bit seeds remain valid. Valid blueprint JSON and SHA-256 identities
are unchanged. A malformed checkpoint is rejected without rewriting its bytes.

Four regression cases failed against the old implementation. The focused
checkpoint suite now passes 21 tests. Logs are retained under
`tmp/final-validation-20261028/checkpoint-seed-{red,green}.log`.
The initial command used an isolated Python without pytest and did not execute
tests; the red/green evidence uses the primary project's existing test runtime.

This change does not address package P2's separate cross-writer locking and
temporary-file ownership questions. It does not establish complete release
acceptance or change historical evidence into a new accepted run.
