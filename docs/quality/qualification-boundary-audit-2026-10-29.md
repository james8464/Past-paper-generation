# Qualification and publication boundary audit

## Review scope

The delegated Python reviewer read all ten files listed below, including their
tests, then reviewed the fixes against those reads. The initial review used
`56170a2c`; final reviewed changes end at
`beb3763e14388cb235aaae84e2011ee88181e899`. A second reviewer inspected the
atomic-publication and parsed-event changes without editing them. This is a
file-level implementation review, not educational calibration or whole-project
acceptance.

| File | Disposition |
| --- | --- |
| `tools/live_generation_matrix.py` | Fixed acceptance of contradictory events. Fresh and resumed results now require an error-free parsed-event stream with exactly one final completion. A zero exit code does not override an error event or timeout. Retained request, model, event and artifact identities remain checked. |
| `tools/live_process.py` | Read fully; no additional actionable finding. Reviewed finite deadlines, streaming logs, interruption, process reaping and descendant termination. Existing tests establish the stated process-lifecycle scope. |
| `tools/atomic_json.py` | Removed redundant cleanup after successful replacement. Failures preserve the original exception and add diagnostics if temporary cleanup also fails. Failed stream construction closes the descriptor that has not transferred ownership. |
| `tools/coverage_matrix.py` | An inapplicable gate can satisfy a permitted prerequisite, but cannot count as observed calibration. Higher displayed levels require satisfied lower prerequisites and an actual pass at the displayed level. The checked-in matrix is unchanged. |
| `Backend/Core/qualification/manifest.py` | Fixed the same publication/descriptor boundaries. Policies reject empty levels, empty gate tuples, blank names and duplicates. An empty tuple introduced through mutation or constructor bypass still cannot qualify through `all(())`. |
| `tests/test_live_generation_matrix.py` | Read and extended fresh/resumed error-before-done, error-after-done, missing/duplicate completion and parsed events after completion cases. Valid historical cases remain tested. |
| `tests/test_live_process.py` | Read fully; retained progress, timeout, interruption, missing executable and descendant-cleanup cases. No extra finding. |
| `tests/test_atomic_json.py` | Added successful-commit cleanup refusal, combined primary/secondary faults, cancellation preservation and unclaimed-descriptor checks. Existing complete-document concurrency tests remain. |
| `tests/test_coverage_matrix.py` | Added twelve explicit state combinations, including inconsistent higher passes and inapplicable prerequisites. Tests preserve input evidence and current resource determinism. |
| `tests/test_qualification_manifest.py` | Added cleanup/descriptor faults, invalid policies and mutated/constructed empty-policy bypasses. |

## Regressions and results

All logs remain in the worktree's ignored `tmp/` directory. The fixes are in
`c7e0b8cb`, `f33c1d13`, `1488eaca`, `68c531a9` and `beb3763e`.

| Retained log | Result |
| --- | --- |
| `audit-publication-cleanup-red.log` | 6 failed, 12 passed before the fix |
| `audit-publication-cleanup-green.log` | 18 passed |
| `audit-publication-descriptor-red.log` | 2 failed, 18 passed before the fix |
| `audit-publication-descriptor-green.log` | 28 passed |
| `audit-terminal-stream-red.log` | 5 failed, 22 passed before the fix |
| `audit-terminal-stream-green.log` | 42 passed |
| `audit-policy-gates-red.log` | 7 failed, 14 passed before the fix |
| `audit-policy-gates-green.log` | 62 passed |
| `audit-calibration-labels-red.log` | 9 failed, 16 passed before the fix |
| `audit-boundary-final-green.log` | 93 passed in 7.76 seconds; Ruff and diff checks passed |

## Limits

The existing parser ignores non-JSON stdout. The new terminal rule applies to
parsed JSON events; it is not a full raw-stream/schema attestation. Atomic writers
publish complete last-writer-wins snapshots, without transactional merging or a
power-loss durability guarantee. The policy model's nested dictionary is still
mutable; the empty-policy check fails closed at qualification time.

No model calls, full application tests or live educational qualification ran for
this package. Current qualification resources and prior evidence were not edited.
The source changes require fresh identity-bound release acceptance before any new
complete-paper acceptance claim.
