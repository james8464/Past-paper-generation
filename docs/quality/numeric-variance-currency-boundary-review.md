# Numeric variance and currency boundary review

## Defects and repair

The former validator accepted a zero variance labelled favourable or adverse,
although its canonical formatter labels rounded zero as nil. Both the printed
scheme and unconditional-alternative paths had the same one-sided check.
The shared validator now requires zero exactly when the direction is nil and
continues to reject a negative magnitude or an incorrect nonzero direction.

The monetary pattern also allowed signs on both sides of the currency symbol.
A token such as `-£-1.00` reached `Decimal` as `--1.00` and raised an exception.
A shared token parser now checks the existing number grammar after normalizing
the currency symbol and Unicode minus. Malformed tokens produce ordinary
rejection results; no catch-all exception handler conceals unrelated failures.
One sign before or after the currency symbol remains supported.

The repair preserves existing unit grammars, scale conversion, precision and
ROUND_HALF_UP policy. Variance direction follows the displayed magnitude:
`0.004` and `-0.004` round to zero at two places, while `0.005` and `-0.005`
round to magnitudes of `0.01`. Alternatives still require exact equality to the
rounded target after their existing pounds, pence or million conversion.
They do not receive another rounding step.

## Replay and acceptance scope

`closed-numeric-v4-variance-signs` replaces the previous v3 integrity identifier.
Canonical reconciliation, saved difficulty review and family checkpoint identity
already require that shared identifier. Old approvals cannot acquire the stronger
meaning by retaining v3 or by receiving filled-in defaults. Tests preserve an
old-policy control that reaches authoring, while the current policy refuses the
same checkpoint. No historical files or records are rewritten.

The initial test run exposed 39 boundary/provenance failures and one incorrect
test import. The import was corrected before acceptance; the checkpoint control
then exercised the intended identity boundary. Focused controls cover both
admission paths, zero and signed zero, rounding thresholds, pence and GBPm,
nonzero directions, valid single signs, malformed double signs and replay.
The existing exact-floating implementation is unchanged; its version assertion
now expects the new shared identifier.

## Source review

The author read the complete 310-line `Backend/Core/numeric_integrity.py` after
the repair and reviewed the changed test paths. Scope includes its value parser,
formatter, quantity grammar and both admission functions. Related reconciliation,
review and checkpoint callers were inspected only where they consume the numeric
integrity contract. This is not a whole-project review or evidence that generated
papers are correct. A separate reviewer read the repaired module through EOF,
the new test file and the changed version assertion, with scoped reads of the
reconciliation, difficulty-review and checkpoint callers. That review found no
issue in the exact source hashes below. Full-suite acceptance and packaged-binary
checks remain separate release work.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/numeric_integrity.py` | `5196aa7c1531b1589c838f7a5350651f3218982f470cb0b2d4275b81deaca9fc` |
| `tests/test_numeric_variance_validation.py` | `6dc674237a1cbcba65b43c3bde3d471d254ca39ea415852fb2ae7745829edbc6` |
| `tests/test_cs_floating_evidence_version.py` | `587ba0e9f9c7c7564f29303c030f5091f4e213d93baf933001961e257c51a82b` |
