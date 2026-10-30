# Bounded French whole-exercise re-drafting

Status: private design, red recovery specifications and typed refusal foundation.
Automatic recovery is not implemented or ready to merge. Base: `463d9c4c`.
Do not change installed behavior until integration gates pass.

## Intended behavior

Allow one additional whole-exercise author, blind-solver and reviewer cycle
after a complete, valid reviewer response explicitly refuses the draft. Never
edit the first candidate, its answers or its rubric. Previously accepted
exercises remain frozen. The second cycle must make fresh provider calls and
pass all current source, safety, schema, layout and semantic checks.

Only a dedicated `SemanticReviewRefusal` may enter this path. Construct it after
all review schemas and indexed blind-note dispositions have been validated.
Negative correctness, completeness, curriculum, language, self-contained-data
or rubric verdicts, explicit blocking issues and reviewer-adjudicated blocking
blind notes remain refusals; the new behavior is a bounded new attempt, not an
approval override. Raw malformed reviews, unsafe code, executable-verification
failures, transport failures, cancellation and programmer errors remain hard
exits. Do not catch a general `ValueError` or `GenerationEvidenceError` to retry.

## Bound and identity

Use a required source-bound policy such as
`fr-nsi-v36-whole-exercise-redraft-v1`. Each exercise has round 1 and at most
round 2. A round has at most two author-format attempts, one blind solve and
one review: at most four generation attempts. The paper maximum is therefore
`3 exercises × 2 rounds × 4 attempts = 24 generation attempts` for the current
production typed, sequential French clients. This excludes ancillary HTTP
requests such as Ollama's before/after model-identity lookup. Legacy client
overrides need separate bounds. Concurrent MLX batching can attempt a batch and
fall back to serial decoding, so any later parallel route must count both.
Test the bound for every supported production provider. Do not add hidden retries.

A call count is not a time or spending limit: 24 nominal 600-second calls can
approach four hours, and the current DeepSeek output budgets can reserve up to
589,824 output tokens. The private experiment needs explicit elapsed-time and
spending ceilings before model testing. Cancellation stops local work but cannot
promise that a remote provider stops inference or billing. Preserve the existing
total US$5 diagnostic cap; no model calls are authorised by these unit tests.

Capture policy, paper seed, exercise ID, round, request identity/hash and model
identity. Derive any second-round seeds deterministically within signed bounds;
do not reuse review/checkpoint evidence from a different candidate. Keep the
existing accepted `authoring_attempts` and `reviews` linked to the final round.
Only accepted cycles may update the shared topics and final attempt lists.
Rejected topics must not leak into the replacement request or later exercises.
Package replay must require and recompute ordered round evidence, including the
exact accepted candidate link. Missing policy, removed rejected rounds,
reordered rounds, forged outcomes and changed raw evidence must fail even when
the outer content hash has been recomputed. Historical source-bound readers
must not silently acquire the new policy.
Before activation, native completion must require the exact new policy and
refuse missing, boolean or old policy values. No native delta is implemented in
this preparatory branch.

## Evidence and private persistence

Persist each completed round before making another call. Keep returned raw
author, blind-solver and reviewer objects intact, their hashes, structural
author-attempt records, review result and typed refusal. Store each raw object
once rather than duplicating it inside several nested records. Provider syntax
failures that were never returned to the caller retain their existing opaque
hash-only record; do not invent missing raw text or call that complete evidence.

Use a dedicated private application-state failure record, not Downloads, user
PDF output or the existing truncated diagnostic writer. No broad checkpoint
framework is needed. Proposed ceiling: 32 MiB, covering the current 24-call,
1-MiB-per-returned-response ceiling plus record framing. Encode with nonfinite
numbers forbidden, enforce the bound before publication, and atomically publish
one mode-0600 file in a mode-0700 app-state directory. Reject symlink targets
and preserve earlier files. A storage failure must not turn rejection into
success or claim that evidence was saved. Retention/privacy behavior must be
explicit; never include API keys or authentication headers.

## Feedback and presentation

Append generic, clearly delimited review feedback as data to a fresh authoring
request. The requested exercise allocation and curriculum scope stay fixed;
the model authors the whole replacement. Do not supply a repaired answer,
preferred numeric result or a question-specific exception. Tell the user that
the exercise is on its second and final attempt. A second semantic refusal
stops before rendering/publication and retains both rounds. Teacher review and
learner calibration remain `not_run`.

## Acceptance work

The private fake-provider specifications cover refusal followed by a fresh
complete pass, two terminal refusals, frozen earlier exercises, malformed
reviews, unsafe authoring, transport errors and cancellation. They are currently
red against the unchanged implementation. Before integration, add replay
tampering tests with recomputed hashes and private persistence tests covering
size limits, failed writes, permissions, symlinks and atomic replacement.
Run focused regression tests first, then root-owned combined and protected
release gates. No paid or local-model calls are part of this preparatory work.

## Research boundary

[Self-Refine](https://arxiv.org/abs/2303.17651) studies iterative feedback across
several tasks. It motivates a hypothesis, not a claim that NSI papers improve.
[Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798)
reports limits and possible degradation in intrinsic reasoning correction.
Fresh independent checks and a terminal refusal therefore remain mandatory.
Neither paper establishes this application's efficacy, exam equivalence or
calibration.

## Private foundation checkpoint

`SemanticReviewRefusal` now distinguishes schema-valid negative verdicts from
malformed responses and transport, safety or cancellation failures. It remains a
`GenerationEvidenceError`, with unchanged messages and bounded diagnostic details.
The exception separately retains deep-copied, untruncated returned blind/reviewer
objects and the canonical admitted exercise, each hashed. The canonical exercise
is not described as the raw author response. No recovery loop, new package policy,
lossless author capture, private persistence or native admission is activated.
The three recovery specifications therefore remain deliberately red. This branch
is not release-ready.
