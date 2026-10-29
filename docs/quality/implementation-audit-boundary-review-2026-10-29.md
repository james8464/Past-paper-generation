# Implementation audit: review and build boundaries

## Scope

This static review read every line of the six files below on 29 October 2026.
It checked validation, ownership and failure paths in the review ledger, along
with the build configuration that enforces formatting and runs release tests.
This record does not certify other files or every runtime path.

| File | Review and disposition |
| --- | --- |
| `tools/audit_coverage.py` | Reviewed canonical relative paths, source-first classification, exact field validation, tracked evidence membership, source/evidence hashes, symlink containment and stale-review handling. Regeneration preserves valid reviews and returns changed source to pending. Invalid evidence refuses regeneration. The CLI writes derived metadata directly, so an interrupted write may require regeneration; it is not a crash-durable application data store. |
| `tests/test_audit_coverage.py` | Read all tests, including isolated Git fixtures, malformed schemas, forged exclusions, changed evidence, external symlinks, symlink loops and stale source. The fixtures use temporary repositories and do not stage the user's project. All 32 tests passed in 1.25 seconds during this review. |
| `ruff.toml` | Reviewed Python 3.12 target, lint rules, explicit test/import exceptions and formatter exclusions. The 29 exact-byte French catalogue files stay linted; their formatting exclusion preserves retained replay identities. These exclusions do not establish a semantic review of those files. |
| `requirements-test.txt` | Reviewed the explicit setuptools build-backend dependency needed by clean Python 3.12 wheel-parity tests, test-only dependencies and bounded major versions. A version range is not a reproducible lock or a dependency security audit. |
| `requirements-build.txt` | Reviewed packaged runtime dependencies and Darwin/arm64 markers for MLX and its grammar support. This does not establish model quality or a fresh dependency-resolution result. |
| `.github/workflows/ci.yml` | Reviewed read-only permissions, per-ref concurrency cancellation, explicit seven-generator installation, lint/format/test steps, separate macOS tests/Store-mode build and failure-only diagnostics. Both jobs have deadlines. Action references use version tags, not immutable commit pins; pinning them is a separate supply-chain improvement. No protection settings were changed. |

## Limits

The ledger's `reviewed` status records a semantic review of particular file bytes.
It does not mean an issue cannot exist, that all suggestions were implemented, or
that an application release passed. Evidence and source hashes bind each ledger
entry to this record and its reviewed version. Formatting alone never supplies
that status.

The current native window-routing work, Accounting validation change and live
qualification event checks require their own tests and release acceptance. This
review leaves teacher validation and observed learner calibration unclaimed.
