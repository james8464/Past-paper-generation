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
