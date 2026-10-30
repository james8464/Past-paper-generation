# Bounded French model capability smoke, 29 October 2026

This is a capability-only comparison, not paper qualification. There were no reference documents, published PDFs, teacher reviews or learner timing observations. One seed and one attempt per task cannot rank models or establish reliability.

## Pinned local smoke

Model: `qwen3.5:9b`, installed digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. Core identity: `1ba734bff3b27f72cbf855aefcffb6223b3e9447247b1595abe8ec0b20b66905`. Harness commit: `d2b58a0a`. Source and model identities were checked before and after every call. No download or production thinking change occurred.

Seed 270100 gave independently calculated answers of distance 12, SQL names `[Noé, Lina]` and Python trace 28. The schema constrained types, not those answers. A separate engineering review checked all three calculations.

| Task | Thinking | Shared output cap | Observed outcome |
| --- | --- | --- | --- |
| Three known-answer tasks | Off | 2,048 | Completed in 9.3 s, 35 tokens; all three answers wrong |
| Authored exercise | Off | 14,000 | Completed in 119.7 s, 2,468 tokens; 13 domain validation errors |
| Three known-answer tasks | On | 2,048 | Length stop in 89.7 s; 7,458 thinking characters and no answer |
| Authored exercise | On | 14,000 | Existing HTTP socket limit reached at 180 s; no response available |

The authored response had a nonrectangular table, invalid graph vertices and inconsistent or malformed marking credits. Validation rejected it without repairing or publishing it. The thinking-on cases do not establish incorrect answers: one exhausted its shared cap and the other reached a transport timeout. Ollama exposes total generated tokens, not an independently measured thought-token count or separate thought-token allowance. A client timeout does not prove that a server-side request immediately stopped.

Evidence remains in the agent worktree under `tmp/french-capability-20261029/qwen35-9b-seed270100`, including prompts, schemas, candidates when returned, raw responses, errors and stop reasons. Summary SHA-256: `2fbb202a51b6273a7f79b128a692540596cce43dd604de44a3c477179af4c10a`.

## Practical model selection

The already installed Qwen 9B was a reasonable first probe on this 18 GiB machine. Its result does not support enabling an unqualified public French authoring route. Weight size alone is not reasoning quality, available working memory or a Keldin acceptance result. Larger quantizations and models also need room for macOS, prompt caches and generation. No further model was downloaded or tested here.

The [official Qwen card](https://huggingface.co/Qwen/Qwen3.5-9B) describes a hybrid thinking model and mode-specific sampling. These runs retained Keldin's conservative sampling and 16,384-token context, so its published benchmark configurations are not equivalent. The card does not support treating `/think` or `/nothink` text as the documented hard mode switch for this model.

[Ollama's thinking API](https://docs.ollama.com/capabilities/thinking) provides the explicit `think` field and separate returned thinking text. [Structured output](https://docs.ollama.com/capabilities/structured-outputs) constrains JSON structure; independent checks remain necessary. The next useful comparison would need an explicitly budgeted thinking configuration and the same known-answer tasks, followed by complete reference-grounded papers if it passes. This smoke does not authorize a default-model change.

## Transport limits found

At the tested source, typed Ollama requests honor their schema and output budget. Typed MLX requests silently used the old 4,096-token cap; a separate scoped fix is required before interpreting a longer-task MLX failure as a model limit. MLX also uses a single answer-phase constrained decoder with thinking disabled, so changing its template flag alone is not a safe thinking implementation.

Typed OpenAI and Anthropic requests currently discard the trusted request budget and schema before transport dispatch. OpenAI uses generic `json_object` without a request-specific output limit. Anthropic uses a fixed 4,096-token limit and a JSON prompt. Downstream validation still applies, but these are not schema-bound transport equivalents. No unsupported API field or relaxed acceptance rule was added by this harness.

## Second installed model: Gemma 4 12B

The same four calls were then run once on installed `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`. This run froze at commit `5a917116`, Core identity `6ebb279c833efb49e799c03c37bb586c6f8138a05fc1bfa7c11a1a46c8ebc63d`. Its intervening provider-budget fix changed MLX and hosted transports, not these Ollama request options or the exercise schema. Source and model checks passed around all four calls. No model was downloaded.

| Task | Thinking | Shared output cap | Observed outcome |
| --- | --- | --- | --- |
| Three known-answer tasks | Off | 2,048 | All three exact answers correct; stop, 38 tokens, 10.3 s |
| Authored exercise | Off | 14,000 | Stop, 2,178 tokens, 158.6 s; curriculum validation rejected the response |
| Three known-answer tasks | On | 2,048 | All three exact answers correct; stop, 999 total tokens, 67.8 s |
| Authored exercise | On | 14,000 | HTTP socket limit reached at 180 s; no response available |

The thinking-on mini response contained 2,231 thinking characters and 85 answer characters. The false-mode authored exercise invented topic identifiers (`SD-GRAPHE`, `BDD-SQL-SELECT`, `ALG-GRAPHES`) outside the supplied curriculum vocabulary. Its four verification objects also used `type` rather than the requested `kind`. The first domain validator rejected it; no normalization, curriculum substitution or response-specific repair was applied. It is not an accepted exercise.

Root's CPU-only native build began during this run. Elapsed values are observations, not controlled speed comparisons. Neither this sequence nor the earlier Qwen sequence establishes overall model rankings. Gemma's exact-answer mini results support further testing; they do not qualify full paper generation. Both thinking-on authoring calls remained unresolved at the transport limit rather than being demonstrated mathematically wrong.

Gemma evidence remains alongside the earlier run in `tmp/french-capability-20261029/gemma4-12b-seed270100`. Summary SHA-256: `f8543ab89f1fb5536381f9b2ff417818b1db79f9051613fdf16dee486eedb31a`. Existing prompts, candidates, errors and earlier attempts were retained. No PDF or user output was published.

The Qwen authoring response reported 2,429 input tokens even without references. Adding its requested 14,000-token output allowance exceeds the configured 16,384 context. Its actual short completion did not reach that boundary, but a full allowance cannot be assumed to fit. This requires an explicit input/context policy before local French qualification. The later bounded typed-budget fix is recorded separately in `mlx-typed-output-budgets-2026-10-29.md`; it does not resolve this Ollama context issue or establish schema-mode equivalence for hosted providers.
