# Generation navigation, estimates and resource controls

## Changes verified

Sidebar navigation stays available during generation. Changing the visible exam
board updates the next selection without changing the captured running job,
clearing its status or starting another request. Creation controls remain locked.
The shared progress footer and Cancel action stay visible in other sections.

Initial time estimates use the median of up to five recent successful runs for
the same board, paper, provider, model and preview setting. Invalid durations and
failed runs are excluded. With no matching history, the existing estimate applies.
Countdown corrections are smoothed over time. Duplicate observations do not
change the estimate; a reversed clock or non-finite progress cannot corrupt it.
An almost-expired estimate during an unfinished review says that it is updating
instead of repeatedly promising one second. These estimates describe software
runtime, not learner completion time.

## Acceptance evidence

- The initial native regression run reproduced three failures. The implementation
  and additional boundary tests then passed.
- Final native run: 279 tests, one opt-in interaction test skipped, no failures.
  Log: `tmp/navigation-eta-rapid-green.log`. A later regression test reproduced
  a three-second ETA jump after only 0.05 seconds between progress events. The
  smoothing interval now uses actual elapsed time, without rounding up to one
  second. Red log: `tmp/navigation-eta-rapid-red.log`. The earlier 278-test run is
  retained in `tmp/navigation-eta-final2.log`.
- A separate opt-in run used the real ContentView with an isolated defaults suite,
  temporary history and a controlled backend. Computer control selected History,
  Documents, French practice and a different UK board while generation remained
  active. The original job was unchanged and only one backend request existed.
  All 277 tests in that run passed. Log: `tmp/navigation-interactive.log`.
- The controlled check made no model calls and did not change user history,
  credentials or output preferences. It proves navigation during work, not model
  throughput or complete interaction coverage.

The AST graph was updated. Graphify reported 44 source files with no extracted
nodes and renamed communities after structural changes; the graph does not cover
those files. The inventory keeps changed file-review attestations pending rather
than certifying them with old hashes.

## Resource-setting plan, not implemented

A single slider cannot honestly promise a hard memory or power limit across
Ollama, MLX and hosted providers. Start with named settings only where a provider
has a supported control and a measured benefit. Keep the existing behaviour as
the default.

1. Record per-request model load, prompt evaluation, generation and review times
   where the provider exposes them. Distinguish queued work from active inference.
   Use a bounded diagnostic record without prompts or credentials.
2. Benchmark a representative request with fixed model, seed and context before
   choosing preset values. Record total latency, peak memory and rejected answers.
   Run these measurements when they will not compete with a user's active job.
3. For MLX, investigate reusable buffer-cache budgets and supported prompt batch
   sizes. Label a cache budget as a cache budget. MLX's memory limit is a graph
   evaluation guideline, not a hard process-memory cap. Keep model calls serialized
   until thread safety and memory behaviour are demonstrated.
4. For Ollama, preserve the context required by the prompt and keep local request
   concurrency at one by default. Its parallelism setting belongs to the server;
   Keldin must not restart or reconfigure a user's server. Increasing parallelism
   multiplies context memory and can cause requests to queue. Do not unload a model
   that another application may be using.
5. For hosted providers, allow bounded concurrency only where independent calls
   already support it. Explain that this affects request rate and possible cost,
   not local GPU memory.
6. Capture any chosen profile when a job starts. Include its effective options in
   request/checkpoint identity and provenance, preserve old-package replay, and
   prevent changes to an active job. Validate provider-incompatible options.
7. Add Settings controls, English/French help and keyboard/accessibility checks
   after the measurements establish useful options. Test cancellation, memory
   failures, invalid saved settings and default migration. Repeat paper-quality
   checks before describing any preset as faster.

Do not trade away answer validation, required syllabus context or publication
checks to improve a speed label. The navigation fix lets people keep using Keldin
while those checks run.

Sources checked on 29 October 2026:

- [Ollama FAQ](https://docs.ollama.com/faq), concurrent requests and context memory.
- [MLX set_memory_limit](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_memory_limit.html), evaluation guideline and allocation failures.
