# Current local-model headroom

## Scope and rationale

The retained single PR193 Qwen trial was stopped during cold loading when memory
pressure became non-normal: one request started, zero completed, no PDF or quality
pass. It was not a model-content failure. The owner reported all post-run source,
reference, model metadata and personal-state checks unchanged. No retry is part
of this repair. The original PR191 memory note remains historical and unchanged.

This increment changes only the shared local Ollama admission module. The existing
physical-memory reserve and macOS normal-pressure requirement remain. New current
headroom is an **approximate policy budget**, not measured runtime/peak RAM:

- Darwin: minimum of physical memory less the existing reserve, and native page
  size times free plus inactive pages. Speculative pages already belong to free;
  overlapping purgeable/file-backed/active/compressor categories are not added.
- Linux: the same physical cap and kernel MemAvailable, never MemFree substitution
  or a fabricated equivalent pressure level.

Bounded direct tags/ps metadata correlates exact installed digest and residency.
Cold loading needs weights plus the existing overhead; a resident selected digest
still needs generation/context overhead, without counting its full weights again.
Conflicting aliases/digests, duplicate residency, malformed or unknown metadata
and sensors refuse with the existing non-retryable resource category. Cancellation
retains its original interruption identity. Sensors run after metadata, with a
fresh pressure/physical-memory recheck; probes have explicit time/content bounds.

Remote Ollama, hosted and Apple paths, prompts, schemas, options, output budgets,
quality validation and approved parallel behavior are unchanged. No model-name
special case, service/global change, runtime monitor or aggregate lock is added.

## Exact reviewed source and evidence

Source: Backend/Core/ollama_admission.py, 259 lines,
SHA256 d6f62485633e80f575695fafa748164f9d0d386dcde96f988cd820fcb3d93e0e.
New tests: tests/test_ollama_headroom.py, 318 lines,
SHA256 e550fc5a6dae7bc4bc1a28ef66a885fb5d038b2ae914ee07b6dc122ec1c7c534.

Genuine RED against unchanged production: 16 failed / 3 passed in 0.15 seconds.
Final focused gate after typing-only finish: 386 passed in 1.54 seconds, five
inherited SWIG warnings (the earlier pre-typing gate was 386 in 1.11 seconds).
The ten-file scope includes new/old admission tests and eight transport-fixture
files. The guarded owner forbids unstubbed sensors, metadata and network sockets;
fixtures supply capacity inputs, never waive production policy. The first guarded
combined run (21 failed / 358 passed) exposed a missing new-test parser binding;
that fixture was corrected to exercise the real parser with mocked sensor input.
Its failed log remains retained, not acceptance evidence.

Controls cover ample reclaimable cache, exact cold/warm byte boundaries, retained
warm overhead, unrelated/ambiguous residency, malformed/oversized/bounded ps,
Linux required available memory, sensor failures/cancellation, pressure changes
after metadata, zero chat POST on refusal and unchanged successful request content.
Ruff check/format and diff checks passed. Strict single-module mypy passed after
explicit JSON/container/set annotations and casts after runtime type validation;
no admission condition, catch, cancellation or retry behavior changed. No full suite, build, live metadata,
model inference, GUI or new empirical quality qualification was performed.

## Remaining limits

Inactive memory may require paging or reactivation, and residency can expire or
change after a snapshot. Concurrent starts are not atomically reserved. Context
growth and cold-load transients may exceed the heuristic; available headroom does
not guarantee runtime fit. Preflight alone cannot cancel pressure rising after
POST: the retained trial's separate owned-job watchdog did that. Per-owned-request
runtime cancellation is deferred design work, not part of this increment. No
claim is made to fix the historical native hang or WindowServer incident, prevent
every crash, qualify this model, or establish public whole-paper/official quality.
