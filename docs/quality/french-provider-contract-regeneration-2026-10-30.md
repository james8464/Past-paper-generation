# French authoring provider-contract regeneration

This is a bounded engineering repair, not a claim that DeepSeek produces correct
papers. Earlier failed attempts and their model-authored answers remain unchanged.

The French pipeline owns at most two authoring attempts per exercise. Previously,
its provider call occurred outside the structural-rejection handler. DeepSeek
validated JSON and the requested schema before returning, so a completed but
malformed provider response bypassed the advertised regeneration path.

The adapter now raises a dedicated typed error only after the response has a
complete assistant message, matching model identity, verified token usage and
bounded final text, but that text fails strict JSON-object parsing or the exact
requested schema. No JSON is repaired or extracted from surrounding commentary.
Incomplete envelopes, oversized responses, transport, cancellation, context,
identity, usage and invalid owned-schema errors remain hard failures.

The author catches that type inside its existing two-attempt loop. It requests
one new whole exercise from the original brief, schema and sampling settings,
with a bounded error category and trusted schema path. A provider-format error
and a local structural/layout error share the same counter; they cannot create
two nested retry budgets. Negative executable checks and semantic reviews still
refuse. Blind-solving and review calls do not gain a retry. Each adapter call
still makes at most one physical DeepSeek request.

A new opaque rejection record retains the provider, fixed failure category,
response SHA-256 and bounded schema path. It contains no candidate values, raw
response, prompt or credential. The hash can match separately retained private
response diagnostics, when available; it does not independently prove the
contents or validity of an unseen response. Replay checks this record's strict
shape and provider identity. Existing local-rejection records still retain and
rehash their original draft in the historical format. No previous refusal is
reclassified or rewritten.

The typed provider boundary is deliberately scoped to DeepSeek. Other adapters
have different envelope, decoder or legacy parsing paths and are not converted
through a generic ValueError catch. This does not establish equivalent retry
coverage for those providers or improve the educational correctness gate.

Mocked real-adapter/pipeline tests cover a successful regeneration, two failures,
mixed local/provider failures, strict replay, bounded redacted diagnostics and
single-call hard refusals. No inference or paid service calls were used for
these tests. Complete live-paper review and publication remain separate gates.
