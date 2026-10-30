# French structured-output repetition policy

## Evidence and scope

The installed free `gpt-oss:20b` model was downloaded from Ollama's official
registry and verified as digest
`f38aa0c53da5f8c49d08c43a99df24ff53167fe68e24664a7777288e7656fdfe`.
The local server reports named reasoning levels with medium as its default.
These capability probes used that default and unchanged source at `e76d5921`.
They are not complete-paper tests or a model ranking.

The same seed 270100 and three small independently calculated tasks were run
twice. Parsed transport payloads are identical apart from repeat_penalty.
The schema constrains result types and ranges, not the expected answers.

| Setting | Exact result |
| --- | --- |
| Existing penalty 1.15 | Distance 12 and trace 28 correct; SQL row order correct, but `Noé` changed to `Noè`, so exact data preservation fails |
| Neutral penalty 1.0 | All three exact results match: 12, `[Noé, Lina]`, 28 |

No accent normalization, answer substitution or expected-answer schema constant
was used. Source and model identities were unchanged around both calls. This
single paired observation does not prove causation, general reliability or a
speed improvement. Cache state and model implementation are further limits.
The initial local probe-driver setup error occurred before any model request;
it remains retained and is not counted as a model failure.

Private evidence is in `tmp/french-v36-live-20261030/` under
`gpt-oss-20b-logic-2` and `gpt-oss-20b-logic-neutral-1`. Request and raw response
records are retained. Response SHA-256 values are respectively
`fa437f99415997940f8e9bef0519c68c15c697525806400dcf89b44a77d9980d`
and `62fed292b631aa81d1671a25679d6ba34a9ff044322470c392d41bbce4195a18`.

## Research and decision

[Qwen's precise-coding guidance](https://huggingface.co/Qwen/Qwen3.5-9B#using-qwen35-via-the-chat-completions-api)
uses repetition penalty 1.0. It is reasonable to avoid discouraging identifiers
and literal data that must repeat in code and JSON, but that is an engineering
inference, not an explanation of the earlier Gemma correction error.

[GPT-OSS guidance](https://github.com/openai/gpt-oss#recommended-sampling-parameters)
recommends temperature 1.0 and top-p 1.0. In contrast,
[Ollama's structured-output guidance](https://docs.ollama.com/capabilities/structured-outputs#tips-for-reliable-structured-outputs)
suggests lower temperatures for determinism. The present change does not claim
to adopt either complete preset. Only the new French NSI route uses neutral
repetition penalty. Legacy UK and diagnostic requests retain 1.15. Temperature,
top-p, seed, schemas, budgets, reasoning policy, timeouts and acceptance rules
remain unchanged and are covered by payload regressions.

Full reference-grounded generation and independent question/page review remain
required. No complete French paper is qualified by these three small tasks.
