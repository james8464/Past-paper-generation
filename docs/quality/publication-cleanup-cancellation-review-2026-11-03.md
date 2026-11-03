# Publication cleanup cancellation review

## Finding and repair

A complete-file review of the public UK generation dispatcher and family adapter at `cd51cb4edc953c73e5c627f8c890048e938b3099` found that cancellation during backup cleanup could report a saved paper as cancelled. All document replacements and the package manifest had already committed, but the cleanup exception reached the handler's cancellation branch before any file or completion event.

An owned temporary fixture reproduced exit 130 with the accepted question file and manifest still present. It used prevalidated fake document bytes and injected `GenerationCancelled` into recovery-directory cleanup. It made no model or network request and did not use user documents.

The repair marks publication committed only after every replacement succeeds. Cancellation during subsequent backup cleanup emits a maintenance notice, then the normal file and completion events. Backup copies can remain at the named recovery path. Cancellation before commit still propagates, and the existing replacement rollback and failed-rollback recovery rules are unchanged. This does not make the file set crash-atomic or handle uncatchable process termination.

## Verification

The corrected tests-only baseline run failed at the expected handler result: 130 instead of 0. Fourteen tests passed. An earlier fixture attempt recursively replaced its own finalization helper; that fixture mistake was corrected before recording the baseline failure. Both attempts remain in the conversation record; the actual baseline log is `tmp/nov3-publication-cleanup-red.log`.

After the repair, 73 focused tests passed in 2.36 seconds. They cover publication, checkpoint ownership, minimal client contracts and atomic rendering. The new completion test exercises the real handler and JSON event protocol, checks every published fixture file, and verifies the retained backup and maintenance notice precede completion. A new backup-phase cancellation control preserves the old set and propagates cancellation. Existing controls cover cancellation before and after a replacement, rollback failure, target-type refusal and cleanup failure after success. Ruff and diff checks passed. The final focused log is `tmp/nov3-publication-cleanup-final-focused.log`. Full-suite and latest-head protected checks remain required for release.

## Review scope

The author read all 575 baseline lines of `generation.py`, all 200 lines of `family_adapter.py`, and all 229 baseline lines of the publication tests through EOF, then reviewed the entire final source and test delta. The final files are bound below. Selected callers and dependencies were traced without a complete-file attestation. Additional complete test reads covered checkpoint ownership, renderer transactions, JSON client contracts and preview presentation; their existing ledger records are not changed here.

| File | Final lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/generation.py` | 585 | `e674024ff3d2acbc2454f0a0cf2b284341e4057f80a50d75ef485287b15fb0a7` |
| `Backend/Core/family_adapter.py` | 200 | `21bf28c5e4a9eb3e98fccfa9cc137184f3ce2b984157576791c6b3914dda13ed` |
| `tests/test_cli_publication_recovery.py` | 298 | `8c9ae27c4d3c015677d59732e8042c496c0428961fe26c422ad3ecc783513c0a` |

The review traced output role and staging checks, manifest hashes, checkpoint identity and retirement, preview/live branching, review requirements, and terminal event ordering. Preview skips authoring and checkpoint writes, carries preview provenance and validates its PDF notice. Static reference-profile qualification flags are not fresh generated-paper qualification. No additional concrete finding was identified in these two production files. This review does not certify the remaining repository, every failure schedule, model answers, academic difficulty, native interactions or App Store acceptance. No native launch, real inference or user-data modification was performed.
