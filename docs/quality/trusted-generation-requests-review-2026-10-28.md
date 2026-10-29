# Trusted provider request metadata

Current assessment requests now separate their output grammar, sampling settings
and batch identifiers from prompt prose. The request contract is
`trusted-generation-request-v1`; the current assessment review contract is
`assessment-review-v7-trusted-generation-requests`.

## Scope and compatibility

The migrated boundaries are shared authoring and batch review, single content
review, demand review, independent solving, CS/Edexcel authoring and the current
CS semantic-credit adjudicator. The response simulator remains a legacy
diagnostic endpoint. This is a scoped call-graph review, not a claim that every
possible caller uses the new interface.
The two maintained package call sites instantiate `ResponseSimulator()` without
a model client; its optional AI-client branch is not used by those call sites.

Minimal/custom clients still receive the original `generate_json(prompt)` call.
Only a class-declared structured method opts in. Hosted clients preserve legacy
subclass, instance and mocked method overrides. A client's internal TypeError is
not caught and retried through another signature. A custom override that chooses
the legacy path does not gain a trusted-metadata qualification claim.

Legacy provider entry points retain their English inference behaviour for
retained callers. Current typed requests use explicit contracts and do not call
the prompt parsers. The grammar dictionaries are shared with the legacy path;
there is no second copy of the existing question/review schemas.

Ordinary authoring, solver, review and specialist payload comparisons retain
the existing Ollama schemas, budgets and sampling settings. OpenAI/Anthropic payload
snapshots are unchanged. OpenAI still uses the Responses API at `/v1/responses`
with `text.format` set to `json_object` and `store:false`; this patch does not
migrate API families or remove application validation. The CS credit adjudicator
previously had an unconstrained
grammar. Its new schema explicitly requires two criteria with owned IDs and
allocation values. Existing semantic, quote, ordering and allocation checks still
decide whether its output is valid.

## Trust boundaries

Schemas are copied into immutable request snapshots and copied again for each
provider attempt. Batch cardinalities must be actual integers matching the owned
IDs. Seeds, attempts and budgets reject Boolean coercion; temperatures must be
finite. Contract collections are tuples, including empty credit allocations.

The sampling policy is `(generation_seed + 104729 * attempt) % 2147483647`;
requests without a generation seed use zero. Ordinary positive seeds retain the
previous transformation. Signed negative seeds now follow that same explicit
policy instead of silently becoming zero. Quoted candidate seeds and repair
markers cannot change trusted settings. Ollama receives the explicit seed,
temperature and output budget; its repairs retain schema, IDs and seed and use
the existing repair temperature of zero. MLX receives the owned schema and IDs
but retains the current Outlines 4096-token limit and sampling behaviour. Its
seed, temperature and budget are not rewired by this change. The patch makes no
cross-provider seed or determinism claim.

Solver grammars receive only public choices, response slots, kind and total
marks. Credit allocations belong only to the separate post-solver adjudicator;
attempting to attach them to a solver contract is rejected. Request metadata is
not added to saved assessment/checkpoint JSON. The current review-version change
separates newly authored checkpoints from older current-provider contracts;
retained files and historical French source modules were not rewritten.

## Evidence and limits

Seven legacy faults were reproduced before implementation, including quoted
schema markers, sampling markers, negative seeds, reworded solver/part headers
and nested marking-lock metadata. The observations remain in
`tmp/trusted-request-legacy-audit-reproduction.log`. The initial request-contract
run recorded 22 failures. The current CS credit route recorded two failures
before its migration. Constructor review then recorded seven failures covering
mutable empty credit collections, unhashable operations and Boolean cardinality.

The tests cover ordinary payload equivalence, repair stability, schema mutation,
custom/fake clients, current authoring/checkpoint resume, solver privacy, credit
adjudication and MLX identifier/duplicate-field/size refusal. MLX tests use local
test doubles and retain `trust_remote_code=false` and local-only loading. No live
model/API request, credential access or runtime dependency installation was used
for this change.

After the constructor fixes, the contract suite passed 71 tests. The final
fixed-source targeted gate passed 1118 tests with two skips in 20.42 seconds,
including the historical French provider/pipeline, current provider/replay,
credit, numeric and specialist suites. Ruff and the whitespace diff check passed.
The final log is `tmp/trusted-generation-requests-reviewed-fixed-source-green.log`.
The narrower logs include `tmp/trusted-open-credit-route-red.log`,
`tmp/trusted-request-constructor-review-red.log` and
`tmp/trusted-generation-requests-final-contract-green.log`.

Full final-source tests, packaging/native checks, protected publication and new
pinned live acceptance remain required. This review establishes no teacher,
learner-calibration, model-equivalence or App Store approval claim.

A separate read-only agent reviewed the request constructors, typed provider
dispatch, schema branches, current callers and regression tests. It found no
additional actionable issue. That review did not run a live provider or replace
the pending final-source acceptance gates.
