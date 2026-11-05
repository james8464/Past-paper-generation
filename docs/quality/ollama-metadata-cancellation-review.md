# Ollama metadata cancellation review

This internal engineering review covers provider cancellation, not generated-paper correctness or release qualification.

## Source scope

The reviewer read all 1,941 lines of `Backend/Core/providers.py` at baseline `8884342422fa6d6514963ff1618dfc2067bdb0dd`, SHA-256 `43a63e6ebdafadcb3e7b97cf88c1f0bac2611b56a8a38b9515cfd5b11a4341a8`, then reviewed both complete cancellation deltas. The final file has 1,967 lines and SHA-256 `30d54c477e3436c5a0fb0594a4a06ba545ccb91c0dfaa9f04ce781c85d914e35`.

The full-file reading covered provider dispatch, capability caching, request and output budgets, MLX ownership and decoding, hosted transports, structured response parsing, schema construction and error handling. Related French signal handling, typed request dispatch and cancellation tests were inspected selectively. This does not attest to complete dependency or whole-project review.

## Defect and repair

The metadata fallback caught `OSError`, including the `InterruptedError` raised by French cancellation. An interrupted `/api/show` lookup could therefore become cached unavailable metadata and start `/api/chat` after cancellation.

The repair propagates the original interruption before caching or inference. A bounded walk follows only the wrappers used by the transports: `URLError.reason` and `RuntimeError.__cause__`. It does not infer cancellation from message text. Ordinary network failures still use the existing cached unavailable policy.

A follow-up control found the same primitive in shared transport: wrapped cancellation could enter the ordinary network retry path during `/api/chat`, before the metadata caller could inspect it. The transport now reuses the same bounded helper before retry progress or sleep. Direct Ollama and standard urllib paths both preserve the original interruption and make no retry. Ordinary network failures retain their existing retry counts and delays. Prompts, schemas, token budgets and validation thresholds are unchanged.

## Checks and review

Seven fully offline regression cases failed before the metadata repair: cancellation during opening or reading, directly or through either known wrapper, plus the real shared urllib wrapper with fake openers. Two additional shared-transport cancellation cases failed before the follow-up repair, while two ordinary retry controls passed. The final focused run passed 165 tests across provider, French capacity, authoring and probe tests. Controls preserve the same interruption object, refuse chat/cache/repair after cancellation, retain ordinary network fallback and retries, ignore misleading error text and bound cyclic wrapper chains. All openers, retry progress and sleep are stubbed in the shared-transport controls.

The first version of the real-wrapper test omitted a downstream chat stub and made one unintended localhost request for the nonexistent model `owned`; the server returned HTTP 404 and no model generation succeeded. The test was corrected to block all chat transport, and the seven-case offline red run was repeated. The earlier request is not acceptance evidence.

Ruff checking, formatting and diff checks passed. The configured type gate passed its four infrastructure files; this is not a claim that the full provider module is statically clean. An ad-hoc direct check exposed existing legacy/import typing errors outside this repair.

Root and a separate native reviewer independently reviewed both the metadata repair and the complete shared-transport follow-up without finding an additional actionable issue. The final test-file SHA-256 is `ce5a13f4a6d3ab535536766c370fb32b3668a64bd4ed1fd7c1d6cc6c2b5b009d`.

Root also reports an offline frozen-helper red control against the preceding build: the checker verified compiled-source identity and blocked all chat transport, then detected inference being reached after metadata cancellation. Its retained log is `tmp/nov5-cancellation-packaged-red.log`. Final packaged acceptance, full suites, protected CI and installation remain integration gates, not completed claims in this report.

No release build, paid request, model inference, GUI operation or publication was performed for this repair. No further concrete defect was established within the reviewed source scope. Semantic paper quality, the known Accounting Q06 limitation and distribution approval remain separate concerns.
