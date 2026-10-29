# Local generation batching acceptance

This review combines the bounded MLX engine, trusted authoring response shapes,
and native mode/progress/ETA changes. It does not establish official paper
equivalence, universal model capability or App Store approval.

## Implementation scope

Ollama's all-subject authoring change was published separately in protected PR122
at `eeea37f80fa876cc51d2cd13e85b532a987fb080`. Its Backend suite passed 4,769
tests with two skips and five existing PDF-library warnings; native checks passed
284 tests with one opt-in skip. Both protected checks passed before merge.

The MLX opt-in keeps one model and inference-owner thread. Two local question
groups can supply independent requests, with independent constrained decoders and
UID-bound results. Long contexts or unsupported caches keep constrained serial
decoding. Hosted-provider scheduling is unchanged. The public French catalogue
remains app-owned and does not call either local model provider.

The native preference is off by default, independent of Ollama's preference, and
captured at job launch. New provenance records a requested worker cap. Historical
records still decode, and ETA history separates serial and parallel modes without
an invented speed multiplier. New progress statuses are localized in English and
French. No hard system RAM or power limit is claimed.

## Actual MLX transport probes

The cached Llama-3.2-3B 4-bit revision
`7f0dc925e0d0afb0322d96f9255cfddf2ba5636e` was used without downloads. The probe
records a streamed hash over model/config/tokenizer data before and after every
process, plus its source-runtime hash. All pins remained unchanged.

Two different finite JSON schemas deliberately prescribe their values. This tests
per-request grammar and result isolation, not question reasoning or exam quality.
Four separate processes ran serial, parallel, parallel, serial; each excluded a
warmup and measured four pairs. All processes exited normally and all results
matched their own schema. Pair means were:

| Run | Mean pair time |
| --- | --- |
| Serial 1 | 3.522 s |
| Parallel 1 | 2.159 s |
| Parallel 2 | 2.067 s |
| Serial 2 | 3.572 s |

The pooled serial mean is 3.547 seconds versus 2.113 seconds in parallel, about
40.4% less time in this short probe. Actual two-sequence decoding events were
observed. This is not a complete-paper speedup estimate.

A source-CLI Accounting P2 job was separately cancelled after real paired decoding
started. It reported cancellation, exited 130 without a forced kill about
0.215 seconds after SIGTERM, and published no PDFs. An oversized prompt-pair probe
reported serial fallback and returned both individually constrained results. Its
MLX allocator peak was 3,444,831,320 bytes, not total computer RAM.

All scripts, raw events and failed/successful attempts are retained privately at
`tmp/local-batching-live-20261029`. Model probes do not create native history
records or change user settings.

## Qualification tooling

The matrix now fingerprints cached MLX model data by file name and full streamed
content hashes, rather than accepting a mutable model name as a pin. Missing
local pins refuse resumable acceptance. Version-two request identities also bind
the desired local worker count, so serial and parallel reports cannot silently
resume each other. No model setup or download is initiated by fingerprinting.

The trusted MCQ shape fix separately narrows response structure; answer correctness
and uniqueness remain checked after decoding. Its evidence and historical limits
are in `trusted-authoring-response-shape-review-2026-10-29.md`.

## Live question-quality limits

Transport success does not establish model reasoning quality. A fresh parallel
Accounting P2 source run with the cached Llama-3.2-3B model refused a question at
independent answer reconciliation and published no paper. Qwen3-8B paired
question trials also produced a contribution question whose correct calculated
value was absent from all four options. The new strict solver validity signal
rejects that case before accepting a canonical answer. It is required for typed
provider responses and cannot be replaced by a string or numeric truth value.

A later Qwen trial rejected the missing-answer question, but accepted a separate
item with two equivalent account statements in reversed conjunction order.
That is a real quality finding, not a successful question qualification. Its
private raw responses and failed probe are retained. A narrow deterministic
regression check now rejects that coordinate-account reversal during candidate
admission and checkpoint restoration. It preserves reversed debit/credit
instructions and different predicates; it is not general semantic-equivalence
detection. Shared review identity v9 prevents reuse of an earlier accepted item
under the stronger policy. Two red reproductions became green in 149 targeted
candidate/checkpoint/solver tests.

These trials do not qualify every cached model, subject or complete paper. The
batching setting remains optional. Refusing invalid model output is intentional;
no answer checks, private-answer boundaries or paper acceptance gates are relaxed
to obtain a successful demonstration.

## Integration gate status

Subagent tests used isolated worktrees: MLX/related contracts 199 passed; trusted
shape/related contracts 306 passed; final native tests 288 passed with one opt-in
skip. Root integration, complete fixed-source tests, rebuilt-helper probes,
protected CI and installed acceptance must all use the final combined head.
These isolated results do not certify later source edits or a whole live paper.
