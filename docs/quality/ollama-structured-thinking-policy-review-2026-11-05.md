# Ollama structured-output thinking policy review

## Scope and evidence

This review covers the provider-policy change from `237198e3` to
`942247f9`, including the metadata cache, strict control selection, response
diagnostics, historical French transport keyword and explicit capability-probe
override. Root and two independent reviewers reported no actionable issue in
this delta. It does not certify every line of the provider or the wider project.

Metadata-only requests to the existing local Ollama server returned version
`0.40.5` and these controls:

| Installed model | `thinking.values` | `thinking.default` |
| --- | --- | --- |
| `gemma4:12b` | `[false, true]` | `true` |
| `gpt-oss:20b` | `["low", "medium", "high"]` | `"medium"` |

These requests did not generate text, load a model for inference or download a
model. Ollama documents control discovery through `/api/show`, exact named
values, default selection when `think` is null, and the distinction between
`message.thinking` and the final `message.content`.
[Thinking controls](https://docs.ollama.com/capabilities/thinking),
[model metadata](https://docs.ollama.com/api-reference/show-model-details).

## Behaviour and limits

All Ollama structured requests use the same policy: advertised literal `false`
first, otherwise advertised `"low"`, otherwise the valid advertised default.
The last case records that reduction was unavailable. Absent or unreachable
metadata retains a legacy `false` request marked unknown. Malformed advertised
controls refuse generation. Numeric zero is not a boolean control.

The lookup uses one five-second attempt, cached under a client lock per model.
The historical French adapter retains its 900-second inference default. The
diagnostic probe retains its explicitly selected experimental mode. Schemas,
prompts, token budgets, response validation and inference retry policies are
unchanged. The new policy does not add an inference retry.

The retained installed-174 Gemma run stopped with `length`, 7,195 input tokens,
8,192 output tokens and empty final content. It did not retain the separate
thinking field. Those counts do not prove how tokens were divided between
reasoning and final output. New refusal diagnostics record thinking-field
presence and character count, never its raw text.

This transport choice offers no measured speed or paper-quality guarantee.
Earlier thinking-disabled authoring completed but had schema and curriculum
errors; a thinking-enabled run also produced code and review failures. Neither
mode establishes correct answers or a qualified complete French paper.

## Reviewed implementation hashes

SHA-256 values bind the reviewed implementation delta; later test and generated
inventory changes do not alter these files.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/ollama_thinking.py` | `cbb1f984829e30de72783542c6814f64970bfe05057ec1d7a73b04b62ada1a62` |
| `Backend/Core/providers.py` | `43a63e6ebdafadcb3e7b97cf88c1f0bac2611b56a8a38b9515cfd5b11a4341a8` |
| `Backend/Core/france/network.py` | `bb376ccf77fb34ca224580fed098c5f92fd056c898524d0759208eb9094256bd` |
| `tools/french_model_capability.py` | `623de9876a97b96a1001ccdb05fed7f343dedc69b97ffc3f28885575cf909e10` |

Focused controls cover actual Gemma/GPT-OSS metadata shapes, unsupported
reduction, absent and unavailable metadata, malformed types and bounds,
concurrent cache use, preserved schema/context/output limits, length refusal,
reasoning-text exclusion and historical timeout compatibility. Release builds,
the full suite and live paper qualification remain separate acceptance work.
