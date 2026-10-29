# Bounded local review concurrency

The optional **Parallel Edexcel reviews** setting allows two independent Economics
Edexcel review jobs to use Ollama concurrently. It defaults to off. Other subjects,
MLX, hosted-provider scheduling and local question authorship are unchanged.
This is not a memory or power limit slider.

Each job still runs the independent solver, answer/scheme agreement check and
reference-demand review. Results are reassembled in paper order. Workers do not
write checkpoints or mutate shared assessment state. Progress is published by the
calling thread. Failures propagate; cancellation can terminate the helper without
waiting for outstanding model sockets. No quality gate is bypassed.

The setting is captured at job launch and recorded as `localReviewWorkers` in new
native provenance. Historical records can omit it. Settings cannot change it during
an active run. Two requests need enough memory for Ollama's expanded context cache;
they can be slower on a memory-constrained machine.

## Local throughput probe

User approval covered enabling two parallel requests and restarting idle Ollama.
The original server used one slot. Two simultaneous requests then merely queued:
serial pairs took 17.20 and 18.25 seconds, concurrent pairs 18.40 and 18.30 seconds.

After setting `OLLAMA_NUM_PARALLEL=2` through the login-session environment and
normally quitting/restarting Ollama, its startup log confirmed two slots. The same
gemma4:12b probe used four counterbalanced pairs, excluding warmup:

| Scheduling | Pair times | Mean |
| --- | --- | --- |
| Serial | 18.48 s, 19.62 s | 19.05 s |
| Two requests | 13.61 s, 13.40 s | 13.51 s |

This is a 29.1% reduction in short-pair wall time, not a measured whole-paper
speedup. All eight responses satisfied the small JSON schema; this does not
establish exam quality. Prompt lengths and generated token counts varied. The
probe used temperature 0, fixed seeds, context 16384 and output limit 180 tokens.
No models were downloaded and no user paper/history was created.

Logs are retained locally at `tmp/local-parallel-probe-20261029.log` and
`tmp/local-parallel-two-slots-probe-20261029.log`. The global environment change is
login-session-scoped. Reverting it requires removing that environment setting and
normally restarting Ollama when idle. No reboot-persistence claim is made.

## Checks and limitations

- Focused Python checks: 176 passed, including worker ordering, overlap, failure,
  invalid limits, process cancellation and serial/concurrent review parity.
- Native suite: 284 tests, one opt-in test skipped, zero failures. Coverage includes
  default/persisted setting, launch capture, provenance and active-run immutability.
- Solver-adapter checks: 28 passed. Both protected CI checks are required before
  merge. Third-party PDF library deprecation warnings remain unchanged.
- The short probe is not a full live Edexcel paper acceptance run. French content,
  paper qualification, App Store approval and full interaction coverage are not
  established by this change.

Ollama documents memory and context implications in its
[FAQ](https://docs.ollama.com/faq). Requests use the existing
[generation API](https://docs.ollama.com/api/generate).
