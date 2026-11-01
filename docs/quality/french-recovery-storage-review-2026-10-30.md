# Private French recovery storage

This helper is not connected to generation yet. It stores complete snapshots in
an existing, application-owned private job directory. It does not validate a
paper, approve a review or make a failed generation successful. The caller must
validate the snapshot's source and recovery policy before using it.

The stored envelope says `approval: not_assessed`, retains the complete JSON
snapshot and records its canonical UTF-8 hash. The 32 MiB ceiling applies to the
whole encoded file. Non-finite numbers, configured credentials and oversized
records are rejected before filesystem writes. A credential in an escaped
string or key is also refused. No content is clipped or silently redacted.

The helper opens the supplied job root and its recovery folder with no-follow
directory descriptors. Parent directories are a trusted platform-provided
input, not an arbitrary export location. Evidence uses mode 0600 inside a 0700
folder. A complete file is synced before an exclusive hard-link publication;
existing snapshots and temporary-name collisions are not overwritten. Both
directory entries are synced before success returns. Visible directory inodes
are checked so a concurrent rename cannot produce a false saved-path report.

The first test run failed because the helper did not exist. The initial
implementation passed 20 tests. Read-only review found missing directory syncs
and the visible-path reporting gap. Five added tests reproduced those gaps and
an early-descriptor-open failure path. All 25 storage tests now pass. Combined
with the existing diagnostics and atomic-JSON regressions, 44 tests passed.
Ruff and a separate strict mypy check passed. The final helper was read again;
the reviewer found no new concrete issue in its error paths.

Logs are in `tmp/final-validation-20261030/recovery-store-*`. No model calls,
paid requests, application builds or full regression runs were made for this
private change. It is not release acceptance. Runtime integration, retention,
deadline and spending controls, source-bound replay, native admission and the
protected release checks remain required. The installed app is unchanged.
