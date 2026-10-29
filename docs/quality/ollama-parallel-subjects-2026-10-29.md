# Ollama generation across subjects

This change extends the existing optional two-request mode to the shared UK
authoring pipeline and both specialist pipelines. Settings now calls it
**Parallel Ollama generation**. The saved preference and environment key retain
their earlier names so an existing choice is not lost. The default remains off.
The existing `localReviewWorkers` provenance count remains accurate for reviews;
the same two-worker ceiling now also applies during authoring.

## Scope and invariants

- Shared route: AQA Accounting, AQA Business, AQA Economics, OCR Economics and OCR
  Computer Science, plus configured families using the shared adapter.
- Specialist routes: Edexcel Economics and AQA Computer Science.
- French's public app-owned catalogue does not call Ollama. Its source and the
  explicit historical French diagnostic route are unchanged.
- Apple MLX remains serial. Hosted-provider scheduling is unchanged.
- Existing local batch sizing, retries, fallback eligibility, independent solver,
  marking agreement, reference-demand checks and final similarity checks remain.
- A paper has at most two active local jobs. Each job makes its model requests
  sequentially. Review phases do not overlap the preceding authoring phase.

This is question-group concurrency within one paper, not simultaneous paper jobs
or loading several model copies. Ollama must itself allow two requests. The
previously approved server setting is still login-session-scoped. Memory use can
increase; there is no hard RAM, power or guaranteed speed limit.

## Checkpoints, ordering and cancellation

Workers read through the existing locked checkpoint store. Their saves and
discards go into a private `DeferredCheckpoints` buffer. Only the caller's
acceptance callback commits a successful job's changes through the original
atomic store. Workers never publish files, commit real checkpoints or modify the
accepted paper. Returned candidates are assembled in original paper order.

On failure, the remaining queue stops. A job already in flight may finish its
model request, but cannot commit its buffer. Completed accepted jobs remain
resumable. A failed multi-item group does not retain its partial in-memory work.
Daemon workers preserve prompt helper exit on cancellation without waiting for
model sockets. Progress reports accepted groups/items from the calling thread,
not the original question index of an out-of-order completion.

## Evidence

Focused checks cover actual two-job overlap for all five shared subject adapters
and both specialist routes, preserved output ordering, caller-only checkpoint
commit, discarded unaccepted buffers, late-worker failure isolation, legacy
serial/hosted behavior and specialist checkpoint resume. Shared scheduling probes
stub model generation with unchanged blueprint items; they are not AI-quality
evidence. Existing validation tests separately exercise the retained gates.

Logs are retained under `tmp/ollama-all-subjects-*`. The first red run refused the
missing checkpoint buffer. A later cancellation fixture initially read an absent
checkpoint file; seeding its retained record corrected the fixture. No production
validation was relaxed.

Final focused Python checks passed 361 tests, including solver adapters and
repository hygiene. The five existing third-party PDF deprecation warnings
remain. Ruff lint and formatting passed. AST Graphify was updated; its 44 existing
zero-node resource warnings remain. The new worker helper passes strict mypy.

The earlier 29.1% short-pair throughput result remains only a probe, not a
whole-paper speed claim for these subjects. No new teacher evidence, learner
timing, full live-paper matrix or App Store approval is claimed. Both protected
Backend and macOS checks are required before merge and installed-app update.
