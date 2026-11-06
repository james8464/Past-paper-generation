# Local model memory checks

## Purpose

A larger local-model trial coincided with a WindowServer watchdog restart. The
diagnostic report does not establish its cause. That trial is retained as
interrupted evidence, not a completed paper-quality test. No further heavy-model
trial is part of this change.

The shared Ollama generation path now checks local capacity before requesting
tokens. This covers the native app, command-line generation, the seven UK
generator families and French generation, including its injected transport.
The guard does not change prompts, questions, output budgets, marks or validators.

## Policy

Only literal loopback addresses and localhost use this Mac's capacity checks.
Remote Ollama endpoints, hosted providers and Apple providers keep their existing
behaviour. Endpoint consent, direct transport and redirect restrictions remain.

The guard reads physical memory from the operating system. On macOS, the
categorical memory-pressure level must also be normal. Linux uses its physical
memory bound without inventing an equivalent pressure level. Unsupported or
unavailable required readings refuse the request explicitly.

A bounded, direct `/api/tags` lookup reads the selected installed model's size.
Missing, malformed, ambiguous or oversized metadata cannot silently admit it.
The physical-memory budget reserves the larger of 4 GiB or one quarter of RAM
for the system. Model weights require the larger of 2 GiB or one quarter of their
size as additional headroom. These margins are a conservative policy, not a
measurement of runtime memory requirements.

Stored model size is not the same as memory needed for generation. Context,
parallel requests, other loaded models and other applications can consume more.
The guard deliberately does not compare the full model size with free memory on
each request: that would count an already loaded model twice and could prevent
the next question from starting.

Resource refusal is distinct from malformed model output. It bypasses both
provider repair attempts and French structural regeneration. Both public routes
emit `local_memory_unavailable`; the app presents a short English or French
explanation. History retains its app-owned failure category rather than raw
resource details. Existing cancellation exceptions remain cancellations.

## Verification and review scope

Tests use fake model metadata, sensors and transports. They cover memory-policy
boundaries, unknown readings, loopback and remote routing, bounded metadata,
aliases, cancellation, repair bypass and unchanged request content. Public-route
tests reproduce the old generic error classification before checking the new
terminal code. Native presentation tests check both languages without disclosing
the raw diagnostic. Transport-only tests explicitly supply fake capacity inputs;
production has no test-mode exemption.

The new admission module and tests received complete-file independent review.
Existing provider, generation, French runtime and native presentation files
received complete-delta and relevant call-path review against their recorded
baselines. This is not a fresh whole-file or whole-project audit. Earlier
source-bound reviews remain identified in the audit ledger.

This is a preflight check, not a runtime monitor, an aggregate allocation lock or
a guarantee against memory exhaustion. Approved bounded parallel generation is
unchanged. No service is restarted, model unloaded, unrelated process closed or
system setting changed. French paper quality, learner timing and provider-wide
qualification remain separate, incomplete work.

Sources: [Ollama model metadata](https://docs.ollama.com/api/tags) and
[Ollama memory and concurrency guidance](https://docs.ollama.com/faq).
