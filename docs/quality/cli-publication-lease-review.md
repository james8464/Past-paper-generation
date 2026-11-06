# CLI publication lease review

## Scope and finding

The reviewer read all 586 lines of `Backend/Core/generation.py`, SHA-256
`19b000ee43e7deb47b06e515796b4561bc5c04c73eaf1920a53048d67acb8e45`,
then the complete publication-lease addition. The final file has 622 lines,
SHA-256 `a78c6b7e29292bf521bc3cfeef0561e3d707065f9b2d47cdc4a534c35a67119f`.
Related checkpoint locking, native job-directory selection and publication tests
were inspected selectively, not reviewed as complete dependencies.

Different CLI generation identities have separate checkpoint leases, but their
final filenames can coincide in one output folder. Two commits could interleave
and both report success with a mixed question paper, correction and manifest.
A failing publisher could also restore its older backup over a second job's
successful output. Native generation uses a separate private folder per job;
the reproduced collision concerns concurrent CLI jobs sharing an output root.

## Repair

Publication now acquires an output-root lease before checking destinations,
creating backups, replacing files or rolling back. It reuses the established
cross-process checkpoint locking primitive and its persistent inode at
`.keldin-checkpoints/publication.job.lock` under the canonical output root.
No visible top-level lock file is added and the lock sidecar is never unlinked.
Aliased output paths share a lock; different output roots remain independent.

Only publication is serialized. Blueprint construction, model work and final
validation can still run concurrently. Acquisition polls the existing
nonblocking lease every 50 milliseconds for at most 30 seconds, then reports
that another paper is being saved. Cancellation propagates during waiting.
The busy-error catch encloses acquisition only, so an error raised by the owned
transaction cannot cause its body to be retried.

The existing overwrite, backup, rollback and recovery-copy policies remain.
This repair does not promise that a later, separately completed CLI job will
never overwrite an earlier one. It prevents overlapping transactions from
mixing their results or rolling back another publisher's committed work.

## Evidence and limits

Two deterministic offline controls failed before the repair. They paused the
first job after its first replacement, completed a second job, then resumed
either a successful first commit or a failing first commit. The former left
the first correction beside the second question; the latter restored an old
question over the successful second job.

The final focused group passed 65 tests: the new concurrency controls, existing
publication recovery tests and checkpoint ownership tests. Added controls cover
both failure paths, separate roots, canonical-path aliases, bounded busy refusal,
cancellation, persistent lock identity and a busy error inside the owned body.
A separate subprocess calls the actual publication function, is refused while
the parent holds the output lease, and publishes successfully after release.
All files belong to temporary fixtures; no model, network or user-file access
is required.

Ruff checking, formatting and diff checks passed. The repository's configured
type gate passed its four infrastructure files; it does not establish complete
static checking of `generation.py`. The final new test-file SHA-256 is
`d52cb096a6ea350f37e95c979518c10335869f274e879a2572d84a10b3ab97f6`.

A separate reviewer checked the exact final lease helper, the complete locked
commit/rollback body, checkpoint locking, caller lock order and all 197 new test
lines. That review found no issue at the recorded source and test hashes.
The lease coordinates cooperating publishers on a local filesystem. It does
not provide immutable reader snapshots or coordinate separate cloud-sync clients.

The combined full suite, protected CI, packaged acceptance and installation
remain separate integration gates. No full-suite run, release
build, GUI operation, paid request, model inference or user-document publication was performed
for this repair. This is not a whole-project audit or generated-paper
qualification.
