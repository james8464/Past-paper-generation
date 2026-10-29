# Typed MLX output budgets, 29 October 2026

Typed MLX requests previously lost their `GenerationRequest.output_budget` at provider dispatch and always decoded at most 4,096 tokens. The provider now carries each request's trusted limit through its queue, constrained serial decoder, per-sequence batch decoder and constrained serial fallback. Legacy prompt-only calls retain 4,096. Budgets must be integers from 1 to 16,384; invalid values fail before loading a model.

Paired requests still have separate grammars, result identifiers and output limits. The installed MLX `BatchGenerator.insert` accepts one limit per sequence. Its constructor receives the larger limit, while each inserted sequence receives its own limit. A short task cannot borrow its neighbour's allowance.

The existing 8,192-token combined prompt cap remains. A pair whose combined prompt and maximum output allocation exceeds 16,384 tokens uses constrained serial decoding with its original limits. This preserves the old worst-case pair allocation and avoids silently reserving two full 14,000-token authoring outputs together. It is a conservative token allocation bound, not a measured guarantee about bytes of device memory or speed.

Red tests reproduced dropped typed budgets, missing per-sequence support and unbounded input before the change. Tests cover unequal limits, queued result isolation, serial fallback, malformed limits, actual structured adapter arguments, legacy 4,096 behavior and trusted-ID repairs retaining their original budget. Existing cancellation, independent decoder, incomplete-output and source validation tests remain in place. No GPU inference was run for this fix. Larger limits can make generation slower; they prevent an unintended transport ceiling and do not establish question quality.

## Hosted requests

Typed OpenAI requests now forward their budget as `max_output_tokens`, bounded from 16 to 16,384. Typed Anthropic requests forward `max_tokens`, bounded from 1 to 16,384. Invalid limits fail before a network request. Prompt-only callers retain their prior behavior: no explicit OpenAI output limit and 4,096 for Anthropic. The model or account may impose additional limits, which remain API errors rather than silently changing a requested budget.

These are documented fields in the [OpenAI Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create) and [Anthropic Messages API](https://platform.claude.com/docs/en/api/typescript/messages/create). OpenAI's cap also includes hidden reasoning tokens, so it is not a promise of that many visible answer tokens. No schema mode, security setting or hosted API version changed. These hosted paths still use generic JSON mode or prompt instructions followed by downstream validation, rather than transport-enforced request-specific schemas. Mocked tests check exact payloads, independent successive budgets and refusal before network access. No paid request was made.

## Ollama context remains a separate limit

Ollama already forwards typed output limits, but its configured context is 16,384 tokens. A 14,000-token output allowance leaves at most 2,384 tokens for the complete input and chat wrapper. The authored exercise prompt includes a large schema and later reference excerpts, so that allowance cannot be assumed to fit. UTF-8 byte counts are not a tokenizer measurement. This fix neither trims source material nor raises the global context. A later explicit context policy needs measured tokenization or a conservatively enforced input bound, and memory acceptance before using a larger context on this 18 GiB machine.
