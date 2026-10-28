# Checkpoint ownership and publication cleanup

The checkpoint JSON format, seed selection, provider/model identity and question revalidation rules are unchanged. This change covers local macOS and Linux filesystems with `flock` support. It does not certify network filesystems or power-loss recovery.

## Ownership

Each canonical checkpoint path has two persistent sidecars. The `.lock` sidecar serializes individual store transactions across separate instances and processes. The `.job.lock` sidecar gives one CLI process ownership from authoring through publication and cleanup. A second CLI request for the same job receives `checkpoint_busy` before authoring starts. Other checkpoint paths remain available.

Sidecars stay in place after clear, failure and successful retirement. Removing a lock file could let a new caller lock a different inode while an existing caller still holds the old one. File descriptors close on normal completion and exceptions; the operating system releases them when a process dies.

Store operations take the instance `RLock` before the transaction file lock. Constructor validation and blueprint-only migration use that same transaction lock. Direct store clients get serialized storage operations; they do not acquire the whole CLI job lease or deduplicate model requests.

## Writes and retirement

Each write uses its own temporary sibling, flushes and syncs its contents, replaces the checkpoint, then syncs the containing directory. Exception cleanup removes only that write's temporary file. A killed process can leave an orphaned temporary file; later writers leave it alone. Previously accepted JSON remains available if the writer dies before replacement.

`clear()` checks the complete stored identity without rebinding a different blueprint. Normal reads retain the existing blueprint-revision migration and subsequent item-revalidation behaviour.

After authoring, the CLI takes a digest receipt under the transaction lock. Once publication succeeds, cleanup deletes the checkpoint only if its bytes still match that receipt. A later direct-store write therefore survives retirement. An absent file is harmless. Storage failure or cancellation raised by the retirement call produces a maintenance progress notice without failing the published run. Publication failure retains the checkpoint.

Preview and non-AI generation do not consume or retire AI checkpoints. Preview and live jobs retain their existing path calculation, so a successful preview cannot discard accepted work from a live run.

## Evidence and limits

The initial scoped run failed nine tests against the old implementation. A second red run exposed blueprint-only clear and preview-retirement gaps. Logs are retained in `tmp/checkpoint-ownership-red.log` and `tmp/checkpoint-ownership-refinement-red.log`.

Tests cover separate instances, spawned processes, constructor migration, canonical aliases, different-job leases, stable sidecar inodes, killed owners/writers, serialization/replacement/sync failures, changed receipts and CLI publication behaviour. Existing strict seed, mismatch, resume and diagnostic tests remain part of the targeted gate.

The initial fixed-source targeted gate passed 83 tests in 34.62 seconds across ownership, existing checkpoints, generation diagnostics, app backend and renderer transactions. Its log is `tmp/checkpoint-ownership-targeted-final-green.log`. An earlier broader run passed 81 tests and failed one stale assertion that disallowed the now-persistent lock directory; the corrected assertion permits only that exact directory and verifies its sidecar suffixes.

A separate red test reproduced an inaccurate cleanup message when deletion succeeded but the following directory sync failed. The final notice says cleanup could not be confirmed, without claiming that the checkpoint still exists. Its red log is `tmp/checkpoint-ownership-maintenance-red.log`.

Review then identified three further failure paths. Nonblocking job acquisition now recognises `EACCES`, `EAGAIN` and `EWOULDBLOCK` from `flock` as contention. Errors opening the sidecar, other lock errors and transaction-lock errors propagate unchanged. If temporary-file cleanup also fails, the original write or serialization error remains the reported failure and the orphan remains on disk. Cancellation during retirement becomes a cleanup notice after publication has committed; cancellation before publication still returns 130.

The follow-up tests first recorded six failures in `tmp/checkpoint-ownership-review-followups-red.log`. They cover the platform errno variants, sidecar-open permission failure, simultaneous primary/cleanup errors and cancellation on both sides of publication.

After the fixes and final lint adjustment, the same targeted gate passed 95 tests in 25.51 seconds. The fixed-source log is `tmp/checkpoint-ownership-reviewed-fixed-source-green.log`; Ruff and the whitespace diff check passed. This is a targeted result, not the full release suite.

Terminal-event review found that a cleanup notice could follow the backend's `done` event and overwrite the native completion status. Seven cases now capture actual JSON events around fixture publication. Five failed before the fix. Files commit first, checkpoint maintenance and any notice follow, and file/completion events are emitted last. Changed receipts, receipt/read failures, retirement and directory-sync failures, and cancellation raised by retirement all keep the published file and return success with `done` last. Pre-publication cancellation still returns 130 without file or completion events.

The revised targeted gate passed 102 tests in 23.91 seconds. Logs are `tmp/checkpoint-terminal-protocol-red.log` and `tmp/checkpoint-terminal-protocol-targeted-green.log`. Ruff and the whitespace diff check passed. The earlier full-suite/Store results precede this terminal-event change; a fresh final-source release gate is required.

A separate root-agent review found an unnecessary unlink after successful checkpoint replacement. A regression first confirmed that the new JSON had committed and no temporary file remained, then reproduced a false save failure when that extra unlink returned EACCES. The author removed the success-path unlink; exception cleanup still removes only the writer's own temporary file and preserves its original failure. The red log is `tmp/checkpoint-success-cleanup-red.log`.

The resulting targeted gate passed 103 tests in 27.21 seconds, recorded in `tmp/checkpoint-success-cleanup-targeted-green.log`. Its first run exposed a stale synthetic diagnostic fixture: trusted authoring requests require a task ID and authoring context before reaching the provider. The fixture now supplies a valid three-part ID and empty unlocked context; its original question number, provider failure and evidence-preservation assertion remain unchanged. No production request validation was relaxed.

Cancellation coverage is retirement-call scoped. A later signal during maintenance-notice emission, file/completion-event emission or lease exit can still reach the existing cancellation handler. This patch makes no unconditional post-commit success guarantee and does not blanket-catch unrelated post-commit errors.

No model requests, teacher reviews or learner timing studies were performed for this storage change. No historical checkpoint or retained paper artifact was edited. Implementation fingerprints will change with Core source; release acceptance must use the final source identity.
