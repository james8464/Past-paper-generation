# Qualification state projection review

Reviewed on 2 November 2026, against parent `0bcb3d502e2fc91867fa088edfc325b1c253c00f`.

## Behavior

The registry previously projected both `passed` and `not_applicable` as a completed
review. It also exposed later review flags without checking their prerequisites.
The projection now agrees with the existing coverage-matrix policy:

- A level is observed only when its own state is `passed`.
- A prerequisite is satisfied by `passed` or `not_applicable`.
- Visual review requires a satisfied engineering prerequisite. Empirical review
  requires satisfied engineering and visual prerequisites.
- Failed or unrun prerequisites suppress dependent flags. Evidence paths remain
  attached to their original levels, and the legacy gates migration is unchanged.

The current registry contains no `not_applicable` qualification states. This
corrects metadata projection; it adds no paper qualification or model evidence.

## Review scope

The independent release-gap reviewer read both files through EOF, including the
complete fix and tests, and selectively checked the coverage-matrix consumer,
its tests and the qualification schema. No further correctness finding was found.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/generator_registry.py` | 267 | `f5e9c3391ede6fed92b1ebded461d7a72a852a6cbbca73fadcc3c5ec96fa2d16` |
| `tests/test_generator_registry.py` | 203 | `999322c8043c5172c648a2fd15f0e7d4ee6cc34b3d3bbb1c2efaac73c07fd60d` |

## Verification and provenance

The author's exhaustive 64-state regression produced 49 failures and 28 passing
controls before the fix. The author's broader focused selection then passed 109
tests. The independent registry and coverage selection passed 102 tests.

The fixed implementation passed the full Python suite: **6616 passed, 2 skipped,
5 existing Swig warnings, 758.21 seconds**. The primary checkout's `.venv/bin/python`
ran `-m pytest -q` from the capacity worktree; its log is retained privately at
`tmp/nov2-registry-state-full-python.log`. The implementation hash was the one
listed above. At that run, the test hash was
`547242902610acf64f894e8415d16cd8295765c2506c8481aa5edc2356a1747a`.
The later test changes only wrap a decorator and an assertion for formatting;
the full result is not a full-suite execution of the later metadata commit.

Registry, coverage and generator/package/Keldin migration tests passed 120 tests
after the assertion wrap. Final formatting, focused tests and ledger checks are
recorded in the pull request. Ruff lint passed across the configured repository
scope; 617 Python files passed formatting. The configured mypy gate passed its
four source files; this is not a whole-project type-check claim.

No native execution, UI inspection, model calls, generated-paper inspection or
new educational qualification was performed for this change. Selective dependency
inspection and these two EOF reviews do not certify the whole repository.
