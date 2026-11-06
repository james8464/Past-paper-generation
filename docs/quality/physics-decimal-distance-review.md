# Exact Physics distance comparison

## Observed boundary defect

The public `compare_physical_answers` helper subtracted finite Decimal values in
the caller's arithmetic context. For `1e-10000000` against zero with zero
tolerance, underflow rounded the nonzero difference to zero and accepted it.
The owned reproduction does not establish a defect in an advertised live paper:
this helper currently appears in the subject registry and tests, rather than
the seven advertised generation routes.

The original source SHA-256 was
`88b7bf9a128d001f16ca780466bb51acb27ebf916d5aa410bce9e866ebe4bc27`.
The new current-API tests produced nine failures and fourteen passing controls
before the production edit. They also reproduced false acceptance at
`MIN_ETINY` and a valid maximum-exponent case incorrectly refused after overflow.
No model was involved.

## Repair and exactness argument

The helper now compares the sign of `high - low - tolerance`, where `high` and
`low` are selected using exact Decimal ordering. It reads the three stored
coefficient tuples and accumulates signed decimal digits by exponent. It never
subtracts Decimal values, constructs powers spanning exponent gaps, converts to
binary floating point, or changes the caller's context.

Columns are processed from least to most significant using integer `divmod`.
Three signed digits and the incoming carry bound the next carry between -3 and
2. Across empty columns a positive carry vanishes after one digit; a negative
carry becomes -1 and remains -1. Both cases produce a nonzero lower digit.
This permits jumping over an arbitrarily large empty exponent gap without
allocating its zeros. After the highest occupied column, a negative carry means
the exact sum is negative, a positive carry means positive, and zero carry is
zero only when every emitted lower digit was zero. The distance is within
tolerance exactly when that sum is nonpositive.

For N supplied coefficient digits, auxiliary storage is O(N), with O(N log N)
sorting time. These bounds depend on actual input length, not exponent distance.
No arbitrary value range is introduced. Existing finite-value, unit and
significant-figure admission remains unchanged; the unrelated Physics plugin
stub is unchanged.

A directed-rounding shortcut was not used. Rounding down below tolerance only
settles the comparison when tolerance is exactly representable on that context's
grid. Decimal supports `MIN_ETINY` below `MIN_EMIN`, so increasing exponent limits
while keeping small precision does not establish that precondition.
The [Python Decimal documentation](https://docs.python.org/3/library/decimal.html)
describes contexts, exponent limits, rounding and context-independent stored
coefficient tuples.

## Scoped evidence and limits

Final focused validation passed 57 tests, including the unchanged science
subject tests and all 23 new tests. The new cases include 250 seeded moderate
comparisons against a Fraction oracle restricted to exponents between -30 and
30. Extreme-exponent cases use explicit mathematical expectations, not enormous
Fraction allocations. Controls cover exact boundaries, opposite signs, borrow
and carry, equivalent representations, signed zero, significant figures,
units, and an ambient precision-one context with traps and preexisting flags.
The context's precision, rounding, traps and flags remain unchanged.

Root independently checked 5,000 additional seeded comparisons against an exact
Fraction oracle, using supplied coefficients up to 35 digits and exponents from
-70 to 70. All passed. This is a count of comparisons, not 5,000 additional
pytest tests. A separate reviewer read the full final source, new tests and this
proof and found no mathematical or integration issue within the stated scope.

Ruff check and format passed for both Python files. No full suite, release build,
provider call, GUI operation or paper qualification was performed. No history,
checkpoint, schema, prompt, answer or policy version was changed. Existing records
are not relabelled; only a fresh call to this helper receives the stronger check.

The complete final source and new test were read through EOF:

- `Backend/Core/subjects/physics.py`: 143 lines, SHA-256
  `44d691dc9e817f82b817b83817b25c0eaf71bce50786315b80275b2aa95281bc`.
- `tests/test_physics_decimal_distance.py`: 109 lines, SHA-256
  `354d9c2e60bd465f703da59dcf1e1fed898615a3124ce03e0a1ca0423448bb92`.
- Root also read the complete unchanged 133-line `tests/test_science_subjects.py`,
  SHA-256 `558a6858b93ab7895a78f5129147e73106e213680cabc53d9114b1711cbea68a`.
  This is a test-file review, not a complete review of its Biology or Chemistry
  implementation dependencies.

Owned logs remain under `tmp/nov6-physics-distance-{red,green,final-focused}.log`.
