# Ollama metadata cancellation review

This internal engineering review covers provider cancellation, not generated-paper correctness or release qualification.

## Source scope

The reviewer read all 1,941 lines of `Backend/Core/providers.py` at baseline `8884342422fa6d6514963ff1618dfc2067bdb0dd`, SHA-256 `43a63e6ebdafadcb3e7b97cf88c1f0bac2611b56a8a38b9515cfd5b11a4341a8`, then reviewed the complete cancellation repair. The final file has 1,964 lines and SHA-256 `d3249fd60038e025155e626c92781ba119ad85ecffe23953726738b9294e1df4`.

The full-file reading covered provider dispatch, capability caching, request and output budgets, MLX ownership and decoding, hosted transports, structured response parsing, schema construction and error handling. Related French signal handling, typed request dispatch and cancellation tests were inspected selectively. This does not attest to complete dependency or whole-project review.

## Defect and repair

The metadata fallback caught `OSError`, including the `InterruptedError` raised by French cancellation. An interrupted `/api/show` lookup could therefore become cached unavailable metadata and start `/api/chat` after cancellation.

The repair propagates the original interruption before caching or inference. A bounded walk follows only the wrappers used by the transports: `URLError.reason` and `RuntimeError.__cause__`. It does not infer cancellation from message text. Ordinary network failures still use the existing cached unavailable policy. Prompts, schemas, token budgets, retries and validation thresholds are unchanged.

## Checks and review

Seven fully offline regression cases failed before the repair: cancellation during opening or reading, directly or through either known wrapper, plus the real shared urllib wrapper with fake openers. The final focused run passed 161 tests across provider, French capacity, authoring and probe tests. Controls preserve the same interruption object, refuse chat/cache/repair after cancellation, retain ordinary network fallback, ignore misleading error text and bound cyclic wrapper chains.

The first version of the real-wrapper test omitted a downstream chat stub and made one unintended localhost request for the nonexistent model `owned`; the server returned HTTP 404 and no model generation succeeded. The test was corrected to block all chat transport, and the seven-case offline red run was repeated. The earlier request is not acceptance evidence.

Ruff checking, formatting and diff checks passed. The configured type gate passed its four infrastructure files; this is not a claim that the full provider module is statically clean. An ad-hoc direct check exposed existing legacy/import typing errors outside this repair.

Root and a separate native reviewer independently reviewed the final production and test delta without finding an additional actionable issue. The final test-file SHA-256 is `e36f31ee61d13e8d439e28cb666d09c2a4bad57bfa38ca577aa4b9903e9f1ff9`.

Root also reports an offline frozen-helper red control against the preceding build: the checker verified compiled-source identity and blocked all chat transport, then detected inference being reached after metadata cancellation. Its retained log is `tmp/nov5-cancellation-packaged-red.log`. Final packaged acceptance, full suites, protected CI and installation remain integration gates, not completed claims in this report.

No release build, paid request, model inference, GUI operation or publication was performed for this repair. No further concrete defect was established within the reviewed source scope. Semantic paper quality, the known Accounting Q06 limitation and distribution approval remain separate concerns.
