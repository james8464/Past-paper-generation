# Provider boundary full-file review

Internal engineering review, 2 November 2026. This records complete-file reading and a repaired transport defect. It does not qualify generated papers or certify every provider.

## Reviewed files

The reviewer read all three files through EOF. `providers.py` was read at its 1,883-line baseline, SHA-256 `ce8627ed0acd104ed4411e4b849ac41d3f27b3ca2a338483b00d99e6b5fe4e66`, then reviewed its complete 13-line transport addition. The other files remained unchanged. The following final hashes were checked again on integration head `449fb335`.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/providers.py` | 1896 | `30802cade04b0f4d4c9bf83ef0ac8337ea15f4f5896a0a60f0b1ac64aa81c6c0` |
| `Backend/Core/apple_intelligence.py` | 414 | `91862246849e3a08acef4cfd7c907d30f8432dce27d0776be57e5828fc9d40ef` |
| `Backend/Core/json_client.py` | 9 | `f1c48f8deb2fed4b7534ef62ffa7a445115cf12a3570a98166cb067a5af66a62` |

## Finding and repair

The French Ollama metadata path used the existing direct, non-redirecting transport, but the default typed inference client still used generic `urlopen`. Environment proxy settings or an HTTP redirect could therefore send the inference request beyond the endpoint admitted by the French path.

Commit `8fc8ed9e71929d37398cc8f68d4774f7e20fa2a9` routes default French inference through `open_ollama_request`, reusing its empty proxy configuration and redirect refusal. The explicit injected-transport contract, UK legacy transport, hosted-provider transports, payload bytes, timeout, error classification and single physical attempt are unchanged. Combining the direct-local and fixed-host modes is refused.

The tests exercise the public typed-client route with fake openers. They cover proxy bypass, redirect refusal, one physical attempt for HTTP/network/timeout failures, context-error classification, unchanged payload bytes and omission of an unrelated hosted credential. No real network request or model inference was used.

Three regression cases failed before the repair. The final focused run passed 348 tests in 2.92 seconds; Ruff and diff checks passed. Local logs are retained under `tmp/french-local-inference-transport/`: `red.log`, `green.log` and `final-focused.log`. These local logs are not bundled qualification evidence.

A separate agent (`french_run23_review`) reviewed the transport change independently and returned no P1/P2 finding. It confirmed that integrated commit `9132d2a1` preserves the author commit's provider, network and test files, and checked typed routing, unchanged payloads/attempts, HTTP error handling, proxy/redirect refusal and the changed tests. This was a bounded source review, recorded in the completed review chat, not a second full-file provider audit or an independently executed test run.

## Other boundaries read

- Provider dispatch, request metadata, context admission, schema handling, retries and error translation were traced. Hosted transport parsing and local transport parsing are not claimed to have identical guarantees.
- The Apple helper's subprocess ownership, cancellation/reaping, filtered credential environment, helper identity, context limits and original-schema post-validation were reviewed. Guided projection remains restricted to compatible operations; unsupported schemas retain their existing route.
- `json_client.py` defines the small `generate_json` protocol. Typed dispatch is selected separately when the client type exposes `generate_request`; simple test clients remain supported.
- Legacy JSON extraction can recover an object from surrounding prose. This existing compatibility behavior was not broadened or presented as strict JSON admission.

## Limits

This is a source-level review of the three exact files above. Related callers and tests were inspected where needed, but unread files are not covered by this attestation. No additional concrete defect was established within this scope; that is not a guarantee that none remains.

Model correctness, full-paper difficulty and formatting, live provider behavior, learner calibration, rights clearance and Store approval require separate evidence. No paid calls, model downloads, accessibility tests or release builds were performed for this review. Full-suite and protected-CI acceptance belong to the integrated release, not to the focused result recorded here.
