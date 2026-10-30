# Scoped concurrency and publication implementation review

## Reviewed source

This read-only engineering review covered every line of the four files below at
commit `da838cec471eabea94ee9234cc872e5ebeacc512`. No new consequential defect was
identified in these control flows. That finding is bounded to these file bytes,
their traced callers and the regression tests inspected; it is not a claim that
every possible execution has been tested.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/mlx_batching.py` | 209 | `698a8f535389e9ca20211474efe9cbec98d393c95e1e4a6cbab39738e93434c6` |
| `Backend/Core/review_workers.py` | 115 | `c37f2b86049b6b23dc252ae10008549fca6b1faa2ececd4a476ac52053b38171` |
| `Backend/Core/france/llm_runtime.py` | 230 | `aaf2f2de18bc11ed7951c125543a44b19c9d18e47789f6f4c02326d920f95ee1` |
| `Backend/Core/render_transaction.py` | 187 | `d78662bf3fb09cfc42fe68827de0f827ac7ea8ead3c1541309def336603259da` |

## Control flows examined

### MLX coalescing and batch decoding

Reviewed the two-slot semaphore and queue, single owner-thread startup, per-call
completion events, cancellation flag, queued-work draining, exception delivery
and result-count validation. The batch path preserves each prompt's decoder,
sequence identifier and output allowance. It rejects repeated or unexpected
identifiers and incomplete output instead of combining a neighbour's response.
Generator cleanup runs in `finally`. Supported cache incompatibilities become a
serial-fallback signal, not a switch to unconstrained decoding.

The per-request output bound is 1 to 16,384 tokens, with the legacy 4,096-token
default retained. Pair admission checks an 8,192-token combined input limit and a
16,384-token combined input/output allocation. These are token bounds, not a
measurement of device memory, inference speed or model quality. Caller traces in
`providers.py` confirmed constrained serial fallback and shared model ownership;
that trace was not a full-file review of `providers.py`.

Inspected regressions in `tests/test_mlx_batching.py` and
`tests/test_mlx_output_budgets.py` covering individual results, poisoned-neighbour
isolation, cancellation without owner-thread joining, fresh decoders, UID order,
cleanup, unsupported-cache fallback, unequal budgets and pair admission limits.

### Bounded review workers

Reviewed local worker validation (one or two), hosted worker validation (one to
four), the serial path, empty inputs, indexed result assembly, progress delivery
and exception propagation. Worker threads are daemon-owned; failure and caller
exit stop further queued work without joining a blocked provider socket.
Acceptance callbacks run on the caller rather than in the worker. Deferred
checkpoint callers were traced to distinguish candidate work from accepted
publication.

Inspected `tests/test_review_workers.py` and
`tests/test_hosted_generation_cancellation.py`, including the subprocess
cancellation cases, result ordering and late-worker/checkpoint boundaries.
Returning from cancellation does not prove that a remote provider immediately
stopped work or ceased charging for an already-started request.

### French model-draft publication

Reviewed argument checks, local model/reference/source snapshots, cancellation
handler restoration, progress dispatch, model-authored package validation and
the absence of catalogue fallback. Rendering and content checks precede private
package/manifest creation. Source, reference and local-model identities are
rechecked before directory promotion. The destination is checked for existing
content; temporary staging is removed on failure. File and completion events
follow successful directory promotion, not partial rendering.

Inspected `tests/test_french_llm_runtime.py` covering all provider route choices,
real PDF publication fixtures, render failure, identity mismatches, cancellation
and changed generation inputs. The backend emits private package and manifest
paths as well as document paths. Native document-only export is a separate
boundary, described in `private-generation-records-2026-10-29.md`; its whole
implementation was not reviewed here.

This review does not establish adversarial filesystem-race resistance or
power-loss durability of the entire multi-file package. Hosted revision identity
remains unavailable, explicitly unlike a pinned local model snapshot.

### Atomic PDF rendering

Reviewed role/deadline validation, main-thread enforcement, sibling temporary
files, readable-PDF checks before and after accessibility rewriting, file and
directory synchronization, atomic destination replacement and failed-temporary
cleanup. The nested deadline restores the preceding signal handler and timer,
subtracting elapsed time, while restoration failures do not conceal the original
exception.

Inspected `tests/test_render_transaction.py` for deadline, readable-output,
replacement and cleanup behavior. Main-thread rendering is an explicit contract,
not permission to render from worker threads. This file does not validate every
question's correctness or every final page's layout.

## Review limits

No tests, builds, downloads or inference were run for this review. The test
references identify coverage inspected, not fresh execution results. The prior
engineering acceptance evidence remains separate.

The provider dispatch, model-owner and transport sections were read selectively;
the complete provider schema-helper file, model setup/download implementation,
native exporter, external dependencies and all other project files remain
outside this attestation. The audit ledger must not mark those files reviewed
from this document. This record provides no whole-project, HIG, App Store,
teacher-review or paper-equivalence certification. Later source edits invalidate
the corresponding exact-byte review.
