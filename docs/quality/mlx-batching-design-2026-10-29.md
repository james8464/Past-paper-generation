# Bounded MLX batching design

The Apple-only opt-in uses one loaded model and one inference-owner thread.
At most two callers may enter its queue. A short coalescing window gathers two
independent requests; one request or an unsupported cache uses the established
constrained serial path. Local authoring workers keep their existing validation,
checkpoint and final-paper gates.

The launch flag is `KELDIN_PARALLEL_MLX_GENERATION=1`, captured when the client is
created. Default/off leaves the existing serial MLX path intact. The older Ollama
flag and `parallel_review_workers` meaning are unchanged. The shared scheduler
reads a separate `parallel_generation_workers` cap for the new Apple mode.

The installed Outlines MLX batch adapter rejects constrained output. The installed
`mlx_lm.batch_generate` also does not forward its `logits_processors` parameter.
The implementation therefore uses `BatchGenerator.insert` directly, supplying a
fresh LLGuidance processor for each sequence. UID mapping restores request order.
No grammar state, tokenizer detokenizer or prompt cache is shared across sequences.

Both model calls and tokenizer work stay on the owner thread. Normal JSON parsing,
full original-schema validation and exact item-ID checks stay per request. A bad
response does not invalidate its neighbour. Cancellation closes queued work and
stops decoding between steps. No worker writes checkpoints or output files.

Two long prompts can use more memory than serial generation. Pair token budget and
batch sizes are bounded, with constrained serial fallback for large contexts and
unsupported cache types. This is not a hard system RAM or power limit, and no
speedup or whole-paper qualification is claimed before local acceptance.

The initial cap is 8192 combined prompt tokens and two 4096-token output limits;
prefill runs in chunks of 512. Each batch generator closes in a `finally` block.
Its existing wired-memory setting is restored before constrained serial fallback.
Actual paired decoding emits `provider_batch` only after two sequence responses
are produced; fallback emits `provider_serial_fallback`. Provenance records a cap,
not a claim that every request pair was batched.

## Engineering checks

The new tests started red on the missing batching module. Final isolated checks
passed 199 tests, including 21 new batching tests, existing provider/JSON-ID
contracts, Ollama scheduling and checkpoint tests. Five existing PDF-library
deprecation warnings remain. Coverage includes one owner/model load, independent
decoders and schemas, stable UID ordering, malformed output rejection, per-request
failure isolation, token-limit refusal, generator cleanup, serial fallback and
process cancellation without waiting on an inference socket/thread. These tests
use fake model/generator objects; no new live-model quality or speed result is
claimed. Logs are retained under `tmp/mlx-batching-20261029`.

Ruff passed. The two batching/scheduler leaves passed strict mypy with optional
third-party imports ignored and imported-module diagnostics suppressed; a wider
strict run exposed a pre-existing `events.py` annotation error, not a new-runtime
acceptance result. Root integration still requires the full protected checks,
signed/frozen runtime acceptance and live provider probes before publication.

Official implementation references:
[MLX generation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/generate.py)
and [Outlines](https://github.com/dottxt-ai/outlines).
