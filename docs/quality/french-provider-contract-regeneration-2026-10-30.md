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

Local structural regeneration now uses a separate prompt hint of at most 320
characters. It contains fixed validation categories and bounded paths drawn from
owned schema field names, never the rejected candidate's values or exception
message. The private rejection record, original issue text and response hashes
remain unchanged. This prevents model-written content in an error from becoming
new repair instructions and bounds the retry's input overhead. It does not add
semantic retries or change the two-attempt limit.

Actual one-token Qwen 3.5 9B capacity probes found that the earlier broad request
used 9,871 input tokens, too large to reserve the existing 8,192-token answer
allowance in a 16,384-token window. Exercise-scoped references reduced initial
requests, but two representative 1,800-character retries still exceeded that
reservation. Removing JSON separator whitespace, without changing any parsed
source string, schema or curriculum data, then fitted all five measured domain
retries, including all five prior-topic labels. Input counts were 7,152, 7,583,
7,418, 7,414 and 7,810. These are transport probes, not generated-paper passes or
a universal bound for arbitrary error text. The later bounded prompt hint still
requires final integrated capacity verification. No server setting, model weight,
source excerpt or answer allowance changed during those probes.
