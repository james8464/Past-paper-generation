# Selected-response dispatch review

## Scope

This is a maintainability refactor of `Backend/Core/subjects/selected_response.py`, not a new solving algorithm or a paper-qualification claim. It replaces the operation ladder with fifteen named registry entries and bounded handlers. A small typed internal result carries the expected choice, explanation steps and numeric results.

The two profit operations retain one shared profit calculation behind separate named handlers. Numeric, percentage, quantity and money choices retain their separate parsing and error messages while sharing the identical final precision/uniqueness check. The existing Decimal `ROUND_HALF_UP` quantization is shared without changing when the public result is rounded. In particular, a profit of 10.5 still returns raw `selected_value: 10.5` while its zero-decimal money choice is `£11m`.

Common public-input validation, four-choice validation, semantic matching, response fields, explanation strings, operation-owned units and precision remain unchanged. The Accounting-version dispatch remains before the generic selected-response checks and delegates only the exact existing version. No private answer facts or broader fallback were added. Version strings are unchanged.

## Characterization and parity evidence

- Original source SHA-256: `018dd35a619c24e9eb7f0fa849bf9b01a0df28bfecbf7d62b0ebe6c17b16b9dd`.
- Final source SHA-256: `abfb5838088a42a2a885b6d6801aa9a0769f344d401329c10e24b167d9e35e7a`.
- `tmp/selected-response-characterisation-baseline-final.log`: 97 tests passed against the original implementation.
- `tmp/selected-response-dispatch-parity.log`: the same 97 tests passed after handler extraction.
- `tmp/selected-response-dispatch-final-targeted.log`: 275 tests passed, including the new complete-registry invariant and existing shared numeric, independent-solver and Accounting solver tests.
- `tmp/selected-response-dispatch-subject-parity.log`: 86 existing AQA Business, AQA Economics and OCR Economics tests passed.
- Ruff check and formatting, and `git diff --check`, passed for the owned files.

The characterization covers all fifteen operations, complete result payloads, raw numeric results, input non-mutation, exact format policy, public input shapes, numeric ambiguity, units, precision, positive and negative half-up cases, all ten economic-shift directions, the categorical comparison outcomes, all four performance-statement outcomes, row ambiguity/missing fields and the narrow Accounting delegation boundary. The registry test checks parity with both the Literal operation set and format policy.

The broader numeric/subject runs reported five dependency deprecation warnings associated with PyMuPDF's SWIG types. They did not fail the tests. No full suite, native build, provider generation or performance measurement was run for this refactor.

## Separate existing guard observation

The strategic-change handler classifies any equal `external_change` and `strategic_change` strings as strategic fit, rather than restricting both values to the generator's high/low vocabulary. Existing generators supply high/low values. This behavior was not changed during the refactor; tightening that domain would need its own defect test and reviewed behavior change.
