# Business rounding and benchmark completion

## Financial answer rounding

A balanced, positive-equity source fixture exposed a mismatch between the
Business answer formatter and the existing numeric contract. Chart values
`[425, 500, 500, 1091, 400]` produce current assets of 810, current liabilities of
720 and equity of 280. The current ratio is 1.125. The scheme printed `1.12:1`
using Python's default formatting, while the independent half-up contract
required `1.13:1` and refused publication.

The formatter now uses the existing shared `rounded` function, retains compact
trailing-zero formatting and displays rounded zero without a minus sign. The
numeric validator is unchanged. No model answer was hardcoded or accepted by
relaxing a tolerance.

The corrected red fixture produced five failures and one passing control. Its
real-question case calls the current question builder, independently solves its
declared inputs and reconciles the printed marking. The new six-case group and
all 47 tests in the Business test file passed after the repair. An earlier test
attempt reversed the reconciliation helper's arguments; that diagnostic is kept
but is not the accepted reproduction. No ordinary-seed or previously published
paper failure is asserted from this owned fixture.

Logs: `tmp/nov3-business-rounding-red-corrected-fixture.log`,
`tmp/nov3-business-rounding-green.log` and
`tmp/nov3-business-rounding-full-file.log`.

## Missing benchmark results

The benchmark previously returned to its initial screen if its process exited
zero without sending a result. It now reports a localized missing-result error.
Existing backend errors are preserved, a valid result still completes normally,
retry clears old state and late callbacks cannot change the replacement run.

The controlled-backend red test produced two expected missing-message failures.
The author then ran the complete native suite: 425 tests executed, three skipped,
zero failures. After combining the protected sidebar fix and test-fixture cleanup,
the native suite executed 427 tests, with three skips and zero failures.

The actual installed main165 benchmark had separately passed start, cancel,
retry and normal completion through native controls. That does not exercise a
missing protocol result in a physical UI. Existing error-view wiring and the new
controlled-backend tests cover that boundary; no fault-injected native journey
is claimed. Benchmark score adjusts the cold ETA heuristic; it does not measure
the selected model's generation speed.

Logs: `tmp/nov3-benchmark-missing-result-red.log`,
`tmp/nov3-benchmark-missing-result-green.log` and
`tmp/nov3-combined-followup-native.log`.

## Implementation review

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Resources/business/aqa/generator/aqabizgen/financials.py` | 117 | `d5acfd47bce25528c78ca9af80bb1e0fef969bee16f22ef2cac4cb57c38c0bc4` |
| `Resources/business/aqa/generator/aqabizgen/configs.py` | 388 | `45d7488a792744bf4c9dd224cf19f663d9b5fc7477db0b4ca2cc5b551692732e` |
| `macOS/Keldin/State/BenchmarkCoordinator.swift` | 110 | `df53a2c4ce77525e6331123230409a0c71e219fe4212de124022111de8865613` |
| `macOS/Keldin/Domain/NativeInterfaceCopy.swift` | 123 | `f90f179dfe623afbf2d4052b5902cb85ea2eb1083c09cdd767c6c7ec7323f514` |
| `macOS/Keldin/Domain/AppModels.swift` | 1379 | `e861a7fe54a05f0afd2abab2197813d43d78085a4877559b730410b2c12ebdd0` |

`release_gap_audit` read the complete original financials and configs files and
reviewed the final rounding delta independently. `quality_status_review` read
both benchmark runtime files through EOF and authored the controlled tests.
The root reviewed that final source, localization and test delta.
`french_run23_review` read AppModels through EOF and selectively traced callers
and tests. Configs and AppModels had no new confirmed P1/P2 finding in that scope.
The expanded test files and whole string catalogue are not represented as new
complete-file reviews.

## Remaining release gates

The earlier reference-only full Python run at `9f97d037` had 6,732 passes, two
skips and 11 failures because the private runner omitted `mypy` from PATH. Source
HEAD and worktree stayed unchanged. Correcting PATH made all 13 tests in those
two static-contract files pass, including the 11 failures. This is not described
as a single all-green full-suite run. The final combined source needs its own
correctly configured full gate and protected checks before merging.

These are implementation repairs. They do not qualify model-authored papers,
establish learner calibration, prove the earlier memory hang fixed or provide
App Store/notarization approval.
