# Trusted generation requests

## Problem and scope

The P4 source audit found that quoted candidate text can change a provider's
inferred response schema, repair temperature, batch cardinality or seed. A signed
negative generation seed is also lost by the current English-header regex.
These are request-boundary defects, not evidence that all retained papers failed.
Reproduce each path before changing it. Preserve every older run and its result.

Separate trusted operation settings from prompt prose. Keep existing provider
selection, models, retries, prompt text, downstream validation and private-answer
boundaries. Do not change historical French implementations or saved JSON formats.
Changing negative-seed or injected-marker behaviour requires a versioned current
assessment contract and new pinned acceptance; it is not an identical refactor.

## Implementation sequence

1. Commit the already tested P5 minimal JSON client protocol separately.
2. Add a dependency-light immutable request contract for prompt, operation,
   explicit output schema, trusted sampling, output budget and expected batch IDs.
   Copy schema data at the boundary and on provider handoff. Validate real integer
   seeds/attempts and finite sampling settings without Boolean coercion.
3. Add one compatibility wrapper. Structured-capable clients receive the request;
   minimal custom/fake clients receive the identical `generate_json(prompt)` call.
   Do not catch a client's internal TypeError and retry a different signature.
   Characterise subclass and mocked-client overrides before choosing dispatch.
4. Add explicit Ollama/MLX paths using those settings. Keep their legacy prompt
   entry points for retained callers. Provider repair keeps schema, IDs and seed,
   with its existing repair-temperature rule supplied explicitly.
5. Migrate current authoring, batch/single reviews, independent solving, demand
   review and specialist CS/Edexcel boundaries. Build contracts from owned input
   structures, never by reparsing the prompt. Solver schemas must use only the
   existing blinded public projection, not marking keys or private credits.
6. Keep OpenAI/Anthropic request payloads and model choices unchanged. Their
   current validation stays mandatory; this patch does not migrate API families.

## Proof before activation

- Ordinary positive-seed legacy/typed Ollama payloads match, including budgets,
  schema, retry settings and existing sampling policy.
- Quoted marker strings and reworded instructions cannot change trusted schema,
  IDs/cardinality, seed or repair state.
- Signed seeds follow the documented new application policy; seed-free reviews
  cannot pick up a seed from candidate text.
- Caller schema mutation, malformed contracts and private-answer canaries refuse.
- Fake clients retain exact prompt strings, call counts and instance identity.
- MLX keeps decoder constraints, duplicate-field refusal, output limits, ID
  validation, no runtime installation and `trust_remote_code=false`.
- OpenAI/Anthropic payload snapshots, current replay, numeric and privacy tests
  remain green. No new request metadata enters historical packages/checkpoints.
- Freeze source, run full tests, package/native checks and pinned complete live
  comparison before any current-provider qualification claim. Protected checks
  and merge remain required.

## Official references checked

OpenAI distinguishes JSON validity from schema adherence and documents incomplete
response/refusal handling. The existing JSON-mode payload is therefore not a
reason to remove application validation. See [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
and the [Responses migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses).
The current app uses `/v1/responses`, `text.format` JSON mode and `store: false`;
preserve those actual payload fields. This work does not switch to Chat Completions.

Ollama accepts an explicit schema in `format`, recommends validating the result,
and exposes runtime options separately from message text. See [Structured
Outputs](https://docs.ollama.com/capabilities/structured-outputs) and [Chat
API](https://docs.ollama.com/api/chat). Its [parameter reference](https://docs.ollama.com/modelfile)
lists integer seeds; that does not establish cross-version or cross-provider
equivalence. Preserve the app's positive-seed transformation and explicitly
version its corrected signed-seed behaviour.

No API requests, credential access, model migration or teacher/learner calibration
are authorised or evidenced by this documentation review alone.
